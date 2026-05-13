---
phase: 02-authentication-stabilization
plan: 01
subsystem: auth-hygiene
tags: [credential-hygiene, gitignore, pre-commit, scanner, AUTHFIX-05]
requires: []
provides:
  - "Credential hygiene gate enforcing zero-credential-leakage on tracked files"
  - "Reusable scanner (scripts/check_credentials.sh) with four pattern passes"
  - "Pre-commit hook in inner repo wired to the scanner"
  - "TEST_ADMIN_EMAIL/PASSWORD env-var contract for Phase-2 follow-on plans"
affects:
  - "pltu-tenayan-full-backup/.gitignore"
  - "pltu-tenayan-full-backup/memory/test_credentials.md (now untracked)"
  - "pltu-tenayan-full-backup/scripts/check_credentials.sh"
  - "pltu-tenayan-full-backup/docs/audit/CREDENTIAL_HYGIENE.md"
  - "pltu-tenayan-full-backup/.git/hooks/pre-commit"
  - "pltu-tenayan-full-backup/.git/hooks/pre-commit.large-files (preserved sub-script)"
tech-stack:
  added: []
  patterns:
    - "Bash scanner over `git ls-files` with EXCLUDE allowlist filtered via `grep -vxFf`"
    - "Chained pre-commit hook (large-file guard + credential scanner)"
    - "Env-var sourcing contract for test credentials (TEST_ADMIN_PASSWORD etc.)"
key-files:
  created:
    - "pltu-tenayan-full-backup/scripts/check_credentials.sh"
    - "pltu-tenayan-full-backup/docs/audit/CREDENTIAL_HYGIENE.md"
    - "pltu-tenayan-full-backup/.git/hooks/pre-commit (chained version)"
    - "pltu-tenayan-full-backup/.git/hooks/pre-commit.large-files (preserved original)"
  modified:
    - "pltu-tenayan-full-backup/.gitignore"
  removed-from-index:
    - "pltu-tenayan-full-backup/memory/test_credentials.md (file stays on disk; no longer tracked)"
decisions:
  - "Chained the existing large-file pre-commit guard rather than replacing it; new hook calls .git/hooks/pre-commit.large-files first, then the scanner."
  - "Allowlisted four pre-existing test files and four iteration_*.json reports under TODO Phase 4 TEST-02; allowlisted API_REFERENCE.md / DEPLOYMENT_GUIDE.md / frontend/public/docs copies + memory/PRD.md under TODO Phase 3 STAB-03. Each entry carries a phase-tagged TODO so debt is visible, not silent."
  - "Scanner uses grep -lEI on tracked files (not on the working tree) so untracked junk does not produce noise."
  - "Hook bypass via --no-verify is documented as policy violation, not a workflow option."
metrics:
  duration: ~25min
  completed: 2026-05-10
---

# Phase 02 Plan 01: Credential Hygiene Gate (AUTHFIX-05) — Summary

Closes AUTHFIX-05. The inner repo (`pltu-tenayan-full-backup/`) now has a deterministic credential-hygiene gate: `memory/test_credentials.md` is gitignored and untracked, a four-pattern scanner runs over `git ls-files` with a phase-tagged exemption allowlist, and a chained pre-commit hook calls the scanner before every commit. The negative-path proof confirmed the hook blocks JWT-shaped strings (exit=1 with FAIL [JWT] banner). Phase-2 follow-on plans 02-02 and 02-03 may now rely on the `TEST_ADMIN_EMAIL` / `TEST_ADMIN_PASSWORD` env-var contract documented in `CREDENTIAL_HYGIENE.md`.

## Inner-repo commit

- Hash: `550cd18`
- Repo: `pltu-tenayan-full-backup/` (inner, separate from outer `/home/damnation/emits`)
- Subject: `feat(authfix-05): credential hygiene gate (gitignore + scanner + pre-commit hook)`
- Files touched: `.gitignore` (M), `docs/audit/CREDENTIAL_HYGIENE.md` (A), `memory/test_credentials.md` (D — untracked only; file remains on disk), `scripts/check_credentials.sh` (A)
- Net: 252 insertions, 9 deletions across 4 files.

## Tasks executed

| # | Name | Status | Notes |
|---|------|--------|-------|
| 1 | Untrack memory/test_credentials.md and add gitignore entry | done | `git ls-files memory/test_credentials.md` returns empty; `git check-ignore` exits 0; file remains on disk; `memory/PRD.md` still tracked. |
| 2 | Create the credential scanner script | done | scripts/check_credentials.sh executable, four patterns implemented, EXCLUDE allowlist with phase-tagged TODOs, exits 0 on the current tree (164 files scanned, 16 exemptions). |
| 3 | Write CREDENTIAL_HYGIENE.md contract document | done | 149 lines, all 9 required headings present, references TEST_ADMIN_PASSWORD and scripts/check_credentials.sh, documents Phase-3/Phase-4 exemption TODOs. |
| 4 | Wire scanner as pre-commit hook | done | Existing large-file guard preserved at `.git/hooks/pre-commit.large-files` and chained from new hook. Negative-path proof: staging a JWT-shaped string returns exit=1 from the hook. Inner-repo commit `550cd18` landed cleanly with the hook running on its own commit. |

## Pre-commit hook content (verbatim — git does not version hooks)

```bash
#!/usr/bin/env bash
# Pre-commit chain for the inner repo.
# Stage 1: existing large-file ignore guard (preserved at .git/hooks/pre-commit.large-files).
# Stage 2: credential-hygiene scanner — source-of-truth at scripts/check_credentials.sh,
#          documented at docs/audit/CREDENTIAL_HYGIENE.md (AUTHFIX-05, plan 02-01).
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
hooks_dir="$repo_root/.git/hooks"

# --- Stage 1: large-file guard (chain pre-existing hook if present) ---
if [ -x "$hooks_dir/pre-commit.large-files" ]; then
    bash "$hooks_dir/pre-commit.large-files"
fi

# --- Stage 2: credential-hygiene scanner ---
scanner="$repo_root/scripts/check_credentials.sh"
if [ ! -x "$scanner" ]; then
    echo "pre-commit: scanner missing or not executable at ${scanner}" >&2
    echo "pre-commit: see docs/audit/CREDENTIAL_HYGIENE.md for remediation." >&2
    exit 1
fi

bash "$scanner"
```

The preserved Stage-1 sub-script `.git/hooks/pre-commit.large-files` is the original 17-line size-threshold guard verbatim (90M cap, auto-appends to `.gitignore` and `git rm --cached` for any oversized file).

## Scanner EXCLUDE allowlist (snapshot)

| Path | Reason | TODO phase |
|------|--------|------------|
| scripts/check_credentials.sh | self-reference | n/a (permanent) |
| docs/audit/CREDENTIAL_HYGIENE.md | self-reference | n/a (permanent) |
| docs/audit/LOGIN_BUG.md | audit trail discusses patterns verbatim | n/a (permanent) |
| backend/tests/test_dashboard_advanced.py | inline `"<TEST_ADMIN_PASSWORD>"` at lines 18, 28 | Phase 4 TEST-02 |
| backend/tests/test_coa_reconciliation.py | inline `"<TEST_ADMIN_PASSWORD>"` | Phase 4 TEST-02 |
| backend/tests/test_merit_order.py | inline `"<TEST_ADMIN_PASSWORD>"` | Phase 4 TEST-02 |
| backend/tests/test_po_batubara.py | inline `"<TEST_ADMIN_PASSWORD>"` | Phase 4 TEST-02 |
| test_reports/iteration_3.json | password literal in summary strings | Phase 4 TEST-02 |
| test_reports/iteration_4.json | same | Phase 4 TEST-02 |
| test_reports/iteration_5.json | same | Phase 4 TEST-02 |
| test_reports/iteration_6.json | same | Phase 4 TEST-02 |
| API_REFERENCE.md | example curl bodies inline admin password | Phase 3 STAB-03 |
| DEPLOYMENT_GUIDE.md | ${MONGO_URL} example | Phase 3 STAB-03 |
| frontend/public/docs/API_REFERENCE.md | duplicate of root | Phase 3 STAB-03 |
| frontend/public/docs/DEPLOYMENT_GUIDE.md | duplicate of root | Phase 3 STAB-03 |
| memory/PRD.md | upstream PRD inlines admin password in test-credentials block | Phase 3 STAB-03 |

16 exemptions total, every non-self-reference entry carries an explicit TODO phase tag.

## Verification — all PASS

| Check | Command | Result |
|-------|---------|--------|
| memory/test_credentials.md not tracked | `git -C pltu-tenayan-full-backup ls-files memory/test_credentials.md` | empty (PASS) |
| memory/test_credentials.md ignored | `git -C pltu-tenayan-full-backup check-ignore memory/test_credentials.md` | exit 0 (PASS) |
| file remains on disk | `test -f pltu-tenayan-full-backup/memory/test_credentials.md` | YES (PASS) |
| memory/PRD.md still tracked | `git -C pltu-tenayan-full-backup ls-files memory/PRD.md` | `memory/PRD.md` (PASS) |
| scanner executable | `test -x pltu-tenayan-full-backup/scripts/check_credentials.sh` | YES (PASS) |
| scanner exits 0 on current tree | `cd pltu-tenayan-full-backup && bash scripts/check_credentials.sh` | exit 0, "OK: no tracked credential patterns found in 164 files (after 16 exemptions)." (PASS) |
| hook executable | `test -x pltu-tenayan-full-backup/.git/hooks/pre-commit` | YES (PASS) |
| hook calls scanner | `grep -c 'check_credentials\.sh' pltu-tenayan-full-backup/.git/hooks/pre-commit` | 2 (PASS) |
| hook exits 0 on current tree | `cd pltu-tenayan-full-backup && bash .git/hooks/pre-commit` | exit 0 (PASS) |
| hygiene doc has all 9 sections | grep loop over headings | all 9 present (PASS) |
| hygiene doc >= 30 lines | `wc -l < docs/audit/CREDENTIAL_HYGIENE.md` | 149 (PASS) |
| inner commit subject contains authfix-05 | `git -C pltu-tenayan-full-backup log -1 --pretty=%s` | matches (PASS) |
| negative-path: hook blocks JWT-shaped string | stage `JWT_PREFIX<>.JWT_PREFIX<>.<sig>` snippet, run hook | exit=1, FAIL [JWT] banner (PASS), file cleaned up after |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] Existing large-file pre-commit hook required chaining (not replacement)**
- **Found during:** Task 4 read step.
- **Issue:** `.git/hooks/pre-commit` already existed as a non-sample hook (90 MB large-file guard, dated 2026-04-30). Plan instructed "if non-sample hook exists, the new content MUST chain (call existing hook first, then run the scanner)."
- **Fix:** Copied the original to `.git/hooks/pre-commit.large-files`, wrote a new `pre-commit` that invokes the preserved sub-script first (Stage 1) then the scanner (Stage 2). Both are `chmod +x`. Verified the chain passes end-to-end (`bash .git/hooks/pre-commit` → exit 0).
- **Files modified:** `.git/hooks/pre-commit`, `.git/hooks/pre-commit.large-files` (new — copy of original).
- **Commit:** Hooks are not version-controlled; verbatim content recorded in this SUMMARY (above) for reproducibility per plan output spec.

**2. [Rule 2 — Auto-add critical] Scanner EXCLUDE list expanded beyond plan's single entry**
- **Found during:** Task 2 first scanner run.
- **Issue:** Plan only mentioned `backend/tests/test_dashboard_advanced.py` as a known pre-existing leak. The actual current tree has the same `"<TEST_ADMIN_PASSWORD>"` literal in three additional test files (`test_coa_reconciliation.py`, `test_merit_order.py`, `test_po_batubara.py`), four `test_reports/iteration_*.json` artifacts, four documentation files (`API_REFERENCE.md` and its `frontend/public/docs/` mirror, plus `DEPLOYMENT_GUIDE.md` and its mirror), and `memory/PRD.md`. Without these, the scanner exits 1 and the hook blocks every commit.
- **Fix:** Added each path to the EXCLUDE array with a phase-tagged TODO comment (`Phase 4 TEST-02` for tests/reports, `Phase 3 STAB-03` for docs/PRD) so the debt remains visible. Updated `CREDENTIAL_HYGIENE.md` "Known exemptions" to list each entry with its TODO.
- **Why critical:** Without this, the pre-commit hook would refuse every commit on the current tree, which is broken and would force `--no-verify` bypass — defeating the entire purpose of the gate.
- **Files modified:** `scripts/check_credentials.sh`, `docs/audit/CREDENTIAL_HYGIENE.md`.
- **Commit:** Included in `550cd18`.

### Auth Gates

None — this plan does not interact with running services or authenticated APIs.

## Cleanup status — audit-probe-* synthetic users

The 3 audit-probe-* users inserted by Phase-1 Plan 01-04 (per LOGIN_BUG.md) are NOT cleaned up by this plan. Cleanup is deferred to Plan 02-03 setup, where the regression-test fixture wiring will own the lifecycle of any synthetic test users. Cleanup filter (recorded for the receiving plan): `db.users.deleteMany({email: /^audit-probe-/})`.

## Known Stubs

None. All artifacts are functional and exercised end-to-end.

## Threat Flags

None. No new network endpoints, auth paths, file-access patterns, or schema changes were introduced. The threat model in 02-01-PLAN.md (`<threat_model>`) was fully addressed:

- T-02-01 (test_credentials.md tracked) → mitigated via gitignore + `git rm --cached`.
- T-02-02 (future inline credentials) → mitigated via scanner pattern D + env-var contract.
- T-02-03 (JWT-shaped strings in commits) → mitigated via patterns A and B; negative-path proof verified.
- T-02-04 (Mongo URI with creds) → mitigated via pattern C; existing `.env*` ignore continues to cover live config.
- T-02-05 (pre-existing test_dashboard_advanced.py) → accepted with TODO Phase 4 TEST-02; documented in scanner EXCLUDE and `CREDENTIAL_HYGIENE.md`.
- T-02-06 (developer disables hook) → accepted; documented in `CREDENTIAL_HYGIENE.md` "How to add a new exemption" as policy violation. Server-side / CI-side enforcement is deferred to Phase 4+.

## Self-Check: PASSED

- FOUND: `pltu-tenayan-full-backup/scripts/check_credentials.sh`
- FOUND: `pltu-tenayan-full-backup/docs/audit/CREDENTIAL_HYGIENE.md` (149 lines)
- FOUND: `pltu-tenayan-full-backup/.git/hooks/pre-commit` (chained, executable)
- FOUND: `pltu-tenayan-full-backup/.git/hooks/pre-commit.large-files` (preserved sub-script)
- FOUND: gitignore entry `memory/test_credentials.md` at line 96 of `pltu-tenayan-full-backup/.gitignore`
- FOUND: inner-repo commit `550cd18` (`git -C pltu-tenayan-full-backup log --oneline | grep 550cd18`)
- CONFIRMED: `git -C pltu-tenayan-full-backup ls-files memory/test_credentials.md` returns empty
- CONFIRMED: `pltu-tenayan-full-backup/memory/test_credentials.md` exists on disk (unmodified)
- CONFIRMED: scanner exits 0 (164 files, 16 exemptions); hook exits 0
- CONFIRMED: negative-path proof — JWT-shaped staged file → hook exit=1
