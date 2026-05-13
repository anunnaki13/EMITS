# Phase 8 Context — Polish & Operational Dashboard

Created: 2026-05-11

## Goal

Ship the PRD P3 polish backlog while prioritizing the owner's newest product direction: the Dashboard must become an operational monitoring surface, not a generic chart page.

## User Direction

The dashboard must be reorganized around the main things operators need to see:

1. Monitoring stock batubara.
2. Monitoring jadwal vs realisasi kedatangan bahan bakar.
3. Monitoring dispute / umpire batubara.

This is more important than keeping the current dashboard's arbitrary chart order.

## Constraints

- Preserve existing `/api/dashboard/stats` and `/api/dashboard/advanced` contracts unless tests are intentionally updated.
- Prefer additive backend endpoints if changing dashboard shape would disrupt existing tests.
- Keep Phase 8 changes production-shaped but focused.
- Continue protecting live data: tests use `MONGO_TEST_DB_NAME`; destructive operations require explicit admin flow.
- Do not commit secrets; `backend/.env` remains local-only.

## Completed Upstream Work

- Phase 6 restored OpenRouter / Smart Blending and AI chat.
- Phase 7 completed backend modularization for auth, COA, smart-stock/sumber-pemakaian, and added rekap date/supplier filters.
- Frontend dev server is running on port 3013.
- Backend is running on port 8013 with Phase-7 code.

## Phase 8 Plan Shape

1. Operational dashboard redesign.
2. Theme toggle.
3. Backup/restore.
4. Audit trail.

Dashboard work is first because the user explicitly called out current dashboard UX as not useful enough.
