# EMITS Production Runbook

This runbook is the Phase 22 operational source of truth for deploying, checking, and rolling back the single-host EMITS installation.

## Host Model

- Source checkout: `/opt/pltu-tenayan/app`
- Backend: FastAPI via systemd service `emits-backend`, bound to `127.0.0.1:8013`
- Frontend: React static build served from `/var/www/emits` through static nginx; production operation must not depend on `yarn start`
- Frontend fallback: if nginx cannot be used, `emits-frontend-static` can serve `/var/www/emits` on `0.0.0.0:3013`
- Public ingress: nginx, reverse proxying `/api/*` to backend
- Database: MongoDB on the same host unless `MONGO_URL` points elsewhere
- Smoke evidence: `/var/log/emits/smoke/*.json`
- Runtime evidence: `/var/log/emits/runtime/*.txt`
- Logs:
  - Backend: `journalctl -u emits-backend`
  - Nginx: `/var/log/nginx/emits.access.log`, `/var/log/nginx/emits.error.log`

## First-Time Installation

1. Copy `ops/systemd/emits-backend.service.example` to `/etc/systemd/system/emits-backend.service`.
2. Copy `ops/nginx/emits.conf.example` to `/etc/nginx/sites-available/emits` and symlink it into `sites-enabled`.
   - If this host must expose the React build directly on port `3013`, copy `ops/systemd/emits-frontend-static.service.example` to `/etc/systemd/system/emits-frontend-static.service` instead of relying on a tmux/manual Python process.
3. Copy `ops/env/backend.env.example` to `backend/.env` on the host and fill real values there.
4. Copy `ops/env/frontend.env.example` to `frontend/.env` before building the frontend.
5. Create writable directories:

```bash
sudo mkdir -p /var/www/emits /var/log/emits /opt/pltu-tenayan/backups/deploy /opt/pltu-tenayan/backups/managed
sudo chown -R www-data:www-data /var/log/emits /opt/pltu-tenayan/app/backend/backups /opt/pltu-tenayan/backups
```

6. Enable services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable emits-backend
sudo systemctl enable emits-frontend-static # only for direct-port frontend mode
sudo nginx -t
sudo systemctl reload nginx
```

## Standard Deploy

Run from the host after `.env` values and service files are installed:

```bash
cd /opt/pltu-tenayan/app
EMITS_BASE_URL=http://127.0.0.1:8013 \
EMITS_FRONTEND_URL=http://127.0.0.1 \
ops/scripts/deploy.sh
```

The deploy script performs:

- clean working tree check
- `git pull --ff-only`
- pre-deploy `mongodump`
- backend dependency install
- frontend install/build
- static frontend `version.json` generation with git/build metadata
- frontend publish via `rsync --delete`
- backend restart and nginx reload
- smoke check with JSON smoke evidence under `SMOKE_EVIDENCE_DIR`, including `/api/health/version` so stale backend/frontend builds are caught

If `TEST_ADMIN_EMAIL` and `TEST_ADMIN_PASSWORD` are present in the shell environment, the deploy smoke check also records the result to `/api/admin/runtime/smoke-report`. Do not put those credentials in committed files.

## Runtime Status

Use the runtime status command after deploy, backend restart, nginx config edits, MongoDB maintenance, or host reboot:

```bash
cd /opt/pltu-tenayan/app
EMITS_BASE_URL=http://127.0.0.1:8013 \
EMITS_FRONTEND_URL=http://127.0.0.1 \
ops/scripts/runtime_status.sh
```

The command checks:

- backend `/api/health`
- backend `/api/health/version` deployment identity
- static nginx frontend
- `systemctl is-active emits-backend`
- `nginx -t`
- disk usage
- latest deploy and managed backup directories
- smoke check with JSON smoke evidence

The command writes a timestamped runtime report transcript under `RUNTIME_EVIDENCE_DIR` (default `/var/log/emits/runtime`) and prints both evidence paths at the end:

- runtime report: `/var/log/emits/runtime/runtime-status-<timestamp>.txt`
- smoke JSON: `/var/log/emits/smoke/status-smoke-<timestamp>.json`

The in-app admin panel at Settings → `Status Operasional` reads `/api/admin/runtime/status`. That endpoint is admin-only and returns allowlisted runtime facts only: version/build metadata, backend, MongoDB, static frontend presence, backup health, latest smoke status, and disk usage.

## v1.4 Release Gate

Run this gate on the production VPS after pulling the release commit or tag:

```bash
cd /opt/pltu-tenayan/app
git status --short
git rev-parse --short HEAD

python3 ops/scripts/release_gate.py \
  --base-url http://127.0.0.1:8013 \
  --frontend-url http://127.0.0.1

EMITS_BASE_URL=http://127.0.0.1:8013 \
EMITS_FRONTEND_URL=http://127.0.0.1 \
ops/scripts/deploy.sh

EMITS_BASE_URL=http://127.0.0.1:8013 \
EMITS_FRONTEND_URL=http://127.0.0.1 \
ops/scripts/runtime_status.sh
```

Release evidence is complete only when all of these are true:

- `ops/scripts/deploy.sh` completes without error.
- `ops/scripts/release_gate.py` exits 0 and writes JSON/Markdown artifacts under `ops/release-artifacts/`.
- `ops/scripts/runtime_status.sh` exits 0.
- The runtime report path and smoke JSON path printed by `runtime_status.sh` exist on the VPS.
- Settings → `Status Operasional` shows the latest smoke result and backend/frontend build identifiers for the deployed SHA or release tag.

If `TEST_ADMIN_EMAIL` and `TEST_ADMIN_PASSWORD` are available only in the operator shell, export them before the deploy/runtime commands so smoke status is also recorded through `/api/admin/runtime/smoke-report`. Unset them after the gate. Never write those values into committed files or pasted release notes.

If the real VPS cannot be reached during development, do not mark runtime verification as passed. Record the release as a manual gate with:

- target host and expected command
- release commit/tag
- reason the command was not executed
- owner who must run it
- expected evidence paths under `/var/log/emits/runtime` and `/var/log/emits/smoke`

Evidence retention policy: keep v1.4 release runtime reports and smoke JSON for at least 90 days, or until the next production milestone audit is accepted. Older routine smoke artifacts may be rotated by host log retention once they are no longer tied to a release gate.

## Smoke Check Only

Use this after any manual restart, data import, nginx edit, or host reboot:

```bash
cd /opt/pltu-tenayan/app
set -a
. backend/.env
set +a
export TEST_ADMIN_EMAIL="$(awk '$0=="## Akun Admin"{in_section=1;next} in_section && /^## /{exit} in_section && /Email:/{sub(/^- Email:[[:space:]]*/,"");print;exit}' memory/test_credentials.md)"
export TEST_ADMIN_PASSWORD="$(awk '$0=="## Akun Admin"{in_section=1;next} in_section && /^## /{exit} in_section && /Password:/{sub(/^- Password:[[:space:]]*/,"");print;exit}' memory/test_credentials.md)"

backend/.venv/bin/python ops/scripts/smoke_check.py \
  --base-url http://127.0.0.1:8013 \
  --frontend-url http://127.0.0.1 \
  --json-output /var/log/emits/smoke/manual-smoke-$(date -u +%Y%m%dT%H%M%SZ).json \
  --record-status

unset TEST_ADMIN_EMAIL TEST_ADMIN_PASSWORD
```

The smoke check covers backend health, frontend, MongoDB ping, login, `/api/auth/me`, dashboard stats, operational dashboard, COA list/KPIs, and management report.

If credentials are unavailable, omit `--record-status`; the JSON artifact is still valid smoke evidence for operations review.

## Failure Triage

Use this order to isolate production incidents:

```bash
sudo systemctl status emits-backend
journalctl -u emits-backend -n 100 --no-pager
sudo nginx -t
sudo systemctl reload nginx
curl -fsS http://127.0.0.1:8013/api/health
df -h /var/www/emits
ls -lt /var/log/emits/smoke | head
```

If the frontend loads but API requests fail, focus on nginx `/api/` proxy and backend service state. If login fails after a restart, verify `JWT_SECRET`, `MONGO_URL`, and `DB_NAME` in the host-only `backend/.env` without copying values into tickets or commits.

## Rollback

### Code Rollback

1. Identify the last known-good commit:

```bash
cd /opt/pltu-tenayan/app
git log --oneline -10
```

2. Reset the host checkout to that commit only after confirming no local operational edits are in the working tree:

```bash
git status --short
git checkout <known-good-commit>
```

3. Re-run the standard deploy script.

### Data Rollback

- For backup automation output: restore through the admin restore validation flow first.
- For COA import mistakes: use the admin-only COA import history rollback action created in Phase 18.
- For deploy-level database rollback: restore the pre-deploy `mongodump` directory produced by `ops/scripts/deploy.sh`.

Example deploy backup restore:

```bash
mongorestore --drop --uri="$MONGO_URL" --db "$DB_NAME" /opt/pltu-tenayan/backups/deploy/<timestamp>/<DB_NAME>
```

Run the smoke check after every rollback.

## Repository Hygiene

Tracked source boundaries:

- Application source: `backend/`, `frontend/src/`, `frontend/public/`, `ops/`, `scripts/`, `docs/`, `.planning/`
- Runtime/generated data: not deployable source
  - `backend/.env`, `frontend/.env`
  - `backend/backups/`
  - Python/Node caches and build output

Current local dirty artifacts may exist on the working host because older snapshots tracked or generated them. Do not commit secrets or runtime state. Use `.env.example` / `ops/env/*.example` for documentation, and handle tracked-file cleanup in a dedicated hygiene change only after confirming the active deployment no longer depends on those files.

Run the release hygiene gate before tagging or deploying source changes:

```bash
python3 scripts/check_repo_hygiene.py
```

The gate allows the documented local-only runtime paths above when they are
unstaged, runs the credential scanner, and blocks unexpected dirty source files
or individual frontend webpack cache pack entries in `.gitignore`. See
`docs/operations/REPO_HYGIENE.md` for the full allowlist and policy.
