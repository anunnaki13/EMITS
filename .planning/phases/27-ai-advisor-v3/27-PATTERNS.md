# Phase 27 Patterns - AI Advisor v3

Date: 2026-05-14

## Backend Patterns

| Concern | Pattern |
| --- | --- |
| Deterministic default | Advisor must work without live LLM calls by default. |
| Optional LLM | Gate behind `ADVISOR_LLM_POLISH=1`; catch failures and keep deterministic memo. |
| Source grounding | Recommendations cite existing source slice names; payload includes `source_context`. |
| Trend context | Consume `report.trend_analytics`; do not recompute trends in advisor. |
| Data quality | Consume `report.data_quality`; include caveats and limitations. |
| Recommendation fields | Add `urgency`, `owner_role`, `category`; preserve existing keys. |
| Grouping | Return `recommendation_groups` by urgency for UI/export consumers. |
| Guardrails | Return `llm_required`, `llm_enabled`, `llm_used`, `fallback_reason`, and `unsupported_claims_refused`. |

## Frontend Patterns

| Concern | Pattern |
| --- | --- |
| Advisor card | Keep existing card; add confidence badge and limitations below header. |
| Grouping | Show recommendations grouped by urgency using existing compact badges. |
| Owner | Show owner role as a small secondary label on each recommendation. |
| Copy | Indonesian labels: "Confidence", "Batasan", "Owner", "Urgensi". |
| Layout | Avoid a new page or hero; keep management report workflow dense. |

## Testing Patterns

| Test Area | Pattern |
| --- | --- |
| No live LLM | Monkeypatch advisor client factory to fail, with polish disabled. |
| Optional polish | Enable env flag and inject fake client; assert `llm_used` and deterministic fallback context remains. |
| Grounding | Assert recommendations carry `source_slice`, `category`, `owner_role`, and evidence. |
| Limitations | Seed sparse/quality-warning records and assert confidence/limitations expose the risk. |

