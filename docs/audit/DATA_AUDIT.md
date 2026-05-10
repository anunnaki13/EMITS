# Data Audit — Live MongoDB Inventory

**Live host:** localhost:27017 (single-host VPS topology)
**Database:** pltu_tenayan
**Captured:** 2026-05-10T11:25:04Z
**Method:** mongosh listCollections + countDocuments({}) per collection. Read-only; no writes issued.

Connection string sourced at probe time from `pltu-tenayan-full-backup/backend/.env` (`MONGO_URL`, `DB_NAME`) and is NOT recorded in this file. Raw artifacts live in `docs/audit/.work/`.

## Inventory

| Collection         | Live count | Documented count | Delta         | Status       | Naming-debt pair       | Notes                                                              |
|--------------------|-----------:|-----------------:|--------------:|--------------|------------------------|--------------------------------------------------------------------|
| ai_chat_history    |         10 |               10 |             0 | matches      | ai-history-pair        | Legacy per CONS-collection-inventory; only side present in live db |
| app_settings       |          1 |                — |  no-doc-count | drift        | settings-pair          | Single COA-pricing doc (`type=coa`); only side present in live db  |
| barges             |        168 |                — |  no-doc-count | undocumented | none                   | Live and active; not enumerated in PROJECT.md "Live data inventory" |
| biomassa           |         45 |               45 |             0 | matches      | none                   |                                                                    |
| coa_reconciliation |        721 |              721 |             0 | matches      | none                   | Largest collection                                                 |
| merit_order        |         58 |               58 |             0 | matches      | none                   |                                                                    |
| po_batubara        |        301 |              301 |             0 | matches      | none                   |                                                                    |
| smartstock         |        207 |              207 |             0 | matches      | smartstock-pair        | Active read target per CONS-collection-naming-debt                 |
| sumberpemakaian    |        208 |              208 |             0 | matches      | sumberpemakaian-pair   | PROJECT.md reports active=sumberpemakaian; confirmed by data       |
| trucking           |        461 |              461 |             0 | matches      | none                   | Largest receipt collection                                         |
| user_settings      |          1 |                — |  no-doc-count | undocumented | none                   | One row (per-user AI settings); not in PROJECT.md inventory        |
| users              |          8 |                7 |            +1 | drift        | none                   | Live has one extra account vs documented                           |
| vessels            |        111 |              111 |             0 | matches      | none                   |                                                                    |
| smart_stock        |          — |                — |             — | missing      | smartstock-pair        | Listed in CONS-collection-inventory; absent from live db           |
| sumber_pemakaian   |          — |                — |             — | missing      | sumberpemakaian-pair   | Listed in CONS-collection-inventory; absent from live db           |
| settings           |          — |                — |             — | missing      | settings-pair          | Listed in CONS-collection-inventory; absent from live db           |
| ai_conversations   |          — |                — |             — | missing      | ai-history-pair        | Listed in CONS-collection-inventory; absent from live db           |

Live total: 13 collections, 2 300 documents across all collections.
Inventory rows: 13 live + 4 missing-from-live (CONS-collection-inventory entries that have no live counterpart) = 17 total.

## Naming-debt mapping (Phase 5 ground truth)

For each duplicate pair flagged in CONS-collection-naming-debt, the row counts on each side are reported below. This section reports what the data says and does NOT pick a canonical winner — Phase 5 owns DEBT-01.

### smartstock-pair

| Name        | Live count | Decision signal             |
|-------------|-----------:|-----------------------------|
| smartstock  |        207 | active read target per SPEC |
| smart_stock |          — | absent (legacy per SPEC)    |

Recommendation row: Canonical winner candidate by row count: **smartstock** (the only side that exists; legacy `smart_stock` collection is not present on this database). Phase 5 still owns the rename decision.

### sumberpemakaian-pair

| Name             | Live count | Decision signal                          |
|------------------|-----------:|------------------------------------------|
| sumberpemakaian  |        208 | active per PROJECT.md "Live data inventory" |
| sumber_pemakaian |          — | absent (paired SPEC name)                |

Recommendation row: Canonical winner candidate by row count: **sumberpemakaian** (only side present). Phase 5 still owns the rename decision.

### settings-pair

| Name         | Live count | Decision signal                                             |
|--------------|-----------:|-------------------------------------------------------------|
| app_settings |          1 | only side present in live db; carries the COA pricing doc   |
| settings     |          — | absent (paired SPEC name)                                   |

Recommendation row: Canonical winner candidate by row count: **app_settings** (only side present, holds 1 doc of `type=coa`). Phase 5 still owns the rename decision.

### ai-history-pair

| Name             | Live count | Decision signal                                                    |
|------------------|-----------:|--------------------------------------------------------------------|
| ai_chat_history  |         10 | only side present; SPEC labels this the legacy name                |
| ai_conversations |          — | absent (SPEC's preferred forward name; CONS-ai-conversations-schema) |

Recommendation row: Data-by-count signal: **ai_chat_history** (only side present, 10 docs). Note for Phase 5: SPEC-preferred forward name (`ai_conversations`) does NOT exist on disk — Phase 5 must consult before any migration that assumes both sides exist.

## Projection contract spot-check (CONS-projection-id-contract)

The CONS-projection-id-contract is enforced by the API layer; presence of `_id` in storage is expected (every MongoDB document has one). The audit checks that an application-level `id` field exists alongside `_id`, so the API can safely apply `{"_id": 0}` and still return a stable public identifier.

| Collection         | Has `id` field in sample?                          | Has `_id` field in sample? | Other suspicious top-level keys                |
|--------------------|----------------------------------------------------|----------------------------|------------------------------------------------|
| ai_chat_history    | yes                                                | yes                        | none                                           |
| app_settings       | no — uses `type` as discriminator (`type=coa`)     | yes                        | none                                           |
| barges             | yes                                                | yes                        | none                                           |
| biomassa           | yes                                                | yes                        | none                                           |
| coa_reconciliation | yes                                                | yes                        | none                                           |
| merit_order        | yes                                                | yes                        | none                                           |
| po_batubara        | yes                                                | yes                        | none                                           |
| smartstock         | yes                                                | yes                        | none                                           |
| sumberpemakaian    | yes                                                | yes                        | none                                           |
| trucking           | yes                                                | yes                        | none                                           |
| user_settings      | no — uses `user_id` as FK to users.id              | yes                        | none                                           |
| users              | yes                                                | yes                        | `password` (bcrypt hash by SPEC; expected here, MUST be projected out) |
| vessels            | yes                                                | yes                        | none                                           |

Anomalies on `id` presence:

- **app_settings** has no `id` field. Its primary key is the `type` discriminator (`type=coa`). This is consistent with CONS-app-settings-schema (recommended unique index on `type`) but breaks the universal CONS-projection-id-contract assumption that "every collection exposes a UUID `id`". Phase 3 (docs refresh) should explicitly note this exception.
- **user_settings** has no `id` field. Its primary key is `user_id` (FK to users.id). The CONS-projection-id-contract carve-out for `user_id` mirrors `ai_conversations.user_id` per CONS-logical-relations. Phase 3 should document the per-user settings collection as a 1:1-with-users projection where the FK *is* the identifier.

`users.password` (bcrypt hash) appears in storage as expected per CONS-users-schema. The `{"_id": 0}` projection alone does NOT scrub this — backend handlers MUST also strip `password`. Confirming that the auth/user endpoints do this is owned by Phase 1 plan 01-01 (ENDPOINT_AUDIT.md) for response-shape audit, not by this plan.

## Cross-collection schema spot-check

For each high-traffic collection, the documented core fields (per CONS-*-schema and DATABASE_SCHEMA.md) are diffed against the live sample's top-level keys.

### users
- Documented core fields: id, email, password, name, role, created_at
- Sample top-level fields: _id, created_at, email, id, name, password, role
- Missing from sample: none
- Extra in sample (undocumented): none

### vessels
- Documented core fields: id, periode_ta, periode_realisasi, shipment_code, voyage_code, suppliers, voyage, name_of_vessel, coal_from, time_arrival, berthed_time, commenced_unloading, completed_unloading, durasi_pembongkaran_hari, durasi_pembongkaran_jam, waktu_tunggu_jam, bl_mt, ds_mt, gcv_arb, tm_arb, ash_arb, ts_arb, slagging_index, fouling_index, created_at, created_by
- Sample top-level fields: _id, al2o3_db, ash_adb, ash_arb, ash_db, berthed_time, bl_mt, c_adb, c_arb, cao_db, coal_from, commenced_unloading, completed_unloading, created_at, created_by, ds_mt, durasi_pembongkaran_hari, durasi_pembongkaran_jam, durasi_terbit_coa, fc_adb, fc_arb, fe2o3_db, fouling_index, gcv_adb, gcv_arb, gcv_db, h_adb, h_arb, hgi, id, idt_reducing, im_adb, k2o_db, mgo_db, mn3o4_db, mno2_db, n_adb, n_arb, n_dafb, na2o_db, name_of_vessel, no_coa, no_cow, o_adb, o_arb, p2o5_db, periode_realisasi, periode_ta, shipment_code, sio2_db, size_2_38mm, size_32mm, size_50mm, size_70mm, slagging_index, so3_db, suppliers, tgl_terbit_coa, tgl_terbit_cow, time_arrival, tio2_db, tm_arb, ts_adb, ts_arb, ts_dafb, ts_db, vm_adb, vm_arb, voyage, voyage_code, waktu_tunggu_jam
- Missing from sample: none (all documented core fields present)
- Extra in sample (undocumented): extended quality fields (ash composition, ultimate analysis, HGI, size analysis, COA metadata) — explicitly anticipated by CONS-vessels-schema ("document may carry extended quality fields"); not a defect.

### barges
- Documented core fields: id, periode, shipment_code, voyage_code, shipment, suppliers, voyage, tb (tug boat), bg (barge), coal_from, ta, completed_unloading, bl_mt, ds_mt, gcv_arb, tm_arb, ash_arb, ts_arb, created_at, created_by
- Sample top-level fields: _id, al2o3_db, ash_adb, ash_arb, ash_db, berthed_time, bg, bl_mt, c_adb, c_arb, cao_db, coal_from, commenced_unloading, completed_unloading, created_at, created_by, ds_mt, durasi_pembongkaran_hari, durasi_pembongkaran_jam, durasi_terbit_coa, fc_adb, fc_arb, fe2o3_db, fouling_index, gcv_adb, gcv_arb, gcv_db, h_adb, h_arb, hgi, id, idt_reducing, im_adb, k2o_db, mgo_db, mn3o4_db, mno2_db, n_adb, n_arb, n_dafb, na2o_db, no_coa, no_cow, o_adb, o_arb, p2o5_db, periode, shipment, shipment_code, sio2_db, size_2_38mm, size_32mm, size_50mm, size_70mm, slagging_index, so3_db, suppliers, ta, tb, tgl_terbit_coa, tgl_terbit_cow, tio2_db, tm_arb, ts_adb, ts_arb, ts_dafb, ts_db, vm_adb, vm_arb, voyage, voyage_code, waktu_tunggu_jam
- Missing from sample: none
- Extra in sample (undocumented): extended quality fields parallel to vessels (ultimate/proximate/ash analysis, COA metadata) — schema-consistent enrichment, not a defect.

### trucking
- Documented core fields: id, shipment_code, suppliers, coal_from, ta/periode_ta, gcv_arb, tm_arb, ash_arb, ts_arb, created_at, created_by
- Sample top-level fields: _id, al2o3_db, ash_adb, ash_arb, ash_db, berthed_time, bl_mt, c_adb, c_arb, cao_db, coal_from, commenced_unloading, completed_unloading, created_at, created_by, ds_mt, durasi_pembongkaran_hari, durasi_pembongkaran_jam, fc_adb, fc_arb, fe2o3_db, fouling_index, gcv_adb, gcv_arb, gcv_db, h_adb, h_arb, hgi, id, idt_reducing, im_adb, k2o_db, mgo_db, mn3o4_db, mno2_db, n_adb, n_arb, n_dafb, na2o_db, no_coa, no_cow, o_adb, o_arb, p2o5_db, periode_realisasi, periode_ta, rit, shipment, shipment_code, sio2_db, size_2_38mm, size_32mm, size_50mm, size_70mm, slagging_index, so3_db, suppliers, ta, tgl_terbit_coa, tgl_terbit_cow, tio2_db, tm_arb, transportasi, ts_adb, ts_arb, ts_dafb, ts_db, vm_adb, vm_arb, voyage_code
- Missing from sample: none (all of id, shipment_code, suppliers, coal_from, ta, periode_ta, gcv_arb, tm_arb, ash_arb, ts_arb, created_at, created_by present)
- Extra in sample (undocumented): `rit`, `transportasi`, plus the same extended quality fields (ash composition, ultimate analysis, HGI, size analysis, COA metadata). `rit` and `transportasi` look domain-meaningful (Indonesian: trip count, mode of transport) — Phase 3 should add to DATABASE_SCHEMA.md.

### biomassa
- Documented core fields: id, shipment_code, suppliers, coal_from, periode, gcv_arb, tm_arb, ash_arb, ts_arb, created_at, created_by
- Sample top-level fields: _id, berthed_time, bg, biomass_type, bl_mt, commenced_unloading, completed_unloading, created_at, created_by, durasi_pembongkaran_hari, durasi_pembongkaran_hari_2, durasi_terbit_coa, gcv_adb, gcv_arb, id, im_adb, jembatan_timbang_mt, lama_terbit_row, lot, lot_1, no_coa, no_cow_row, periode, shipment_code, shipper, suppliers, surveyor_unloading, ta, tb, tgl_terbit_coa, tgl_terbit_cow, tm_arb, voyage_code, waktu_tunggu_jam
- Missing from sample: `coal_from`, `ash_arb`, `ts_arb`. Three documented core fields are absent from the sample document. This may be a schema-version gap (older documents) or a documentation-vs-reality drift — Phase 3 must confirm.
- Extra in sample (undocumented): `biomass_type`, `bg`, `bl_mt`, `berthed_time`, `commenced_unloading`, `completed_unloading`, `durasi_pembongkaran_hari`, `durasi_pembongkaran_hari_2`, `durasi_terbit_coa`, `gcv_adb`, `im_adb`, `jembatan_timbang_mt`, `lama_terbit_row`, `lot`, `lot_1`, `no_coa`, `no_cow_row`, `shipper`, `surveyor_unloading`, `ta`, `tb`, `tgl_terbit_coa`, `tgl_terbit_cow`, `voyage_code`, `waktu_tunggu_jam`. Significant undocumented surface; Phase 3 should expand CONS-biomassa-schema.

### po_batubara
- Documented core fields: id, district_code, district_name, periode, po_number, supplier_code, supplier_name, spec, vessel_tugboat, barge, no_jadwal, id_bbo_no_pengiriman, id_bbo_trans, no_shipment, time_arrival, completed, completed_year, completed_month, tonase_po, tonase_po_1000, inventory_price, freight_inventory_fob, total, created_at, created_by
- Sample top-level fields: _id, barge, completed, completed_month, completed_year, created_at, created_by, district_code, district_name, freight_inventory_fob, id, id_bbo_no_pengiriman, id_bbo_trans, inventory_price, no_jadwal, no_shipment, periode, po_number, spec, stock_code, supplier_code, supplier_name, time_arrival, tonase_po, tonase_po_1000, total, vessel_tugboat, warehouse
- Missing from sample: none
- Extra in sample (undocumented): `stock_code`, `warehouse` — both are documented in CONS-po-batubara-endpoint as accepted body fields but were NOT listed in CONS-po-batubara-schema's "core fields" enumeration. Phase 3 should reconcile schema doc with endpoint doc.

### merit_order
- Documented core fields: id, periode, periode_year, periode_month, pemasok, moda, tipikal_kcal_kg, jenis_kontrak, harga_batubara, harga_freight, harga_cif, rp_kg, rp_kcal, created_at, created_by
- Sample top-level fields: _id, created_at, created_by, harga_batubara, harga_cif, harga_freight, id, jenis_kontrak, moda, pemasok, periode, periode_month, periode_year, rp_kcal, rp_kg, tipikal_kcal_kg
- Missing from sample: none
- Extra in sample (undocumented): none

### smartstock
- Documented core fields: id?, date (YYYY-MM-DD), stock_awal, suppliers (object), total_penerimaan, stock_akhir (derived), created_at, created_by
- Sample top-level fields: _id, created_at, date, id, stock_awal, suppliers, total_penerimaan, updated_at
- Missing from sample: `stock_akhir` (documented as derived; may be computed at read time, not persisted), `created_by`.
- Extra in sample (undocumented): `updated_at` — Phase 3 should add to CONS-smartstock-schema.

### sumberpemakaian (active per CONS-collection-naming-debt; legacy `sumber_pemakaian` not in live db)
- Documented core fields (per CONS-sumber-pemakaian-schema): date (YYYY-MM-DD), stock_awal, suppliers (object), total_pemakaian, created_at, created_by
- Sample top-level fields: _id, created_at, date, id, stock_awal, suppliers, total_pemakaian, updated_at
- Missing from sample: `created_by`
- Extra in sample (undocumented): `id` (documented schema does not list `id` for this collection but the doc clearly carries one — this is consistent with CONS-projection-id-contract and Phase 3 should add to schema), `updated_at`.

### coa_reconciliation
- Documented core fields: id, shipment, suppliers/supplier, periode, tb, bg, ds_mt, completed_unloading; loading_*, unloading_*, internal_* per quality; delta_loading_internal, delta_unloading_internal, delta_loading_unloading, status, umpire_status; umpire_*; uploaded_by, uploaded_at
- Sample top-level fields: _id, bg, completed_unloading, created_at, delta_loading_internal, delta_loading_unloading, delta_unloading_internal, ds_mt, id, internal_ash_arb, internal_gcv_arb, internal_tm_arb, internal_ts_arb, loading_ash_arb, loading_gcv_arb, loading_no_coa, loading_surveyor, loading_tm_arb, loading_ts_arb, periode, shipment, status, suppliers, tb, umpire_ash_arb, umpire_completed_at, umpire_gcv_arb, umpire_lab_name, umpire_notes, umpire_proposed_at, umpire_proposed_by, umpire_result_date, umpire_sample_number, umpire_started_at, umpire_status, umpire_tm_arb, umpire_ts_arb, unloading_ash_arb, unloading_fouling, unloading_gcv_arb, unloading_slagging, unloading_surveyor, unloading_tm_arb, unloading_ts_arb, uploaded_at, uploaded_by
- Missing from sample: none of the documented core/identity fields are missing. Some umpire workflow fields documented as `umpire_completed_by`, `umpire_result_notes` are absent from THIS sample — those fields are conditional on workflow stage (a non-completed-umpire row will not carry them); not a defect.
- Extra in sample (undocumented): `loading_no_coa`, `loading_surveyor`, `unloading_surveyor`, `unloading_fouling`, `unloading_slagging`. These are quality-source-metadata enrichments and align with the surveyor/lab fields elsewhere; Phase 3 should add to CONS-coa-reconciliation-schema.

### ai_chat_history (legacy per SPEC; `ai_conversations` SPEC name absent from live db)
- Documented core fields (per CONS-ai-conversations-schema): session_id, user_id, messages[], created_at, updated_at, module
- Sample top-level fields: _id, created_at, id, module, parameters, query, response, session_id, user_id
- Missing from sample: `messages[]`, `updated_at`. The live `ai_chat_history` schema is shaped as one-row-per-Q&A (`query`+`response`) rather than session-with-messages-array. CONS-ai-conversations-schema describes the SPEC-preferred forward shape, NOT what the live `ai_chat_history` rows look like. Phase 5 must reconcile: migrating ai_chat_history to ai_conversations is a SHAPE migration (rows → grouped-by-session messages[]), not just a rename.
- Extra in sample (undocumented): `id`, `parameters`, `query`, `response`. These are the actual fields of the legacy collection.

### app_settings (only side present of settings-pair)
- Documented core fields (per CONS-app-settings-schema): type, price_per_kcal_per_ton, updated_at, updated_by
- Sample top-level fields: _id, price_per_kcal_per_ton, type, updated_at, updated_by
- Missing from sample: none
- Extra in sample (undocumented): none

### user_settings (not enumerated in CONS-collection-inventory but exists live)
- Documented core fields (per CONS-ai-query-endpoint settings spec): custom_api_key, llm_provider, llm_model
- Sample top-level fields: _id, custom_api_key, llm_model, llm_provider, updated_at, user_id
- Missing from sample: none
- Extra in sample (undocumented): `updated_at`, `user_id` — both are obviously expected; Phase 3 should formalize CONS-user-settings-schema (currently only the endpoint contract exists).

## Anomalies / next-phase notes

- **Status `undocumented`** (Phase 3 must add to DATABASE_SCHEMA.md / PROJECT.md "Live data inventory"):
  - `barges` (168 rows) — already covered by CONS-barges-schema but missing from PROJECT.md inventory table.
  - `user_settings` (1 row) — has no CONS-*-schema entry at all.
- **Status `missing`** (collections in CONS-collection-inventory but absent from live db) — Phase 5 must consult before migration design:
  - `smart_stock` — legacy paired with active `smartstock`; absent simplifies migration (rename or no-op rather than merge).
  - `sumber_pemakaian` — legacy paired with active `sumberpemakaian`; absent simplifies migration.
  - `settings` — paired with `app_settings`; absent simplifies migration.
  - `ai_conversations` — SPEC-preferred forward name; absent means Phase 5's task is collection rename + document-shape migration (ai_chat_history rows are not the same shape as CONS-ai-conversations-schema messages[]).
- **Naming-debt pairs where BOTH sides have non-zero rows:** none on this database. Every duplicate pair has the legacy/SPEC-paired side absent. This is the easiest possible Phase 5 starting position — no merge logic required.
- **Naming-debt pairs where active-read side has FEWER rows than legacy:** N/A (no pair has both sides populated).
- **users drift (+1):** live has 8 users vs documented 7. Plausibly a new admin/operator account added since the documentation snapshot. Phase 1 plan 01-01 (ENDPOINT_AUDIT) and Phase 2 (login bug) should be aware that the live user roster is not what PROJECT.md says.
- **Schema doc gaps to feed Phase 3:**
  - `biomassa` sample is missing 3 documented core fields (`coal_from`, `ash_arb`, `ts_arb`) and carries 25 undocumented extras — significant doc drift.
  - `trucking` carries `rit`, `transportasi` not in CONS-trucking-schema.
  - `po_batubara` carries `stock_code`, `warehouse` documented at endpoint layer but not at schema layer.
  - `smartstock` and `sumberpemakaian` carry `updated_at` not in schema.
  - `coa_reconciliation` carries `loading_no_coa`, `loading_surveyor`, `unloading_surveyor`, `unloading_fouling`, `unloading_slagging` not in schema.
  - `ai_chat_history` does not match CONS-ai-conversations-schema at all (different shape; this is a Phase 5 migration concern, not a Phase 3 doc fix).

## Methodology

Reproducible scripts and raw artifacts live in `pltu-tenayan-full-backup/docs/audit/.work/`:

- `mongo-collections.txt` — `db.getCollectionNames().sort()` output, one collection per line.
- `mongo-counts.json` — `{ collection: countDocuments({}) }` per collection, JSON.
- `mongo-samples.json` — `{ collection: Object.keys(findOne({})).sort() }` per collection, JSON. Field names only; document payloads were not persisted to the audit artifacts.

Connection string sourced from `backend/.env` at probe time and never written to this file or to git. No write operation (insert / update / delete / drop / rename) was issued against the live database during probing. This audit does NOT pick a canonical winner for any naming-debt pair — Phase 5 owns DEBT-01.
