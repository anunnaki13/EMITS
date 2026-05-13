---
phase: 27
plan: 27-01
subsystem: backend-frontend
tags:
  - ai-advisor
  - guardrails
  - trend-context
  - data-quality
requirements-completed:
  - AI3-01
  - AI3-02
  - AI3-03
  - AI3-04
  - AI3-05
completed: 2026-05-13T19:53:00Z
duration: 17 min
---

# Phase 27 Plan 01: AI Advisor v3 Summary

Upgraded the operational advisor so it consumes trend/data-quality context, exposes confidence and limitations, groups recommendations by urgency and owner role, and keeps deterministic fallback reliable with optional LLM memo polish disabled by default.

## Tasks Completed

1. Reworked `backend/services/operational_advisor.py` to add `trend_context`, `data_quality_context`, `confidence`, `limitations`, `recommendation_groups`, and richer guardrails.
2. Added trend/data-quality recommendations for stock forecast risk, arrival trend, quality trend, supplier risk trend, and data-quality follow-up.
3. Added `urgency`, `urgency_label`, `owner_role`, and `category` fields to recommendations while preserving existing IDs, severity, evidence, and source slices.
4. Added optional `ADVISOR_LLM_POLISH=1` memo polish through `get_ai_client()` with deterministic fallback and safe guardrail metadata.
5. Updated management report UI to show advisor confidence, limitations, grouped recommendations, owner roles, evidence, and source slices.
6. Added `backend/tests/test_ai_advisor_v3.py` for advisor context, grouping, default no-LLM behavior, optional fake polish, and fallback on LLM failure.

## Key Files

Created:

- `backend/tests/test_ai_advisor_v3.py`

Modified:

- `backend/services/operational_advisor.py`
- `frontend/src/pages/LaporanPage.js`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `.planning/PROJECT.md`

## Commits

| Commit | Description |
| --- | --- |
| `d95990d` | Planned Phase 27. |
| `869ea02` | Upgraded backend advisor context, grouping, confidence, and LLM polish guardrails. |
| `9bbd7c2` | Added frontend advisor confidence, limitations, grouping, owner, and evidence display. |
| `0131c21` | Added Advisor v3 guardrail tests. |

## Deviations From Plan

- Optional LLM polish is implemented as memo polish only. It does not create or alter recommendations, which keeps source-backed deterministic output authoritative.
- Unit tests for optional LLM polish target the polish helper directly to avoid tying Motor's async client to a test event loop; full advisor payload behavior is covered through the HTTP endpoint.

## Verification

- `python3 -m py_compile backend/services/operational_advisor.py backend/services/management_reports.py backend/tests/test_ai_advisor_v3.py`
- `ops/scripts/pytest_with_local_credentials.sh tests/test_ai_advisor_v3.py tests/test_management_reports.py tests/test_service_boundaries.py -q`
- `cd frontend && npm run build`

Result: backend compile passed, 6 backend tests passed, frontend build passed with pre-existing React hook warnings.

## Next Phase Readiness

Phase 28 can focus on UI/UX polish using the now richer dashboard, report, trend, data-quality, and advisor payloads.

