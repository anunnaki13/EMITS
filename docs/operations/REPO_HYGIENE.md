# Repository Hygiene And Secret Safety

Phase 32 separates release-blocking source changes from intentional local-only
runtime state.

## Local-Only Allowlist

The following paths may appear dirty on the VPS/developer host and must not be
committed with real runtime values:

| Path | Reason |
|------|--------|
| `backend/.env` | Local backend runtime secrets/config. |
| `frontend/.env` | Local frontend runtime config. |

The allowlist only applies to unstaged worktree changes. If any of these files
are staged, the hygiene check fails because staged local runtime state can leak
into a commit.

## Commands

Run the repo hygiene gate before release:

```bash
python3 scripts/check_repo_hygiene.py
```

Machine-readable output:

```bash
python3 scripts/check_repo_hygiene.py --json
```

The check runs `scripts/check_credentials.sh`, rejects unexpected dirty files,
and rejects individual frontend webpack pack entries in `.gitignore`.

## Build Cache Policy

Frontend cache directories are ignored at directory level:

- `frontend/node_modules/.cache/`
- `frontend/.cache/`

Do not append individual `frontend/node_modules/.cache/default-development/*.pack`
paths to `.gitignore`. That churn hides the real source diff and makes release
review noisy.

## Credential Policy

Real secrets stay in local environment files or the operator secret store. Tests
source credentials from environment variables or `memory/test_credentials.md`,
which is gitignored. New scanner exemptions require updating
`scripts/check_credentials.sh` and `docs/audit/CREDENTIAL_HYGIENE.md` together.
