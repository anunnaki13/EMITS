# Requirements (PRD Intel)

Extracted from `pltu-tenayan-full-backup/memory/PRD.md`. The PRD is bilingual (Bahasa Indonesia / English); requirement statements below preserve the original wording where load-bearing.

## REQ-auth-rbac
- source: pltu-tenayan-full-backup/memory/PRD.md
- description: Role-based access control with three roles — Admin (full access, user management, AI settings, delete), Operator (input/edit/upload Excel, AI access), Viewer (read-only).
- acceptance criteria:
  - Login/Register with JWT
  - Three roles enforced server-side: `admin`, `operator`, `viewer`
  - Settings page restricted to admin
- scope: authentication, authorization
- status: implemented per PRD checklist

## REQ-rekap-penerimaan-bb
- source: pltu-tenayan-full-backup/memory/PRD.md
- description: CRUD for six fuel-receipt categories: Vessel TNY, Barge TNY, Trucking TNY, Biomassa TNY, Purchase Order Batubara, Merit Order. Excel auto-parsing on upload.
- acceptance criteria:
  - List, detail, create, update, delete, delete-all, and Excel upload endpoints exist for each category
  - Pagination supported on list endpoints
  - Roles: admin/operator can create/update; admin can delete-all
- scope: rekap penerimaan bahan bakar
- status: implemented per PRD checklist

## REQ-dashboard-advanced
- source: pltu-tenayan-full-backup/memory/PRD.md
- description: Dashboard with real-time statistics and 7 advanced visualizations.
- acceptance criteria:
  - GET /api/dashboard/stats returns total counts (vessel/barge/trucking/biomassa), tonnage, avg GCV, recent shipments, monthly trend, supplier stats
  - GET /api/dashboard/advanced returns advanced visualizations: total_ds_mt, contract_percentage, fuel_composition, gcv_trend, supplier_economy, slagging_matrix, six_months_summary, available_periods, available_moda
- scope: dashboard
- status: implemented per PRD checklist

## REQ-export-pdf-excel
- source: pltu-tenayan-full-backup/memory/PRD.md
- description: PDF/Excel export for reports and COA reconciliation.
- acceptance criteria:
  - Laporan page exports PDF/Excel
  - GET /api/coa-reconciliation/export/excel and /export/pdf available
  - Files generated on-demand (not persisted as collections)
- scope: reporting/export
- status: implemented per PRD checklist

## REQ-ai-intelligence-agent
- source: pltu-tenayan-full-backup/memory/PRD.md
- description: AI Intelligence Agent with chat interface and 7 analysis modules.
- acceptance criteria:
  - POST /api/ai/query supports modules: general, blending, boiler/boiler_risk, contract, logistics, smart-stock, coa
  - Session memory via /api/ai/sessions endpoints (create, list, detail, delete)
  - Quick analysis endpoints: blending-suggestion, boiler-alerts, contract-status, logistics-losses, smart-stock, coa-alerts
  - Per-user AI settings (custom API key, llm_provider, llm_model) via /api/ai/settings
- scope: AI / LLM integration
- status: implemented per PRD checklist

## REQ-smart-stock
- source: pltu-tenayan-full-backup/memory/PRD.md
- description: Smart Stock module with Sumber Penerimaan, Sumber Pemakaian, and Smart Blending AI sub-features.
- acceptance criteria:
  - GET/POST/Upload/Delete endpoints for /api/smart-stock and /api/sumber-pemakaian
  - Manual entry forms with daily date, stock_awal, supplier-zone breakdown
  - Excel upload via parser
- scope: smart stock
- status: implemented per PRD checklist

## REQ-smart-blending-ai
- source: pltu-tenayan-full-backup/memory/PRD.md
- source: pltu-tenayan-full-backup/frontend/public/docs/Smart_Blending_AI_Formula.md
- description: AI-driven coal blending recommendation that hits a target GCV while respecting ash/sulphur/moisture/VM/FC constraints.
- acceptance criteria:
  - POST /api/smart-blending/recommend accepts: target_gcv, max_ash, max_sulphur, max_total_moisture, max_inherent_moisture, min_volatile_matter, min_fixed_carbon, target_quantity
  - Backend pulls 6-month quality history from vessels/barges/trucking, latest stock from smartstock, prices from merit_order
  - Output JSON contains: recommendation[], predicted_quality, meets_target, reasoning, cost_warning
  - Constraint validation: GCV_blend ≥ target_GCV; Ash/Sulphur/TM/IM ≤ max; VM/FC ≥ min
  - Tonnage_i = total_quantity × percentage_i; Σ percentages = 100%
  - LRC + MRC blending typical (60-70% LRC + 30-40% MRC for target 4000-4200 kcal/kg)
- scope: AI blending
- status: implemented; known P1 issue — Smart Blending AI Timeout (BadGatewayError) BLOCKED on LLM budget

## REQ-coa-reconciliation
- source: pltu-tenayan-full-backup/memory/PRD.md
- description: Triple-check coal quality reconciliation across loading, unloading, and internal lab; supports umpire dispute workflow.
- acceptance criteria:
  - List endpoint with pagination, status filter, search, date_from/date_to
  - KPI endpoint returning deviation alert count, potential loss (Rp), umpire status, average accuracy
  - Trend chart endpoint (months 1-12, default 3)
  - Supplier-consistency chart endpoint
  - Detail endpoint with radar/spider quality data
  - Triple Check table with conditional red formatting when |delta| > 150 kCal/kg
  - High Deviation Alert threshold: |delta GCV| > 100 kCal/kg
  - Upload of three Excel files (loading_file, unloading_file, internal_file) via multipart
  - Manual single-record input
  - Propose-umpire workflow (sample_number, notes; admin/operator role)
  - Submit-umpire-result with full quality fields and lab name; produces Quad Check radar
  - Admin-only DELETE all
  - Excel and PDF export endpoints
- scope: COA reconciliation, dispute monitor
- status: implemented per PRD checklist

## REQ-i18n-indonesian-ui
- source: pltu-tenayan-full-backup/memory/PRD.md
- description: User interface in Bahasa Indonesia.
- acceptance criteria: All user-facing labels render in Indonesian; bilingual error messages acceptable.
- scope: localization

## REQ-dark-saas-ui
- source: pltu-tenayan-full-backup/memory/PRD.md
- description: Dark Mode SaaS Dashboard UI as primary visual style.
- acceptance criteria: Application defaults to dark theme; built with Tailwind + Shadcn/UI.
- scope: UI/theme

## REQ-pagination-server-side
- source: pltu-tenayan-full-backup/memory/PRD.md
- source: pltu-tenayan-full-backup/API_REFERENCE.md
- description: Server-side pagination across list endpoints.
- acceptance criteria:
  - Response shape: { items, total, page, page_size, total_pages }
  - Default page=1, page_size=50; max page_size 500 (operational endpoints) or 50000 (smart_stock list)
- scope: API list contract
- status: implemented (P1 — DONE)

## REQ-coa-export
- source: pltu-tenayan-full-backup/memory/PRD.md
- description: Export COA reconciliation data to PDF and Excel with optional status_filter query param.
- acceptance criteria: GET /api/coa-reconciliation/export/excel, /export/pdf each with status_filter query.
- scope: COA / export
- status: implemented (P1 — DONE Jan 30, 2026)

## REQ-laporan-supplier-filter
- source: pltu-tenayan-full-backup/memory/PRD.md
- description: Filter Laporan page by Supplier.
- acceptance criteria: Laporan page exposes supplier filter that maps to backend supplier query.
- scope: reporting
- status: implemented (P1 — DONE Jan 30, 2026)

## REQ-ai-conversation-memory
- source: pltu-tenayan-full-backup/memory/PRD.md
- description: AI conversation memory persists per user/session and reflects current modules (Smart Stock, COA).
- acceptance criteria: ai_conversations collection holds messages[]; session endpoints functional; modules include smart-stock and coa.
- scope: AI memory
- status: backend implemented; P2 frontend integration remaining

## REQ-developer-docs-suite
- source: pltu-tenayan-full-backup/memory/PRD.md
- description: README, technical documentation, API reference, schema doc, deployment guide, and Smart Blending formula doc maintained at project root and docs path.
- acceptance criteria: Files present and discoverable: README.md, documentation.md, API_REFERENCE.md, DATABASE_SCHEMA.md, DEPLOYMENT_GUIDE.md, frontend/public/docs/Smart_Blending_AI_Formula.md
- scope: documentation
- status: implemented per PRD checklist

## Open / Backlog (extracted verbatim from PRD)

### REQ-fix-smart-blending-timeout (P1)
- source: pltu-tenayan-full-backup/memory/PRD.md
- description: Fix Smart Blending AI Timeout (BadGatewayError).
- status: BLOCKED — LLM budget exhausted; awaiting Universal Key recharge.

### REQ-verify-excel-parser-total-penerimaan (P1)
- source: pltu-tenayan-full-backup/memory/PRD.md
- description: Verify Excel Parser with `total penerimaan.xlsx`.
- status: BLOCKED — awaiting actual sample file from user.

### REQ-refactor-server-py (P2)
- source: pltu-tenayan-full-backup/memory/PRD.md
- source: pltu-tenayan-full-backup/documentation.md
- description: Refactor `server.py` into modular routers.
- status: partially done; supplier filter endpoints already updated.

### REQ-advanced-filtering-date-range (P2)
- source: pltu-tenayan-full-backup/memory/PRD.md
- description: Advanced filtering and date range support across modules.
- status: backlog.

### REQ-dashboard-period-filter (P3)
- source: pltu-tenayan-full-backup/memory/PRD.md
- description: Dashboard filter by Periode.
- status: nice-to-have.

### REQ-dark-light-mode-toggle (P3)
- source: pltu-tenayan-full-backup/memory/PRD.md
- description: Dark/Light mode toggle (currently dark-only).
- status: nice-to-have.

### REQ-data-backup-restore (P3)
- source: pltu-tenayan-full-backup/memory/PRD.md
- description: Application-level data backup and restore.
- status: nice-to-have.

### REQ-audit-trail (P3)
- source: pltu-tenayan-full-backup/memory/PRD.md
- description: Audit trail / activity log across user actions.
- status: nice-to-have.
