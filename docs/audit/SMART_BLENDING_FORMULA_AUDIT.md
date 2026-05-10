# Smart Blending AI Formula Audit (Phase-3 plan 03-05)

**Verified:** 2026-05-10
**Source of truth:** `.planning/intel/constraints.md` → CONS-blending-formula,
CONS-blending-input-ranges, CONS-blending-constraint-validation, CONS-blending-ai-output,
CONS-blending-tolerance.
**File audited:** `frontend/public/docs/Smart_Blending_AI_Formula.md`.

## Outcome

**NO DRIFT** — The formula doc matches all CONS-blending-* clauses exactly.
No corrections were required.

## Clause-by-clause comparison

| CONS clause | Doc claim | Match? | Notes |
|-------------|-----------|--------|-------|
| Linear weighted-average blend across GCV/Ash/Sulphur/TM/IM/VM/FC (`Hasil_Parameter = Σ (Parameter_i × Persentase_i); Σ Persentase_i = 1.0`) | Section 2.1: "Formula dasar blending menggunakan prinsip rata-rata tertimbang (weighted average): `Hasil_Parameter = Σ (Parameter_i × Persentase_i)` ... `Σ Persentase_i = 1.0`" | ✓ | Exact match including the formula string and the constraint `Σ = 1.0` |
| Applied per parameter: GCV_blend, Ash_blend, Sulphur_blend, TM_blend, IM_blend, VM_blend, FC_blend | Section 2.2: table rows for GCV Campuran, Abu Campuran, Sulphur Campuran, Total Moisture, Inherent Moisture, Volatile Matter, Fixed Carbon | ✓ | All 7 parameters explicitly listed |
| `Tonase_i = Total_Kuantitas × Persentase_i` | Section 2.3: `Tonase_i = Total_Kuantitas × Persentase_i` | ✓ | Exact match |
| GCV_blend ≥ Target_GCV | Section 7.2: `GCV_hasil ≥ Target_GCV` | ✓ | Correct inequality direction |
| Ash_blend ≤ Max_Ash | Section 7.2: `Ash_hasil ≤ Max_Ash` | ✓ | Correct inequality direction |
| Sulphur_blend ≤ Max_Sulphur | Section 7.2: `Sulphur_hasil ≤ Max_Sulphur` | ✓ | Correct inequality direction |
| TM_blend ≤ Max_Total_Moisture | Section 7.2: `TM_hasil ≤ Max_Total_Moisture` | ✓ | Correct inequality direction |
| IM_blend ≤ Max_Inherent_Moisture | Section 7.2: `IM_hasil ≤ Max_Inherent_Moisture` | ✓ | Correct inequality direction |
| VM_blend ≥ Min_Volatile_Matter | Section 7.2: `VM_hasil ≥ Min_Volatile_Matter` | ✓ | Correct inequality direction |
| FC_blend ≥ Min_Fixed_Carbon | Section 7.2: `FC_hasil ≥ Min_Fixed_Carbon` | ✓ | Correct inequality direction |
| ±5% prediction tolerance | Section 10.2 point 4: "Nilai prediksi memiliki toleransi ±5% dari hasil aktual" | ✓ | Exact match |
| Output JSON shape locked: `{ recommendation: [], predicted_quality: {}, meets_target: bool, reasoning: str, cost_warning?: str }` | Section 9.1: JSON example with `recommendation`, `predicted_quality`, `meets_target`, `reasoning`, `cost_warning` | ✓ | All top-level fields present |
| recommendation[] item: supplier, source, type, percentage, tonnage, gcv, ash, sulphur, total_moisture, inherent_moisture, volatile_matter, fixed_carbon | Section 9.1: example recommendation item with all listed fields | ✓ | All fields present in example |
| predicted_quality: gcv, ash, sulphur, total_moisture, inherent_moisture, volatile_matter, fixed_carbon | Section 9.1: `predicted_quality` block with gcv, ash, sulphur, total_moisture, inherent_moisture, volatile_matter, fixed_carbon | ✓ | All fields match |
| Parameter ranges — Target GCV: 3700-4700 kcal/kg | Section 3.1: "Target GCV ... 3700 - 4700" | ✓ | Exact match |
| Max Ash: 3.3-6.0 % (ARB) | Section 3.1: "Max Ash ... 3.3 - 6.0" | ✓ | Exact match |
| Max Sulphur: 0.13-2.2 % (ARB) | Section 3.1: "Max Sulphur ... 0.13 - 2.2" | ✓ | Exact match |
| Max Total Moisture: 25-40 % (ARB), default 35.0 | Section 3.1: "Max Total Moisture ... 25 - 40 ... 35.0" | ✓ | Exact match |
| Max Inherent Moisture: 13.8-25 % (ADB), default 18.0 | Section 3.1: "Max Inherent Moisture ... 13.8 - 25 ... 18.0" | ✓ | Exact match |
| Min Volatile Matter: 27.9-40 % (ARB), default 35.0 | Section 3.1: "Min Volatile Matter ... 27.9 - 40 ... 35.0" | ✓ | Exact match |
| Min Fixed Carbon: 23-41 % (ARB), default 25.0 | Section 3.1: "Min Fixed Carbon ... 23 - 41 ... 25.0" | ✓ | Exact match |
| Data sources: vessels (max 50), barges (max 50), trucking (max 50) — last 6 months | Section 6.1: table with Vessel/Barge/Trucking, all Max Records=50; Section 1: "6 bulan terakhir" | ✓ | Exact match |
| Smart Stock data and Merit Order pricing included | Section 6.3: Smart Stock and Merit Order listed as supporting data | ✓ | Both present |
| Coal rank: LRC 3000-4500, MRC 4500-6000, HRC >6000 | Section 4.1 table: LRC 3000-4500, MRC 4500-6000, HRC >6000 | ✓ | Exact match |
| Typical mix for 4000-4200 target: 60-70% LRC + 30-40% MRC | Section 4.2: "60-70% LRC + 30-40% MRC untuk target GCV 4000-4200 kcal/kg" | ✓ | Exact match |
| Measurement basis: AR/ARB, ADB, DB, DAF/DAFB; conversions documented | Section 5.1-5.2: all four bases defined; conversion formulas for GCV(ADB) and GCV(DB) | ✓ | Exact match |
| Reference standards: ASTM D388, ISO 1928, ISO 11722, ISO 1171 | Section 10.1: all four standards listed | ✓ | Exact match |

## Corrections applied

None — NO DRIFT outcome. The formula document required no changes to bring it
into alignment with the CONS-blending-* constraints. Only the Phase-3 verification
stamp was appended to the file (additive only; no content modifications).

## Operational caveat

The formula is correct and locked. Operational availability of Smart Blending
AI is degraded today (LLM key budget — see Known Issues entry "Smart Blending
AI" in `documentation.md#known-issues` + REQUIREMENTS OPS-01). Code path matches
formula; budget restoration in Phase 6 unblocks live recommendations.

## Cross-references

- `.planning/intel/constraints.md` → CONS-blending-formula, CONS-blending-input-ranges,
  CONS-blending-constraint-validation, CONS-blending-ai-output, CONS-blending-tolerance,
  CONS-blending-classification, CONS-blending-data-sources, CONS-blending-measurement-basis
- `pltu-tenayan-full-backup/frontend/public/docs/Smart_Blending_AI_Formula.md` (the audited doc)
- `pltu-tenayan-full-backup/documentation.md` §Known Issues entry "Smart Blending AI"
