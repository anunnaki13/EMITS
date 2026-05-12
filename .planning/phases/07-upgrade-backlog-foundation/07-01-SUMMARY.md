# 07-01 Summary — Auth/Users Router Extraction

Completed: 2026-05-11

## Outcome

Auth and users endpoints were extracted from `backend/server.py` into the mounted auth router path while preserving the existing `/api/*` contract.

## Changes

- Mounted `routers.auth.router` and `routers.auth.users_router` under the existing `/api` router.
- Removed inline auth route handlers from `server.py`:
  - `POST /api/auth/register`
  - `POST /api/auth/login`
  - `GET /api/auth/me`
  - `GET /api/users`
- Kept auth Pydantic models in `backend/models/__init__.py` and imported them from `routers/auth.py`.
- Moved canonical auth helper usage through `backend/utils/auth.py`.
- Updated `utils.database` to honor `MONGO_TEST_DB_NAME` so router-level DB access uses the same test database selection as `server.py`.
- Preserved Indonesian auth error messages and the app-level `/api/auth/*` validation behavior.

## Verification

Commands run from `pltu-tenayan-full-backup/backend`:

```bash
./.venv/bin/python -m py_compile server.py routers/auth.py utils/auth.py utils/database.py
```

Result: passed.

```bash
TEST_ADMIN_EMAIL="$(awk '/^- Email:/{print $3; exit}' ../memory/test_credentials.md)" \
TEST_ADMIN_PASSWORD="$(awk '/^- Password:/{print $3; exit}' ../memory/test_credentials.md)" \
AI_FAKE=1 ./.venv/bin/pytest tests/test_auth_session.py -q
```

Result: `5 passed`.

Earlier role-suite smoke:

```bash
AI_FAKE=1 ./.venv/bin/pytest tests/test_auth_session.py tests/test_auth_roles.py -q
```

Result: `3 passed, 14 skipped` because operator/viewer/admin role environment variables were not all present in the shell.

## Residual Notes

- Full role matrix should be rerun when `TEST_OPERATOR_EMAIL`, `TEST_OPERATOR_PASSWORD`, `TEST_VIEWER_EMAIL`, and `TEST_VIEWER_PASSWORD` are available.
- Live backend process was not restarted during this plan; this was validated as code/test refactor work.
