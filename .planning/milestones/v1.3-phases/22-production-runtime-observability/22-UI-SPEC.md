# Phase 22 UI-SPEC: Production Runtime & Observability

**Phase:** 22 - Production Runtime & Observability
**Date:** 2026-05-13
**Status:** Approved for planning

## UI Surface

Primary surface: admin-only Settings page.

Recommended implementation:

- Add `frontend/src/components/RuntimeHealthPanel.js`.
- Render it near the top of `frontend/src/pages/SettingsPage.js`, before user management and configuration cards.
- Keep `/settings` as the route; do not create a new navigation item unless the page becomes too large during implementation.

## User

Admin/operator owner who is checking whether EMITS is safe to operate after deploy, host restart, nginx edit, or backup event.

## Layout Contract

- Use a compact operational section with a clear title: `Status Operasional`.
- No nested cards. The panel can be one card with internal grid rows/tiles.
- First row: overall status, last generated time, app/build version, refresh button.
- Second row: four stable status tiles:
  - Backend/API
  - MongoDB
  - Backup
  - Smoke Check
- Third row: disk usage and last smoke details if available.
- On desktop: 4 status tiles in a row.
- On tablet: 2 columns.
- On mobile: 1 column with no horizontal overflow.

## Component States

| State | Behavior |
|-------|----------|
| Loading | Skeleton/loader inside fixed-height panel; do not shift page content. |
| Healthy | Emerald badge, concise Indonesian status text. |
| Warning | Amber/slate badge, show reason and suggested action. |
| Critical | Red badge, show reason and "jalankan smoke check / cek runbook" action text. |
| Unknown | Slate badge, explain that status has not been recorded yet. |
| Error fetching status | Keep panel visible with retry button and Indonesian error copy. |

## Interaction Contract

- Refresh button refetches `/api/admin/runtime/status`.
- No destructive actions in this panel.
- No raw paths/secrets shown except safe labels such as static root presence and DB name if already non-secret.
- If last smoke report exists, show pass/fail counts and timestamp. Detailed check list may be collapsible or a compact table.

## Visual Style

- Match current dark operational UI.
- Use lucide icons if adding icons:
  - `Server` or `Activity` for backend
  - `Database` for MongoDB
  - `DatabaseBackup` for backup
  - `Radar` or `CheckCircle` for smoke
  - `RefreshCw` for refresh
- Avoid big hero layouts, decorative gradients, or explanatory marketing copy.
- Keep cards radius consistent with existing app style and avoid rounded pill overload.

## Content Copy

Use Indonesian operational copy:

- Overall healthy: `Sistem operasional`
- Warning: `Perlu perhatian`
- Critical: `Perlu tindakan`
- Unknown: `Belum ada data`
- Refresh: `Refresh status`
- Smoke detail: `Smoke terakhir`
- Backup detail: `Backup terakhir`

## Accessibility and Responsiveness

- Buttons must have text plus icon or accessible label.
- Status cannot rely on color only; include visible text.
- Text must wrap inside tiles and not overlap at common tablet widths.
- Numeric values should use Indonesian locale formatting where applicable.

## Verification

- `npm run build` passes.
- Manual visual check at desktop and tablet widths if a browser is available.
- Runtime panel does not display secret-like strings: Mongo URL, JWT secret, API keys, tokens, or passwords.

---
*UI contract generated inline because Phase 22 contains admin-facing runtime health UI.*
