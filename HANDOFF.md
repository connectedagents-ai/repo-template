# HANDOFF — 2026-10-22

This repository is **public**. Case, account, incident and personal details are kept out of it; the full handoff
is in the owner's private Google Drive (the litigation production folder → `07 Working` → "HANDOFF 2026-10-22 …").

## Done in this repo
- PR #1 (merged): client onboarding SOP, discovery tools, consolidation runbook.
- Default branch renamed to `main`.

## In progress
- `ops/dedup/drive_topic_search.py` and `ops/dedup/legal_consolidate_plan.py` exist locally but are **not committed**:
  they contain matter-specific names. Move them to a private repo, or make the topic list a config file loaded from
  outside the repo, before committing.
- `ops/security/scan_infected_repos.sh` (on branch `claude/code-chairman-repo-org-ocoe3d`): line 16 needs
  `${owner}` instead of `$owner…` (the ellipsis breaks `set -u`), and empty repos must be skipped (a 409 response
  is counted as a hit today).

## Open decisions (owner)
- Make this repository private, or confirm it should stay public.
- Merge the five security-cleanup PRs listed in the private handoff.

## Next step
Fix the two script issues above in a small PR; keep matter names out of public code.

## Standing rules for agents
1. Search every source (repo, Google Drive incl. shared drives, the Extreme SSD, Notion, mail) with filename and regex
   searches before calling anything unknown.
2. When something won't reconcile, show the working: question, steps, each document checked, what conflicts or is
   missing, and the search that would settle it.
3. Don't hand questions back when the answer is in the data; name a professional only where a step legally requires one,
   and still give the analysis.
4. If a tool can't search, move files or archive duplicates, say so immediately.
