# Operating plan: how agents keep work from getting lost (owner: Robbie Bailey)

This file holds process only. Case facts, amounts and client data live in Google Drive, never in this repo.

## 1. Why work got lost (from the Oct 20–22, 2026 session logs)
1. **Agents wrote to the cloud container.** Memory, scratchpad files and outputs were saved inside a temporary
   cloud container. That container is deleted when the session ends, so everything in it disappears.
2. **Long chats get summarized.** Each summary kept folder IDs but dropped the key fact: there is ONE master folder.
3. **Agents built new structures instead of using the owner's.** They created 00_MASTER_INTAKE, LEGAL MATTERS and
   00 BAILEY MASTER, plus new trackers, when the owner's folder and documents already existed.
4. **Agents re-asked settled facts** because the answers were not in a place every session reads at start.
5. **Agent-made rules blocked the actual job.** "Legal hold: never move" plus per-batch approval meant files were
   never filed, and the owner was never shown a batch to approve.

## 2. Where things live (the only durable stores)
| What | Where | Durable? |
|---|---|---|
| All files, outputs, reports, workbooks | Google Drive master folder "1Bailey Financials 2018-2026 YTD - Tax, IRS, Assets and Liabilities Only" (https://drive.google.com/drive/folders/121X1o4QU7r5YPs8uB58d878XAfqNGtSj), in its existing subfolders | Yes |
| Settled facts | Drive doc "00 ESTABLISHED FACTS" (in 14 Mullins / 07 Working) | Yes |
| Rules, start-up steps, task board | Drive doc "00 READ FIRST" (in 07 Working), this file, `AGENTS.md` | Yes |
| Artifact list | Drive sheet "project registry" (link in `AGENTS.md`) | Yes |
| Cloud scratchpad, `/root/.claude/*`, chat memory | the container | **No: never the only copy** |

Never create a new master folder, tracker, registry or facts document. Update the existing one in place.

## 3. Session start (every agent, every tool)
1. Read `AGENTS.md`, this file, "00 READ FIRST" and "00 ESTABLISHED FACTS".
2. Read the task board in "00 READ FIRST". Continue open tasks; do not restart them.
3. Search those documents before asking the owner anything. Ask only what none of them answers, and batch all
   questions at the end.

## 4. While working
- Save every deliverable into the master folder as it is produced. A deliverable that exists only in the
  scratchpad does not count as done.
- Searching, reading, indexing and copying files into the master folder may proceed without asking.
  Moving or deleting files needs the owner's yes, given once per plan, not once per batch.
- Log every write (file id, old place, new place) in the master folder's "z21 Workpapers and Cleanup Logs".

## 5. Session end (or every ~2 hours)
1. Update the task board in "00 READ FIRST": done, in progress (with the next step), blocked (with what is needed).
2. Record new facts the owner gave in "00 ESTABLISHED FACTS" the same day.
3. Add new or superseded artifacts to the registry.
4. Confirm that nothing exists only in the scratchpad.

## 6. Search plan: owner's information the agents asked for
The owner says the filed returns and supporting records are on these surfaces: Google Drive (My Drive, Shared
drives, shared with me), Gmail (every account), Outlook/OneDrive/SharePoint, the Mac and SSD, the IRS online
account and QuickBooks Online.

| Item | Surfaces | Who |
|---|---|---|
| Filed returns TY2018–2025 (1040, 1065, 1120-S, K-1s), e-file acceptances, signed 8879s, CPA transmittals | Drive fullText, Gmail (DRDA / Doug Dickey, RSM, Intuit, "accepted", "Submission ID"), Outlook, Mac/SSD | agent; Mac/SSD needs the owner to run the script |
| IRS transcripts, notices, OIC, levies, liens | Drive "06 IRS Notices and Liens", Gmail/Outlook (irs.gov), IRS online account | agent; IRS login is the owner's |
| 2023 bank reconciliations (about May 2024) | QuickBooks Online: Settings > Reconcile > History; Gmail from the bookkeeper or CPA | QuickBooks login is the owner's |
| Missing statements (0282 from Mar 2023, J.P. Morgan, accounts 6000/6468/3862), vehicle repossession letters | Drive, Gmail/Outlook, bank sites | agent, then the owner for bank downloads |

Results go into the master folder (index sheet in z21 Workpapers) and onto the task board. Each found item is
recorded as a fact, so it is never asked again.
