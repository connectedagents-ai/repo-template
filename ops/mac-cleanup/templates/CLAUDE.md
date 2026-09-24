# Global instructions (~/.claude/CLAUDE.md)

Keep this file short. Repo-specific rules live in each repo's AGENTS.md.

## Who / where
- GitHub: the only account is `connectedagents-ai`. Never create repos elsewhere.
- Code lives in `~/Code/connectedagents-ai/<repo>`. Never inside Desktop, Downloads, or iCloud Documents.
- Scratch work goes in `~/Code/_scratch/` and is deleted or promoted weekly.

## How to work
- Read the repo's AGENTS.md first and follow it.
- One branch per task, then a PR. Never push straight to `main`.
- Run the repo's lint and test commands before you say the work is done.
- Prefer editing existing files over creating new ones. Don't create one-off copies (`-v2`, `-final`, `copy`).

## Safety
- No secrets in files. Use 1Password references (`op://…`) or env vars injected by `op run`.
- Archive, never delete: move retired material to `~/Archive/<topic>-<YYYYMMDD>/`.
- Ask before doing anything destructive or outward-facing: deleting, force-pushing, transferring repos, or sending messages.
