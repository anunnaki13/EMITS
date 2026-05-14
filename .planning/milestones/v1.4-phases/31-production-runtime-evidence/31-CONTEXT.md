# Phase 31 Context: Production Runtime Evidence

**Date:** 2026-05-14
**Milestone:** v1.4 Production QA & Cleanup
**Phase:** 31 - Production Runtime Evidence
**Requirements:** OPS4-01, OPS4-02, OPS4-03, OPS4-04, OPS4-05

## Goal

Make production runtime verification auditable instead of informal: operators should be able to run one runtime status command on the VPS, retain the resulting evidence artifact, record smoke status through the admin API, and see deployed build metadata in the admin runtime panel.

## Current Situation

- `ops/scripts/runtime_status.sh` already checks backend health, frontend reachability, systemd, nginx, disk, backups, and delegates to `ops/scripts/smoke_check.py`.
- `ops/scripts/smoke_check.py` already writes JSON smoke evidence and can post to `/api/admin/runtime/smoke-report` when admin credentials are present.
- `/api/admin/runtime/status` already returns allowlisted runtime status, version metadata from backend environment, backup health, disk, frontend presence, and latest smoke summary.
- `frontend/src/components/RuntimeHealthPanel.js` already shows runtime health and latest smoke status, but version/build metadata is still coarse and not explicit for both backend and static frontend.
- `docs/operations/PRODUCTION_RUNBOOK.md` documents deploy/runtime status paths, but v1.4 needs a clearer release gate, expected artifacts, fallback/manual gate, and evidence retention rules.

## Constraints

- Do not commit secrets, tokens, admin credentials, or production `.env` values.
- Treat live VPS execution as a manual gate if this development session cannot access the real production host safely.
- Keep runtime status output allowlisted and secret-free.
- Prefer additive script/API/UI changes over replacing the existing Phase 22 runtime surface.
- Keep generated evidence under ignored runtime/log paths, not committed repository files.

## Definition Of Done

- Runtime status command produces a durable report artifact path in addition to smoke JSON evidence.
- Smoke check can still record status through the admin API and the latest result remains visible in Settings runtime health.
- Admin runtime health displays backend and static frontend build/release metadata clearly enough to trace deployed SHA/tag.
- Production runbook has a v1.4 release gate with artifact paths, fallback steps, evidence retention, and manual-gate wording.
- Phase 31 validation records which checks ran locally and which production-only check remains manual until executed on the real VPS.
