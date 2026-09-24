# Global Ontology: one governed model for names, tags, structure and meaning

**"Ontology" / "Global Ontology"** is the single name for everything that says what things *are*, what they're *called*,
how they're *labelled* and where they *live*, across every company, tool and storage location. Today that knowledge is
spread over dozens of competing files; this document is the process for turning them into one canonical, versioned spec
that people, agents and scripts all use.

## What the Global Ontology covers (one spec, six chapters)
| Chapter | Question it answers | Today's closest source |
|---|---|---|
| **Ontology** (entities + relationships) | What kinds of things exist (company, person, matter, project, document, agent, skill, account…) and how they relate | `ontology_v1.yaml` (Drive, "ONEWISHOS canonical ontology v1.0.0"), `master-ontology-taxonomy.md` (SharePoint DEVOPS) |
| **Taxonomy** (hierarchy) | Domains → sub-domains → collections, one tree per company | `POWER_CONNECTION_MASTER_TAXONOMY.md`, `Connected-Companies-Folder-Naming-Convention-and-Hierarchy.pdf`, `TAX_ONTOLOGY_AND_HIERARCHY.md` |
| **Topology** (where things live) | Which system is the home for each class (L0 identity → L5 apps; Mac, Drive, SharePoint, GitHub, Notion, Linear) | `docs/CLOUD-ARCHITECTURE.md` (layers L0–L5), `docs/ARCHITECTURE.md` |
| **Naming + syntax** | Allowed characters, casing, date format, ID format, per-object patterns | `docs/NAMING-CONVENTIONS.md`, SharePoint `ontology.md` (from the Notion "Master Guide: Naming Conventions") |
| **Tags + metadata schema** | Required fields and allowed values (`type`, `domain`, `entity`, `project`, `status`, `sensitivity`, `owner`, `source`) | `docs/NAMING-CONVENTIONS.md` §3, SharePoint `ONTOLOGY.md` (`#entity/person` tag style) |
| **Rules as code** | The regexes scripts use to classify, flag and validate | legal/sensitivity pattern (`ops/dedup/dedup_scan.py`), duplicate-name noise (`dedup_merge.py`), secret names (`ingest_library.py`, `find_plaintext_keys.py`), platform/tenant patterns (`discover_accounts.py`) |

Domain models (legal matters such as Mullins, tax, CRM, voice agents) are **namespaced extensions** of the global model
(`legal:`, `tax:`, `crm:`, `voice:`), not separate rival ontologies.

## What exists today (found 2026-09-24; not yet read in full)
- **SharePoint (OneWish Labs):** ~2,100 hits for "ontology". Candidates: `DEVOPS/Shared Documents/master-ontology-taxonomy.md` (Foundry-style,
  canonicalId issuance), `…/FEDERATED_ONTOLOGY.md` (self-marked `NONCANONICAL_LOCAL_PROPOSAL`), `OneWishLabs/DevopsFilesInbox/…/ONTOLOGY.md` (tag
  dictionary), `CentralFileCloud/…/docs/modules/ontology.md` (naming + schema, from Notion; 2 copies), `PowerConnection/Shared Documents/ontology_terms.json`
  and `METHOD_Fuzzy_Ontology_Matching.md`, `IncomeTax/…/TAX_ONTOLOGY_AND_HIERARCHY.md`. Mac-generated indexes `DEV-ONTOLOGY-INDEX.md` (4 copies across
  DEVOPS, CONNECTEDENERGYPARENT, Media library) point at run logs in `~/Developer/chairman-life-os/run-logs/dev-ontology/` on the Mac, and
  `DEV-ONTOLOGY-AGENTIC-SYSTEM.md` describes an "ontology orchestrator" agent. `zero-crm_schema_and_ontology…md` and
  `zero-talian_contact_ontology…md` also sit in a **bank-statements tax library** (misfiled).
- **Google Drive:** `ontology_v1.yaml` (the only versioned, machine-readable spec found, with validation rules), `ONTOLOGY_FOUNDATION.md`,
  `POWER_CONNECTION_MASTER_TAXONOMY.md`, `CONSTITUTION_ONTOLOGY_VOICE.md` (+`__dup`), `PRD_AGREEMENT_FORMS_ONTOLOGY_OS.md` (+`__dup`), `ontology.py`,
  7 × `generate_ontology_graph_*.json`, `cenergy-ontology-manifesto.pdf`, `brand-element-taxonomy.md`, `WHY USE NAMING CONVENTIONS 1.md`,
  Mullins `ontology_nodes/edges` sheets (×4, legal: privileged), folders `AsIs_Ontology` (×2), `04_Ontology_Matching`,
  `…talians_master_ontology_and_taxonomy_framework`.
- **Notion:** wikis "LEXVAULT-Ontology", "CRM Ontology / Schema / Syntax / Taxonomy", "Master Guide: Naming Conventions" (cited by the SharePoint copies).
- **Linear:** POW-136 (Microsoft Graph global ontology design), POW-161 (Master Ontology: cross-domain entity & relationship model),
  POW-239 (canonical folder structure, local + SharePoint), project P-POW-53 (Linear governance & structured output standard).
- **This repo:** `docs/NAMING-CONVENTIONS.md` and the regex rules listed in the table above.
- **Not checked:** Cursor workspaces and other GitHub orgs/repos (not reachable from here); the Mac run logs. `bash ops/start.sh` → 4 lists the Mac side.

## Process (each step produces a reviewable file; nothing is renamed or moved until step 6)
1. **Collect.** Export every candidate above (plus Notion wikis and the Mac run logs) into `agent-central-config/ontology/sources/` with
   `ingest_library.py --source ontology` (dedups copies and records where each came from). Privileged legal models (Mullins) stay in
   the litigation store and are referenced by name only.
2. **Compare.** One table: every source × the six chapters above: what each defines, where they agree, where they conflict.
   Recommended base: `ontology_v1.yaml` (versioned, machine-readable, has validation rules), with naming from `NAMING-CONVENTIONS.md`
   and topology from `CLOUD-ARCHITECTURE.md`. Decide each conflict once, and record the decision.
3. **Write the canonical spec:** `agent-central-config/ontology/global-ontology.yaml` (semantic version, owner, changelog) with sections
   `namespaces`, `entities`, `relationships`, `taxonomy`, `topology`, `naming` (patterns as regexes), `metadata` (fields + allowed values),
   `sensitivity`, `ids`. A generated `GLOBAL-ONTOLOGY.md` explains it for people. This repo's `NAMING-CONVENTIONS.md` becomes its naming chapter.
4. **Rules as code.** Scripts read their patterns from the YAML instead of hard-coding them (legal/sensitivity flags, duplicate-name noise,
   kind/type classification, secret names). A `lint_names.py` checks any inventory (dedup CSVs, Drive/SharePoint listings, GitHub repo list)
   against the naming and metadata rules and writes a violations report with proposed names.
5. **Agents.** `AGENTS.md` points every agent (Claude, Codex, Cursor, Copilot, Gemini, Grok, Devin, Warp) at the Global Ontology for names,
   tags and filing; the "ontology orchestrator" agent spec is rewritten against the canonical YAML.
6. **Apply.** Renames and re-tagging run from the lint report as a before→after manifest (dry run → approval → apply, with undo),
   repo renames via GitHub (redirects kept). Superseded ontology files move to `archive/` with a pointer to the canonical spec;
   duplicates (`__dup`, 4 × DEV-ONTOLOGY-INDEX, 7 × generate_ontology_graph, misfiled `zero-*` copies) go through the dedup.
Where the ontology gets used at scale (graph, vector search, OCR + extraction + renaming pipeline, voice agents), options and
costs are compared in `docs/research/2026-09-24_graph-vector-voice-ocr-research.md`.

7. **Govern.** Changes only by PR to `global-ontology.yaml` (owner approves), semver bump, changelog. Tracked in **one** Linear
   project ("Global Ontology"), into which POW-136, POW-161 and POW-239 are moved.
