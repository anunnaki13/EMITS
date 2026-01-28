# PRD: Sistem Manajemen Bahan Bakar Digital PLTU Tenayan

## Overview
Sistem digital untuk mengelola rekapitulasi penerimaan batubara dan biomassa di PLTU Tenayan.

## User Personas
1. **Admin** - Akses penuh, kelola pengguna, hapus data
2. **Operator** - Input data, edit, upload Excel
3. **Viewer** - Hanya melihat data dan laporan

## Core Requirements (Static)
- Dashboard dengan statistik real-time
- CRUD untuk 6 kategori: Vessel TNY, Barge TNY, Trucking TNY, Biomassa TNY, Purchase Order Batubara, **Merit Order**
- Upload Excel dengan auto-parsing
- Role-based access control
- Export laporan PDF/Excel
- Interface Bahasa Indonesia
- Dark Mode SaaS Dashboard UI

## What's Been Implemented ✅
*Last Updated: January 28, 2026*

### Backend (FastAPI)
- ✅ User authentication (JWT)
- ✅ Role-based authorization
- ✅ CRUD endpoints untuk semua kategori (Vessel, Barge, Trucking, Biomassa, PO Batubara, Merit Order)
- ✅ Excel upload & parsing untuk semua kategori
- ✅ Delete all data endpoint per kategori
- ✅ Dashboard statistics API
- ✅ **PO Batubara API** - /api/po-batubara dengan filter year/month
- ✅ **Merit Order API** - /api/merit-order dengan CRUD lengkap

### Frontend (React)
- ✅ Login/Register page dengan dark theme
- ✅ Dashboard dengan grafik Recharts
- ✅ Vessel TNY page (tabbed form dengan 5 tab)
- ✅ Barge TNY page (tabbed form lengkap)
- ✅ Trucking TNY page (tabbed form lengkap)
- ✅ Biomassa TNY page (tabbed form dengan 4 tab)
- ✅ **Purchase Order Batubara page** - Tampilan per tahun/bulan dengan total
- ✅ **Merit Order page** - Tabel perbandingan harga pemasok dengan icon moda dan badge kontrak
- ✅ Laporan page (tabs untuk 4 kategori, statistik, filter, tombol export)
- ✅ Settings page (profil user, manajemen user, info hak akses role)
- ✅ **Dropdown Navigation** - Menu "Rekap Penerimaan BB" dengan 6 submenu
- ✅ Responsive sidebar navigation
- ✅ Dark theme dengan glassmorphism

### Navigation Structure
```
├── Dashboard
├── Rekap Penerimaan BB (Dropdown)
│   ├── Vessel TNY
│   ├── Barge TNY
│   ├── Trucking TNY
│   ├── Biomassa TNY
│   ├── Purchase Order Batubara
│   └── Merit Order ✨ NEW
├── Laporan
└── Pengaturan (Admin only)
```

## Prioritized Backlog

### P0 (Critical) - DONE ✅
- [x] User authentication
- [x] Basic CRUD operations
- [x] Dashboard overview
- [x] Navigation dropdown restructure
- [x] Purchase Order Batubara page
- [x] **Merit Order page**

### P1 (High Priority)
- [ ] Real export PDF/Excel implementation di Laporan
- [ ] Server-side pagination (current: client-side dengan limit 5000)
- [ ] Add PO Batubara dan Merit Order ke halaman Laporan

### P2 (Medium Priority)
- [ ] Refactor backend server.py ke modular structure (/routes, /models, /services)
- [ ] Refactor frontend duplicate code ke reusable hooks
- [ ] Advanced filtering & date range
- [ ] Fix frontend linting errors

### P3 (Nice to Have)
- [ ] Dashboard Analytics improvements
- [ ] Dark/Light mode toggle
- [ ] Data backup & restore
- [ ] Audit trail / activity log

## Next Tasks
1. Implement real PDF/Excel export di halaman Laporan
2. Add PO Batubara dan Merit Order ke tab di halaman Laporan
3. Refactor backend server.py ke modular structure

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, Shadcn/UI, Recharts, Lucide-React
- **Backend**: FastAPI, Motor (MongoDB async), Pandas, Openpyxl
- **Database**: MongoDB
- **Auth**: JWT (python-jose, bcrypt)

## Test Credentials
- **Email**: admin@example.com
- **Password**: adminpassword
