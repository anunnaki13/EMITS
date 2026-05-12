# Phase 04: Test Suite Stabilization - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-11
**Phase:** 04-test-suite-stabilization
**Areas discussed:** Test data isolation, AI mock granularity, Excel fixture provenance, Test runner posture

---

## Test data isolation — DB strategy

| Option | Description | Selected |
|--------|-------------|----------|
| pltu_tenayan_test_* isolated DB | Konsisten dengan pattern Phase 2 plan 02-02. conftest seed minimum data + tear down setelah session. Live pltu_tenayan TIDAK pernah disentuh oleh test. | ✓ |
| Hybrid — isolated DB untuk write, live untuk read-only smoke | Test yang write/delete pakai pltu_tenayan_test_*; test read-only (mis. pagination shape) boleh hit live. Lebih cepat tapi dua mode = lebih kompleks. | |
| Live pltu_tenayan read-only + label cleanup | Semua write di-tag prefix (mis. `audit-probe-`) + auto-cleanup via fixture teardown. Risiko: kalau cleanup fail, data sampah masuk produksi (sudah pernah kejadian Plan 01-04). | |

**User's choice:** pltu_tenayan_test_* isolated DB (Recommended)
**Notes:** Phase-2 plan 02-02 already proved this pattern. Plan 01-04 had a real incident with audit-probe-* synthetic users leaking into live `users` collection — that historical evidence anchored the decision.

---

## AI test mock granularity (TEST-06)

### Round 1 — Initial trade-off

| Option | Description | Selected |
|--------|-------------|----------|
| Stub EmergentLLMClient via DI | Ganti class dengan FakeEmergentLLMClient di conftest fixture. Test fokus ke request validation + response shape transformation di server.py. Tidak butuh network lib tambahan. Maintenance minimal. | (free-text response) |
| HTTP-level mock pakai respx | Install respx, intercept httpx request ke emergent endpoint. Lebih realistic. Tambah 1 dependency. Payload lib harus di-mirror. | |
| Kombinasi: stub default, respx untuk 1-2 critical endpoint | Mostly stub (cepat), tapi 1-2 AI endpoint pakai respx untuk catch integration drift. | |

**User's free-text response:** "ok, jadi perbaiki ini masalah AI ini, tidak masalah stub ke EmergentLLMClient, namun ubah namanya, buatkan atau desainkan yang terbaru, dimana saya menggunakan openrouter bukan gemini seperti yang sekarang"

**Claude's redirect:** Provider migration (Gemini → OpenRouter) is scope creep per PROJECT.md "Out of Scope" line 87 (IMPLICIT-005) and ROADMAP Phase 6 boundary. Proposed: introduce `AIClient` Protocol/ABC in Phase 4 as the structural seam, wrap existing `EmergentLLMClient` behind it (no rename, no rewrite), test against the interface. Deferred provider migration + rename to a dedicated future phase.

### Round 2 — Confirmation

| Option | Description | Selected |
|--------|-------------|----------|
| Setuju — introduce AIClient interface + stub interface | Phase 4: abstract Protocol/ABC `AIClient`, production wraps EmergentLLMClient di balik interface (no rename, no rewrite). Test stub interface. OpenRouter migration di-defer ke phase tersendiri. | ✓ |
| Tetap stub class konkret EmergentLLMClient (lebih cepat) | Tidak introduce interface. Test stub class langsung. Saat migrasi OpenRouter nanti, test perlu di-update karena class name berubah. Lebih cepat sekarang, lebih kerja nanti. | |
| Insert Phase 4.5 atau prioritas-ulang Phase 6 — OpenRouter dulu | Stop Phase 4. Pakai /gsd-phase untuk insert atau rearrange ROADMAP supaya OpenRouter migration dikerjakan dulu, Phase 4 setelahnya. | |

**User's choice:** Setuju — introduce AIClient interface + stub interface (Recommended)
**Notes:** Provider migration captured as deferred idea. The interface seam Phase 4 builds is the precise enabler for the future migration phase to swap implementations without touching tests.

---

## Excel fixture provenance (TEST-04)

| Option | Description | Selected |
|--------|-------------|----------|
| Sanitized synthetic minimal per mode | 1 .xlsx per mode (vessel, barge, trucking, biomassa) berisi 5-10 baris, header asli, data dummy. Total <50 KB. Edge case (header variant) ditambah test terpisah. Phase 6 OPS-02 yang ngurus real-sample verification. | ✓ |
| Truncate Loading.xlsx / Unloading.xlsx jadi 5 baris | Pakai file produksi yang ada, potong jadi sekitar 5-10 baris per mode, sanitize nilai PII. Realistic format tapi butuh review manual sebelum commit. | |
| Pakai xlsx live as-is + tambah ke .gitignore daftar review | Commit file mentah, fix problem PII via ad-hoc sanitization commit. Cepat, tapi melanggar aturan credential / data hygiene. | |

**User's choice:** Sanitized synthetic minimal per mode (Recommended)
**Notes:** Phase 6 OPS-02 owns real-sample numerical verification. Phase 4 only needs to prove parser code-path executes end-to-end. Header-variant edge cases tracked via a HEADER_VARIANTS.md pointer in fixtures dir.

---

## Test runner posture (TEST-01 "clean checkout exit 0")

| Option | Description | Selected |
|--------|-------------|----------|
| Conftest auto-spawn backend subprocess | Pertahankan existing 1634-line test (no refactor). Conftest session-scoped fixture: cek :8013, kalau mati spawn uvicorn pakai .venv, tunggu /api/health 200, tear down di akhir. Satu command → exit 0. PID file untuk cleanup kalau test crash. | ✓ |
| Migrate to FastAPI TestClient end-to-end | Refactor 1634 baris dari requests → TestClient. Lebih cepat (tanpa HTTP), benar-benar self-contained, no port. Cost: chunk refactor (mungkin 2-3 plan tambahan). | |
| Status quo + tests/README.md operator workflow | Test tetap butuh backend hidup. Tambah doc step. TEST-01 diinterpretasikan sebagai "satu jalur, exit 0 setelah backend running". Paling minim effort, tapi melanggar literal "clean checkout". | |

**User's choice:** Conftest auto-spawn backend subprocess (Recommended)
**Notes:** Preserves Phase-2 conftest pattern, no refactor of 1634 existing lines, satisfies TEST-01's literal "clean checkout exit 0" with one command. PID file ensures cleanup if a run crashes.

---

## Claude's Discretion

- Exact `pytest.ini` / `pyproject.toml` placement (root vs `backend/`), conftest naming convention, factory-function signatures.
- Whether `tests/factories/` and `tests/fakes/` are flat modules or sub-packages.
- Pagination assertion helper API.
- Mechanism for the `MONGO_TEST_DB_NAME` env-var override in `server.py` (startup-only vs per-request).

## Deferred Ideas

- **LLM provider migration to OpenRouter** — captured as the principal deferred item. Future dedicated phase, candidate position: between Phase 4 and Phase 5, or fold into Phase 6. AIClient Protocol introduced by Phase 4 is the migration seam.
- **Excel header-variant edge cases** — Phase 6 OPS-02.
- **Numerical coverage gating (`pytest --cov-fail-under`)** — post-milestone polish phase.
- **Frontend test surface (Jest / React Testing Library)** — future phase, not yet scheduled.
- **CI / GitHub Actions** — post-milestone-v1.0.
