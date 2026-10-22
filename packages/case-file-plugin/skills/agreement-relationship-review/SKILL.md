---
name: agreement-relationship-review
description: Review every agreement and related correspondence with one counterparty (e.g. a manufacturer, channel partner or former employee) from an organized case file, and produce a master agreement timeline, an obligation matrix, a breach analysis, an exclusivity assessment, a reliance evidence summary and a contract damages framework, with an evidence log. Use when the owner or counsel asks to analyze a business relationship, its agreements, breaches, exclusivity, reliance or contract damages.
---

# Agreement and relationship review

Inputs: the case file built by case-file-organizer (`collection/02-agreements`, `03-correspondence`,
`04-transcripts-recordings`, `index.csv`) and the counterparty's names in `entities.txt`. Outputs go to
`/Volumes/Extreme SSD/cases/<matter>/work-product/<YYYY-MM-DD>_<deliverable>.md`, marked "Author: <owner> · Review:
external counsel · Draft for attorney review". Same rules as case-file-deliverables: every point cites its file
(and page or timestamp), is labeled VERIFIED or INFERRED, and nothing is invented.

## 1. Identify and organize
Catalog the counterparty's agreements oldest first. Separate base agreements from amendments, addenda and renewals.
Tag each by type (NDA/MNDA, certified installer or dealer, distribution, consulting, licensee, employment). Link each
to the correspondence that acknowledges, clarifies or changes it.

## 2. Extract, per agreement (one table row per provision, with section number)
- **Relationship structure:** status granted, territory definitions, exclusivity, customer and lead routing, partner
  onboarding, inventory and material access, training and certification duties.
- **Confidentiality:** definition, permitted uses, duration, authorized recipients, return or destruction,
  notice of disclosure, exceptions.
- **Business practice:** training, installation standards, marketing and brand rules, customer service, warranty
  administration, partner management.
- **Termination and change:** termination rights, notice periods, cure provisions, post-termination duties,
  modification procedure, surviving terms, integration (entire-agreement) clause.
- **Reliance:** required investment, infrastructure, personnel, financial commitments, market development.

## 3. Methodology checks
Provisions clarified in correspondence · written acknowledgments of verbal changes · course of dealing · implied
good faith · integration clause effect on side promises · notice requirements met or missed · cross-reference with
recorded conversations and meeting notes.

## 4. Deliverables
1. **Master agreement timeline:** relationship progression, documents and key communications by date.
2. **Obligation matrix:** each counterparty duty · source section · performed / not performed / disputed · evidence.
3. **Breach analysis:** each required action versus what happened, with dates and files, and expected defenses.
4. **Exclusivity assessment:** what the documents and correspondence actually grant on territory and partners.
5. **Reliance evidence summary:** what the owner's company invested and committed because of each promise.
6. **Damages framework:** each contract-based damage item · measure · amount or method · supporting files.

## 5. Evidence log and triage
Keep `evidence-log.csv`: item · discovery date · found by · preservation method (original file, screenshot,
archive, export) · storage location on the SSD · sha256 (from index.csv) · related claim.
Rank findings by legal relevance to each pleaded claim, strength, closeness to key dates, and litigation value.
Flag for **immediate attorney review**: direct admissions, documents that contradict the other side's account,
timeline inconsistencies, and anything that may be privileged.
