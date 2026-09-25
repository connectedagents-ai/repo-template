# Naming conventions and rename backlog

**Principle:** a name says *what the thing is*. Everything else — that it's developer material, its status, its owner, its
version, its date — goes in **tags/metadata**, not in the name. Informal working labels get replaced by professional terms.

## 1. Informal labels → professional terms
| Informal (today) | Professional replacement | Notes |
|---|---|---|
| "golden artifacts", "golden", "gold copy" | **reference** (or **canonical** / **source of truth** in prose) | folder `reference/`; tag `status: reference` |
| `dev` / `dev-` / `development-` / `developer-` prefix meaning "developer-type file" | **drop the prefix**; add tag `type: engineering` | "dev" only means the *development environment* (vs staging/prod) |
| `-a0`, `-a1`, `m0-m1` (draft/iteration markers) | drop; use git branches/tags or `status: draft` | |
| `-v2`, `-final`, `-new`, `copy`, `(1)` | drop; version lives in git or `version:` metadata | the older copy goes to archive |
| dates in repo/project names (`_2026-07-26`, `_20260810t215407z`) | drop from repo names; allowed as **prefix** on dated documents only | documents: `YYYY-MM-DD_<subject>` |
| `-ingestion` suffix for raw dumps | `sources/` or `imports/` folder inside the owning repo | |
| stack-in-name duplicates (`dev-cursorcloudagents-dev-*`) | folder names inside one repo | |

## 2. Rules by object
| Object | Pattern | Example |
|---|---|---|
| GitHub repo | `<domain>` or `<domain>-<component>`, kebab-case, no prefixes/dates/versions | `onewish-os`, `power-connection`, `voice-agents` |
| Folder in a repo | kebab-case, plural for collections | `apps/`, `packages/`, `agents/`, `reference/` |
| Code file | the language's convention (`snake_case.py`, `kebab-case.ts`, `PascalCase.tsx` components) | |
| Document | `YYYY-MM-DD_<Entity>_<Subject>_<DocType>.ext` when dated; `<Entity>_<Subject>_<DocType>.ext` when evergreen | `2026-09-24_PowerConnection_Q3-Board-Update_Deck.pptx` |
| Agent | `<role>-agent` | `chairman-agent`, `intake-agent` |
| Skill | verb-first kebab-case | `review-contract`, `summarize-deposition` |
| Branch | `<type>/<slug>` | `feat/intake-form`, `chore/rename-dev-repos` |

Allowed characters: letters, digits, `-`, `_`, `.`. No spaces in code/repo names; no emoji; ≤ 60 chars; fix typos when renaming.

## 3. Standard tags / metadata (replace what names used to encode)
`type` (engineering · document · data · design · legal · finance) · `domain` · `entity` (company) · `project` ·
`status` (active · draft · reference · archived) · `sensitivity` (public · internal · confidential · privileged) · `owner` · `source` (tool/account it came from).
GitHub: repo **topics** + description. Drive/OneDrive: labels/properties. Mac: Finder tags. Library: front matter.

## 4. Rename backlog (seen so far — extend from the inventories)
| Current | Proposed | Reason |
|---|---|---|
| `dev-*` repos (~40), `development-onewish-dev-*` (~30), `developer-*` | fold into domain repos (see MIGRATION-PLAN.md) — no prefixed survivors | informal "dev" marker |
| `development-onewish-dev-onewis` | fold into `onewish-os` | truncated name |
| `development-onewish-claud-cursor-provinence-2026-06-01` | `onewish-os/docs/provenance/` | typos (claud, provinence) + date |
| `development-onewish-dev-onewish-custom-tranformations-template-cust-yyyymmdd*` | `onewish-os/templates/custom-transformations/` | typo (tranformations) + placeholder in name |
| `dev-dev-chatgpt-skill-builder-skill` | `ai-library/skills/build-chatgpt-skill/` | doubled prefix |
| `dev-agents-multi-agent-swarms*` (no separator) | `agent-lab/swarms/<name>/` | run-together names |
| CEA `powermedmarkeetingai-v0-modern-website-design` | `power-connection/apps/powermed-marketing-site/` | typo + tool marker (v0) |
| CEA `my-vercel-neon-app-litigatioinforce1` | archive | typo + scaffold name |
| `olive-prairie-acorn-kite`, `turbo-crane-mountain-wave` | inspect → archive or give a real name | auto-generated names |
| any file/folder named "golden …" | `reference/…` | informal label |
| `MASTER_VAULT_2026` (Chairman target folder) | decide with the canonical taxonomy (no year in a permanent root) | dated root |

Renames are done by script with a before→after manifest (and GitHub redirects for repos), never by hand one at a time.
