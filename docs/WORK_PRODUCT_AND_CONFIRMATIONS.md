# Segmenting and capturing work product and confirmations

Owner direction (2026-10-22): every piece of work product and every confirmation is segmented and captured, so that
nothing is lost between sessions and every approval or send can be proven later.

## 1. Segments
| Code | Segment | What goes in it | Where it is stored (durable) |
|---|---|---|---|
| WP-PRIV | Privileged work product | Drafts for counsel, strategy, damages reasoning, deposition prep, case summaries, claim registers, timelines built for litigation | LEGAL MATTERS/<matter>/08_Drafts_For_Counsel (or 07_Damages, 10_Deposition_Prep, 04_Timelines) |
| WP-OPS | Operational work product | Indexes, workbooks, maps, inventories, regex/classifier outputs, plans | Financial master subfolder by domain; agent logs in z21 Workpapers |
| PROD | Production material | Anything sent or to be sent to opposing counsel (Bates sets, responses, cover letters, privilege log) | 14 Mullins Production (frozen once served); a shortcut in LEGAL MATTERS/MULLINS/06 |
| CNF | Confirmations | Owner approvals (verbatim), sends, deliveries, court or IRS receipts, e-file acceptances, Bates logs, signed and served copies | Ledger row (below) + the evidence file in the matter or tax folder |
| RCPT | Agent receipts | Each agent run: inputs, outputs, files touched, approvals used, failures | Ledger row + log file in z21 Workpapers |

Privileged work product is never produced, emailed or pasted into a general-purpose AI memory. Whether an item is
privileged is decided by counsel; agents only label it `privilege_status: pending_review`.
Label on WP-PRIV documents: "PRIVILEGED & CONFIDENTIAL – prepared in anticipation of litigation – counsel to confirm".

## 2. The ledger (one place, no new files)
The ledger is the **Ledger** tab of the existing master plan sheet "00 MASTER PLAN + REQUIREMENTS REGISTER"
(https://docs.google.com/spreadsheets/d/111QyaBWdGU7wkgxu4D2QDw6XMXX-gEVpgrGUJtp_6WA/edit).

Columns:
- `ledger_id`: CNF-YYYYMMDD-NNN / WP-YYYYMMDD-NNN / RCPT-YYYYMMDD-NNN
- `timestamp` (UTC)
- `segment`
- `type`: approval, send, delivery, receipt, filing, e-file, work-product, agent-run
- `matter_or_project`: MAT-/PRJ- ID
- `description`
- `owner_words_verbatim`: required for approvals
- `evidence_link`: Drive file id, Gmail message id or URL
- `stored_at`
- `produced_by`: owner, agent name or counterparty
- `privilege_status`
- `sha256`: if a file
- `supersedes`

## 3. Capture rules (every agent, every tool)
1. **Owner approvals:** record the owner's exact words, with the date and the scope they cover, in the same turn.
   Example: "go copy" (2026-10-22) covers copying scratchpad deliverables into the two Drive roots; it covers no moves or deletes.
2. **Sends:** every email or letter sent gets a CNF row with the sent-mail message id and the attachment list. The
   attachments are hashed before sending.
3. **Third-party confirmations:** each one gets a CNF row and the original saved to the matter or tax folder. These
   include court e-file receipts, certified-mail green cards, IRS acceptances and notices, bank confirmations and opposing counsel's acknowledgments.
4. **Work product:** created files get a WP row (segment, matter, where stored). WP-PRIV is never stored outside LEGAL MATTERS.
5. **Agent runs:** each run's final report becomes an RCPT row: what ran, what changed, what failed, what is blocked.
6. **No row, no proof:** a send, approval or deliverable without a ledger row is treated as not done.
