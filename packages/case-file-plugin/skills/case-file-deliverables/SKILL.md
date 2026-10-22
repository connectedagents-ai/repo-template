---
name: case-file-deliverables
description: Build working legal materials from an organized case file (the output of case-file-organizer) - a sourced chronology, a who/what/when/why/how people and entity map, a claim-to-evidence matrix, deposition outlines per witness, a plain-language jury timeline, and a litigation-finance brief and deck outline. Use when the owner asks for a case summary, timeline, deposition prep, trial or jury materials, or a pitch for litigation funders.
---

# Case-file deliverables

Inputs: `/Volumes/Extreme SSD/cases/<matter>/run-*/index.csv` and `collection/`, plus `entities.txt`. Write every
output to `/Volumes/Extreme SSD/cases/<matter>/work-product/` as Markdown or DOCX (and CSV for tables), named
`<YYYY-MM-DD>_<deliverable>.md`. Mark every output "Prepared at the direction of counsel - draft for attorney review".

## Rules (non-negotiable)
- Every fact cites its source file path from the collection (and page or timestamp when known).
- Label each fact VERIFIED (read in a document or recording) or INFERRED (drawn from several), and never invent a
  date, amount, quote, party or event. A gap becomes an open question for the owner.
- Quotes are copied exactly from transcripts or documents, with the file path.
- Legal conclusions (claim strength, damages theory, settlement value) are drafts for the attorney, labeled as such.
- Nothing leaves the SSD: no uploads, shared links or emails unless the owner asks in a separate, explicit step.

## Deliverables (build what the owner asks for, one per file)
1. **Chronology** (CSV + Markdown): date · event · who · source file · VERIFIED/INFERRED. Newest research first in
   the CSV, oldest-first in the Markdown narrative.
2. **People and entity map**: each person or company, role, side, agreements signed (with dates and files), and
   first and last appearance in the record; plus a Mermaid diagram of relationships.
3. **Claim-to-evidence matrix**: for each claim the attorney names, the elements, the documents and testimony that
   support each element, the gaps, and the expected defenses with the documents that answer them.
4. **Deposition outline per witness**: background, agreements, timeline of that person's involvement, exhibits to
   show (file paths), questions grouped by topic, and admissions to lock in.
5. **Jury timeline**: one page, plain words, 10-15 dated events, each tied to one exhibit.
6. **Damages table**: each item, amount, basis, supporting files, VERIFIED/INFERRED.
7. **Litigation-finance brief and deck outline**: parties, claims, damages range, key evidence, risks, budget and
   timeline - for counsel to review before any funder sees it, and shared only under an NDA.

Finish with the confirmation list and the open questions for the owner and counsel.
