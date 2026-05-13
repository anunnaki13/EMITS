# Phase 28 Patterns - Operator UI/UX Polish

Date: 2026-05-14

## Frontend Patterns

| Concern | Pattern |
| --- | --- |
| Quick actions | Use compact linked tiles with icon, label, and live metric. |
| State copy | Indonesian operational copy: "Data perlu dicek", "Belum ada data", "Perlu tindak lanjut". |
| Data quality | Show compact caveat and link to `/data-quality` when status is warning/critical. |
| Stable layout | Use responsive grids, min heights, overflow wrapping, and no text overlap. |
| Advisor/report | Keep dense grouped rows; avoid nested decorative cards. |
| Hook cleanup | Convert page fetch functions to `useCallback` only when dependencies are explicit. |

## Verification Patterns

| Area | Pattern |
| --- | --- |
| Build | `cd frontend && npm run build` is the primary UI gate. |
| Hook register | Update `docs/quality/REACT_HOOK_WARNINGS.md` based on actual build output. |
| Backend smoke | Run recently affected backend tests to confirm no payload assumptions changed. |

