---
phase: 29
title: Frontend Warning & Visual QA
requirements:
  - QA4-02
  - QA4-03
  - QA4-05
status: planned
---

# UI Spec: Frontend Warning & Visual QA

## Experience Contract

The covered pages must remain operational screens, not marketing pages. They should show useful data panels, filters, actions, and state messages without layout drift between desktop and tablet.

## Covered Viewports

- Desktop: 1440 x 1000
- Tablet landscape: 1024 x 768

## Covered Pages And Required Anchors

| Page | URL | Required Surfaces |
|------|-----|-------------------|
| Dashboard | `/dashboard` | Operational dashboard title, stock panel, arrival/realisasi panel, dispute/umpire panel, data-quality action |
| Management Report | `/laporan?tab=management` | Laporan page title, management/report tab content, export action, management summary cards/table |
| Data Quality | `/data-quality` | Data Quality Monitor title, summary surface, export/action control, rule/status content |
| Dispute Monitor | `/dispute-monitor` | Dispute Monitor title, summary counters, table/list surface, note/close action affordance when data exists |
| Settings Runtime | `/settings` | Pengaturan title, Status Operasional runtime panel, refresh action, admin settings sections |

## Visual Failure Conditions

Visual smoke should fail when:

- A covered page renders a blank body or near-empty body text.
- The page is redirected to login after authentication setup.
- Required anchors are missing.
- The document has horizontal overflow beyond the viewport.
- Visible text nodes overlap each other in the same rendered band in a way that indicates obvious collision.

## Copy Rules

- Loading, empty, error, partial-data, and success states use Indonesian copy.
- Empty states explain what is missing and what operator action is available when relevant.
- Technical English is acceptable only for product/module names such as Data Quality Monitor, Runtime, or API labels already used consistently in the app.
