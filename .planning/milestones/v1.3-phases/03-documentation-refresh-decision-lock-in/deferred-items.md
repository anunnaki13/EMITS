# Phase 03 Deferred Items

Items discovered during Phase 03 execution that are out of scope for the current
plan but should be tracked.

## From plan 03-02 (2026-05-10)

### Outer-repo `.planning/` credential literals (pre-existing, scanner flag)

When the inner-repo credential scanner (`pltu-tenayan-full-backup/scripts/check_credentials.sh`)
is invoked with cwd at the outer repo root, it scans the outer repo's tracked files and
flags pre-existing credential patterns in `.planning/`:

- `Admin-password-literal` (8 files):
  - `.planning/phases/01-production-audit-onboarding/01-01-SUMMARY.md`
  - `.planning/phases/02-authentication-stabilization/02-01-PLAN.md`
  - `.planning/phases/02-authentication-stabilization/02-01-SUMMARY.md`
  - `.planning/phases/02-authentication-stabilization/02-02-PLAN.md`
  - `.planning/phases/02-authentication-stabilization/02-02-SUMMARY.md`
  - `.planning/phases/02-authentication-stabilization/02-03-PLAN.md`
  - `.planning/phases/02-authentication-stabilization/02-03-SUMMARY.md`
  - `.planning/phases/03-documentation-refresh-decision-lock-in/03-03-PLAN.md`
  - `.planning/phases/03-documentation-refresh-decision-lock-in/03-05-PLAN.md`
- `MongoDB-URI-with-creds` (4 files):
  - `.planning/phases/01-production-audit-onboarding/01-02-PLAN.md`
  - `.planning/phases/01-production-audit-onboarding/VERIFICATION.md`
  - `.planning/phases/02-authentication-stabilization/02-01-SUMMARY.md`
  - `.planning/phases/03-documentation-refresh-decision-lock-in/03-05-PLAN.md`
- `JWT` (1 file):
  - `.planning/phases/02-authentication-stabilization/02-01-PLAN.md`

**Status:** Pre-existing — not introduced by plan 03-02. The inner-repo pre-commit
hook only scans inner-repo tracked files (cwd=`pltu-tenayan-full-backup/`), so these
do not block inner-repo commits. The outer repo has no equivalent pre-commit hook today.

**Why not fixed here:** Out of scope for plan 03-02 (D-11 / D-13 / SS-04 carry-forwards).
These artifacts are planning-history records and should be remediated in a dedicated
sweep, ideally:
- Phase 3 plan 03-04 (Known Issues) could add a hygiene-debt entry pointing here.
- A future Phase 3.x or pre-Phase-4 cleanup plan could redact / replace literals
  with `<REDACTED>` placeholders + cite to `memory/test_credentials.md`, plus install
  a parallel pre-commit hook in the outer repo.

**Recommended remediation pattern:** same as the inner-repo fix applied in plan
03-02 task 1 (LOCAL_SETUP.md section 9): replace literal email/password/Mongo URI
with awk-extraction snippets pointing at the gitignored
`pltu-tenayan-full-backup/memory/test_credentials.md`.
