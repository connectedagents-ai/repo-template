# LEGAL MATTERS: folder structure and ontology

Built on the owner's CURSOR-CLOUD-AGENTS / LitigationForce foundation:
- `cases/{Case}/` workspaces
- claim typing and the four-gate evaluator
- combined timelines (master → by claim → by party)
- immutable raw evidence with hashed derivatives
- a knowledge graph of Evidence, Claim, Party, PredicateAct and TimelineEvent

This file holds the structure only. Case content lives in the Drive LEGAL MATTERS folder
(https://drive.google.com/drive/folders/1Pv-i27zSgoAMYC1JvHaVkos98jpYqL53).

## 1. Status vocabulary (stops "planned" from reading as "filed")
Every matter, claim and track has exactly one `status`:
`FILED-ACTIVE` · `POST-JUDGMENT` · `ON-APPEAL` · `CLOSED` · `POTENTIAL-NOT-FILED` · `PARKED`.
The foundation repo describes Tesla tracks A, B and C as litigation. Their status here is `POTENTIAL-NOT-FILED`,
and RICO is `PARKED`. No suit has been filed and there is no litigation funding. These are settled facts and are not
re-asked.

## 2. Matters (keys)
| Key | Matter | Status |
|---|---|---|
| MUL | Mullins v. Connected Solar, 2024-CI-17193 | POST-JUDGMENT (compelled production) |
| WIN | Winchell | ON-APPEAL |
| TSL | Tesla program umbrella (Tesla, Vikta, Solytx, related parties) | POTENTIAL-NOT-FILED; RICO PARKED |
| CUS | Customer disputes | per matter |
| IRS | IRS collection / OIC | ACTIVE (administrative) |
| EVC | Evictions and other | per matter |
Matters sit under one program when they share facts (TSL umbrella). A document shared by several matters is stored
once in its home matter, with Drive shortcuts in the others.

## 3. Folder template (identical in every matter)
```
LEGAL MATTERS/
  <KEY> <Matter name>/
    00_Matter_Card          one doc: parties (IDs), forum, cause no., status, deadlines, counsel, links
    01_Pleadings_Orders     court filings and orders (served or filed copies only)
    02_Evidence_Raw         originals, never edited; sha256 recorded in the evidence index
    03_Evidence_Derivatives OCR text, extracts, redacted copies (each points to its raw file)
    04_Timelines            master timeline + views by claim and by party
    05_Claims_Defenses      claim register: elements → facts → evidence
    06_Discovery_Production requests, responses, Bates sets, privilege log (MUL: the existing 14 Mullins Production)
    07_Damages              model inputs, calculations, reasoning (audience outputs 4 and 7)
    08_Drafts_For_Counsel   work product: drafts only, attorney review required
    09_Correspondence       letters and emails with counsel, courts, opposing parties
    10_Deposition_Prep      prior-statement index, topics, exhibits (audience output 6)
```
For MUL, the existing frozen folder `14 Mullins Production 2024-CI-17193` in the financial master folder stays where it is.
Its `06_Discovery_Production` holds a shortcut to it, never a copy or a move.

## 4. Ontology (node and edge types)
- **Nodes:** Matter, Party (person / entity, with ID), Claim, Element, Fact, Evidence, TimelineEvent, Deadline,
  Production (Bates range), Contract, Account, DamageItem, PredicateAct (PARKED).
- **Edges:**
  - Matter–has→Claim–requires→Element–proven_by→Fact–supported_by→Evidence
  - TimelineEvent–cites→Evidence
  - Party–party_to→Matter
  - Contract–binds→Party
  - DamageItem–derived_from→Fact
  - Evidence–produced_as→Production
- **Claim typing on every statement:**
  - `FACT`: needs the fact check
  - `INFERENCE`: fact check + logic
  - `OPINION`: ethics review
  - `LEGAL_CONCLUSION`: citation + logic + ethics, and an attorney decides
- **Confidence scale** (from the org-chart system):
  - 1.00: signed primary document
  - 0.95: authenticated original; the minimum for litigation exhibits and the IRS
  - 0.90 / 0.85: investor or internal use
  - below 0.80: internal only, flagged
- **Evidence labels:** VERIFIED · STATEMENT · OWNER-STATED · DISPUTED · AI-GENERATED (non-source).
- **Production scope:** RESPONSIVE · OUT-OF-SCOPE (with a written reason) · ATTORNEY-REVIEW → privilege log.

## 5. Naming
`<KEY>_<YYYY-MM-DD>_<doctype>_<short-descriptor>`, for example `MUL_2026-08-31_order_compel-production`.
No "-v2", "-final" or "copy" suffixes; use the version history. Never use "do not say" style labels.

## 6. Rules
- Raw evidence is immutable; only derivatives are created.
- Privilege calls, filings, productions and anything sent need a human checkpoint.
- Every output passes the cross-audience consistency check in `AUDIENCE_OUTPUTS.md`.
