# Phase 27 Context - AI Advisor v3

Date: 2026-05-14
Status: planning
Source: user approved continuing; context derived from roadmap, requirements, current advisor service, Phase 25 data-quality caveats, and Phase 26 trend analytics.

## Phase Goal

The operational advisor should explain trend and data-quality context, expose confidence and limitations, group recommendations by urgency and suggested owner, and keep deterministic fallback reliable even if optional LLM polish is disabled or unavailable.

## Requirements Covered

- `AI3-01`: Advisor can summarize trend and data-quality findings using visible source slices.
- `AI3-02`: Advisor can optionally use a configured LLM for narrative polish while deterministic fallback remains available.
- `AI3-03`: Advisor exposes confidence and limitations when data quality or historical coverage is weak.
- `AI3-04`: Advisor recommendations are grouped by urgency and suggested owner or operating role.
- `AI3-05`: Tests prevent unsupported claims and prevent accidental live LLM calls in normal test runs.

## Current Codebase Context

Existing advisor:

- `backend/services/operational_advisor.py` builds deterministic recommendations and `memo_draft`.
- `backend/routers/ai_intelligence.py` exposes `GET /api/ai/advisor/operational`.
- `frontend/src/pages/LaporanPage.js` shows advisor recommendations and memo in the management report tab.

Available context:

- `build_management_report(...)` now includes `data_quality`.
- `build_management_report(...)` now includes `trend_analytics`.
- `backend/app/ai/client.py` provides `get_ai_client()` with `AI_FAKE=1` test stub support.
- `backend/app/ai/openrouter_client.py` maps provider failures to safe Indonesian errors.

## Compatibility Boundary

In scope:

- Add trend/data-quality context to advisor payload.
- Add confidence, limitations, recommendation grouping, and owner/role fields.
- Optional LLM polish behind an explicit env flag.
- Frontend management report should display confidence/limitations/group/owner without breaking existing recommendation rendering.
- Tests must prove default advisor path does not call live LLM.

Out of scope:

- Replacing provider stack or adding multi-provider routing.
- Letting the LLM invent claims not present in source slices.
- Autonomous actions.
- Long chat conversation changes outside the operational advisor endpoint.

## Canonical References

- `.planning/REQUIREMENTS.md` - AI3 requirements.
- `.planning/ROADMAP.md` - Phase 27 success criteria.
- `.planning/phases/25-data-quality-monitor/25-01-SUMMARY.md` - data-quality payloads and caveats.
- `.planning/phases/26-trend-analytics-forecasting/26-01-SUMMARY.md` - trend analytics payloads and caveats.
- `backend/services/operational_advisor.py` - advisor implementation.
- `backend/services/management_reports.py` - report payload consumed by advisor.
- `backend/app/ai/client.py` - optional AI client factory and fake-client test guard.
- `frontend/src/pages/LaporanPage.js` - visible advisor UI.

