# Phase 27 Research - AI Advisor v3

Date: 2026-05-14
Status: complete

## Implementation Findings

### Existing Advisor Shape

`backend/services/operational_advisor.py` already returns:

- `recommendations`
- `memo_draft`
- `guardrails`
- `source_slices`
- `source_counts`
- `data_health`

This is a good base. Phase 27 should add fields, not replace the current contract.

### Trend And Data Quality Inputs

Management report now exposes:

- `trend_analytics.metrics`
- `trend_analytics.supplier_trends`
- `trend_analytics.stock_forecast`
- `trend_analytics.confidence`
- `trend_analytics.caveats`
- `data_quality.status`
- `data_quality.counts`
- `data_quality.caveats`

Advisor can summarize these deterministically without extra queries.

### Optional LLM Polish

Recommended default:

- `ADVISOR_LLM_POLISH` absent or not `1`: deterministic memo only.
- `ADVISOR_LLM_POLISH=1`: call `get_ai_client()` with a bounded prompt containing only generated deterministic memo, recommendations, source slices, limitations, and guardrails.
- Any LLM error: return deterministic memo and record fallback reason.

Never make LLM output the source of truth. It may only polish the memo wording.

### Recommendation Grouping

Add fields on each recommendation:

- `urgency`: `critical`, `warning`, `watch`, `info`
- `owner_role`: likely owner such as `operator`, `coal_analyst`, `logistics`, `management`, `admin`
- `category`: `stock`, `arrivals`, `quality`, `dispute`, `supplier`, `data_quality`, `trend`

Add top-level `recommendation_groups` grouped by urgency with counts and item IDs.

### Confidence And Limitations

Top-level `confidence` should combine:

- report data health
- trend analytics confidence/sparse status
- data-quality status

Top-level `limitations` should list why recommendations are limited:

- empty report data
- sparse trend history
- critical/warning data quality
- missing usage/COA/arrival data
- LLM polish disabled or failed

### Frontend Shape

Existing `AI Advisor` card can show:

- confidence badge
- grouped recommendations with owner role
- limitations list
- memo draft as-is

No large redesign needed before Phase 28.

## Risks And Mitigations

- LLM accidentally used during tests.
  - Default polish off; add tests that monkeypatch client factory to fail if called.

- Unsupported claims.
  - Build memo/recommendations only from report fields and source slices; LLM prompt tells it not to add facts.

- UI breakage from new fields.
  - Add fields additively and keep existing `recommendations`/`memo_draft`.

