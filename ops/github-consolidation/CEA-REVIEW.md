# Connected-Energy-AI: repo review sheet

**Connected-Energy-AI (CEA) holds most of the valuable code.** It is the main source for the new org, not a leftover:
its active repos move first and with the most care, and every repo is backed up in full before anything moves.

## Step 0: full backup on the SSD (before anything else)
Every CEA repo, including all branches, tags and history, cloned as a mirror onto the Extreme SSD. It only reads from
GitHub and writes to the SSD, never to the Mac. Re-running it updates the backup. In Terminal on your Mac:
```bash
DEST="/Volumes/Extreme SSD/github-backup/Connected-Energy-AI"; mkdir -p "$DEST" && cd "$DEST" || exit 1
gh repo list Connected-Energy-AI --limit 500 --json name -q '.[].name' | while read -r r; do
  if [ -d "$r.git" ]; then git -C "$r.git" remote update --prune; else gh repo clone "Connected-Energy-AI/$r" "$r.git" -- --mirror; fi
done
echo "Backed up: $(ls -d *.git | wc -l | tr -d ' ') repos, $(du -sh . | cut -f1)"
```
It should report 80 repos. Some repos (for example `agent-central-config`) have keys and case files in their history,
so this backup is sensitive: keep the SSD private, and use an encrypted APFS volume if you can.

**Rule:** nothing in Connected-Energy-AI (CEA) is archived, transferred or deleted until its row is decided here and its
open work (PRs, unmerged branches) is merged or consciously dropped. Destinations follow `docs/GITHUB-BLUEPRINT.md` §3.
Inventory taken 2026-09-25: **80 repos**. 39 are active, 20 are already archived, and 21 are forks.

## Step 1: find the unmerged work (read-only, about 5 minutes)
In Terminal on your Mac:
```bash
cd ~/Code/repo-template && git pull
bash ops/github-consolidation/review_open_work.sh Connected-Energy-AI
```
It lists every repo with **open pull requests** or **branches that have commits `main` doesn't have**, and writes a CSV
report. Paste the list it prints into Claude. That list is the "needs review/merge" queue, worked one repo at a time.

## Step 2: decide each row
**Dup** means a repo with the same name also exists under `connectedagents-ai`: compare both copies first, keep the newer work.
**⚠ legal** means screen it for case material before moving (evidence stays in the evidence store, never in a code repo).
**⚠ secrets** means scan its history with gitleaks first; if it has keys, move the files only, not the history.

### Active repos (39): review, then fold into the new org
| Repo | Last push | Proposed destination | Notes |
|---|---|---|---|
| onewish-os | 2026-09-24 | `onewish` | Dup. The CEA copy is newest: bring its commits in first |
| CURSOR-CLOUD-AGENTS | 2026-09-22 | `platform/agents/` | Recent work: check its branches |
| codex-platform | 2026-09-03 | `platform` | Dup |
| LitigationForce.AI | 2026-08-02 | `litigationforce` | Dup · ⚠ legal |
| agent-skills-suite-v2 | 2026-07-23 | `platform/skills/` | Compare with `agent-skills-suite` |
| AI-Generated-Agents | 2026-07-10 | `platform/agents/` | |
| connected-dev-docs | 2026-07-03 | `config/docs/` | |
| github-migration | 2026-07-03 | `config` | Superseded by `ops/github-consolidation`; keep anything unique |
| chairman-life-os | 2026-07-03 | `onewish` | ⚠ secrets (personal data possible) |
| mcp-manager | 2026-07-03 | `platform/packages/` | |
| twinkle-tale-lab-v2 | 2026-07-02 | `lab` | |
| dev-new-project | 2026-07-02 | `lab` or drop | Likely a scaffold: check whether it has content |
| legal-case-assistant | 2026-07-02 | `litigationforce` | ⚠ legal |
| repo-template | 2026-07-02 | `config` | Dup: the `connectedagents-ai` copy is current |
| github-governance | 2026-07-02 | `config` | |
| gforce-repo-ops | 2026-07-02 | `config` | Dup |
| smithwick-ai-demo | 2026-07-02 | `lab` | Client demo? Confirm |
| tesla-energy-battlecards | 2026-07-02 | `powerconnection` | |
| antigravity-gcp-bootstrap | 2026-07-02 | `platform` | |
| autonomousagentos | 2026-07-02 | `onewish` | |
| desktop-md-ingest-2026-05-09 | 2026-07-02 | not GitHub: private raw store | Looks like a data dump (dated name) |
| connected-agents-control-plane | 2026-07-02 | `platform` | |
| lawsuite-monorepo | 2026-07-02 | `litigationforce` | ⚠ legal |
| skill-library-factory | 2026-07-02 | `platform/skills/` | |
| connected-agents-ai | 2026-07-02 | `platform` | Dup |
| agent-central-config | 2026-07-02 | `config` (files only) | Dup · ⚠ secrets · ⚠ legal (MIGRATION-PLAN step 0) |
| intelligence-os-vault | 2026-07-02 | `onewish` or raw store | "Vault": check whether it's notes (not code) |
| monorepo | 2026-07-02 | review | Unknown contents: open it first |
| .github-private | 2026-06-30 | `.github` | Org profile/templates |
| github-governance-agent | 2026-06-29 | `platform/agents/` | |
| energy-navigator-ai | 2026-05-18 | `powerconnection` | |
| empathic-voice-interface-starter | 2026-05-18 | `voice-agents` | |
| file-management-toolkit | 2026-05-18 | `config` | Overlaps `ops/dedup` |
| Litigation-Force-Interactive-Presentation | 2026-05-18 | `litigationforce` | ⚠ legal |
| Powermed-Marketing | 2026-05-18 | `powerconnection` | |
| powerconnectionai | 2026-05-18 | `powerconnection` | |
| powermedmarkeetingai-v0-modern-website-design | 2026-05-18 | `powerconnection` | Misspelled name; the folder gets a clean name |
| voiceagent.ai | 2026-05-18 | `voice-agents` | |
| powerconnectionaiapplications | 2026-03-03 | `powerconnection` | **Public**: check that nothing sensitive is exposed |

### Already archived (20): leave archived, read-only reference
my-vercel-neon-app-litigatioinforce1 · backstage · demo-api-scalar-galaxy-docs · case-commander-pro · connected-agents-platform ·
litforce-ai-gateway · litigationagentsmultimodalchat · powerconnectionodoo · mcpservers · Nexus-Blockchain · personal-website ·
luxechat-ai · onewishos-web-agents · website-webapp-component · xmcp · SlackAgents · litigationforce.nextjs-ai-chatbot ·
veritaslitigationtech · connectedenergyai · ai-sdk-starter-xai-litforce.
If any of these holds code a product still needs, copy it into that product's repo and note it here.

### Forks (21): don't carry over
gemini-cli · github-mcp-server · github-mcp-server2 · railway-skills · agentskills · antigravity-sdk-python · openai-agents-python ·
pi-skills · obsidian-folio-theme · plugins · skills · agent-skills-suite (**private fork: check for your own commits first**) ·
xai-chatbots-xmcp · DesktopCommanderMCP · inspector · cursor-notion-plugin · twinkle-tale-lab · agents · opcode ·
render-mcp-server · knowledge_graphos.
Keep a fork only if the Step 1 scan shows your own unmerged commits on it. Otherwise star the original project and archive the fork.

## Step 3: after each repo moves
Its PR in the new org merges → archive the CEA repo (Settings → Danger Zone → Archive, reversible) → tick it here.
When every row is ticked, remove app installs from CEA and leave the org read-only.
