# Phase 07: Upgrade Backlog Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-11
**Phase:** 07-upgrade-backlog-foundation
**Areas discussed:** Execution strategy, filter UI scope, dashboard product direction

---

## Execution Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Refactor dulu | Kurangi risiko dengan memindahkan router/model sambil menjaga test suite tetap hijau sebelum menambah filter. | ✓ |
| Filter dulu | Prioritaskan fitur date-range/filter di backend dan frontend, lalu refactor setelahnya. | |
| Irisan per modul | Selesaikan refactor dan filter per modul satu per satu. Lebih cepat terlihat di UI, tapi risiko overlap lebih tinggi. | |

**User's choice:** `1` — refactor first.
**Notes:** This makes Phase 7 a contract-preserving backend cleanup first, then feature extension. Existing tests remain the primary safety net.

---

## Filter UI Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal konsisten | Tambahkan kontrol tanggal dan satu filter kategori di halaman rekap/laporan dengan layout yang mengikuti UI saat ini. | ✓ |
| Panel filter lengkap | Buat area filter lebih kaya untuk date range, supplier, mode, dan reset dengan cakupan UI lebih besar. | |
| Backend dulu | Tunda UI besar; cukup kontrak API dan test backend, lalu UI di plan terpisah. | |

**User's choice:** Interpreted as `1` for Phase 7 based on "1,1" and the need to keep this phase controlled.
**Notes:** The user also typed "1,2"; because the follow-up requested broader dashboard UI/UX changes, the richer UI work is captured as deferred/dashboard-specific rather than expanding the rekap filter scope.

---

## Dashboard Product Direction

| Direction | Description | Captured |
|-----------|-------------|----------|
| Stock batubara monitoring | Dashboard should show coal stock as a primary operational signal. | ✓ |
| Jadwal vs realisasi kedatangan bahan bakar | Dashboard should compare planned vs actual fuel arrivals. | ✓ |
| Dispute/umpire batubara monitoring | Dashboard should expose COA dispute/umpire status as a core monitoring area. | ✓ |

**User's choice:** Dashboard UI/UX needs redesign because current dashboard output feels arbitrary.
**Notes:** Captured as deferred product direction for Phase 8 or a dedicated dashboard phase. Phase 7 can extract/preserve dashboard backend code, but should not attempt a full dashboard visual redesign unless roadmap scope changes.

---

## the agent's Discretion

- Exact router/model file names.
- Whether to reuse or replace existing stale router files.
- Exact date-filter helper implementation after inspecting production-shaped date fields.

## Deferred Ideas

- Dashboard redesign around stock, arrival schedule vs realization, and dispute/umpire monitoring.
- Full advanced filter panel beyond minimal date/category controls.
