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
