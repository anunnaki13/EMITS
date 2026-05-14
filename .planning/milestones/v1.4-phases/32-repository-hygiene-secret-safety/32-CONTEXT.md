---
phase: 32
title: Repository Hygiene & Secret Safety
requirements:
  - REPO4-01
  - REPO4-02
  - REPO4-03
  - REPO4-04
status: context
---

# Phase 32 Context

## Objective

Resolve repository hygiene debt before the release gate: document intentional
local-only dirt, stop frontend build-cache `.gitignore` churn, preserve secret
scanning, and provide a release hygiene check.

## Inputs

- `.planning/ROADMAP.md` Phase 32 success criteria.
- `.planning/REQUIREMENTS.md` REPO4-01..04.
- Current worktree shows intentional local-only dirt in
  `README.md`, `backend/.env`, and `frontend/.env`.
- `.gitignore` contained individual `frontend/node_modules/.cache/default-development/*.pack`
  entries appended by prior build-cache churn.
- Existing credential scanner lives at `scripts/check_credentials.sh`.

## Scope

- Add a repo hygiene gate that separates intentional local-only changes from
  release-blocking source changes.
- Replace individual frontend cache pack ignores with directory-level cache
  ignores.
- Document the local-only allowlist and command in operations docs.

## Out Of Scope

- Rewriting git history to purge already-tracked historical secrets.
- Committing real `.env` values.
- Removing tracked local-only files from the index while production dependency
  on those paths is not fully proven.
