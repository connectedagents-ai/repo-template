#!/usr/bin/env python3
"""find_plaintext_keys.py — READ-ONLY: list API keys/tokens stored as plain text, so you know what to rotate.

    python3 find_plaintext_keys.py                       # scan the usual places on this Mac
    python3 find_plaintext_keys.py ~/Code/some-repo      # also scan these folders/files

Prints file, line, variable NAME, whether the file is committed to git, and where to rotate it.
Never prints a value. Values that are already references (op://…, $(op read …), ${VAR}) are ignored.
"""
import argparse, os, re, subprocess, sys
from pathlib import Path

HOME = Path.home()
# PAT only as its own word part (GITHUB_PAT, PAT_2), so PATH/PYTHONPATH don't count
NAME = r"[A-Za-z0-9_.-]*(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|PAT(?![A-Za-z]))[A-Za-z0-9_.-]*"
# NAME=value · export NAME=value · NAME = "value" (TOML) · "name": "value" (JSON)
ASSIGN = re.compile(rf"""^\s*(?:export\s+)?["']?({NAME})["']?\s*[:=]\s*["']?([^"'\s#,]+)""", re.I)
# .npmrc registry auth: //registry.npmjs.org/:_authToken=value
NPMRC = re.compile(r"^\s*(//[^\s=]+:(?:_authToken|_auth|_password))\s*=\s*[\"']?([^\"'\s]+)")
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


def tracked_in_git(path):
    r = subprocess.run(["git", "-C", str(path.parent), "ls-files", "--error-unmatch", "--", path.name],
                       capture_output=True, text=True)
    return r.returncode == 0


def scan_file(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for n, line in enumerate(f, 1):
                m = ASSIGN.match(line) or NPMRC.match(line)
                if m and is_plaintext(m.group(2)):
                    yield n, m.group(1)
    except OSError:
        return


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
    hits, seen = [], set()
    for t in targets:
        if not t.exists():
            continue
        for f in candidates(t):
            if f in seen or f.stat().st_size > 2_000_000:
                continue
            seen.add(f)
            for line, name in scan_file(f):
                hits.append((str(f).replace(str(HOME), "~", 1), line, name, tracked_in_git(f)))
    if not hits:
        print("No plain-text keys found in the places scanned. 🎉")
        return
    print(f"Found {len(hits)} plain-text key(s). Values are NOT shown.\n")
    for f, line, name, in_git in hits:
        flag = "  ⚠ COMMITTED TO GIT: treat as leaked" if in_git else ""
        print(f"- {name}\n    in {f} (line {line}){flag}\n    rotate at: {rotate_url(name)}")
    print("\nFor each one: 1) make a new key at the link, 2) save it in 1Password, 3) replace the line with an op:// reference,"
          " 4) delete the old key at the provider.")
    sys.exit(1 if any(h[3] for h in hits) else 0)


if __name__ == "__main__":
    main()
