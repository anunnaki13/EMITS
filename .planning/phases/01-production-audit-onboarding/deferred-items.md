# Deferred Items — Phase 1

Out-of-scope discoveries logged during plan execution. None of these block plan completion; they are tracked here for the next planning round to address.

## From plan 01-04 (2026-05-10)

### Stale ROADMAP / REQUIREMENTS checkboxes for plans 01-01 and 01-02

**Found during:** plan 01-04 execution while updating outer-repo metadata.

**Issue:** SUMMARY files exist on disk for plans 01-01 (ENDPOINT_AUDIT.md) and 01-02 (DATA_AUDIT.md), confirming those plans completed during earlier sessions. However:

- `.planning/ROADMAP.md` lines 36–37 still show `- [ ]` (unchecked) for 01-01-PLAN.md and 01-02-PLAN.md.
- `.planning/REQUIREMENTS.md` shows AUDIT-01 and AUDIT-02 as "Pending" in the traceability table (lines 114–115) and unchecked in the AUDIT requirements list (lines 12–13).

**Why deferred:** Plan 01-04 only owns AUDIT-04 / 01-04 checkboxes. Flipping AUDIT-01 / AUDIT-02 / 01-01 / 01-02 checkboxes is out of scope for this plan per the executor's SCOPE BOUNDARY rule (only fix what current task's changes directly cause). Those flips should be done by a quick plan-state-sync pass at the start of Phase 2 setup, after re-reading the 01-01 and 01-02 SUMMARY files to confirm acceptance criteria were met.

**Recommendation:** Phase 2 kickoff should run a single sync step:

```bash
# After confirming 01-01-SUMMARY.md and 01-02-SUMMARY.md acceptance criteria look good:
# 1. Edit ROADMAP.md: flip 01-01-PLAN.md and 01-02-PLAN.md checkboxes to [x].
# 2. Edit REQUIREMENTS.md: flip AUDIT-01 and AUDIT-02 to [x] and update traceability table to "Complete".
# 3. Edit ROADMAP.md Phase 1 line: flip phase-level checkbox to [x] now that all four plans are confirmed done.
```

### CONS-auth-header divergence: 422 vs 400 on validation

**Found during:** Path B step 3 (POST `/api/auth/login` with malformed body).

**Issue:** Backend returns HTTP 422 (FastAPI/Pydantic default) but CONS-auth-header in PROJECT.md specifies 400 for validation errors. Documented in LOGIN_BUG.md "Path B → Divergence".

**Why deferred:** Phase 1 is read-only. The fix (custom RequestValidationError handler vs spec update) belongs in Phase 2 (AUTHFIX-02) or Phase 3 (DOCS-02 spec alignment).

### email-validator rejects RFC 6761 reserved TLDs

**Found during:** Path C round 1 (synthetic register emails using `.invalid` TLD).

**Issue:** Pydantic's `email-validator` rejects `.invalid`, `.test`, `.local`, `.example` with 422 ("special-use or reserved name"). The plan's documented safety choice (`.invalid` per RFC 6761) is incompatible with the live validator.

**Why deferred:** Phase 2 regression test fixtures must avoid these TLDs OR override `email-validator`'s reserved-TLD check. Decision belongs to Phase 2 (AUTHFIX-04 regression test setup).

### Three audit-probe-* synthetic users in live `users` collection

**Found during:** Path C round 2 (successful register probes against synthetic non-reserved domain).

**Issue:** Three `audit-probe-*@audit-probes-2026.com` users were inserted into the live MongoDB `users` collection during the register repro. Listed in LOGIN_BUG.md "Path C → Side-effect note" and `.work/register-backend.txt` cleanup-note row.

**Why deferred:** Phase 2 may use them as regression-test fixtures (already-registered users for login flow) or Phase 5 may clean them up via:

```js
db.users.deleteMany({ email: /^audit-probe-/ })
```
