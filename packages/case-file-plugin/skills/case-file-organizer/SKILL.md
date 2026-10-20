---
name: case-file-organizer
description: Find every document related to a lawsuit across the Mac, the Extreme SSD, Google Drive (including shared drives) and iCloud, tag each one with the people and companies it mentions, move exact duplicates aside, and copy the rest into a numbered case-file folder on the SSD. Use when the owner asks to gather, sort, clean up or organize files for a case, a motion, discovery, a deposition, trial or litigation finance.
---

# Case-file organizer

Everything here follows the repo's AGENTS.md §4, §6 and §7. Case material never goes into a git repo or a public
link. It stays on "/Volumes/Extreme SSD/cases/<matter>/". If the SSD is not mounted, stop and say so.

## Inputs (local files on the SSD, never in the repo)
- `/Volumes/Extreme SSD/cases/<matter>/entities.txt`: one `Name: regex` per line for every party, person, company,
  customer, project and law firm, with name variants (maiden names, nicknames, DBAs, email domains, EINs).
- Optional `terms.txt`: extra `category: regex` lines for matter words.
If entities.txt is missing, build it with the owner from their case summary first and show it for approval.

## Steps (preview first, then the owner's OK)
1. Tools check: `python3 --version`, the SSD mounted, `git -C ~/Code/repo-template pull`.
2. Preview:
   ```
   S="/Volumes/Extreme SSD/cases/<matter>"
   python3 ~/Code/repo-template/ops/financial-discovery/find_financial_records.py \
     --categories ~/Code/repo-template/ops/financial-discovery/litigation_categories.txt --layout type \
     --entities "$S/entities.txt" --since <first year of events> --out "$S/run-$(date +%Y%m%d)" --move-duplicates \
     ~/Documents ~/Desktop ~/Downloads ~/Library/CloudStorage "$HOME/Library/Mobile Documents" "/Volumes/Extreme SSD"
   ```
   Show summary.md, the counts per entity (from index.csv), and the duplicates it would move. Wait for OK.
3. Apply: the same command plus `--apply`. It copies unique files into `collection/<NN-type>/<year>/`, moves exact
   duplicates into `_duplicates/` on their own drive (undo: `restore_duplicates.sh`), and puts possible
   attorney-client files into `collection/_privilege-review/`. Originals are never renamed or deleted.
4. Report with the confirmation list: files per folder, files per entity, privilege-review count, name-only
   (cloud) matches the owner may need to make available offline, and the path to index.csv.

## Folder map (from litigation_categories.txt)
01 pleadings and court · 02 agreements · 03 correspondence · 04 transcripts and recordings · 05 damages and
financial · 06 customers and projects · 07 people and employment · 08 timeline · 09 discovery · 10 deposition prep ·
11 trial and jury · 12 litigation finance · 13 media and social · 14 marketing and product.
