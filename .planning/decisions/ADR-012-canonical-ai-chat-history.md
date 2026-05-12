# ADR-012: ai_chat_history as Canonical AI-Chat-History Collection Name

## Status

Accepted (locked, 2026-05-11) — promoted from Phase-3 duplicate-pair audit; canonical name selected per D-04 in 05-CONTEXT.md.

## Context

EMITS maintains an `ai_chat_history` collection holding AI session and message records for the PLTU Tenayan AI Intelligence Agent. At the time Phase 5 is planned, the live `pltu_tenayan` database contains **10 records** in `ai_chat_history` and **0 records** in `ai_conversations` — confirmed by `db.getCollectionNames()` on 2026-05-11, which shows `ai_conversations` is **entirely absent** from the live database (not merely empty — it does not exist as a collection).

**Critical distinguishing finding:** Unlike the other three duplicate pairs in this phase, `ai_conversations` does not appear anywhere in `server.py`. A verified `grep -n "ai_conversations" server.py` executed on 2026-05-11 returns **ZERO results** (RESEARCH.md Focus 2 §"`ai_conversations` (ZERO occurrences)", line 218). The canonical assignment has been in place since the AI module was authored:

- `server.py:2266` — `ai_chat_collection = db.ai_chat_history` — module-level assignment; all AI session reads and writes go through this variable

All AI session history CRUD operations reference the `ai_chat_collection` variable (which is bound to `db.ai_chat_history`), so there are no direct `db.ai_conversations` references to find or fix. The code for this pair is already correct.

The Phase-3 audit (DATABASE_SCHEMA.md §"Duplicate Pair Active Read Targets", lines 695-735, audit table row at line 707) recorded `ai_chat_history` as the active collection and `ai_conversations` as the legacy, with code evidence at `server.py:2264` (the audit cited line 2264; RESEARCH.md verified the current line as 2266 after intervening edits).

The Phase-3 audit plan 03-05 did not anchor `ai_conversations` code reads (noting "planner MUST grep" in D-04 of 05-CONTEXT.md). RESEARCH.md Focus 2 closes that gap: the grep confirms zero `ai_conversations` references. This pair requires **no code edits in Plan 05-02** and a **no-op drop step in Plan 05-04** (the migration script's "SKIP — does not exist" idempotency branch handles the absent collection transparently).

DEBT-01 in `.planning/REQUIREMENTS.md` requires that a canonical-name decision be recorded in an ADR for each duplicate pair. This ADR satisfies that requirement for the `ai_chat_history` / `ai_conversations` pair and formally closes the open grep-verification gap from D-04.

## Decision

**`ai_chat_history`** is the canonical collection name. `ai_conversations` is rejected as the legacy duplicate.

The canonical assignment `ai_chat_collection = db.ai_chat_history` at `server.py:2266` is already in place — **no code edits are required for this pair** in Plan 05-02. The codebase is already correct.

Plan 05-04's `migrate_collection_names.py --apply` step will report `[SKIP] ai_conversations — does not exist` (per the migration script's idempotency pattern documented in RESEARCH.md Focus 5). This is the EXPECTED outcome — not an error. Operators reading the migration log must understand that "SKIP — does not exist" for `ai_conversations` is the correct output, not a failure.

DATABASE_SCHEMA.md §13.2 (the `ai_conversations` stub section, if present) is removed in Plan 05-04 as part of the DEBT-05 cleanup.

## Consequences

**Positive:**

- Closes DEBT-01 for this pair with **zero code risk** — no `server.py` edits, no read-path changes, no regression potential for the AI chat session features.
- DATABASE_SCHEMA.md cleanup in Plan 05-04 removes the `ai_conversations` stub and the "legacy" annotation for this pair, eliminating ambiguity for future contributors.
- The formal ADR provides a citation source for Plans 05-02, 05-03, and 05-04 (they can reference "ADR-012" instead of re-deriving the decision).
- The verified grep result (ZERO `ai_conversations` occurrences in `server.py`) is now documented and locked — future contributors will not re-investigate this pair.
- Post-Phase-5, `grep -c "ai_conversations" server.py` returns 0 (already true); `db.getCollectionNames()` shows `ai_conversations` absent (already true).

**Negative / accepted tradeoffs:**

- The migration script will emit a "SKIP — does not exist" log line for `ai_conversations` during Plan 05-04. Operators must understand this is expected, not an error. MIGRATION_RUNBOOK.md (Plan 05-03) must document this explicitly.
- No data-loss risk for this pair because there is nothing to drop and nothing to move.

## Alternatives Considered

**`ai_conversations` as canonical** — rejected. `ai_conversations` is absent from both `server.py` (ZERO grep occurrences) and the live `pltu_tenayan` database (confirmed by `db.getCollectionNames()`). There are 10 existing records in `ai_chat_history`; switching canonical to `ai_conversations` would require renaming or moving those 10 records and changing the module-level assignment at `server.py:2266`. This is a pointless refactor with no functional benefit. `ai_chat_history` is already the de-facto canonical name by virtue of being the only name in use.

**Bidirectional dual-read window** — rejected per D-08. The legacy `ai_conversations` collection is confirmed absent from the live DB entirely; a dual-read window would add complexity for zero safety benefit.

**Snake_case normalization** — deferred to Phase 8. Both candidate names (`ai_chat_history` and `ai_conversations`) already use underscores; no snake_case issue applies to this pair.

## References

- **Source decision:** `.planning/phases/05-collection-naming-debt-resolution/05-CONTEXT.md` §"Implementation Decisions" D-04 — "ai_chat_history is canonical (NOT ai_conversations). Active read assigned at server.py:2264. ai_conversations is legacy; 0 records; planner MUST grep for remaining ai_conversations reads."
- **Phase-3 audit:** `pltu-tenayan-full-backup/DATABASE_SCHEMA.md` §"Duplicate Pair Active Read Targets (Phase-3 audit, 2026-05-10)" lines 695-735 — audit table row at line 707: "ai_chat_history vs ai_conversations | ai_chat_history (canonical) | ai_conversations (legacy) | Active count: 10 | Legacy count: 0".
- **Code anchor — canonical assignment (already in place; DO NOT change):**
  - `pltu-tenayan-full-backup/backend/server.py:2266` — `ai_chat_collection = db.ai_chat_history` (module-level assignment; all AI session reads and writes go through this variable)
- **ZERO legacy reads verified:**
  - `pltu-tenayan-full-backup/backend/server.py` — `grep -n "ai_conversations" server.py` returns **ZERO results** [VERIFIED 2026-05-11]. `ai_conversations` is entirely absent from `server.py`. This is the key finding that makes Plan 05-02 a no-op for this pair.
  - RESEARCH.md Focus 2 §"`ai_conversations` (ZERO occurrences)" line 218: "The `ai_conversations` collection is completely absent from `server.py`."
- **DB-side absence verified:**
  - `mongosh pltu_tenayan --eval "db.getCollectionNames().join('\n')" --quiet` — `ai_conversations` does not appear in the live `pltu_tenayan` DB collection list [VERIFIED 2026-05-11]. See also RESEARCH.md §"Pitfall E: ai_conversations does not exist in live DB".
- **Migration no-op:** Plan 05-04 migration script will emit `[SKIP] ai_conversations — does not exist` — this is EXPECTED behaviour per the script's idempotency pattern (RESEARCH.md Focus 5). MIGRATION_RUNBOOK.md (Plan 05-03) must document this as the correct output.
- **Requirement:** `.planning/REQUIREMENTS.md` DEBT-01 — "Canonical-name decision recorded in an ADR for each duplicate pair."
- **Sibling ADRs:** `.planning/decisions/ADR-009-canonical-smartstock.md`, `.planning/decisions/ADR-010-canonical-sumberpemakaian.md`, `.planning/decisions/ADR-011-canonical-app-settings.md` — the four canonical-name ADRs land together as a set in Phase 5 Plan 05-01.
