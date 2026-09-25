# GitHub setup: every setting, connection and tool

`<ORG>` below is the new org from `docs/GITHUB-BLUEPRINT.md` (recommended: `powerconnection`). Everything that GitHub's API
can set is done by one script (§1). The rest must be clicked in the web UI (§2–§5). Do the sections in order. ☐ = a checkbox for you.

## 1. Org and repo settings: one script (preview first)
```bash
cd ~/Code/<ORG>/config            # or wherever this repo is cloned
gh auth refresh -h github.com -s admin:org
bash ops/github-setup/configure_github.sh <ORG>                          # preview: lists every change, makes none
bash ops/github-setup/configure_github.sh --apply --create-repos <ORG>   # apply, and create the blueprint repos
```
It sets the following, and is safe to re-run (for example after adding repos):
| Area | Setting |
|---|---|
| Members | base permission *Read*; only owners create repos; no forking private repos |
| Team | `maintainers` (used by `CODEOWNERS`), with you as maintainer |
| Actions | allowed only: GitHub-made, verified creators, `anthropics/claude-code-action`. The workflow token is read-only unless a workflow asks for more; workflows can't approve PRs |
| Security (every repo + default for new ones) | dependency graph, Dependabot alerts + security updates, **secret scanning + push protection**, private vulnerability reporting |
| Ruleset `protect-main` (every repo's default branch) | PR required; checks `secrets` and `check` must pass; review threads resolved; no force-push or deletion; org owners can bypass in an emergency. 0 required approvals, because you work alone and can't approve your own PR (raise it when a second person joins) |
| Every repo | squash merge only (the PR title becomes the commit), auto-merge on, update-branch button, branches deleted after merge, wiki/projects off |
| `--create-repos` | the 8 blueprint repos; `config` is marked as the template |

The script prints a FAIL line for anything your plan doesn't include (see §8) and carries on. The `.github` repo is public on
purpose: GitHub only reads org-wide default templates and the org profile from a public `.github`.

## 2. Web-only settings (github.com/organizations/<ORG>/settings)
- ☐ **Authentication security:** require two-factor authentication for everyone.
- ☐ **Billing and plans → Spending limits:** Actions and Codespaces **$0** (nothing is charged beyond the included minutes until you raise it).
- ☐ **Third-party access → OAuth app policy:** *Access restricted*. Approve only the apps in §3 as they ask.
- ☐ **Pages:** leave off unless a repo publishes a site.
- ☐ **Codespaces:** *Disabled*, or *Selected members* (you) if you want cloud dev environments (repos include `.devcontainer/`).
- ☐ **Repository → Repository transfers:** off (the fresh start copies repos in instead of transferring them).
- ☐ **Profile:** add the org avatar and a short description; the `.github` repo's `profile/README.md` becomes the org home page.

## 3. Apps and cloud agents: install each on `<ORG>` only
| Tool | Where | Settings |
|---|---|---|
| **Claude** (Claude Code on the web, `@claude` in issues/PRs) | github.com/apps/claude → Configure → `<ORG>` → *All repositories* | Web sessions use it to push and open PRs. `@claude` in GitHub runs `.github/workflows/claude.yml` (needs the secret in §5) |
| **Linear** | Linear → Settings → Integrations → GitHub → connect `<ORG>` | Links branches/PRs that carry the issue key (`POW-123`) and closes the issue on merge |
| **One review bot** | CodeRabbit (app.coderabbit.ai) *or* Cursor Bugbot *or* Copilot code review (§4) | Pick **one**. Two bots doubled the noise on the old PR #1 |
| OpenAI Codex (cloud) | chatgpt.com/codex → Settings → GitHub connector | Select `<ORG>` only |
| Cursor (background agents) | cursor.com → Settings → Integrations → GitHub | Select `<ORG>` only |
| Devin | app.devin.ai → Settings → Integrations → GitHub | Only the repos Devin works in |
| Warp | Warp → Settings → AI → Rules | Reads `AGENTS.md`; API keys stay in 1Password (Linear POW-89) |
| Vercel / Render / Cloudflare | each dashboard → Git integration | Only the repos that deploy there (`powerconnection`, `onewish`, …) |
| Gemini Code Assist, Grok, others | each tool's GitHub integration page | Write access only where the agent actually works |

Then: ☐ Org → Settings → **GitHub Apps**: remove anything you don't recognize. ☐ Your account → Settings → **Applications**: the same.
☐ After the fresh start, uninstall these apps from `connectedagents-ai` and `Connected-Energy-AI`.

## 4. GitHub Copilot (agents, cloud, review)
Copilot on an org needs **Copilot Business** (§8). With a personal Copilot Pro/Pro+ plan you can still use it in your IDE on
these repos, but the org-level coding agent and policies below need the org plan.
- ☐ Org → **Copilot → Access**: give yourself (and later, the team) a seat.
- ☐ Org → **Copilot → Policies**: Copilot in IDEs *on*; Copilot Chat *on*; **Copilot coding agent** *on*; **MCP servers** *on* (the coding agent can use the repo's MCP configuration); suggestions matching public code *blocked*; Copilot code review *on* only if you picked it as the one review bot.
- ☐ Org → **Copilot → Coding agent**: enable it for *All repositories* (or the repos you choose).
- ☐ Org → **Copilot → Models**: turn on the Claude models if you want Copilot to use them.
- How it works here: assign an issue to **Copilot** (or ask in Copilot Chat) → it works on a `copilot/…` branch in GitHub Actions,
  prepared by `.github/workflows/copilot-setup-steps.yml` (runs `make setup`), and opens a PR. It follows
  `.github/copilot-instructions.md` → `AGENTS.md`. The `protect-main` ruleset applies to its PRs like anyone else's.

## 5. Secrets for workflows (from 1Password, never pasted in chat)
```bash
claude setup-token                    # on the Mac: creates a long-lived Claude Code token; save it in 1Password as "Claude Code GitHub token"
op read "op://AI-Agents/Claude Code GitHub token/credential" | gh secret set CLAUDE_CODE_OAUTH_TOKEN --org <ORG> --visibility all
```
If GitHub refuses org-level secrets for private repos on your plan, set it per repo instead: `… | gh secret set CLAUDE_CODE_OAUTH_TOKEN --repo <ORG>/<repo>`.
Nothing else is needed for CI: the secret scan and tests use no secrets.

## 6. Your Mac: one identity everywhere
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
git config --global core.excludesFile ~/.gitignore_global   # from the config repo

# Fresh clones of the new repos (old clones stay where they are until you archive them)
mkdir -p ~/Code/<ORG> && cd ~/Code/<ORG>
for r in config platform powerconnection onewish litigationforce voice-agents lab; do gh repo clone "<ORG>/$r"; done
```
- ☐ One SSH key (`~/.ssh/id_ed25519`), stored in 1Password's SSH agent and added to GitHub. Delete stale keys at github.com/settings/keys.
- ☐ Fine-grained PATs only (scoped to `<ORG>`, with an expiry), stored in 1Password. Revoke all classic PATs at github.com/settings/tokens.
- ☐ Folder layout: `~/Code/<ORG>/<repo>` (see `docs/ARCHITECTURE.md`).

## 7. Agent CLIs and IDEs: every tool reads the same rules
| Tool | Setup | Rules come from |
|---|---|---|
| Claude Code (terminal, desktop, web) | `~/.claude/CLAUDE.md` + `~/.claude/settings.json` from `ops/mac-cleanup/templates/`; each repo's `.claude/settings.json` blocks reading `.env`/keys and force-pushes | `CLAUDE.md` → `AGENTS.md` |
| VS Code | Open a repo and accept the **recommended extensions** prompt (`.vscode/extensions.json`: Claude Code, Copilot, Copilot Chat, GitHub PRs, 1Password, EditorConfig, Python) | Copilot: `.github/copilot-instructions.md` → `AGENTS.md` |
| Cursor | Install the Claude Code extension; sign in to GitHub as your one account | reads `AGENTS.md` natively; `.cursor/rules/` only for Cursor-only extras |
| JetBrains (PyCharm, WebStorm) | Plugins: GitHub Copilot, Claude Code | same files |
| Codespaces / dev containers | `.devcontainer/devcontainer.json` (Python 3.12, Node LTS, gh, the same extensions); runs `make setup` | same files |
| Codex CLI | `~/.codex/config.toml`, `~/.codex/AGENTS.md` | reads `AGENTS.md` natively |
| Gemini CLI / Antigravity | `~/.gemini/GEMINI.md`, `~/.gemini/settings.json` | `GEMINI.md` → `AGENTS.md` |
| Grok CLI | `~/.grok/` settings | pass `AGENTS.md` as its context file |
| Warp | Settings → AI → Rules | `AGENTS.md` |

Keep the global files (and MCP server templates **without secrets**) in the `config` repo, and symlink them into place from there.

## 8. What each repo gets from the `config` template
`AGENTS.md` (+ `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md` pointers) · `.github/workflows/ci.yml` (secret scan
of the full history + `make lint` + `make test`) · `.github/workflows/claude.yml` (`@claude`, trusted users only) ·
`.github/workflows/copilot-setup-steps.yml` · `.github/dependabot.yml` · `CODEOWNERS` · PR template · issue form (Linear
first, with a no-secrets/PII/privileged-material check) · `.claude/settings.json` · `.vscode/extensions.json` ·
`.devcontainer/` · `.editorconfig` · `.gitignore` (secrets blocked) · `Makefile` (`setup`, `lint`, `test`, `dev`).
When you create a repo from the template, change `CODEOWNERS` to `@<ORG>/maintainers`.

## 9. Which settings need a paid plan
Prices are GitHub's list prices as last checked. Confirm on github.com/pricing before buying. Nothing here is bought automatically.
| Plan | About | Unlocks for **private** repos |
|---|---|---|
| Free | $0 | everything in §1 except the rows below. Public repos get rulesets and secret scanning free |
| **Team** | $4 per user/month | the `protect-main` ruleset and required checks, org-level secrets for private repos, required reviewers |
| **GitHub Secret Protection** | $19 per active committer/month | secret scanning + push protection on private repos (the CI secret scan still runs free on every PR) |
| **Copilot Business** | $19 per user/month | the Copilot org seat, policies and coding agent (§4) |
Minimum recommended: **Team** (about $4/month for you alone), because without it nothing stops a direct push or force-push to `main` on a private repo.
