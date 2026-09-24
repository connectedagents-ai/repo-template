# T-02 · Engagement authorization (discovery and consolidation)
_Template. Have the client's counsel review it before use. This is not legal advice._

**Client:** ______ ("Client")  **Provider:** ______ ("Provider")  **Effective:** ______

1. **Scope.** Client authorizes Provider, and the AI agents Provider operates (e.g. Claude, Claude Code), to inventory the systems listed in Schedule A.
   Anything not listed is out of scope.
2. **Read-only discovery.** Discovery collects metadata only (names, sizes, dates, owners, hashes, configuration) and makes no changes.
   File contents are not read, except where Client asks for a specific file to be reviewed.
3. **Changes.** No change (move, rename, archive, delete, migrate, key rotation, permission change) is made without Client's written approval
   of the specific dry-run plan. Every change is logged with an undo path where technically possible.
4. **Secrets.** Provider records the existence and location of credentials, never their values. Credentials found exposed will be
   reported immediately so Client can rotate them.
4b. **Browser and password-manager metadata.** ☐ Client consents to reading browser history and bookmarks (Chrome, Edge, Safari and others)
   and 1Password item titles and domains to discover accounts. History is reduced to known-platform domains and AI project links. Full browsing
   history, search terms and password values are not exported.
5. **Sensitive data.** Data flagged as privileged, regulated or personal is not opened, copied or moved except as Client and counsel direct.
6. **Access.** Access granted to Provider is logged (T-05) and revoked at close.
7. **Outputs.** Discovery outputs are Client's property. At close they are ☐ delivered and deleted by Provider · ☐ retained for __ days, then deleted.
8. **AI processing.** Client acknowledges that the listed AI tools process metadata to produce inventories and reports, under those tools' commercial terms.

**Schedule A: in-scope systems**
| System | Account / tenant | Access type granted | Granted by | Date |
|---|---|---|---|---|
| | | | | |

Client signature ______  Date ______        Provider signature ______  Date ______
