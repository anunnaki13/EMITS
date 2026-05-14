---
phase: 32
requirements:
  - REPO4-01
  - REPO4-02
  - REPO4-03
  - REPO4-04
nyquist_status: passed
validation_owner: codex
---

# Phase 32 Validation Plan

## Gates

| Requirement | Validation |
|-------------|------------|
| REPO4-01 | Repo hygiene docs and gate allow only documented unstaged local-only dirt. |
| REPO4-02 | `.gitignore` uses directory-level frontend cache ignores and has no individual cache pack entries. |
| REPO4-03 | `scripts/check_repo_hygiene.py` invokes `scripts/check_credentials.sh`; credential scan passes. |
| REPO4-04 | Hygiene gate reports release-blocking dirty changes separately from allowed local-only files. |

## Commands

```bash
python3 -m py_compile scripts/check_repo_hygiene.py tests/test_repo_hygiene.py
python3 -m pytest tests/test_repo_hygiene.py -q
bash scripts/check_credentials.sh
git diff --check -- .gitignore scripts/check_repo_hygiene.py tests/test_repo_hygiene.py docs/operations/REPO_HYGIENE.md docs/operations/PRODUCTION_RUNBOOK.md .planning/phases/32-repository-hygiene-secret-safety
python3 scripts/check_repo_hygiene.py
```

## Results

Validated on 2026-05-14:

| Command | Result |
|---------|--------|
| `python3 -m py_compile scripts/check_repo_hygiene.py tests/test_repo_hygiene.py` | Pass |
| `python3 -m pytest tests/test_repo_hygiene.py -q` | Pass: 2 passed |
| `bash scripts/check_credentials.sh` | Pass |
| `git diff --check -- .gitignore scripts/check_repo_hygiene.py tests/test_repo_hygiene.py docs/operations/REPO_HYGIENE.md docs/operations/PRODUCTION_RUNBOOK.md .planning/phases/32-repository-hygiene-secret-safety` | Pass |
| `python3 scripts/check_repo_hygiene.py` before commit | Expected fail: blocked current source/doc changes while allowing 5 documented local-only paths. |
| `python3 scripts/check_repo_hygiene.py` after commit | Pass with only documented local-only paths. |

## Residual Risks

- The tracked local-only paths remain dirty by design until a separate operator-approved cleanup confirms production no longer depends on their tracked history.
- The credential scanner still carries legacy documented exemptions; new exemptions remain prohibited without updating the scanner and hygiene documentation together.
