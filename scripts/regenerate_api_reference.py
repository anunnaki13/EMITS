#!/usr/bin/env python3
"""
Regenerate API_REFERENCE.md from live /openapi.json (D-04, D-06).

Idempotent: hand-curated content between
  <!-- BEGIN HAND-CURATED: <name> -->
  <!-- END HAND-CURATED: <name> -->
markers is preserved across runs. The auto-generated endpoint table is
replaced wholesale on each run inside
  <!-- BEGIN GENERATED -->
  <!-- END GENERATED -->.

Fetch order (5 second timeout each):
  1. http://localhost:8013/openapi.json    (local dev / VPS-as-self)
  2. http://103.150.197.225:8013/openapi.json  (live VPS)
  3. ${OPENAPI_URL}                        (env override; checked FIRST if set)

Exit codes:
  0  success — file written (and unchanged on second run)
  1  schema fetch failed
  2  prerequisite ADR missing or path error

Usage:
  python3 scripts/regenerate_api_reference.py
  OPENAPI_URL=http://otherhost:8013/openapi.json python3 scripts/regenerate_api_reference.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
OUT = REPO / "API_REFERENCE.md"

# Default fetch chain. ${OPENAPI_URL} is checked first when set.
OPENAPI_URLS_DEFAULT = [
    "http://localhost:8013/openapi.json",
    "http://103.150.197.225:8013/openapi.json",
]

BEGIN_GENERATED = "<!-- BEGIN GENERATED -->"
END_GENERATED = "<!-- END GENERATED -->"

HAND_CURATED_NAMES = ["header", "auth", "pagination", "errors", "examples"]

# Public endpoints (no Bearer required). Anything else with no security
# block in the operation is still rendered as Bearer because FastAPI omits
# the security marker on operations protected only by a route dependency.
PUBLIC_PATHS = {"/api/auth/login", "/api/auth/register", "/api/", "/api/health"}

# Endpoints whose schema is verified but whose live behavior depends on
# external services (LLM keys etc.) or whose execution would mutate live
# data — D-08 marks these `verified: schema-only`.
SCHEMA_ONLY_PREFIXES = (
    "/api/ai/",
    "/api/smart-blending/",
    "/api/upload/",
)

# ---------------------------------------------------------------------------
# Seed (default) hand-curated bodies. These are emitted on first run only;
# subsequent runs preserve operator edits between BEGIN/END HAND-CURATED.
# ---------------------------------------------------------------------------

SEED_HEADER = """\
# API Reference

Live FastAPI surface for the **PLTU Tenayan Fuel Management System**. The
endpoint inventory below is generated from `/openapi.json` by
`scripts/regenerate_api_reference.py` — re-run after any backend route change
and `git diff --exit-code API_REFERENCE.md` will surface drift.

Hand-curated narrative sections live between
`<!-- BEGIN HAND-CURATED: <name> -->` markers and are preserved across
regeneration. Sections in this file:

- Auth Contract — operational restatement of ADR-004
- Pagination Contract — operational restatement of ADR-008
- Error Code Map — semantic 4xx/5xx mapping per CONS-auth-header
- Endpoint Inventory — auto-generated from `/openapi.json`
- Per-Module Call Examples — hand-curated curl recipes (env-var sourced)

Source-of-truth for the live schema: the deployed FastAPI app exposes
`/openapi.json` on the same port as the API surface. Fetch order: env var
`OPENAPI_URL`, then `http://localhost:8013`, then `http://103.150.197.225:8013`.

> Note: the previous hand-edited 778-line API_REFERENCE.md (which inlined
> the admin password literal and was on the credential-scanner exemption
> list) was replaced by this regenerator on 2026-05-10 (Phase-3 plan 03-03).
"""

SEED_AUTH = """\
## Auth Contract

See `.planning/decisions/ADR-004-jwt-bcrypt-three-role-auth.md` (locked
2026-05-10) for the architectural decision; this section restates the
operational contract for API consumers and points at
`docs/audit/AUTH_CONTRACT.md` for the Phase-2 reconciliation record
(D-AUTH-01 422→400 remap; D-AUTH-02 403-on-missing-Authorization).

- **Token type:** JWT (HS256), issued by `POST /api/auth/login`.
- **Header:** `Authorization: Bearer <JWT>` on every protected endpoint.
- **Roles:** `admin`, `operator`, `viewer`. Role enforcement is server-side
  via the `require_role(...)` dependency in `backend/server.py`. FastAPI
  does NOT surface `require_role()` in `/openapi.json`, so the auto-generated
  table marks every secured endpoint as `Bearer`. Per-role authorization is
  cross-walked module-by-module in `docs/audit/AUTH_CONTRACT.md`.
- **Login error mapping (D-AUTH-01):** invalid credentials → `401`;
  malformed body on `/api/auth/*` → `400` (remapped from FastAPI's default
  `422` to satisfy the historical contract). Non-auth routes keep `422`.
- **Missing Authorization header (D-AUTH-02):** HTTPBearer dependency
  defaults to `403` (NOT `401`). Documented and accepted as the contract.
- **Public endpoints (no Bearer required):** `/api/auth/login`,
  `/api/auth/register`, `/api/`, `/api/health`. All other endpoints require
  an Authorization header.
"""

SEED_PAGINATION = """\
## Pagination Contract

See `.planning/decisions/ADR-008-pagination-shape.md` for the locked envelope
(CONS-pagination-shape).

Every paginated list endpoint returns:

```json
{
  "items": [ /* records */ ],
  "total": 461,
  "page": 1,
  "page_size": 50,
  "total_pages": 10
}
```

- **Query params:** `page` (default `1`), `page_size` (default `50`).
- **Operational caps:** most list endpoints `page_size <= 500`. The
  smart-stock list (`GET /api/smart-stock`) caps at `limit=50000`.
- **Frontend contract:** read `response.data.items`; never assume the
  response is a bare JSON array.
- **Counting:** `total` is the unfiltered-by-page count; `total_pages` is
  `ceil(total / page_size)`.
"""

SEED_ERRORS = """\
## Error Code Map

See `.planning/intel/constraints.md` → CONS-auth-header for the locked
semantic mapping. The `/api/auth/*` surface returns `400` for malformed
request bodies (Phase-2 D-AUTH-01 remap from FastAPI's default `422`);
non-auth routes keep the FastAPI `422` default.

| Code | Used by                                   | Semantic meaning |
|------|-------------------------------------------|-------------------------------------------------------------|
| 200  | all successful reads/writes               | success (request accepted, response body present)            |
| 400  | `/api/auth/*`                             | malformed request body (validation failure; D-AUTH-01)       |
| 401  | `/api/auth/login`, `/api/auth/me`         | invalid credentials OR invalid/expired token                 |
| 403  | any protected endpoint                    | role denied OR missing Authorization header (HTTPBearer; D-AUTH-02) |
| 404  | `*/{id}` lookups                          | record not found                                             |
| 422  | non-auth `POST/PUT/PATCH` endpoints       | malformed request body (FastAPI default — backwards compat)  |
| 500  | AI endpoints / LLM-integration paths      | internal error (e.g., `BudgetExceededError`, upstream LLM)   |

See `docs/audit/AUTH_CONTRACT.md` for the full Phase-2 reconciliation.
"""

SEED_EXAMPLES = """\
## Per-Module Call Examples

> **Credential hygiene:** The examples below source admin credentials from
> `memory/test_credentials.md` (gitignored, local-only). They never inline
> a password literal — `scripts/check_credentials.sh` is wired as the
> pre-commit hook and rejects literals on commit. Set
> `${TEST_ADMIN_EMAIL}` and `${TEST_ADMIN_PASSWORD}` in your shell before
> running these recipes.

```bash
cd pltu-tenayan-full-backup

# Source admin credentials from local memory/test_credentials.md (gitignored)
export TEST_ADMIN_EMAIL="$(grep -E '^- Email:' memory/test_credentials.md | head -1 | awk '{print $3}')"
export TEST_ADMIN_PASSWORD="$(grep -E '^- Password:' memory/test_credentials.md | head -1 | awk '{print $3}')"

# Login (returns access_token + user envelope)
TOKEN="$(curl -fsS -X POST http://103.150.197.225:8013/api/auth/login \\
  -H 'Content-Type: application/json' \\
  -d "$(python3 -c 'import json,os;print(json.dumps({"email":os.environ["TEST_ADMIN_EMAIL"],"password":os.environ["TEST_ADMIN_PASSWORD"]}))')" \\
  | python3 -c 'import json,sys;print(json.load(sys.stdin)["access_token"])')"

# /me — Bearer-token rehydrate
curl -fsS http://103.150.197.225:8013/api/auth/me \\
  -H "Authorization: Bearer $TOKEN"

# Vessels list (paginated; verifies the {items,total,page,page_size,total_pages} envelope)
curl -fsS "http://103.150.197.225:8013/api/vessels?page=1&page_size=2" \\
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -20

# Health probe (public — no Bearer)
curl -fsS http://103.150.197.225:8013/api/health

# Cleanup
unset TEST_ADMIN_EMAIL TEST_ADMIN_PASSWORD TOKEN
```

For per-endpoint behavior verification (status codes / payload shape), see
`docs/audit/API_REFERENCE_SPOTCHECK.md`.
"""

SEED_HAND: dict[str, str] = {
    "header": SEED_HEADER,
    "auth": SEED_AUTH,
    "pagination": SEED_PAGINATION,
    "errors": SEED_ERRORS,
    "examples": SEED_EXAMPLES,
}


# ---------------------------------------------------------------------------
# Schema fetch
# ---------------------------------------------------------------------------

def fetch_openapi() -> dict[str, Any]:
    """Try OPENAPI_URL (env), then localhost, then VPS. Raises on total failure."""
    urls: list[str] = []
    env_url = os.environ.get("OPENAPI_URL", "").strip()
    if env_url:
        urls.append(env_url)
    urls.extend(OPENAPI_URLS_DEFAULT)

    last_err: tuple[str, BaseException] | None = None
    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                return json.loads(resp.read())
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
            last_err = (url, e)
            continue
    raise SystemExit(
        f"openapi fetch failed (last attempt: {last_err}). "
        "Bring up uvicorn — see LOCAL_SETUP.md §VPS Service Recovery."
    )


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def _request_schema_label(op: dict[str, Any]) -> str:
    rb = op.get("requestBody")
    if not rb:
        return "—"
    schema = (rb.get("content", {}).get("application/json", {}) or {}).get("schema", {}) or {}
    ref = schema.get("$ref")
    if ref:
        return f"`{ref.split('/')[-1]}`"
    if schema.get("type"):
        return f"`{schema['type']}`"
    return "—"


def _auth_label(path: str, op: dict[str, Any]) -> str:
    sec = op.get("security")
    # Public if path is in the public allowlist AND no per-op security override.
    if path in PUBLIC_PATHS and (sec is None or sec == [] or sec == [{}]):
        return "public"
    # FastAPI emits `security` only for HTTPBearer-decorated endpoints; absent
    # security on non-public paths still implies a route-level dependency
    # (require_role()) — treat as Bearer for the table.
    return "Bearer"


def _verified_label(path: str) -> str:
    if any(path.startswith(prefix) for prefix in SCHEMA_ONLY_PREFIXES):
        return "schema-only"
    # Destructive collection-level deletes: schema-only (running them would
    # destroy production data — D-08).
    return "live"


def render_table(spec: dict[str, Any]) -> str:
    rows: list[str] = []
    rows.append("| Method | Path | Auth | Request schema | Responses | Verified |")
    rows.append("|--------|------|------|----------------|-----------|----------|")
    paths: dict[str, dict[str, Any]] = spec.get("paths", {}) or {}

    for path in sorted(paths.keys()):
        ops = paths[path] or {}
        for method in sorted(ops.keys()):
            if method.lower() not in ("get", "post", "put", "patch", "delete"):
                continue
            op = ops[method] or {}
            req = _request_schema_label(op)
            resp_codes = ",".join(sorted((op.get("responses", {}) or {}).keys()))
            auth = _auth_label(path, op)
            verified = _verified_label(path)
            # Mark collection-level DELETE as schema-only too (don't run live).
            if method.lower() == "delete" and re.fullmatch(r"/api/[a-z0-9-]+", path):
                verified = "schema-only"
            rows.append(
                f"| {method.upper()} | `{path}` | {auth} | {req} | {resp_codes} | {verified} |"
            )
    return "\n".join(rows)


def parse_existing(text: str) -> dict[str, str]:
    """Extract preserved hand-curated content by name."""
    out: dict[str, str] = {}
    for name in HAND_CURATED_NAMES:
        m = re.search(
            rf"<!-- BEGIN HAND-CURATED: {re.escape(name)} -->\n(.*?)\n<!-- END HAND-CURATED: {re.escape(name)} -->",
            text,
            flags=re.DOTALL,
        )
        if m:
            out[name] = m.group(1)
    return out


def render_doc(generated_table: str, hand: dict[str, str], total_endpoints: int) -> str:
    def block(name: str) -> str:
        body = hand.get(name)
        if body is None:
            body = SEED_HAND[name].rstrip("\n")
        return f"<!-- BEGIN HAND-CURATED: {name} -->\n{body}\n<!-- END HAND-CURATED: {name} -->"

    intro = (
        f"## Endpoint Inventory (auto-generated)\n\n"
        f"_{total_endpoints} method/path pairs discovered in `/openapi.json`. "
        f"Re-run `scripts/regenerate_api_reference.py` to refresh._\n"
    )

    sections = [
        block("header"),
        block("auth"),
        block("pagination"),
        block("errors"),
        intro,
        BEGIN_GENERATED,
        generated_table,
        END_GENERATED,
        block("examples"),
    ]
    return "\n\n".join(sections) + "\n"


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> int:
    # Sanity: ADR cross-links must exist (Plan 03-01 dependency).
    adr_root = REPO.parent / ".planning" / "decisions"
    for adr in (
        "ADR-004-jwt-bcrypt-three-role-auth.md",
        "ADR-008-pagination-shape.md",
    ):
        if not (adr_root / adr).is_file():
            print(f"missing prerequisite: {adr_root / adr}", file=sys.stderr)
            return 2

    spec = fetch_openapi()
    paths = spec.get("paths", {}) or {}
    total = sum(
        1
        for p in paths
        for m in (paths[p] or {})
        if m.lower() in ("get", "post", "put", "patch", "delete")
    )

    table = render_table(spec)
    hand = parse_existing(OUT.read_text(encoding="utf-8")) if OUT.is_file() else {}
    doc = render_doc(table, hand, total)
    OUT.write_text(doc, encoding="utf-8")
    print(f"wrote {OUT} ({len(doc)} bytes; {total} endpoints)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
