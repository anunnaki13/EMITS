# Phase 25 UI Spec - Data Quality Monitor

Date: 2026-05-14
Status: ready

## Surface

New route: `/data-quality`

Audience:

- Admin
- Operator

Primary job:

Help operators/admins quickly see whether current operational data is safe enough to use for dashboard, report, import, and management decisions.

## Layout Contract

First viewport:

- Header row:
  - title: "Data Quality Monitor"
  - subtitle: latest generated timestamp and active filter scope
  - actions: refresh/recompute, export CSV
- Summary strip:
  - Critical count
  - Warning count
  - Healthy/info count
  - Total checked records or total issues
- Filter row:
  - module select
  - severity select
  - reset filter button
- Issue list/table:
  - severity badge
  - module
  - issue type
  - source label/record
  - message
  - suggested fix

## States

Loading:

- skeleton or spinner inside the data surface.

Healthy/empty:

- Indonesian copy: "Tidak ada issue kualitas data pada filter ini."
- Keep summary cards visible with zero counts.

Partial:

- If report has source caveats, show an amber callout above issues.

Error:

- Indonesian error callout with retry action.

## Visual Rules

- Use compact, operational density.
- Avoid hero sections and decorative backgrounds.
- Keep cards at existing radius and border style.
- Use lucide icons for refresh/export/warning/check actions.
- Text must wrap inside table/list cells on desktop and mobile.
- On mobile/tablet, issue table may become stacked rows, but severity and source must remain visible.

## Acceptance Checks

- `/data-quality` is reachable for admin/operator and blocked for viewer.
- Summary cards, filters, refresh, export, and issue list render without overlapping text.
- Empty, loading, error, and critical/warning states have Indonesian copy.
- Existing dashboard/report pages can display data-quality caveats without layout shift.
