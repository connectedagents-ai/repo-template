#!/usr/bin/env python3
"""find_financial_records.py — find every banking, tax, investment, account and LP/business-interest record since a
given year, for a discovery request or a motion to compel. PREVIEW by default: reads files, changes nothing.

    python3 find_financial_records.py ~/Documents ~/Desktop "/Volumes/Extreme SSD"            # preview: index only
    python3 find_financial_records.py --apply ~/Documents ~/Desktop "/Volumes/Extreme SSD"    # also copy matches

Output goes to "/Volumes/Extreme SSD/financial-discovery/<stamp>/" (never the Mac's internal disk unless
--allow-internal): index.csv (every match: category, years, matched terms, privilege flag, sha256, duplicate_of),
summary.md (counts by category and year). --apply COPIES each unique match to collection/<category>/<year>/ with a
clean name "<year>_<category>_<original name>"; originals are never moved, renamed or deleted. Possibly privileged
files (attorney, counsel, work product) go to collection/_privilege-review/ for a lawyer to look at first.
--move-duplicates moves each exact duplicate (same sha256 as the kept file) into a "_duplicates" folder at the top of
the same drive (the scanned folder, or that Google Drive / shared drive), keeping its folder path; with --apply it
moves them for real and writes MOVED.tsv and restore_duplicates.sh, which puts every file back. Nothing is deleted.
Matter-specific words (party names, account numbers) belong in a local --terms file on the SSD, never in this repo:
one "category: regex" per line. --categories replaces the built-in financial categories with your own file (see
litigation_categories.txt for a case file: pleadings, agreements, correspondence, transcripts, damages, deposition and
trial material, litigation finance); --layout type files the collection by category/year. --entities is a second local file, one "Entity name: regex" per line
(legal name, DBAs, EIN); each match is tagged with its entities and, with --apply, filed under the first one. Google Drive, shared drives, OneDrive and iCloud: pass ~/Library/CloudStorage and "~/Library/Mobile Documents".
Files there are matched by file and folder name only, because reading them makes the cloud app download them onto
the Mac's internal disk; --read-cloud reads them anyway. Native Google Docs (.gdoc) are always name-only. Reads text from .txt/.csv/.md/.eml/.ofx/.qfx/.qbo/.json, .docx/.xlsx/.pptx, and .pdf
when pdftotext is installed (brew install poppler); other files are matched by name and folder only.
"""
import argparse, csv, hashlib, os, re, shlex, shutil, subprocess, sys, zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

CATEGORIES = {
    "banking": r"bank\s*statement|checking|savings|account\s*statement|wire\s*transfer|\bach\b|deposit|routing\s*number"
               r"|chase|wells\s*fargo|bank\s*of\s*america|citibank|capital\s*one|\bpnc\b|truist|frost\s*bank",
    "income-tax": r"\b1040\b|\bw-?2\b|\b1099(-?[a-z]{1,3})?\b|tax\s*return|\birs\b|tax\s*transcript|schedule\s*[ce]\b"
                  r"|\b1065\b|\b1120-?s?\b|form\s*\d{3,4}|estimated\s*tax|franchise\s*tax|turbotax|tax\s*year",
    "investments": r"brokerage|portfolio|\b401\s*\(?k\)?|\bira\b|roth|securities|dividend|capital\s*gain|schwab|fidelity"
                   r"|vanguard|e\*?trade|robinhood|merrill|morgan\s*stanley|coinbase|crypto|bitcoin|annuity|trade\s*confirm"
                   r"|qualified\s*opportunity|\bqof\b|\bqozb?\b|form\s*899[67]",
    "lp-business-interests": r"limited\s*partnership|\bl\.?p\.?\b|\bk-?1\b|partnership\s*agreement|operating\s*agreement"
                             r"|membership\s*interest|capital\s*account|capital\s*call|subscription\s*agreement"
                             r"|cap\s*table|\bllc\b|distribution\s*notice|units?\s*held|shareholder"
                             r"|certificate\s*of\s*formation|public\s*information\s*report|\bcp\s*575\b|ein\s*letter",
    "loans-debt": r"\bloan\b|mortgage|promissory\s*note|line\s*of\s*credit|\bheloc\b|credit\s*card\s*statement|\blien\b",
    "financial-statements": r"balance\s*sheet|profit\s*(and|&)\s*loss|\bp\s*&\s*l\b|income\s*statement|general\s*ledger"
                            r"|quickbooks|cash\s*flow|financial\s*statement|audit(ed)?\s*report|trial\s*balance",
    "agreements": r"non[-\s]*circumvent(ion)?|\bnda\b|non[-\s]*disclosure|confidentiality\s*agreement"
                  r"|home\s*improvement\s*contract|\bhic\b|form\s*of\s*agreement|template\s*agreement"
                  r"|lease\s*agreement|\bleas(e|ing)\b|power\s*purchase\s*agreement|\bppa\b|licens(e|ee|or)\s*agreement"
                  r"|\blicensee\b|joint\s*venture|\bjv\b|partner\s*agreement|commission\s*agreement|referral\s*agreement",
    "employment-payroll": r"\bemployees?\b|employment\s*agreement|offer\s*letter|payroll|pay\s*stub|\bw-?4\b"
                          r"|independent\s*contractor|1099-nec|gusto|\badp\b",
    "accounts-general": r"account\s*(number|summary|holder)|statement\s*period|ending\s*balance|beginning\s*balance",
}
PRIVILEGE = r"attorney[-\s]client|privileged|work\s*product|legal\s*advice|engagement\s*letter|\bcounsel\b"
CLOUD_IN_LIBRARY = {"CloudStorage", "Mobile Documents"}  # Google Drive / OneDrive / Dropbox, and iCloud Drive
COPY_NAME = re.compile(r"(\bcopy\b|\s\d{1,2}$|\(\d+\)$)", re.I)
YEAR = re.compile(r"(?<!\d)(20[0-4]\d)(?!\d)")
SKIP_DIRS = {".git", "node_modules", ".Trash", ".cache", "__pycache__", ".venv", "venv",
             ".Spotlight-V100", ".fseventsd", ".DocumentRevisions-V100", "financial-discovery", "_duplicates"}
TEXT_EXT = {".txt", ".csv", ".md", ".eml", ".ofx", ".qfx", ".qbo", ".json", ".tsv"}
ZIP_EXT = {".docx", ".xlsx", ".pptx"}
MAX_TEXT = 2_000_000


def file_text(path):
    """Searchable text from the file's content ('' when it can't be read)."""
    ext = path.suffix.lower()
    try:
        if ext in TEXT_EXT:
            with open(path, "rb") as f:
                return f.read(MAX_TEXT).decode("utf-8", "ignore")
        if ext in ZIP_EXT:
            with zipfile.ZipFile(path) as z:
                xml = " ".join(z.read(n).decode("utf-8", "ignore") for n in z.namelist()
                               if n.endswith(".xml") and ("word/" in n or "sharedStrings" in n or "slides/" in n))
            return re.sub(r"<[^>]+>", " ", xml)[:MAX_TEXT]
        if ext == ".pdf" and shutil.which("pdftotext"):
            r = subprocess.run(["pdftotext", "-l", "20", "-q", str(path), "-"], capture_output=True, timeout=60)
            return r.stdout.decode("utf-8", "ignore")[:MAX_TEXT]
    except (OSError, zipfile.BadZipFile, subprocess.SubprocessError):
        pass
    return ""


def load_categories(path):
    """Built-in financial categories, or a 'category: regex' file that replaces them (e.g. litigation_categories.txt)."""
    if not path:
        return dict(CATEGORIES)
    cats = {}
    for line in Path(path).read_text().splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            cat, rx = line.split(":", 1)
            cats[cat.strip()] = f"{cats[cat.strip()]}|{rx.strip()}" if cat.strip() in cats else rx.strip()
    return cats


def load_terms(path, categories=CATEGORIES):
    rules = {k: [re.compile(v, re.I)] for k, v in categories.items()}
    if path:
        for line in Path(path).read_text().splitlines():
            if ":" in line and not line.lstrip().startswith("#"):
                cat, rx = line.split(":", 1)
                rules.setdefault(cat.strip(), []).append(re.compile(rx.strip(), re.I))
    return rules


def load_entities(path):
    ents = {}
    for line in (Path(path).read_text().splitlines() if path else []):
        if ":" in line and not line.lstrip().startswith("#"):
            name, rx = line.split(":", 1)
            ents.setdefault(name.strip(), []).append(re.compile(rx.strip(), re.I))
    return ents


def entities_of(path, text, ents):
    """Entity names whose patterns appear, most mentions first."""
    hay = f"{path}\n{text}"
    hits = Counter({name: sum(len(rx.findall(hay)) for rx in rxs) for name, rxs in ents.items()})
    return [n for n, c in hits.most_common() if c]


def safe(name):
    return re.sub(r"[^\w .,&-]+", "", name).strip() or "unnamed"


def classify(path, text, rules):
    """(categories ranked by hits, matched terms) for one file."""
    hay = f"{path}\n{text}"
    hits, terms = Counter(), []
    for cat, rxs in rules.items():
        for rx in rxs:
            found = [m.group(0) for m in rx.finditer(hay)]
            if found:
                hits[cat] += len(found)
                terms += [t.strip() for t in found[:3]]
    return [c for c, _ in hits.most_common()], list(dict.fromkeys(terms))[:8]


def years_of(path, text, since):
    """Years >= since named in the path or content (all named years when none are that recent); else the modified year."""
    named = sorted({int(y) for y in YEAR.findall(f"{path}\n{text[:200_000]}")} & set(range(2000, datetime.now().year + 2)))
    if named:
        return [y for y in named if y >= since] or named, "content-or-name"
    return [datetime.fromtimestamp(path.stat().st_mtime).year], "modified-date"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def mark_duplicates(rows):
    """Exact copies point at one kept file: the one without "copy"/a number in its name, then the shortest path."""
    groups = {}
    for r in rows:
        groups.setdefault(r["sha256"], []).append(r)
    for same in groups.values():
        keep = min(same, key=lambda r: (bool(COPY_NAME.search(Path(r["path"]).stem)), len(r["path"]), r["path"]))
        for r in same:
            if r is not keep:
                r["duplicate_of"] = keep["path"]


def duplicates_home(path, root):
    """Top of the drive a duplicate stays on: its Google Drive, shared drive or cloud folder, else the scanned folder."""
    parts = path.parts
    if "CloudStorage" in parts:
        i = parts.index("CloudStorage")
        depth = 3 if parts[i + 2:i + 3] == ("My Drive",) else 4 if parts[i + 2:i + 3] == ("Shared drives",) else 2
        return Path(*parts[:i + depth])
    return root


def move_duplicates(rows, out, apply):
    """Move exact duplicates into <drive top>/_duplicates/<same path>; returns (planned, moved)."""
    planned = moved = 0
    log = restore = None
    if apply:
        log, restore = open(out / "MOVED.tsv", "a"), open(out / "restore_duplicates.sh", "a")
        restore.write("#!/bin/bash\n# Put back the duplicates moved by find_financial_records.py\n")
    for r in rows:
        if not r["duplicate_of"]:
            continue
        src, keep = Path(r["path"]), Path(r["duplicate_of"])
        home = duplicates_home(src, Path(r["scan_root"]))
        dest = home / "_duplicates" / src.relative_to(home)
        planned += 1
        if not apply:
            print(f"would move  {src}\n        to  {dest}\n      kept  {keep}")
            continue
        if not keep.is_file() or sha256(src) != r["sha256"] or sha256(keep) != r["sha256"]:
            print(f"  left alone (changed since the scan or kept copy missing): {src}", file=sys.stderr)
            continue
        n = 1
        while dest.exists():
            dest = dest.with_name(f"{src.stem}_{n}{src.suffix}")
            n += 1
        dest.parent.mkdir(parents=True, exist_ok=True)
        os.rename(src, dest)
        log.write(f"{r['sha256']}\t{src}\t{dest}\t{keep}\n")
        restore.write(f"mkdir -p {shlex.quote(str(src.parent))} && mv -n {shlex.quote(str(dest))} {shlex.quote(str(src))}\n")
        moved += 1
    if apply:
        log.close(); restore.close()
        os.chmod(out / "restore_duplicates.sh", 0o755)
    return planned, moved


def walk(roots):
    for root in roots:
        root = Path(root).expanduser()
        if root.is_file():
            yield root.parent, root
            continue
        for p in root.rglob("*"):
            rel = p.relative_to(root).parts
            if rel[0] == "Library" and (len(rel) < 2 or rel[1] not in CLOUD_IN_LIBRARY):
                continue
            if any(part in SKIP_DIRS or part.startswith(".") for part in rel):
                continue
            if p.is_file() and not p.is_symlink():
                yield root, p


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("roots", nargs="+", help="folders to search")
    ap.add_argument("--since", type=int, default=2022, help="first year to include (default 2022)")
    ap.add_argument("--out", type=Path, help="report folder (default: on the Extreme SSD)")
    ap.add_argument("--terms", help="local file of extra 'category: regex' lines (keep it on the SSD)")
    ap.add_argument("--categories", help="file of 'category: regex' lines that replaces the built-in financial ones")
    ap.add_argument("--layout", choices=["entity", "type"], default="entity",
                    help="collection folders: entity/category/year (default) or category/year with the entity in the index")
    ap.add_argument("--entities", help="local file of 'Entity name: regex' lines (names, DBAs, EINs; keep it on the SSD)")
    ap.add_argument("--apply", action="store_true", help="copy unique matches into the collection folder")
    ap.add_argument("--move-duplicates", action="store_true",
                    help="move exact duplicates into a _duplicates folder on the same drive (preview unless --apply)")
    ap.add_argument("--read-cloud", action="store_true", help="also read the contents of cloud-synced files")
    ap.add_argument("--allow-internal", action="store_true", help="allow --out outside /Volumes (not recommended)")
    a = ap.parse_args()

    out = a.out or Path("/Volumes/Extreme SSD/financial-discovery") / datetime.now().strftime("%Y%m%d-%H%M%S")
    if not str(out).startswith("/Volumes/") and not a.allow_internal:
        sys.exit(f"--out must be on an external drive (/Volumes/...), got {out}. Plug in the SSD.")
    if not a.out and not Path("/Volumes/Extreme SSD").is_dir():
        sys.exit("The Extreme SSD is not mounted. Plug it in, or pass --out /Volumes/<drive>/financial-discovery.")
    out.mkdir(parents=True, exist_ok=True)
    rules, priv = load_terms(a.terms, load_categories(a.categories)), re.compile(PRIVILEGE, re.I)
    ents = load_entities(a.entities)

    rows, scanned = [], 0
    for root, p in walk(a.roots):
        scanned += 1
        cloud = "/Library/CloudStorage/" in str(p) or "/Library/Mobile Documents/" in str(p)
        text = "" if cloud and not a.read_cloud else file_text(p)
        cats, terms = classify(p, text, rules)
        if not cats:
            continue
        years, basis = years_of(p, text, a.since)
        if max(years) < a.since:
            continue
        rows.append({"path": str(p), "entities": ";".join(entities_of(p, text, ents)),
                     "category": cats[0], "all_categories": ";".join(cats),
                     "years": ";".join(map(str, years)), "year_basis": basis, "matched_terms": "; ".join(terms),
                     "privilege_review": "yes" if priv.search(f"{p.name}\n{text}") else "",
                     "text_read": "yes" if text else "name-only", "size": p.stat().st_size, "sha256": sha256(p),
                     "duplicate_of": "", "scan_root": str(root)})
        if scanned % 500 == 0:
            print(f"  …{scanned} files scanned, {len(rows)} matches", file=sys.stderr)

    mark_duplicates(rows)
    fields = list(rows[0]) if rows else ["path"]
    with open(out / "index.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    copied = 0
    if a.apply:
        with open(out / "COPIED.tsv", "a") as log:
            for r in rows:
                if r["duplicate_of"]:
                    continue
                src, year = Path(r["path"]), r["years"].split(";")[-1]
                owner = "" if a.layout == "type" or not ents else (
                    safe(r["entities"].split(";")[0]) + "/" if r["entities"] else "_no-entity/")
                folder = "_privilege-review" if r["privilege_review"] else f"{owner}{r['category']}/{year}"
                dest = out / "collection" / folder / f"{year}_{r['category']}_{src.name}"
                n = 1
                while dest.exists():
                    dest = dest.with_name(f"{year}_{r['category']}_{src.stem}_{n}{src.suffix}")
                    n += 1
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                log.write(f"{r['sha256']}\t{src}\t{dest}\n")
                copied += 1

    planned = moved = 0
    if a.move_duplicates:
        planned, moved = move_duplicates(rows, out, a.apply)

    unique = [r for r in rows if not r["duplicate_of"]]
    table = Counter((r["category"], r["years"].split(";")[-1]) for r in unique)
    lines = [f"# Records since {a.since}", "",
             f"Scanned {scanned} files; {len(rows)} matches, {len(unique)} unique "
             f"({sum(1 for r in unique if r['privilege_review'])} flagged for privilege review, "
             f"{sum(1 for r in unique if r['year_basis'] == 'modified-date')} dated only by file date).", "",
             "| Category | Year | Files |", "| --- | --- | --- |"]
    lines += [f"| {c} | {y} | {n} |" for (c, y), n in sorted(table.items())]
    (out / "summary.md").write_text("\n".join(lines) + "\n")

    print("\n".join(lines))
    print(f"\nReport: {out}/index.csv and summary.md")
    print(f"Copied {copied} files into {out}/collection (originals untouched)." if a.apply
          else "Preview only: nothing was copied. Re-run with --apply to build the collection.")
    if a.move_duplicates:
        print(f"Moved {moved} of {planned} duplicates into _duplicates folders. Undo: bash "
              f"{shlex.quote(str(out / 'restore_duplicates.sh'))}" if a.apply
              else f"Would move {planned} duplicates into _duplicates folders (preview; add --apply to move).")


if __name__ == "__main__":
    main()
