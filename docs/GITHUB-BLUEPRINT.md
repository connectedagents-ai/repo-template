# GitHub fresh start: blueprint

**Decisions (2026-09-25, kickoff session):** start over in **one new, clean org**. Build **a handful of monorepos** instead of
~280 small repos. **Carry over** the proven rules and ops tools from `repo-template` PR #1, then close that PR. Nothing old is
deleted: old repos are **archived** (read-only, reversible) once their useful parts have moved.

This file replaces the *target* in `ops/github-consolidation/MIGRATION-PLAN.md` (that plan moved everything into
`connectedagents-ai`). Its **step 0 still applies first**: rotate the keys committed in `agent-central-config`, and keep case
files out of code repos.

## 1. Why start over (what the inventory shows)
- About 200 repos in `connectedagents-ai` and 82 in `Connected-Energy-AI`. Around 90 were created in a 10-minute burst on 2026-09-03:
  a Mac folder tree turned into one repo per folder (`dev-*`, `development-onewish-*`, `dev-cursorcloudagents-dev-*`, …).
- The same names appear in both orgs (`onewish-os`, `codex-platform`, `LitigationForce.AI`, `gemini-cli`, …). There are also
  random names (`olive-prairie-acorn-kite`, `turbo-crane-mountain-wave`) and many unmodified forks.
- `repo-template`'s default branch was named after an unused product idea; it was renamed to `main` on 2026-09-25.
- `agent-central-config` has live keys and about 173 MB of case files **in its git history**, so it must never be copied with its history.

## 2. The new org
- **Name:** `powerconnectionai`, display name "Power Connection" (created 2026-09-25 on the Team plan): **https://github.com/powerconnectionai**
  Created by you on github.com (GitHub doesn't let apps or agents create orgs).
- **Private by default.** Public only on purpose (e.g. an open-source package or a marketing site).
- Settings: `ops/github-setup/configure_github.sh` applies everything the API can set (members, Actions, security, the
  `protect-main` ruleset, merge settings). `docs/GITHUB-SETUP.md` §2–§5 lists the web-only steps (2FA, spending limits, apps, Copilot).

## 3. The repos (8 in total; sub-projects are folders, never new repos)
| Repo | What goes in it | Folds in (examples from the old orgs) |
|---|---|---|
| `.github` | Org profile README, default PR/issue templates, `CODEOWNERS` default, reusable CI workflows | new |
| `config` | **The rules and tools:** `AGENTS.md` (single source of truth), `CLAUDE.md` pointer, `.claude/` settings, hooks and skills, dotfiles, MCP templates, `ops/` scripts and tests from PR #1. Marked as the **template repository** | `repo-template` (PR #1 files), clean parts of `agent-central-config` (files only, no history), `scripts`, `rename-scripts`, `archive-dedup-playbook`, `gforce-repo-ops`, `docker-stack` |
| `platform` | Shared building blocks: `packages/` (MCP servers, SDK wrappers, plugins), `agents/` (agent definitions), `skills/` | `dev-mcp-server*`, `github-mcp-server` work, `agent-skills-suite`, `developer-skills`, `chairman-agent`, `piper-cto-agent`, `linear-plugin-onewishos`, `attio-plugin-onewishos`, `op-smart-agent` |
| `powerconnection` | The energy business: web, geo, marketing, CRM apps | `powerconnection-web`, `powerconnection-geo`, `powerconnection-monorepo`, `power-connection-ai`, `connected-marketing-app`, `landing-pages` |
| `onewish` | OneWish OS and its apps: dashboard, design system, second brain, ontology | `onewish-os` (newest copy), `onewishos`, `onewish-dashboard`, `onewish-design-system`, `onewish-second-brain`, `onewish-live`, `development-onewish-dev-ontology` |
| `litigationforce` | LitigationForce / LexVault **product code only**. Case evidence stays in the evidence store, never here | `LitigationForce.AI` (both copies), `litforce`, `litigationforce-aad-bridge` |
| `voice-agents` | Voice agent platform and console, telephony, realtime clients | `voice-agent-platform`, `twilio-voice-agent`, `node-voice-agent`, `xai-realtime-agent-client`, `voice-empire` |
| `lab` | Experiments and spikes. Anything goes; pruned every quarter; nothing ships from here | `empty-window`, `hyperframes`, `GrokMultiModal`, `gemini-chat`, the random-name repos worth keeping |

Anything that isn't code (plans, exports, notes, PRDs) goes to Notion / SharePoint / the private raw store, not GitHub.
Forks: don't carry them over. Star the upstream and re-fork only when you have a change to contribute.

## 4. Naming rules (enforced from day one)
- **Repos:** lowercase kebab-case, the business or product name only (`voice-agents`). No tool names (`cursor-`, `claude-`, `dev-`),
  no dates, no `v2` / `final` / `copy` / `new`, no random names.
- **Folders inside a repo:** `apps/<name>` (deployables) · `packages/<name>` (libraries, MCP servers) · `agents/<name>` · `docs/` · `scripts/` · `tests/`.
- **Default branch:** `main`, always.
- **Branches:** `<type>/<LINEAR-KEY>-<slug>` (`feat/POW-123-intake-form`). Agents use their own prefix (`claude/…`, `codex/…`).
- **Commits:** Conventional Commits. **PR titles:** include the Linear key, so Linear links the PR and closes the issue on merge.
- Full list: `docs/NAMING-CONVENTIONS.md`.

## 5. How old repos come in (per repo, never in bulk)
| Class | Test | Action |
|---|---|---|
| **Fold with history** | Real code, no secrets or case files in its history (`gitleaks detect` is clean) | `ops/github-consolidation/merge_into_monorepo.sh` into its folder in the new repo |
| **Fold as files** | Useful, but its history has secrets or case files | Copy the current files only (a fresh history), after removing the secrets |
| **Reference** | Might be needed later, not active | Leave it where it is and archive it |
| **Drop** | Unmodified forks, empty repos, duplicates | Archive it (no deletion) |
Every row is decided in a classification sheet first (generated by `migrate_to_connectedagents.sh`'s dry run, retargeted to the new org), and you approve it.
Once a repo's contents are in the new org, archive the old repo. When both old orgs are fully archived, remove their app installs.

## 6. Kickoff session: the order of work
| # | Who | Step | Done when |
|---|---|---|---|
| 1 | You | Create the org at github.com/account/organizations/new (Free is fine to start; Team if you want required reviewers on private repos) | the org exists |
| 2 | You | Install the **Claude GitHub App** on the new org (github.com/apps/claude → Configure → *All repositories*). Also Linear, and **one** review bot (CodeRabbit or Cursor Bugbot, not both: two bots doubled the review noise on PR #1) | the app shows the org |
| 3 | You | Run `bash ops/github-setup/configure_github.sh powerconnectionai` (preview), then with `--apply --create-repos`; tick `docs/GITHUB-SETUP.md` §2–§5 | the script ends with no FAIL lines, or only plan-limited ones you accept |
| 4 | Claude | Create `config` and `.github`, and seed `config` with the PR #1 files (`AGENTS.md` with the new org name, `ops/`, `tests/`, `Makefile`, CI, `.claude/settings.json`, the gitleaks hook). Default branch `main`, CI green | first PR merged |
| 5 | Claude | Seed the six product and platform repos (created in step 3) from the `config` template files, each with a README stating what belongs in it | 8 repos have CI green |
| 6 | Claude + you | Generate the classification sheet for all old repos; you approve it in batches | sheet approved |
| 7 | Claude | Fold repos in, one PR per old repo; archive each old repo after its PR merges | old orgs archived |
| 8 | You | Close `repo-template` PR #1 (its files now live in `config`) | done |

Steps 1–3 take about 20 minutes on your side. Step 4 starts as soon as the Claude app can see the new org.
