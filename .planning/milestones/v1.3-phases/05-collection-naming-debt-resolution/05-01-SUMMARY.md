---
phase: 05
plan: 01
subsystem: planning/decisions
tags: [adr, collection-naming, phase-5, debt-01]
dependency_graph:
  requires: []
  provides:
    - .planning/decisions/ADR-009-canonical-smartstock.md
    - .planning/decisions/ADR-010-canonical-sumberpemakaian.md
    - .planning/decisions/ADR-011-canonical-app-settings.md
    - .planning/decisions/ADR-012-canonical-ai-chat-history.md
  affects:
    - .planning/phases/05-collection-naming-debt-resolution/05-02-PLAN.md (cites ADR-009..012 in commit messages)
    - .planning/phases/05-collection-naming-debt-resolution/05-03-PLAN.md (MIGRATION_RUNBOOK.md references these ADRs)
    - .planning/phases/05-collection-naming-debt-resolution/05-04-PLAN.md (DATABASE_SCHEMA.md cleanup references these ADRs)
tech_stack:
  added: []
  patterns:
    - MADR-format ADR (same structure as ADR-001..008; Status / Context / Decision / Consequences / Alternatives Considered / References)
key_files:
  created:
    - .planning/decisions/ADR-009-canonical-smartstock.md
    - .planning/decisions/ADR-010-canonical-sumberpemakaian.md
    - .planning/decisions/ADR-011-canonical-app-settings.md
    - .planning/decisions/ADR-012-canonical-ai-chat-history.md
  modified: []
decisions:
  - "ADR-009: smartstock canonical (207 records); 3 AI-module legacy reads (server.py:2379/2395/2863) fixed in Plan 05-02"
  - "ADR-010: sumberpemakaian canonical (208 records); 4 AI-module legacy reads (server.py:2387/2398/2868/2877) fixed in Plan 05-02"
  - "ADR-011: app_settings canonical (1 record); 3 export+AI legacy reads (server.py:2427/2926/4346) fixed in Plan 05-02; material behavioural fix (COA export + AI COA-alerts were using hardcoded price_per_kcal_per_ton=50)"
  - "ADR-012: ai_chat_history canonical (10 records); ai_conversations absent from server.py (ZERO grep hits) AND absent from live DB; no code edits required; Plan 05-04 drop is a no-op"
metrics:
  duration: 4min
  completed: 2026-05-11
  tasks_completed: 2
  files_created: 4
---

# Phase 05 Plan 01: Canonical Collection Name ADRs (ADR-009..012) Summary

Four locked MADR-format ADRs documenting the canonical-name decision for each of the four duplicate MongoDB collection pairs identified in the Phase-3 audit, covering 10 verified legacy-read line citations from server.py and closing the open `ai_conversations` grep-verification gap from D-04.

## Files Created

| File | ADR | Canonical | Legacy | Records | Code edits in 05-02 |
|------|-----|-----------|--------|---------|---------------------|
| `.planning/decisions/ADR-009-canonical-smartstock.md` | ADR-009 | smartstock | smart_stock | 207 | server.py:2379, 2395, 2863 |
| `.planning/decisions/ADR-010-canonical-sumberpemakaian.md` | ADR-010 | sumberpemakaian | sumber_pemakaian | 208 | server.py:2387, 2398, 2868, 2877 |
| `.planning/decisions/ADR-011-canonical-app-settings.md` | ADR-011 | app_settings | settings | 1 | server.py:2427, 2926, 4346 |
| `.planning/decisions/ADR-012-canonical-ai-chat-history.md` | ADR-012 | ai_chat_history | ai_conversations | 10 | NONE (zero legacy reads) |

## Verification Output

```
$ ls .planning/decisions/ADR-{009,010,011,012}-*.md
.planning/decisions/ADR-009-canonical-smartstock.md
.planning/decisions/ADR-010-canonical-sumberpemakaian.md
.planning/decisions/ADR-011-canonical-app-settings.md
.planning/decisions/ADR-012-canonical-ai-chat-history.md

ALL 4 ADRs valid
```

All 5 verification gates passed:
1. All 4 ADR files exist
2. Each has `Accepted (locked, 2026-05-11)` Status line
3. Each cites `DATABASE_SCHEMA.md` Phase-3 audit table
4. Each references `DEBT-01`
5. Each has >= 6 `## ` section headers (Status / Context / Decision / Consequences / Alternatives Considered / References)

## Key Clarifications vs CONTEXT.md Line Citations

CONTEXT.md (D-01..D-03) cited outdated line numbers derived from the Phase-3 audit. RESEARCH.md Focus 2 (verified 2026-05-11) corrects these discrepancies. The ADRs use the **verified** line numbers from RESEARCH.md, not the CONTEXT.md originals:

| CONTEXT.md cited | Actual (RESEARCH.md verified) | Discrepancy |
|-----------------|-------------------------------|-------------|
| 2377 (smart_stock) | 2379, 2395, 2863 | Line 2377 is a string literal `if module in ["general", "smart_stock"]` — NOT a collection read; explicitly excluded from Phase 5 edits |
| 2385 (sumber_pemakaian) | 2387, 2398, 2868, 2877 | 4 lines, not 1 |
| 2425 (settings) | 2427, 2926, 4346 | 3 lines including COA export; line 4346, not 4382 |
| 4382 (settings) | 4346 | 36-line offset from intervening edits since Phase-3 audit |

ADR-009 explicitly notes the line 2377 exclusion. ADR-011 explicitly notes the line 4346 correction (from CONTEXT.md's 4382).

## ai_conversations Gap Closed

CONTEXT.md D-04 required the planner to grep `server.py` for `ai_conversations` reads. RESEARCH.md Focus 2 confirmed: `grep -n "ai_conversations" server.py` returns **ZERO results** [VERIFIED 2026-05-11]. The legacy collection is also absent from the live `pltu_tenayan` DB. ADR-012 formally records this finding and documents that Plan 05-02 requires no code edits for this pair, and Plan 05-04's drop step will emit `[SKIP] ai_conversations — does not exist` (expected, not an error).

## Commits

| Task | Description | Commit |
|------|-------------|--------|
| 05-01-01 | ADR-009 (smartstock) + ADR-010 (sumberpemakaian) | a3e9e64 |
| 05-01-02 | ADR-011 (app_settings) + ADR-012 (ai_chat_history) | ebd1995 |

## Deviations from Plan

None — plan executed exactly as written. All 4 ADRs follow the MADR format from ADR-001..008, cite Phase-3 audit table rows and verified server.py line numbers, and reference REQUIREMENTS.md DEBT-01. The only adjustments were to use RESEARCH.md-verified line numbers (not CONTEXT.md's outdated citations), which was the intended behaviour per the plan's `<interfaces>` block.

## Next Plan

**05-02** depends on these ADRs being committed. Plan 05-02 will cite ADR-009 through ADR-012 by path in its commit messages for the server.py legacy-read edits (10 lines total: 2379, 2387, 2395, 2398, 2427, 2863, 2868, 2877, 2926, 4346) and the migration script authoring.

## Known Stubs

None — ADRs are documentation artifacts with no data-wiring concerns.

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or schema changes introduced. ADRs are read-only documentation artifacts.

## Self-Check: PASSED

- `.planning/decisions/ADR-009-canonical-smartstock.md` — FOUND
- `.planning/decisions/ADR-010-canonical-sumberpemakaian.md` — FOUND
- `.planning/decisions/ADR-011-canonical-app-settings.md` — FOUND
- `.planning/decisions/ADR-012-canonical-ai-chat-history.md` — FOUND
- Commits a3e9e64, ebd1995 — FOUND
