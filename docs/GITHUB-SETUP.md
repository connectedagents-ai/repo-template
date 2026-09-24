# GitHub setup: `connectedagents-ai` as the one account

Do these once, in order. ☐ = a checkbox for you.

## 1. Org security (github.com/organizations/connectedagents-ai/settings)
- ☐ **Authentication security:** require 2FA for all members.
- ☐ **Code security → Global settings:** enable **Secret scanning** and **Push protection** for all repos, plus Dependabot alerts and security updates. Push protection would have blocked the committed `.env` in `agent-central-config`.
- ☐ **Repository → Rulesets:** create an org ruleset *"protect main"* targeting all repos' default branch: require a PR, require status checks `CI / secrets` **and** `CI / check`, block force pushes and deletions. Add yourself as bypass actor for emergencies.
- ☐ **Member privileges:** base permission *Read*. Only owners can create repos, so every new repo starts from the template.
- ☐ **Repository → Repository transfers:** allow transfers in (needed for the migration), then turn this off again.
- ☐ Create team `maintainers` (it's referenced by `CODEOWNERS`).
- ☐ Mark `connectedagents-ai/repo-template` as **Template repository** (repo Settings → General).

## 2. Apps and cloud agents: connect them to this org only
For each app: install it on `connectedagents-ai` → *Only select repositories* (or all, if you prefer), then **uninstall it from Connected-Energy-AI and any other account** once the migration is done.

| Tool | Where | Notes |
|---|---|---|
| Claude (Claude Code on the web, GitHub App, `@claude` reviews) | github.com/apps/claude → Configure | Web sessions use it for push and PR access |
| OpenAI Codex (cloud) | chatgpt.com/codex → Settings → GitHub connector | Remove other orgs from the connector |
| Cursor (background agents, Bugbot) | cursor.com → Settings → Integrations → GitHub | |
| GitHub Copilot (coding agent + reviews) | Org → Copilot → Policies / Coding agent | Seats on the org. Instructions come from `.github/copilot-instructions.md` → `AGENTS.md` |
| Devin | app.devin.ai → Settings → Integrations → GitHub | |
| Gemini Code Assist / Antigravity, Grok, others | each tool's GitHub integration page | Only give write access where the agent actually works |

Then audit: Org → Settings → **GitHub Apps** and **OAuth app policy**. Remove anything you don't recognize or no longer use.
Do the same under your personal account: Settings → Applications (Authorized OAuth Apps / GitHub Apps).

## 3. Your Mac: one identity everywhere
```bash
# GitHub CLI: exactly one account
gh auth status                       # lists every logged-in account
gh auth logout --hostname github.com --user <other-account>   # repeat for each extra one
gh auth login --hostname github.com --git-protocol ssh --web
gh auth setup-git

# Git identity for all code under ~/Code
git config --global user.name  "Robert Bailey"
git config --global user.email "<your GitHub noreply or work email>"
git config --global init.defaultBranch main
git config --global pull.rebase true
git config --global core.excludesFile ~/.gitignore_global   # from agent-central-config/config/gitignore_global

# Old remotes: fix clones still pointing at the old org (after transfer the redirect works, but make it explicit)
for r in ~/Code/*/*/; do u=$(git -C "$r" remote get-url origin 2>/dev/null) || continue
  case "$u" in *Connected-Energy-AI/*) git -C "$r" remote set-url origin "${u/Connected-Energy-AI/connectedagents-ai}"; echo "fixed $r";; esac
done
```
- ☐ One SSH key (`~/.ssh/id_ed25519`), stored in 1Password's SSH agent and added to GitHub. Delete stale keys at github.com/settings/keys.
- ☐ Fine-grained PATs only (scoped to `connectedagents-ai`, with an expiry), stored in 1Password. Revoke all classic PATs at github.com/settings/tokens.
- ☐ Folder layout: `~/Code/connectedagents-ai/<repo>` (see `docs/ARCHITECTURE.md`).

## 4. Agent CLIs: every tool reads the same rules
| CLI | Global config | Points to |
|---|---|---|
| Claude Code | `~/.claude/CLAUDE.md`, `~/.claude/settings.json` | templates in `ops/mac-cleanup/templates/` |
| Codex CLI | `~/.codex/config.toml`, `~/.codex/AGENTS.md` | reads repo `AGENTS.md` natively |
| Cursor | Settings → Rules, `.cursor/rules/` | reads repo `AGENTS.md` natively. Keep `.cursor/rules` for Cursor-only extras |
| Gemini CLI / Antigravity | `~/.gemini/GEMINI.md`, `~/.gemini/settings.json` | repo `GEMINI.md` → `AGENTS.md` |
| Copilot | `.github/copilot-instructions.md` | → `AGENTS.md` |
| Grok CLI | `~/.grok/` settings | pass `AGENTS.md` as its instructions/context file |

Keep the global files (and MCP server templates **without secrets**) in `connectedagents-ai/agent-central-config`, and symlink them into place with its `scripts/setup-mac.sh`.
