---
phase: 05
slug: collection-naming-debt-resolution
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-11
---

# Phase 05 — Validation Strategy

> Derived from 05-RESEARCH.md §"Validation Architecture (Nyquist Dimension 8)". Maps each DEBT-NN to a verifiable surface — every task in Phase 5 plans must align to one of the validation rows below.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 (already installed; Phase-4 baseline) + bash + mongosh |
| **Config file** | `pltu-tenayan-full-backup/backend/pytest.ini` (Phase-4 deliverable) |
| **Quick run command** | `cd pltu-tenayan-full-backup/backend && .venv/bin/pytest tests/ -q -m "not destructive"` |
| **Full suite command** | `cd pltu-tenayan-full-backup/backend && RUN_DESTRUCTIVE_TESTS=1 .venv/bin/pytest tests/ -q` |
| **Migration script** | `pltu-tenayan-full-backup/scripts/migrate_collection_names.py` (Phase-5 Plan 05-02 deliverable; CLI: `--dry-run` / `--apply` / `--verify` / `--target-db`) |
| **Estimated runtime** | quick: ~30 s · full: ~60 s · migration script verify on dryrun DB: <30 s |

---

## Sampling Rate

- **After every task commit:** Run the quick command (skip-destructive). For Plan 05-02 (server.py edits), additionally run `pytest tests/ -q` end-to-end to confirm regression bar holds.
- **Before production cutover:** `migrate_collection_names.py --verify --target-db pltu_tenayan_migration_dryrun` must exit 0 with zero diff.
- **Before legacy-drop (post-cutover ≥48h observation window):** `migrate_collection_names.py --verify --target-db pltu_tenayan` must exit 0 AND `db[legacy].count_documents({}) == 0` for all 4 legacy collections.
- **Max feedback latency:** 90 s.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | DEBT-01 | — | ADR-009..012 exist with `Accepted (locked, YYYY-MM-DD)` Status field; each cites the Phase-3 audit table row + server.py line evidence | static | `for n in 009 010 011 012; do test -f .planning/decisions/ADR-$n-*.md && grep -q "Accepted (locked" .planning/decisions/ADR-$n-*.md; done` | ❌ W0 | ⬜ pending |
| 05-02-01 | 02 | 2 | DEBT-03 | T-legacy-read-leak-01 | All 10 legacy-name reads in server.py replaced with canonical (lines 2379, 2387, 2395, 2398, 2427, 2863, 2868, 2877, 2926, 4346). Line 2377 string literal NOT touched. | static | `grep -cE "db\.(smart_stock|sumber_pemakaian)" pltu-tenayan-full-backup/backend/server.py` = 0 AND `grep -cE "db\.settings\.find_one\(\{.type.: .coa.\}\)" pltu-tenayan-full-backup/backend/server.py` = 0 | ❌ W0 | ⬜ pending |
| 05-02-02 | 02 | 2 | DEBT-02 (script) | T-data-loss-during-migration-01 | `migrate_collection_names.py` provides `--dry-run`, `--apply`, `--verify`, `--target-db` flags; idempotent (running twice = zero diff); pre-drop count guard asserts `legacy.count_documents({}) == 0` before `drop()` | integration | `python scripts/migrate_collection_names.py --dry-run --target-db pltu_tenayan` exits 0 with documented stdout shape | ❌ W0 | ⬜ pending |
| 05-02-03 | 02 | 2 | TEST-01 regression | — | `pytest backend/tests -q` exits 0 against canonical-only codebase (Phase-4 SC-1 must not regress) | integration | `cd pltu-tenayan-full-backup/backend && .venv/bin/pytest tests/ -q; echo $?` = 0 | ✅ | ⬜ pending |
| 05-03-01 | 03 | 2 | DEBT-02 (dry-run procedure) | — | MIGRATION_RUNBOOK.md documents `mongodump pltu_tenayan` → `mongorestore --nsFrom 'pltu_tenayan.*' --nsTo 'pltu_tenayan_migration_dryrun.*'` → `migrate_collection_names.py --verify --target-db pltu_tenayan_migration_dryrun` → `mongosh pltu_tenayan_migration_dryrun --eval "db.dropDatabase()"` | static | `grep -c "pltu_tenayan_migration_dryrun" pltu-tenayan-full-backup/MIGRATION_RUNBOOK.md` ≥ 3 | ❌ W0 | ⬜ pending |
| 05-03-02 | 03 | 2 | DEBT-04 (rollback) | T-rollback-failure-01 / mitigated | MIGRATION_RUNBOOK.md `## Rollback` section documents `mongorestore --drop --uri ... <backup-dir>` + `git revert <merge-commit>` procedures separately; backup retention ≥30 days documented | static | `grep -c "## Rollback" pltu-tenayan-full-backup/MIGRATION_RUNBOOK.md` ≥ 1 AND `grep -c "mongorestore" pltu-tenayan-full-backup/MIGRATION_RUNBOOK.md` ≥ 1 AND `grep -c "git revert" pltu-tenayan-full-backup/MIGRATION_RUNBOOK.md` ≥ 1 | ❌ W0 | ⬜ pending |
| 05-04-01 | 04 | 3 | DEBT-04 (backup taken) | T-data-loss-during-migration-01 / mitigated | `/home/damnation/backups/pre-phase5-YYYYMMDD-HHMMSS/pltu_tenayan/` exists with `.bson` files for the 13 active collections; `bsondump` smoke passes (no corruption) | manual | (see Manual-Only Verifications) | ❌ W0 | ⬜ pending |
| 05-04-02 | 04 | 3 | DEBT-04 (prod cutover) | T-legacy-read-leak-01 / mitigated | Code deploy (read-switch) applied to VPS via LOCAL_SETUP.md §VPS Service Recovery procedure; uvicorn restarted; `/api/health` returns 200 post-restart | manual | (see Manual-Only Verifications) | ❌ W0 | ⬜ pending |
| 05-04-03 | 04 | 3 | DEBT-04 + DEBT-02 (legacy-drop after observation) | T-premature-drop-01 / mitigated | After ≥48h observation window: `migrate_collection_names.py --apply --target-db pltu_tenayan` drops 4 empty legacy collections (drop-if-exists; count guard asserts each is empty); `db.getCollectionNames()` post-drop shows zero of: smart_stock, sumber_pemakaian, settings (legacy), ai_conversations | manual | (see Manual-Only Verifications) | ❌ W0 | ⬜ pending |
| 05-04-04 | 04 | 3 | DEBT-05 | — | DATABASE_SCHEMA.md "Duplicate-pair active-target audit" section removed or archived with "Resolved YYYY-MM-DD by Phase 5" annotation; `grep -c "legacy" DATABASE_SCHEMA.md` ≤ 1 (or 0 — planner decides) | static | `grep -c "legacy" pltu-tenayan-full-backup/DATABASE_SCHEMA.md` ≤ 1 | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Wave 0 = the prerequisite scaffolding before Wave-2 (server.py edits + script) can land. Plan 05-01 (ADRs) is wave 1 = pure planning artifact, doesn't block code work but provides the citation source for Plan 05-02 commit messages.

- [ ] `.planning/decisions/ADR-009-canonical-smartstock.md`
- [ ] `.planning/decisions/ADR-010-canonical-sumberpemakaian.md`
- [ ] `.planning/decisions/ADR-011-canonical-app-settings.md`
- [ ] `.planning/decisions/ADR-012-canonical-ai-chat-history.md`
- [ ] `pltu-tenayan-full-backup/scripts/migrate_collection_names.py` — 4 CLI flags, idempotent, pre-drop count guard
- [ ] `pltu-tenayan-full-backup/MIGRATION_RUNBOOK.md` — Backup / Dry-run / Cutover / Observation / Drop-legacy / Rollback / Cleanup sections

*Existing infrastructure that Wave 0 builds on (do NOT replace):*
- Phase-4 conftest + pytest infra (regression bar)
- Phase-3 audit (`DATABASE_SCHEMA.md` lines 697-735) — source-of-truth for the duplicate-pair table
- `LOCAL_SETUP.md` §"VPS Service Recovery" — cross-link target

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Production mongodump backup taken | DEBT-04 (backup verified) | Filesystem state outside test scope; operator action | Operator runs `mongodump --uri mongodb://localhost:27017 --db pltu_tenayan --out /home/damnation/backups/pre-phase5-$(date +%Y%m%d-%H%M%S)/` per MIGRATION_RUNBOOK.md §Backup; verifies output dir has 13 .bson files + .metadata.json files; runs `bsondump <file>.bson | head` smoke for each |
| Production cutover (read-switch deploy) | DEBT-04 (applied to production) | Operator action; requires VPS access | Operator pulls latest from inner-repo on VPS, runs LOCAL_SETUP.md §VPS Service Recovery uvicorn restart, confirms `/api/health` 200, runs smoke curls on AI module endpoints (`/api/ai/quick/smart-stock`, `/api/ai/quick/coa-alerts`) and verifies responses now contain real data (non-empty arrays) |
| Observation window ≥48 hours before legacy-drop | DEBT-04 (no premature drop) | Time-based; can't be automated within a pytest run | Operator notes the cutover timestamp in MIGRATION_RUNBOOK.md, waits ≥48h, runs smoke curls again to confirm no regression, then proceeds to drop step |
| Production legacy-drop step | DEBT-04 + DEBT-02 (apply) | Operator action with pre-drop count guard from the script | Operator runs `python scripts/migrate_collection_names.py --apply --target-db pltu_tenayan`; script asserts each legacy collection has 0 records and drops; operator confirms `mongosh pltu_tenayan --eval "db.getCollectionNames()"` no longer lists `smart_stock`, `sumber_pemakaian`, `settings` (legacy), `ai_conversations` |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Manual-Only entry
- [ ] Sampling continuity: every Plan 05-02 task has an automated grep/pytest gate
- [ ] Wave 0 covers all MISSING references (6 deliverables)
- [ ] No watch-mode flags (every command above is one-shot)
- [ ] Feedback latency < 90 s for automated paths
- [ ] Manual-only paths (DEBT-04 production cutover, observation window) are explicitly flagged so the verifier doesn't expect automation
- [ ] `nyquist_compliant: true` set in frontmatter (flip after planner produces PLAN.md files that satisfy §Per-Task Verification Map)

**Approval:** pending
