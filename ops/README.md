# Consolidation runbook

Everything here is **dry-run by default**, copies or archives instead of deleting, and logs what it did. Run the steps in order.
**Run every command from the `ops/` folder:** `cd ~/Code/connectedagents-ai/repo-template/ops` (paths below are relative to it).
**Easiest way in:** `bash start.sh` opens a numbered menu of every safe (read-only or preview) step below, and saves the reports to `~/ops-reports/`.
(After consolidation, move `ops/` into `agent-central-config` and delete it from the template.)

| # | Step | Command / doc |
|---|---|---|
| 0 | **Rotate exposed secrets** and turn on push protection. **Do this first**: exposed credentials stay usable during every later step until rotated | `python3 secrets/find_plaintext_keys.py` lists which keys to rotate (names only) · `github-consolidation/MIGRATION-PLAN.md` step 0 · `../docs/GITHUB-SETUP.md` §1 |
| 00 | **New client?** Run the full SOP instead: `../docs/sop/01-CLIENT-ONBOARDING-SOP.md` + checklist `02-…` + templates `../docs/sop/templates/`. One-command discovery: `bash client-discovery/run_discovery.sh <client>`. Claude skill: `client-discovery/skill/client-discovery/` (copy to `~/.claude/skills/`) | |
| 0a | Inventory the cloud stack top-down (Entra → Azure → GCP → GitHub → Vercel → Cloudflare → 1Password), then decide D1–D6 | `bash cloud-inventory/inventory_cloud.sh` · `../docs/CLOUD-ARCHITECTURE.md` |
| 0b | Point legacy domains at powerconnection.com (web 301 + email via Google Workspace alias domains) | `domains/DOMAIN-CONSOLIDATION.md` · `bash domains/check_domains.sh` |
| 0c | Set up 1Password for agents (vault map, Touch ID CLI on the Mac, read-only service account for cloud sessions) | `1password/SETUP.md` |
| 1 | Audit the Mac: Claude, Codex, Cursor, Antigravity/Gemini, Grok, Perplexity, ChatGPT and Copilot files, git repos, disk hogs | `bash mac-cleanup/audit_claude_files.sh` → read `~/claude-audit-*.md` |
| 2 | Rescue agent scratch work into one inbox repo | `bash mac-cleanup/collect_ai_workspaces.sh` → `--apply` |
| 3 | Archive beginner-era Claude clutter and install the lean Claude Desktop config | `bash mac-cleanup/archive_claude_files.sh` → `--apply --install-desktop-config mac-cleanup/templates/claude_desktop_config.json` (undo: `~/Archive/claude-legacy-*/restore.sh`) |
| 3b | Reset the Claude app/account itself (export → chats, projects, artifacts, scheduled, skills, connectors, plugins, extensions, memory) | `mac-cleanup/CLAUDE-APP-RESET.md` |
| 3c | **Dedup** every surface (Mac, cloud folders, iCloud, and via their APIs Google Drive, OneDrive, SharePoint, pCloud): parallel dry-run scan → plan → approved archive (SSD, or each cloud's own archive folder) | `dedup/README.md` · `bash dedup/connect_cloud.sh` · `bash dedup/start_here.sh` |
| 3e | Microsoft tenants: finish the netzerolending.io move (mail done 2026-05-21, files not yet), personal OneDrive, retire the old tenant | `microsoft/TENANT-MIGRATION.md` |
| 3d | Wire **Codex + Grok CLI** (and every AI tool) to one core MCP set, one install per CLI, and audit agent access (bot vaults, AI OAuth apps) | `mcp/README.md` · `mcp/park_mcp_servers.py` |
| 4 | Reset global agent config | copy `mac-cleanup/templates/CLAUDE.md` + `settings.json` into `~/.claude/`. Configure the other CLIs per `../docs/GITHUB-SETUP.md` §4 |
| 5 | Set up the GitHub org, apps and CLI | `../docs/GITHUB-SETUP.md` |
| 6 | Move every other org or account into `connectedagents-ai` | `bash github-consolidation/migrate_to_connectedagents.sh Connected-Energy-AI` → `--apply` |
| 7 | Collapse ~280 repos into ~10 | `github-consolidation/MIGRATION-PLAN.md` step 2 · `bash github-consolidation/merge_into_monorepo.sh --apply <target> <owner/src> <path>` → PR → archive the source |
| 8 | Export Perplexity, ChatGPT/OpenAI, Grok/xAI, Copilot (3 accounts), Google (Gemini, NotebookLM, AI Studio), Antigravity, Claude → central library | `ai-library/README.md` · `python3 ai-library/ingest_library.py --source <tool> --account <label> <export>` |
| 8b | Settle the **Global Ontology** (names, tags, taxonomy, topology, schema) from the scattered ontology files | `../docs/GLOBAL-ONTOLOGY.md` |
| 9 | Clean up cloud agents' leftover branches and PRs (Codex, Cursor, Devin, Claude) | `github-consolidation/MIGRATION-PLAN.md` step 3 |
