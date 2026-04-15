# API Reference

Dokumen ini merangkum endpoint backend utama yang digunakan aplikasi PLTU Tenayan Fuel Management System. Fokusnya adalah membantu developer memahami kontrak API yang aktif, pola auth, struktur pagination, serta payload inti per modul.

## 1. Base URL dan Konvensi

- Base URL frontend dikonfigurasi melalui `REACT_APP_BACKEND_URL`
- Semua endpoint backend dipanggil dengan prefix `/api`
- Contoh base URL produksi/preview:
  - `https://your-domain.com/api`

Contoh request dengan token:

```bash
curl -X GET "https://your-domain.com/api/auth/me" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

## 2. Authentication

### Header Auth
Hampir semua endpoint selain login/register memerlukan:

```http
Authorization: Bearer <token>
```

### Role yang digunakan
- `admin`
- `operator`
- `viewer`

## 3. Format Response Umum

### 3.1 Response Pagination
Banyak endpoint list memakai pola berikut:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 50,
  "total_pages": 0
}
```

Catatan penting:
- Frontend harus membaca `response.data.items`
- Jangan mengasumsikan response list langsung berupa array

### 3.2 Response Pesan Sederhana

```json
{
  "message": "Operasi berhasil"
}
```

### 3.3 Error Umum
- `400` bad request / validasi gagal / file gagal diproses
- `401` token tidak valid / login gagal
- `403` role tidak diizinkan
- `404` data tidak ditemukan
- `500` error internal atau error integrasi AI

---

## 4. Health & Root

### GET `/api/`
Cek root API.

**Auth:** Tidak perlu  
**Response:**
```json
{
  "message": "PLTU Tenayan Fuel Management System API",
  "status": "running"
}
```

### GET `/api/health`
Health check aplikasi.

**Auth:** Tidak perlu

---

## 5. Authentication API

### POST `/api/auth/register`
Mendaftarkan user baru.

**Auth:** Umumnya dipakai saat bootstrap atau admin flow, tergantung kontrol frontend  
**Body:**
```json
{
  "email": "operator@example.com",
  "password": "secret123",
  "name": "Operator A",
  "role": "operator"
}
```

**Response:** token + data user.

### POST `/api/auth/login`
Login user.

**Auth:** Tidak perlu  
**Body:**
```json
{
  "email": "admin@example.com",
  "password": "adminpassword"
}
```

**Response:**
```json
{
  "access_token": "...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "admin@example.com",
    "name": "Admin",
    "role": "admin",
    "created_at": "2026-01-01T00:00:00+00:00"
  }
}
```

### GET `/api/auth/me`
Mengambil profil user aktif berdasarkan JWT.

**Auth:** Ya

### GET `/api/users`
Daftar user untuk admin/settings.

**Auth:** Ya  
**Role:** Admin

---

## 6. Rekap Penerimaan BB

Domain ini mencakup vessel, barge, trucking, dan biomassa. Polanya relatif konsisten: list, detail, create, update, delete, delete-all, dan upload Excel.

## 6.1 Vessel

### GET `/api/vessels`
Mengambil daftar vessel.

**Auth:** Ya  
**Query params:**
- `search` (opsional)
- `page` (default `1`)
- `page_size` (umumnya maksimal `500`)

**Search fields:**
- `shipment_code`
- `suppliers`
- `name_of_vessel`

### GET `/api/vessels/{vessel_id}`
Detail vessel berdasarkan `id`.

### POST `/api/vessels`
Tambah data vessel.

**Role:** `admin`, `operator`  
**Body utama:** `VesselTNYCreate`

Field penting:
- `periode_ta`
- `periode_realisasi`
- `shipment_code`
- `voyage_code`
- `suppliers`
- `voyage`
- `name_of_vessel`
- `coal_from`
- `time_arrival`
- `completed_unloading`
- `bl_mt`, `ds_mt`
- `gcv_arb`, `tm_arb`, `ash_arb`, `ts_arb`
- dan turunan kualitas lainnya

### PUT `/api/vessels/{vessel_id}`
Update vessel.

### DELETE `/api/vessels/{vessel_id}`
Hapus 1 vessel.

**Role:** `admin`

### DELETE `/api/vessels`
Hapus seluruh data vessel.

**Role:** `admin`

### POST `/api/upload/vessel`
Upload Excel vessel.

**Auth:** Ya  
**Role:** `admin`, `operator`  
**Content-Type:** `multipart/form-data`

## 6.2 Barge

### GET `/api/barges`
**Query params:** `search`, `page`, `page_size`

**Search fields:**
- `shipment_code`
- `suppliers`
- `tb`

### GET `/api/barges/{barge_id}`
### POST `/api/barges`
### PUT `/api/barges/{barge_id}`
### DELETE `/api/barges/{barge_id}`
### DELETE `/api/barges`
### POST `/api/upload/barge`

**Body utama `BargeTNYCreate`:**
- `periode`
- `shipment_code`
- `voyage_code`
- `shipment`
- `suppliers`
- `voyage`
- `tb`, `bg`
- `coal_from`
- `ta`, `completed_unloading`
- `bl_mt`, `ds_mt`
- `gcv_arb`, `tm_arb`, `ash_arb`, `ts_arb`

## 6.3 Trucking

### GET `/api/trucking`
**Query params:** `search`, `page`, `page_size`

**Search fields:**
- `shipment_code`
- `suppliers`
- `coal_from`

### GET `/api/trucking/{trucking_id}`
### POST `/api/trucking`
### PUT `/api/trucking/{trucking_id}`
### DELETE `/api/trucking/{trucking_id}`
### DELETE `/api/trucking`
### POST `/api/upload/trucking`

## 6.4 Biomassa

### GET `/api/biomassa`
**Query params:** `search`, `page`, `page_size`

**Search fields:**
- `shipment_code`
- `suppliers`
- `coal_from`

### GET `/api/biomassa/{biomassa_id}`
### POST `/api/biomassa`
### PUT `/api/biomassa/{biomassa_id}`
### DELETE `/api/biomassa/{biomassa_id}`
### DELETE `/api/biomassa`
### POST `/api/upload/biomassa`

---

## 7. Purchase Order Batubara

### GET `/api/po-batubara`
Mengambil daftar PO.

**Auth:** Ya  
**Query params:** biasanya mendukung filter periode/tahun/supplier sesuai kebutuhan halaman.

### GET `/api/po-batubara/years`
Daftar tahun yang tersedia untuk filter frontend.

### GET `/api/po-batubara/{po_id}`
Detail PO.

### POST `/api/po-batubara`
Tambah PO.

**Body utama `POBatubaraCreate`:**
- `district_code`, `district_name`
- `periode`
- `stock_code`, `warehouse`
- `po_number`
- `supplier_code`, `supplier_name`
- `spec`
- `vessel_tugboat`, `barge`
- `no_jadwal`
- `id_bbo_no_pengiriman`, `id_bbo_trans`
- `no_shipment`
- `time_arrival`, `completed`
- `completed_year`, `completed_month`
- `tonase_po`, `tonase_po_1000`
- `inventory_price`, `freight_inventory_fob`, `total`

### PUT `/api/po-batubara/{po_id}`
### DELETE `/api/po-batubara/{po_id}`
### DELETE `/api/po-batubara`
### POST `/api/upload/po-batubara`

---

## 8. Merit Order

### GET `/api/merit-order`
Mengambil daftar merit order.

### GET `/api/merit-order/periods`
Daftar periode yang tersedia.

### GET `/api/merit-order/{mo_id}`
Detail merit order.

### POST `/api/merit-order`
Tambah merit order.

**Body utama `MeritOrderCreate`:**
- `periode`
- `periode_year`
- `periode_month`
- `pemasok`
- `moda`
- `tipikal_kcal_kg`
- `jenis_kontrak`
- `harga_batubara`
- `harga_freight`
- `harga_cif`
- `rp_kg`
- `rp_kcal`

### PUT `/api/merit-order/{mo_id}`
### DELETE `/api/merit-order/{mo_id}`
### DELETE `/api/merit-order`
### POST `/api/upload/merit-order`

---

## 9. Supplier Lookup dan Dashboard

### GET `/api/suppliers`
Daftar supplier untuk dropdown/filter laporan.

**Auth:** Ya

### GET `/api/dashboard/stats`
Statistik ringkas dashboard.

**Response utama:**
- `total_vessel`
- `total_barge`
- `total_trucking`
- `total_biomassa`
- `total_tonase_batubara`
- `total_tonase_biomassa`
- `avg_gcv`
- `recent_shipments`
- `monthly_trend`
- `supplier_stats`

### GET `/api/dashboard/advanced`
Data visualisasi advanced dashboard.

**Response utama:**
- `total_ds_mt`
- `total_tonase_po`
- `contract_percentage`
- `fuel_composition`
- `gcv_trend`
- `supplier_economy`
- `slagging_matrix`
- `six_months_summary`
- `available_periods`
- `available_moda`

---

## 10. AI Intelligence API

## 10.1 Main Query

### POST `/api/ai/query`
Mengirim pertanyaan ke AI.

**Auth:** Ya  
**Body `AIQueryRequest`:**
```json
{
  "query": "Analisis supplier dengan deviasi terbesar",
  "module": "general",
  "session_id": "optional-uuid",
  "parameters": {}
}
```

**Module yang umum digunakan:**
- `general`
- `blending`
- `boiler_risk` / `boiler`
- `contract`
- `logistics`
- `smart-stock`
- `coa`

**Response utama:**
- teks jawaban AI
- metadata sesi jika ada

### GET `/api/ai/history`
Mengambil riwayat chat AI model lama.

### DELETE `/api/ai/history`
Menghapus riwayat AI model lama.

### GET `/api/ai/settings`
Mengambil pengaturan AI user aktif.

### PUT `/api/ai/settings`
Menyimpan pengaturan AI user aktif.

**Body:**
```json
{
  "custom_api_key": "optional",
  "llm_provider": "gemini",
  "llm_model": "gemini-2.5-flash"
}
```

## 10.2 Quick Insight Endpoints

### GET `/api/ai/quick/blending-suggestion`
**Query param:** `target_gcv` (default `4000`)

### GET `/api/ai/quick/boiler-alerts`
Ringkasan alert boiler dari data kualitas.

### GET `/api/ai/quick/contract-status`
Ringkasan status kontrak dan pemenuhan PO.

### GET `/api/ai/quick/logistics-losses`
Analisis loss logistik berdasarkan data BL vs DS.

### GET `/api/ai/quick/smart-stock`
Ringkasan stok pintar / persediaan dari smart stock.

### GET `/api/ai/quick/coa-alerts`
Ringkasan alert COA reconciliation.

## 10.3 Session Memory

### GET `/api/ai/sessions`
List sesi percakapan.

**Query params:**
- `page`
- `page_size`

### GET `/api/ai/sessions/{session_id}`
Detail percakapan per sesi.

### DELETE `/api/ai/sessions/{session_id}`
Hapus sesi percakapan.

### POST `/api/ai/sessions/new`
Membuat sesi baru.

---

## 11. Smart Stock API

## 11.1 Sumber Penerimaan

### GET `/api/smart-stock`
Mengambil data smart stock.

**Query params:**
- `limit` (default `100`, max `50000`)
- `start_date` (opsional, format `YYYY-MM-DD`)
- `end_date` (opsional, format `YYYY-MM-DD`)

**Response utama:**
```json
{
  "data": [],
  "recent_30_days": [],
  "supplier_totals": {},
  "total_count": 0
}
```

### POST `/api/smart-stock/entry`
Input manual smart stock.

**Body `SmartStockEntry`:**
```json
{
  "date": "2026-01-30",
  "stock_awal": 1000,
  "suppliers": {
    "RIAU_MITRA": { "A": 100, "B": 200, "C": 50 }
  },
  "total_penerimaan": 350
}
```

### POST `/api/smart-stock/upload`
Upload Excel smart stock.

**Content-Type:** `multipart/form-data`

### DELETE `/api/smart-stock/{entry_id}`
Hapus satu entry smart stock.

### DELETE `/api/smart-stock`
Hapus semua entry smart stock.

## 11.2 Sumber Pemakaian

### GET `/api/sumber-pemakaian`
Mengambil data sumber pemakaian.

### POST `/api/sumber-pemakaian/entry`
Input manual sumber pemakaian.

**Body `SumberPemakaianEntry`:**
```json
{
  "date": "2026-01-30",
  "stock_awal": 1000,
  "suppliers": {
    "RIAU_MITRA": {
      "UNIT1": { "A": 20, "B": 10, "C": 5 },
      "UNIT2": { "A": 25, "B": 10, "C": 0 }
    }
  },
  "total_pemakaian": 70
}
```

### POST `/api/sumber-pemakaian/upload`
Upload Excel sumber pemakaian.

### DELETE `/api/sumber-pemakaian`
Hapus semua data sumber pemakaian.

---

## 12. Smart Blending API

### POST `/api/smart-blending/recommend`
Menghasilkan rekomendasi blending berbasis AI.

**Auth:** Ya  
**Body `SmartBlendingRequest`:**
```json
{
  "target_gcv": 4200,
  "max_ash": 5.5,
  "max_sulphur": 0.8,
  "max_total_moisture": 35,
  "max_inherent_moisture": 18,
  "min_volatile_matter": 35,
  "min_fixed_carbon": 25,
  "target_quantity": 5000
}
```

**Sumber data yang dipakai backend:**
- kualitas 6 bulan terakhir dari `vessels`, `barges`, `trucking`
- stok terbaru dari `smartstock`
- harga dari `merit_order`

**Catatan penting:**
- endpoint ini tergantung integrasi LLM
- bila saldo/budget key habis, request dapat gagal walau payload benar

---

## 13. Settings API

### GET `/api/settings/coa`
Mengambil parameter bisnis COA.

### PUT `/api/settings/coa`
Menyimpan parameter bisnis COA.

**Role:** `admin`  
**Body:**
```json
{
  "price_per_kcal_per_ton": 12.5
}
```

---

## 14. COA Reconciliation API

## 14.1 List, KPI, dan Chart

### GET `/api/coa-reconciliation`
Daftar data rekonsiliasi COA.

**Query params:**
- `page` (default `1`)
- `page_size` (default `50`, max `50000`)
- `status` (`all` / status tertentu)
- `search` (shipment atau supplier)
- `date_from` (`YYYY-MM-DD`)
- `date_to` (`YYYY-MM-DD`)

### GET `/api/coa-reconciliation/kpis`
Mengambil KPI deviasi, kerugian, akurasi, dsb.

### GET `/api/coa-reconciliation/trend`
Mengambil data tren GCV.

**Query params:**
- `months` (default `3`, min `1`, max `12`)

### GET `/api/coa-reconciliation/supplier-consistency`
Chart konsistensi supplier.

### GET `/api/coa-reconciliation/dispute-monitor`
Daftar data dispute untuk halaman monitor.

**Query params:**
- `page`
- `page_size`
- `status`

### GET `/api/coa-reconciliation/{record_id}`
Detail 1 record COA reconciliation.

### GET `/api/coa-reconciliation/shipment/{shipment}`
Lookup berdasarkan shipment.

## 14.2 Workflow Dispute / Umpire

### POST `/api/coa-reconciliation/propose-umpire`
Mengajukan umpire untuk record tertentu.

**Role:** `admin`, `operator`  
**Body:**
```json
{
  "reconciliation_id": "uuid",
  "sample_number": "SAMPLE-001",
  "notes": "Deviasi tinggi, perlu verifikasi pihak ketiga"
}
```

### POST `/api/coa-reconciliation/update-umpire-status/{record_id}`
Mengubah status umpire.

**Role:** `admin`, `operator`  
**Query param:** `status`

### POST `/api/coa-reconciliation/submit-umpire-result`
Mengirim hasil umpire final.

**Role:** `admin`, `operator`  
**Body `UmpireResultInput`:**
```json
{
  "reconciliation_id": "uuid",
  "umpire_gcv_arb": 4150,
  "umpire_tm_arb": 28.5,
  "umpire_ash_arb": 4.8,
  "umpire_ts_arb": 0.45,
  "umpire_lab_name": "Lab ABC",
  "umpire_result_date": "2026-01-30",
  "notes": "Hasil final umpire"
}
```

## 14.3 Input Data

### POST `/api/coa-reconciliation/upload`
Upload 3 file COA sekaligus.

**Role:** `admin`, `operator`  
**Content-Type:** `multipart/form-data`

**Field upload:**
- `loading_file`
- `unloading_file`
- `internal_file`

**Perilaku penting:**
- data lama di koleksi COA dihapus
- hasil merge baru disimpan ulang

### POST `/api/coa-reconciliation/manual`
Input manual satu data rekonsiliasi.

**Role:** `admin`, `operator`  
**Body `COAManualInput`:**
- `shipment`
- `suppliers`
- `periode`
- `tb`
- `bg`
- `ds_mt`
- `completed_unloading`
- `loading_*`
- `unloading_*`
- `internal_*`

### DELETE `/api/coa-reconciliation`
Hapus seluruh data COA.

**Role:** `admin`

## 14.4 Export

### GET `/api/coa-reconciliation/export/excel`
Export data COA ke Excel.

**Query params:**
- `status_filter`

### GET `/api/coa-reconciliation/export/pdf`
Export data COA ke PDF.

**Query params:**
- `status_filter`

---

## 15. Contoh Alur Integrasi Frontend

### 15.1 Login lalu ambil list vessel

```bash
API_URL="https://your-domain.com"
TOKEN=$(curl -s -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"adminpassword"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s "$API_URL/api/vessels?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
```

### 15.2 Upload COA batch

```bash
curl -X POST "https://your-domain.com/api/coa-reconciliation/upload" \
  -H "Authorization: Bearer <TOKEN>" \
  -F "loading_file=@Loading.xlsx" \
  -F "unloading_file=@Unloading.xlsx" \
  -F "internal_file=@LabInternal.xlsx"
```

---

## 16. Catatan Developer

- Backend aktif masih sangat bergantung pada `server.py` meski folder `routers/` sudah tersedia.
- Saat menambah endpoint baru, pertahankan pola `/api/*` dan projection MongoDB yang aman (`{"_id": 0}`).
- Untuk endpoint list, pertahankan format paginated agar frontend konsisten.
- Untuk endpoint upload, dokumentasikan field form-data secara eksplisit.
- Untuk endpoint AI, bedakan error aplikasi dengan error budget/kunci integrasi.
