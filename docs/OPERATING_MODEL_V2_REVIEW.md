# Review: master-ontology-v2 (Perplexity Instance Operating Model), 2026-10-22

Reviewed: 00–09, 11, 12, 14–26, the README and the uploaded template cards. Cross-checked against `AGENTS.md`,
`OPERATING_PLAN.md`, `AUDIENCE_OUTPUTS.md`, `LEGAL_MATTERS_ONTOLOGY.md`, `templates/*` and the owner's settled facts.
This review holds structure only. It contains no case facts, amounts, account numbers or personal data, and the uploads
were not copied into this repo.

## 1. Verdict
**Adopt v2 as the control plane.** It is the most complete version of the owner's model: projects first, provenance
by default, privilege intake, claim typing and confidence thresholds. It already agrees with this repo on IDs
(PRJ-, AGT-, GATE-, CEE-, CEP-), the evaluator gates and the confidence scale. Before v2 moves from `draft` to
`active` (24 §Release), apply the patches in §7.

How the Claude Code docs plug in. They implement v2; they are not a second model.
| v2 layer | Claude Code doc that implements it |
|---|---|
| 01 project registry, matter layer (missing) | `LEGAL_MATTERS_ONTOLOGY.md` §2 matter keys and status vocabulary → becomes v2's matter registry (`MAT-<KEY>`) |
| 06 document taxonomy, 11 ingestion | `LEGAL_MATTERS_ONTOLOGY.md` §3 folder template and §5 naming; `AGENTS.md` intake rule |
| 10 Obsidian templates | `docs/templates/*` (+ `REVIEW.md`), the same cards with fixes |
| 12 QA, 16 confidence, 19 evaluator | `AUDIENCE_OUTPUTS.md` consistency checks; evidence labels |
| 04 agents, 05 workflows | repo skills: discovery-production, bank-statement-audit, financial-statements-prep, tax-review-gap-analysis, legal-matter-summary, manifest-audit |
| 00 source-of-truth rule | `OPERATING_PLAN.md` §2 durable stores (Drive master, facts register, task board) |
Rule: v2 registries stay the master. Repo docs cite v2 IDs and do not define rival ones. Where they differ today,
§7 changes v2 to carry the settled facts.

## 2. Gaps
| # | Gap | Where | Fix |
|---|---|---|---|
| G1 | **Mullins 2024-CI-17193** (post-judgment, active court order compelling production) has no project or matter record. The highest-deadline matter is absent. | 01, 23, 26 | Add `MAT-MUL` (§7) |
| G2 | **Winchell** absent | 01 | Add `MAT-WIN` |
| G3 | **Lee 23-DCV-301569** absent | 01 | Add `MAT-LEE` |
| G4 | **IRS collection / OIC** has no matter. Only the tax project and subsystem exist. | 01, 18 | Add `MAT-IRS` under `PRJ-FIN-INCOMETAX-ROBERTBAILEY` |
| G5 | **Evictions** (and customer disputes) absent | 01 | Add `MAT-EVC`, `MAT-CUS` |
| G6 | **No matter ID prefix.** 09 constrains `Matter.matter_id`, but 15 has no `MAT-` and data uses a free-text `BAILEY-TESLA`. | 15, 09, 26, timelines | `MAT-<KEY>`; `BAILEY-TESLA` → `MAT-TSL` |
| G7 | **Drive master folder** (121X1o4QU7r5YPs8uB58d878XAfqNGtSj), **LEGAL MATTERS** root (1Pv-i27zSgoAMYC1JvHaVkos98jpYqL53) and **00_MASTER_INTAKE** are absent. `google_drive` is one generic row, and raw docs point to `raw_docs/` and local paths. | 00, 03, 11, 17, 18 | Register them as source systems; make them the raw and durable targets |
| G8 | **Claude Code** is absent as a surface (08 routes only Perplexity / Claude Desktop) and as an agent (04). It is the route doing repo, Drive and skill work today. | 03, 04, 08 | Add `claude_code` source, `AGT-CLAUDE-CODE`, routing rows |
| G9 | Sources referenced but not registered: `linear_alt`, `asana_mcp_merge`, `canva__pipedream`, `google_docs__pipedream`, `airtop__pipedream`, Gmail, Cloud Vision. Also missing: 1Password (secrets rule) and the IRS online account. | 01, 04, 08 vs 03 | Register them, or replace the references |
| G10 | Prefixes in use but not in 15: `FIN-TAX-` (tax-case card), `SUBSYS-` (18), `TRACK-` (26). 15 says "no new prefix without an entry". | 15 | Add them |
| G11 | Two gate styles: `GATE-*` (v2) and lowercase `sensitive_document_review`, `graph_import_review`, `crm_write_approval` … (05). None defined (13 missing). | 05, 13 | One `GATE-` list in 13 |
| G12 | Document taxonomy lacks production/IRS types: Bates set, production log, IRS transcript, collection information statement (433-A/F), federal tax lien, levy. It also lacks the fields `evidence_label` and `production_scope`. | 06 | Add (§7) |
| G13 | 24 checklist and the README folder map stop at 24. They omit 25 and 26; 15 points CLM- at "17-claim-taxonomy" (the claim taxonomy is 25). | 15, 24, README | Fix the references |
| G14 | Repo registry lists only an external reference repo and LitigationForce. It is missing the `connectedagents-ai` org repos (this repo included), the only allowed org. | 07 | Add `REPO-TECH-REPO-TEMPLATE`; inventory the org |
| G15 | The status vocabulary has no administrative value for the IRS (the repo says "ACTIVE (administrative)", outside its own list). | repo §1, v2 | Add `ADMINISTRATIVE-ACTIVE` to both |

## 3. Conflicts with settled facts
| # | Conflict | Settled position | Change |
|---|---|---|---|
| C1 | `PRJ-LF-CENERGY-TESLA` titled "CONNECTED ENERGY VS TESLA INC ET AL", `status: active`, "litigation matter". It reads as filed litigation. Timelines title it "Bailey v. Tesla et al." | No suit filed; no funding | Title "Tesla program: potential claims (not filed)"; project `status: active` means *work* is active, while matter `MAT-TSL` carries `POTENTIAL-NOT-FILED` |
| C2 | 26 tracks have **no status field**. The forum wording ("arbitration track", "court-based litigation") reads as pending proceedings. | Forums assigned by contract; nothing filed | Each track: `status: POTENTIAL-NOT-FILED`, `forum_basis: contract`, `filed: false` |
| C3 | RICO-forward framing: CLM-RICO listed first, with the rule "RICO is the ceiling, not the floor"; Track A/C list CLM-RICO; timeline `track: federal_rico`; `rico_analysis` is a primary use (03, 17); project tags `rico`, `predicate-acts`; 22 dashboard shows "predicate act status"; PA-/RICO- prefixes active | RICO is PARKED | `CLM-RICO status: PARKED`; replace the rule with "every claim stands on its own without RICO"; drop RICO from track `related_claims` (keep as `parked_claims`); PredicateAct nodes and PA-/RICO- prefixes stay readable, marked `PARKED` |
| C4 | 09 edge verbs `CONSPIRED_WITH`, `DIVERTED_FROM`, `CIRCUMVENTED` state allegations as graph facts | Not filed; claim typing required | Add `assertion_type` (FACT / INFERENCE / OPINION / LEGAL_CONCLUSION) and `evidence_label` to these edges, or prefix them `ALLEGED_` |
| C5 | `CES-` = Connected Energy *service line*. It collides with "CES" in existing filenames and with Champion Energy Services as an entity name. | One meaning per prefix | Rename to `CESVC-`; `CES` stays free text |
| C6 | `SRC-` is used for both canonical-dataset sources and raw-doc metadata (15 collision note; the dataset already uses SRC-001…013) | One namespace per registry | Split: `SRC-CEE-#####` (canonical dataset), `SRC-DOC-#####` (raw-doc metadata); keep a legacy map from `SRC-001` |
| C7 | 20 privilege-by-default "block production … until cleared", with no production-scope rule. Read alone, this can become withholding. | Produce everything responsive; exclusions only out-of-scope, in writing; privilege → licensed attorney + privilege log | Add `production_scope: RESPONSIVE / OUT-OF-SCOPE (written reason) / ATTORNEY-REVIEW → privilege log`. Privilege-by-default governs indexing and export, not the decision to produce. |
| C8 | 14 asks "Which records should never leave local storage?" | No never-say / do-not-send labels | Rephrase as storage tiers (`sensitivity`, `storage: drive_master / 1password / legal_matters`); never name a list "never …" |
| C9 | `PRJ-FIN-INCOMETAX-ROBERTBAILEY` `status: proposed` | Personal TY2023–2025 not filed; OIC needs recast | `status: active` |
| C10 | Raw targets `raw_docs/`, `~/Docs/legal-case-package/…` (dataset SRC-001) | One Drive master; intake via 00_MASTER_INTAKE | Raw target = Drive (G7); local paths become mirrors only |

## 4. Per-file comments
| File | Comment |
|---|---|
| 00 operating model | Sound. Add Drive master / LEGAL MATTERS as the primary store for legal evidence and financial data, and Claude Code to connector-aware execution. Lifecycle step 6 "filings" needs `GATE-FILING-REVIEW` and an attorney. |
| 01 project registry | Good preservation rule. Fix C1 and C9; add a `matters:` block (G1–G5). Fix the `ENTITES`/`TECHSTACH`/`CONNECTD` typos per `NAMING-CONVENTIONS.md`. |
| 02 space map | The 01 Space sub-scopes cover only Tesla; add a "matters" sub-scope (MUL, WIN, LEE, IRS, EVC). |
| 03 source registry | Add G7–G9. `litigationforce_ai` primary use `rico_analysis` → `claims_analysis` (C3). |
| 04 agent registry | Add `AGT-CLAUDE-CODE`. Base agents lack the escalation and failure-mode fields that 12 requires. v2 evaluator agents lack inputs/outputs. |
| 05 workflow registry | Unify gate names (G11). WF-PRIVILEGE-INTAKE: add the production-scope step (C7). Add WF-PRODUCTION (discovery-production skill) and WF-MATTER-BOOTSTRAP. |
| 06 document taxonomy | Add G12 types and fields. `oic_filing` is good. Add `document_date` beside `captured_at` (per REVIEW.md). |
| 07 repo registry | Add the org repos (G14). The LitigationForce repo URL is still null. |
| 08 routing matrix | Add Claude Code rows (§7). Gmail is "Claude Desktop" here but connected in Claude Code too; route by session. |
| 09 neo4j schema | Received. Matter constraint is good; add an index on `Matter.status` and `Claim.status`. Apply C4. `Track` needs a `status` property. Vector dims are a placeholder; keep. |
| 11 ingestion | Good separation rules. Raw target → Drive (C10). Classification needs `matter_id` beside `project_id`. |
| 12 QA | Consistent with the repo. Add the cross-audience consistency check from `AUDIENCE_OUTPUTS.md`. |
| 14 open questions | Many are already answered (§5). |
| 15 ID prefixes | Add MAT-, FIN-TAX-, TRACK-, SUBSYS-; rename CES- → CESVC-; split SRC-; CLM- owner → 25. |
| 16 confidence | Matches the repo scale. The repo adds "≥0.95 for IRS" as well as exhibits; add an `irs_submission: 0.95` threshold. |
| 17 LitigationForce source | `case_tracks` carry no status (C2); `rico_analysis` (C3); `filing_drafting` needs an attorney gate. |
| 18 financial-audit-tax | Good scope and disclaimer. Link to `MAT-IRS`; raw target → Drive master tax subfolders, not `raw_docs/`. |
| 19 evaluator swarm | Matches the repo. Force human escalation for LEGAL_CONCLUSION (REVIEW.md). |
| 20 privilege + intake | Strong. Add C7. Checkpoint "approvers" are roles; map them to the licensed attorney for each matter. |
| 22 dashboard spec | Keep as spec (its own non-goals). The litigation module must show matter status first; predicate acts only under PARKED. |
| 23 dependency map | Complete for projects; no matters. Add rows once §7 lands. |
| 24 packaging checklist | Add 13, 25, 26 and the matter registry. "Human sign-off before active" is right. |
| 25 claim taxonomy | Apply C3. Add `status` per claim and `matter_id: MAT-TSL`; `matter_scope` mixes a matter key and a project ID. |
| 26 track registry | Apply C2 and C3. The defendant lists belong in the personnel registry by ID (DEF-/CC-), not free-text names. |
| README | Folder map omits 25, 26; add a "settled facts win" rule pointing to the facts register. |
| Template cards | Same as `docs/templates/`; apply `REVIEW.md` (null not 0.0 scores, `evidence_label`, `drive_file_id`, last-4 only). |

## 5. Answers to 14-open-questions
Answered by settled facts or existing work:
| Question | Answer | Source |
|---|---|---|
| Master raw document archive | Drive master folder 121X1o4QU7r5YPs8uB58d878XAfqNGtSj for financial and tax records; LEGAL MATTERS 1Pv-i27zSgoAMYC1JvHaVkos98jpYqL53 for case content; 00_MASTER_INTAKE for new or unsorted files. No new master folder. | CLAUDE.md, `OPERATING_PLAN.md` §2 |
| Matter ID convention | `MAT-<KEY>` (MUL, WIN, LEE, TSL, IRS, EVC, CUS); document names `<KEY>_<YYYY-MM-DD>_<doctype>_<descriptor>` | `LEGAL_MATTERS_ONTOLOGY.md` §2, §5; `templates/matter.md` |
| Evidence ID | Raw evidence keyed by sha256 in the matter evidence index; proposed ID `EVD-<KEY>-#####`, confirmed with the §7 patch | `LEGAL_MATTERS_ONTOLOGY.md` §3 |
| OIC/NOL scenario owner | `PRJ-FIN-INCOMETAX-ROBERTBAILEY`, matter `MAT-IRS` | tax-case card, CLAUDE.md |
| Dashboard build vs spec | Spec until schemas are validated (22 non-goals; no new trackers) | 22, `OPERATING_PLAN.md` |
| Neo4j staging | Files first; no import before seed-batch QA. Hosting is the owner's choice (below). | 11 §Graph |
| Spelling (TECHSTACH, CONNECTD, ENTITES) | Normalize when renaming | `NAMING-CONVENTIONS.md` |
| Person/entity spelling variants | Resolve from primary documents (formation records, signed instruments), not by asking the owner | settled-facts process |
| Which files are privileged | A licensed attorney decides; recorded in the privilege log. Not an owner or agent call. | CLAUDE.md, 20 |
| What never leaves local storage | Secrets → 1Password; client PII and privileged material → Drive matter folders, never code repos | `AGENTS.md` §4 |
| Connector in front of LexVault / Neon / Blackbox | Interim: Claude Code or an API bridge; no native Perplexity access assumed (08) | 08, this review |

Owner's decisions, batched:
1. Control-plane Space name (`09-KNOWLEDGE-ONTOLOGY` vs `LITIGATIONFORCE-DATABASE`).
2. Neo4j hosting (local Docker / Aura / Supabase-linked).
3. Human review layer: Obsidian or Notion.
4. Primary CRM (Airtable / Attio / Notion).
5. Repo audit order after this repo.
6. Scope of Open Human, MARKETING X and PHONE UI; POWER MED placement; DISPUTE CHARGES domain; X SCRAPER purpose.
7. `SRC-` split (recommended: split, C6).
8. OneWish DevOps vs CURSOR CLOUD AGENTS: merge or relate.
9. `CEP-` vs `PER-` (recommended: keep `PER-` as a legacy namespace joined through the personnel registry).
10. Backup approver for `GATE-CANONICAL-DATASET-WRITE`.
11. Accept `CES-` → `CESVC-` and the matter registry in §7.

## 6. Missing files to request
| File | Status |
|---|---|
| 09-neo4j-schema.cypher | Received (reviewed above) |
| 10-obsidian-frontmatter-templates/ | Partly: 7 cards received. Missing the predicate-act and workflow cards that 24 lists. |
| 13-approval-gates.md | Missing. Referenced by 15, 18, 26; it defines every GATE-/APR- ID. |
| 17-claim-taxonomy | Resolved: it is `25-claim-taxonomy.yaml`; fix the references in 15 |
| 21-connected-energy-canonical-dataset-schema.yaml | Missing. The uploaded org-chart `schema.yaml` may be its source; confirm. |

## 7. Patch list
```yaml
# 01-project-registry.yaml: change
- project_id: PRJ-LF-CENERGY-TESLA
  title: "Tesla program: potential claims (not filed)"
  status: active                     # work status; legal status lives on MAT-TSL
  description: "Tesla/Vikta/Solytx potential claims; forums assigned by contract; nothing filed; no funding; RICO PARKED."
  matter_ids: [MAT-TSL]
  tags: ["tesla", "potential-claims", "not-filed", "rico-parked"]
- project_id: PRJ-FIN-INCOMETAX-ROBERTBAILEY
  status: active
  matter_ids: [MAT-IRS]

# 01-project-registry.yaml: add (or new matter registry owned by LEGAL_MATTERS_ONTOLOGY.md)
status_vocabulary: [FILED-ACTIVE, POST-JUDGMENT, ON-APPEAL, ADMINISTRATIVE-ACTIVE, CLOSED, POTENTIAL-NOT-FILED, PARKED]
matters:
  - {matter_id: MAT-MUL, title: "Mullins v. Connected Solar", cause_number: "2024-CI-17193", status: POST-JUDGMENT, note: "order compelling production", project_id: PRJ-LF-ONTOLOGY}
  - {matter_id: MAT-WIN, title: "Winchell", status: FILED-ACTIVE, posture: "won on appeal; new developments expected", project_id: PRJ-LF-ONTOLOGY}
  - {matter_id: MAT-LEE, title: "Lee v. Connected Solar & Bailey", cause_number: "23-DCV-301569", status: FILED-ACTIVE, project_id: PRJ-LF-ONTOLOGY}
  - {matter_id: MAT-TSL, title: "Tesla program", status: POTENTIAL-NOT-FILED, project_id: PRJ-LF-CENERGY-TESLA}
  - {matter_id: MAT-IRS, title: "IRS collection / OIC", status: ADMINISTRATIVE-ACTIVE, project_id: PRJ-FIN-INCOMETAX-ROBERTBAILEY}
  - {matter_id: MAT-EVC, title: "Evictions and other", status: per_matter}
  - {matter_id: MAT-CUS, title: "Customer disputes", status: per_matter}
# every matter: drive_folder under LEGAL MATTERS (1Pv-i27zSgoAMYC1JvHaVkos98jpYqL53)

# 03-source-system-registry.yaml: add
- {source_id: drive_master_financial, display_name: "Drive master folder", folder_id: 121X1o4QU7r5YPs8uB58d878XAfqNGtSj, category: file_storage, role: durable_primary, sensitivity: financial_sensitive}
- {source_id: drive_legal_matters, display_name: "Drive LEGAL MATTERS", folder_id: 1Pv-i27zSgoAMYC1JvHaVkos98jpYqL53, category: file_storage, role: legal_root, sensitivity: privileged}
- {source_id: drive_master_intake, display_name: "00_MASTER_INTAKE", folder_id: 1gSKjscg0lJGdOVuhPbCXrRC-EUQiJQhd, category: file_storage, role: intake_only}
- {source_id: claude_code, display_name: "Claude Code", category: agent_surface, platform_route: claude_code, primary_uses: [repo_work, drive_search_and_filing, skills, productions_prep], status: connected}
- {source_id: gmail, category: communication, platform_route: claude_code_or_desktop, status: connected}
- {source_id: linear, category: work_tracking, notes: "workspace powerconnection; replaces linear_alt"}
- {source_id: onepassword, category: secrets, notes: "secrets only; never intake"}
- {source_id: irs_online_account, category: government_portal, notes: "owner login"}
# litigationforce_ai.primary_uses: rico_analysis -> claims_analysis

# 04-agent-registry.yaml: add
- agent_id: AGT-CLAUDE-CODE
  name: Claude Code
  role: "Repo, Drive and skill executor"
  skills: [discovery-production, bank-statement-audit, financial-statements-prep, tax-review-gap-analysis, legal-matter-summary, manifest-audit, file-system-steward]
  outputs_to: drive_master_financial
  quality_gate: "Reads facts register first; dry-run by default; human checkpoint for send, file, delete, merge."

# 08-connector-routing-matrix.md: add rows
# | GitHub repos, PRs, repo docs           | Claude Code | AGENTS.md workflow |
# | Drive search, filing into master folder| Claude Code | file-system-steward skill |
# | Productions, Bates, tax gap, bank audit| Claude Code | repo skills |

# 15-id-prefix-registry.yaml: add / change
- {prefix: "MAT-<KEY>", meaning: "Legal matter", owner: "LEGAL_MATTERS_ONTOLOGY.md", example: MAT-MUL}
- {prefix: "EVD-<KEY>-#####", meaning: "Evidence item (sha256 in index)", owner: "matter evidence index", example: EVD-MUL-00001}
- {prefix: "FIN-TAX-", meaning: "Tax/IRS case card", owner: "financial-audit-tax-case template", example: FIN-TAX-001}
- {prefix: "TRACK-", meaning: "Forum track", owner: "26-litigation-track-registry.yaml"}
- {prefix: "SUBSYS-", meaning: "Subsystem", owner: "18"}
- {prefix: "CESVC-", meaning: "Connected Energy service line", replaces: "CES-"}
- {prefix: "SRC-CEE-#####", meaning: "Canonical-dataset source", replaces: "SRC- (dataset)"}
- {prefix: "SRC-DOC-#####", meaning: "Raw-doc metadata source"}
- {prefix: "CLM-", owner: "25-claim-taxonomy.yaml"}
- {prefix: "PA-", status: PARKED}
- {prefix: "RICO-", status: PARKED}

# 25-claim-taxonomy.yaml: change
matter_scope: [MAT-TSL]
claims:
  - {claim_id: CLM-RICO, status: PARKED}
  # every other claim: status: POTENTIAL-NOT-FILED
rules:
  - "Every claim must stand on its own without RICO. RICO is PARKED."

# 26-litigation-track-registry.yaml: change (each track)
matter_id: MAT-TSL
tracks:
  - track_id: TRACK-A-JAMS-CALIFORNIA
    status: POTENTIAL-NOT-FILED
    forum_basis: contract
    filed: false
    related_claims: [CLM-BC, CLM-TS, CLM-TI-T]
    parked_claims: [CLM-RICO]
  # TRACK-B: same status fields; TRACK-C: same, parked_claims: [CLM-RICO]; defendants by DEF-/CC- ID

# 06-document-taxonomy.yaml: add
legal_types: [production_set, bates_log, privilege_log, court_order_compelling]
financial_audit_tax_types: [irs_transcript, collection_information_statement, federal_tax_lien, levy_notice]
required_metadata_add: [matter_id, document_date, evidence_label, production_scope, drive_file_id]

# 20-privilege-and-intake-rules.md: add
production_scope: [RESPONSIVE, OUT-OF-SCOPE_with_written_reason, ATTORNEY-REVIEW_to_privilege_log]
rule: "Privilege-by-default governs indexing and export. It does not narrow production: everything responsive is produced."

# 09-neo4j-schema.cypher: add
# CREATE INDEX matter_status_idx IF NOT EXISTS FOR (n:Matter) ON (n.status);
# CREATE INDEX claim_status_idx  IF NOT EXISTS FOR (n:Claim)  ON (n.status);
# Track.status required; CONSPIRED_WITH / DIVERTED_FROM / CIRCUMVENTED carry assertion_type + evidence_label
```
