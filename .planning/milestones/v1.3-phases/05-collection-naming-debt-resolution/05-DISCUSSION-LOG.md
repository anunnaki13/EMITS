# Phase 05: Collection Naming Debt Resolution - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-11
**Phase:** 05-collection-naming-debt-resolution
**Areas discussed:** Canonical name choice, Migration sequencing, Backup + rollback procedure, Test gating + cutover

---

## Canonical name choice

| Option | Description | Selected |
|--------|-------------|----------|
| Pakai 'active' name | Canonical = smartstock, sumberpemakaian, app_settings, ai_chat_history (yang sudah produksi tulis). Migration = update AI module reads dari legacy → active, drop 4 empty legacy collections. Zero data movement. Stabilisasi-first. | ✓ |
| Snake_case Python-idiomatic | Canonical = smart_stock, sumber_pemakaian, settings, ai_conversations. Cost: rename 4 active collections (416 record total), update SEMUA CRUD endpoint, plus AI module reads. Lebih idealistic, lebih besar blast radius. | |
| Mixed (case-by-case) | Setiap pair dievaluasi sendiri. Per-pair evaluation collapses to the same outcome as option 1 in this codebase. | |

**User's choice:** Pakai 'active' name (Recommended)
**Notes:** Stabilization milestone — minimum disruption preferred. The "active" names already have 416 records in production; renaming would require non-trivial migration with no functional gain. `app_settings` is more specific than `settings`; `ai_chat_history` is more accurate than `ai_conversations`.

---

## Migration sequencing

| Option | Description | Selected |
|--------|-------------|----------|
| Update reads first, drop legacy after | Step 1: ubah AI/secondary reads dari legacy → active di server.py. Step 2: deploy + verifikasi (smoke test, monitor 1-2 hari). Step 3: drop 4 empty legacy collections via mongo shell + script. Aman karena code sudah tidak baca legacy. | ✓ |
| Defensive: count-check then drop pre-switch | Step 1: assert legacy.count_documents({}) == 0. Step 2: drop legacy. Step 3: switch reads. Risk: race-condition write ke legacy antara step 1-2, kita kehilangan data. | |
| Bidirectional copy fallback | Copy any rows from legacy → active sebelum drop (jaga-jaga audit miss). Karena audit sudah confirm 0 records, ini purely defensive overhead. | |

**User's choice:** Update reads first, drop legacy after (Recommended)
**Notes:** Read-path switch is non-destructive; observation window (≥48h) catches missed read paths before the irreversible drop step. Pre-drop count-check (D-07) provides safety even without bidirectional copy.

---

## Backup + rollback procedure (DEBT-04)

| Option | Description | Selected |
|--------|-------------|----------|
| mongodump full-DB + git revert | `mongodump --db pltu_tenayan` before migrate. Rollback: `mongorestore --drop` + `git revert <merge-commit>`. Documented step-by-step di MIGRATION_RUNBOOK.md. Storage cost ~tens-MB; mongo native tooling. | ✓ |
| Per-collection .bson snapshot | Dump 8 collection (4 pair). Lebih granular tapi lebih repotin operator saat incident. | |
| Dual-read code window (no data backup) | Tinggalkan kode legacy reads di-comment. Tidak ada data backup. Tidak memenuhi DEBT-04 literal ("backup verified"). | |

**User's choice:** mongodump full-DB + git revert (Recommended)
**Notes:** Native MongoDB tooling, well-understood; satisfies DEBT-04 literal "backup verified". Backup retention ≥30 days post-milestone (D-11).

---

## Test gating + production cutover

| Option | Description | Selected |
|--------|-------------|----------|
| Snapshot → dry-run → verify → prod cutover | (1) mongodump pltu_tenayan → restore to pltu_tenayan_migration_dryrun. (2) Run migration script + assert row-count + checksum parity (DEBT-02). (3) pytest -q exit 0 against dryrun DB. (4) Backup taken (Area 3). (5) Apply ke prod via same script. (6) Smoke test live endpoints. Soft maintenance window ~5 menit. | ✓ |
| Test factories only + prod cutover | Skip production-snapshot, pakai test DB factories untuk validation. Cepat tapi tidak memenuhi DEBT-02 literal ("copy of production data"). | |
| No formal test — prod cutover dengan backup | Trust the script + backup safety net. Cepat tapi melewatkan DEBT-02 dry-run gate. | |

**User's choice:** Snapshot → dry-run → verify → prod cutover (Recommended)
**Notes:** DEBT-02 literal ("dry-run on a copy of production data with zero data-loss diff") requires production-shaped data. Factory data wouldn't satisfy the SC. Cutover is a ~5-minute uvicorn restart; non-disruptive for the single-operator workflow.

---

## Claude's Discretion

- Exact ADR slug naming (`ADR-009-canonical-smartstock.md` vs `ADR-009-collection-smartstock.md`).
- Migration script CLI flag design (`--dry-run`, `--apply`, `--verify`, `--target-db`).
- MIGRATION_RUNBOOK.md placement (inner repo vs outer `.planning/runbooks/`).
- Plan decomposition: 2–4 plans for Phase 5 — planner decides at planning time.
- Whether Phase 5 owns the literal production cutover or hands the runbook to the operator after dry-run verification — planner addresses via AskUserQuestion at planning time.

## Deferred Ideas

- Snake_case refactor of all collection names — future polish phase (Phase 8 or post-milestone).
- Index rationalization / schema validation on canonical collections — future polish.
- Performance optimization on AI module post-migration — Phase 6 (Operational Unblocks) if observed.
