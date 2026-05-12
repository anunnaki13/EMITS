---
phase: 01-production-audit-onboarding
plan: 02
subsystem: audit/data
tags: [audit, mongodb, inventory, naming-debt, projection-contract]
requires: []
provides:
  - pltu-tenayan-full-backup/docs/audit/DATA_AUDIT.md
  - pltu-tenayan-full-backup/docs/audit/.work/mongo-collections.txt
  - pltu-tenayan-full-backup/docs/audit/.work/mongo-counts.json
  - pltu-tenayan-full-backup/docs/audit/.work/mongo-samples.json
affects: []
tech-stack:
  added: []
  patterns: [mongosh-read-only-probe, count-vs-documented-reconciliation]
key-files:
  created:
    - pltu-tenayan-full-backup/docs/audit/DATA_AUDIT.md
    - pltu-tenayan-full-backup/docs/audit/.work/mongo-collections.txt
    - pltu-tenayan-full-backup/docs/audit/.work/mongo-counts.json
    - pltu-tenayan-full-backup/docs/audit/.work/mongo-samples.json
  modified: []
decisions:
  - "Naming-debt pairs are easier than expected: every legacy/SPEC-paired side is absent from live db, so Phase 5 starts from rename-or-no-op, not merge."
  - "users drift (+1) flagged for Phase 2 login investigation context."
metrics:
  duration_minutes: 8
  completed_date: 2026-05-10
requirements:
  - AUDIT-02
---

# Phase 01 Plan 02: Data Audit Summary

Live-counted every collection in MongoDB `pltu_tenayan` and reconciled against documented numbers, naming-debt pairs, and the {"_id": 0} + UUID `id` projection contract — Phase 3/4/5 now have ground truth without re-probing.

## What Was Built

`pltu-tenayan-full-backup/docs/audit/DATA_AUDIT.md` (213 lines): live MongoDB inventory with row counts, documented-vs-actual deltas, status flags (matches / drift / undocumented / missing / empty), naming-debt pair mapping (one subsection per pair), projection-contract spot-check (per-collection `id` and `_id` presence), per-collection schema diff against CONS-*-schema, and an anomalies/next-phase notes section feeding directly into Phase 3 (docs refresh) and Phase 5 (DEBT-01 migration).

Raw artifacts in `docs/audit/.work/`:
- `mongo-collections.txt` — 13 collections, sorted, one per line.
- `mongo-counts.json` — countDocuments per collection.
- `mongo-samples.json` — top-level field-key set per collection (no document payloads persisted).

## Live Inventory Headline

- Live collection count: **13**.
- Total documents across all collections: **2 300**.
- Documented count cross-check: **9/10 match exactly** (vessels=111, trucking=461, coa_reconciliation=721, biomassa=45, smartstock=207, po_batubara=301, merit_order=58, sumberpemakaian=208, ai_chat_history=10).
- Single drift: **users**, documented 7, live 8 (+1).

## Drift Collections

| Collection | Live | Documented | Delta | Notes |
|------------|-----:|-----------:|------:|-------|
| users      | 8    | 7          | +1    | One extra account vs PROJECT.md snapshot — Phase 2 login investigation context |

## Undocumented (live but not in CONS-collection-inventory or PROJECT.md "Live data inventory")

| Collection    | Live | Notes |
|---------------|-----:|-------|
| barges        | 168  | Has CONS-barges-schema entry but missing from PROJECT.md inventory table |
| user_settings | 1    | Has no CONS-*-schema entry; only documented at endpoint layer (CONS-ai-query-endpoint settings spec) |

## Missing (in CONS-collection-inventory but absent from live db)

- `smart_stock` — paired legacy of smartstock.
- `sumber_pemakaian` — paired legacy of sumberpemakaian.
- `settings` — paired with app_settings.
- `ai_conversations` — SPEC-preferred forward name; legacy `ai_chat_history` is the side with data.

## Naming-debt pair signals (no decision — Phase 5 owns DEBT-01)

| Pair                  | Active-name live | Paired-name live | Side with data    |
|-----------------------|-----------------:|-----------------:|-------------------|
| smartstock-pair       | 207 (smartstock) | absent (smart_stock) | smartstock |
| sumberpemakaian-pair  | 208 (sumberpemakaian) | absent (sumber_pemakaian) | sumberpemakaian |
| settings-pair         | 1 (app_settings) | absent (settings) | app_settings |
| ai-history-pair       | 10 (ai_chat_history) | absent (ai_conversations) | ai_chat_history |

Key takeaway: **every duplicate pair has only one side populated**. Phase 5 is collection rename + (for ai-history-pair only) document-shape migration — no merge logic needed for any pair.

## Projection-contract anomalies (CONS-projection-id-contract)

Two collections have NO application-level UUID `id` field:

| Collection    | Identifier used | Notes |
|---------------|-----------------|-------|
| app_settings  | `type` (e.g. `coa`) | Consistent with CONS-app-settings-schema (recommended unique on `type`); SPEC contract is satisfied via discriminator, not UUID |
| user_settings | `user_id` (FK to users.id) | 1:1 with users; FK is the identifier |

These are legitimate exceptions to the universal-`id` reading of CONS-projection-id-contract; Phase 3 should explicitly note them in DATABASE_SCHEMA.md.

`users` documents carry `password` (bcrypt hash) at top level — expected per CONS-users-schema, MUST be projected out by API handlers (the {"_id": 0} projection alone does not strip it). Confirming the auth/user response shape is owned by ENDPOINT_AUDIT (Phase 1 plan 01-01), not this plan.

## Schema doc gaps surfaced (Phase 3 input)

- `biomassa` — sample missing 3 documented core fields (`coal_from`, `ash_arb`, `ts_arb`) and carries 25 undocumented extras (significant drift).
- `trucking` — `rit`, `transportasi` not in CONS-trucking-schema.
- `po_batubara` — `stock_code`, `warehouse` documented at endpoint layer but not at schema layer.
- `smartstock` and `sumberpemakaian` — `updated_at` missing from schema.
- `coa_reconciliation` — `loading_no_coa`, `loading_surveyor`, `unloading_surveyor`, `unloading_fouling`, `unloading_slagging` missing from schema.
- `ai_chat_history` does not match CONS-ai-conversations-schema at all (different shape; this is a Phase 5 migration concern, not a Phase 3 doc fix).

## Deviations from Plan

None — plan executed exactly as written. All Task 1 and Task 2 acceptance criteria passed on first run.

## Self-Check: PASSED

- Created files exist:
  - `pltu-tenayan-full-backup/docs/audit/DATA_AUDIT.md` (213 lines) — present
  - `pltu-tenayan-full-backup/docs/audit/.work/mongo-collections.txt` — present
  - `pltu-tenayan-full-backup/docs/audit/.work/mongo-counts.json` — present
  - `pltu-tenayan-full-backup/docs/audit/.work/mongo-samples.json` — present
- Commits exist (inner repo `pltu-tenayan-full-backup`):
  - `1eb2960` chore(01-02): capture live MongoDB inventory, counts, and sample field-keys
  - `1ffd75f` docs(01-02): write DATA_AUDIT.md from live MongoDB inventory
- Automated verify (Task 2): inventory rowcount=44 (≥8 required), all four pair subsections present, projection spot-check section present, no credential / connection-string / password leak.
- Documented-count cross-check: every expected (vessels=111, trucking=461, coa_reconciliation=721, biomassa=45, smartstock=207, po_batubara=301, merit_order=58, sumberpemakaian=208, ai_chat_history=10, users=7) matches a row in the inventory table.
- No canonical-winner pick in DATA_AUDIT.md (Phase 5 boundary respected).
- No write operations issued against the live MongoDB.
