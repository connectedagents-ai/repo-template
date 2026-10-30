#!/usr/bin/env python3
"""skills_hub.py — find every Agent Skill (SKILL.md) on this machine, flag duplicates, and serve one canonical set to every tool.

    python3 skills_hub.py inventory                                   # report: every skill, which tool, duplicates, bad front matter
    python3 skills_hub.py inventory --scan-repos ~/Code --out ~/ops-reports/skills.csv
    python3 skills_hub.py link --hub ~/Code/connectedagents-ai/config/skills            # DRY RUN: what would be linked
    python3 skills_hub.py link --hub ~/Code/connectedagents-ai/config/skills --apply

inventory: read-only. Scans the known per-tool skill folders (Claude Code, the cross-agent ~/.agents/skills that Codex and Cursor
read, Cursor, Codex, Antigravity/Gemini, Grok) plus any --root, and with --scan-repos every repo-level .claude/.agents/.cursor/
.codex/.agent skills folder under that directory. Same name or identical content = one duplicate group.

link: symlinks each skill folder in --hub into every --target (default ~/.claude/skills, ~/.agents/skills,
~/.gemini/antigravity/skills). Anything already at a target path that is not the right symlink is moved, never deleted, to
~/Archive/skills-replaced-<stamp>/, with a manifest.tsv and restore.sh. Without --apply nothing changes.
"""
import argparse, csv, datetime, hashlib, re, shutil, sys
from pathlib import Path

USER_ROOTS = {  # tool label -> skills folder relative to $HOME
    "claude": ".claude/skills",
    "agents": ".agents/skills",
    "cursor": ".cursor/skills",
    "codex": ".codex/skills",
    "antigravity": ".gemini/antigravity/skills",
    "gemini": ".gemini/skills",
    "gemini-config": ".gemini/config/skills",
    "grok": ".grok/skills",
}
REPO_DIRS = {".claude/skills": "claude", ".agents/skills": "agents", ".cursor/skills": "cursor",
             ".codex/skills": "codex", ".agent/skills": "antigravity"}
DEFAULT_TARGETS = [".claude/skills", ".agents/skills", ".gemini/antigravity/skills"]
SKIP = {".git", "node_modules", ".venv", "venv", "__pycache__", "Library"}
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def front_matter(text):
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    out = {}
    for ln in m.group(1).splitlines():
        k, sep, v = ln.partition(":")
        if sep and not ln.startswith((" ", "\t")):
            out[k.strip()] = v.strip().strip("'\"")
    return out


def find_skills(root):
    root = Path(root)
    if not root.is_dir():
        return
    stack = [root]
    while stack:
        d = stack.pop()
        try:
            entries = list(d.iterdir())
        except OSError:
            continue
        for p in entries:
            if p.name == "SKILL.md" and p.is_file():
                yield p
            elif p.is_dir() and p.name not in SKIP:
                stack.append(p)


def repo_roots(base):
    """Every <repo>/.claude/skills (etc.) under base, without descending into the skills folders themselves."""
    base = Path(base).expanduser()
    for rel, tool in REPO_DIRS.items():
        for hit in base.rglob(rel):
            if not any(part in SKIP for part in hit.relative_to(base).parts):
                yield tool, hit


def issues_for(path, fm):
    folder, name = path.parent.name, fm.get("name", "")
    probs = []
    if not name:
        probs.append("no name")
    elif name != folder:
        probs.append(f"name '{name}' != folder '{folder}'")
    if name and not KEBAB.match(name):
        probs.append("name not kebab-case")
    if not fm.get("description"):
        probs.append("no description")
    return probs


def inventory(a):
    home = Path.home()
    roots = [(tool, home / rel) for tool, rel in USER_ROOTS.items()]
    roots += [("extra", Path(r).expanduser()) for r in a.root]
    if a.scan_repos:
        roots += list(repo_roots(a.scan_repos))
    rows, seen = [], set()
    for tool, root in roots:
        for skill in find_skills(root):
            real = skill.resolve()
            if real in seen:  # same file reached through a symlink: already counted
                continue
            seen.add(real)
            text = skill.read_text(errors="replace")
            fm = front_matter(text)
            rows.append({"name": fm.get("name") or skill.parent.name, "tool": tool, "path": str(skill.parent),
                         "sha": hashlib.sha256(text.strip().encode()).hexdigest()[:12],
                         "issues": "; ".join(issues_for(skill, fm)), "description": fm.get("description", "")[:120]})
    by_name, by_sha = {}, {}
    for r in rows:
        by_name.setdefault(r["name"], []).append(r)
        by_sha.setdefault(r["sha"], []).append(r)
    for r in rows:
        same_name, same_sha = by_name[r["name"]], by_sha[r["sha"]]
        if len(same_sha) > 1:
            r["duplicate"] = "identical copy" if same_sha[0] is not r else "identical (first seen)"
        elif len(same_name) > 1:
            r["duplicate"] = "variant: merge"
        else:
            r["duplicate"] = ""
    rows.sort(key=lambda r: (r["name"], r["tool"]))
    cols = ["name", "tool", "duplicate", "issues", "sha", "path", "description"]
    if a.out:
        out = Path(a.out).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {out}")
    for r in rows:
        print(f"{r['name']:<40} {r['tool']:<12} {r['duplicate'] or '-':<22} {r['issues'] or 'ok'}")
    dups = sum(1 for v in by_name.values() if len(v) > 1)
    print(f"\n{len(rows)} skills, {len(by_name)} distinct names, {dups} names with more than one copy, "
          f"{sum(1 for r in rows if r['issues'])} with front-matter issues")


def link(a):
    hub = Path(a.hub).expanduser().resolve()
    skills = sorted(p.parent for p in hub.glob("*/SKILL.md"))
    if not skills:
        sys.exit(f"no <name>/SKILL.md folders in {hub}")
    home = Path.home()
    targets = [home / t for t in (a.target or DEFAULT_TARGETS)]
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    archive = home / "Archive" / f"skills-replaced-{stamp}"
    moves, links = [], []
    for target in targets:
        for skill in skills:
            dest = target / skill.name
            if dest.is_symlink() and dest.resolve() == skill:
                continue
            if dest.exists() or dest.is_symlink():
                moves.append((dest, archive / target.relative_to(home).as_posix().replace("/", "_") / skill.name))
            links.append((dest, skill))
    for src, dst in moves:
        print(f"{'ARCHIVE' if a.apply else 'would archive'} {src} -> {dst}")
    for dest, skill in links:
        print(f"{'LINK' if a.apply else 'would link'} {dest} -> {skill}")
    if not links:
        print("every target already points at the hub; nothing to do")
        return
    if not a.apply:
        print(f"\nDRY RUN: {len(links)} links, {len(moves)} existing entries to archive. Re-run with --apply.")
        return
    if moves:
        archive.mkdir(parents=True)
        with (archive / "manifest.tsv").open("w") as man, (archive / "restore.sh").open("w") as rs:
            rs.write("#!/usr/bin/env bash\nset -euo pipefail\n")
            for src, dst in moves:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
                man.write(f"{src}\t{dst}\n")
                rs.write(f'rm -f "{src}"; mv "{dst}" "{src}"\n')
    for dest, skill in links:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.symlink_to(skill, target_is_directory=True)
    print(f"\nlinked {len(links)}; archived {len(moves)}" + (f" to {archive} (undo: bash {archive}/restore.sh)" if moves else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    inv = sub.add_parser("inventory", help="list every skill and its duplicates (read-only)")
    inv.add_argument("--root", action="append", default=[], help="extra folder to scan (repeatable)")
    inv.add_argument("--scan-repos", help="also scan repo-level skills folders under this directory")
    inv.add_argument("--out", help="write the full report as CSV")
    ln = sub.add_parser("link", help="symlink the canonical hub into each tool's skills folder")
    ln.add_argument("--hub", required=True, help="folder of <name>/SKILL.md skills (the config repo's skills/)")
    ln.add_argument("--target", action="append", help="skills folder relative to $HOME (repeatable; default: claude, agents, antigravity)")
    ln.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    inventory(a) if a.cmd == "inventory" else link(a)


if __name__ == "__main__":
    main()
