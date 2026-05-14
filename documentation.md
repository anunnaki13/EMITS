# Dokumentasi Teknis Aplikasi

## 1. Gambaran Umum

PLTU Tenayan Fuel Management System adalah aplikasi full-stack untuk digitalisasi proses pengelolaan bahan bakar pembangkit, khususnya batubara dan biomassa. Sistem ini menggabungkan pencatatan operasional, pemrosesan Excel, dashboard analitik, AI intelligence, smart stock, dan quality dispute monitoring dalam satu platform.

Dokumen ini ditujukan untuk developer aplikasi agar memahami:
- ruang lingkup fitur
- arsitektur frontend dan backend
- struktur data dan modul inti
- pola pengembangan fitur baru
- cara menjalankan, menguji, dan memelihara aplikasi

---

## 2. Tujuan Sistem

Tujuan utama aplikasi:
1. Menyatukan data operasional penerimaan bahan bakar dari berbagai moda.
2. Memudahkan input manual dan impor massal via Excel.
3. Menyediakan dashboard dan laporan untuk monitoring harian.
4. Membantu analisis kualitas dan stok melalui AI.
5. Menyediakan workflow COA reconciliation dan dispute umpire.
6. Menjadi fondasi sistem operasional yang dapat terus dikembangkan.

---

## 3. Domain Fitur Lengkap

### 3.1 Otentikasi dan Role
Fitur utama:
- Login
- Register user baru
- Persistensi token di frontend
- Endpoint `me` untuk bootstrap sesi
- Akses berbasis role:
  - `admin`: penuh, termasuk settings, delete all, user management
  - `operator`: CRUD operasional
  - `viewer`: akses baca

Komponen teknis:
- Token JWT
- Password hashing dengan bcrypt
- HTTP Bearer auth pada FastAPI

### 3.2 Rekap Penerimaan Bahan Bakar
Terdapat beberapa modul operasional utama:
- Vessel TNY
- Barge TNY
- Trucking TNY
- Biomassa TNY
- Purchase Order Batubara
- Merit Order

Setiap modul pada umumnya mendukung:
- daftar data
- pencarian/filter dasar
- tambah data manual
- edit data
- hapus data tunggal
- hapus seluruh data tertentu (role tertentu)
- upload Excel
- pagination backend

### 3.3 Dashboard
Dashboard merangkum kondisi operasional melalui statistik dan chart. Tujuannya untuk memberi ringkasan cepat atas kondisi penerimaan, kualitas, dan tren pasokan.

### 3.4 Smart Stock
Submodul:
- Sumber Penerimaan
- Sumber Pemakaian
- Smart Blending AI

Kapabilitas:
- input manual
- upload Excel dengan parser khusus
- visualisasi stok/pemakaian
- rekomendasi blending berbasis AI

### 3.5 AI Intelligence Agent
Kapabilitas:
- chat AI berbasis domain
- session memory per user
- penyimpanan riwayat percakapan di database
- quick analysis tanpa percakapan penuh

Modul AI yang didukung:
- general
- blending
- boiler
- contract
- logistics
- smart stock
- coa reconciliation

Catatan:
- integrasi AI menggunakan OpenRouter melalui `backend/app/ai/openrouter_client.py`
- model default dikontrol oleh `OPENROUTER_DEFAULT_MODEL`
- jika key user tidak di-set, backend akan mencoba memakai `OPENROUTER_API_KEY`

### 3.6 COA Reconciliation & Dispute Monitor
Fitur inti:
- upload batch 3 file COA
- input manual
- tabel triple check
- KPI deviasi dan kerugian potensial
- chart tren GCV
- chart konsistensi supplier
- detail per record dengan chart radar/spider
- propose umpire
- dispute monitor
- input hasil umpire
- export PDF dan Excel

Ini adalah salah satu domain bisnis paling penting dalam aplikasi karena menghubungkan kualitas batubara ke dampak finansial dan proses dispute supplier.

### 3.7 Laporan
Fitur:
- memilih sumber data laporan
- filter supplier
- export
- tampilan agregat untuk kebutuhan pelaporan operasional

### 3.8 Settings
Fitur admin:
- pengaturan AI/LLM
- pengaturan parameter COA
- manajemen user

---

## 4. Arsitektur Tingkat Tinggi

```text
[ Browser / Frontend React ]
          |
          | axios -> /api/*
          v
[ FastAPI Backend ]
  - auth
  - CRUD operasional
  - upload Excel
  - laporan
  - AI orchestration
  - COA reconciliation
          |
          | Motor
          v
[ MongoDB ]

Tambahan integrasi:
- OpenRouter LLM
- ReportLab / xlsx export engine
```

Karakter arsitektur saat ini:
- Frontend dan backend dipisah jelas.
- Komunikasi utama memakai JSON via REST API.
- Backend sudah memiliki fondasi modular (`routers`, `services`, `utils`), namun entrypoint `server.py` masih monolitik dan memuat mayoritas route aktif.
- MongoDB dipakai sebagai penyimpanan utama untuk data operasional, settings, dan riwayat AI.

---

## 5. Arsitektur Frontend

### 5.1 Teknologi
- React 19
- React Router 7
- Tailwind CSS
- Shadcn/UI
- Axios
- Recharts
- jsPDF / xlsx

### 5.2 Struktur Folder Utama

```text
/frontend/src
├── App.js
├── index.js
├── components/
│   ├── Layout.js
│   ├── Pagination.js
│   └── ui/
├── contexts/
│   └── AuthContext.js
├── hooks/
├── lib/
└── pages/
    ├── Login.js
    ├── Dashboard.js
    ├── VesselPage.js
    ├── BargePage.js
    ├── TruckingPage.js
    ├── BiomassaPage.js
    ├── POBatubaraPage.js
    ├── MeritOrderPage.js
    ├── SmartStockPage.js
    ├── SumberPemakaianPage.js
    ├── SmartBlendingPage.js
    ├── AIIntelligencePage.js
    ├── LaporanPage.js
    ├── COAReconciliationPage.js
    ├── DisputeMonitorPage.js
    └── SettingsPage.js
```

### 5.3 Pola Frontend Saat Ini
- Routing dipusatkan di `src/App.js`
- Gate akses memakai `ProtectedRoute`
- State auth dipusatkan pada `AuthContext`
- Setiap page umumnya bertanggung jawab atas:
  - fetch data
  - form state
  - tindakan CRUD
  - notifikasi sukses/gagal
  - rendering tabel/chart/dialog

### 5.4 Layout dan Navigasi
`Layout.js` mengatur:
- sidebar desktop/mobile
- menu dropdown untuk Rekap Penerimaan BB
- menu dropdown untuk Smart Stock
- menu dropdown untuk COA Reconciliation
- logout dan identitas user

Navigasi utama aplikasi:
- Dashboard
- Rekap Penerimaan BB
- Smart Stock
- Laporan
- COA Reconciliation
- AI Intelligence
- Settings

### 5.5 Auth Flow Frontend
`AuthContext.js`:
- membaca token dari `localStorage`
- memvalidasi token dengan `/api/auth/me`
- menyediakan helper `getAuthHeader()`
- mengelola login, register, dan logout

Konvensi penting:
- seluruh call frontend harus menggunakan `process.env.REACT_APP_BACKEND_URL`
- seluruh endpoint backend diakses melalui prefix `/api`

---

## 6. Arsitektur Backend

### 6.1 Teknologi
- FastAPI
- Motor untuk MongoDB async
- Pandas / OpenPyXL / xlrd untuk parsing Excel
- ReportLab untuk export PDF
- bcrypt + JWT untuk auth
- OpenRouter client untuk LLM

### 6.2 Struktur Folder Utama

```text
/backend
├── server.py
├── requirements.txt
├── models/
├── routers/
│   ├── auth.py
│   ├── ai.py
│   └── data.py
├── services/
│   ├── coa_reconciliation.py
│   └── excel_parser.py
├── utils/
│   ├── auth.py
│   └── database.py
└── tests/
    ├── test_coa_reconciliation.py
    ├── test_dashboard_advanced.py
    ├── test_merit_order.py
    └── test_po_batubara.py
```

### 6.3 Kondisi Backend Saat Ini
Walau folder modular sudah tersedia, aplikasi masih banyak bergantung pada `server.py` sebagai pusat:
- definisi model Pydantic
- setup FastAPI
- koneksi database
- route auth/data/dashboard/AI/COA/export
- helper domain tertentu

Implikasinya:
- onboarding developer baru lebih berat
- konflik perubahan lebih besar
- pengujian unit per modul lebih sulit
- refactoring modular adalah prioritas teknis penting

### 6.4 Koneksi Database
Pola saat ini:
- `MONGO_URL` dibaca dari `.env`
- database dipilih dengan `DB_NAME`
- menggunakan `AsyncIOMotorClient`
- koleksi diakses langsung dari object `db`

Prinsip penting saat bekerja dengan MongoDB:
- jangan kembalikan field `_id` mentah ke response JSON
- gunakan projection `{"_id": 0}` saat query
- hati-hati dengan object hasil insert/update karena MongoDB dapat menyisipkan `_id`
- simpan `datetime` dalam format ISO string saat perlu konsistensi serialisasi

---

## 7. Model Data Konseptual

Berikut model konseptual utama yang digunakan aplikasi.

### 7.1 Users
Field utama:
- `id`
- `email`
- `password`
- `name`
- `role`
- `created_at`

### 7.2 Data Operasional Rekap Penerimaan
Koleksi utama:
- `vessels`
- `barges`
- `trucking`
- `biomassa`
- `po_batubara`
- `merit_order`

Ciri umum:
- `id`
- field domain operasional
- `created_at`
- `created_by`

### 7.3 Smart Stock
Koleksi yang relevan:
- smart stock penerimaan
- sumber pemakaian

Ciri data:
- tanggal
- stock awal
- total penerimaan atau burn
- detail supplier / unit
- stock akhir atau detail pemakaian

### 7.4 COA Reconciliation
Field penting berdasarkan implementasi aktif:
- `id`
- `shipment`
- `supplier`
- `completed_unloading`
- `loading_gcv_arb`
- `unloading_gcv_arb`
- `internal_gcv_arb`
- `delta_loading_internal`
- `status`
- `umpire_status`

### 7.5 Settings
Field yang diketahui:
- `type: "coa"`
- `price_per_kcal_per_ton`

### 7.6 User Settings
Dipakai untuk pengaturan AI per user, termasuk kemungkinan custom API key.

### 7.7 AI Conversations
Dipakai untuk memory percakapan:
- `session_id`
- `user_id`
- `messages[]`
- `created_at`
- `updated_at`
- `module`

---

## 8. Peta API Utama

Berikut peta endpoint yang relevan untuk developer. Daftar ini fokus pada endpoint inti yang paling penting dipahami.

### 8.1 Health dan Root
- `GET /api/`
- `GET /api/health`

### 8.2 Auth
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

### 8.3 Data Operasional
- `GET /api/vessels`
- `POST /api/vessels`
- `PUT /api/vessels/{id}`
- `DELETE /api/vessels/{id}`
- `DELETE /api/vessels`

- `GET /api/barges`
- `POST /api/barges`
- `PUT /api/barges/{id}`
- `DELETE /api/barges/{id}`
- `DELETE /api/barges`

- `GET /api/trucking`
- `POST /api/trucking`
- `PUT /api/trucking/{id}`
- `DELETE /api/trucking/{id}`
- `DELETE /api/trucking`

- `GET /api/biomassa`
- `POST /api/biomassa`
- `PUT /api/biomassa/{id}`
- `DELETE /api/biomassa/{id}`
- `DELETE /api/biomassa`

Selain itu terdapat endpoint domain lain untuk:
- purchase order batubara
- merit order
- upload Excel (`/api/upload/*`)
- supplier lookup
- dashboard statistik

### 8.4 Smart Stock
- `GET /api/smart-stock`
- `POST /api/smart-stock/entry`
- `POST /api/smart-stock/upload`
- `DELETE /api/smart-stock`

- `GET /api/sumber-pemakaian`
- `POST /api/sumber-pemakaian/entry`
- `POST /api/sumber-pemakaian/upload`
- `DELETE /api/sumber-pemakaian`

### 8.5 Smart Blending AI
- `POST /api/smart-blending/recommend`

Catatan operasional:
- fitur ini tergantung `OPENROUTER_API_KEY`, model default, dan kuota provider
- kegagalan provider atau kuota harus ditangani sebagai dependency operasional, bukan bug logika aplikasi

### 8.6 AI Intelligence
- `POST /api/ai/query`
- `GET /api/ai/sessions`
- `GET /api/ai/sessions/{session_id}`
- `DELETE /api/ai/sessions/{session_id}`
- `POST /api/ai/sessions/new`
- quick endpoints, misalnya:
  - `/api/ai/quick/blending-suggestion`
  - `/api/ai/quick/boiler-alerts`
  - `/api/ai/quick/contract-status`
  - `/api/ai/quick/logistics-losses`
  - `/api/ai/quick/smart-stock`
  - `/api/ai/quick/coa-alerts`

### 8.7 COA Reconciliation
- `GET /api/coa-reconciliation`
- `GET /api/coa-reconciliation/kpis`
- `GET /api/coa-reconciliation/trend`
- `GET /api/coa-reconciliation/supplier-consistency`
- `GET /api/coa-reconciliation/{id}`
- `POST /api/coa-reconciliation/upload`
- `POST /api/coa-reconciliation/manual`
- `POST /api/coa-reconciliation/propose-umpire`
- `GET /api/coa-reconciliation/dispute-monitor`
- `POST /api/coa-reconciliation/update-umpire-status/{id}`
- `POST /api/coa-reconciliation/submit-umpire-result`
- `DELETE /api/coa-reconciliation`
- `GET /api/coa-reconciliation/export/excel`
- `GET /api/coa-reconciliation/export/pdf`

### 8.8 Settings
- `GET /api/settings/coa`
- `PUT /api/settings/coa`
- `GET /api/ai/settings`
- `PUT /api/ai/settings`
- `GET /api/users`

---

## 9. Flow Sistem Penting

### 9.1 Flow Login
1. User login dari frontend.
2. Frontend memanggil `POST /api/auth/login`.
3. Backend memvalidasi password bcrypt.
4. Backend mengembalikan JWT.
5. Frontend menyimpan token di `localStorage`.
6. Saat reload, frontend memanggil `GET /api/auth/me` untuk memulihkan sesi.

### 9.2 Flow CRUD Data Operasional
1. User membuka salah satu halaman data.
2. Frontend melakukan fetch list ke endpoint domain terkait.
3. Backend mengembalikan struktur paginated: `items`, `total`, `page`, `page_size`, `total_pages`.
4. Frontend harus membaca `response.data.items`, bukan mengasumsikan array langsung.
5. Aksi create/update/delete dilakukan dengan token bearer.

### 9.3 Flow Upload Excel
1. User mengunggah file Excel dari UI.
2. Frontend mengirim `multipart/form-data` ke endpoint upload.
3. Backend membaca file bytes.
4. Service parser memetakan header kompleks dan nilai per baris.
5. Hasil parsing disimpan ke MongoDB.
6. Frontend refresh daftar data.

### 9.4 Flow Smart Blending AI
1. User memilih/menyediakan parameter blending.
2. Frontend memanggil endpoint recommendation.
3. Backend menyiapkan prompt dan context data.
4. Backend memanggil LLM melalui OpenRouter.
5. Hasil rekomendasi dikembalikan ke frontend.

Risiko operasional:
- jika kuota atau provider LLM tidak tersedia, fitur gagal walau kode benar
- perlu monitoring kuota OpenRouter pada environment pengguna

### 9.5 Flow AI Intelligence dengan Memory
1. Frontend mengirim query dan `session_id` opsional.
2. Backend membuat session baru jika belum ada.
3. Backend menarik konteks pesan terakhir dari MongoDB.
4. Backend membangun prompt final.
5. Model AI menghasilkan jawaban.
6. Pesan user dan assistant disimpan ke `ai_conversations`.

### 9.6 Flow COA Reconciliation
1. Data COA dimasukkan melalui upload batch atau input manual.
2. Backend menyimpan dan menghitung indikator deviasi.
3. Halaman utama menampilkan KPI, tabel, chart, dan detail.
4. Jika ditemukan anomali, user dapat memicu `propose umpire`.
5. Dispute Monitor melacak status sampai hasil umpire masuk.
6. Setelah final, data dapat diexport ke Excel/PDF.

---

## 10. Pengembangan Lokal

### 10.1 Prasyarat
- Python 3.11+
- Node.js + Yarn
- MongoDB

### 10.2 Environment Variable

#### Frontend
Diperlukan:
- `REACT_APP_BACKEND_URL`

#### Backend
Diperlukan minimal:
- `MONGO_URL`
- `DB_NAME`
- `JWT_SECRET`
- `CORS_ORIGINS`
- `OPENROUTER_API_KEY` (jika memakai default key global)

### 10.3 Menjalankan Frontend
```bash
cd /app/frontend
yarn install
yarn start
```

### 10.4 Menjalankan Backend
```bash
cd /app/backend
pip install -r requirements.txt
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

### 10.5 Menjalankan Test
```bash
cd /app/backend
pytest tests -q
```

---

## 11. Konvensi Pengembangan

### 11.1 Konvensi Frontend
- Gunakan `REACT_APP_BACKEND_URL` untuk semua panggilan API.
- Selalu akses backend dengan prefix `/api`.
- Komponen UI utamakan dari Shadcn/UI.
- Untuk perubahan UI penting, tambahkan `data-testid` pada elemen interaktif dan elemen informasi kritikal.
- Page sebaiknya tidak semakin besar; arah refactor ke reusable component.

### 11.2 Konvensi Backend
- Gunakan projection `{"_id": 0}` untuk response MongoDB.
- Simpan waktu dengan `datetime.now(timezone.utc)`.
- Hindari mengembalikan ObjectId mentah.
- Pisahkan logic parsing, business rule, dan route saat melakukan refactor baru.
- Semua route eksternal harus berada di bawah `/api`.

### 11.3 Strategi Modularisasi yang Disarankan
Urutan refactor yang aman:
1. ekstrak auth dan dependency role
2. ekstrak route laporan / dashboard
3. ekstrak route COA reconciliation
4. ekstrak route smart stock
5. ekstrak model Pydantic ke package `models`
6. ekstrak service dan repository layer bila diperlukan

### 11.4 Strategi Menambah Fitur Baru
Jika menambah modul baru, langkah aman:
1. definisikan use case bisnis
2. tentukan koleksi MongoDB dan response model
3. buat endpoint backend dengan projection aman
4. buat halaman frontend + integrasi auth header
5. tambahkan menu navigasi
6. tambahkan export/filter bila relevan
7. tambahkan test backend atau test e2e
8. dokumentasikan perubahan

---

## 12. Area Teknis yang Perlu Diperhatikan

### 12.1 Technical Debt Saat Ini
1. `server.py` masih terlalu besar.
2. Beberapa halaman frontend masih memuat logika fetch/form/render dalam satu file besar.
3. Standar pagination belum sepenuhnya seragam di semua domain lama.
4. Cakupan test belum merata untuk seluruh modul.

### 12.2 Known Issues
- Tidak ada blocker produk aktif yang tercatat setelah v1.4.
- Caveat operasional utama: fitur AI membutuhkan key/kuota OpenRouter valid, runtime evidence VPS perlu disimpan oleh operator, dan workbook baru harus tetap lewat import preview sebelum apply.

### 12.3 Risiko Refactor
Saat memodularisasi backend, area yang paling rawan regresi:
- dependency auth dan role
- pagination format `items`
- export endpoint
- upload multipart/form-data
- serialisasi data MongoDB

---

## 13. File Penting yang Perlu Dipahami Developer

### Backend
- `/app/backend/server.py` — entrypoint utama dan sumber sebagian besar endpoint
- `/app/backend/routers/auth.py` — auth modular awal
- `/app/backend/routers/ai.py` — session memory AI modular awal
- `/app/backend/routers/data.py` — CRUD modular awal untuk domain penerimaan tertentu
- `/app/backend/services/excel_parser.py` — parser Excel smart stock
- `/app/backend/services/coa_reconciliation.py` — logic domain COA
- `/app/backend/utils/database.py` — koneksi DB dan JWT constants

### Frontend
- `/app/frontend/src/App.js` — routing utama
- `/app/frontend/src/components/Layout.js` — shell aplikasi dan navigasi
- `/app/frontend/src/contexts/AuthContext.js` — state auth aplikasi
- `/app/frontend/src/pages/*.js` — implementasi tiap domain bisnis

### Dokumen Tambahan
- `/app/frontend/public/docs/Smart_Blending_AI_Formula.md` — dokumen formula Smart Blending AI
- `/app/memory/PRD.md` — ringkasan kebutuhan dan progres implementasi internal

---

## 14. Strategi Testing yang Disarankan

### Backend
Prioritas test:
- auth flow
- pagination shape
- upload Excel
- COA reconciliation KPI dan export
- AI endpoints yang tidak butuh live budget atau dapat di-mock secara aman

### Frontend
Prioritas test:
- login
- load halaman data besar
- submit form create/edit
- export button
- filter supplier laporan
- halaman COA dan Dispute Monitor

### Regression Checklist Manual
- login berhasil
- halaman vessel/barge/trucking/biomassa tidak blank
- pagination membaca `response.data.items`
- halaman laporan dapat filter supplier
- export COA PDF/Excel berhasil
- AI quick insight tetap load

---

## 15. Roadmap Teknis yang Direkomendasikan

### P0
- Jaga stabilitas modul operasional dan COA
- Pastikan dependency OpenRouter, runtime evidence VPS, dan import governance terpantau

### P1
- Modularisasi `server.py`
- Tambah test coverage untuk auth, laporan, smart stock, AI sessions
- Pecah page frontend besar menjadi komponen reusable

### P2
- Standardisasi DTO/schema lintas domain
- Rework service layer untuk domain besar
- Perbaikan observability dan log error domain

### P3
- CI/CD atau GitHub Actions release gate
- Persisted data-quality snapshots dan forecasting historis
- Multi-provider LLM routing dan budget tracking per user

---

## 16. Kesimpulan

Aplikasi ini sudah mencakup domain operasional yang cukup luas dan bernilai tinggi untuk pengelolaan bahan bakar PLTU. Fondasi bisnisnya kuat: CRUD operasional, dashboard, smart stock, AI, pelaporan, dan COA dispute sudah tersedia. Fokus pengembangan berikutnya sebaiknya bukan menambah terlalu banyak fitur baru, tetapi menurunkan technical debt, menambah test coverage, dan memodularisasi backend agar maintainable untuk jangka panjang.

---

## 17. Dokumen Tambahan

Dokumen pendukung developer yang tersedia di root project:
- `readme.md`
- `documentation.md`
- `API_REFERENCE.md`
- `DATABASE_SCHEMA.md`
- `DEPLOYMENT_GUIDE.md`
- `frontend/public/docs/Smart_Blending_AI_Formula.md`


## Known Issues

Operational state of the system as of 2026-05-14 after v1.4. New issues land
here with a status badge: `**[mitigated]**` (impact contained but root cause
upstream), `**[accepted]**` (verified non-impactful today), or `**[closed]**`
(resolved by a shipped phase). The readme points here as the canonical
operator-facing surface.

- **[mitigated]** Login: `ResizeObserver loop completed with undelivered notifications`
  console emission on the register tab. Root cause is upstream in `@radix-ui/react-select`
  Tabs-content remount machinery. Suppressed at the page level by
  `frontend/public/index.html:49-65`. Login contract path is regression-protected
  by `backend/tests/test_auth_session.py::test_login_then_me_rehydrates_same_user`
  (Phase-2 plan 02-02). Full disposition + Phase-3 follow-up (Radix upgrade
  evaluation): see `docs/audit/LOGIN_BUG_RESOLUTION.md`. (Cite: `docs/audit/LOGIN_BUG_RESOLUTION.md`,
  `docs/audit/AUTH_CONTRACT.md`, `.planning/decisions/ADR-004-jwt-bcrypt-three-role-auth.md`)

- **[accepted]** AI provider dependency: Smart Blending and AI Intelligence now
  use OpenRouter through `OPENROUTER_API_KEY`, with fake-client regression
  coverage for tests. Live recommendations still depend on a valid provider
  key, selected model, and available quota. If provider calls fail, operators
  should check runtime settings and provider balance before treating it as an
  application defect. (Cite: `.planning/decisions/ADR-005-openrouter-ai-provider.md`,
  `backend/app/ai/openrouter_client.py`, `backend/tests/test_openrouter_client.py`)

- **[closed]** Excel/COA data refresh: recurring combined COA workbook imports
  are previewable and rollback-safe, and the March 2026 COA update is documented
  in `docs/data/coa-maret-2026-import.md`. New workbook formats still require
  preview review before apply. (Cite: `backend/scripts/import_coa_workbook.py`,
  `backend/scripts/sync_coa_realisasi.py`, `docs/data/coa-maret-2026-import.md`)

- **[closed]** Collection naming debt: canonical collection decisions are locked
  in ADR-009..ADR-012, code reads were migrated, and regression coverage blocks
  reintroducing legacy reads. (Cite: `.planning/decisions/ADR-009-canonical-smartstock.md`,
  `.planning/decisions/ADR-010-canonical-sumberpemakaian.md`,
  `.planning/decisions/ADR-011-canonical-app-settings.md`,
  `.planning/decisions/ADR-012-canonical-ai-chat-history.md`,
  `backend/tests/test_clean_checkout_gate.py`)

- **[accepted]** Audit-probe synthetic users: 3 `audit-probe-*@audit-probes-2026.com`
  users were inserted into the live `users` collection during Phase-1 plan
  01-04 register-flow audit. Verified clean as of 2026-05-10 (live count 0).
  Phase-2 conftest cleanup fixture (`backend/tests/conftest.py`) re-runs the
  anchor-prefixed deletion on every test session; documented for record only —
  no active leak today. (Cite: `docs/audit/LOGIN_BUG_RESOLUTION.md` lines 75-77,
  `.planning/phases/02-authentication-stabilization/VERIFICATION.md` SS-05)

### Adding a new entry

1. Pick the status badge (`mitigated`, `accepted`, or `closed`).
2. One paragraph: what the user observes, what the root cause is, what the
   mitigation or schedule is.
3. Cite at least one source file (relative path from repo root).
4. Commit on the inner repo with subject `docs(known-issues): add <slug>`.
