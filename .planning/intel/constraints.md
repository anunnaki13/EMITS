# Constraints (SPEC Intel)

Authoritative technical contracts extracted from SPEC-class documents. Higher precedence than PRD/DOC content.

---

## CONS-api-base
- title: API Base URL and Path Convention
- source: pltu-tenayan-full-backup/API_REFERENCE.md
- type: api-contract
- statement:
  - Frontend resolves base URL via `REACT_APP_BACKEND_URL`.
  - All backend HTTP routes are prefixed `/api`.
  - Production example: `https://your-domain.com/api`.

## CONS-auth-header
- title: Authentication Header Contract
- source: pltu-tenayan-full-backup/API_REFERENCE.md
- type: api-contract
- statement:
  - All endpoints except `/api/auth/register`, `/api/auth/login`, `/api/`, `/api/health` require `Authorization: Bearer <JWT>`.
  - Roles: `admin`, `operator`, `viewer`.
  - HTTP error codes: 400 validation, 401 invalid/expired token, 403 role denied, 404 not found, 500 internal/AI integration error.

## CONS-pagination-shape
- title: Paginated List Response Shape
- source: pltu-tenayan-full-backup/API_REFERENCE.md
- type: api-contract
- statement:
  - Response: `{ "items": [], "total": 0, "page": 1, "page_size": 50, "total_pages": 0 }`
  - Frontend MUST read `response.data.items`; never assume the response is a bare array.
  - Default page_size 50; operational list endpoints typically cap at 500; smart-stock list caps at 50000.

## CONS-vessel-endpoint
- title: Vessel CRUD + Upload Endpoints
- source: pltu-tenayan-full-backup/API_REFERENCE.md
- type: api-contract
- statement:
  - GET /api/vessels (search, page, page_size; search fields: shipment_code, suppliers, name_of_vessel)
  - GET /api/vessels/{id}
  - POST /api/vessels (admin/operator; body VesselTNYCreate)
  - PUT /api/vessels/{id}
  - DELETE /api/vessels/{id} (admin)
  - DELETE /api/vessels (admin; delete all)
  - POST /api/upload/vessel (admin/operator; multipart/form-data)
  - VesselTNYCreate fields: periode_ta, periode_realisasi, shipment_code, voyage_code, suppliers, voyage, name_of_vessel, coal_from, time_arrival, completed_unloading, bl_mt, ds_mt, gcv_arb, tm_arb, ash_arb, ts_arb, plus quality derivatives.

## CONS-barge-trucking-biomassa-endpoints
- title: Barge / Trucking / Biomassa CRUD + Upload Endpoints
- source: pltu-tenayan-full-backup/API_REFERENCE.md
- type: api-contract
- statement: Each follows the same pattern as Vessel — list/detail/create/update/delete-one/delete-all/upload — with domain-specific search fields:
  - barges search: shipment_code, suppliers, tb (tug boat)
  - trucking search: shipment_code, suppliers, coal_from
  - biomassa search: shipment_code, suppliers, coal_from
  - BargeTNYCreate body fields documented (periode, shipment_code, voyage_code, shipment, suppliers, voyage, tb, bg, coal_from, ta, completed_unloading, bl_mt, ds_mt, gcv_arb, tm_arb, ash_arb, ts_arb).

## CONS-po-batubara-endpoint
- title: Purchase Order Batubara Endpoints
- source: pltu-tenayan-full-backup/API_REFERENCE.md
- type: api-contract
- statement:
  - GET /api/po-batubara, /api/po-batubara/years, /api/po-batubara/{id}
  - POST/PUT/DELETE/DELETE-all + POST /api/upload/po-batubara
  - POBatubaraCreate fields: district_code, district_name, periode, stock_code, warehouse, po_number, supplier_code, supplier_name, spec, vessel_tugboat, barge, no_jadwal, id_bbo_no_pengiriman, id_bbo_trans, no_shipment, time_arrival, completed, completed_year, completed_month, tonase_po, tonase_po_1000, inventory_price, freight_inventory_fob, total.

## CONS-merit-order-endpoint
- title: Merit Order Endpoints
- source: pltu-tenayan-full-backup/API_REFERENCE.md
- type: api-contract
- statement:
  - GET /api/merit-order, /api/merit-order/periods, /api/merit-order/{id}
  - POST/PUT/DELETE/DELETE-all + POST /api/upload/merit-order
  - MeritOrderCreate fields: periode, periode_year, periode_month, pemasok, moda, tipikal_kcal_kg, jenis_kontrak, harga_batubara, harga_freight, harga_cif, rp_kg, rp_kcal.

## CONS-ai-query-endpoint
- title: AI Intelligence Main Query Endpoint
- source: pltu-tenayan-full-backup/API_REFERENCE.md
- type: api-contract
- statement:
  - POST /api/ai/query body: { query, module, session_id?, parameters? }
  - Modules: general, blending, boiler/boiler_risk, contract, logistics, smart-stock, coa
  - Session endpoints: GET/DELETE /api/ai/sessions, GET/DELETE /api/ai/sessions/{id}, POST /api/ai/sessions/new
  - Quick endpoints: /api/ai/quick/blending-suggestion (target_gcv default 4000), /boiler-alerts, /contract-status, /logistics-losses, /smart-stock, /coa-alerts
  - Settings: GET/PUT /api/ai/settings body { custom_api_key?, llm_provider, llm_model } default `gemini` / `gemini-2.5-flash`.

## CONS-smart-stock-endpoint
- title: Smart Stock and Sumber Pemakaian Endpoints
- source: pltu-tenayan-full-backup/API_REFERENCE.md
- type: api-contract
- statement:
  - GET /api/smart-stock with query (limit default 100, max 50000; start_date, end_date YYYY-MM-DD)
  - Response: { data, recent_30_days, supplier_totals, total_count }
  - POST /api/smart-stock/entry body SmartStockEntry { date, stock_awal, suppliers: { SUPPLIER: { A,B,C } }, total_penerimaan }
  - POST /api/smart-stock/upload (multipart)
  - DELETE /api/smart-stock/{id} and DELETE /api/smart-stock
  - GET /api/sumber-pemakaian, POST /api/sumber-pemakaian/entry body SumberPemakaianEntry { date, stock_awal, suppliers: { SUPPLIER: { UNIT1:{A,B,C}, UNIT2:{...} } }, total_pemakaian }
  - POST /api/sumber-pemakaian/upload, DELETE /api/sumber-pemakaian.

## CONS-smart-blending-endpoint
- title: Smart Blending Recommendation Endpoint
- source: pltu-tenayan-full-backup/API_REFERENCE.md
- type: api-contract
- statement:
  - POST /api/smart-blending/recommend body SmartBlendingRequest { target_gcv, max_ash, max_sulphur, max_total_moisture, max_inherent_moisture, min_volatile_matter, min_fixed_carbon, target_quantity }
  - Backend data sources: 6-month vessels/barges/trucking quality, latest smartstock, merit_order pricing.
  - Operational note: depends on LLM budget; failure when budget exhausted is environmental, not a code defect.

## CONS-settings-coa-endpoint
- title: COA Settings Endpoint
- source: pltu-tenayan-full-backup/API_REFERENCE.md
- type: api-contract
- statement:
  - GET /api/settings/coa
  - PUT /api/settings/coa (admin) body { price_per_kcal_per_ton: 12.5 }

## CONS-coa-reconciliation-endpoint
- title: COA Reconciliation Endpoints
- source: pltu-tenayan-full-backup/API_REFERENCE.md
- type: api-contract
- statement:
  - List: GET /api/coa-reconciliation (page, page_size [default 50, max 50000], status, search, date_from, date_to)
  - Aggregations: GET /kpis, /trend (months 1..12 default 3), /supplier-consistency, /dispute-monitor (page, page_size, status)
  - Lookups: GET /{record_id}, /shipment/{shipment}
  - Workflow: POST /propose-umpire { reconciliation_id, sample_number, notes }, POST /update-umpire-status/{id}?status=..., POST /submit-umpire-result body UmpireResultInput { reconciliation_id, umpire_gcv_arb, umpire_tm_arb, umpire_ash_arb, umpire_ts_arb, umpire_lab_name, umpire_result_date, notes }
  - Input: POST /upload (multipart fields loading_file, unloading_file, internal_file; old data dropped before merge), POST /manual body COAManualInput { shipment, suppliers, periode, tb, bg, ds_mt, completed_unloading, loading_*, unloading_*, internal_* }
  - DELETE /api/coa-reconciliation (admin; delete all)
  - Export: GET /export/excel, /export/pdf with optional status_filter

## CONS-projection-id-contract
- title: MongoDB Projection and ID Contract
- source: pltu-tenayan-full-backup/DATABASE_SCHEMA.md
- type: schema
- statement:
  - Public identifier is application-level UUID `id`; MongoDB `_id` MUST NOT be returned to clients.
  - Backend MUST use projection `{"_id": 0}` on reads.
  - Datetimes serialized as ISO 8601 strings.
  - Audit metadata fields: `created_at`, `updated_at`, `uploaded_at`, `umpire_completed_at`, `created_by`, `updated_by`, `uploaded_by`, `umpire_completed_by`.

## CONS-collection-inventory
- title: MongoDB Collection Inventory
- source: pltu-tenayan-full-backup/DATABASE_SCHEMA.md
- type: schema
- statement: Active collections observed: `users`, `user_settings`, `vessels`, `barges`, `trucking`, `biomassa`, `po_batubara`, `merit_order`, `smartstock`, `smart_stock` (legacy), `sumber_pemakaian`, `sumberpemakaian` (legacy), `coa_reconciliation`, `app_settings`, `settings` (legacy), `ai_chat_history` (legacy), `ai_conversations`.

## CONS-collection-naming-debt
- title: Collection Naming Inconsistencies (Tech Debt)
- source: pltu-tenayan-full-backup/DATABASE_SCHEMA.md
- type: schema
- statement: SPEC explicitly flags as needing standardization:
  - `smartstock` vs `smart_stock` (active reads target `smartstock`)
  - `sumber_pemakaian` vs `sumberpemakaian`
  - `app_settings` vs `settings`
  - `ai_chat_history` vs `ai_conversations`
- note: SPEC author recommends standardization but does not yet pick a winner.

## CONS-users-schema
- title: users Collection Schema
- source: pltu-tenayan-full-backup/DATABASE_SCHEMA.md
- type: schema
- statement:
  - Fields: id (UUID), email (unique), password (bcrypt hash), name, role (admin/operator/viewer), created_at (ISO).
  - Recommended indexes: unique on `email`, unique on `id`.

## CONS-vessels-schema
- title: vessels Collection Schema
- source: pltu-tenayan-full-backup/DATABASE_SCHEMA.md
- type: schema
- statement:
  - Core fields: id, periode_ta, periode_realisasi, shipment_code, voyage_code, suppliers, voyage, name_of_vessel, coal_from, time_arrival, berthed_time, commenced_unloading, completed_unloading, durasi_pembongkaran_hari/jam, waktu_tunggu_jam, bl_mt, ds_mt, gcv_arb, tm_arb, ash_arb, ts_arb, slagging_index, fouling_index, created_at, created_by.
  - Document may carry extended quality fields (ash composition, ultimate analysis, HGI, size analysis, COA metadata).
  - Recommended indexes: id unique, shipment_code, suppliers, time_arrival; optional compound `suppliers + completed_unloading`.

## CONS-barges-schema
- title: barges Collection Schema
- source: pltu-tenayan-full-backup/DATABASE_SCHEMA.md
- type: schema
- statement:
  - Core fields: id, periode, shipment_code, voyage_code, shipment, suppliers, voyage, tb (tug boat), bg (barge), coal_from, ta, completed_unloading, bl_mt, ds_mt, gcv_arb, tm_arb, ash_arb, ts_arb, created_at, created_by.
  - Recommended indexes: id unique, shipment_code, suppliers, ta.

## CONS-trucking-schema
- title: trucking Collection Schema
- source: pltu-tenayan-full-backup/DATABASE_SCHEMA.md
- type: schema
- statement:
  - Core fields: id, shipment_code, suppliers, coal_from, ta/periode_ta, gcv_arb, tm_arb, ash_arb, ts_arb, created_at, created_by.
  - Recommended indexes: id unique, shipment_code, suppliers, ta.

## CONS-biomassa-schema
- title: biomassa Collection Schema
- source: pltu-tenayan-full-backup/DATABASE_SCHEMA.md
- type: schema
- statement:
  - Core fields: id, shipment_code, suppliers, coal_from, periode, gcv_arb, tm_arb, ash_arb, ts_arb, created_at, created_by.
  - Recommended indexes: id unique, shipment_code, suppliers, periode.

## CONS-po-batubara-schema
- title: po_batubara Collection Schema
- source: pltu-tenayan-full-backup/DATABASE_SCHEMA.md
- type: schema
- statement:
  - Core fields: id, district_code/name, periode, po_number, supplier_code/name, spec, vessel_tugboat, barge, no_jadwal, id_bbo_no_pengiriman, id_bbo_trans, no_shipment, time_arrival, completed, completed_year, completed_month, tonase_po, tonase_po_1000, inventory_price, freight_inventory_fob, total, created_at, created_by.
  - Recommended indexes: id unique, po_number, supplier_name, completed_year, completed_month; optional compound `completed_year + completed_month`.

## CONS-merit-order-schema
- title: merit_order Collection Schema
- source: pltu-tenayan-full-backup/DATABASE_SCHEMA.md
- type: schema
- statement:
  - Core fields: id, periode, periode_year, periode_month, pemasok, moda (Tongkang/Trucking/Vessel), tipikal_kcal_kg, jenis_kontrak (CIF/CFR/FOB), harga_batubara, harga_freight, harga_cif, rp_kg, rp_kcal, created_at, created_by.
  - Recommended indexes: id unique, periode, periode_year, periode_month, pemasok, rp_kcal.

## CONS-smartstock-schema
- title: smartstock Collection Schema
- source: pltu-tenayan-full-backup/DATABASE_SCHEMA.md
- type: schema
- statement:
  - Core fields: id?, date (YYYY-MM-DD), stock_awal, suppliers (object: SUPPLIER -> {A,B,C}), total_penerimaan, stock_akhir (derived), created_at, created_by.
  - Sources: manual entry and `parse_smart_stock_excel`.
  - Recommended indexes: `date`; optional partial-unique on `date` if 1 entry/day enforced.

## CONS-sumber-pemakaian-schema
- title: sumber_pemakaian Collection Schema
- source: pltu-tenayan-full-backup/DATABASE_SCHEMA.md
- type: schema
- statement:
  - Core fields: date (YYYY-MM-DD), stock_awal, suppliers (object: SUPPLIER -> { UNIT1:{A,B,C}, UNIT2:{...} }), total_pemakaian, created_at, created_by.
  - Sources: manual entry and `parse_sumber_pemakaian_excel`.
  - Recommended indexes: `date`.

## CONS-coa-reconciliation-schema
- title: coa_reconciliation Collection Schema
- source: pltu-tenayan-full-backup/DATABASE_SCHEMA.md
- type: schema
- statement:
  - Identity: id, shipment, suppliers/supplier, periode, tb, bg, ds_mt, completed_unloading.
  - Quality fields per source: loading_{gcv_arb,tm_arb,ash_arb,ts_arb}, unloading_{...}, internal_{...}.
  - Derived: delta_loading_internal, delta_unloading_internal, delta_loading_unloading, status (`normal`/`warning`/`critical`), umpire_status (`none`/`proposed`/`in_progress`/`completed`).
  - Umpire workflow: sample_number, umpire_notes, umpire_proposed_at/by, umpire_{gcv,tm,ash,ts}_arb, umpire_lab_name, umpire_result_date, umpire_result_notes, umpire_completed_at/by.
  - Upload metadata: uploaded_by, uploaded_at.
  - Recommended indexes: id unique, shipment, suppliers, completed_unloading, status, umpire_status; compounds `status + completed_unloading` and `umpire_status + completed_unloading`.

## CONS-app-settings-schema
- title: app_settings Collection Schema
- source: pltu-tenayan-full-backup/DATABASE_SCHEMA.md
- type: schema
- statement:
  - Fields: type (e.g. `coa`), price_per_kcal_per_ton, updated_at, updated_by.
  - Recommended index: unique on `type`.

## CONS-ai-conversations-schema
- title: ai_conversations Collection Schema
- source: pltu-tenayan-full-backup/DATABASE_SCHEMA.md
- type: schema
- statement:
  - Fields: session_id, user_id, messages[], created_at, updated_at, module.
  - messages[] item: { role: 'user'|'assistant', content, timestamp, module }.
  - Recommended indexes: unique session_id, user_id, compound `user_id + updated_at`.

## CONS-logical-relations
- title: Logical Cross-Collection Relations
- source: pltu-tenayan-full-backup/DATABASE_SCHEMA.md
- type: schema
- statement:
  - users.id ← created_by, updated_by, uploaded_by, umpire_completed_by, user_id
  - user_settings.user_id → users.id
  - ai_conversations.user_id → users.id
  - coa_reconciliation.id ↔ flow umpire via reconciliation_id
  - merit_order, vessels, barges, trucking, smartstock → Smart Blending AI inputs
  - po_batubara, merit_order, vessels, barges → AI Intelligence and dashboard context

## CONS-blending-formula
- title: Smart Blending Mathematical Contract
- source: pltu-tenayan-full-backup/frontend/public/docs/Smart_Blending_AI_Formula.md
- type: protocol
- statement:
  - Linear weighted-average: Hasil_Parameter = Σ (Parameter_i × Persentase_i); Σ Persentase_i = 1.0
  - Apply per parameter: GCV_blend, Ash_blend, Sulphur_blend, TM_blend, IM_blend, VM_blend, FC_blend.
  - Tonase_i = Total_Kuantitas × Persentase_i

## CONS-blending-input-ranges
- title: Smart Blending Parameter Ranges and Defaults
- source: pltu-tenayan-full-backup/frontend/public/docs/Smart_Blending_AI_Formula.md
- type: protocol
- statement:
  - Target GCV: 3700 - 4700 kcal/kg (no default)
  - Max Ash: 3.3 - 6.0 % (ARB)
  - Max Sulphur: 0.13 - 2.2 % (ARB)
  - Max Total Moisture: 25 - 40 % (ARB), default 35.0
  - Max Inherent Moisture: 13.8 - 25 % (ADB), default 18.0
  - Min Volatile Matter: 27.9 - 40 % (ARB), default 35.0
  - Min Fixed Carbon: 23 - 41 % (ARB), default 25.0
  - Target Quantity: in MT, no default

## CONS-blending-constraint-validation
- title: Smart Blending Constraint Validation
- source: pltu-tenayan-full-backup/frontend/public/docs/Smart_Blending_AI_Formula.md
- type: protocol
- statement: Each recommendation MUST satisfy:
  - GCV_blend ≥ Target_GCV
  - Ash_blend ≤ Max_Ash
  - Sulphur_blend ≤ Max_Sulphur
  - TM_blend ≤ Max_Total_Moisture
  - IM_blend ≤ Max_Inherent_Moisture
  - VM_blend ≥ Min_Volatile_Matter
  - FC_blend ≥ Min_Fixed_Carbon

## CONS-blending-data-sources
- title: Smart Blending Data Sources
- source: pltu-tenayan-full-backup/frontend/public/docs/Smart_Blending_AI_Formula.md
- type: protocol
- statement:
  - Inventory: vessels (max 50 records), barges (max 50), trucking (max 50) — last 6 months.
  - Per record: supplier, gcv_arb, ash_arb, ts_arb, tm_arb, im_adb, vm_arb, fc_arb, bl_mt/quantity, date.
  - Smart Stock: actual stockpile state.
  - Merit Order: price per kCal per supplier.

## CONS-blending-ai-output
- title: Smart Blending AI JSON Output Schema
- source: pltu-tenayan-full-backup/frontend/public/docs/Smart_Blending_AI_Formula.md
- type: protocol
- statement:
  - Top-level: { recommendation: [], predicted_quality: {}, meets_target: bool, reasoning: str, cost_warning?: str }
  - recommendation[] item: { supplier, source (Vessel/Barge/Trucking), type (LRC/MRC/HRC), percentage, tonnage, gcv, ash, sulphur, total_moisture, inherent_moisture, volatile_matter, fixed_carbon }
  - predicted_quality: { gcv, ash, sulphur, total_moisture, inherent_moisture, volatile_matter, fixed_carbon }

## CONS-blending-classification
- title: Coal Rank Classification
- source: pltu-tenayan-full-backup/frontend/public/docs/Smart_Blending_AI_Formula.md
- type: protocol
- statement:
  - LRC: 3000-4500 kcal/kg, high moisture (>30%), high VM, cheap.
  - MRC: 4500-6000 kcal/kg, moderate moisture, balanced VM/FC.
  - HRC: >6000 kcal/kg, low moisture, high FC, expensive.
  - Typical mix for 4000-4200 kcal/kg target: 60-70% LRC + 30-40% MRC.
  - Operational ideal: 2-4 distinct coal types per blend.

## CONS-blending-measurement-basis
- title: Coal Measurement Basis Conventions
- source: pltu-tenayan-full-backup/frontend/public/docs/Smart_Blending_AI_Formula.md
- type: protocol
- statement:
  - AR/ARB: As Received Basis (operational figures).
  - ADB: Air Dried Basis (lab standard).
  - DB: Dry Basis (cross-coal comparison).
  - DAF/DAFB: Dry Ash-Free Basis (organic-only analysis).
  - Conversion: GCV(ADB) = GCV(ARB) × [100 / (100 - Surface Moisture)]; GCV(DB) = GCV(ADB) × [100 / (100 - Inherent Moisture)].
  - Reference standards: ASTM D388, ISO 1928, ISO 11722, ISO 1171.

## CONS-blending-tolerance
- title: Smart Blending Prediction Tolerance
- source: pltu-tenayan-full-backup/frontend/public/docs/Smart_Blending_AI_Formula.md
- type: nfr
- statement: Predicted blend values carry a ±5% tolerance vs actual post-mix measurement. Assumptions: homogeneous mixing; COA accuracy trusted; segregation during storage NOT modeled.
