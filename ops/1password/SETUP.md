# 1Password for Claude (and other agents)

Account: **Power Connection** (1Password Business). Principle: agents get **read-only** access to the **fewest vaults** they need,
never to Employee, Litigation-Secure or Investment-Operations. Secrets are referenced (`op://vault/item/field`), never copied into files or chat.

## Vault map (where each kind of secret lives)
| Vault | Holds | Agent access |
|---|---|---|
| AI-Agents | LLM API keys (Anthropic, OpenAI, xAI, Gemini, Perplexity, OpenRouter, Groq, DeepSeek, Mistral) | ✅ read (cloud + local) |
| MCP-Servers | MCP/tool keys (Firecrawl, Brave, Tavily, Exa, …) | ✅ read (cloud + local) |
| GitHub-CI-CD | GitHub fine-grained PATs, deploy keys, CI tokens | 🟡 local only (Touch ID). **Not** in the cloud agent's scope: a read-only *vault* grant still hands over tokens that can *write* to repos |
| Agent-GitHub (new, tiny) | only the one token a cloud agent needs: a fine-grained PAT scoped to the specific repos and permissions of that task, with an expiry | ✅ read (cloud), one task-scoped service account per purpose |
| Cloud-Infrastructure | Vercel, Cloudflare, GCP/Azure service principals | 🟡 local only (Touch ID), cloud only when a task needs it |
| Database-Connections | Postgres/Supabase/Neon URLs | 🟡 local only |
| DevStack-Production | production env | 🟡 local only, per task |
| Business-Operations | Stripe, Slack, Notion, Linear, HubSpot, Attio, Airtable, QuickBooks | 🟡 local only |
| Energy-Operations, Investment-Operations, Employee, Litigation-Secure | business, financial, personal and privileged | ❌ never for agents |

The keys found in `agent-central-config/.env` and SharePoint `gemini-api.md` must be **rotated first**. Store the new values straight into the vault above, never in files.

## A. On the Mac (Claude Code / Claude Desktop): biometric, no stored token
1. `brew install 1password-cli`
2. 1Password app → Settings → **Developer** → turn on **Integrate with 1Password CLI** (and **Use the SSH agent** for git).
3. Check it: `op whoami` and `op vault list`. You'll get a Touch ID prompt, and the vault list should show.
4. Using it: `op run --env-file=.env.example -- <command>` or `op read "op://AI-Agents/Anthropic/credential"`. Each new terminal session asks for Touch ID once.
5. Claude Desktop's `1password` MCP server: set its command to the absolute path (`/opt/homebrew/bin/op` or the server's own binary), then restart Claude.

## B. Claude Code on the web (cloud sessions): service account
1. 1Password (web) → **Developer → Directory → Service Accounts → New service account**. Name it `claude-code-cloud`.
2. Grant **read-only** access to **AI-Agents and MCP-Servers** only. Leave "create vaults" off. If a cloud task needs GitHub access, put a single task-scoped fine-grained PAT (only the repos and permissions that task needs, with an expiry) in the small **Agent-GitHub** vault and grant that vault to a separate service account for that task. Never grant GitHub-CI-CD to a general cloud agent.
3. Copy the token. It's shown once, so save it into 1Password itself as well (e.g. `Employee/claude-code-cloud service account`).
4. claude.ai/code → this session's title bar → the cloud **environment menu → Edit**:
   - **Environment variables / API credentials:** add `OP_SERVICE_ACCOUNT_TOKEN` = the token. **Never paste it into chat.**
   - **Network access:** allow `*.1password.com`, `*.1password.ca`, `*.1password.eu` and `cache.agilebits.com` (the CLI download), or pick a broader access level.
   - **Setup script:** add `bash ops/1password/install-op-cli.sh` (or paste its contents).
5. Start a new session. Claude checks `op whoami` → `op vault list`, which should show only the granted vaults.
6. Rotate the service-account token every 90 days (set an expiry when you create it) and review its usage in 1Password's activity log.

## C. Using secrets in repos
- `.env.example` lists variable names with `op://` references, e.g. `ANTHROPIC_API_KEY=op://AI-Agents/Anthropic/credential`.
- Run with `op run --env-file=.env.example -- make dev`. Nothing secret touches disk.
- CI: prefer OIDC. Where a secret is unavoidable, use the 1Password GitHub Action with a *separate* CI service account scoped to GitHub-CI-CD.
