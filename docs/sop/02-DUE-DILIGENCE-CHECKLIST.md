# SOP-02 · Technical due-diligence checklist (acquiring-CTO standard)

Mark each item: ✅ verified (cite evidence) · ⚠️ finding (→ T-04) · ❓ gap (why it couldn't be verified) · n/a.
**Tool:** where discovery comes from. `D` = `run_discovery.sh` on the Mac · `C` = `inventory_cloud.sh` · `K` = claude.ai connector · `A` = admin console · `Q` = ask the client.

## A. Entities and ownership
| # | Check | Tool |
|---|---|---|
| A1 | List every legal entity, and which accounts, domains and repos each owns | Q |
| A2 | Who is the **owner of record** for each critical account (not an ex-employee or contractor)? | A, Q |
| A3 | Code and IP ownership: are repos in company orgs, and are contractor agreements assigning IP on file? | A, Q |
| A4 | Billing: which card or entity pays for each service? Are there orphaned subscriptions? | A, Q |

## B. Identity and access
| # | Check | Tool |
|---|---|---|
| B1 | Identity providers in use (Entra ID, Okta, Google Workspace), and which one is primary | C, A |
| B2 | All tenants and domains per identity provider, verified domains, license SKUs and counts | C |
| B3 | MFA enforced for all admins and users. Conditional Access / context-aware access policies | A |
| B4 | Admin role holders: named, minimal count, no shared admin accounts | C, A |
| B5 | Break-glass accounts documented and protected | A, Q |
| B6 | SSO coverage: which apps use SSO, and which use local passwords | C, A |
| B7 | Stale users, guests and external collaborators | C, A |
| B8 | App registrations / OAuth apps with broad scopes or expired or long-lived secrets | C |
| B9 | Personal and consumer accounts used for business (outlook.com, personal Gmail, iCloud) | D, Q |
| B10 | **Orphaned logins:** accounts registered to an email the client can no longer receive (old company domain, lapsed mailbox) but still signed in somewhere. **P0:** add a second owner the client controls, export, then change the email or recover the domain *before the session expires* | D (browser/1Password), Q |

## C. Secrets and credentials
| # | Check | Tool |
|---|---|---|
| C1 | Secret store(s): 1Password (all accounts; item **titles and domains** only), Keychain, browser password managers (Chrome, Edge, Safari). Which is canonical? | D, Q |
| C2 | Secrets committed to git (current files **and history**) in every org | C, A (secret scanning) |
| C3 | Secrets inline in config files: MCP configs, `.env`, shell profiles, CI variables | D |
| C4 | API keys per provider: count, owner, last used, rotation date | A |
| C5 | SSH keys and PATs: where they live, their scope, their expiry | D, A |
| C6 | Push protection / secret scanning enabled | A |

## D. Domains, DNS and email
| # | Check | Tool |
|---|---|---|
| D1 | All domains: registrar (Namecheap, GoDaddy, Squarespace, Cloudflare, …), expiry, auto-renew, registrant entity. Registrars are found in browser history and 1Password | D, Q, A |
| D2 | DNS host (Cloudflare or other), and records for mail, SPF/DKIM/DMARC | A |
| D3 | Mail systems per domain (M365, Google), and forwarding rules to personal accounts | A |
| D4 | **Expired, parked or broken-mail domains.** Search the inbox for registrar "parked/canceled/renew" alerts and for mailer-daemon bounces per domain | K (mail search) |
| D5 | **Critical addresses on each domain:** court e-filing/service contacts, bank, registrar, tax agencies and investors that still send to a legacy address. Re-point them before changing or retiring a domain | K, Q, counsel |

## E. Cloud platforms and infrastructure
| # | Check | Tool |
|---|---|---|
| E1 | Azure subscriptions → resource groups → resources, and cost | C |
| E2 | GCP organization → projects → enabled services, Cloud Run/Functions, service accounts, billing | C |
| E3 | Other hosting: Vercel, Cloudflare, Render, Railway, Netlify, Hugging Face, AWS | C, Q |
| E4 | Databases and storage: Supabase, Neon, Firebase, Postgres, buckets. Backups and restore tested? | C, A |
| E5 | Environments: prod, staging, preview. Which are live, and which are abandoned? | C, A |
| E6 | Monitoring, logging, uptime alerts, budget alerts | A |
| E7 | CI/CD: pipelines, deploy credentials (OIDC vs stored keys) | C, A |

## F. Code and repositories
| # | Check | Tool |
|---|---|---|
| F1 | Every GitHub/GitLab/Bitbucket org and personal account. Repo counts: active, archived, forks | C, K |
| F2 | Duplicate repos (same name across orgs, near-identical names, folder-exploded repos) | K |
| F3 | Local clones: unpushed commits, uncommitted work, repos with no remote (**sole copies**) | D |
| F4 | Clones living in Desktop/Downloads/iCloud Documents (sync corruption risk) | D |
| F5 | Branch protection/rulesets, required reviews, CI status on the default branch | A |
| F6 | Installed GitHub Apps and their access (Claude, Codex, Cursor, Copilot, Devin, others) | C |
| F7 | Open PRs and branches left by AI agents (`claude/`, `codex/`, `cursor/`, `devin/`, `copilot/`) | K |
| F8 | Dependency and license risk (lockfiles present, Dependabot alerts) | A |
| F9 | Which repos are **products**, which are experiments, which are junk | Q + review |

## G. Data and documents
| # | Check | Tool |
|---|---|---|
| G1 | Storage locations: Mac local, iCloud Drive, Google Drive (each account), OneDrive/SharePoint (each tenant), Dropbox (each account), external drives, NAS | D, K |
| G2 | Size, file count and last-modified per location | D, K |
| G3 | **Crown-jewel data**: what it is, where every copy lives, and whether it's backed up | Q + D, K |
| G4 | Duplicates across locations (hash-based) | D, `archive-dedup-playbook` |
| G5 | Sensitive and regulated data: PII, PHI, financial, **privileged legal**. Where is it, and who can access it? | Q + review (flag only) |
| G6 | Sharing: public links, "anyone with the link", external shares | K, A |
| G7 | Backups: Time Machine or other. Last successful run. Off-site copy | D, Q |
| G8 | Retention or legal hold obligations | Q, counsel |

## H. AI tools and agent estate
| # | Check | Tool |
|---|---|---|
| H1 | AI accounts per tool and per login: Claude, ChatGPT/OpenAI, Grok/xAI, Perplexity, Gemini/NotebookLM/AI Studio, Copilot (consumer + M365), Cursor, Codex, Devin, Antigravity, and others | D, Q |
| H2 | Plan and seat per account (personal vs team/enterprise). Where does data retention and training opt-out stand? | A, Q |
| H3 | Projects, custom GPTs, Gems, Spaces, notebooks: count and purpose | Q + exports |
| H4 | Skills, plugins and MCP servers per tool: duplicates, broken ones, inline secrets | D |
| H5 | Instruction files: CLAUDE.md, AGENTS.md, GEMINI.md, .cursor/rules, copilot-instructions. Are they consistent? | D |
| H6 | Agent scratch work not in git (Antigravity scratch, Codex/Cursor worktrees, Grok) | D |
| H7 | Exports requested and received per account | Q |
| H8 | Agent automations: scheduled tasks, launchd jobs, Routines, Zapier/Make/n8n | D, Q |
| H9 | AI projects, GPTs, Spaces, Gems and notebooks found in browser history (`ai-projects.csv`), reconciled with the exports | D |
| H10 | Microsoft 365 Copilot per tenant, plus Copilot Studio agents | K, A |

## I. Endpoints (each Mac)
| # | Check | Tool |
|---|---|---|
| I1 | macOS version, FileVault on, firewall, auto-updates | D |
| I2 | Installed apps, Homebrew, global npm/pip packages, login items, LaunchAgents | D |
| I3 | Disk usage and largest regenerable folders | D |
| I4 | Cloud sync clients installed and signed-in accounts (iCloud, Drive, OneDrive, Dropbox) | D |
| I5 | Duplicate installs of dev tools (multiple claude/node/python) | D |
| I6 | Browsers and profiles (Chrome, Edge, Safari, Brave, Arc, Comet): which accounts each profile is signed into. Bookmarks reviewed | D |

## J. SaaS and business systems
| # | Check | Tool |
|---|---|---|
| J1 | CRM, PM, notes, comms: Notion (every workspace/account), Obsidian (every vault), Slack, Linear, HubSpot, Attio, Airtable, and others | D, K, Q |
| J1b | **Finance systems:** QuickBooks Online (company files, accountant access), Stripe, banks, payroll. Who has admin? Is MFA on? Which entity is each company file? | D, Q, A |
| J2 | For each: owner, plan, cost, SSO, data export available, and a decision | Q, A |
| J3 | Integrations and API keys between SaaS tools | A |

## K. Continuity and governance
| # | Check | Tool |
|---|---|---|
| K1 | Single points of failure (one person, one device, one account) | review |
| K2 | Documented runbooks: setup, rotation, recovery | review |
| K3 | Emergency access to the password manager and domain registrar | Q |
| K4 | Prior cleanup/governance attempts: find them and consolidate them, don't start another | D, K |

## Scoring
For each section: **Green** (no ⚠️ above P2) · **Amber** (P1/P2 findings) · **Red** (any P0 or > 25% ❓).
The section scores go at the top of the T-06 discovery report.
