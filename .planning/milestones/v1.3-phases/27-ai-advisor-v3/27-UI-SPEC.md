# Phase 27 UI Spec - AI Advisor v3

Date: 2026-05-14
Status: ready

## Surface

Existing management report tab in `frontend/src/pages/LaporanPage.js`.

## Layout Contract

Within the existing AI Advisor card:

- Header includes title and confidence badge.
- Show limitations/caveats if present.
- Recommendations are grouped by urgency.
- Each recommendation shows:
  - title
  - urgency/severity badge
  - owner role
  - recommendation text
  - evidence
  - source slice
- Memo remains visible in the existing memo block.

## States

High confidence:

- Show concise confidence badge.

Low/medium confidence:

- Show amber/red limitation callout with Indonesian explanation.

No recommendation:

- Keep deterministic "monitor normal" recommendation if report has usable data.
- If report is empty, show limitations and bounded memo.

Optional LLM polish disabled/failed:

- No UI error; guardrail/fallback metadata can be shown as small text.

## Visual Rules

- Keep dense operational layout.
- No decorative hero.
- No nested cards for individual recommendation groups; use bordered rows/panels.
- Long evidence and limitation text wraps.
- Existing export/menu controls remain unchanged.

