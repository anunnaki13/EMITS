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
- Interface Bahasa Indonesia
- Dark Mode SaaS Dashboard UI

## What's Been Implemented ✅
*Last Updated: January 29, 2026*

### Backend (FastAPI)
- ✅ User authentication (JWT)
- ✅ Role-based authorization
- ✅ CRUD endpoints untuk semua kategori
- ✅ Excel upload & parsing untuk semua kategori
- ✅ Dashboard statistics API & Advanced Dashboard API
- ✅ **AI Intelligence API** - /api/ai/query dengan 4 modul
- ✅ **AI Quick Analysis Endpoints** - blending, boiler alerts, contract status, logistics losses
- ✅ **AI Settings API** - Custom API key management
- ✅ **Smart Stock Management API** - GET, POST, Upload Excel, Delete endpoints
- ✅ **Sumber Pemakaian API** - GET, POST, Upload Excel, Delete endpoints
- ✅ **Smart Blending AI API** - /api/smart-blending/recommend dengan:
  - Filter data supplier 6 bulan terakhir
  - Menggunakan API key dari Pengaturan AI Intelligence
  - Parameter constraint sesuai spesifikasi batubara (GCV 3700-4700, Ash 3.3-6%, Sulphur 0.13-2.2%)

### Frontend (React)
- ✅ Login/Register page dengan dark theme
- ✅ **Dashboard Advanced** dengan 7 visualisasi
- ✅ Vessel TNY, Barge TNY, Trucking TNY, Biomassa TNY pages
- ✅ Purchase Order Batubara page
- ✅ Merit Order page
- ✅ **Smart Stock - Sumber Penerimaan** dengan:
  - Area Chart untuk tren Stock Awal (30 hari terakhir)
  - Stacked Bar Chart untuk Total Penerimaan per Supplier
  - Tabel interaktif dengan freeze header
  - Filter tanggal (rentang tanggal)
  - Upload Excel untuk bulk import
  - Form Input Harian manual
  - Export PDF button (placeholder)
  - No Delivery alert untuk hari tanpa penerimaan
- ✅ **Smart Stock - Sumber Pemakaian** dengan:
  - KPI Dashboard (4 kartu: Total Burn Today, Unit 1, Unit 2, Rata-rata)
  - Tabel kompak dengan expandable rows
  - Upload Excel dengan multi-level header parsing
  - Form Input Harian manual
- ✅ **Smart Stock - Smart Blending AI** dengan:
  - Parameter Target sliders (GCV, Ash, Sulphur, Quantity)
  - AI-powered blending recommendations via Gemini
  - Recommendation cards dengan detail supplier asli dari database
  - Radar Chart untuk perbandingan Target vs Predicted
  - Alasan AI dan Analisis Biaya dalam Bahasa Indonesia
- ✅ **Tenayan Fuel Intelligence Agent** dengan:
  - Smart Blending Optimizer modul
  - Boiler Risk Warning modul
  - Contract Compliance & PO Tracker modul
  - Logistic Efficiency & Loss Analysis modul
  - Chat interface dengan markdown rendering
  - Quick Insights panel
  - Suggested queries
- ✅ Laporan page
- ✅ **Settings page** dengan pengaturan AI/LLM API key

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
├── Smart Stock (Dropdown) ✨ NEW
│   ├── Sumber Penerimaan
│   ├── Sumber Pemakaian
│   └── Smart Blending AI
├── Laporan
├── AI Intelligence
└── Pengaturan (Admin only)
    └── Pengaturan AI/LLM
```

## AI Intelligence Agent Modules
1. **General Intelligence** - Pertanyaan umum tentang data
2. **Smart Blending Optimizer** - Optimasi campuran batubara & biomassa
3. **Boiler Risk Warning** - Deteksi risiko slagging/fouling
4. **Contract Compliance** - Monitoring PO & kontrak
5. **Logistics Analysis** - Efisiensi & losses pengiriman
6. **Smart Blending AI** ✨ NEW - Digital Chemist untuk rekomendasi blending optimal berbasis AI

## Prioritized Backlog

### P0 (Critical) - DONE ✅
- [x] User authentication
- [x] Basic CRUD operations
- [x] Dashboard Advanced
- [x] Navigation dropdown restructure
- [x] All data entry pages
- [x] **AI Intelligence Agent**
- [x] **AI Settings in Settings page**
- [x] **Smart Stock Module (Sumber Penerimaan, Sumber Pemakaian)**
- [x] **Smart Blending AI** (Gemini-powered optimization)
- [x] **Export PDF/Excel** di halaman Laporan, Sumber Penerimaan, Sumber Pemakaian

### P1 (High Priority)
- [x] Real export PDF/Excel implementation di Laporan ✅ DONE
- [x] Add PO Batubara dan Merit Order ke halaman Laporan ✅ DONE
- [ ] Server-side pagination

### P2 (Medium Priority)
- [ ] Refactor backend server.py ke modular structure
- [ ] Advanced filtering & date range
- [ ] AI conversation memory (multi-turn)
- [ ] Fix Excel parser bug untuk "Sumber Penerimaan" (TOTALPENERIMAAN header issue)

### P3 (Nice to Have)
- [ ] Dashboard filter by Periode functionality
- [ ] Dark/Light mode toggle
- [ ] Data backup & restore
- [ ] Audit trail / activity log

## Next Tasks
1. Implement real PDF/Excel export di halaman Laporan
2. Add PO Batubara dan Merit Order ke tab di halaman Laporan
3. Refactor backend server.py ke modular structure

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, Shadcn/UI, Recharts, Lucide-React, react-markdown
- **Backend**: FastAPI, Motor (MongoDB async), Pandas, Openpyxl, emergentintegrations
- **Database**: MongoDB
- **Auth**: JWT (python-jose, bcrypt)
- **AI**: Gemini via Emergent LLM Key

## Test Credentials
- **Email**: admin@example.com
- **Password**: adminpassword
