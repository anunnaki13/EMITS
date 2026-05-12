---
phase: 03-documentation-refresh-decision-lock-in
plan: 04
subsystem: docs
tags: [known-issues, documentation, readme, project-md, adr-cross-link, docs-04, docs-05]

# Dependency graph
requires:
  - phase: 03-documentation-refresh-decision-lock-in
    provides: "Plan 03-01 ADRs at .planning/decisions/ADR-001..008-*.md (needed by Known Issues entries and PROJECT.md cross-link table)"
  - phase: 03-documentation-refresh-decision-lock-in
    provides: "Plan 03-02 VPS Service Recovery runbook in LOCAL_SETUP.md (operator context for Known Issues entry on login mitigation)"
provides:
  - "documentation.md 'Known Issues' H2 section with 5 initial entries (mitigated login bug, Smart Blending pending Phase 6, Excel parser pending Phase 6, collection naming debt pending Phase 5, audit-probe synthetic users accepted/clean)"
  - "readme.md one-line Known Issues pointer to documentation.md#known-issues"
  - "PROJECT.md ADR cross-link table (IMPLICIT-001..008 → ADR-001..008 slugs) + Key Decisions STAB-04 closure row updated"
affects: [03-05, phase-4-testing, downstream-phases]

# Tech tracking
tech-stack:
  added: []  # Pure documentation — no new libraries
  patterns:
    - "Known Issues entry format: '- **[<status>]** Title — desc. (Cite: relative-path)' with badges mitigated/pending-Phase-N/accepted"
    - "Operator-facing doc section (documentation.md) as canonical Known Issues surface; README points to it via anchor link"
    - "ADR cross-link table in PROJECT.md appended as new H2 after existing content; IMPLICIT rows preserved for backwards-compat greps"

key-files:
  created: []
  modified:
    - pltu-tenayan-full-backup/documentation.md
    - pltu-tenayan-full-backup/readme.md
    - .planning/PROJECT.md

key-decisions:
  - "Known Issues placed in documentation.md as plain H2 (per D-09) — no section number, distinct from numbered Bahasa sections, signals operational state vs domain content"
  - "readme.md pointer inserted as blockquote callout after Ringkasan paragraph — visible at top of README without burying it below feature list"
  - "PROJECT.md cross-link approach: append new H2 section rather than inline-editing IMPLICIT-NNN rows — minimises blast radius; existing text-search queries for IMPLICIT-NNN continue working"
  - "audit-probe [accepted] status confirmed by live mongosh count 0 (2026-05-11 verification)"

patterns-established:
  - "Two-repo atomic commit protocol for Plan 03-04: one inner-repo commit (documentation.md + readme.md), one outer-repo commit (PROJECT.md)"

requirements-completed: [DOCS-04, DOCS-05]

# Metrics
duration: ~8min
completed: 2026-05-11
---

# Phase 03 Plan 04: Known Issues section + readme pointer + PROJECT.md ADR cross-link — Summary

**Known Issues H2 lands in documentation.md with 5 operator-facing entries (login mitigated, Smart Blending budget, Excel parser, collection naming debt, audit-probe cleanup); readme.md gains a one-line anchor pointer; PROJECT.md gains the IMPLICIT→ADR cross-link table and flips the STAB-04 Key Decisions row to Applied.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-05-11
- **Completed:** 2026-05-11
- **Tasks:** 2 / 2
- **Files modified:** 3
- **Commits:** 2 (1 inner, 1 outer)

## Accomplishments

- `pltu-tenayan-full-backup/documentation.md`: new `## Known Issues` H2 appended after section 17 with 5 entries using D-10 status badges and cite clauses
- `pltu-tenayan-full-backup/readme.md`: blockquote pointer `> **Status terkini:** lihat [Known Issues](documentation.md#known-issues) ...` inserted after Ringkasan paragraph
- `.planning/PROJECT.md`:
  - Key Decisions row "Promote IMPLICIT-001..008 to locked ADRs" flipped from `— Pending (Phase 3)` to `✓ Applied (Phase 3 plan 03-01, 2026-05-10)`
  - Footer updated to `Last updated: 2026-05-10 after Phase-3 plan 03-04 ADR cross-link`
  - New `## ADR Cross-Links (Phase-3 lock-in)` H2 appended with 8-row table mapping IMPLICIT-NNN → ADR-NNN-slug.md relative links

## Task Commits

1. **Task 1: Known Issues H2 + readme pointer (inner repo)** — `62b4558` (`docs(docs-05): add Known Issues section + readme pointer (D-09, D-10)`) — `pltu-tenayan-full-backup` repo
2. **Task 2: ADR cross-link section + Key Decisions update (outer repo)** — `b7a803e` (`docs(docs-04): add ADR cross-link section to PROJECT.md (STAB-04 closure)`) — outer `emits` repo

## Live Verification Data

**audit-probe synthetic user count (2026-05-11):** `mongosh --eval "db.getSiblingDB('pltu_tenayan').users.countDocuments({email:/^audit-probe-/})"` → **0**

The `[accepted]` status and "live count 0" claim in the Known Issues entry is accurate as of this plan's execution date. The Phase-2 conftest cleanup fixture (`backend/tests/conftest.py cleanup_audit_probe_users`) continues to guard against re-insertion on test runs.

## Known Issues anchor text

The literal anchor for the Known Issues section (for downstream plan cross-linking):

```
documentation.md#known-issues
```

Markdown link form used in readme.md: `[Known Issues](documentation.md#known-issues)`

## Files Created/Modified

- `pltu-tenayan-full-backup/documentation.md` — Known Issues H2 section added at end of file (was 732 lines → ~792 lines). 5 entries with status badges per D-10, each citing ≥1 source file. Credential scanner exits 0 (inner repo).
- `pltu-tenayan-full-backup/readme.md` — Blockquote pointer after Ringkasan paragraph. Anchor link to `documentation.md#known-issues`.
- `.planning/PROJECT.md` — ADR cross-link H2 table (8 rows, IMPLICIT-001..008 → ADR paths with relative links). Key Decisions STAB-04 row updated to Applied. Footer updated.

## Decisions Made

- **D-09 + D-10 honored exactly.** Known Issues section title is the literal `## Known Issues` (no number); entries use the exact badge/cite format from the plan.
- **blockquote callout placement.** Per D-09 plan note ("line ~7 area"), the pointer lands immediately after the Ringkasan paragraph — above Fitur Utama — so operators see it early on README scan.
- **PROJECT.md append-only approach chosen.** IMPLICIT-NNN rows are high-grep-traffic references; inline editing would risk surprising future search results. New H2 section is purely additive.
- **audit-probe live count confirmed before writing.** Ran `mongosh` count → 0 before writing the `[accepted]` entry; had count been non-zero, the plan required downgrade to `[pending-Phase-3]`.

## Deviations from Plan

None — plan executed exactly as written. Two tasks, two commits, all acceptance criteria met.

## Known Stubs

None — all Known Issues entries cite real files at real paths. No placeholder text or TODO stubs in the added content.

## Threat Flags

None — this plan adds documentation only; no new network endpoints, auth paths, file access patterns, or schema changes.

## Self-Check: PASSED

**File existence:**
- FOUND: `pltu-tenayan-full-backup/documentation.md` (contains `## Known Issues`)
- FOUND: `pltu-tenayan-full-backup/readme.md` (contains `documentation.md#known-issues`)
- FOUND: `.planning/PROJECT.md` (contains `## ADR Cross-Links (Phase-3 lock-in)`)

**Commit existence:**
- FOUND: inner `62b4558` (`docs(docs-05): add Known Issues section + readme pointer (D-09, D-10)`)
- FOUND: outer `b7a803e` (`docs(docs-04): add ADR cross-link section to PROJECT.md (STAB-04 closure)`)

**Verification checks passed:**
- `## Known Issues` H2 count: 1
- Known Issues entries (`^- \*\*\[`): 5
- `LOGIN_BUG_RESOLUTION.md` cite: present
- `ADR-004-jwt-bcrypt-three-role-auth` cite: present
- `OPS-01` cite: present
- `CONS-collection-naming-debt` cite: present
- readme anchor `documentation.md#known-issues`: present
- inner-repo credential scanner: exit 0
- `## ADR Cross-Links` H2: present (1)
- ADR-001..008 rows: all 8 present
- `✓ Applied (Phase 3 plan 03-01, 2026-05-10)` in Key Decisions: present
- Footer `Last updated: 2026-05-10 after Phase-3 plan 03-04`: present

---
*Phase: 03-documentation-refresh-decision-lock-in*
*Plan: 04*
*Completed: 2026-05-11*
