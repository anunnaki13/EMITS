# PRD: Sistem Manajemen Bahan Bakar Digital PLTU Tenayan

## Overview
Sistem digital untuk mengelola rekapitulasi penerimaan batubara dan biomassa di PLTU Tenayan.

## User Personas
1. **Admin** - Akses penuh, kelola pengguna, hapus data
2. **Operator** - Input data, edit, upload Excel
3. **Viewer** - Hanya melihat data dan laporan

## Core Requirements (Static)
- Dashboard dengan statistik real-time
- CRUD untuk 4 kategori: Vessel TNY, Barge TNY, Trucking TNY, Biomassa TNY
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
- ✅ CRUD endpoints untuk semua kategori (Vessel, Barge, Trucking, Biomassa)
- ✅ Excel upload & parsing untuk semua kategori
- ✅ Delete all data endpoint per kategori
- ✅ Dashboard statistics API

### Frontend (React)
- ✅ Login/Register page dengan dark theme
- ✅ Dashboard dengan grafik Recharts
- ✅ Vessel TNY page (tabbed form dengan 5 tab: Shipment, Muatan, Kualitas, Ultimate, Ash Comp)
- ✅ Barge TNY page (tabbed form lengkap)
- ✅ Trucking TNY page (tabbed form lengkap)
- ✅ Biomassa TNY page (tabbed form dengan 4 tab: Shipment, Waktu, Muatan, Kualitas)
- ✅ Laporan page (tabs untuk 4 kategori, statistik, filter, tombol export)
- ✅ Settings page (profil user, manajemen user, info hak akses role)
- ✅ Responsive sidebar navigation
- ✅ Dark theme dengan glassmorphism
- ✅ All forms tested with E2E testing (100% pass rate)
- ✅ **View Detail Dialog** - Tombol "Lihat" untuk melihat detail data tanpa edit
- ✅ **Pagination** - 100 data per halaman dengan navigasi First/Prev/Page Numbers/Next/Last
- ✅ **Data Sorting** - Data diurutkan dari terbaru (halaman 1 = data terbaru)
- ✅ "Made with Emergent" badge dihapus dari semua halaman

## Prioritized Backlog

### P0 (Critical) - DONE
- [x] User authentication
- [x] Basic CRUD operations
- [x] Dashboard overview

### P1 (High Priority)
- [ ] Real export PDF/Excel implementation
- [ ] Data validation & error handling improvement
- [ ] Bulk delete functionality
- [ ] Pagination for large datasets

### P2 (Medium Priority)
- [ ] Advanced filtering & date range
- [ ] Notification alerts for anomalies
- [ ] Data import from existing Excel templates
- [ ] Audit trail / activity log

### P3 (Nice to Have)
- [ ] Print-friendly views
- [ ] Dark/Light mode toggle
- [ ] Data backup & restore
- [ ] Multi-language support

## Next Tasks
1. Implement real PDF/Excel export dengan library pdfkit/xlsxwriter
2. Add pagination untuk tables dengan banyak data
3. Improve form validation dan error messages
4. Add date range filter di laporan

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, Shadcn/UI, Recharts
- **Backend**: FastAPI, Motor (MongoDB async)
- **Database**: MongoDB
- **Auth**: JWT (python-jose, bcrypt)
