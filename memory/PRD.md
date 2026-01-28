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
*Last Updated: January 28, 2026*

### Backend (FastAPI)
- ✅ User authentication (JWT)
- ✅ Role-based authorization
- ✅ CRUD endpoints untuk semua kategori
- ✅ Excel upload & parsing untuk semua kategori
- ✅ Dashboard statistics API & Advanced Dashboard API
- ✅ **AI Intelligence API** - /api/ai/query dengan 4 modul
- ✅ **AI Quick Analysis Endpoints** - blending, boiler alerts, contract status, logistics losses
- ✅ **AI Settings API** - Custom API key management

### Frontend (React)
- ✅ Login/Register page dengan dark theme
- ✅ **Dashboard Advanced** dengan visualisasi lengkap:
  - Panel Monitoring Kontrak (Gauge Chart) - Realisasi vs PO
  - Summary Stats 6 Bulan Terakhir
  - Tren Penerimaan 6 Bulan (Bar Chart) dengan tabel detail
  - **Komposisi Bahan Bakar (Donut Chart)** - Batubara LRC/MRC dari PO + Biomassa WOODCHIP/SAWDUST
  - Tren Kualitas GCV (Line Chart) dengan target 4000 Kcal/Kg
  - Analisis Ekonomi Supplier (Horizontal Bar Chart) - RP/Kcal terendah
  - **Matriks Risiko Slagging & Fouling** - Data dari Vessel, Barge, DAN Trucking dengan kolom Moda
  - Filter interaktif berdasarkan Moda
- ✅ Vessel TNY page (tabbed form dengan 5 tab)
- ✅ Barge TNY page (tabbed form lengkap)
- ✅ Trucking TNY page (tabbed form lengkap)
- ✅ Biomassa TNY page (tabbed form dengan 4 tab)
- ✅ Purchase Order Batubara page
- ✅ Merit Order page
- ✅ Laporan page
- ✅ Settings page
- ✅ Dropdown Navigation dengan 6 submenu

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
├── Laporan
└── Pengaturan (Admin only)
```

## Prioritized Backlog

### P0 (Critical) - DONE ✅
- [x] User authentication
- [x] Basic CRUD operations
- [x] **Dashboard Advanced dengan 7 visualisasi**
- [x] Navigation dropdown restructure
- [x] Purchase Order Batubara page
- [x] Merit Order page

### P1 (High Priority)
- [ ] Real export PDF/Excel implementation di Laporan
- [ ] Server-side pagination (current: client-side)
- [ ] Add PO Batubara dan Merit Order ke halaman Laporan

### P2 (Medium Priority)
- [ ] Refactor backend server.py ke modular structure
- [ ] Refactor frontend duplicate code ke reusable hooks
- [ ] Advanced filtering & date range

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
- **Frontend**: React 19, Tailwind CSS, Shadcn/UI, Recharts, Lucide-React
- **Backend**: FastAPI, Motor (MongoDB async), Pandas, Openpyxl, python-dateutil
- **Database**: MongoDB
- **Auth**: JWT (python-jose, bcrypt)

## Test Credentials
- **Email**: admin@example.com
- **Password**: adminpassword
