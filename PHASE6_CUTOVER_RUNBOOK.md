# PHASE6_CUTOVER_RUNBOOK.md — OpenRouter Production Cutover (Phase 6)

**Scope:** Production cutover procedure for Phase-6 OpenRouter migration.
**Commit basis:** Plans 06-01..06-05 already merged to inner repo `main` branch before this runbook is executed.
**Tooling versions (VERIFIED 2026-05-11):** uvicorn 0.x, httpx (in .venv), mongosh 2.8.3.

---

## 0. Pre-Cutover Sanity

Confirm all of the following before touching production:

**0a. Phase-6 plan SUMMARY files present:**

```bash
ls /home/damnation/emits/.planning/phases/06-operational-unblocks/06-0{1,2,3,4,5}-SUMMARY.md
# Expected: 5 paths printed (06-01 through 06-05)
```

**0b. Full test suite green under AI_FAKE:**

```bash
cd /home/damnation/emits/pltu-tenayan-full-backup/backend
AI_FAKE=1 .venv/bin/pytest tests/ -x -q
echo "exit=$?"
# Expected: exit=0 (one pre-existing test_clean_checkout_gate failure is acceptable — confirmed pre-Phase-6)
```

**0c. Zero legacy references in inner-repo code and markdown:**

```bash
cd /home/damnation/emits/pltu-tenayan-full-backup

# No emergentintegrations imports
grep -rn "emergentintegrations" backend/app/ backend/server.py backend/requirements.txt
# Expected: zero matches

# No legacy EMERGENT_LLM_KEY in tracked markdown
grep -rn "EMERGENT_LLM_KEY" --include="*.md" .
# Expected: zero matches

# No stale ai_conversations collection references
grep -rn "ai_conversations" backend/server.py frontend/src/
# Expected: zero matches
```

**0d. OpenRouter account ready:**

- Log in to https://openrouter.ai/keys
- Confirm dashboard credit balance > $5 (covers ~5,500 smart-blending calls at ~$0.0009/call for `openai/gpt-4o-mini`, per Phase-6 D-04 cost estimate)
- Copy the API key — it starts with `sk-or-`

---

## 1. Prerequisites

| Item | Detail |
|------|--------|
| VPS SSH access | `ssh damnation@103.150.197.225` |
| OPENROUTER_API_KEY | Format: `sk-or-<40+ chars>` — from https://openrouter.ai/keys |
| `screen` or `tmux` (optional) | Recommended for safe process management during restart |
| Inner-repo path | `/home/damnation/emits/pltu-tenayan-full-backup/` |
| Production ports | Backend: `:8013`, Frontend: `:3013` |

---

## 2. Backup Current .env

Before any production change, preserve the current `.env` state:

```bash
cp /home/damnation/emits/pltu-tenayan-full-backup/backend/.env \
   /home/damnation/emits/pltu-tenayan-full-backup/backend/.env.bak-$(date +%Y%m%d-%H%M%S)

# Confirm backup exists
ls -lh /home/damnation/emits/pltu-tenayan-full-backup/backend/.env.bak-*
# Expected: one file printed with non-zero size
```

This preserves the old placeholder value (and any other current settings) for rollback per §5.

---

## 3. Apply — Rotate OPENROUTER_API_KEY into Production .env

### Step 1 — Edit .env

```bash
nano /home/damnation/emits/pltu-tenayan-full-backup/backend/.env
```

Inside the editor, make the following changes:

1. Find the line `OPENROUTER_API_KEY=` (added by Plan 06-01 as an empty placeholder)
2. Replace it with your real key:
   ```
   OPENROUTER_API_KEY=sk-or-<your-real-key-here>
   ```
3. Confirm the default model line is present (added by Plan 06-01):
   ```
   OPENROUTER_DEFAULT_MODEL=openai/gpt-4o-mini
   ```
4. Confirm there is NO `EMERGENT_LLM_KEY=` line remaining (removed by Plan 06-01)
5. Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X` in nano)

**Verify the three key invariants after saving:**

```bash
cd /home/damnation/emits/pltu-tenayan-full-backup/backend

# 1. OPENROUTER_API_KEY is set (non-empty)
grep -E "^OPENROUTER_API_KEY=sk-or-" .env && echo "KEY OK" || echo "KEY MISSING OR WRONG FORMAT"

# 2. Default model is present
grep -c "^OPENROUTER_DEFAULT_MODEL=openai/gpt-4o-mini" .env
# Expected: 1

# 3. No legacy EMERGENT_LLM_KEY remains
grep -c "EMERGENT_LLM_KEY" .env
# Expected: 0
```

### Step 2 — Stop uvicorn

```bash
pkill -f "uvicorn.*server:app" || true
sleep 2
pgrep -f uvicorn || echo "uvicorn stopped"
# Expected: "uvicorn stopped" (or empty output from pgrep)
```

### Step 3 — Start uvicorn

Follow **[LOCAL_SETUP.md §"VPS Service Recovery"](LOCAL_SETUP.md#vps-service-recovery-post-restart)** — the full procedure lives there. For convenience, the relevant commands are:

```bash
cd /home/damnation/emits/pltu-tenayan-full-backup/backend

# Activate venv and source .env (set -a exports all vars to subprocess)
source .venv/bin/activate
set -a
. ./.env
set +a

# Start uvicorn with production config
nohup ./.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8013 \
  >> /home/damnation/emits/logs/backend.log 2>&1 &
```

### Step 4 — Wait for warmup and verify

```bash
sleep 5

# Health check
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8013/api/health
# Expected: 200

# Tail logs for 30s — confirm no startup errors
tail -n 50 /home/damnation/emits/logs/backend.log | grep -E "ERROR|ImportError|NameError|Traceback" || echo "No startup errors"
# Expected: "No startup errors"
```

---

## 4. Smoke Tests

### Smoke A: Smart-Blending 3-GCV Probe (OPS-01 SC-1)

The three target GCV values 4000 / 4200 / 4500 are the acceptance contract per D-08. Each curl must return HTTP 200 with parseable JSON containing a non-empty `blend` array.

**Step 1 — Obtain admin JWT (never paste credentials into this runbook):**

```bash
cd /home/damnation/emits/pltu-tenayan-full-backup

export TEST_ADMIN_EMAIL="$(awk '/^## Akun Admin$/,/^##/{ if(/Email:/){sub(/^- Email:[[:space:]]*/,"");print;exit} }' memory/test_credentials.md)"
export TEST_ADMIN_PASSWORD="$(awk '/^## Akun Admin$/,/^##/{ if(/Password:/){sub(/^- Password:[[:space:]]*/,"");print;exit} }' memory/test_credentials.md)"

TOKEN=$(curl -fsS -X POST http://localhost:8013/api/auth/login \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "import json,os;print(json.dumps({'email':os.environ['TEST_ADMIN_EMAIL'],'password':os.environ['TEST_ADMIN_PASSWORD']}))")" \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])")

unset TEST_ADMIN_EMAIL TEST_ADMIN_PASSWORD
echo "TOKEN acquired: ${TOKEN:0:20}..."
```

**Step 2 — Run 3 GCV smoke calls:**

```bash
# GCV 4000
curl -s -X POST http://localhost:8013/api/smart-blending/recommend \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target_gcv": 4000, "max_ash": 12, "max_sulphur": 0.7, "max_tm": 30}' \
  | python3 -c "import json,sys; r=json.load(sys.stdin); b=r.get('ai_recommendation',{}).get('blend',[]); print(f'GCV 4000: blend={len(b)} items, OK={bool(b)}')"
# Expected: GCV 4000: blend=N items, OK=True

# GCV 4200
curl -s -X POST http://localhost:8013/api/smart-blending/recommend \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target_gcv": 4200, "max_ash": 12, "max_sulphur": 0.7, "max_tm": 30}' \
  | python3 -c "import json,sys; r=json.load(sys.stdin); b=r.get('ai_recommendation',{}).get('blend',[]); print(f'GCV 4200: blend={len(b)} items, OK={bool(b)}')"
# Expected: GCV 4200: blend=N items, OK=True

# GCV 4500
curl -s -X POST http://localhost:8013/api/smart-blending/recommend \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target_gcv": 4500, "max_ash": 12, "max_sulphur": 0.7, "max_tm": 30}' \
  | python3 -c "import json,sys; r=json.load(sys.stdin); b=r.get('ai_recommendation',{}).get('blend',[]); print(f'GCV 4500: blend={len(b)} items, OK={bool(b)}')"
# Expected: GCV 4500: blend=N items, OK=True

unset TOKEN
```

**Acceptance criteria:** All 3 calls return `OK=True`. If any returns 503 with detail "Layanan AI sementara tidak tersedia. Silakan coba lagi sebentar.", check OpenRouter dashboard credit balance and API key validity before retrying. Persistent 503 → rollback per §5.

### Smoke B: AI Chat UI Live Smoke (OPS-04 SC-4)

Operator visits `http://103.150.197.225:3013/ai-chat` in a browser and confirms:

1. **Empty-state or existing conversations:** Sidebar shows "Percakapan Saya" heading + "Percakapan Baru" button. Main panel shows "Belum ada percakapan" + "Mulai Percakapan" CTA (if no prior conversations), OR shows the most recent conversation's messages (if prior conversations exist).

2. **New conversation works:** Click "Percakapan Baru" → new conversation appears at top of sidebar with title "Percakapan tanpa judul".

3. **Message send + AI response:** Type "Berapa total stok batubara saat ini?" and press Enter.
   - User message bubble appears immediately (right-aligned, cyan).
   - "AI sedang mengetik..." indicator appears below.
   - Within ~3–8s: AI response bubble appears (left-aligned, glass-card) in Indonesian.
   - Sidebar updates conversation title to first 50 chars of user message.
   - `last_message_at` timestamp updates to "baru saja".

4. **Conversation switch + history persistence:** Click a different conversation in the sidebar → messages from that conversation render. Click back on the new conversation → the user+AI exchange is still visible (persisted in `ai_chat_history`).

5. **Indonesian error toast (OPS-02 cross-cut):**
   - Temporarily set `OPENROUTER_API_KEY=sk-or-invalid` in `.env` and restart uvicorn (per §3 Step 2–4).
   - Send a chat message.
   - EXPECTED: sonner toast appears top-right with title "Layanan AI tidak tersedia", body "Layanan AI sementara tidak tersedia. Silakan coba lagi sebentar.", and "Coba lagi" button visible; the optimistic user message is removed from view.
   - Restore the real key in `.env` and restart uvicorn.
   - Click "Coba lagi" or resend — EXPECTED: AI response succeeds.

---

## 5. Rollback

**When to use:** Any smoke test in §4 returns a persistent failure that cannot be resolved by checking the API key or OpenRouter dashboard.

### Phase-6-specific revert steps:

**Step 1 — Restore the previous .env immediately:**

```bash
# Identify the backup file (created in §2)
ls /home/damnation/emits/pltu-tenayan-full-backup/backend/.env.bak-*

# Restore (replace with actual filename):
cp /home/damnation/emits/pltu-tenayan-full-backup/backend/.env.bak-YYYYMMDD-HHMMSS \
   /home/damnation/emits/pltu-tenayan-full-backup/backend/.env
```

**Step 2 — Restart uvicorn with restored env:**

Follow [LOCAL_SETUP.md §"VPS Service Recovery"](LOCAL_SETUP.md#vps-service-recovery-post-restart) to restart. After restart:

```bash
curl -fsS http://localhost:8013/api/health
# Expected: HTTP 200
```

**Step 3 — Revert Phase-6 inner-repo commits (if code changes contributed to the failure):**

```bash
cd /home/damnation/emits/pltu-tenayan-full-backup

# Identify the Phase-6 merge commits (Plans 06-01 through 06-05):
git log --oneline | head -20
# Find commits for feat(06-01) through feat(06-05); note their SHAs

# Revert from newest to oldest (use the actual SHAs from git log):
git revert <phase-6-plan-05-commit-sha>
git revert <phase-6-plan-04-commit-sha>
git revert <phase-6-plan-03-commit-sha>
git revert <phase-6-plan-02-commit-sha>
git revert <phase-6-plan-01-commit-sha>
```

**Step 4 — Cross-reference the Phase-5 rollback procedures** for deeper data-layer rollback if needed:

See [MIGRATION_RUNBOOK.md §7 Rollback](MIGRATION_RUNBOOK.md#7-rollback-procedure-d-10) — covers both code-only (§7a) and full data-restore (§7b) paths. The Phase-5 30-day backup retention policy (D-11) guarantees the pre-Phase-5 DB snapshot is available at `/home/damnation/backups/pre-phase5-YYYYMMDD-HHMMSS/` through the milestone v1.0 window.

**Document the rollback:** Append a rollback note to `06-06-SUMMARY.md` with timestamp, operator, failure description, and which step was used.

---

## 6. Cleanup and Observation Window

After all smoke tests in §4 pass:

**6a. 48-hour observation window:**

```
Cutover applied at:     YYYY-MM-DD HH:MM WIB
Earliest cleanup:       cutover + 48h = YYYY-MM-DD HH:MM WIB
```

During the 48-hour window, monitor:

- [ ] `tail -f /home/damnation/emits/logs/backend.log` — no new `LLMUnavailableError` events reaching users (occasional transient retries are expected; persistent 503s are not).
- [ ] `curl -fsS http://localhost:8013/api/health` returns 200 throughout the window.
- [ ] Smart-blending endpoint continues to return non-empty blend arrays when called.
- [ ] OpenRouter dashboard shows spend accumulating normally (not zero, which would indicate key not being used, or unexpectedly high, which would indicate a loop bug).

**6b. After 48h with zero user-visible 503s:**

```bash
# Delete .env backup files
rm /home/damnation/emits/pltu-tenayan-full-backup/backend/.env.bak-*

# Confirm deletion
ls /home/damnation/emits/pltu-tenayan-full-backup/backend/.env.bak-* 2>/dev/null \
  && echo "WARN: backup files still present" || echo "Backup files removed"
```

**6c. Monthly spend monitoring:**

Check OpenRouter dashboard at https://openrouter.ai/dashboard monthly. With `openai/gpt-4o-mini` as the default model, typical smart-blending usage costs ~$0.0009/call. If the operator wants to upgrade to a higher-quality model (e.g., `anthropic/claude-3-5-haiku`), set `OPENROUTER_DEFAULT_MODEL=<new-model-id>` in `.env` and restart uvicorn — no code deploy required (D-04).

---

## Cross-References

| Reference | Path | Why |
|-----------|------|-----|
| [LOCAL_SETUP.md §"VPS Service Recovery"](LOCAL_SETUP.md#vps-service-recovery-post-restart) | inner repo, top-level | Full uvicorn-restart procedure (§3, §5 rollback) |
| [MIGRATION_RUNBOOK.md §7 Rollback](MIGRATION_RUNBOOK.md#7-rollback-procedure-d-10) | inner repo, top-level | Phase-5 rollback procedures (data-layer fallback) |
| [backend/.env.example](backend/.env.example) | inner repo, `backend/` | Canonical env-var reference; `OPENROUTER_API_KEY` + `OPENROUTER_DEFAULT_MODEL` documented there |
| [06-CONTEXT.md D-04](../../.planning/phases/06-operational-unblocks/06-CONTEXT.md) | outer repo planning | Default model decision: `openai/gpt-4o-mini`; operator-overridable via env |
| [06-CONTEXT.md D-08](../../.planning/phases/06-operational-unblocks/06-CONTEXT.md) | outer repo planning | 3-GCV smoke contract: 4000 / 4200 / 4500 as OPS-01 SC-1 acceptance criteria |
| [06-CONTEXT.md D-09](../../.planning/phases/06-operational-unblocks/06-CONTEXT.md) | outer repo planning | Retry-with-backoff (1s/2s/4s); `LLMUnavailableError` → HTTP 503 Indonesian copy |
| [docs/audit/AI_CHAT_API.md](docs/audit/AI_CHAT_API.md) | inner repo | Endpoint contract for `/api/ai/conversations/*` (Plan 06-04 deliverable) |
| [docs/audit/CREDENTIAL_HYGIENE.md](docs/audit/CREDENTIAL_HYGIENE.md) | inner repo | Never echo `OPENROUTER_API_KEY` in scripts or commit messages |

---

*PHASE6_CUTOVER_RUNBOOK.md created: 2026-05-11 (Phase 6 Plan 06-06, Task 06-06-00). Follows MIGRATION_RUNBOOK.md style (Phase 5 Plan 05-03). Citations: D-04 (default model), D-08 (3-GCV smoke), D-09 (retry/503), D-10 (error UX), LOCAL_SETUP.md §VPS Service Recovery (uvicorn restart).*
