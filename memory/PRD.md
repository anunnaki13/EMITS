# PRD: Sistem Manajemen Bahan Bakar Digital PLTU Tenayan

## Overview
Sistem digital untuk mengelola rekapitulasi penerimaan batubara dan biomassa di PLTU Tenayan, dilengkapi dengan AI Intelligence Agent untuk analisis data.

## User Personas
1. **Admin** - Akses penuh, kelola pengguna, hapus data, pengaturan AI
2. **Operator** - Input data, edit, upload Excel, akses AI
3. **Viewer** - Hanya melihat data dan laporan

## Core Requirements (Static)
- Dashboard dengan statistik real-time dan visualisasi advanced
- CRUD untuk 6 kategori: Vessel TNY, Barge TNY, Trucking TNY, Biomassa TNY, Purchase Order Batubara, Merit Order
- Upload Excel dengan auto-parsing
- Role-based access control
- Export laporan PDF/Excel
- **AI Intelligence Agent** dengan 4 modul analisis
- **COA Reconciliation & Dispute Monitor** - Rekonsiliasi kualitas batubara dari 3 sumber
- Interface Bahasa Indonesia
- Dark Mode SaaS Dashboard UI

## What's Been Implemented ✅
*Last Updated: January 30, 2026*

### Backend (FastAPI)
- ✅ User authentication (JWT)
- ✅ Role-based authorization
- ✅ CRUD endpoints untuk semua kategori
- ✅ Excel upload & parsing untuk semua kategori
- ✅ Dashboard statistics API & Advanced Dashboard API
- ✅ **AI Intelligence API** - /api/ai/query dengan 7 modul (termasuk Smart Stock & COA)
- ✅ **AI Quick Analysis Endpoints** - blending, boiler alerts, contract status, logistics losses, smart-stock, coa-alerts
- ✅ **AI Settings API** - Custom API key management
- ✅ **Smart Stock Management API** - GET, POST, Upload Excel, Delete endpoints
- ✅ **Sumber Pemakaian API** - GET, POST, Upload Excel, Delete endpoints
- ✅ **Smart Blending AI API** - /api/smart-blending/recommend
- ✅ **COA Reconciliation API** ✨ ENHANCED:
  - GET /api/coa-reconciliation - Paginated reconciliation data
  - GET /api/coa-reconciliation/kpis - KPI metrics (deviation alerts, potential loss, umpire status)
  - GET /api/coa-reconciliation/trend - GCV trend data for line chart
  - GET /api/coa-reconciliation/supplier-consistency - Supplier deviation data
  - GET /api/coa-reconciliation/{id} - Detail with radar chart data
  - POST /api/coa-reconciliation/upload - Upload 3 COA files
  - POST /api/coa-reconciliation/manual - Input data manual
  - POST /api/coa-reconciliation/propose-umpire - Umpire proposal workflow
  - DELETE /api/coa-reconciliation - Hapus semua data (admin only)
  - **GET /api/coa-reconciliation/export/excel - Export ke Excel** ✨ NEW
  - **GET /api/coa-reconciliation/export/pdf - Export ke PDF** ✨ NEW

### Frontend (React)
- ✅ Login/Register page dengan dark theme
- ✅ **Dashboard Advanced** dengan 7 visualisasi
- ✅ Vessel TNY, Barge TNY, Trucking TNY, Biomassa TNY pages
- ✅ Purchase Order Batubara page
- ✅ Merit Order page
- ✅ **Smart Stock - Sumber Penerimaan** dengan charts dan tabel
- ✅ **Smart Stock - Sumber Pemakaian** dengan KPI dan tabel
- ✅ **Smart Stock - Smart Blending AI** dengan Radar Chart
- ✅ **Tenayan Fuel Intelligence Agent** dengan chat interface
- ✅ Laporan page dengan export PDF/Excel
- ✅ **Settings page** dengan pengaturan AI/LLM API key
- ✅ **COA Reconciliation & Dispute Monitor** ✨ NEW:
  - KPI Dashboard: High Deviation Alert, Potential Loss, Umpire Status, Rata-rata Akurasi
  - Insight Card untuk supplier dengan deviasi tertinggi
  - Line Chart: Tren GCV Triple Comparison (Loading, Unloading, Internal)
  - Bar Chart: Supplier dengan Deviasi Tertinggi
  - Tabel "Triple Check" dengan conditional formatting merah
  - Dialog detail dengan Radar/Spider Chart
  - Umpire Proposal workflow dengan audit trail

### Navigation Structure
```
├── Dashboard (Advanced dengan 7 visualisasi)
├── Rekap Penerimaan BB (Dropdown)
│   ├── Vessel TNY
│   ├── Barge TNY
│   ├── Trucking TNY
│   ├── Biomassa TNY
│   ├── Purchase Order Batubara
│   └── Merit Order
├── Smart Stock (Dropdown)
│   ├── Sumber Penerimaan
│   ├── Sumber Pemakaian
│   └── Smart Blending AI
├── Laporan
├── COA Reconciliation ✨ NEW
├── AI Intelligence
└── Pengaturan (Admin only)
    └── Pengaturan AI/LLM
```

## COA Reconciliation Features ✨
1. **Anomaly Dashboard (KPIs)**
   - High Deviation Alert: Jumlah Lot dengan selisih GCV > 100 kCal/kg
   - Potential Loss (Rp): Estimasi kerugian finansial akibat penurunan kalori
   - Umpire Status: Jumlah kargo dalam proses uji pihak ketiga
   - Rata-rata Akurasi: Persentase akurasi supplier

2. **Triple Check Table** ✨ UPDATED
   - Kolom: Shipment (termasuk format "LOT XXX"), Supplier, Loading GCV, Unloading GCV, Internal GCV, Delta, Status, Umpire, Aksi
   - Conditional Formatting: Baris merah jika delta > 150 kCal/kg
   - Urutan berdasarkan tanggal completed_unloading (terbaru di atas)
   - **Filter Tanggal**: Date range picker untuk filter periode

3. **Data Science Charts**
   - Radar/Spider Chart: Perbandingan profil kualitas dari 3 atau 4 tes (Quad Check jika umpire selesai)
   - Supplier Consistency Chart: Bar chart supplier dengan data tidak sinkron
   - Trend Chart: Line chart tren GCV dari 3 sumber

4. **Dispute Management Workflow** ✨ ENHANCED
   - Automatic Umpire Trigger: Tombol "Propose Umpire" untuk anomali tinggi
   - Audit Trail: Menyimpan nomor sampel dan catatan
   - **Sub-menu Dispute Monitor**: Halaman terpisah untuk monitoring umpire
   - **Input Hasil Umpire**: Form untuk memasukkan hasil tes umpire (GCV, TM, Ash, S, Lab Name, Tanggal)
   - **Quad Check Radar**: Setelah hasil umpire diinput, Radar Chart menampilkan 4 sumber

5. **Input & Manajemen Data**
   - Input Manual: Form untuk menambah data COA secara manual (mendukung format "LOT XXX")
   - Upload Batch: Upload 3 file Excel dengan dialog pemetaan file
   - Hapus Semua: Fitur admin untuk menghapus seluruh data (dengan konfirmasi)

## Prioritized Backlog

### P0 (Critical) - DONE ✅
- [x] User authentication
- [x] Basic CRUD operations
- [x] Dashboard Advanced
- [x] Navigation dropdown restructure
- [x] All data entry pages
- [x] **AI Intelligence Agent**
- [x] **AI Settings in Settings page**
- [x] **Smart Stock Module**
- [x] **Smart Blending AI**
- [x] **Export PDF/Excel**
- [x] **COA Reconciliation & Dispute Monitor** ✅ NEW (Jan 29, 2026)

### P1 (High Priority)
- [x] Server-side pagination ✅ DONE
- [x] Update AI conversation memory with COA features ✅ DONE (Jan 30, 2026)
- [ ] Fix Smart Blending AI Timeout (BadGatewayError) - BLOCKED: LLM budget exhausted
- [ ] Verify Excel Parser with "total penerimaan.xlsx"

### P2 (Medium Priority)
- [ ] Advanced filtering & date range
- [ ] AI conversation memory frontend integration

### P3 (Nice to Have)
- [ ] Dashboard filter by Periode functionality
- [ ] Dark/Light mode toggle
- [ ] Data backup & restore
- [ ] Audit trail / activity log

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, Shadcn/UI, Recharts, Lucide-React, react-markdown
- **Backend**: FastAPI, Motor (MongoDB async), Pandas, Openpyxl, emergentintegrations
- **Database**: MongoDB
- **Auth**: JWT (python-jose, bcrypt)
- **AI**: Gemini via Emergent LLM Key

## Test Credentials
- **Email**: admin@example.com
- **Password**: adminpassword
