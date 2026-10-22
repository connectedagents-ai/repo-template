# Agent file system and shared memory

One private repo, the **agent home**, holds every agent's definition and one memory pack that every agent system and LLM reads from.
READMEs, per-agent memory views and per-tool files are **generated** and refreshed automatically, so they never drift.
Scripts: `ops/agents/agent_fs.py` and `ops/agents/refresh.sh` (dry run unless `--apply`). Governance: the Chairman Agent (authority matrix,
approval tickets, receipts). This page is generic; the agent home itself is private because it holds personal memory.

## 1. Layout
```
README.md                      GENERATED: agent roster, memory counts, tools wired, open decisions, last refresh
AGENTS.md                      the rules (single source)
chairman/CHAIRMAN.md           Chairman instructions v0.2 (v0.1 + the waves in UNIFIED-AI-WORKSPACE.md)
chairman/principal_decisions.yaml   ONE file: Chairman decisions + the account register. No credentials
agents/<agent-id>/AGENT.md     the source: front matter (agent_id, system, role, risk_tier, memory_namespaces, tools, skills, approval_gates) + instructions
agents/<agent-id>/README.md    GENERATED summary   ·   agents/<agent-id>/memory/MEMORY.md  GENERATED memory view   ·   receipts/  run receipts
memory/sources/<platform>/<account>.jsonl   imported items (source of truth for memory)
memory/pack.jsonl              GENERATED unified pack: one fact per item, every source attached
memory/CONFLICTS.md · BOUNDARY.md   GENERATED review reports after each merge
memory/namespaces/<ns>.md · memory/SYSTEM_MEMORY_v1/<ns>.md   GENERATED views
profile/                       principal profile (namespace personal)
skills/<name>/SKILL.md         canonical skills (linked into tools by ops/skills/skills_hub.py)
tools/<tool>/<file>            GENERATED per-tool rules + memory (see §4)
```
`agent_fs.py init --root <repo> --apply` creates it, with one `AGENT.md` stub per agent: the Chairman and its sub-agents (inventory, extraction,
reconciliation, distribution, governance), the personal chief of staff, and every coding agent (Claude Code, Codex, Cursor, Copilot, Devin, Warp,
Grok CLI) plus the Grok bot. Edit the stubs; re-running `init` never overwrites them.

## 2. Memory lifecycle
1. **Export** each account's memory (table in §3). For bulk exports, file them first: `ingest_library.py --source <tool> --account <label> --kind memory <export>`.
2. **Import:** `agent_fs.py memory import --root <r> --platform <tool> --account <label> [--namespace personal] [--tag privileged] <file|dir> --apply`.
   Reads JSONL records, Markdown bullets (`- Location: Houston` becomes key `location`) and plain lines; stores the Chairman schema
   (`platform, account, item_type, item_id, title, body_md, created_at, updated_at, tags, project, source_url, provenance_hash`) plus `namespace` and `key`.
3. **Merge:** `agent_fs.py memory merge --root <r> --apply`. Same fact from several tools becomes one item with every source; for the same key the newest
   value wins and the older one is listed in `CONFLICTS.md`; anything tagged privileged/family-office aimed at a general namespace is refused and listed in `BOUNDARY.md`.
4. **Render:** `agent_fs.py render --root <r> --apply` regenerates every generated file. Output is stable: re-running changes nothing unless a source changed.
5. **Sync:** `agent_fs.py sync --root <r> --apply` installs into each tool (§4). Backups and `restore.sh` go to `~/Archive/agent-home-sync-<stamp>/`.

**Namespaces:** `core` (everyone), `personal`, `business`, `engineering`; restricted `family-office` and `privileged` are stored as **pointers only**
(title + source, no body) and never reach a general-purpose tool. Litigation content stays in its own store.

## 3. Memory sources, per tool
| Tool / account | Where its memory lives | How to export |
|---|---|---|
| Claude (claude.ai) | Settings → memory; Project instructions and knowledge | copy memory text; Settings → Privacy → Export data; copy each Project's instructions |
| Claude Code | `~/.claude/CLAUDE.md`, `~/.claude/projects/*/memory/`, every repo's `CLAUDE.md` / `AGENTS.md` | import the files directly |
| ChatGPT (each account) | Settings → Personalization → Memory; custom instructions; Projects | copy "Manage memories" into a `.md`; copy custom instructions |
| Codex (each account) | `~/.codex/AGENTS.md`, `~/.codex/prompts/` | import the files |
| Grok (each account) + Grok bot | memory and workspace instructions; bot prompts in Linear / Notion | copy text; data export; Linear/Notion bot pages |
| Gemini | Saved Info; Gems; `~/.gemini/GEMINI.md` | copy Saved Info and Gem instructions; import the file |
| Perplexity | Memory; Spaces instructions | copy |
| Microsoft Copilot (each account) | Copilot memory / saved prompts | copy |
| Cursor (each account) | User Rules (Settings), `.cursor/rules/`, Memories | copy User Rules and Memories; import rule files |
| Windsurf / Codeium | `~/.codeium/windsurf/memories/` | import the folder |
| Devin · Warp · Linear | Knowledge · Rules · agent guidance | copy |
| Notion | Memory pages (About + Memories database) | export the pages as Markdown |

## 4. Where each tool reads the shared memory
| Tool | Generated file | Namespaces | Installed |
|---|---|---|---|
| Claude Code | `tools/claude/CLAUDE.md` | core, engineering, personal, business | one `@<path>` import line appended to `~/.claude/CLAUDE.md` |
| Codex | `tools/codex/AGENTS.md` | core, engineering | managed block in `~/.codex/AGENTS.md` |
| Gemini CLI / Antigravity | `tools/gemini/GEMINI.md` | core, engineering | managed block in `~/.gemini/GEMINI.md` |
| Cursor, Copilot, Warp, Devin, Grok CLI | `tools/<tool>/…` | core, engineering | paste (User Rules / instructions / Rules / Knowledge) |
| ChatGPT, Perplexity, Gemini app, Grok app, Copilot app | `tools/<tool>/paste.md` | core, personal, business | paste into custom instructions / Space / Gem / memory |
Managed blocks sit between `<!-- agent-home:start -->` and `<!-- agent-home:end -->`; everything else in those files stays yours.
Chat apps have no API to write memory, so the paste file is regenerated and you paste it after a refresh that changed it.

## 5. Dynamic updates (pick any; all run `refresh.sh`)
- **Nightly on the Mac:** `ops/agents/templates/com.connectedagents.agent-home-refresh.plist` (03:00, the Chairman cadence). Edit the two paths, copy to `~/Library/LaunchAgents/`, `launchctl load` it.
- **On push to the private repo:** `ops/agents/templates/refresh-agent-home.yml` → `.github/workflows/` there. Regenerates and commits files (no sync in CI).
  It checks out `repo-template` for the scripts; if that repo goes private, give the workflow a read token.
- **After each Claude Code session:** add a `SessionEnd` hook in `~/.claude/settings.json` that runs
  `bash <repo-template>/ops/agents/refresh.sh --root <agent home> --apply`. Opt-in by hand (the scripts never edit your settings).
Any agent that learns a durable fact appends it to `memory/sources/<platform>/<account>.jsonl` (or runs `memory import`), and the next refresh carries it everywhere.

## 6. Rules
- Approval gates in each `AGENT.md` follow the Chairman authority matrix; scripts write receipts to `agents/<id>/receipts/`.
- No credentials in any file. Keys stay in 1Password.
- Generated files carry a banner; edit the source, not the output.
