#!/usr/bin/env python3
"""find_plaintext_keys.py — READ-ONLY: list API keys/tokens stored as plain text, so you know what to rotate.

    python3 find_plaintext_keys.py                       # scan the usual places on this Mac
    python3 find_plaintext_keys.py ~/Code/some-repo      # also scan these folders/files

Prints file, line, variable NAME, whether the value is in git history (or the file is merely git-tracked), and where
to rotate it. Never prints a value. Values that are already references (op://…, $(op read …), ${VAR}) are ignored.
Exit status: 1 = a key is in git history · 2 = some files could not be read (scan incomplete) · 0 = otherwise.
"""
import argparse, os, re, subprocess, sys
from pathlib import Path

HOME = Path.home()
# PAT only as its own word part (GITHUB_PAT, PAT_2), so PATH/PYTHONPATH don't count
NAME = r"[A-Za-z0-9_.-]*(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|PAT(?![A-Za-z]))[A-Za-z0-9_.-]*"
# NAME=value · export NAME=value · NAME = "value" (TOML) · "name": "value" (JSON)
# The value is the whole quoted string when quoted ("correct horse battery staple"), else up to whitespace/#/,
# (backslash-escaped quotes stay inside the value: "ab\"cd")
VALUE = r"""(?:"((?:[^"\\]|\\.)*)"|'((?:[^'\\]|\\.)*)'|([^"'\s#,]+))"""
ASSIGN = re.compile(rf"""^\s*(?:export\s+)?["']?({NAME})["']?\s*[:=]\s*{VALUE}""", re.I)
# .npmrc registry auth: //registry.npmjs.org/:_authToken=value
NPMRC = re.compile(rf"^\s*(//[^\s=]+:(?:_authToken|_auth|_password))\s*=\s*{VALUE}")
REFERENCE = ("op://", "$(", "${", "$", "<", "your", "xxx", "changeme", "replace", "example", "none", "null", "true", "false")
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", "Library", ".Trash"}
CANDIDATE = re.compile(r"(^\.env(?!\.example$)|\.env$|rc$|profile$|config\.toml$|settings\.json$|mcp.*\.json$|claude_desktop_config.*\.json$|\.json$)", re.I)
ROTATE = [
    ("ANTHROPIC|CLAUDE", "https://console.anthropic.com/settings/keys"),
    ("OPENAI", "https://platform.openai.com/api-keys"),
    ("XAI|GROK", "https://console.x.ai"),
    ("GITHUB|GH_", "https://github.com/settings/tokens"),
    ("STRIPE", "https://dashboard.stripe.com/apikeys"),
    ("SLACK", "https://api.slack.com/apps"),
    ("VERCEL", "https://vercel.com/account/tokens"),
    ("CLOUDFLARE|CF_", "https://dash.cloudflare.com/profile/api-tokens"),
    ("GOOGLE|GEMINI", "https://aistudio.google.com/apikey"),
    ("PERPLEXITY|PPLX", "https://www.perplexity.ai/settings/api"),
    ("NOTION", "https://www.notion.so/profile/integrations"),
    ("OPENROUTER", "https://openrouter.ai/settings/keys"),
    (r"^//[^:]*npmjs\.org/?:_|\bNPM_", "https://www.npmjs.com/settings/~/tokens"),
    ("SUPABASE", "https://supabase.com/dashboard/account/tokens"),
    ("TWILIO", "https://console.twilio.com"),
]
DEFAULT_FILES = [".zshrc", ".zprofile", ".bashrc", ".bash_profile", ".profile", ".npmrc", ".codex/config.toml",
                 ".grok/user-settings.json", ".gemini/settings.json", ".cursor/mcp.json",
                 "Library/Application Support/Claude/claude_desktop_config.json"]


def rotate_url(name):
    for pat, url in ROTATE:
        if re.search(pat, name, re.I):
            return url
    return "the provider's console"


def is_plaintext(value):
    v = value.strip().lower()
    return len(v) >= 8 and not v.startswith(REFERENCE)


def git_status(path, value):
    """'committed' if this value is in the file's git history, 'tracked' if git tracks the file, else ''.
    The value never goes into a git command line (other local users can read process arguments): git hands back
    every committed version of the file, merge resolutions included, and the search happens here."""
    d, name = str(path.parent), path.name
    tracked = subprocess.run(["git", "-C", d, "ls-files", "--full-name", "--error-unmatch", "--", name],
                             capture_output=True, text=True)
    if tracked.returncode != 0:
        return ""
    repo_path = tracked.stdout.splitlines()[0]
    commits = subprocess.run(["git", "-C", d, "log", "--all", "--full-history", "-m", "--format=%H", "--", name],
                             capture_output=True, text=True).stdout.split()
    if not commits:
        return "tracked"
    wanted = "".join(f"{c}:{repo_path}\n" for c in dict.fromkeys(commits)).encode()
    blobs = subprocess.run(["git", "-C", d, "cat-file", "--batch"], input=wanted, capture_output=True).stdout
    return "committed" if value.encode() in blobs else "tracked"


def scan_file(path):
    """[(line, name, value)]. Raises OSError if the file can't be read, so the caller can report the gap."""
    found = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for n, line in enumerate(f, 1):
            m = ASSIGN.match(line) or NPMRC.match(line)
            if m:
                value = next(v for v in m.groups()[1:] if v is not None)
                if is_plaintext(value):
                    found.append((n, m.group(1), value))
    return found


def candidates(root, max_depth=5):
    if root.is_file():
        yield root
        return
    base = len(root.parts)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS] if len(Path(dirpath).parts) - base < max_depth else []
        for fn in filenames:
            if CANDIDATE.search(fn):
                yield Path(dirpath) / fn


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", type=Path, help="extra folders or files to scan")
    ap.add_argument("--no-defaults", action="store_true", help="scan only the given paths")
    a = ap.parse_args()
    targets = [] if a.no_defaults else [HOME / f for f in DEFAULT_FILES] + [
        p for pat in ("agent-central-config", "*/agent-central-config", "*/*/agent-central-config")
        for p in (HOME / "Code").glob(pat) if p.is_dir()]
    targets += [p.expanduser() for p in a.paths]
    hits, seen, unreadable = [], set(), []
    for t in targets:
        if not t.exists():
            continue
        for f in candidates(t):
            if f in seen:
                continue
            seen.add(f)
            short = str(f).replace(str(HOME), "~", 1)
            try:
                if f.stat().st_size > 2_000_000:
                    continue
                found = scan_file(f)
            except OSError as e:  # broken symlink, permission denied, vanished file
                unreadable.append(f"{short} ({e.strerror or type(e).__name__})")
                continue
            hits += [(short, line, name, git_status(f, value)) for line, name, value in found]
    flags = {"committed": "  ⚠ IN GIT HISTORY: treat as leaked",
             "tracked": "  ⚠ file is tracked by git: check it was never committed (git log -p -- <file>)"}
    if hits:
        print(f"Found {len(hits)} plain-text key(s). Values are NOT shown.\n")
        for f, line, name, status in hits:
            print(f"- {name}\n    in {f} (line {line}){flags.get(status, '')}\n    rotate at: {rotate_url(name)}")
        print("\nFor each one: 1) make a new key at the link, 2) save it in 1Password, 3) replace the line with an op:// reference,"
              " 4) delete the old key at the provider.")
    else:
        print("No plain-text keys found in the files that could be read.")
    if unreadable:
        print(f"\n⚠ INCOMPLETE: {len(unreadable)} file(s) could not be read, so they were not checked:")
        print("\n".join(f"  - {u}" for u in unreadable))
    sys.exit(1 if any(h[3] == "committed" for h in hits) else 2 if unreadable else 0)


if __name__ == "__main__":
    main()
