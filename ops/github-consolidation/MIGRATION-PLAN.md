# GitHub consolidation plan → `connectedagents-ai`

**Decision (2026-09-24):** `connectedagents-ai` is the **only** GitHub account/org. Everything else migrates in, then goes quiet.

> ⚠️ **Reverse the old direction first.** `connectedagents-ai/repo-template` and `connectedagents-ai/agent-central-config`
> carry a "MOVED → Connected-Energy-AI" banner. That migration ran the wrong way. This branch removes the banner from
> `repo-template`. Do the same in `agent-central-config` once its secrets issue (below) is fixed.

## Inventory snapshot (2026-09-24)

| Owner | Repos | Notes |
|---|---|---|
| `connectedagents-ai` | ~200+ | ~90 created in a single 10-minute burst on 2026-09-03 (03:24–03:33 UTC). That was a Mac folder tree exploded into one repo per folder: `dev-*`, `development-onewish-*`, `dev-cursorcloudagents-dev-*`, `dev-agents-multi-agent-swarms*`, `developer-*` |
| `Connected-Energy-AI` | 82 | 24 already archived, ~20 forks, 13 names that also exist in `connectedagents-ai` |

## Step 0: stop the bleeding (do before migrating)

1. **Rotate secrets.** `agent-central-config` has a committed `.env` whose API-key fields (Anthropic, OpenAI, xAI, GitHub PAT, Stripe, Slack, Vercel, Cloudflare, and more) are non-empty. Treat every one as exposed: rotate it in its provider console, store the new value only in 1Password, and turn on **secret scanning + push protection** for the org (see `docs/GITHUB-SETUP.md`). Deleting the file is not enough, because it stays in git history.
2. **Move case files out of config repos.** `agent-central-config/litigation/` holds about 173 MB of case documents (spreadsheets, emails, BOMs, many duplicate copies). Privileged material belongs in the litigation product's private evidence store (or an encrypted vault), not in a tool-config repo that every Mac and agent clones.

## Step 1: transfer `Connected-Energy-AI` → `connectedagents-ai`

```bash
bash ops/github-consolidation/migrate_to_connectedagents.sh Connected-Energy-AI          # dry run → CSV plan
bash ops/github-consolidation/migrate_to_connectedagents.sh --apply Connected-Energy-AI  # transfers non-colliding repos
```

GitHub transfers keep issues, PRs, stars and history, and leave a redirect from the old URL. You must re-create **Actions
secrets/variables, webhooks, deploy keys and GitHub App installs** on the new side.

### Name collisions: decide per repo (the script never auto-transfers these)

| Repo in both orgs | Recommended action |
|---|---|
| `onewish-os` | CEA copy is the most recently pushed (2026-09-24). Diff both copies, merge CEA's newer commits into `connectedagents-ai/onewish-os` (`merge_into_monorepo.sh … --as-branch`), then archive the CEA copy |
| `repo-template`, `agent-central-config`, `gforce-repo-ops`, `connected-agents-ai`, `codex-platform`, `LitigationForce.AI`, `agent-skills-suite` | Compare the last commit dates. Keep the `connectedagents-ai` copy and cherry-pick anything newer from CEA. Archive the CEA copy |
| `gemini-cli`, `github-mcp-server`, `railway-skills`, `agentskills`, `skills` (all unmodified upstream forks) | Keep **neither** unless you have commits on them. Delete or archive the forks and star the upstream instead |

Other accounts (personal users, old orgs): run the same script with their owner names.

## Step 2: collapse ~280 repos into ~10 domain repos

Target: **one repo per product or domain**, with sub-projects as folders (`apps/`, `packages/`, `agents/`, `docs/`).
Fold each source in with its history preserved (`merge_into_monorepo.sh`), then **archive** the source (read-only, reversible, nothing is deleted).

| Target repo | Folds in (examples; verify with the dry-run CSVs) |
|---|---|
| `onewish-os` | `onewishos`, `onewish-agent-os-constitution`, `onewish-constitutional`, `onewish-second-brain`, `onewish-dashboard`, `onewish-design-system`, `onewish-live`, `onewish-wire-hub`, `onewish-vertical-company-os`, all `development-onewish-dev-onewish-*` (≈30), all `dev-onewish-*` (≈12), `dev-onewishos-ingestion-m0-m1`, `dev-onewishlabs-*`, `dev-apollo-onewishlabs-graph`, `onewish-document-ops`, `onewish-mac-shortcuts-a0`, `onewish-project-coordination-explainer-workspace`, `onewish_work_decomposition_matrix_*`, CEA `autonomousagentos`, `intelligence-os-vault` |
| `chairman-agent` | `dev-chairman-agent-package`, `piper-cto-agent`, CEA `chairman-life-os`, `development-onewish-dev-onewish-chairman-life-os-ingestion`, `agent-central-config/chairman/` docs |
| `power-connection` (rename of `powerconnection-monorepo`) | `power-connection-ai`, `dev-power-connection-ai`, `powerconnection-web`, `powerconnection-geo`, `power-connection-artifact-demo`, `powermed-runtime`, `powermed-landing`, `cenergy-graph-ops`, `tejas-*`, CEA `powerconnectionai`, `powerconnectionaiapplications`, `Powermed-Marketing`, `energy-navigator-ai`, `tesla-energy-battlecards` |
| `litigationforce` | `LitigationForce.AI`, `litforce`, `litigationforce-aad-bridge`, CEA `lawsuite-monorepo`, `legal-case-assistant`, `Litigation-Force-Interactive-Presentation`, the case files moved out of `agent-central-config` (private, encrypted) |
| `voice-agents` | `voice-agent-platform`, `dev-voice-agent-platform`, `developer-voiceagents-*`, `voice-empire`, `node-voice-agent`, `twilio-voice-agent`, `twilio-video-app-react`, `xai-realtime-agent-client`, `genie-voice-landing`, CEA `voiceagent.ai`, `empathic-voice-interface-starter` |
| `agent-skills` (skills, plugins, MCP servers as `packages/*`) | `agent-skills-suite`, CEA `agent-skills-suite-v2`, `developer-skills`, `skill-grok-platform`, `dev-cross-platform-skill-builder`, `dev-dev-chatgpt-skill-builder-skill`, `dev-agents-skills-*`, `dev-mcp-server*`, `chatgpt-mcp-app`, `attio-plugin-onewishos`, `linear-plugin-onewishos`, `qodo-onewish-wrapper`, CEA `skill-library-factory`, `mcp-manager` |
| `agent-lab` (experiments from the other coding agents) | **Codex:** `codex-platform`. **Cursor:** CEA `CURSOR-CLOUD-AGENTS`, `dev-cursor-cloud-agents-main`, `dev-cursorcloudagents-dev-*` (15), `cursor-scripts`, `cursor-docs`. **Devin:** `dev-devin-agent-kits`. **Grok:** `GrokMultiModal`. **Copilot:** `dev-onewish-copilot-sdk-lab`. **Multi-agent:** `dev-agents-multi-agent-swarms*` (6), `dev-agent-architecture`, `dev-compose-for-agents-main`, `dev-claude-agent-sdk`, `agent-efficiency`, `openrouter-agent`, `op-smart-agent`, `my-agent`, `dev-my-agent`, `intelligence_agent`, CEA `AI-Generated-Agents` |
| `agent-central-config` | dotfiles, rules, MCP templates for **every** tool on every Mac. Folds in `archive-dedup-playbook`, `gforce-repo-ops`, `rename-scripts`, `scripts`, `docker-stack`, `vscode-migration-archive`, `stack-inventory-*`, CEA `github-governance*`, `github-migration`, `file-management-toolkit` |
| `knowledge-base` | `docs`, `plans`, `product-specs`, `governance-work`, `obsidian-system`, `cursor-docs`, CEA `connected-dev-docs` |
| `repo-template` | this repo: the template every new repo starts from |
| `ai-workspace-inbox` (new) | code rescued from Antigravity, Codex, Cursor, Grok, Devin and Copilot scratch folders (`ops/mac-cleanup/collect_ai_workspaces.sh`) |

**Inspect, then archive** (auto-generated names or tutorials): `olive-prairie-acorn-kite`, `turbo-crane-mountain-wave`,
`empty-window`, `desktop-tutorial`, `skills-code-with-codespaces`, `photos-on-render`, `hf-spaces`, `gemini-chat`.

**Forks** (`hyperframes`, `Agent-Reach`, `arcadedb`, `ldbc_*`, `github-docs`, `AAxD`, `onepassword-sdk-python`,
`AKS-Lab-GitHubCopilot`, `accounting-and-audit-by-design`, `cursor-plugin`, `daloopa-plugin-codex`, and similar): if a fork has no
commits of your own, delete it and star the upstream. If it does, keep it and name the reason in its description.

## Step 3: cloud agents' leftover work

These tools keep work outside your Mac, so the local audit can't see it:

| Tool | Where work hides | Action |
|---|---|---|
| Codex cloud | `codex/*` branches and draft PRs on each repo | Merge or close each open PR. Delete merged branches. In Codex settings, connect **only** `connectedagents-ai` |
| Cursor background agents | `cursor/*` branches | Same as Codex. In Cursor → GitHub integration, limit it to `connectedagents-ai` |
| Devin | Devin sessions plus `devin/*` branches | Export anything worth keeping into `agent-lab`. Remove Devin's access to the old orgs |
| Grok CLI / terminal agent | local only → covered by the Mac audit (`~/.grok`) | collect into `ai-workspace-inbox` |
| Microsoft 365 Copilot | OneDrive/SharePoint (Copilot Pages, Loop) | out of GitHub's scope: export code snippets into `ai-workspace-inbox/copilot/`; archive the rest via `archive-dedup-playbook` |
| Claude Code (web) | `claude/*` branches | Merge or close PRs. Delete merged branches |

List stale agent branches in any repo with:

```bash
git ls-remote --heads origin | grep -E 'refs/heads/(codex|cursor|devin|claude|copilot)/'
```

## Step 4: lock it in

- New repos are created **only** from `connectedagents-ai/repo-template` (turn on "Template repository" in its settings).
- Name repos `<domain>` or `<domain>-<thing>` in kebab-case. No dates, no `dev-`/`development-` prefixes, no `-v2` (use branches and tags instead).
- Quarterly: run `migrate_to_connectedagents.sh` (dry run) against any stray owner, plus the Mac audit.
