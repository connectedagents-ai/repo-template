---
name: client-discovery
description: Run the client digital-estate discovery (SOP-01/SOP-02) on a client's Mac and connected cloud accounts. Inventories devices, accounts, identity, cloud, code, data, AI tools, projects, skills, browsers, 1Password titles, domains and finance systems, read-only, then drafts the platform register, findings and discovery report. Use when onboarding a new client or re-auditing an existing one.
---

# Client discovery

Follow `docs/sop/01-CLIENT-ONBOARDING-SOP.md` from the repo that ships this skill (`connectedagents-ai/repo-template`).

## Before running anything
1. Confirm that T-02 (engagement authorization) is signed and lists the in-scope systems. If browser history or 1Password are in scope, clause 4b must be ticked.
2. Confirm you are on the client's Mac (Claude Desktop or `claude remote-control`), not a cloud container.
3. Open T-05 (access log) and record the access you are using.

## Run (read-only)
1. `bash ops/client-discovery/run_discovery.sh <client-slug>` → bundle in `~/client-discovery/<client>-<date>/`.
2. From a cloud session with connectors, inventory Google Drive, Microsoft 365 / SharePoint, Notion and GitHub (metadata only).
3. List the exports the client must trigger (`ops/ai-library/README.md`) and track them in T-03 notes.

## Analyze
1. Merge `T-03-platform-register.csv` with connector and cloud results. One row per platform and account, deduplicated.
2. Work through `docs/sop/02-DUE-DILIGENCE-CHECKLIST.md`. Mark each item ✅/⚠️/❓ with evidence.
3. File findings in T-04 with P0–P3 severity. Tell the client about P0s (exposed secrets, admins without MFA, sole copies) right away.
4. Draft the T-06 discovery report: scorecard, topology (`docs/CLOUD-ARCHITECTURE.md` format), decisions needed, plan.

## Rules
- Never read or copy secret values or file contents. Record names, locations and metadata only.
- No changes during discovery. Any cleanup is a separate, approved dry-run → apply step with a manifest and an undo path.
- Flag privileged, regulated or personal data. Don't open it.
