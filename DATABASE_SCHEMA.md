# Database Schema

Dokumen ini menjelaskan skema data aplikasi berdasarkan implementasi kode yang aktif. Karena aplikasi memadukan input manual, upload Excel, dan perhitungan turunan, beberapa koleksi memiliki field yang bersifat dinamis atau bertambah sesuai kebutuhan domain. Fokus dokumen ini adalah field inti, pola penyimpanan, relasi logis, dan rekomendasi indexing.

## 1. Gambaran Umum Database

Database utama menggunakan MongoDB dan diakses melalui `Motor` (async MongoDB driver). Nama database dikonfigurasi melalui environment variable `DB_NAME` dan koneksi melalui `MONGO_URL`.

Karakter penyimpanan saat ini:
- Tidak memakai relasi SQL; relasi bersifat logis melalui field seperti `id`, `created_by`, `user_id`, `reconciliation_id`
- Beberapa koleksi menyimpan `datetime` sebagai ISO string
- Banyak dokumen menyertakan `created_at`, `updated_at`, `created_by`, atau metadata upload
- Nama koleksi telah distandardisasi per Phase 5 (2026-05-11); tidak ada lagi duplikasi aktif

## 2. Daftar Koleksi yang Terlihat di Kode

Koleksi yang terobservasi dari kode backend:
- `users`
- `user_settings`
- `vessels`
- `barges`
- `trucking`
- `biomassa`
- `po_batubara`
- `merit_order`
- `smartstock`
- `sumberpemakaian`
- `coa_reconciliation`
- `app_settings`
- `ai_chat_history`

Catatan penting:
- Nama koleksi telah distandardisasi per Phase 5 (2026-05-11). Lihat Duplicate Pair Resolution Log di bawah.

---

## 3. Prinsip Skema dan Serialisasi

### 3.1 ID Aplikasi vs `_id` MongoDB
Mayoritas modul menggunakan field `id` berbasis UUID sebagai identifier publik. Field `_id` MongoDB tidak seharusnya dikirim ke frontend.

### 3.2 Date/Time
Sebagian besar timestamp disimpan sebagai string ISO 8601, misalnya:
- `created_at`
- `updated_at`
- `uploaded_at`
- `umpire_completed_at`

### 3.3 Metadata Audit
Beberapa domain menyimpan metadata audit:
- `created_by`
- `updated_by`
- `uploaded_by`
- `umpire_completed_by`

### 3.4 Dynamic Fields
Dokumen hasil upload Excel dapat memiliki field dinamis tambahan tergantung format sheet dan hasil parser. Karena itu, developer tidak boleh terlalu kaku mengasumsikan semua dokumen selalu identik 100%.

---

## 4. Koleksi `users`

### Tujuan
Menyimpan akun aplikasi.

### Field inti
| Field | Tipe | Wajib | Keterangan |
|---|---|---:|---|
| `id` | string (UUID) | Ya | ID publik user |
| `email` | string | Ya | Harus unik secara bisnis |
| `password` | string | Ya | Hash bcrypt |
| `name` | string | Ya | Nama user |
| `role` | string | Ya | `admin`, `operator`, `viewer` |
| `created_at` | string (ISO datetime) | Ya | Waktu pembuatan akun |

### Contoh dokumen
```json
{
  "id": "c24f...",
  "email": "admin@example.com",
  "password": "$2b$12$...",
  "name": "Admin",
  "role": "admin",
  "created_at": "2026-01-30T12:00:00+00:00"
}
```

### Rekomendasi index
- unique index pada `email`
- unique index pada `id`

---

## 5. Koleksi `user_settings`

### Tujuan
Menyimpan pengaturan AI per user.

### Field inti yang terobservasi
| Field | Tipe | Keterangan |
|---|---|---|
| `user_id` | string | Referensi logis ke `users.id` |
| `custom_api_key` | string/null | API key custom user |
| `llm_provider` | string | Provider LLM, default gemini |
| `llm_model` | string | Model LLM aktif |
| `updated_at` | string | Timestamp update |

### Relasi logis
- `user_settings.user_id` → `users.id`

### Rekomendasi index
- unique index pada `user_id`

---

## 6. Koleksi Operasional Rekap Penerimaan

Kelompok ini mencakup:
- `vessels`
- `barges`
- `trucking`
- `biomassa`

Semua menyimpan data penerimaan bahan bakar, kualitas, tonase, dan metadata operasional.

## 6.1 `vessels`

### Tujuan
Menyimpan data penerimaan batubara via vessel.

### Field inti bisnis
| Field | Tipe | Keterangan |
|---|---|---|
| `id` | string | ID publik |
| `periode_ta` | string | Periode TA |
| `periode_realisasi` | string | Periode realisasi |
| `shipment_code` | string | Kode shipment |
| `voyage_code` | string | Kode voyage |
| `suppliers` | string | Nama supplier |
| `voyage` | string | Nomor/nama voyage |
| `name_of_vessel` | string | Nama vessel |
| `coal_from` | string | Asal coal |
| `time_arrival` | string | Waktu tiba |
| `berthed_time` | string | Waktu sandar |
| `commenced_unloading` | string | Waktu mulai bongkar |
| `completed_unloading` | string | Waktu selesai bongkar |
| `durasi_pembongkaran_hari` | number | Durasi hari |
| `durasi_pembongkaran_jam` | number | Durasi jam |
| `waktu_tunggu_jam` | number | Waiting time |
| `bl_mt` | number | Bill of Lading MT |
| `ds_mt` | number | Draft survey MT |
| `gcv_arb` | number | Nilai kalor |
| `tm_arb` | number | Total moisture |
| `ash_arb` | number | Ash |
| `ts_arb` | number | Total sulphur |
| `slagging_index` | string | Risiko slagging |
| `fouling_index` | string | Risiko fouling |
| `created_at` | string | Timestamp create |
| `created_by` | string | User pembuat |

### Catatan
Koleksi ini memuat banyak field kualitas lanjutan seperti ash composition, ultimate analysis, HGI, size analysis, COA metadata.

### Query pattern umum
- cari berdasarkan `shipment_code`, `suppliers`, `name_of_vessel`
- urut berdasarkan `time_arrival`
- dipakai juga untuk dashboard, AI, dan smart blending

### Rekomendasi index
- unique index `id`
- index `shipment_code`
- index `suppliers`
- index `time_arrival`
- compound index opsional `suppliers + completed_unloading`

## 6.2 `barges`

### Tujuan
Penerimaan batubara via tongkang/barge.

### Field inti
| Field | Tipe | Keterangan |
|---|---|---|
| `id` | string | ID publik |
| `periode` | string | Periode |
| `shipment_code` | string | Kode shipment |
| `voyage_code` | string | Kode voyage |
| `shipment` | string | Identitas shipment |
| `suppliers` | string | Supplier |
| `voyage` | string | Voyage |
| `tb` | string | Tug boat |
| `bg` | string | Nama barge |
| `coal_from` | string | Asal bahan bakar |
| `ta` | string | Time arrival |
| `completed_unloading` | string | Selesai bongkar |
| `bl_mt` | number | Bill of Lading |
| `ds_mt` | number | Draft survey |
| `gcv_arb` | number | Nilai kalor |
| `tm_arb` | number | Moisture |
| `ash_arb` | number | Ash |
| `ts_arb` | number | Sulphur |
| `created_at` | string | Timestamp create |
| `created_by` | string | User pembuat |

### Query pattern umum
- cari berdasarkan `shipment_code`, `suppliers`, `tb`
- urut berdasarkan `ta`

### Rekomendasi index
- unique index `id`
- index `shipment_code`
- index `suppliers`
- index `ta`

## 6.3 `trucking`

### Tujuan
Penerimaan via trucking.

### Field inti yang konsisten dari pola kode
| Field | Tipe | Keterangan |
|---|---|---|
| `id` | string | ID publik |
| `shipment_code` | string | Shipment |
| `suppliers` | string | Supplier |
| `coal_from` | string | Asal |
| `ta` / `periode_ta` | string | Waktu/periode |
| `gcv_arb` | number | Nilai kalor |
| `tm_arb` | number | Moisture |
| `ash_arb` | number | Ash |
| `ts_arb` | number | Sulphur |
| `created_at` | string | Timestamp create |
| `created_by` | string | User pembuat |

### Query pattern umum
- cari berdasarkan `shipment_code`, `suppliers`, `coal_from`
- urut berdasarkan `ta`

### Rekomendasi index
- unique index `id`
- index `shipment_code`
- index `suppliers`
- index `ta`

## 6.4 `biomassa`

### Tujuan
Penerimaan biomassa.

### Field inti
| Field | Tipe | Keterangan |
|---|---|---|
| `id` | string | ID publik |
| `shipment_code` | string | Shipment |
| `suppliers` | string | Supplier |
| `coal_from` | string | Sumber/asal |
| `periode` | string | Periode |
| `gcv_arb` | number | Nilai kalor |
| `tm_arb` | number | Moisture |
| `ash_arb` | number | Ash |
| `ts_arb` | number | Sulphur |
| `created_at` | string | Timestamp create |
| `created_by` | string | User pembuat |

### Query pattern umum
- cari berdasarkan `shipment_code`, `suppliers`, `coal_from`
- urut berdasarkan `periode`

### Rekomendasi index
- unique index `id`
- index `shipment_code`
- index `suppliers`
- index `periode`

---

## 7. Koleksi `po_batubara`

### Tujuan
Menyimpan data purchase order batubara.

### Field inti
| Field | Tipe | Keterangan |
|---|---|---|
| `id` | string | ID publik |
| `district_code` | string | Kode district |
| `district_name` | string | Nama district |
| `periode` | string | Periode |
| `po_number` | string | Nomor PO |
| `supplier_code` | string | Kode supplier |
| `supplier_name` | string | Nama supplier |
| `spec` | string | Spesifikasi |
| `vessel_tugboat` | string | Moda kapal/tugboat |
| `barge` | string | Nama barge |
| `no_jadwal` | string | Jadwal |
| `id_bbo_no_pengiriman` | string | Referensi pengiriman |
| `id_bbo_trans` | string | Referensi transaksi |
| `no_shipment` | string | Nomor shipment |
| `time_arrival` | string | Waktu tiba |
| `completed` | string | Selesai |
| `completed_year` | number | Tahun selesai |
| `completed_month` | number | Bulan selesai |
| `tonase_po` | number | Tonase PO |
| `tonase_po_1000` | number | Tonase turunan |
| `inventory_price` | number | Harga inventory |
| `freight_inventory_fob` | number | Biaya freight |
| `total` | number | Nilai total |
| `created_at` | string | Timestamp |
| `created_by` | string | User |

### Query pattern umum
- filter per tahun/periode
- agregasi supplier dan tonase
- dipakai untuk contract status dan AI context

### Rekomendasi index
- unique index `id`
- index `po_number`
- index `supplier_name`
- index `completed_year`
- index `completed_month`
- compound index opsional `completed_year + completed_month`

---

## 8. Koleksi `merit_order`

### Tujuan
Menyimpan ranking/evaluasi ekonomi pemasok dan moda pasok.

### Field inti
| Field | Tipe | Keterangan |
|---|---|---|
| `id` | string | ID publik |
| `periode` | string | Periode |
| `periode_year` | number | Tahun |
| `periode_month` | number | Bulan |
| `pemasok` | string | Supplier |
| `moda` | string | Tongkang, Trucking, Vessel |
| `tipikal_kcal_kg` | number | Kalori tipikal |
| `jenis_kontrak` | string | CIF, CFR, FOB |
| `harga_batubara` | number | Harga batubara |
| `harga_freight` | number | Harga freight |
| `harga_cif` | number | Harga CIF |
| `rp_kg` | number | Rupiah per kg |
| `rp_kcal` | number | Rupiah per kcal |
| `created_at` | string | Timestamp |
| `created_by` | string | User |

### Query pattern umum
- urut/analisis berdasarkan `rp_kcal`
- filter periodisasi
- dipakai oleh dashboard dan smart blending

### Rekomendasi index
- unique index `id`
- index `periode`
- index `periode_year`
- index `periode_month`
- index `pemasok`
- index `rp_kcal`

---

## 9. Koleksi Smart Stock

## 9.1 `smartstock`

### Tujuan
Menyimpan stok harian berdasarkan sumber penerimaan dan supplier/zona.

### Field inti hasil model/input manual
| Field | Tipe | Keterangan |
|---|---|---|
| `id` | string? | Bisa ada jika dibuat manual/diturunkan implementasi |
| `date` | string (`YYYY-MM-DD`) | Tanggal stok |
| `stock_awal` | number | Stok awal |
| `suppliers` | object | Struktur supplier -> zona A/B/C |
| `total_penerimaan` | number | Total penerimaan |
| `stock_akhir` | number | Nilai turunan / hasil hitung |
| `created_at` | string | Timestamp |
| `created_by` | string | User |

### Struktur `suppliers`
```json
{
  "RIAU_MITRA": { "A": 100, "B": 200, "C": 50 },
  "SUPPLIER_B": { "A": 0, "B": 75, "C": 10 }
}
```

### Sumber data
- input manual
- hasil parser Excel `parse_smart_stock_excel`

### Query pattern umum
- filter date range
- cari data terbaru
- agregasi supplier total 30 hari terakhir

### Rekomendasi index
- index `date`
- unique/partial unique index opsional pada `date` bila 1 entry per hari dijaga

---

## 10. Koleksi Sumber Pemakaian

## 10.1 `sumberpemakaian`

### Tujuan
Menyimpan pemakaian bahan bakar per hari, per unit, dan per supplier.

### Field inti hasil model/input manual
| Field | Tipe | Keterangan |
|---|---|---|
| `date` | string (`YYYY-MM-DD`) | Tanggal |
| `stock_awal` | number | Stok awal |
| `suppliers` | object | Struktur supplier -> UNIT1/UNIT2 -> zona |
| `total_pemakaian` | number | Total pemakaian |
| `created_at` | string | Timestamp |
| `created_by` | string | User |

### Struktur `suppliers`
```json
{
  "RIAU_MITRA": {
    "UNIT1": { "A": 20, "B": 10, "C": 5 },
    "UNIT2": { "A": 15, "B": 8, "C": 2 }
  }
}
```

### Sumber data
- input manual
- hasil parser `parse_sumber_pemakaian_excel`

### Rekomendasi index
- index `date`

---

## 11. Koleksi `coa_reconciliation`

### Tujuan
Menyimpan hasil rekonsiliasi kualitas batubara dari beberapa sumber lab serta workflow dispute/umpire.

### Field inti kualitas
| Field | Tipe | Keterangan |
|---|---|---|
| `id` | string | ID publik record |
| `shipment` | string | Identitas shipment / lot |
| `suppliers` / `supplier` | string | Nama supplier |
| `periode` | string | Periode |
| `tb` | string | Tug boat |
| `bg` | string | Barge |
| `ds_mt` | number | Tonase |
| `completed_unloading` | string | Tanggal selesai bongkar |
| `loading_gcv_arb` | number | GCV loading |
| `loading_tm_arb` | number | TM loading |
| `loading_ash_arb` | number | Ash loading |
| `loading_ts_arb` | number | Sulphur loading |
| `unloading_gcv_arb` | number | GCV unloading |
| `unloading_tm_arb` | number | TM unloading |
| `unloading_ash_arb` | number | Ash unloading |
| `unloading_ts_arb` | number | Sulphur unloading |
| `internal_gcv_arb` | number | GCV internal |
| `internal_tm_arb` | number | TM internal |
| `internal_ash_arb` | number | Ash internal |
| `internal_ts_arb` | number | Sulphur internal |

### Field turunan dan status
| Field | Tipe | Keterangan |
|---|---|---|
| `delta_loading_internal` | number | Selisih loading vs internal |
| `delta_unloading_internal` | number | Selisih unloading vs internal |
| `delta_loading_unloading` | number | Selisih loading vs unloading |
| `status` | string | mis. `normal`, `warning`, `critical` sesuai rule |
| `umpire_status` | string | `none`, `proposed`, `in_progress`, `completed` |

### Field workflow umpire
| Field | Tipe | Keterangan |
|---|---|---|
| `sample_number` | string | Nomor sampel umpire |
| `umpire_notes` | string | Catatan proposal |
| `umpire_proposed_at` | string | Timestamp proposal |
| `umpire_proposed_by` | string | User pengusul |
| `umpire_gcv_arb` | number | Hasil umpire GCV |
| `umpire_tm_arb` | number | Hasil umpire TM |
| `umpire_ash_arb` | number | Hasil umpire Ash |
| `umpire_ts_arb` | number | Hasil umpire TS |
| `umpire_lab_name` | string | Nama lab umpire |
| `umpire_result_date` | string | Tanggal hasil |
| `umpire_result_notes` | string | Catatan hasil |
| `umpire_completed_at` | string | Timestamp finalisasi |
| `umpire_completed_by` | string | User finalisasi |

### Field upload metadata
| Field | Tipe | Keterangan |
|---|---|---|
| `uploaded_by` | string | User upload batch |
| `uploaded_at` | string | Timestamp upload |

### Query pattern umum
- filter `status`
- filter/search `shipment`, `suppliers`
- filter date range `completed_unloading`
- monitoring `umpire_status`
- export dan chart analytic

### Rekomendasi index
- unique index `id`
- index `shipment`
- index `suppliers`
- index `completed_unloading`
- index `status`
- index `umpire_status`
- compound index `status + completed_unloading`
- compound index `umpire_status + completed_unloading`

---

## 12. Koleksi Settings

## 12.1 `app_settings`

### Tujuan
Menyimpan konfigurasi aplikasi global, terutama COA settings.

### Field yang terobservasi
| Field | Tipe | Keterangan |
|---|---|---|
| `type` | string | contoh: `coa` |
| `price_per_kcal_per_ton` | number | parameter bisnis perhitungan kerugian |
| `updated_at` | string | waktu update |
| `updated_by` | string | user updater |

### Rekomendasi index
- unique index pada `type`

---

## 13. Koleksi AI History

## 13.1 `ai_chat_history`

### Tujuan
Penyimpanan history AI model/pola lama.

### Field yang mungkin ada
Karena route dan fitur history masih ada, kemungkinan minimal memuat:
- `id`
- `user_id`
- `query`
- `response`
- `module`
- `created_at`

### Status
`ai_chat_history` is the canonical AI chat history collection (per ADR-012). The previous `ai_conversations` duplicate has been resolved by Phase 5 (2026-05-11).

---

## 14. Relasi Logis Antar Koleksi

Walau MongoDB tidak memaksa relasi, aplikasi memiliki relasi logis berikut:

- `users.id` → `created_by`, `updated_by`, `uploaded_by`, `umpire_completed_by`, `user_id`
- `user_settings.user_id` → `users.id`
- `ai_chat_history.user_id` → `users.id`
- `coa_reconciliation.id` ↔ dipakai oleh flow umpire melalui `reconciliation_id`
- `merit_order`, `vessels`, `barges`, `trucking`, `smartstock` → menjadi input analitik untuk Smart Blending AI
- `po_batubara`, `merit_order`, `vessels`, `barges` → menjadi context data untuk AI Intelligence dan dashboard

---

## 15. Catatan Skema per Fitur

### 15.1 Dashboard
Dashboard bukan koleksi tersendiri; ia merupakan hasil agregasi dari beberapa koleksi operasional.

### 15.2 Laporan
Halaman laporan memanfaatkan koleksi domain yang sudah ada, bukan tabel report materialized terpisah.

### 15.3 Export PDF/Excel
File export tidak disimpan permanen sebagai koleksi database; file dibangkitkan on-demand dari data yang ada.

---

## 16. Technical Debt dan Standardisasi yang Disarankan

### 16.1 Naming Koleksi
Resolved by Phase 5 (2026-05-11). See ADR-009 (smartstock), ADR-010 (sumberpemakaian), ADR-011 (app_settings), ADR-012 (ai_chat_history). Procedure: pltu-tenayan-full-backup/MIGRATION_RUNBOOK.md.

### 16.2 Index Management
Saat ini kode tidak menunjukkan definisi index eksplisit. Disarankan menambahkan bootstrap index pada startup atau migration script terpisah.

### 16.3 Schema Governance
Disarankan:
- memindahkan seluruh Pydantic model ke package `models/`
- membuat data dictionary versi resmi
- menambahkan migration notes ketika ada perubahan field domain

---

## 17. Ringkasan Rekomendasi Index Minimum

| Koleksi | Index minimum yang direkomendasikan |
|---|---|
| `users` | `id` unique, `email` unique |
| `user_settings` | `user_id` unique |
| `vessels` | `id`, `shipment_code`, `suppliers`, `time_arrival` |
| `barges` | `id`, `shipment_code`, `suppliers`, `ta` |
| `trucking` | `id`, `shipment_code`, `suppliers`, `ta` |
| `biomassa` | `id`, `shipment_code`, `suppliers`, `periode` |
| `po_batubara` | `id`, `po_number`, `supplier_name`, `completed_year`, `completed_month` |
| `merit_order` | `id`, `periode`, `pemasok`, `rp_kcal` |
| `smartstock` | `date` |
| `sumberpemakaian` | `date` |
| `coa_reconciliation` | `id`, `shipment`, `suppliers`, `status`, `umpire_status`, `completed_unloading` |
| `app_settings` | `type` unique |
| `ai_chat_history` | `user_id`, `created_at` |

---

## 18. Kesimpulan

Skema database aplikasi ini kaya domain dan cukup fleksibel. Naming koleksi telah distandardisasi di Phase 5 (2026-05-11). Untuk pengembangan jangka panjang, fokus terbaik adalah menambah index, mempertegas batas antara data inti vs data historis/arsip, dan mendokumentasikan field operasional hasil upload Excel secara lebih formal.

---

## Duplicate Pair Resolution Log

Phase-3 plan 03-05 audited 4 duplicate-name collection pairs. Phase 5 (2026-05-11)
resolved each pair: a canonical name was locked in an ADR, the superseded collection
was confirmed empty in the live `pltu_tenayan` DB, server.py reads were switched
to the canonical name, and the empty superseded collection was dropped after a ≥48h
observation window. See `pltu-tenayan-full-backup/MIGRATION_RUNBOOK.md` for the
procedure.

| Pair | Canonical (kept) | Superseded (resolved) | ADR | Resolved | Notes |
|------|------------------|--------------------|------|----------|-------|
| smartstock / smart_stock | smartstock | smart_stock | [ADR-009](../../.planning/decisions/ADR-009-canonical-smartstock.md) | Resolved by Phase 5 (2026-05-11) | Superseded: 0 records; absent from live DB at drop time |
| sumberpemakaian / sumber_pemakaian | sumberpemakaian | sumber_pemakaian | [ADR-010](../../.planning/decisions/ADR-010-canonical-sumberpemakaian.md) | Resolved by Phase 5 (2026-05-11) | Superseded: 0 records; absent from live DB at drop time |
| app_settings / settings | app_settings | settings | [ADR-011](../../.planning/decisions/ADR-011-canonical-app-settings.md) | Resolved by Phase 5 (2026-05-11) | Superseded: 0 records; 3 server.py reads switched (lines 2427, 2926, 4346); absent from live DB at drop time |
| ai_chat_history / ai_conversations | ai_chat_history | ai_conversations | [ADR-012](../../.planning/decisions/ADR-012-canonical-ai-chat-history.md) | Resolved by Phase 5 (2026-05-11) | Superseded: 0 records; zero server.py reads (no code edits required); absent from live DB at drop time |

**Method (Phase 3 audit, preserved for historical context):**
`grep -nE 'db\.(smartstock|smart_stock|sumberpemakaian|sumber_pemakaian|app_settings|settings|ai_chat_history|ai_conversations)\.' backend/server.py`
plus live `db.<name>.countDocuments({})` against the production VPS
(read-only — no writes performed by the audit).
