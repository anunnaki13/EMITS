## Conflict Detection Report

### BLOCKERS (0)

(none)

### WARNINGS (1)

[WARNING] Cross-reference cycle between PRD and developer documentation
  Found: pltu-tenayan-full-backup/memory/PRD.md cross-references pltu-tenayan-full-backup/documentation.md (and README.md), and pltu-tenayan-full-backup/documentation.md cross-references pltu-tenayan-full-backup/memory/PRD.md back. README.md → documentation.md → PRD.md → README.md also closes via README's reference chain.
  Impact: A literal cross_refs cycle was detected between PRD (precedence rank 3) and DOC (precedence rank 4). Because the docs sit at different precedence ranks, no actual content-derivation loop occurs during synthesis — DOC content cannot override PRD content. The cycle is a citation pattern, not a synthesis hazard. However, per the synthesizer contract every detected cycle must be surfaced for explicit user awareness so that downstream regeneration of cross_refs (e.g., by the roadmapper) does not introduce a true content loop.
  → Acknowledge the citation cycle and proceed, OR trim cross_refs in one direction (recommended: drop the back-reference from documentation.md → memory/PRD.md, since DOC should not assert PRD provenance).

### INFO (5)

[INFO] No ADR-class documents in ingest set
  Note: 0 of 10 ingested documents classified as ADR. Decisions in `intel/decisions.md` are derived from PRD/SPEC/DOC content as IMPLICIT-001 through IMPLICIT-008. Roadmapper should consider promoting these into formal ADRs so future precedence checks have authoritative anchors. No LOCKED-vs-LOCKED conflict possible because no ADR is locked.

[INFO] Auto-resolved: SPEC > DOC on API endpoint surface
  Note: pltu-tenayan-full-backup/API_REFERENCE.md (SPEC, precedence 2) and pltu-tenayan-full-backup/documentation.md (DOC, precedence 4) both enumerate API endpoints. Where the DOC's "Peta API Utama" (section 8) lists subsets of endpoints documented authoritatively in API_REFERENCE.md, the SPEC version was used in `intel/constraints.md`. The DOC version is preserved as orientation in `intel/context.md` but is non-authoritative. Same reasoning applies for data-model summaries in documentation.md section 7 vs DATABASE_SCHEMA.md (SPEC).

[INFO] Auto-resolved: SPEC > DOC on Smart Blending math
  Note: pltu-tenayan-full-backup/frontend/public/docs/Smart_Blending_AI_Formula.md (SPEC, precedence 2) defines the authoritative blending formula, parameter ranges, constraint inequalities, AI JSON output schema, and ±5% tolerance. pltu-tenayan-full-backup/documentation.md and readme.md describe Smart Blending narratively without contradicting the SPEC. SPEC content is canonicalized in `intel/constraints.md`; DOC narrative kept in `intel/context.md`.

[INFO] Pre-existing collection naming inconsistencies surfaced by SPEC author
  Note: pltu-tenayan-full-backup/DATABASE_SCHEMA.md (SPEC) explicitly flags `smartstock` vs `smart_stock`, `sumber_pemakaian` vs `sumberpemakaian`, `app_settings` vs `settings`, `ai_chat_history` vs `ai_conversations` as legacy/transitional names that need standardization. This is intra-SPEC technical debt, not a cross-doc conflict. Recorded in `intel/constraints.md` under CONS-collection-naming-debt; roadmapper should treat as backlog work.

[INFO] PRD ships test credentials inline
  Note: pltu-tenayan-full-backup/memory/PRD.md publishes test credentials inline (see `pltu-tenayan-full-backup/memory/test_credentials.md` for the literal values). Not a conflict, but worth noting: any downstream artifact derived from PRD that gets committed publicly carries these credentials. Roadmapper should consider sanitizing before any artifact lands in PROJECT.md.
