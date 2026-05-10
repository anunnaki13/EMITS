# Excel Header Variant Notes

**Phase 4 synthetic fixtures use plain (non-newline) headers only.**

The server.py parsers accept both multi-line header variants (e.g., `"GCV (Kcal/Kg)\nARB"`) and plain variants (`"GCV (Kcal/Kg) ARB"`) via fallback `row.get()` calls. The biomassa parser normalizes all headers with `df.columns.str.replace('\n', ' ').str.strip()` before reading.

Phase 4 fixtures (`vessel_minimal.xlsx`, `barge_minimal.xlsx`, `trucking_minimal.xlsx`, `biomassa_minimal.xlsx`) use the plain single-line variants exclusively to avoid multi-line cell encoding complexity in openpyxl.

## Header Variant Edge Cases — DEFERRED to Phase 6 OPS-02

The following header-variant edge cases are NOT covered by Phase 4 fixtures:

1. **Multi-line header cells** — production xlsx files may use `"GCV (Kcal/Kg)\nARB"` (with embedded newline) as the cell content. The server.py fallback handles this, but the parser test here uses only plain variants.

2. **Column ordering** — the real `total penerimaan.xlsx` (Loading.xlsx, Unloading.xlsx, Lab_Internal.xlsx) may have columns in a different order than the Phase 4 synthetic fixtures. All parsers use `row.get("Header Name")` which is order-independent.

3. **Column casing variants** — production samples have been observed with minor casing differences (e.g., "GCV (Kcal/kg) ARB" vs "GCV (Kcal/Kg) ARB"). Not tested here.

4. **Missing optional columns** — some fields are optional (`safe_float` returns None). Phase 4 fixtures include all known columns.

**Action required in Phase 6 OPS-02:** Verify parsers against the real `total penerimaan.xlsx` sample (tracked as Phase 6 OPS-02 `EXCEL_PARSER_VERIFY` task). Use the real sample to exercise the multi-line header path and confirm numerical totals match expectations.

See: `pltu-tenayan-full-backup/docs/audit/API_REFERENCE_SPOTCHECK.md` for endpoints currently marked `verified: schema-only` that Phase 6 will promote to `verified: data`.
