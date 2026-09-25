#!/usr/bin/env python3
"""ingest_library.py — file exports from any AI tool into the central ai-library, de-duplicated.

    python3 ingest_library.py --source perplexity ~/Downloads/perplexity-export            # DRY RUN
    python3 ingest_library.py --source perplexity ~/Downloads/perplexity-export --apply
    python3 ingest_library.py --source chatgpt --account team ~/Downloads/chatgpt-export.zip --apply   # zips are unpacked
    python3 ingest_library.py --source grok --account personal ~/Downloads/grok-export --apply

Layout written under --library (default ~/Archive/ai-library-raw, a PRIVATE store that is not a git repo):
    skills/<name>/                   any folder that contains SKILL.md (portable Agent Skills format)
    sources/<source>/<account>/<kind>/<file>   everything else, kind = docs | forms | templates | data | code | media | other
    catalog.json                     one entry per unique file (sha256), with every original path it came from
    INDEX.md                         regenerated table of contents

Copies only; never moves or deletes originals. Identical content (same sha256) is stored once.
Secrets-looking files (.env, keys, credentials) and symlinks are skipped, also inside skill folders.
A skill whose content is already in the library is recorded as a duplicate, not copied again.
Every catalog entry keeps its provenance: one {source, account, origin} record per place it was found.
A ChatGPT export's conversations.json (or conversations-NNN.json) is also split into one Markdown file per
conversation (sources/.../chats/); re-ingesting a newer export updates each conversation's file in place.
"""
import argparse, datetime, hashlib, json, os, re, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path

KINDS = {
    "docs": {".md", ".markdown", ".txt", ".pdf", ".docx", ".doc", ".rtf", ".html", ".htm", ".pptx", ".key"},
    "data": {".csv", ".tsv", ".xlsx", ".xls", ".json", ".jsonl", ".yaml", ".yml", ".xml", ".sqlite"},
    "code": {".py", ".js", ".ts", ".tsx", ".jsx", ".sh", ".ipynb", ".sql", ".go", ".rs", ".swift", ".css"},
    "media": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".mp3", ".mp4", ".wav", ".mov"},
}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".next", "dist", "build", ".DS_Store"}
SECRET = re.compile(r"(^\.env)|(\.pem$)|(\.p12$)|(^id_(rsa|ed25519))|credential|secret|password|token", re.I)
CHATGPT_CONVERSATIONS = re.compile(r"conversations(-\d+)?\.json")


def looks_secret(p: Path) -> bool:
    """Name-based secret check; a .key file is a secret only if it is a PEM key (Keynote .key files are not)."""
    if SECRET.search(p.name):
        return True
    if p.suffix.lower() == ".key":
        try:
            with p.open("rb") as f:
                return f.read(64).lstrip().startswith(b"-----BEGIN")
        except OSError:
            return True
    return False


def kind_of(p: Path) -> str:
    name = p.name.lower()
    if re.search(r"\b(form|intake|questionnaire|application|checklist)\b", name.replace("_", " ").replace("-", " ")):
        return "forms"
    if "template" in name or p.suffix.lower() in {".dotx", ".potx", ".xltx"}:
        return "templates"
    for k, exts in KINDS.items():
        if p.suffix.lower() in exts:
            return k
    return "other"


def slug(s: str) -> str:
    s = re.sub(r"[^\w.\- ]+", "", s).strip().replace(" ", "-")
    return re.sub(r"-{2,}", "-", s)[:120] or "untitled"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def skip_in_copy(p: Path) -> bool:
    return p.name in SKIP_DIRS or p.is_symlink() or (p.is_file() and looks_secret(p))


def skill_files(d: Path):
    """Files a skill copy would contain, relative to d, in a stable order."""
    out = []
    for dirpath, dirnames, filenames in os.walk(d):
        base = Path(dirpath)
        dirnames[:] = sorted(x for x in dirnames if not skip_in_copy(base / x))
        out += [base / f for f in sorted(filenames) if not skip_in_copy(base / f)]
    return out


def skill_hash(d: Path) -> str:
    h = hashlib.sha256()
    for f in skill_files(d):
        h.update(f.relative_to(d).as_posix().encode() + b"\0" + sha256(f).encode() + b"\n")
    return h.hexdigest()


def add_origin(entry: dict, prov: dict):
    if prov not in entry["origins"]:
        entry["origins"].append(prov)


def split_chatgpt(path: Path, out: Path, apply: bool) -> int:
    """ChatGPT export → one Markdown file per conversation, named by conversation id. Other formats stay raw JSON."""
    try:
        convs = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return 0
    if not (isinstance(convs, list) and convs and isinstance(convs[0], dict) and "mapping" in convs[0]):
        return 0
    n = 0
    for c in convs:
        msgs = []
        for node in (c.get("mapping") or {}).values():
            m = node.get("message") or {}
            parts = (m.get("content") or {}).get("parts") or []
            text = "\n".join(p for p in parts if isinstance(p, str)).strip()
            role = (m.get("author") or {}).get("role")
            if text and role in ("user", "assistant"):
                msgs.append((m.get("create_time") or 0, role, text))
        if not msgs:
            continue
        msgs.sort(key=lambda x: x[0])
        created = datetime.datetime.fromtimestamp(c.get("create_time") or 0).strftime("%Y-%m-%d")
        title = c.get("title") or "untitled"
        body = [f"# {title}", "", f"_{created} · ChatGPT export_", ""]
        body += [f"**{r}:**\n\n{t}\n" for _, r, t in msgs]
        if apply:
            out.mkdir(parents=True, exist_ok=True)
            ident = slug(str(c.get("id") or c.get("conversation_id") or f"{created}-{title}"))
            dest = out / f"{created}-{slug(title)[:80]}--{ident}.md"
            tmp = dest.with_name(dest.name + ".tmp")
            tmp.write_text("\n".join(body), encoding="utf-8")
            os.replace(tmp, dest)  # the new copy is complete before any older one is removed
            for old in out.glob(f"*--{ident}.md"):  # same conversation from an earlier export, under an older title
                if old != dest:
                    old.unlink()
        n += 1
    return n


class NoRoom(Exception):
    pass


def ensure_room(dest: Path, need: int, min_free_gb: float):
    """Stop before a copy that would leave less than min_free_gb free on dest's disk."""
    probe = dest
    while not probe.exists():
        probe = probe.parent
    free = shutil.disk_usage(probe).free
    if free - need < min_free_gb * 1024**3:
        raise NoRoom(f"STOP: copying {need / 1e9:.2f} GB more would leave less than {min_free_gb} GB free on {probe} "
                 f"({free / 1e9:.1f} GB free now). Nothing further was copied. Use --library /Volumes/<SSD>/ai-library-raw.")


def tree_size(d: Path) -> int:
    return sum(f.stat().st_size for f in skill_files(d))


def unpack_zip(inp: Path, tmp_parent: Path, min_free_gb: float) -> Path:
    """Extract next to the library (not into the system temp dir), after checking the unpacked size fits."""
    with zipfile.ZipFile(inp) as z:
        members = z.infolist()
        for m in members:  # zipfile already strips "../" and leading "/", but refuse such archives outright
            p = Path(m.filename)
            if p.is_absolute() or ".." in p.parts or m.filename.startswith(("/", "\\")):
                raise SystemExit(f"refusing {inp}: member {m.filename!r} points outside the archive")
        ensure_room(tmp_parent, sum(m.file_size for m in members), min_free_gb)
        t = Path(tempfile.mkdtemp(prefix=".ingest-", dir=tmp_parent))
        try:
            z.extractall(t)
        except BaseException:
            shutil.rmtree(t, ignore_errors=True)  # don't leave a half-extracted archive behind
            raise
    return t


def walk(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        yield Path(dirpath), dirnames, filenames


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", type=Path)
    ap.add_argument("--source", required=True, help="perplexity | perplexity-computer | chatgpt | openai-platform | grok | xai-console | claude | codex | cursor | copilot | devin | antigravity | other")
    ap.add_argument("--account", default="default", help="which login this export came from, e.g. personal | team | teams | enterprise | api | work-email")
    ap.add_argument("--library", type=Path, default=Path.home() / "Archive/ai-library-raw",
                    help="raw export store: private, NOT a git repo. Promote reviewed items into the ai-library repo by hand")
    ap.add_argument("--min-free-gb", type=float, default=15, help="refuse to copy if less than this would remain free")
    ap.add_argument("--allow-git", action="store_true", help="allow --library inside a git work tree (only for sanitized input)")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    lib = a.library.expanduser()
    probe = lib if lib.exists() else lib.parent
    while not probe.exists():
        probe = probe.parent
    in_git = subprocess.run(["git", "-C", str(probe), "rev-parse", "--is-inside-work-tree"],
                            capture_output=True, text=True).stdout.strip() == "true"
    if in_git and not a.allow_git:
        sys.exit(f"refusing: {lib} is inside a git work tree. Raw exports can hold PII, privileged material or credentials; "
                 "keep them in a private store and promote reviewed items by hand (or pass --allow-git for sanitized input).")
    catalog_path = lib / "catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8")) if catalog_path.exists() else {}
    by_hash = {e["sha256"]: e for e in catalog.values()}
    today = datetime.date.today().isoformat()
    stats = {"new": 0, "duplicate": 0, "skipped-secret": 0, "skills": 0}
    tmpdirs = []
    roots = []
    stopped = None
    try:
        for inp in a.inputs:
            inp = inp.expanduser()
            if inp.suffix.lower() == ".zip":
                t = unpack_zip(inp, probe, a.min_free_gb); tmpdirs.append(t)
                roots.append((t, inp))
            elif inp.exists():
                roots.append((inp, inp))
            else:
                print(f"missing: {inp}", file=sys.stderr)

        for root, origin in roots:
            files = [root] if root.is_file() else None
            if files is None:
                files = []
                for d, dirnames, filenames in walk(root):
                    if "SKILL.md" in filenames and d != root.parent:
                        dirnames[:] = []
                        if (d / "SKILL.md").is_symlink():  # the copy would have no entry point
                            print(f"skip-skill {d} (SKILL.md is a symlink)")
                            continue
                        h = skill_hash(d)
                        prov = {"source": a.source, "account": a.account, "origin": str(origin / d.relative_to(root))}
                        if h in by_hash:
                            stats["duplicate"] += 1
                            add_origin(by_hash[h], prov)
                            continue
                        dest = lib / "skills" / slug(d.name)
                        k = 1
                        while dest.exists():
                            dest = dest.with_name(f"{slug(d.name)}-{k}"); k += 1
                        print(f"skill      {d} → {dest.relative_to(lib)}")
                        stats["skills"] += 1
                        entry = {"sha256": h, "path": str(dest.relative_to(lib)), "source": a.source, "account": a.account,
                                 "kind": "skill", "title": d.name, "ingested": today, "bytes": tree_size(d), "origins": [prov]}
                        by_hash[h] = entry
                        if a.apply:
                            ensure_room(dest, entry["bytes"], a.min_free_gb)
                            shutil.copytree(d, dest, ignore=lambda src, names: [n for n in names if skip_in_copy(Path(src) / n)])
                            catalog[entry["path"]] = entry
                        continue
                    files += [d / f for f in filenames if f != ".DS_Store"]
            for f in files:
                if f.is_symlink():
                    continue
                if looks_secret(f):
                    stats["skipped-secret"] += 1
                    print(f"skip-secret {f}")
                    continue
                h = sha256(f)
                orig = str(origin / f.relative_to(root)) if root.is_dir() else str(origin)
                prov = {"source": a.source, "account": a.account, "origin": orig}
                chats_dir = lib / "sources" / slug(a.source) / slug(a.account) / "chats"
                if h in by_hash:
                    stats["duplicate"] += 1
                    add_origin(by_hash[h], prov)
                    if CHATGPT_CONVERSATIONS.fullmatch(f.name):  # same export, maybe another account: still split it here
                        stats["chats"] = stats.get("chats", 0) + split_chatgpt(f, chats_dir, a.apply)
                    continue
                k = kind_of(f)
                dest = lib / "sources" / slug(a.source) / slug(a.account) / k / slug(f.name)
                n = 1
                while dest.exists():
                    dest = dest.with_name(f"{dest.stem}-{n}{dest.suffix}"); n += 1
                print(f"new        [{k:9}] {orig} → {dest.relative_to(lib)}")
                stats["new"] += 1
                entry = {"sha256": h, "path": str(dest.relative_to(lib)), "source": a.source, "account": a.account, "kind": k,
                         "title": f.stem, "ingested": today, "bytes": f.stat().st_size, "origins": [prov]}
                by_hash[h] = entry
                if a.apply:
                    ensure_room(dest, f.stat().st_size, a.min_free_gb)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, dest)
                    catalog[entry["path"]] = entry
                if CHATGPT_CONVERSATIONS.fullmatch(f.name):
                    stats["chats"] = stats.get("chats", 0) + split_chatgpt(f, chats_dir, a.apply)

    except NoRoom as e:  # keep the catalog consistent with what was already copied
        stopped = str(e)

    if a.apply:
        lib.mkdir(parents=True, exist_ok=True)
        catalog_path.write_text(json.dumps(catalog, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
        lines = ["# AI library index", "", f"_Regenerated {today} by ingest_library.py: {len(catalog)} files._", ""]
        skills = sorted(p.name for p in (lib / "skills").glob("*") if p.is_dir()) if (lib / "skills").exists() else []
        if skills:
            lines += ["## Skills", ""] + [f"- [`{s}`](skills/{s}/SKILL.md)" for s in skills] + [""]
        groups = {}
        for e in (e for e in catalog.values() if e["kind"] != "skill"):
            groups.setdefault((e["source"], e.get("account", "default"), e["kind"]), []).append(e)
        for (src, acct, k), es in sorted(groups.items()):
            lines += [f"## {src} · {acct} · {k} ({len(es)})", ""]
            lines += [f"- [{e['title']}]({e['path'].replace(' ', '%20')})" for e in sorted(es, key=lambda e: e["title"].lower())]
            lines.append("")
        for chats in sorted(lib.glob("sources/*/*/chats")):
            src, acct = chats.parts[-3], chats.parts[-2]
            files = sorted(chats.glob("*.md"))
            lines += [f"## {src} · {acct} · chats ({len(files)})", ""]
            lines += [f"- [{f.stem}]({f.relative_to(lib).as_posix().replace(' ', '%20')})" for f in files] + [""]
        (lib / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")

    for t in tmpdirs:
        shutil.rmtree(t, ignore_errors=True)
    print("\n" + "  ".join(f"{k}: {v}" for k, v in stats.items()))
    if not a.apply:
        print("Dry run. Re-run with --apply to copy into", lib)
    if stopped:
        sys.exit(stopped + " Files copied before the stop are recorded in catalog.json.")


if __name__ == "__main__":
    main()
