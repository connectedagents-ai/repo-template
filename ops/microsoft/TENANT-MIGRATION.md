# Microsoft tenants: migration status and plan (OneDrive, SharePoint, mail)

Three Microsoft identities are in play. Status is from evidence found on 2026-09-24 (email reports, the connected
Microsoft 365 account and Linear). "Unknown" means nothing could be checked from here, not that nothing exists.

| Identity | Kind | Mail + calendar | OneDrive / SharePoint files | Evidence |
|---|---|---|---|---|
| `rbailey@netzerolending.io` | Work tenant (Entra ID) | **Migrated to Google Workspace** (powerconnection.com) on 2026-05-21 with Google's Data Migration Service: 2 users, 6,220 emails found, **6,213 migrated, 7 failed**; 2,363 calendar events and 1 contact migrated | **Not migrated as far as can be seen.** No file-migration report exists and the tenant is not connected here | Google migration report e-mail (2026-05-22, execution `5poa75hsvct8o`, per-item CSVs attached). Bounces ("Undeliverable", stale `IMCEAEX…` addresses) from the tenant's Exchange through May 2026 show the mailbox was still in use |
| `rbailey.713@icloud.com` | Personal Microsoft account (OneDrive Personal) | n/a (mail is iCloud) | **Unknown.** Not connected here and no migration evidence found | none |
| `rbailey@onewishlabs.com` | Work tenant (the one connected here) | Active | Active: 15+ SharePoint sites and OneDrive, with heavy duplication (see the connector inventory) | connected Microsoft 365 account |

Related Linear work: POW-149 (corpus inventory across Mac, OneDrive, Drive, SharePoint: In Progress), POW-141 (iCloud overflow
to SharePoint via rclone: In Progress), POW-153 (SharePoint bookkeeping sites), POW-36 (mail hub decision), project P-POW-57
(Digital Asset Catalog & SharePoint Library). Decision D2 in `docs/CLOUD-ARCHITECTURE.md` (which tenant is primary) is still open.

## Plan (each step is read-only or a dry run until you approve the next)

1. **Close out the mail migration.** Open the 2026-05-22 report e-mail, download `Migration_Report_…csv`, and list the 7 failed
   items (usually oversized or corrupt messages). Re-run Google's Data Migration Service for those, or export them from Outlook.
   Keep the netzerolending.io mailbox until step 5.
2. **Connect the file sources** (once): `bash ops/dedup/connect_cloud.sh` → option 3 for `onedrive-netzerolending`,
   `onedrive-msa` (the rbailey.713@icloud.com account) and `onedrive-onewishlabs`; option 4 for each SharePoint site worth
   checking (e.g. `sp-centralfilecloud`, `sp-legalmatters`). Sign-in only; nothing is copied.
3. **Inventory and dedup preview across all of them, with the Mac, Google Drive and iCloud:**
   `bash ops/dedup/start_here.sh` and answer **y** to "include connected cloud accounts". OneDrive and SharePoint are
   compared by Microsoft's own checksum (QuickXorHash), so nothing downloads. Legal-looking paths are flagged and never moved.
   Result: `PLAN.md` with what exists only in netzerolending / the personal OneDrive, and what is already duplicated elsewhere.
4. **Migrate what exists only in the old tenant / personal OneDrive** to the target chosen in D2 (Google Drive or the
   OneWish Labs SharePoint), as a **copy** (never a move), using only an **approved file list**, never the whole account:
   - Build the candidate list from the step 3 run folder (`<run>`): files in the old tenant that have no copy anywhere
     else (one copy when the only duplicates are inside the old tenant) and are **not** flagged legal:
     ```bash
     python3 - <run> onedrive-netzerolending > ~/migrate-netzerolending.txt <<'PY'
     import csv, glob, sys
     from collections import defaultdict
     run, remote = sys.argv[1], sys.argv[2]
     groups, group_of = defaultdict(list), {}
     for r in csv.DictReader(open(f"{run}/duplicates.csv")):
         groups[r["group"]].append(r["path"]); group_of[r["path"]] = r["group"]
     copied = set()  # one copy per duplicate group; skip groups that already have a copy outside this account
     for inv in glob.glob(f"{run}/inventory-{remote}*.csv"):
         for r in csv.DictReader(open(inv)):
             g = group_of.get(r["path"])
             if r["legal"] != "0" or g in copied:
                 continue
             if g and any(not p.startswith(remote + ":") for p in groups[g]):
                 continue
             if g:
                 copied.add(g)
             print(r["path"].split(":", 1)[1])
     PY
     ```
   - **Review the list** and delete any line that should not move (anything privileged or client-confidential). That
     reviewed file is the approved set.
   - Set the target remote once, e.g. `TARGET=sp-centralfilecloud` (or `gdrive-powerconnection`), then
     `rclone copy onedrive-netzerolending: "${TARGET}:Archive/netzerolending" --files-from ~/migrate-netzerolending.txt --dry-run`
     → review → run without `--dry-run` →
     `rclone check onedrive-netzerolending: "${TARGET}:Archive/netzerolending" --files-from ~/migrate-netzerolending.txt --one-way`
     must report 0 differences.
   - This is **not** a server-to-server copy: OneDrive → Google Drive or → another tenant are different accounts, so
     rclone streams each file through the machine running it (network traffic, not stored on its disk). Run it on a
     fast connection, or on a cloud VM for large sets.
   - Privileged legal material is excluded from this list on purpose. It goes to the litigation evidence store instead
     (with counsel), per MIGRATION-PLAN step 0.
5. **Retire the source** only after step 4 checks clean: make it read-only for 30 days, then follow
   `ops/domains/DOMAIN-CONSOLIDATION.md` (M365 domain removal order) for netzerolending.io. The personal Microsoft account
   can simply stay as a read-only archive.
6. **Dedup inside the kept tenant** (OneWish Labs SharePoint: the ~10 copies of the Tesla letter, GOLDEN-PACKET.md in 7 places,
   "(Selective Sync Conflict)" folders): `python3 ops/dedup/cloud_apply.py --plan <run>/duplicates.csv` (dry run) → approve →
   `--apply`. Duplicates move into that site's own `_Dedup-Archive/`, with an undo script; nothing is deleted.
