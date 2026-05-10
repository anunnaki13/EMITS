# PLTU Tenayan Fuel Management System

Aplikasi full-stack untuk manajemen penerimaan bahan bakar, pemantauan kualitas batubara, rekonsiliasi COA, pelaporan operasional, dan analitik AI di lingkungan PLTU Tenayan.

## Ringkasan

Sistem ini dibangun untuk membantu tim operasional, admin, dan developer mengelola data penerimaan batubara/biomassa dari berbagai jalur logistik, memonitor kualitas bahan bakar, menghasilkan laporan, serta menjalankan analisis berbasis AI untuk stok, blending, kontrak, boiler, dan dispute quality control.

> **Status terkini:** lihat [Known Issues](documentation.md#known-issues) untuk login-bug status, Smart Blending AI budget, dan parser Excel verification status.

## Fitur Utama

### 1. Otentikasi dan Otorisasi
- Login dan register berbasis JWT
- Role-based access control: `admin`, `operator`, `viewer`
- Halaman pengaturan dibatasi untuk admin

### 2. Rekap Penerimaan Bahan Bakar
- CRUD dan pencarian untuk:
  - Vessel TNY
  - Barge TNY
  - Trucking TNY
  - Biomassa TNY
  - Purchase Order Batubara
  - Merit Order
- Upload Excel untuk impor data operasional
- Pagination backend untuk dataset besar

### 3. Dashboard Operasional
- Statistik ringkas
- Visualisasi lanjutan untuk kondisi data dan performa pasokan
- Ringkasan cepat untuk kebutuhan monitoring harian

### 4. Smart Stock
- Modul Sumber Penerimaan
- Modul Sumber Pemakaian
- Smart Blending AI untuk rekomendasi pencampuran batubara
- Import Excel dengan parser khusus untuk format sheet operasional

### 5. AI Intelligence Agent
- Chat AI berbasis modul domain
- Riwayat percakapan per sesi
- Modul analisis:
  - General
  - Blending
  - Boiler
  - Contract
  - Logistics
  - Smart Stock
  - COA Reconciliation
- Quick insights berbasis data aplikasi

### 6. COA Reconciliation & Dispute Monitor
- Triple check kualitas batubara dari loading, unloading, dan internal lab
- KPI deviasi dan estimasi potensi kerugian
- Chart tren dan konsistensi supplier
- Workflow propose umpire
- Dispute monitor dan input hasil umpire
- Export hasil rekonsiliasi ke PDF dan Excel

### 7. Laporan dan Export
- Halaman laporan lintas data operasional
- Filter supplier
- Export PDF/Excel

### 8. Pengaturan Sistem
- Pengaturan AI/LLM per user
- Pengaturan COA berbasis parameter bisnis
- Manajemen user oleh admin

## Arsitektur Singkat

```text
Frontend (React + Tailwind + Shadcn/UI)
        |
        | HTTPS / JSON
        v
Backend API (/api) - FastAPI
        |
        | Async driver (Motor)
        v
MongoDB
        |
        +--> LLM Integration (Gemini via Emergent Integrations)
        +--> Export Engine (ReportLab / XLSX)
```

## Struktur Proyek

```text
/app
├── backend
│   ├── server.py                # Entry point utama FastAPI, masih memuat mayoritas route
│   ├── routers/                 # Cikal bakal modularisasi route
│   ├── services/                # Layanan domain, parser Excel, COA service
│   ├── utils/                   # Utilitas DB dan auth
│   └── tests/                   # Test backend yang sudah tersedia
├── frontend
│   ├── public/                  # Asset publik dan file unduhan
│   └── src/
│       ├── components/          # Layout, pagination, dan komponen UI
│       ├── contexts/            # AuthContext
│       └── pages/               # Seluruh halaman aplikasi
├── memory/                      # PRD, kredensial testing, catatan internal
├── README.md
└── documentation.md
```

## Tech Stack

### Frontend
- React 19
- React Router 7
- Tailwind CSS
- Shadcn/UI
- Axios
- Recharts
- jsPDF
- xlsx

### Backend
- FastAPI
- Motor (MongoDB async)
- Pandas
- OpenPyXL / xlrd
- ReportLab
- JWT (`python-jose` / `PyJWT` + bcrypt)
- emergentintegrations

### Database
- MongoDB

## Environment Variable Penting

### Frontend
- `REACT_APP_BACKEND_URL` — base URL backend yang dipanggil frontend

### Backend
- `MONGO_URL` — koneksi MongoDB
- `DB_NAME` — nama database
- `JWT_SECRET` — secret JWT
- `CORS_ORIGINS` — daftar origin yang diizinkan
- `EMERGENT_LLM_KEY` — kunci LLM default bila user tidak memakai custom key

## Menjalankan Aplikasi

### Frontend
```bash
cd /app/frontend
yarn install
yarn start
```

### Backend
```bash
cd /app/backend
pip install -r requirements.txt
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

## Pengujian

Jalankan test backend yang tersedia:

```bash
cd /app/backend
pytest tests -q
```

## Dokumentasi Lengkap

Untuk dokumentasi teknis yang lebih lengkap, lihat file berikut:
- [`documentation.md`](./documentation.md)
- [`API_REFERENCE.md`](./API_REFERENCE.md)
- [`DATABASE_SCHEMA.md`](./DATABASE_SCHEMA.md)
- [`DEPLOYMENT_GUIDE.md`](./DEPLOYMENT_GUIDE.md)
- [`frontend/public/docs/Smart_Blending_AI_Formula.md`](./frontend/public/docs/Smart_Blending_AI_Formula.md)

## Catatan Teknis Saat Ini
- `backend/server.py` masih sangat besar dan perlu dipecah ke router modular
- Struktur pagination backend/frontend sudah lebih stabil, tetapi masih perlu standardisasi penuh
- Smart Blending AI dapat gagal bila saldo Universal Key habis (`BudgetExceededError`)
- Verifikasi parser Excel `total penerimaan.xlsx` masih menunggu file contoh aktual

## Arah Pengembangan Berikutnya
- Modularisasi route FastAPI secara bertahap
- Reusable component untuk halaman data frontend
- Backup & restore data
- Toggle dark/light mode
