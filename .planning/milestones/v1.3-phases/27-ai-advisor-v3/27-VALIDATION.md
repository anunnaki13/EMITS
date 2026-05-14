---
phase: 27
slug: ai-advisor-v3
status: archived
nyquist_status: legacy_exception
nyquist_exception: "Archived before v1.4 metadata standard; validation evidence preserved in this file and phase verification."
metadata_reviewed: "2026-05-14"
---

# Phase 27 Validation - AI Advisor v3

Date: 2026-05-14
Status: planned

## Required Verification

```bash
python3 -m py_compile backend/services/operational_advisor.py backend/services/management_reports.py
```

```bash
ops/scripts/pytest_with_local_credentials.sh tests/test_ai_advisor_v3.py tests/test_management_reports.py tests/test_service_boundaries.py -q
```

```bash
cd frontend && npm run build
```

## Functional Validation

- Verify advisor payload includes trend context, data-quality context, confidence, limitations, recommendation groups, owner roles, and guardrails.
- Verify default advisor path does not call live LLM.
- Verify optional polish uses an injected fake client when explicitly enabled.
- Verify LLM polish failure falls back to deterministic memo.
- Verify frontend renders confidence, limitations, grouped recommendations, owner roles, evidence, and source slices.

## Residual Risk To Watch

- Optional LLM output is polish only and must not become a source of unsupported facts.
- Existing frontend hook warnings may remain until Phase 28.
