# Credential Hygiene Contract

## Status

AUTHFIX-05 satisfied. `memory/test_credentials.md` is gitignored and untracked
in the inner repo. The scanner at `scripts/check_credentials.sh` enforces the
forbidden-pattern policy below and is wired as a pre-commit hook at
`.git/hooks/pre-commit`. Future commits that introduce a forbidden pattern in
a tracked file (and outside the documented exemption list) cannot land via
the standard commit path.

## Allowed locations

- `pltu-tenayan-full-backup/memory/test_credentials.md` — local-only,
  gitignored, never tracked. Operator's source of truth for live test
  credentials. The file lives on the developer workstation and on the VPS
  but is not part of any git history going forward.
- Environment variables consumed by Phase-2 regression tests:
  - `TEST_ADMIN_EMAIL`
  - `TEST_ADMIN_PASSWORD`
  - `TEST_OPERATOR_EMAIL`
  - `TEST_OPERATOR_PASSWORD`
  - `TEST_VIEWER_EMAIL`
  - `TEST_VIEWER_PASSWORD`
- `MONGO_URL` and `JWT_SECRET` belong in `backend/.env` (already excluded by
  the existing `.env*` ignore rules). They are NEVER committed under any
  tracked path.

## Forbidden patterns

The four patterns below are enforced by the scanner. Source-of-truth lives
in `scripts/check_credentials.sh` — update the patterns there and this
document together. Examples are sanitized; do NOT inline real credentials
when adding a new row.

| Pattern | Regex (extended) | Sanitized example |
|---------|------------------|-------------------|
| JWT-shaped | `eyJ[A-Za-z0-9._-]{20,}\.[A-Za-z0-9._-]{20,}\.[A-Za-z0-9._-]{20,}` | `eyJhbG<...header...>.eyJzdWI<...claims...>.<sig>` |
| Bearer + JWT | `[Bb]earer[[:space:]]+eyJ[A-Za-z0-9._-]{20,}` | `Authorization: Bearer eyJhbG<...>` |
| MongoDB URI with embedded credentials | `mongodb(\+srv)?://[^[:space:]/]+:[^[:space:]/]+@` | `mongodb://USER:PASS@host:27017/db` |
| Admin password literal | `adminpassword` | (literal token; never inline) |

The scanner runs all four passes against the output of `git ls-files` minus
the EXCLUDE allowlist. Any match in any file outside the allowlist exits 1.

## How tests source credentials

Tests MUST read credentials from environment variables, never inline literals.

```python
import os

admin_email    = os.environ["TEST_ADMIN_EMAIL"]
admin_password = os.environ["TEST_ADMIN_PASSWORD"]
# ... assemble the login payload from the env values, never from string literals.
```

Note on the admin email: `admin@example.com` is documented in audit artifacts
(LOGIN_BUG.md, ENDPOINT_AUDIT.md) and is not itself a credential — only the
password is. The email may appear in committed test files. The password
literal `adminpassword` may not.

## How to run the scanner

Manual run, from anywhere:

```
cd pltu-tenayan-full-backup
bash scripts/check_credentials.sh
```

The scanner is also wired as a pre-commit hook at
`pltu-tenayan-full-backup/.git/hooks/pre-commit` (chained after the
pre-existing large-file ignore helper). Every `git commit` in the inner repo
runs the scanner before the commit is recorded, and a non-zero exit aborts
the commit.

## Known exemptions

The EXCLUDE array in `scripts/check_credentials.sh` is now limited to
self-references only:

- `scripts/check_credentials.sh` — owns the regex patterns and therefore
  necessarily contains the forbidden examples.
- `docs/audit/CREDENTIAL_HYGIENE.md` — documents the policy and sanitized
  examples.
- `docs/audit/LOGIN_BUG.md` — preserves the original audit trail for the
  historical login investigation.

All earlier technical-debt exemptions were cleared by replacing credential
literals with environment placeholders, redacting the PRD credential block,
and syncing the in-app public docs from the sanitized canonical docs. Files
that now pass on their own merits include:

- `test_reports/iteration_3.json` through `test_reports/iteration_6.json`
- `frontend/public/docs/API_REFERENCE.md`
- `frontend/public/docs/DEPLOYMENT_GUIDE.md`
- `memory/PRD.md`

## How to add a new exemption

A new exemption is the last resort. The preferred fix is always to remove
the literal and source from an env var. If a new exemption is genuinely
required (e.g., a test fixture that documents a sanitized example
credential):

1. Edit `scripts/check_credentials.sh`. Append the file path to the EXCLUDE
   array.
2. Add a `# TODO <PHASE-ID>` comment on the line ABOVE or as a trailing
   comment naming the phase that will remove the exemption. Example:
   `"foo/bar.py"  # TODO Phase 7 CLEANUP: replace with env-var read`.
3. Run `bash scripts/check_credentials.sh` and confirm it exits 0.
4. Commit `scripts/check_credentials.sh` and this document together with a
   message that names the file being added and the rationale.

Silently disabling the hook (`git commit --no-verify`) is prohibited by
policy. If the hook is genuinely broken, fix the scanner; do not bypass it.

## Operator runbook for setting test env vars

`memory/test_credentials.md` is the local source of truth. Source it into
the shell before running pytest. Example pattern (do NOT print the actual
secret values):

```bash
cd pltu-tenayan-full-backup
# extract values from the local credentials file (gitignored, local-only)
export TEST_ADMIN_EMAIL="$(grep -E '^- Email:' memory/test_credentials.md | head -1 | awk '{print $3}')"
export TEST_ADMIN_PASSWORD="$(grep -E '^- Password:' memory/test_credentials.md | head -1 | awk '{print $3}')"
# repeat for operator and viewer roles using their respective entries
# verify the env vars are set without printing the password
[ -n "$TEST_ADMIN_PASSWORD" ] && echo "TEST_ADMIN_PASSWORD: set" || echo "TEST_ADMIN_PASSWORD: MISSING"
# now run the tests
cd backend && pytest tests/
```

For CI runners (Phase 4+), the env vars are injected from the secret store
provided by the runner; the local `memory/test_credentials.md` file is not
present and is not required.
