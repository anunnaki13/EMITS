# Phase 29 Context: Frontend Warning & Visual QA

**Date:** 2026-05-14
**Milestone:** v1.4 Production QA & Cleanup
**Phase:** 29 - Frontend Warning & Visual QA
**Requirements:** QA4-01, QA4-02, QA4-03, QA4-04, QA4-05

## Goal

Remove or strictly account for remaining frontend warning debt and add repeatable browser visual smoke coverage for the operator/admin pages that carry release risk.

## User Intent

The application is now used as an operations dashboard for PLTU Tenayan fuel work. The main dashboard should remain focused on:

- Monitoring stock batubara.
- Monitoring jadwal dan realisasi kedatangan bahan bakar.
- Monitoring dispute/umpire batubara.

Phase 29 does not redesign those flows again. It hardens the current frontend so future dashboard/report/settings work has warning and visual QA gates.

## Covered Surfaces

Visual smoke coverage must include:

- Dashboard: `/dashboard`
- Management report: `/laporan?tab=management`
- Data Quality Monitor: `/data-quality`
- Dispute Monitor: `/dispute-monitor`
- Settings runtime status: `/settings`

## Constraints

- Do not commit local secrets or `.env` contents.
- Preserve existing page behavior while normalizing React hook dependencies.
- Avoid broad UI redesign in this phase; changes should be QA infrastructure and warning cleanup.
- Browser smoke may require local credentials or a stored token at runtime. The test must fail clearly when configured services are broken and skip clearly when credentials are not provided.
- Existing dirty files outside this phase are intentionally local and must not be reverted.

## Definition Of Done

- Remaining React hook warnings are either removed or documented with owner/rationale.
- A build warning checker compares actual hook warnings against `docs/quality/REACT_HOOK_WARNINGS.md`.
- Browser smoke tests exercise the five covered surfaces on desktop and tablet viewport profiles.
- Smoke checks detect blank content, missing primary UI anchors, horizontal overflow, and obvious text collisions.
- Covered state copy remains Indonesian and readable.
