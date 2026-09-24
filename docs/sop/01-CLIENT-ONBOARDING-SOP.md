# SOP-01 · Client onboarding: digital estate discovery and consolidation

**Purpose:** take a founder or CEO whose valuable data, code, AI work and accounts are scattered across devices, clouds and tools.
Produce a complete, verified inventory, a risk register and a consolidation plan, then execute it safely.
The standard is that of a CTO doing technical due diligence on an acquisition.

**Principles (non-negotiable)**
1. **Consent first.** Nothing is scanned until the engagement authorization (template T-02) is signed and the scope is listed.
2. **Read-only until approved.** Discovery never changes anything. Every change is previewed as a dry run, approved, logged and reversible.
3. **Names, not values.** Record *that* a secret exists and where. Never copy the secret itself. Values are rotated, never transcribed.
4. **Minimum data.** Inventories hold metadata (names, sizes, dates, owners, hashes), not file contents. Privileged or regulated data gets flagged, not opened.
5. **Evidence for every claim.** Each register row cites where it was observed (command output, screenshot, admin console).
6. **Archive, don't delete.** Retirement = export + read-only archive + documented date.

## Roles
| Role | Who | Responsibilities |
|---|---|---|
| Client owner | the CEO/founder | signs authorization, grants access, makes keep/migrate/retire decisions |
| Lead (fractional CTO) | engagement lead | runs the SOP, owns the registers, presents findings |
| Agent operator | Claude Code / Claude Desktop / Cowork on the client's Mac, plus cloud sessions with connectors | runs discovery scripts and connector inventories, drafts reports; asks before any change |
| Counsel (as needed) | client's attorney | privileged/regulated data handling, retention rules |

## Timeline (typical: 2–3 weeks)
| Phase | Days | Output | Gate |
|---|---|---|---|
| 0. Kickoff and consent | 1 | T-01 intake, T-02 authorization, T-05 access log opened | authorization signed |
| 1. Access and connectors | 1–2 | client's Mac runs Claude (Desktop or `claude remote-control`); connectors for Google, Microsoft 365, GitHub, Notion, Slack; admin read access to Entra/Google/GitHub | all in-scope systems reachable, or marked "out of reach" |
| 2. Discovery (read-only) | 2–4 | `ops/client-discovery/run_discovery.sh` bundle, connector inventories, AI-tool exports requested | every checklist section (SOP-02) has evidence or an explicit gap |
| 3. Mapping | 2–3 | T-03 platform register, cloud topology (`docs/CLOUD-ARCHITECTURE.md` format), repo map, data map, AI asset map | register reviewed with client |
| 4. Risk and findings | 1–2 | T-04 findings register (severity-ranked) + T-06 discovery report | P0 items (exposed secrets, no MFA, sole copies) actioned immediately |
| 5. Target design | 2–3 | identity, secrets, storage and repo topology; taxonomy and naming (`docs/NAMING-CONVENTIONS.md`); agent/skill standard (`AGENTS.md`) | client approves decisions |
| 6. Execute | 5–10 | rescue → dedup → consolidate → migrate → retire, each as dry run then apply, with manifests | each batch approved and verified |
| 7. Automate and hand over | 1–2 | scheduled audits, sorters, hygiene reports; runbook; owner training | client can run the weekly check alone |
| 8. Close | 1 | final report, access revoked (T-05 closed), discovery bundle retained or destroyed per T-02 | sign-off |

## Phase detail

### 0. Kickoff and consent
- ☐ Send the **T-01 intake questionnaire** before the kickoff call. It covers entities, devices, accounts, tools, known pain points and crown-jewel data.
- ☐ Agree scope: which entities, devices, accounts and tools are in scope, and which are explicitly out.
- ☐ Sign **T-02 engagement authorization**: scope, read-only discovery, change approval rule, data handling, retention of outputs.
- ☐ Open **T-05 access log**. Every credential, admin role or connector granted gets a row, with its revocation date.

### 1. Access and connectors
- ☐ On the client's Mac: install Claude Desktop, sign in, and enable Claude Code. For hands-on runs use `claude remote-control` in `~/Code` so the lead can drive it from the Claude app.
- ☐ Grant macOS permissions only for the session: Full Disk Access for Terminal (needed to see Library and iCloud metadata). Remove it at close.
- ☐ Install read-only CLIs as needed: `gh`, `az`, `gcloud`, `op`, `vercel`, `wrangler` (see `ops/cloud-inventory/inventory_cloud.sh`).
- ☐ Connect cloud connectors in claude.ai: Google Drive/Gmail, Microsoft 365, GitHub, Notion, Slack. Record each in T-05.
- ☐ Admin read roles: Entra Global Reader, Google Workspace read-only admin, GitHub org owner or auditor, 1Password (vault *names* only).

### 2. Discovery (read-only)
- ☐ Run `bash ops/client-discovery/run_discovery.sh <client-slug>` on each Mac. It bundles the Mac, dev, AI-tool and cloud audits.
  Browsers, 1Password and Apple Mail are read only if T-02 clause 4b is ticked: then prefix `CONSENT_4B=1 MAIL_ACCOUNTS="<Schedule A mail accounts>"`.
  A `DISCOVERY-INCOMPLETE.txt` in the bundle lists any step that failed.
- ☐ Run connector inventories from a cloud session: Drive, OneDrive/SharePoint, Notion, GitHub (all orgs), mailboxes (metadata only).
- ☐ Request exports the client must trigger themselves (see `ops/ai-library/README.md`): ChatGPT, Claude, Grok, Perplexity, Google Takeout, Microsoft Purview.
- ☐ Work through **SOP-02** section by section. Mark each item ✅ evidence · ⚠️ finding · ❓ gap (with the reason).

### 3. Mapping
- ☐ **T-03 platform register:** one row per platform/account/tenant, with owner, entity, status, cost, SSO, data held, and decision.
- ☐ Cloud topology, top-down: identity → clouds → workspaces → code → hosting/data → SaaS/AI.
- ☐ Repo map (products and duplicates), data map (where crown-jewel data lives, and how many copies), AI asset map (skills, prompts, GPTs, projects, agents).

### 4. Risk and findings
- ☐ **T-04 findings register**, severity P0–P3. P0 = exposed secret, admin without MFA, sole copy of critical data, unknown admin, public data leak.
- ☐ P0s are **escalated to the client the same day**. Discovery itself stays read-only. The fixes (rotate keys, enable MFA, back up sole copies) run as a
  separate, approved change batch with its own dry-run → apply record (Phase 6 rules), started immediately rather than waiting for Phase 6.
- ☐ **T-06 discovery report** presented to the client (template).

### 5. Target design
- ☐ Decisions log: primary identity provider, primary tenant(s), primary document store, notes system, code org, secret store, AI tool set.
- ☐ Taxonomy, naming and tagging standard adopted, and the rename backlog generated.
- ☐ Agent standard: `AGENTS.md` rules, skills library, MCP/plugin set with no inline secrets.

### 6. Execute (dry run → approve → apply → verify)
Order: **rescue sole copies → rotate secrets → identity/SSO → dedup → consolidate → migrate → rename → retire.**
Use the kit: `ops/mac-cleanup/*`, `ops/github-consolidation/*`, `ops/ai-library/ingest_library.py`, `archive-dedup-playbook` (Drive, OneDrive, Dropbox, iCloud).
Each batch gets a manifest and an undo path. Verify counts and hashes after each batch.

### 7. Automate and hand over
- ☐ Weekly: Mac audit (launchd), Downloads/Desktop sorter, Drive/OneDrive dedup report, GitHub hygiene report, secret-scan alerts.
- ☐ Runbook plus a 30-minute owner walkthrough. The client runs one weekly check with the lead watching.

### 8. Close
- ☐ Revoke every access in T-05. Remove Full Disk Access and temporary admin roles. Disconnect the lead's connectors.
- ☐ Deliver the final report and registers. Retain or destroy the discovery bundle as T-02 says, and record which.
