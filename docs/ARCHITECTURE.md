# Workspace architecture

## Layers
```
GitHub: connectedagents-ai (the only org)
├── product repos      onewish-os · chairman-agent · power-connection · litigationforce · voice-agents
├── shared             ai-library (skills, prompts, templates, forms, MCP/plugins) · knowledge-base
├── ops                agent-central-config (dotfiles, rules, MCP templates, Mac setup) · repo-template (this)
├── lab / inbox        agent-lab (experiments) · ai-workspace-inbox (rescued agent scratch)
└── archived           everything else: read-only, never deleted
```

## Mac layout
```
~/Code/connectedagents-ai/<repo>   every git clone, one level deep. Not in Desktop/Documents/iCloud (sync breaks git and node_modules)
~/Code/_scratch/                   throwaway. Empty it weekly: promote to a repo or delete
~/Archive/<topic>-<YYYYMMDD>/      anything retired, with a MANIFEST and restore.sh (see ops/mac-cleanup)
~/.claude  ~/.codex  ~/.cursor  ~/.gemini  ~/.grok   tool state only. Rules and configs are symlinked from agent-central-config
```

## Work tracking: Linear is the hub
Linear workspace **Powerconnection** (teams POW, LIT, SALES) is where dev work is planned and tracked; GitHub holds the code,
AGENTS.md the rules. Coding agents take work from Linear and report back to it: Devin, Cursor, Codex and Claude through their Linear
integrations or the Linear MCP server, and GitHub PRs link automatically when the branch or PR title contains the issue key.
Open consolidation items already live there: POW-89 (Warp), POW-94 (Devin), POW-232 (reporting protocol for external agents),
P-POW-52 (Master Configuration & Dev Tools Alignment), P-POW-38 (Corpus Consolidation), POW-149 (corpus inventory).

## Rules of the road
1. **One rules file:** `AGENTS.md` in every repo. Tool-specific files are one-line pointers to it.
2. **One secret store:** 1Password. Configs contain `op://` references, never values.
3. **One home per thing:** code → its product repo. Reusable prompts, skills and templates → `ai-library`. Documents and data → the document vault (not GitHub).
4. **Archive, don't delete.** Every cleanup script is dry-run first, logs its moves and can be undone.
5. **New repo = template + reason.** If it could be a folder in an existing repo, it should be.

## Claude Desktop MCP servers (lean set)
The current Desktop config has duplicates (`Filesystem` + `filesystem`), four tools that overlap (Desktop Commander, `desktop-automation`, `shell`, `applescript`) and several failing servers.

| Keep | Why |
|---|---|
| **Filesystem** (extension) | file access, managed by Desktop |
| **Desktop Commander** | shell and process control. Replaces `shell`, `applescript`, `desktop-automation` |
| **Claude in Chrome** (built-in setting) | browser control. Replaces the failing *Control Chrome* extension |
| **1Password** | fix it rather than drop it: install `op` and sign in, then point the server at the absolute `/opt/homebrew/bin/op` path |
| `playwright` (optional) | scripted browser testing |
| `firecrawl` | web scraping. Move its API key out of the JSON into 1Password |

Remove: `filesystem` (duplicate), `desktop-automation`, `shell`, `applescript`, `git` (Desktop Commander and Claude Code handle git), `github`
(use the claude.ai **GitHub connector**, not a PAT in plain JSON), `sequential-thinking` (built-in extended thinking replaces it), `sqlite`,
`email` and *Read and Send iMessages* (unless you actively use them; use the Gmail / Microsoft 365 connectors for email), and `grok`
(an LLM-calling-LLM bridge; keep it only if you ask Claude to call Grok).

Automated: `bash ops/mac-cleanup/archive_claude_files.sh --prune-mcp` (dry run) → `--apply --prune-mcp` (backup + restore.sh).

Most "Server disconnected" errors on a Mac come from Desktop launching with a minimal PATH: `npx` or `node` installed via nvm or Homebrew isn't found.
Use absolute paths (`/opt/homebrew/bin/npx`), then check `~/Library/Logs/Claude/mcp-server-<name>.log`.
