# MCP and agent wiring: one core toolset for every AI tool

**In scope:** Claude Desktop/Code, **Codex** (CLI + app), **Grok CLI (xAI terminal agent)**, Cursor, VS Code, Antigravity/Gemini, Windsurf.
Every tool gets the **same core MCP servers** (`core-servers.txt`), with secrets from 1Password (`op://`). Everything else is parked, reversibly.

## 1. Wire Codex and Grok into the consolidation
```bash
# fill core-servers.txt with the same core set the Cursor consolidation used, then (dry run first):
python3 ops/mcp/park_mcp_servers.py --config ~/.codex/config.toml      --keep-file ops/mcp/core-servers.txt
python3 ops/mcp/park_mcp_servers.py --config ~/.grok/user-settings.json --keep-file ops/mcp/core-servers.txt
# project-level Grok config, if present:
python3 ops/mcp/park_mcp_servers.py --config <project>/.grok/settings.json --keep-file ops/mcp/core-servers.txt
# then re-run each with --apply  (backup <config>.bak-<stamp>; parked servers → mcp.parked.toml / mcp.parked.json)
```
The tool flags inline secrets (env values) and plain-text `apiKey` fields. Move them to 1Password and pass them in with `op run`, e.g.
`alias grok='op run --env-file=$HOME/.config/op/grok.env -- grok'` where `grok.env` holds `XAI_API_KEY=op://AI-Agents/xAI/credential`.

## 2. One install per CLI
`bash ops/client-discovery/run_discovery.sh <client>` → `endpoint.md` → "Duplicate dev tool installs" lists each CLI with more than one copy
(for example `codex` in `~/.local/bin` and `~/.npm-global/bin`). Keep **one** per tool: the self-updating native installer, or the Homebrew cask, not both.
Remove the extra with its own package manager (`npm uninstall -g @openai/codex`, `brew uninstall …`). Never `rm` a binary another
manager owns. Record what you removed in the platform register.

## 3. Access audit (most important)
| Finding | Why it matters | Fix |
|---|---|---|
| 1Password vault **"Shared with Grok Bot"**: ~402 of 793 items, including logins | any bot or agent with that vault can read those credentials | Create a small vault (`AI-Agents`) with **only** the items the bot needs, re-share just that, then **stop sharing** the big vault. Rotate anything sensitive that was in it. Check with `op vault user list <vault>` (also in `inventory_cloud.sh`) |
| 4 **"Grok Business"** apps in the OneWish Labs tenant (Outlook mail, Calendar, OneDrive, Teams) | delegated or admin consent can let an AI app read all mail and files | Entra admin center → **Enterprise applications** → search "Grok" → each app → **Permissions** (admin vs user consent, scopes like `Mail.Read`, `Files.Read.All`) and **Sign-in logs**. Remove the ones you don't use (Properties → Delete, or revoke admin consent). Keep the rest with the narrowest scopes, and set **user consent to "Do not allow"** in Enterprise apps → Consent and permissions |
| AI tools' OAuth grants in Google Workspace and GitHub | the same risk for Gmail/Drive and repos | Google Admin → Security → API controls → App access control. GitHub org → Settings → GitHub Apps / OAuth app policy |
