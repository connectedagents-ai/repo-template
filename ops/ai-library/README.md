# Central AI library: one home for every skill, prompt, template, form and artifact

Target repo: **`connectedagents-ai/ai-library`** (private). It absorbs the skills, plugins and MCP repos listed in
`ops/github-consolidation/MIGRATION-PLAN.md`, plus everything exported from Perplexity, ChatGPT/OpenAI, Grok/xAI,
Claude, Codex, Cursor, Copilot, Devin and Antigravity.

```
ai-library/
├── skills/<name>/SKILL.md          portable Agent Skills: work in Claude, Codex, Cursor, Gemini/Antigravity, Copilot
├── prompts/<domain>/<name>.md       reusable prompts / system instructions (Custom GPTs, Perplexity Spaces, Grok, Claude Projects)
├── templates/<domain>/              document, deck and spreadsheet templates
├── forms/<domain>/                  intake forms, questionnaires, checklists
├── packages/                        plugins + MCP servers (code)
└── INDEX.md                         table of contents of the promoted material
```

Raw exports are **not** part of this repo. `ingest_library.py` files them into a **private raw store**
(default `~/Archive/ai-library-raw/`, or an external drive), which has `sources/<tool>/<account>/…`, `catalog.json` and its own
`INDEX.md`. The script refuses to write inside a git work tree unless you pass `--allow-git` for already-sanitized input.

**Workflow:** export from each account → `ingest_library.py` files it into the private raw store (with duplicates removed) → **review**
each item and copy only the reusable, sanitized pieces (no client data, secrets or privileged material) into this repo's `skills/`,
`prompts/`, `templates/` or `forms/` → commit those. Only promoted material is "the library"; the raw store never gets committed.

```bash
python3 ops/ai-library/ingest_library.py --source perplexity --account personal ~/Downloads/perplexity/   # dry run
python3 ops/ai-library/ingest_library.py --source perplexity --account personal ~/Downloads/perplexity/ --apply
```

## Export checklist, per account

Menu names change often. If one isn't where this says, search the tool's settings for "export" or "data".
Use one `--account` label per login (`personal`, `team`, `enterprise`, `api`, …) so you can always tell where something came from.

### Perplexity (+ Perplexity Computer)
| What | How to get it out | `--source` |
|---|---|---|
| Threads (Library) | Open each thread you want to keep → **Export** (Markdown/PDF/DOCX). For bulk, check Settings for an account data export and use it if your plan offers one | `perplexity` |
| Spaces | Copy each Space's **instructions** into `prompts/perplexity/<space>.md`. Download its uploaded files. Export its key threads | `perplexity` |
| Pages | Open each page → export or download | `perplexity` |
| Labs / Computer artifacts (apps, charts, sheets, docs) | Open the task → **Assets** / files panel → download each file. Perplexity Computer projects: download every output file plus the task prompt | `perplexity-computer` |
| Tasks / scheduled prompts | Copy each prompt into `prompts/perplexity/tasks/` | — |

### ChatGPT / OpenAI
| Account | How | `--source` / `--account` |
|---|---|---|
| ChatGPT personal (Plus/Pro) | Settings → Data controls → **Export data**. You get a zip by email; ingest the zip as-is (conversations are split into Markdown automatically) | `chatgpt` / `personal` |
| ChatGPT Team / Business / Enterprise | Workspace exports are an admin function (workspace settings, or the Enterprise Compliance API). If you're a member, ask the owner. Otherwise export the important chats one at a time | `chatgpt` / `team` |
| Custom GPTs | No bulk export: open each GPT → Configure → copy its instructions into `prompts/chatgpt/gpts/<name>.md`, and download its knowledge files | `chatgpt` |
| Projects / Canvas | Download canvases and project files. Copy the project instructions into `prompts/` | `chatgpt` |
| OpenAI platform (API) | Stored prompts, Assistants, files and vector stores are listed via the API (`/v1/assistants`, `/v1/files`). Save the JSON and ingest it. Also export org usage and API keys **names** only | `openai-platform` / `api` |

### Grok / xAI
| Account | How | `--source` / `--account` |
|---|---|---|
| Grok personal (grok.com / X) | grok.com → Settings → Data controls → **download / export your data**. Ingest the archive | `grok` / `personal` |
| Grok on X (in-app) | X → Settings → Your account → **Download an archive of your data** (includes Grok chats) | `grok` / `x` |
| Grok Business / Teams | Workspace exports are an admin function. Ask the workspace owner or use the admin console | `grok` / `teams` |
| Grok workspaces / projects, custom instructions | Copy the instructions into `prompts/grok/`. Download project files | `grok` |
| xAI console (API) | Save collections/files listings and your prompt library. **Never** export keys; rotate any key that was ever committed (see MIGRATION-PLAN Step 0) | `xai-console` / `api` |
| Grok terminal agent (CLI) | local files, covered by `ops/mac-cleanup/audit_claude_files.sh` §8 → `collect_ai_workspaces.sh` | `grok` / `cli` |

### Microsoft Copilot (three accounts)
| Account label | Type | How | `--account` |
|---|---|---|---|
| `outlook-personal` (the Outlook.com login) | Consumer Copilot (Microsoft account) | copilot.microsoft.com → sign in → export or delete chat history. Or account.microsoft.com → Privacy → download your data. Save Copilot Pages/Notebooks as .docx/.pdf | `outlook-personal` |
| `netzerolending` (netzerolending.io tenant) | Microsoft 365 Copilot (work, Entra ID) | Copilot chat history lives in the user's Exchange mailbox. A tenant admin exports it with **Microsoft Purview → eDiscovery / Content search** (filter to Copilot interactions). Copilot Pages and Loop files live in OneDrive/SharePoint: pull them with `archive-dedup-playbook/scripts/onedrive/inventory_onedrive.py` (Graph, already configured for this tenant) | `netzerolending` |
| `onewishlabs` (onewishlabs.com tenant) | Microsoft 365 Copilot (work) | Same as above, in that tenant. Also export any **Copilot Studio** agents (solution export from Power Platform) into `packages/copilot-studio/` | `onewishlabs` |

In every account, also copy saved prompts (Prompt Gallery / "Saved prompts") into `prompts/copilot/`.

Run each export through `ingest_library.py --source copilot --account <label>`.

> GitHub Copilot is a different product. Its seats and instructions belong to the `connectedagents-ai` org
> (see `docs/GITHUB-SETUP.md`). Its repo instructions come from `.github/copilot-instructions.md` → `AGENTS.md`.

### Google Antigravity / Gemini (account label `powerconnection`, the powerconnection.com Google login)
| What | Where | Action |
|---|---|---|
| Scratch projects | `~/.gemini/antigravity/scratch/*`, `playground/*` (the Chairman Agent was born here) | `ops/mac-cleanup/collect_ai_workspaces.sh` → `ai-workspace-inbox`, then promote to product repos |
| Agent artifacts (plans, walkthroughs, task lists, screenshots) | `~/.gemini/antigravity/brain/` (per-conversation folders) | `ingest_library.py --source antigravity --account powerconnection ~/.gemini/antigravity/brain` |
| Knowledge items | `~/.gemini/antigravity/knowledge/` (if present) | ingest the same way, then promote into `prompts/` or `skills/` |
| Global rules / workflows | `~/.gemini/GEMINI.md`, workspace `.agent/rules/`, `.agent/workflows/` | move into `agent-central-config` and replace each with a pointer to `AGENTS.md` |

### Google: every Google account (Gemini, NotebookLM, AI Studio, Drive)
Repeat these steps for **each** Google login (the powerconnection.com Workspace account, any personal Gmail, other Workspace domains),
with a distinct `--account` label for each.

| What | How to get it out | `--source` |
|---|---|---|
| Gemini app chats | **Google Takeout** → select "My Activity" → filter to *Gemini Apps* (Workspace: the admin may need to enable Takeout / Gemini activity) | `gemini` |
| Gems (custom Geminis) | No bulk export: open each Gem → copy its instructions into `prompts/gemini/gems/<name>.md`, and download its knowledge files | `gemini` |
| NotebookLM notebooks | No bulk export today. For each notebook: (1) note its **sources**. Drive docs are already in Drive; download uploaded PDFs; list the URLs. (2) Copy saved **notes** (or "convert to source" → it lands in Drive). (3) Download Audio/Video Overviews, mind maps and reports. (4) Save the notebook's custom instructions into `prompts/notebooklm/` | `notebooklm` |
| Google AI Studio | Saved prompts are stored in Drive, folder **"Google AI Studio"**: download that folder. Get-code snippets → `prompts/ai-studio/` | `ai-studio` |
| Drive files Gemini created (Docs, Sheets, Slides "Help me create…") | Inventory with `archive-dedup-playbook/scripts/google_drive/inventory_google_drive.py`, then export the ones worth keeping | `google-drive` |
| Gemini CLI | `~/.gemini/settings.json` (MCP servers), `~/.gemini/GEMINI.md`, `~/.gemini/commands/`: move into `agent-central-config`, and replace `GEMINI.md` with a pointer to `AGENTS.md` | `gemini-cli` |
| MCP config | `~/.gemini/antigravity/mcp_config.json` | replace inline keys with `op://` references, and keep the template in `agent-central-config/mcp-configs/` |

### Others
| Tool | How | `--source` |
|---|---|---|
| Claude (claude.ai) | Settings → Privacy → **Export data**. Copy Projects' instructions into `prompts/claude/`. Skills go straight into `skills/` | `claude` |
| Devin | Export session summaries and playbooks. Knowledge entries go into `prompts/devin/` | `devin` |
| Codex / Cursor / Antigravity | Local rules and prompts: `~/.codex/AGENTS.md`, `~/.codex/prompts/`, `.cursor/rules/`, `~/.gemini/GEMINI.md` | tool name |

## Promotion rules
- **Skill:** a repeatable procedure with steps. Use the Agent Skills format (`SKILL.md` with `name` + `description` front matter) so every tool can load it.
- **Prompt:** a single system/instruction block. One file per prompt, with front matter `source:` (tool + account) and `use-for:`.
- **Template / form:** the blank, reusable version only. Filled-in client copies go only to the designated private document vault, never
  into this repo or a product repo (AGENTS.md §4: no client PII or privileged material in code repos).
- One canonical copy per item. If two tools had variants, merge them into the better one and note `supersedes:` in its front matter.
- No secrets, no client PII, no privileged litigation material in this repo.
