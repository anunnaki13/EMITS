# Excel Parser Verification Log

**Plan:** 06-03 (OPS-03)
**Date:** 2026-05-11
**Verified by:** GSD executor (claude-sonnet-4-6)

## Scope

Verification of `parse_coa_excel()` in `services/coa_reconciliation.py` against 3
sanitized production-proxy fixtures (Loading / Unloading / Lab_Internal), each capped
at 50 data rows with PII scrubbed per RESEARCH Focus 8 sanitization rules.

## Parser Discrepancies Found

**None.** The parser correctly handles all 3 source types without modification.

## Verification Results

| Mode | Fixture | Records Returned | Anchor Shp 555 | DS_MT 5626.021 | Quality Fields |
|------|---------|-----------------|----------------|----------------|----------------|
| loading | loading_sample.xlsx | 50 | FOUND | 5626.021 | Sparse (row 2 null; row 3 shp556 gcv_arb=4211.0) |
| unloading | unloading_sample.xlsx | 50 | FOUND | 5626.021 | Present (gcv_arb=4006.0, ts_arb=0.23) |
| internal | lab_internal_sample.xlsx | 50 | FOUND | 5626.021 | All None in first 50 rows (data starts at shp~725) |

## Notes

**Loading / Lab_Internal quality sparsity:** The first data row (Shipment 555 / Aug 2020)
has no COA quality values in either the Loading or Lab_Internal files. This is a production
data gap, NOT a parser bug. The parser correctly returns `None` for these fields via
`safe_float()` on NaN pandas values. Lab_Internal quality data begins at Shipment ~725
(row ~292 in the full file), which is outside the 50-row fixture window.

**Periode formula cells:** The Periode column uses `=EOMONTH(G2,-1)+1` Excel formulas.
openpyxl does not evaluate formulas; pandas reads these as `None`. The parser's `safe_str()`
returns `""` for the Periode field — this is expected and consistent with the merge logic
which uses `completed_unloading` for sorting, not Periode.

**Surveyor in Unloading:** `PT GEOSERVICES` is retained as an organizational identifier
per D-13 sanitization rules (not personal PII). Assertion in test_coa_regression_unloading
verifies this value is present and unchanged.

**Column name normalization:** `clean_column_name()` (line 40-44) strips `\n` from headers
before row.get() lookups. The dual-key fallback pattern in parse_coa_excel (e.g.
`row.get("GCV (Kcal/Kg) ARB", row.get("GCV (Kcal/Kg)\nARB"))`) is correctly handled
because after normalization both forms collapse to the same key. Verified: pandas retains
the raw `\n` in column names; `clean_column_name()` normalizes them to spaces before lookup.

## Pytest Output

```
3 passed, 5 skipped in 4.25s
```

Skipped: Phase-4 live-server tests (require TEST_ADMIN_EMAIL env var + running backend).
