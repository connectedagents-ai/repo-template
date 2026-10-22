# One evidence base, seven audience outputs

The owner needs the same financial and legal facts presented to several audiences. The rule: **one canonical
dataset, many views.** No audience gets its own version of the facts. Any number stated to the IRS, a court, a
creditor or opposing counsel must trace to the same evidence row. A figure that differs between audiences (for
example, the stale 433-F numbers) is a liability, so it is corrected at the source and every view is rebuilt.

This file holds the process only. All data and outputs live in the master Drive folder
(https://drive.google.com/drive/folders/121X1o4QU7r5YPs8uB58d878XAfqNGtSj).

## Existing systems to reuse (do not recreate)
- **Financial Audit & Tax subsystem** (LitigationForce repo, `financial-audit-tax/`). Agents: financial_audit_forensic_damages,
  irs_letters, oic_agent, tax_evidence_prep_agent, nol_oic_treatment_specialist, bankruptcy_calculator_type_chooser,
  entity_account_master_file, damages_modeler, evidence_linker.
- **Org Chart System** (`org-chart-system/`): a canonical-dataset.yaml with confidence scores and litigation-exhibit
  output (threshold 0.95).
- **This repo's skills:** discovery-production, bank-statement-audit, financial-statements-prep, tax-review-gap-analysis,
  legal-matter-summary, manifest-audit.

## Canonical layer (built once, feeds everything)
| Dataset | Source today |
|---|---|
| Entity and account master (entity, EIN last 4, accounts by timeline) | entity_account_master_file; Accounts tab of the manifest |
| Statement coverage and monthly true-up, Jan 2022 to date | Mullins master workbook (Monthly_TrueUp, Gap_Analysis) |
| Tax filing status by year and filer | 00 TAX RETURNS FOUND; TAX_GAP_GRID |
| Assets and liabilities register, each row with an evidence label | assets_liabilities map; IRS lien/levy records |
| Facts register | 00 ESTABLISHED FACTS (with the Accuracy Register) |
| Evidence index (every fact → file id, Bates if produced, confidence) | evidence_linker |

## Audience outputs
| # | Audience | Purpose | Contents | Evidence bar | Gate |
|---|---|---|---|---|---|
| 1 | IRS (exam/audit, collections) | Defend returns; OIC resubmission; 433-A/F | Year × filer status, income/expense support by year, reconciliations, NOL schedule, asset/liability statement, IRS letter log | Signed or filed documents and statements only (≥0.95) | CPA (Doug Dickey) reviews; owner signs |
| 2 | Mullins counsel (DeBard): compliance with the Aug 31 order compelling production | Show complete, good-faith production; answer deficiencies | Request-by-request response grid, Bates log, gap list with written reasons, supplement schedule | Produced documents only; no characterizations | Owner sends; attorney reviews privilege |
| 3 | Creditors and judgment holders (debtor-facing workout) | Settlement or payment-plan proposals | Financial statement, liquidation vs. plan comparison, proposed terms per creditor | Same numbers as #1; no unsupported asset values | Owner approves every number and term |
| 4 | Damages (Tesla program and other claims) | Quantify losses | Damage model by entity, division, state, city, partner and deal; assumptions table | Each input tagged with evidence and confidence; assumptions separated from facts | Counsel review; RICO stays PARKED |
| 5 | Legal case summary (counsel, new chat, court) | Posture, deadlines, exposure across matters | Per-matter summary, deadline calendar, cross-matter conflicts | Facts register only | Owner/counsel |
| 6 | Deposition preparation (when counterparties depose the owner) | Testimony consistent with every prior statement | Prior-statement index (IRS filings, 433s, discovery responses, declarations), timeline, likely questions, documents per topic | Prior sworn or filed statements, verbatim | Attorney-led |
| 7 | Damage-model reasoning (expert backup) | Defend every number in #4 | Step-by-step calculation, source per input, sensitivity, rebuttal notes | ≥0.90; anything lower flagged | Expert/counsel |

## Consistency checks (run before any output leaves)
1. Every amount ties to the canonical layer. If it doesn't, stop.
2. Cross-audience diff: compare the IRS figures (#1), the creditor statement (#3), discovery responses (#2) and prior
   sworn statements (#6). Every difference is explained or corrected at the source.
3. Privilege screen: #4, #5, #6 and #7 are work product and are never produced. #2 produces responsive records
   only, with a privilege log.
4. Settled facts are never re-argued in any output.
