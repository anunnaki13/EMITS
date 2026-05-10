# Database Schema

Dokumen ini menjelaskan skema data aplikasi berdasarkan implementasi kode yang aktif. Karena aplikasi memadukan input manual, upload Excel, dan perhitungan turunan, beberapa koleksi memiliki field yang bersifat dinamis atau bertambah sesuai kebutuhan domain. Fokus dokumen ini adalah field inti, pola penyimpanan, relasi logis, dan rekomendasi indexing.

## 1. Gambaran Umum Database

Database utama menggunakan MongoDB dan diakses melalui `Motor` (async MongoDB driver). Nama database dikonfigurasi melalui environment variable `DB_NAME` dan koneksi melalui `MONGO_URL`.

Karakter penyimpanan saat ini:
- Tidak memakai relasi SQL; relasi bersifat logis melalui field seperti `id`, `created_by`, `user_id`, `reconciliation_id`
- Beberapa koleksi menyimpan `datetime` sebagai ISO string
- Banyak dokumen menyertakan `created_at`, `updated_at`, `created_by`, atau metadata upload
- Beberapa nama koleksi menunjukkan adanya legacy/transitional structure

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
- `smart_stock`
- `sumber_pemakaian`
- `sumberpemakaian`
- `coa_reconciliation`
- `app_settings`
- `settings`
- `ai_chat_history`
- `ai_conversations`

Catatan penting:
- `smartstock` dan `smart_stock` tampak hidup berdampingan; ini mengindikasikan naming legacy/transisi.
- `sumber_pemakaian` dan `sumberpemakaian` juga mengindikasikan pola serupa.
- `app_settings` dan `settings` sama-sama muncul di kode; perlu standardisasi jangka panjang.
- `ai_chat_history` dan `ai_conversations` menunjukkan ada dua pola penyimpanan history AI pada generasi fitur yang berbeda.

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

## 9.1 `smartstock` / `smart_stock`

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

## 9.2 Catatan naming
Kode aktif list smart stock membaca dari `db.smartstock`, tetapi nama `smart_stock` juga muncul di kode. Sebelum migrasi skema, developer perlu memastikan koleksi mana yang benar-benar dipakai environment produksi.

---

## 10. Koleksi Sumber Pemakaian

## 10.1 `sumber_pemakaian` / `sumberpemakaian`

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

### Catatan naming
Seperti smart stock, ada indikasi naming legacy yang harus distandardisasi.

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

## 12.2 `settings`
Muncul di kode, namun penggunaan aktifnya perlu diverifikasi. Potensial legacy/global settings collection.

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
Masih relevan untuk compatibility/history lama, namun fitur session-based yang lebih jelas kini menggunakan `ai_conversations`.

## 13.2 `ai_conversations`

### Tujuan
Penyimpanan percakapan AI per sesi.

### Field inti
| Field | Tipe | Keterangan |
|---|---|---|
| `session_id` | string | ID sesi percakapan |
| `user_id` | string | User pemilik sesi |
| `messages` | array | Daftar pesan user/assistant |
| `created_at` | string | Waktu dibuat |
| `updated_at` | string | Waktu update terakhir |
| `module` | string | Domain percakapan |

### Struktur `messages[]`
```json
[
  {
    "role": "user",
    "content": "Analisis supplier terbaik",
    "timestamp": "2026-01-30T12:00:00+00:00",
    "module": "general"
  },
  {
    "role": "assistant",
    "content": "Berdasarkan data...",
    "timestamp": "2026-01-30T12:00:02+00:00",
    "module": "general"
  }
]
```

### Query pattern umum
- list sesi per `user_id`
- cari `session_id + user_id`
- sort berdasarkan `updated_at`

### Rekomendasi index
- unique index `session_id`
- index `user_id`
- compound index `user_id + updated_at`

---

## 14. Relasi Logis Antar Koleksi

Walau MongoDB tidak memaksa relasi, aplikasi memiliki relasi logis berikut:

- `users.id` → `created_by`, `updated_by`, `uploaded_by`, `umpire_completed_by`, `user_id`
- `user_settings.user_id` → `users.id`
- `ai_conversations.user_id` → `users.id`
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
Prioritas penting:
- standardisasi `smartstock` vs `smart_stock`
- standardisasi `sumber_pemakaian` vs `sumberpemakaian`
- standardisasi `app_settings` vs `settings`
- standardisasi `ai_chat_history` vs `ai_conversations`

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
| `sumber_pemakaian` | `date` |
| `coa_reconciliation` | `id`, `shipment`, `suppliers`, `status`, `umpire_status`, `completed_unloading` |
| `app_settings` | `type` unique |
| `ai_conversations` | `session_id` unique, `user_id`, `user_id + updated_at` |

---

## 18. Kesimpulan

Skema database aplikasi ini kaya domain dan cukup fleksibel, tetapi mulai menunjukkan kebutuhan standardisasi serius. Untuk pengembangan jangka panjang, fokus terbaik adalah menstabilkan naming koleksi, menambah index, memperjelas batas antara data inti vs data legacy, dan mendokumentasikan field operasional hasil upload Excel secara lebih formal.

---

## Duplicate Pair Active Read Targets (Phase-3 audit, 2026-05-10)

Phase-3 plan 03-05 documents the active read target for each duplicate-pair
collection. **This is documentation only — Phase 5 (DEBT-01..05) owns the
rename and migration.** Determinations are based on `grep -nE 'db\.<name>\.'
backend/server.py` evidence and live row counts as of 2026-05-10.

| Pair | Active (read target) | Legacy | Active count | Legacy count | Code evidence |
|------|----------------------|--------|--------------|--------------|---------------|
| smartstock vs smart_stock | **Both names actively read** — CRUD endpoints use `smartstock`; AI module uses `smart_stock` | N/A — canonical winner deferred to Phase 5 | 207 | 0 | `backend/server.py:3100` db.smartstock.find (CRUD); `backend/server.py:2377` db.smart_stock.find (AI module) |
| sumberpemakaian vs sumber_pemakaian | **Both names actively read** — CRUD endpoints use `sumberpemakaian`; AI module uses `sumber_pemakaian` | N/A — canonical winner deferred to Phase 5 | 208 | 0 | `backend/server.py:3374` db.sumberpemakaian.find (CRUD); `backend/server.py:2385` db.sumber_pemakaian.find (AI module) |
| app_settings vs settings | **Both names actively read** — `/settings/coa` GET/PUT uses `app_settings`; COA export and AI COA-alerts use `settings` | N/A — canonical winner deferred to Phase 5 | 1 | 0 | `backend/server.py:3853` db.app_settings.find_one (settings endpoint); `backend/server.py:4382` db.settings.find_one (COA export); `backend/server.py:2425` db.settings.find_one (AI module) |
| ai_chat_history vs ai_conversations | `ai_chat_history` | `ai_conversations` | 10 | 0 | `backend/server.py:2264` ai_chat_collection = db.ai_chat_history (module-level assignment; all AI session reads go through this variable) |

**Notes on "Both names actively read" rows:**

For `smartstock`/`smart_stock`: the CRUD module (line 3100 onwards) reads from
`db.smartstock` (207 records, the production write target). The AI intelligence
module (line 2377) reads from `db.smart_stock` (0 records). Because live data
lives only in `smartstock`, the AI quick-smart-stock endpoint currently returns
empty/zero context from `smart_stock`. Phase 5 must migrate the AI module read
to `smartstock` and drop `smart_stock`.

For `sumberpemakaian`/`sumber_pemakaian`: same pattern — CRUD writes to
`sumberpemakaian` (208 records); AI module reads `sumber_pemakaian` (0 records).
Phase 5 must align the AI module read to `sumberpemakaian`.

For `app_settings`/`settings`: the canonical `/settings/coa` endpoint reads and
writes `app_settings` (1 record, production data). The COA-export PDF path
(line 4382) and AI COA-alerts context (line 2425) still read the legacy `settings`
collection (0 records). This means COA export and AI COA-alerts silently fall back
to the hardcoded default (`price_per_kcal_per_ton = 50`). Phase 5 must unify
these reads to `app_settings`.

**Method:** `grep -nE 'db\.(smartstock|smart_stock|sumberpemakaian|sumber_pemakaian|app_settings|settings|ai_chat_history|ai_conversations)\.' backend/server.py`
plus live `db.<name>.countDocuments({})` against the production VPS
(read-only — no writes performed by this audit).

**Phase 5 dependency:** the rename plan (DEBT-01..05) MUST start from this
table — picking a canonical winner per row, dry-running migration, and
removing legacy reads only after verified row-count + checksum parity.

See `.planning/ROADMAP.md` §"Phase 5: Collection Naming Debt Resolution"
and `.planning/intel/constraints.md` → CONS-collection-naming-debt.
