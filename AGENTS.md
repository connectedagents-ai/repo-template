# AGENTS.md: rules for every coding agent and human in this repo

This is the **single source of truth** for coding rules. Claude Code, Codex, Cursor, GitHub Copilot, Gemini/Antigravity,
Grok CLI, Devin and Warp all read this file, directly or through a one-line pointer (`CLAUDE.md`, `GEMINI.md`,
`.github/copilot-instructions.md`). Change the rules here, never in the pointers.

## 0. Project facts (fill in when creating a repo from the template)
- **Purpose:** _one sentence_
- **Stack:** _e.g. TypeScript + Next.js / Python 3.12 + uv_
- **Setup:** `make setup`  ·  **Test:** `make test`  ·  **Lint/format:** `make lint`  ·  **Run:** `make dev`
- **Owner:** @connectedagents-ai  ·  **Deploys to:** _Render / Vercel / Cloudflare / none_

## 1. Where things go
- GitHub org: **`connectedagents-ai` only**. Never create repos in other orgs or personal accounts.
- One repo per product or domain. Sub-projects are folders, not new repos:
  `apps/` (deployables) · `packages/` (shared libs, MCP servers, plugins) · `agents/` (agent definitions) · `docs/` · `scripts/` · `tests/`
- Before creating a file, look for an existing one that already does the job. **Never** create copies such as `-v2`, `-final`, `-new`, `copy`,
  or date-stamped duplicates. Use git history and branches instead.
- Experiments go on a branch or in `connectedagents-ai/agent-lab`, not in a new repo.
- **The one master folder:** Google Drive > My Drive > `1Bailey Financials 2018-2026 YTD - Tax, IRS, Assets and Liabilities Only`
  (https://drive.google.com/drive/folders/121X1o4QU7r5YPs8uB58d878XAfqNGtSj). Every deliverable is saved into its existing
  subfolders. Legal matters live in the owner-requested **LEGAL MATTERS** folder
  (https://drive.google.com/drive/folders/1Pv-i27zSgoAMYC1JvHaVkos98jpYqL53), structured per `docs/LEGAL_MATTERS_ONTOLOGY.md`.
  Never create another master or root folder.
- **File intake (until the owner says otherwise):** every new, loose or unsorted file goes to Google Drive >
  My Drive > `00_MASTER_INTAKE` (https://drive.google.com/drive/folders/1gSKjscg0lJGdOVuhPbCXrRC-EUQiJQhd),
  never the Mac Desktop or Downloads. Files leave intake only through the shared regex rules into the Global
  Ontology domains, in logged batches the owner approves. Secrets never go to intake; they go to 1Password.

## 2. Workflow
- Branch per task: `<type>/<short-slug>` (`feat/`, `fix/`, `chore/`, `docs/`). Agents may use their tool prefix (`claude/`, `codex/`, `cursor/`, `devin/`).
- Every change lands through a PR into `main`. No direct pushes, no force-pushes to shared branches.
- Linear (workspace `powerconnection`) is the system of record for dev work. When an issue exists, put its key in the branch name
  or PR title (`feat/POW-123-intake-form`) so Linear links the PR and closes the issue on merge.
- Commit messages follow Conventional Commits: `feat: …`, `fix: …`, `chore: …`, `docs: …`, `refactor: …`, `test: …`.
- Keep PRs small and focused. Explain the *why* in the description.
- Before you open or update a PR: run `make lint` and `make test` and fix what fails. Say plainly in the PR if something could not be run.
- Delete your branch after merge. Close abandoned agent PRs; don't leave them open.

## 3. Code rules
- Match the surrounding code's style, naming and comment density. Add a comment only where the *why* isn't obvious.
- Small functions, explicit names, no dead code, no commented-out code.
- Add or update tests for every behavior change. Bug fixes start with a failing test.
- Dependencies: add one only when it clearly pays for itself. Pin versions with a lockfile. Python → `uv`; JS/TS → `pnpm`.
- Config comes from environment variables, documented in `.env.example`, never hard-coded.

## 4. Secrets and data (non-negotiable)
- **Never** commit secrets. `.env*` (except `.env.example`), keys, tokens, `*.pem` and credentials are git-ignored and blocked by push protection.
- Secrets live in 1Password. Load them with `op run --env-file=.env.example -- <cmd>` or `op://` references.
- If a secret ever lands in git, **rotate it immediately**. Deleting the file doesn't make it safe.
- No client PII, privileged legal material or raw exports in code repos. They go in the designated private data store.
- Scripts that touch files are **dry-run by default**, archive instead of deleting, and log what they did.

## 5. Agent behavior
- Read this file and the repo's `docs/ARCHITECTURE.md` before changing code.
- Ask before anything destructive or outward-facing: deleting data, transferring or archiving repos, force-pushing, sending messages, spending money.
- Don't widen scope. If you notice something unrelated, mention it in the PR instead of fixing it silently.
- Report results honestly: what ran, what passed, what didn't, what you skipped.
- Owner operating rules for all agents and LLMs: https://docs.google.com/document/d/1OoyYTeCVJB2V3QQW0CuP-9Kxf1w3qnY48MsIpQBR3eM/edit
  Every output goes to Drive `00_MASTER_INTAKE/_AGENT_OUTPUTS/<tool>/` with a handoff header, and every new or
  superseded artifact gets a row in the project registry
  (https://docs.google.com/spreadsheets/d/1WI8seKlAwl3DWGoMC83eWvdm15YYlwfMIdjg6vFx-pQ/edit). Update in place; never duplicate.
- Segment and capture every work product and confirmation per `docs/WORK_PRODUCT_AND_CONFIRMATIONS.md` (Ledger tab of the master plan sheet).
- Follow `docs/OPERATING_PLAN.md` (durable stores, session start/end steps). The cloud container is never the only copy.
- **LitigationForce material is reference only** (owner, 2026-10-22). Use it only to guide the ontology, folder structure,
  regex and file review. Nothing else: never as case facts, never in filings or productions, never to build or run the platform.
- Never re-ask the owner a settled fact. Before any question, search the owner's established-facts register
  (Drive "00 ESTABLISHED FACTS"), prior handoffs and the project's source-of-truth files; ask only what none of
  them answers, and record every new answer in the register the same day.
- For every step the owner does themselves, give the exact page as a full, visible URL (not only link text) and a
  copy-paste command or script. The owner is a beginner: no step should need them to find a setting or write code.

## 6. Agent-run jobs: web, terminal, clicking, forms, configuration
Choose the fastest, lowest-token path for the job. **Default to a terminal script** (`gh`, `git`, CLIs, APIs, a short
Python/bash script); use browser clicking only for what has no CLI or API (billing, some settings, OAuth approval).
Batch similar steps into one script instead of doing them one by one.

Size the job first; the smallest size that fits wins:
- **Just do it**: read-only or trivially reversible local work (look something up, run a status check, list files).
  Report in one line.
- **Quick confirm**: a one-off, simple job (about 3 steps or fewer, one target) that isn't destructive, paid or
  outward-facing. One line of intent and target ("Rename X to Y in repo Z. OK?"), answered yes or no by button or
  voice. Afterwards, one line of result with proof.
- **Full checklist** (below): several steps or targets, anything that deletes, revokes, pays, sends, publishes or
  touches credentials, anything that can't be undone, or a tool the agent hasn't checked yet.

A full-checklist job follows three steps:
1. **Pre-job checklist, shown before starting.** Goal and done-when · every page (full URL), command and file it will
   touch · tools it needs, checked to be present and signed in (e.g. `gh auth status`, browser connected, `python3`,
   `node`, the SSD mounted), installing what's missing only with a copy-paste command the owner approves · which steps
   need the owner (logins, 2FA, payments, deletions) · how to undo it. Wait for the owner's OK.
2. **Do the job**, pausing at each step that needs the owner.
3. **Confirmation list after finishing.** Each checklist item marked done / failed / skipped, with proof (the command
   output, the page state, a screenshot) · what changed and where · anything left for the owner, as full URLs and
   copy-paste commands.

## 7. Standing authority: what agents may do for the owner without asking
Agents working for the owner on the Mac, dev tools, repos and templates may do these **without asking** (report after):
read anything except secrets · run previews, dry-runs, audits, `make lint`, `make test` · install the rule files and
tools listed by `ops/cowork/bootstrap_mac.sh` · create branches, commit, push agent branches and open PRs · refactor
code on a branch (the owner merges) · move clutter into `~/Archive/<topic>-<YYYYMMDD>/` with a restore script.
**Always ask first** (quick confirm or full checklist, §6): deleting anything, merging to `main`, force-pushing,
changing account, billing, org or security settings, revoking access, sending or publishing, and anything touching
client or case data. **Who decides:** agents plan, prepare, track and build; the owner sets priorities and makes the
legal, money and external calls ("the agent prepares, the owner decides").
