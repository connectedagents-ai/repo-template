# Review of the record-card templates (2026-10-22)

Templates reviewed: agent, canonical-entity, document, evaluator-gate-result, financial-audit-tax-case, project,
source-system, matter. The structure works: YAML front matter, stable IDs, privilege status and approval gates.
The changes below are recommendations; the templates themselves are unchanged until the owner accepts them.

## Cross-cutting
1. **One status vocabulary per card type.** Defaults today include `draft`, `raw_captured`, `pending` and `unknown`,
   with no defined list behind them. Publish the allowed values for each card type (see LEGAL_MATTERS_ONTOLOGY §1 for matters).
2. **Unscored is not zero.** `confidence_score: 0.0` and `score: 0.0` read as "scored and failed". Default to `null`.
3. **AI provenance field on every card:** `generated_by: human|agent:<AGT-id>|ai-tool:<name>` and
   `evidence_label: VERIFIED|STATEMENT|OWNER-STATED|DISPUTED|AI-GENERATED`. Without it, AI-written analysis gets
   mistaken for source. That has already happened once (an AI workpaper was read as a tax fact).
4. **Durable location:** `drive_file_id` / `drive_folder` on every card. Cards stored only in a container or chat get lost.
5. **Sensitive identifiers:** last-4 fields only (`account_last4`, `ein_last4`). There is no field for full numbers, SSNs or DOBs.
6. **ID registry:** PRJ-, MAT-, DOC-, CEE- (entity), CEP- (person, from the org-chart system), AGT-, FIN-TAX-, GATE-.
   Keep the prefixes in one list so new card types don't collide.
7. **Supersession:** `supersedes` / `superseded_by` / `duplicate_of` on documents, entities and projects, so old
   versions are archived, not deleted, and never cited.

## Per template
- **document:** `captured_at` is when the file was collected, not the date of the document. Add `document_date`, and
  `period_start` / `period_end` for statements, plus `tax_year`, `account_last4`, `bates_range`, `production_scope`
  (RESPONSIVE / OUT-OF-SCOPE + reason / ATTORNEY-REVIEW) and `evidence_label`. `sha256` is good; keep it required for
  raw evidence.
- **canonical-entity:** add `jurisdiction`, `formation_date`, `ein_last4`, `dbas`, `effective_start` / `effective_end`
  and `operating_status` (active / inactive since 2024). Define `reliability_tier` values or drop it in favor of
  confidence_score.
- **evaluator-gate-result:** a LEGAL_CONCLUSION needs three gates (citation, logic, ethics), so add `gate_set_id`
  linking the results for one claim and `gate_set_complete`. Force `human_escalation_required: true` for
  LEGAL_CONCLUSION and privilege calls. Add `evaluated_at`, `evidence_checked` and `max_remediation_loops`.
- **agent:** add `output_location` (master-folder subfolder), `state_location` (where its task state persists between
  sessions), `write_scope` (which folders it may change; default none), `handoff_to` and `model_route`. Default
  `approval_gates` to a human checkpoint for any write, send or delete.
- **financial-audit-tax-case:** `taxpayer_or_entity` should point to a CEE- or person ID, not free text. Add a
  per-year `filing_status` with evidence (accepted e-file / signed copy / transcript), `irs_notices`, `cpa`, and
  `deadlines` as dated items.
- **project:** add `owner`, `drive_folder`, `done_when`, `next_step` and `last_session_update`. These are the fields that
  carry work across sessions.
- **source-system:** add `coverage` (complete / partial, plus what is not reached), `last_synced_at`,
  `owner_login_required` and `bulk_download` (yes/no). These are the limits that caused the gaps in the harvest and the tax search.
