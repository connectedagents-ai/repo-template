# Unified AI workspace: build instructions for the hub project

**Goal:** one Claude Code project, the **hub**, that every AI tool, account and coding agent reads from: the same rules,
skills, ontology, MCP servers and secrets, with all code on GitHub and all AI history exported into one library.
Covers Mac, GitHub, Google, Microsoft, Claude, ChatGPT/Codex, Grok/xAI, Perplexity, Copilot, Cursor, Devin, Warp, Docker,
Linear, Notion, Replit, Antigravity, VS Code and the web builders (Vercel, Netlify, Cloudflare and others).

This file is the **order of work**. The steps themselves already exist in this repo: each phase links to the runbook step
or script that does the job, and only adds what was missing. Rules for every phase: [`AGENTS.md`](../AGENTS.md)
(dry run first, archive don't delete, no secrets or client material in git, ask before anything outward-facing).

> **Where this runs.** Phases 1–3 and 5–7 read and change files on **your Mac**. Run them in Claude Code (or a terminal) on the Mac,
> not in a claude.ai cloud session: a cloud container's `~/.claude` is empty scaffolding that resets every session. A
> `/setup-audit` run in a cloud session confirmed this on 2026-10-22: no settings, no hooks, no history, nothing to audit.
> Cloud sessions are good for the GitHub-side work (phases 2b, 4, 6 PRs, 8 docs).

## 0. What you end up with
```
                 ┌─────────────── connectedagents-ai/config  (the hub repo, private) ────────────────┐
                 │ AGENTS.md · ontology/ · skills/ · prompts/ · agents/ · mcp/ · tools/<tool>/ · env/  │
                 └───────┬──────────────────┬──────────────────┬──────────────────┬─────────────────┘
          symlinks on Mac│     repo template│      MCP (one set)│     op:// refs    │ connectors / APIs
   ┌─────────────────────┴───┐  ┌───────────┴──────┐  ┌────────┴────────┐  ┌──────┴──────┐  ┌──────┴───────────┐
   │ ~/.claude ~/.agents     │  │ every product    │  │ Claude Codex    │  │ 1Password   │  │ Linear (work hub)│
   │ ~/.codex ~/.cursor      │  │ repo: AGENTS.md, │  │ Cursor VS Code  │  │ vault       │  │ Notion (docs)    │
   │ ~/.gemini ~/.grok Warp  │  │ CI, .claude/     │  │ Gemini Grok     │  │ AI-Agents   │  │ Drive/SharePoint │
   └─────────────────────────┘  └──────────────────┘  │ Perplexity …    │  └─────────────┘  └──────────────────┘
                                                      └─────────────────┘
```
- **One rules file** (`AGENTS.md`); every tool-specific file is a one-line pointer to it.
- **One skills folder** (`config/skills/`), linked into every tool by `ops/skills/skills_hub.py`.
- **One ontology** (`config/ontology/global-ontology.yaml`): names, tags, taxonomy, topology. See [`GLOBAL-ONTOLOGY.md`](GLOBAL-ONTOLOGY.md).
- **One MCP core set** (`ops/mcp/core-servers.txt`), optionally served through one Docker MCP gateway.
- **One secret store** (1Password); configs hold `op://` references only.
- **One work hub** (Linear workspace Powerconnection). Every phase below is one Linear issue under project P-POW-52.

## 1. The hub repo
**Name:** `connectedagents-ai/config`. It is the clean successor to `agent-central-config`. Never copy that repo's history:
it has live keys and case files in it ([`GITHUB-BLUEPRINT.md`](GITHUB-BLUEPRINT.md) §1). Create it from this template, then:

```
config/
├── AGENTS.md                      the rules (this repo's file, with section 0 filled in)
├── CLAUDE.md  GEMINI.md  .github/copilot-instructions.md     one-line pointers
├── ontology/
│   ├── global-ontology.yaml       entities, relationships, taxonomy, topology, naming regexes, tags, sensitivity
│   └── GLOBAL-ONTOLOGY.md         generated explanation for people
├── skills/<verb-noun>/SKILL.md    the ONE canonical skill set (Agent Skills format)
├── prompts/<tool>/<name>.md       system prompts: Claude Projects, Custom GPTs, Gems, Perplexity Spaces, Grok, Copilot
├── agents/<role>-agent.md         subagent / bot definitions (Claude subagents, Devin playbooks, Grok bot, Linear agents)
├── mcp/
│   ├── core-servers.txt           the core set
│   └── templates/                 per-client MCP config templates, op:// refs only
├── tools/<tool>/                  global config templates per tool (settings.json, config.toml, rules) → symlinked on the Mac
├── env/ai-apis.env.example        API keys as op:// refs (copy of ops/env/ai-apis.env.example)
├── register/
│   ├── accounts.csv               every account (§2), owner, plan, export status
│   └── platforms.csv              from docs/sop/templates/T-03-platform-register.csv
└── ops/                           the scripts from this repo's ops/, with their tests
```
Large libraries stay out of it: shared code goes to `platform`, the promoted prompt and skill library can live in `ai-library`
if it outgrows `config` (see [`ops/ai-library/README.md`](../ops/ai-library/README.md)), raw exports go to the private raw store.

## 2. Account register (fill `register/accounts.csv` first)
Give each login one **label** and use that label everywhere: `--account` in the ingest script, folder names in the raw store,
1Password item names.

| Tool | Accounts → label | What to collect | How |
|---|---|---|---|
| Claude (claude.ai, Projects, Claude Code, Desktop) | `claude-main` (+ team/enterprise if any) | chats, Projects' instructions + files, artifacts, skills, connectors, scheduled tasks, memory | [`CLAUDE-APP-RESET.md`](../ops/mac-cleanup/CLAUDE-APP-RESET.md) · Settings → Privacy → Export data |
| Claude API (Console) | `anthropic-api` | workspaces, key **names**, spend limits | console.anthropic.com → Settings |
| ChatGPT | `chatgpt-personal`, `chatgpt-team` | chats, Projects, Custom GPTs, memory, connectors | [ai-library §ChatGPT](../ops/ai-library/README.md) |
| Codex (CLI, IDE, cloud) | `codex-personal`, `codex-team` (the two ChatGPT logins) | `~/.codex/` (config, AGENTS.md, prompts, sessions), cloud task history and the branches it opened | `audit_claude_files.sh` covers `~/.codex`; cloud tasks: chatgpt.com/codex → each task's PR |
| OpenAI API | `openai-api` | projects, Assistants/files/vector stores, key names | ai-library §ChatGPT, "OpenAI platform" row |
| Grok | `grok-personal`, `grok-x`, `grok-teams` | chats, projects/workspaces, custom instructions, files | [ai-library §Grok](../ops/ai-library/README.md) |
| Grok bots (in Linear, Notion, Slack) | `grok-bot` | everything the bot wrote and what it was told (§4.3) | Linear and Notion search, below |
| xAI API / console | `xai-api` | collections, files, key names | console.x.ai |
| Perplexity (web + Mac app + Comet) | `perplexity-personal`, `perplexity-desktop` (if a separate login) | threads, Spaces + instructions, Pages, Labs/Computer assets, tasks, Mac app connectors | ai-library §Perplexity · Mac app → Settings → Connectors (screenshot the list) |
| Microsoft Copilot | `outlook-personal`, `netzerolending`, `onewishlabs` | chats, Pages/Notebooks, saved prompts, Copilot Studio agents | ai-library §Copilot |
| GitHub Copilot | org seat in `connectedagents-ai` | instructions, coding-agent PRs | [`GITHUB-SETUP.md`](GITHUB-SETUP.md) §4 |
| Cursor | `cursor-a`, `cursor-b` (the two logins) | rules (`.cursor/rules`, user rules in Settings), `~/.cursor/mcp.json`, `~/.cursor/skills`, background-agent PRs, chat history | `audit_claude_files.sh` · chats: Cursor → each chat → Export, or the `state.vscdb` files under `~/Library/Application Support/Cursor/User/` (copy, never edit) |
| Google (Gemini, NotebookLM, AI Studio, Antigravity, Drive) | `powerconnection` + one label per other Google login | Takeout, Gems, notebooks, AI Studio folder, `~/.gemini/` | ai-library §Google |
| Devin | `devin` | Knowledge, Playbooks, session summaries, repo setups | Devin → Settings → Knowledge / Playbooks (copy text) |
| Warp | `warp` | Rules, Warp Drive workflows/notebooks/prompts, MCP list | Warp → Warp Drive → export, Settings → AI → Rules |
| Docker | `docker` | Docker Desktop MCP Toolkit servers, compose stacks | `docker mcp server ls` (if the toolkit is on), `docker compose ls` |
| Linear | workspace `powerconnection` | agent integrations, guidance text, bot users | Linear → Settings → Integrations / Agents |
| Notion | workspace(s) | integrations + their page access, AI instructions | Notion → Settings → Connections |
| Replit | `replit` | Repls/apps, `replit.md` agent instructions, secrets **names** | each app → Git pane → connect to GitHub (phase 2) |
| Vercel, Netlify, Cloudflare, Render | one label per team | projects, linked repos, domains, env var **names** | phase 8 |
| Web builders (v0, Lovable, Bolt, Replit Agent, Wix/B12) | one label each | generated apps: sync to GitHub, then treat as code | phase 2 |

## 3. Phases

### Phase −1 · Active incident? Contain it before anything else
If a scan reports malicious workflow files committed by a bot account across repos (a GitHub Actions worm), the order matters,
because a worm that still holds a token re-steals every new secret:
1. **Cut its access:** revoke the bot's PATs and OAuth grants, suspend or remove the bot account from both orgs, remove unknown GitHub
   Apps and deploy keys, and revoke your own PATs that have `workflow` scope (github.com → Settings → Developer settings; org →
   Settings → Third-party access / GitHub Apps / Personal access tokens).
2. **Stop it running:** org → Settings → Actions → disable Actions (or allow only selected, pinned actions) until clean.
3. **Then rotate** every secret in the affected repos' and orgs' Actions secrets, and every key the scan names, at each provider.
4. **Clean** each repo by PR: remove the injected workflows, review the audit log (org → Settings → Audit log, filter by the bot), check
   for new collaborators, webhooks and releases. Re-enable Actions with the `protect-main` ruleset and required review on `.github/workflows/**`.
5. **Record** names only (repos, secrets rotated, dates) in the private store, never in a public repo.

### Phase 0 · Secrets first (blocks everything else)
Rotate every key that was ever committed or pasted into a config, turn on push protection, and create the small **`AI-Agents`**
vault that agents may read. [`ops/README.md`](../ops/README.md) step 0 · `python3 ops/secrets/find_plaintext_keys.py` ·
[`ops/1password/SETUP.md`](../ops/1password/SETUP.md) · the "Shared with Grok Bot" vault fix in [`ops/mcp/README.md`](../ops/mcp/README.md) §3.
**Done when** the plaintext-key report is empty and no bot shares a vault larger than `AI-Agents`.

### Phase 1 · Inventory (read-only)
On the Mac, from `repo-template/ops`:
```bash
bash start.sh                                                   # menu of every read-only step; reports go to ~/ops-reports/
bash mac-cleanup/audit_claude_files.sh                          # Claude, Codex, Cursor, Gemini/Antigravity, Grok, Perplexity, ChatGPT, Copilot files
bash client-discovery/run_discovery.sh powerconnection          # accounts, duplicate CLI installs, endpoint report
bash cloud-inventory/inventory_cloud.sh                         # Entra, Azure, GCP, GitHub, Vercel, Cloudflare, 1Password
python3 skills/skills_hub.py inventory --scan-repos ~/Code --out ~/ops-reports/skills.csv
find ~ -name .git -type d -prune -not -path '*/Library/*' 2>/dev/null > ~/ops-reports/git-repos.txt
```
Then, in **Claude Code on the Mac**: `claude doctor`, `/setup-audit` (the setup-audit plugin) and `/insights` for the real config,
permission rules, hooks and context cost. **Done when** `register/accounts.csv` has a row for every login in §2 and
`~/ops-reports/` holds each report.

### Phase 2 · Push all existing code to GitHub
Code lives only in `~/Code/connectedagents-ai/<repo>` and on GitHub. Nothing becomes its own repo just because it was a folder.
1. **Classify** every path in `git-repos.txt` and every non-git code folder (scratch projects, Antigravity playgrounds, Cursor
   workspaces, Replit/v0/Lovable exports) into: product repo folder · `lab` · `ai-workspace-inbox` · archive. Use the class
   table in [`GITHUB-BLUEPRINT.md`](GITHUB-BLUEPRINT.md) §5.
2. **Scan before pushing:** `gitleaks detect --source <path>` (history) and `gitleaks dir <path>` (files). A dirty history means
   "fold as files", never push the history.
3. **Agent scratch work** → `bash mac-cleanup/collect_ai_workspaces.sh` → `--apply` (rescues it into `ai-workspace-inbox`).
4. **Existing repos** → `github-consolidation/migrate_to_connectedagents.sh` (other orgs) and `merge_into_monorepo.sh` (fold into
   the ~8 target repos), one PR per source repo, archive the source after merge. [`MIGRATION-PLAN.md`](../ops/github-consolidation/MIGRATION-PLAN.md).
5. **Uncommitted local work** in any clone: commit it on a branch `chore/rescue-<host>-<YYYYMMDD>` and push; never leave work only on the Mac.
6. **Web builders and Replit:** connect each app to GitHub from the builder (v0 / Lovable / Bolt "Sync to GitHub", Replit Git pane)
   into `lab` or its product repo's `apps/<name>`, then edit only through git.
**Done when** every row of `git-repos.txt` is marked pushed, folded or archived, and `git status` is clean in every clone.

### Phase 3 · Export every AI account into the library
For each row of §2: export → `python3 ai-library/ingest_library.py --source <tool> --account <label> <export>` (dry run, then `--apply`).
It files raw exports into the private raw store (never git) and removes duplicates. Then **promote** the reusable pieces
(prompts, skills, templates) into `config/` as in [ai-library "Promotion rules"](../ops/ai-library/README.md).
The full per-tool checklist is in [`ops/ai-library/README.md`](../ops/ai-library/README.md); additions:
- **Codex (two logins):** `~/.codex/sessions/` is the transcript store. Ingest with `--source codex --account codex-<label>`.
  Cloud tasks leave branches and PRs; those are cleaned up in runbook step 9.
- **Cursor (two logins):** sign in to each in turn and export the chats worth keeping; copy each login's **User Rules** text into
  `prompts/cursor/<label>-user-rules.md`.
- **Perplexity Mac app:** record each local connector's command (Settings → Connectors), so it can be rebuilt from `mcp/templates/`.
- **Warp and Devin:** their rules and knowledge become `prompts/warp/` and `prompts/devin/`. Anything that repeats `AGENTS.md` is dropped.

### Phase 4 · Global ontology, master folders, naming and tags
Run the seven-step process in [`GLOBAL-ONTOLOGY.md`](GLOBAL-ONTOLOGY.md) (collect → compare → canonical YAML → rules as code → agents →
apply → govern). Naming rules: [`NAMING-CONVENTIONS.md`](NAMING-CONVENTIONS.md). Topology (which system owns what): [`CLOUD-ARCHITECTURE.md`](CLOUD-ARCHITECTURE.md).

**Master folder system.** One tree, the same in every document store (Google Drive, SharePoint/OneDrive, the Mac's document
folder, Notion teamspaces). Draft to ratify in `global-ontology.yaml` → `taxonomy`; nothing is moved before that:
```
00-inbox/                              everything new lands here; emptied weekly
10-companies/<entity>/                 PowerConnection · OneWish-Labs · NetZero-Lending · LitigationForce · Connected-Energy
    admin/ finance/ legal/ sales/ marketing/ product/ operations/ people/
20-projects/<project>/                 cross-company work with an end date
30-knowledge/  reference/ research/ ontology/
40-ai/         prompts/ skills/ agents/ exports-index/     (indexes only: raw exports stay in the private raw store)
80-templates/  <domain>/
90-archive/    <topic>-<YYYYMMDD>/     with MANIFEST + restore notes
```
Code is never in this tree (it lives in git). Privileged legal material stays in its litigation store and is referenced by name only.
Tags (not names) carry `type · domain · entity · project · status · sensitivity · owner · source` ([`NAMING-CONVENTIONS.md`](NAMING-CONVENTIONS.md) §3):
GitHub topics, Drive labels, SharePoint columns, Finder tags, Notion database properties, Linear labels, skill front matter.
**Done when** `global-ontology.yaml` v1.0.0 is merged and the lint report (`lint_names.py`) lists every violation with a proposed name.

### Phase 5 · Centralize the skills
1. **Inventory:** `python3 ops/skills/skills_hub.py inventory --scan-repos ~/Code --out ~/ops-reports/skills.csv` lists every
   `SKILL.md` in Claude, `~/.agents`, Cursor, Codex, Antigravity/Gemini, Grok and every repo-level skills folder, with
   identical copies, same-name variants and front-matter problems. Add plugin skills from Claude Code's `/plugin` list and the
   skills exported in phase 3.
2. **Classify** each distinct skill once:

   | Class | Test | Goes to |
   |---|---|---|
   | **Core** | used across companies and tools, at least monthly | `config/skills/` (linked everywhere) |
   | **Domain** | one product or practice area (legal, tax, energy, voice) | that product repo's `.claude/skills/` (repo-level, loads only there) |
   | **Plugin** | maintained upstream (Anthropic, vendor plugins) | leave installed via the plugin marketplace; do not copy |
   | **Retire** | duplicate, superseded, unused 90 days, or just restates `AGENTS.md` | archive; note `supersedes:` in the survivor |

3. **Merge variants** into one copy each: front matter `name` (verb-first kebab-case, equal to the folder name) and `description`
   (what it does and when to use it); `source:` and `supersedes:` lines for provenance. No secrets, client data or privileged text.
4. **Starting core set** (check against the inventory; keep it under ~25): `client-discovery` (exists in `ops/client-discovery/skill/`),
   `create-linear-issue`, `report-to-linear`, `open-pull-request`, `review-code`, `write-tests-first`, `run-dedup`, `file-document`
   (names and tags from the ontology), `ingest-export`, `rotate-secret`, `deploy-preview`, `write-sop`, `summarize-meeting`,
   `research-topic`. Anthropic's built-in document skills (docx, xlsx, pptx, pdf) stay plugin-managed.
5. **Link:** `python3 ops/skills/skills_hub.py link --hub ~/Code/connectedagents-ai/config/skills` (dry run), then `--apply`.
   It symlinks each skill into `~/.claude/skills` (Claude Code), `~/.agents/skills` (the cross-agent folder Codex and Cursor read)
   and `~/.gemini/antigravity/skills` (Antigravity), and archives whatever was there (undo with the printed `restore.sh`).
   Add `--target .grok/skills` or others if a tool needs it. Cursor reads `~/.agents/skills` **and** `~/.claude/skills`, so it may
   list a skill twice; that's cosmetic.
6. **Chat apps without a skills folder** (ChatGPT, Gemini Gems, Perplexity Spaces, Grok projects, Copilot): paste the skill body as
   the instruction text, and keep that copy listed in the skill's front matter (`mirrors:`) so updates are pushed everywhere.
   claude.ai accepts skill uploads directly (Settings → Capabilities → Skills).
**Done when** the inventory shows each core skill once (symlinks count once) with no front-matter issues.

### Phase 6 · Agent instructions: every tool reads AGENTS.md
Skill and rule paths drift between releases. The Codex, Cursor, Antigravity and Docker rows were checked against vendor docs on
2026-10-22 (see Sources); the rest are from earlier knowledge and say "per … docs" where unsure. Confirm on the tool's own docs page
before relying on a path. Global files come from `config/tools/<tool>/` by symlink.

| Tool | Global rules | Project rules | Skills | MCP config |
|---|---|---|---|---|
| Claude Code | `~/.claude/CLAUDE.md` → "Follow ~/Code/connectedagents-ai/config/AGENTS.md" (template: `ops/mac-cleanup/templates/CLAUDE.md`) | `CLAUDE.md` = `@AGENTS.md` | `~/.claude/skills`, `.claude/skills` | `claude mcp add --scope user …`, project `.mcp.json` |
| Claude Desktop | n/a (Projects instructions in the app) | n/a | uploaded skills | `~/Library/Application Support/Claude/claude_desktop_config.json` (template in `ops/mac-cleanup/templates/`) |
| Codex CLI / IDE / cloud | `~/.codex/AGENTS.md` | `AGENTS.md` (native) | `~/.agents/skills`, `.agents/skills` | `~/.codex/config.toml` `[mcp_servers.*]`, or `codex mcp add` |
| Cursor | Settings → Rules → User Rules: one line pointing to AGENTS.md | `AGENTS.md` (native); `.cursor/rules/*.mdc` only for Cursor-only extras | `~/.cursor/skills`, `~/.agents/skills`, `.cursor/skills` | `~/.cursor/mcp.json`, `.cursor/mcp.json` |
| VS Code + GitHub Copilot | Copilot settings → instructions | `.github/copilot-instructions.md` → AGENTS.md; Copilot also reads `AGENTS.md` | n/a | `.vscode/mcp.json` or user `mcp.json` |
| Gemini CLI | `~/.gemini/GEMINI.md` pointer, or `"context": {"fileName": ["AGENTS.md"]}` in `~/.gemini/settings.json` | `GEMINI.md` → AGENTS.md | per Gemini CLI docs | `~/.gemini/settings.json` `mcpServers` |
| Antigravity | `~/.gemini/GEMINI.md` | `.agent/rules/` → one pointer file | `~/.gemini/antigravity/skills`, `.agent/skills` | `~/.gemini/antigravity/mcp_config.json` |
| Grok CLI (Grok Build) | per xAI docs | `AGENTS.md` | per xAI docs (supports skills) | its config file (`park_mcp_servers.py` handles `~/.grok/*.json`) |
| Warp | Settings → AI → Rules: pointer to AGENTS.md | reads `AGENTS.md` / `WARP.md` | n/a | Settings → AI → MCP servers |
| Devin | Knowledge entry: "Always follow AGENTS.md in the repo root" | `AGENTS.md` | Playbooks | Devin → Settings → MCP |
| Replit Agent | n/a | `replit.md` → one line pointing to AGENTS.md | n/a | Replit → Integrations |
| ChatGPT / Gemini / Perplexity / Grok / Copilot chat | custom instructions: short house style + "names and tags follow the Global Ontology" | Project / Gem / Space / workspace instructions from `config/prompts/<tool>/` | phase 5 step 6 | ChatGPT connectors (developer mode), Perplexity Mac connectors, Copilot Studio |
| Linear agents (Devin, Cursor, Codex, Copilot, Warp, Claude, Grok bot) | workspace-level agent guidance if your Linear plan has it (check Settings → Agents); otherwise each agent's own instructions. Text: summary of AGENTS.md §2 + "branch/PR title carries the issue key" | n/a | n/a | Linear MCP for tools that need it |

Product repos get all of this from the template ([`GITHUB-SETUP.md`](GITHUB-SETUP.md) §7–§8). **Done when** each tool, asked
"what file holds your rules?", names AGENTS.md.

### Phase 7 · One MCP set for every client
1. Fill `ops/mcp/core-servers.txt` (start: github, filesystem, playwright, firecrawl, 1password, notion, linear).
2. Park everything else per client: `python3 ops/mcp/park_mcp_servers.py --config <file> --keep-file ops/mcp/core-servers.txt` → `--apply`
   for `~/.codex/config.toml`, `~/.cursor/mcp.json`, `~/.gemini/settings.json`, `~/.gemini/antigravity/mcp_config.json`, the Grok
   config, and Claude Desktop's config. It reports inline secrets to move to `op://`.
3. **Optional single gateway:** Docker Desktop's **MCP Toolkit** runs the servers in containers behind one gateway. Add the core
   servers to a profile, then connect clients from its Clients tab, or point any client at `docker mcp gateway run --profile <name>`
   as a stdio server. Then each client has one MCP entry (`MCP_DOCKER`) instead of seven. Check with `claude mcp list` / `codex mcp list`.
4. Prefer the **claude.ai connectors** (GitHub, Linear, Notion, Google, Microsoft 365) over local servers with tokens for Claude itself.
5. Access audit: AI OAuth apps in Entra (the four "Grok Business" apps), Google Admin and GitHub ([`ops/mcp/README.md`](../ops/mcp/README.md) §3).

### Phase 8 · API environments (Claude, OpenAI, xAI)
1. One key **per environment** (dev, ci, prod) and per provider, stored in `AI-Agents` (dev) and the CI/prod vaults. Names:
   `Anthropic-dev`, `OpenAI-ci`, `xAI-prod`, …
2. Template: [`ops/env/ai-apis.env.example`](../ops/env/ai-apis.env.example). Run anything with
   `op run --env-file=ops/env/ai-apis.env.example -- <cmd>`. CI uses a 1Password service account or GitHub OIDC, never a pasted key.
3. Smoke test each provider (prints the model list, not the key):
   ```bash
   op run --env-file=ops/env/ai-apis.env.example -- sh -c '
     curl -sf https://api.anthropic.com/v1/models -H "x-api-key: $ANTHROPIC_API_KEY" -H "anthropic-version: 2023-06-01" | head -c 300; echo
     curl -sf https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY" | head -c 300; echo
     curl -sf "$XAI_BASE_URL/models" -H "Authorization: Bearer $XAI_API_KEY" | head -c 300; echo'
   ```
4. Set a **monthly spend limit and alert** in each console (Anthropic Console, OpenAI platform, xAI console). Delete keys nobody owns.
5. Claude Code headless (`claude -p`), the Claude Agent SDK, the OpenAI Agents SDK and Grok's OpenAI-compatible endpoint all read these
   same three variables.

### Phase 9 · Work hub, docs and deploy targets
- **Linear** (system of record): install the GitHub integration on `connectedagents-ai`; enable the agents you actually use (Devin, Cursor,
  Codex, Copilot, Warp, Claude) and remove the rest; one project per phase of this file under P-POW-52.
- **Grok bot data in Linear and Notion:** list what it wrote before deciding its future. Linear: filter issues and comments by the bot user
  (or Linear MCP `list_issues` / `list_comments`), export to CSV. Notion: Settings → Connections → the Grok integration → pages it can
  access; search pages it created. Keep useful instructions as `config/agents/grok-bot.md`; narrow its page access to what it needs, or remove it.
- **Notion:** documents and wikis only (no code, no secrets). Teamspaces follow the master folder tree. Ontology wikis feed phase 4 and then
  point to the YAML.
- **Devin / Warp / Docker:** each connects to GitHub through the org app (no personal tokens), reads `AGENTS.md`, gets secrets from 1Password.
- **Deploy targets:** one host per app, recorded in the app's `README` and in `AGENTS.md` section 0.

  | Host | Use for | Setup |
  |---|---|---|
  | Vercel | Next.js / frontends (powerconnection.ai today) | Git integration on the org repo, preview deploy per PR, env vars from 1Password (1Password's Vercel integration or `vercel env`), team SSO |
  | Netlify | static sites and simple marketing pages | `netlify.toml` in the app folder, Git-based deploys, deploy previews |
  | Cloudflare (Pages, Workers, DNS) | DNS for every domain, edge functions | DNS consolidation in [`DOMAIN-CONSOLIDATION.md`](../ops/domains/DOMAIN-CONSOLIDATION.md) |
  | Render / GCP | long-running backends, workers, voice agents | per [`CLOUD-ARCHITECTURE.md`](CLOUD-ARCHITECTURE.md) decision D4 |
  | Replit, v0, Lovable, Bolt | prototypes only | sync to GitHub (phase 2), deploy from the repo on one of the hosts above once it's real |

### Phase 10 · Verify and keep it that way
- [ ] `find_plaintext_keys.py` clean; push protection on; no bot shares more than `AI-Agents`
- [ ] every account in `register/accounts.csv` exported and ingested; promoted items committed to `config`
- [ ] every local repo pushed or archived; old orgs archived
- [ ] `skills_hub.py inventory`: each core skill once, no issues; `skills_hub.py link` says "nothing to do"
- [ ] every tool in the phase 6 table points at AGENTS.md; every MCP client lists only the core set
- [ ] three API smoke tests pass; spend limits set
- [ ] `global-ontology.yaml` merged; naming lint report worked down
- **Weekly (15 min):** empty `00-inbox/` and `~/Code/_scratch/`, re-run the skills inventory and the MCP park dry runs, close stale agent PRs.
- **Changes** only by PR to `config`; the ontology gets a semver bump and changelog entry.

## 4. Kickoff prompt for the hub project
Create `config` (phase 1), clone it to `~/Code/connectedagents-ai/config`, open Claude Code **on the Mac** in that folder, and paste:

```text
You are setting up the hub repo for our unified AI workspace. Read AGENTS.md and docs/UNIFIED-AI-WORKSPACE.md first; follow
AGENTS.md exactly (dry run first, archive instead of delete, never print or commit secret values, ask before anything
outward-facing or destructive).

Work through docs/UNIFIED-AI-WORKSPACE.md phase by phase, starting at phase 0. For each phase:
1. Create or find its Linear issue in project P-POW-52 and put the key in the branch name.
2. Run the read-only/dry-run commands it lists, save reports in ~/ops-reports/, and summarize what they found.
3. Propose the changes as a short plan and wait for my approval before any --apply step.
4. Open a PR to this repo for every file change (register, prompts, skills, ontology, tool templates), with make lint and make test passing.
5. Tick the phase's "Done when" line in the Linear issue, then move on.

Start now with phase 0 and phase 1: list which keys need rotating (names only), run the inventories, and draft register/accounts.csv
from the account table in §2. Stop and show me the draft before going further.
```

## 5. Running it with subagents
Split the work into waves; agents in a wave run in parallel, and no wave starts before the one above is done. Agents on the **Mac**
(Claude Code with Desktop Commander) do local file work; **cloud** sessions do GitHub PRs. Every agent stops at its dry-run report;
`--apply` runs only after you approve it. Reports go to `~/ops-reports/` and the private store, never into a public repo.

| Wave | Agents (where) | Job | Gate |
|---|---|---|---|
| 0 · You | — | Phase −1 steps 1–2: cut the attacker's access, disable Actions | Actions off |
| 1 · Contain | `scanner` (cloud): `ops/security/scan_infected_repos.sh` across both orgs, every branch · `secret-inventory` (Mac): `find_plaintext_keys.py` + Actions secret names → rotation list · `repo-cleaner` ×N (cloud): one PR per infected repo | scanner re-run reports 0 infected |
| 2 · Documents | `doc-scan` (Mac): `dedup_scan.py --root <folder> --ext … --skip-repos` → `dedup_merge.py` · `doc-dedup` (Mac): `dedup_apply.py` · `drive-consolidate` (Mac): `consolidate_to_drive.py` · `matter-memory`: matter brief into the private store + a Claude Project instruction | you approve PLAN.md; `rclone check` shows 0 missing |
| 3 · Workspace | `inventory`, `code-push`, `export-<tool>` ×1 per account, `skills`, `tool-config` + `mcp`, `ontology`, `api-env` + `deploy`: phases 1–9 above | each phase's "Done when" |
| 4 · GitHub declutter | `org-classify` (cloud): `migrate_to_connectedagents.sh <old-org>` dry run → classification sheet + what costs money · `org-migrate`: transfer, fold with `merge_into_monorepo.sh`, archive the rest · `org-declutter`: same inside the main org, close stale agent branches/PRs · **you**: remove the old org's seats and Copilot, downgrade or cancel it | old org has 0 active repos; its next invoice is $0 |

## Sources (checked 2026-10-22)
- OpenAI Codex: [Agent Skills](https://developers.openai.com/codex/skills) (skills folder; `~/.agents/skills` per community guides such as [this one](https://codex.danielvaughan.com/2026/05/05/agent-skills-open-standard-portable-skills-codex-cli-cross-agent/))
- Cursor: [Agent Skills](https://cursor.com/docs/skills) (`.cursor/skills`, `.agents/skills`, `~/.cursor/skills`, `~/.agents/skills`, plus `.claude/skills` and `.codex/skills`)
- Docker: [Get started with MCP Toolkit](https://docs.docker.com/ai/mcp-catalog-and-toolkit/get-started/) · [MCP Toolkit](https://docs.docker.com/ai/mcp-catalog-and-toolkit/toolkit/)
- Google Antigravity: [Authoring Antigravity Skills codelab](https://codelabs.developers.google.com/getting-started-with-antigravity-skills?hl=en) (`.agent/skills`, `~/.gemini/antigravity/skills`)
- Grok Build CLI (third-party coverage; confirm with xAI docs): [overview](https://mer.vin/2026/05/grok-build-cli-xai-terminal-coding-agent-with-plan-mode-subagents-and-headless-ci/)
- Perplexity Mac connectors: [9to5Mac](https://9to5mac.com/2025/07/25/perplexity-for-mac-now-supports-mcp-and-you-should-check-it-out/) · [setup guide](https://dev.to/moefqy/set-up-a-local-mcp-server-for-perplexity-macos-guide-548m)
- Linear agents: [AI agents guide](https://linear.app/enablement/guide/ai-agents)
- Agent Skills open standard: [agentskills.io](https://agentskills.io)
