# MIGRATION_RUNBOOK.md — Collection Naming Debt Resolution (Phase 5)

**Scope:** Production procedure for Phase-5 collection-naming-debt migration.
**Commit basis:** Plan 05-02 server.py edits + migration script are already merged to the inner repo `main` branch before this runbook is executed.
**Tooling versions (VERIFIED 2026-05-11):** mongodump/mongorestore 100.16.1, mongosh 2.8.3, mongod 7.0.32.

---

## 0. Prerequisites

Before starting any section of this runbook, confirm all of the following:

- **Tooling on PATH:**
  ```bash
  which mongodump mongorestore mongosh
  # Expected: 3 paths printed (e.g. /usr/bin/mongodump, /usr/bin/mongorestore, /usr/bin/mongosh)
  ```
- **Python venv active:**
  ```bash
  cd /home/damnation/emits/pltu-tenayan-full-backup
  source backend/.venv/bin/activate
  python3 --version   # Expected: Python 3.x
  ```
- **pymongo available (for the migration script):**
  ```bash
  python3 -c "import pymongo; print(pymongo.version)"
  # Expected: version string printed, no ImportError
  ```
- **DB_NAME set:**
  ```bash
  export DB_NAME=pltu_tenayan
  ```
- **Admin credentials sourced from `memory/test_credentials.md` (gitignored — NEVER echoed).**
  Per [CREDENTIAL_HYGIENE.md](docs/audit/CREDENTIAL_HYGIENE.md): do NOT paste literal credential values into commit messages, scripts, or this runbook. The awk-based sourcing pattern from [LOCAL_SETUP.md §VPS Service Recovery](LOCAL_SETUP.md#vps-service-recovery-post-restart) is the canonical credential-load procedure.

---

## 1. Backup Procedure (D-09)

Run BEFORE any production change. Creates the restore point for §7b rollback.

```bash
BACKUP_DIR="/home/damnation/backups/pre-phase5-$(date +%Y%m%d-%H%M%S)"
mongodump --uri mongodb://localhost:27017 --db pltu_tenayan --out "$BACKUP_DIR"

# Verify .bson file count (expect 13 collections per live DB inventory 2026-05-11)
ls "$BACKUP_DIR/pltu_tenayan/"*.bson | wc -l   # Expected: 13

# Spot-check integrity per collection
for f in "$BACKUP_DIR/pltu_tenayan/"*.bson; do
  echo "$(basename "$f"):"; bsondump "$f" 2>/dev/null | head -1
done
# Expected: each line prints a JSON document (first doc of that collection) without error
```

**Expected output:** `13` from the `wc -l` command. Each `bsondump | head -1` line prints a valid JSON document (or `{"$date":...}` for timestamp-heavy collections) with no `Failed:` errors.

**Backup dir naming:** `/home/damnation/backups/pre-phase5-YYYYMMDD-HHMMSS/` (matches D-09). Retention policy: §10.

**Note on read consistency (RESEARCH Pitfall D):** `mongodump` on a live database produces per-collection point-in-time snapshots, NOT a single cross-collection atomic snapshot. This is acceptable for Phase 5 because the migration only drops EMPTY legacy collections (per D-07 count guard); canonical collections are untouched.

---

## 2. Dryrun Procedure (D-12)

Run AFTER §1 backup, BEFORE §3 deploy. Validates the migration script against a production-snapshot copy.

```bash
SNAP_DIR="/tmp/pltu_tenayan_snapshot_$(date +%Y%m%d-%H%M%S)"
mongodump --uri mongodb://localhost:27017 --db pltu_tenayan --out "$SNAP_DIR"

mongorestore \
  --uri mongodb://localhost:27017 \
  --nsFrom 'pltu_tenayan.*' \
  --nsTo 'pltu_tenayan_migration_dryrun.*' \
  "$SNAP_DIR"
# Expected: restores all collections into pltu_tenayan_migration_dryrun namespace
# Note: pass $SNAP_DIR (the dump dir), not $SNAP_DIR/pltu_tenayan/ — --nsFrom/--nsTo
# operate on the dump directory (RESEARCH Pitfall: don't pass the subdirectory).

cd /home/damnation/emits/pltu-tenayan-full-backup
python3 scripts/migrate_collection_names.py \
  --target-db pltu_tenayan_migration_dryrun \
  --apply \
  --verify
```

**Expected output:**

```
[INFO] Connected to MongoDB: mongodb://localhost:27017
[INFO] Target DB: pltu_tenayan_migration_dryrun
[INFO] Mode: apply

[VERIFY] Checksums for 'pltu_tenayan_migration_dryrun':
  smartstock: count=207, checksum=<hex>
  sumberpemakaian: count=208, checksum=<hex>
  app_settings: count=1, checksum=<hex>
  ai_chat_history: count=<N>, checksum=<hex>

[SKIP] smart_stock — does not exist (already clean or never created)
[SKIP] sumber_pemakaian — does not exist (already clean or never created)
[SKIP] settings — does not exist (already clean or never created)
[SKIP] ai_conversations — does not exist (already clean or never created)

[VERIFY] Checksums for 'pltu_tenayan_migration_dryrun':
  smartstock: count=207, checksum=<same hex>
  ...

[OK] Checksums match before and after. Zero data loss confirmed.
```

**IMPORTANT — 4 `[SKIP]` lines is the EXPECTED result.** It confirms the live `pltu_tenayan` DB is already clean: none of the 4 legacy collection names (`smart_stock`, `sumber_pemakaian`, `settings`, `ai_conversations`) exist in the live database. Per RESEARCH Pitfall 4: "If the script reports '[SKIP] — does not exist' for all 4 legacy names, this is the EXPECTED result. It confirms the system is already in a clean state. Proceed to §3 (code deploy)."

**Cleanup after dryrun:**

```bash
mongosh pltu_tenayan_migration_dryrun --eval "db.dropDatabase()"
rm -rf "$SNAP_DIR"
# Expected: dropDatabase returns { ok: 1 }; $SNAP_DIR removed
```

---

## 3. Read-Path Switch Deploy (D-06 steps 1-3)

**Assumption:** Plan 05-02 (10 surgical edits to `backend/server.py` + `scripts/migrate_collection_names.py`) is merged to the inner repo `main` branch. The code is already in the repo; this step deploys it to the running VPS service.

**Step 1 — Pull the inner repo:**

```bash
cd /home/damnation/emits/pltu-tenayan-full-backup
git status    # must be clean before pulling
git pull --ff-only
# Expected: Fast-forward merge (or "Already up to date.")
# Do NOT use --rebase; use --ff-only to stay consistent with the outer-repo commit boundary.
```

**Step 2 — Restart uvicorn (maintenance window ~5 min):**

Follow **[LOCAL_SETUP.md §"VPS Service Recovery"](LOCAL_SETUP.md#vps-service-recovery-post-restart)** — the full uvicorn-restart procedure lives there. Do NOT duplicate it here.

After restart, verify the backend is responding:

```bash
curl -fsS http://localhost:8013/api/health
# Expected: HTTP 200 + JSON body (e.g. {"status":"ok"} or similar)
```

**Step 3 — Smoke-test AI module endpoints (RESEARCH Focus 6):**

Source admin credentials (per LOCAL_SETUP.md §"VPS Service Recovery" §3 pattern — use awk, not grep/head, for the full multi-line credential block):

```bash
cd /home/damnation/emits/pltu-tenayan-full-backup
export TEST_ADMIN_EMAIL="$(grep -E '^- Email:' memory/test_credentials.md | head -1 | awk '{print $3}')"
export TEST_ADMIN_PASSWORD="$(grep -E '^- Password:' memory/test_credentials.md | head -1 | awk '{print $3}')"

# 1. Login and capture token
TOKEN=$(curl -fsS -X POST http://localhost:8013/api/auth/login \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "import json,os;print(json.dumps({'email':os.environ['TEST_ADMIN_EMAIL'],'password':os.environ['TEST_ADMIN_PASSWORD']}))")" \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])")
# Expected: TOKEN is set (non-empty string)

# 2. Smoke: /ai/quick/smart-stock — should now return non-zero penerimaan (207 records)
curl -fsS http://localhost:8013/api/ai/quick/smart-stock \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# Expected: total_penerimaan > 0, current_stock is a realistic number (not 0)

# 3. Smoke: /ai/quick/coa-alerts — potential_loss now uses real price_per_kcal from app_settings
curl -fsS http://localhost:8013/api/ai/quick/coa-alerts \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# Expected: HTTP 200; potential_loss may differ from pre-migration value (EXPECTED — uses real settings)

# 4. Smoke: AI query (smart_stock module) — context should include real data
curl -fsS -X POST http://localhost:8013/api/ai/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "berapa total stok batubara saat ini?", "module": "smart_stock"}' \
  | python3 -m json.tool
# Expected: HTTP 200; no 500 errors

unset TEST_ADMIN_EMAIL TEST_ADMIN_PASSWORD TOKEN
```

**Behavioral note:** After this deploy, `/ai/quick/smart-stock` will return REAL data (207 smartstock records aggregated). `potential_loss` in `/ai/quick/coa-alerts` may change (real `price_per_kcal_per_ton` from `app_settings` instead of hardcoded default 50). Both are positive consequences of ADR-009 + ADR-011. Note this in the operator handoff.

---

## 4. Observation Window Checklist (>=48h, D-06 step 4)

After §3 deploy, record the cutover timestamp and do NOT proceed to §6 (legacy-drop) for at least 48 hours.

```
Cutover applied at:      YYYY-MM-DD HH:MM TZ
Earliest legacy-drop:    cutover + 48h  =  YYYY-MM-DD HH:MM TZ
```

During the 48-hour window, verify the following checklist:

- [ ] `tail -f /home/damnation/emits/logs/backend.log` shows no new tracebacks involving `smart_stock`, `sumber_pemakaian`, `settings`, or `ai_conversations`.
- [ ] `curl -fsS http://localhost:8013/api/health` returns 200 throughout the window (no service interruption).
- [ ] AI module smoke (§3 step 2 and step 3) returns NON-ZERO totals (`total_penerimaan > 0`, coa-alerts returns 200) — confirms the read-switch to canonical collections is working.
- [ ] `mongosh pltu_tenayan --eval "['smart_stock','sumber_pemakaian','settings','ai_conversations'].forEach(c=>print(c+': '+db.getCollectionNames().includes(c)))"` reports `false` for all 4 — confirms the live DB still has no legacy collections (same state as pre-cutover; this is the negative-control assertion).
- [ ] No operator complaints about COA export PDF pricing differences. The `potential_loss` figure may change once `app_settings` real value is used (per ADR-011 and RESEARCH Focus 6 §"Endpoint 2"). This is EXPECTED — document in the operator handoff that the behavioral change is intentional.

**Rollback criteria during observation window:** If ANY of the above checks fails (e.g., traceback in logs involving a legacy name, repeated 500 on an AI endpoint), proceed to §7a (code-only rollback) immediately. Do NOT wait for the 48h window to expire before rolling back on a confirmed regression.

---

## 5. pytest Regression Gate (D-14)

Run AFTER the 48h observation window passes and ALL §4 checklist items are signed off. Run BEFORE §6 legacy-drop.

Source credentials and run the full suite per [TEST-RUNNER.md §"One-time setup"](backend/tests/TEST-RUNNER.md#one-time-setup):

```bash
cd /home/damnation/emits/pltu-tenayan-full-backup
export TEST_ADMIN_EMAIL="$(grep -E '^- Email:' memory/test_credentials.md | head -1 | awk '{print $3}')"
export TEST_ADMIN_PASSWORD="$(grep -E '^- Password:' memory/test_credentials.md | head -1 | awk '{print $3}')"
export TEST_OPERATOR_EMAIL="$(grep -E '^- Email:' memory/test_credentials.md | sed -n '2p' | awk '{print $3}')"
export TEST_OPERATOR_PASSWORD="$(grep -E '^- Password:' memory/test_credentials.md | sed -n '2p' | awk '{print $3}')"
export TEST_VIEWER_EMAIL="$(grep -E '^- Email:' memory/test_credentials.md | sed -n '3p' | awk '{print $3}')"
export TEST_VIEWER_PASSWORD="$(grep -E '^- Password:' memory/test_credentials.md | sed -n '3p' | awk '{print $3}')"
export MONGO_URL="mongodb://localhost:27017"
export DB_NAME="pltu_tenayan"
export JWT_SECRET="$(grep '^JWT_SECRET=' backend/.env | cut -d= -f2-)"

cd backend
.venv/bin/pytest tests/ -q
echo "exit=$?"
# Expected: exit=0 and summary line like "111 passed in Ts"
```

**Hard gate:** If `exit=1` or any test fails, HALT — do not proceed to §6 legacy-drop. Per D-14: investigate the failing test and apply a fix-forward (add the missing read-path edit that the audit missed). The `test_no_legacy_collection_reads_in_server_py` test in `test_clean_checkout_gate.py` will catch any legacy collection reads that remain in `server.py`.

See [TEST-RUNNER.md](backend/tests/TEST-RUNNER.md) for the full credential-sourcing block, troubleshooting (port-in-use, stale PID file), and destructive-test flags.

---

## 6. Legacy-Drop Procedure (D-06 step 5)

Run ONLY after §4 observation window is signed off AND §5 pytest gate exits 0.

**Step 1 — Final pre-drop dry-run on PRODUCTION DB:**

```bash
cd /home/damnation/emits/pltu-tenayan-full-backup
python3 scripts/migrate_collection_names.py --target-db pltu_tenayan --dry-run
# Expected: 4 [SKIP] lines (live DB has none of the legacy names already) — same result as dryrun
# Output:
#   [SKIP] smart_stock — does not exist (already clean or never created)
#   [SKIP] sumber_pemakaian — does not exist (already clean or never created)
#   [SKIP] settings — does not exist (already clean or never created)
#   [SKIP] ai_conversations — does not exist (already clean or never created)
```

**Step 2 — Apply with verification:**

```bash
python3 scripts/migrate_collection_names.py --target-db pltu_tenayan --apply --verify
# Expected: same 4 [SKIP] lines + [OK] Checksums match before and after. Zero data loss confirmed.
```

**Safety guard:** `--target-db pltu_tenayan` is REQUIRED explicitly. A bare invocation (without `--target-db`) that resolves to production is rejected by the script with exit code 1 (RESEARCH Pitfall A; production-DB safety guard). Do NOT omit the flag.

**Step 3 — Post-drop verification:**

```bash
mongosh pltu_tenayan --eval \
  "['smart_stock','sumber_pemakaian','settings','ai_conversations'].forEach(c=>print(c+': '+db.getCollectionNames().includes(c)))"
# Expected: all 4 report "false" (legacy names absent — same state as before, now confirmed)
```

**Step 4 — Re-run pytest regression gate (per D-14):**

```bash
cd /home/damnation/emits/pltu-tenayan-full-backup/backend
.venv/bin/pytest tests/ -q
echo "exit=$?"
# Expected: exit=0, same pass count as §5 gate
```

---

## 7. Rollback Procedure (D-10)

Rollback has two distinct paths used in DIFFERENT failure modes. Read both before starting. The code-only path (§7a) is the common case; the data-restore path (§7b) is an extreme edge case that should never be needed given the D-07 pre-drop count guard and D-08 empty-legacy confirmation (all 4 legacy collections were confirmed absent from the live `pltu_tenayan` DB at the time of Phase 5 planning).

### 7a. Code-Only Rollback (most common)

**When to use:** The §3 read-switch deploy introduced a regression (e.g., pytest fails post-deploy, an AI endpoint returns 5xx, logs show unexpected tracebacks). The legacy collections in mongod are NOT touched in this scenario — `--apply` has not run yet. Only the code (`server.py`) needs to be reverted.

```bash
# Identify the Plan 05-02 commit in the inner repo:
cd /home/damnation/emits/pltu-tenayan-full-backup
git log --oneline | head -10
# Find the commit for "feat(05-02): apply 10 surgical server.py edits" (or similar)

git revert <commit-hash>
# Git will open an editor for the revert commit message; save and close.
# Then follow LOCAL_SETUP.md §VPS Service Recovery to restart uvicorn.
```

After reverting, follow **[LOCAL_SETUP.md §"VPS Service Recovery"](LOCAL_SETUP.md#vps-service-recovery-post-restart)** to restart uvicorn with the reverted code.

**Post-revert verification:**

```bash
# Confirm legacy reads are back in server.py:
grep -cE "db\.(smart_stock|sumber_pemakaian)\b|db\.settings\.find_one" \
  /home/damnation/emits/pltu-tenayan-full-backup/backend/server.py
# Expected: > 0 (the legacy reads are restored by the revert)

# Re-run smoke tests from §3:
curl -fsS http://localhost:8013/api/health
# Expected: 200
```

### 7b. Full Data Restore (extreme edge case)

**When to use:** ONLY if a CANONICAL collection (`smartstock`, `sumberpemakaian`, `app_settings`, `ai_chat_history`) somehow lost data AFTER `--apply` ran on the production DB AND the §7a code revert is not sufficient. Per D-08, the legacy collections were EMPTY at drop time — the drop step itself cannot delete real data. The only theoretical risk is canonical-collection corruption coincident with the migration window.

> **WARNING:** `mongorestore --drop` will replace ALL collections in the target namespace from the backup. Any writes that occurred between backup time and the restore will be LOST. Use ONLY after confirming with the operator that actual data loss has occurred and the backup is the appropriate restore point.

```bash
BACKUP_DIR="/home/damnation/backups/pre-phase5-YYYYMMDD-HHMMSS"   # replace with actual dir name from §1

mongorestore \
  --drop \
  --uri mongodb://localhost:27017 \
  --nsInclude 'pltu_tenayan.*' \
  "$BACKUP_DIR"
# Expected: each collection in the backup printed as "restoring pltu_tenayan.<name>"
# --drop drops each target collection before restoring from the dump file.
# --nsInclude 'pltu_tenayan.*' restores only the pltu_tenayan namespace.
```

**Post-restore verification:**

Re-run §5 pytest gate and the §3 AI-module smoke tests. Confirm data counts match the backup-time state before any migration was applied.

---

## 8. Cleanup Procedure (DEBT-05)

Post-cutover and post-legacy-drop, `DATABASE_SCHEMA.md` must be cleaned of all `legacy` markings per DEBT-05. Specific lines to edit are catalogued in RESEARCH Focus 8 (`.planning/phases/05-collection-naming-debt-resolution/05-RESEARCH.md §Research Focus 8`).

This cleanup is handled by **Phase 5 Plan 05-04** (separate plan, `autonomous: false`). Plan 05-04 includes the checkpoint that pauses for operator confirmation at the legacy-drop step before proceeding to `DATABASE_SCHEMA.md` cleanup.

See: [.planning/phases/05-collection-naming-debt-resolution/05-04-PLAN.md](../../.planning/phases/05-collection-naming-debt-resolution/05-04-PLAN.md)

---

## 9. Cross-References

| Reference | Path | Why |
|-----------|------|-----|
| [LOCAL_SETUP.md §"VPS Service Recovery"](LOCAL_SETUP.md#vps-service-recovery-post-restart) | inner repo, top-level | uvicorn-restart procedure (§3 deploy, §7a rollback) — do NOT duplicate here |
| [TEST-RUNNER.md §"One-time setup"](backend/tests/TEST-RUNNER.md#one-time-setup) | inner repo, `backend/tests/TEST-RUNNER.md` | Credential-sourcing block for pytest gate (§5) |
| [ADR-009: smartstock](../../.planning/decisions/ADR-009-canonical-smartstock.md) | outer repo, `.planning/decisions/` | D-01 canonical-name source for `smartstock` / `smart_stock` |
| [ADR-010: sumberpemakaian](../../.planning/decisions/ADR-010-canonical-sumberpemakaian.md) | outer repo, `.planning/decisions/` | D-02 canonical-name source for `sumberpemakaian` / `sumber_pemakaian` |
| [ADR-011: app_settings](../../.planning/decisions/ADR-011-canonical-app-settings.md) | outer repo, `.planning/decisions/` | D-03 canonical-name source for `app_settings` / `settings` |
| [ADR-012: ai_chat_history](../../.planning/decisions/ADR-012-canonical-ai-chat-history.md) | outer repo, `.planning/decisions/` | D-04 canonical-name source for `ai_chat_history` / `ai_conversations` |
| [D-NN labels (D-01..D-14)](../../.planning/phases/05-collection-naming-debt-resolution/05-CONTEXT.md) | `.planning/phases/05-collection-naming-debt-resolution/05-CONTEXT.md` | User-locked decisions traced from this runbook |
| [RESEARCH Focus 6](../../.planning/phases/05-collection-naming-debt-resolution/05-RESEARCH.md) | `.planning/phases/05-collection-naming-debt-resolution/05-RESEARCH.md` | AI module smoke-test curl commands (§3, §4) |
| [scripts/migrate_collection_names.py](scripts/migrate_collection_names.py) | inner repo, `scripts/` | The migration script this runbook documents (Plan 05-02 deliverable) |

---

## 10. Backup Retention (D-11)

The pre-phase5 backup at `/home/damnation/backups/pre-phase5-YYYYMMDD-HHMMSS/` MUST be retained for at least **30 days** after milestone v1.0 close. The operator decides retention beyond 30 days. There is NO auto-delete in the migration script — backup retention is an operator-managed policy.

**Recommended backup directory permissions:**

```bash
chmod 700 /home/damnation/backups/
# Prevents world-read of .bson files (which contain production fuel-receipt records).
# The operator owns the backups directory.
```

**Retention confirmation checklist:**

- [ ] Backup dir exists: `ls -lh /home/damnation/backups/pre-phase5-*/`
- [ ] Backup dir size is non-zero: `du -sh /home/damnation/backups/pre-phase5-*/pltu_tenayan/`
- [ ] Backup dir has 13 `.bson` files: `ls /home/damnation/backups/pre-phase5-*/pltu_tenayan/*.bson | wc -l` → 13
- [ ] Directory permissions set to 700: `stat -c "%a" /home/damnation/backups/` → 700
- [ ] Earliest deletion date recorded by operator: `cutover_date + 30_days + v1.0_close_gap`

---

*MIGRATION_RUNBOOK.md created: 2026-05-11 (Phase 5 Plan 05-03). Citations: ADR-009..012 (canonical names), D-01..D-14 (CONTEXT.md decisions), RESEARCH Focus 1/4/6/7 (verbatim commands and structure).*
