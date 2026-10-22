# Chairman v0.1: crosswalk to work done (2026-10-22)

| v0.1 agent | Status | Evidence / blocker |
|---|---|---|
| INV-DRIVE | Done, Google | 145,997 items; OneDrive 2,826 items. Missing: md5 hashes, which need the Apps Script run inside the owner's account |
| INV-MAC | Not run | The cloud session can't reach the Mac. Scripts are ready (scripts_native) |
| INV-REPO | Partial | 19 Connected-Energy-AI repos read. connectedagents-ai and powerconnectionai repos are not attached |
| INV-CLOUD | Not started | Needs read-only credentials from 1Password (owner) |
| INV-LLM / EXT-LLM-MEMORY | Partial | Claude (33 artifacts), Notion and Perplexity files read. Exports for ChatGPT, Grok, Perplexity threads and personal Copilot are owner actions |
| EXT-REPO-DOCS | Partial | 1,575 docs from 19 repos. Code is now being retrieved for the Cursor regex/dedup comparison |
| EXT-DRIVE-DOCS | Partial | Desktop OCR read 801 files. QuickBooks/tax regex: 2,719 bank statement rows, 1,740 tax rows |
| REC-DEDUP-DOCS | Partial | 12,842 probable duplicate groups (name+size+date). Exact-hash dedup needs md5/sha256 from the Apps Script and Mac runs |
| REC-ONTOLOGY | Done, as a dry run | 49 regex rules, 88% coverage. Being retargeted to the two roots |
| REC-ENTITY | Not started | Inputs: canonical-dataset.yaml and personnel-master-registry (reference only) |
| Phase 4: Principal review | Waiting on the owner | One "yes" for the plan (moves), plus "go copy" (save outputs to Drive) |
| DIST-* | Not started | Supabase/Neo4j/Obsidian targets are OPEN in principal_decisions.yaml |
| GOV-BRIEF | Manual | Master plan sheet + "00 READ FIRST" task board. The nightly routine is disabled because it can't carry connectors (owner must add them in claude.ai/code) |

## Conflicts to resolve
1. **System of record.** v0.1 says Supabase. The owner's rule for files is Drive, with two roots. Proposal: Drive holds
   files and evidence; Supabase `core.*` holds structured registers (entities, accounts, matters, documents index).
   This is the owner's decision.
2. **Mac read scope.** v0.1 blocks paths outside ~/Developer, ~/Documents and ~/Desktop unless named. The owner has
   named Desktop Review, DESKTOP SORT, the SSDs and "all of my Mac", so those are recorded in principal_decisions.yaml.
3. **Victoria's MacBook Air** is a v0.1 default the owner has not named. It stays OPEN.
