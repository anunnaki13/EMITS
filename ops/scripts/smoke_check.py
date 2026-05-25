#!/usr/bin/env python3
"""Production smoke check for EMITS.

Run from the backend virtualenv so pymongo is available:

    cd /opt/pltu-tenayan/app
    backend/.venv/bin/python ops/scripts/smoke_check.py \
      --base-url http://127.0.0.1:8013 \
      --frontend-url http://127.0.0.1
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _payload(
    *,
    started_at: str,
    finished_at: str,
    base_url: str,
    frontend_url: str | None,
    results: list[CheckResult],
) -> dict[str, Any]:
    result_items = [{"name": result.name, "ok": result.ok, "detail": result.detail} for result in results]
    passed = sum(1 for result in results if result.ok)
    failed = len(results) - passed
    return {
        "started_at": started_at,
        "finished_at": finished_at,
        "base_url": base_url,
        "frontend_url": frontend_url,
        "passed": passed,
        "failed": failed,
        "results": result_items,
    }


def _write_json_output(path: str, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _request(method: str, url: str, payload: dict[str, Any] | None = None, token: str | None = None, timeout: int = 30) -> tuple[int, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read()
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            body = json.loads(raw.decode("utf-8"))
        else:
            body = raw.decode("utf-8", errors="replace")
        return response.status, body


def _check_http(name: str, method: str, url: str, payload: dict[str, Any] | None = None, token: str | None = None) -> tuple[CheckResult, Any]:
    try:
        status, body = _request(method, url, payload=payload, token=token)
        ok = 200 <= status < 300
        return CheckResult(name, ok, f"HTTP {status}"), body
    except urllib.error.HTTPError as exc:
        return CheckResult(name, False, f"HTTP {exc.code}"), None
    except Exception as exc:
        return CheckResult(name, False, str(exc)), None


def _check_frontend(frontend_url: str | None) -> CheckResult:
    if not frontend_url:
        return CheckResult("frontend", True, "skipped")
    try:
        req = urllib.request.Request(frontend_url, method="GET", headers={"Accept": "text/html"})
        with urllib.request.urlopen(req, timeout=30) as response:
            body = response.read(4096).decode("utf-8", errors="replace")
            ok = 200 <= response.status < 300 and ("root" in body or "EMITS" in body or "<html" in body.lower())
            return CheckResult("frontend", ok, f"HTTP {response.status}")
    except Exception as exc:
        return CheckResult("frontend", False, str(exc))


def _check_mongo(mongo_url: str | None, db_name: str | None) -> CheckResult:
    if not mongo_url or not db_name:
        return CheckResult("mongodb", False, "MONGO_URL and DB_NAME are required")
    try:
        import pymongo

        client = pymongo.MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        count = client[db_name].list_collection_names()
        client.close()
        return CheckResult("mongodb", True, f"ping ok, collections={len(count)}")
    except Exception as exc:
        return CheckResult("mongodb", False, str(exc))


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-check EMITS deployment")
    parser.add_argument("--base-url", default=os.environ.get("EMITS_BASE_URL", "http://127.0.0.1:8013"))
    parser.add_argument("--frontend-url", default=os.environ.get("EMITS_FRONTEND_URL"))
    parser.add_argument("--mongo-url", default=os.environ.get("MONGO_URL"))
    parser.add_argument("--db-name", default=os.environ.get("DB_NAME"))
    parser.add_argument("--email", default=os.environ.get("TEST_ADMIN_EMAIL"))
    parser.add_argument("--password", default=os.environ.get("TEST_ADMIN_PASSWORD"))
    parser.add_argument("--json-output", help="Write structured smoke evidence JSON to this path")
    parser.add_argument("--record-status", action="store_true", help="Post smoke evidence to /api/admin/runtime/smoke-report when auth succeeds")
    parser.add_argument("--skip-auth", action="store_true")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    started_at = _now_iso()
    results: list[CheckResult] = []

    health, _ = _check_http("backend health", "GET", f"{base_url}/api/health")
    results.append(health)
    version_check, version_body = _check_http("backend version", "GET", f"{base_url}/api/health/version")
    if isinstance(version_body, dict):
        backend_git = ((version_body.get("backend") or {}).get("version") or {}).get("git_sha")
        frontend_git = ((version_body.get("frontend") or {}).get("version") or {}).get("git_sha")
        detail = f"backend={backend_git or 'unknown'}, frontend={frontend_git or 'unknown'}"
        if not version_body.get("versions_match") and frontend_git:
            detail = f"{detail}, mismatch"
            version_check = CheckResult("backend version", False, detail)
        elif version_check.ok:
            version_check = CheckResult("backend version", True, detail)
    results.append(version_check)
    results.append(_check_frontend(args.frontend_url))
    results.append(_check_mongo(args.mongo_url, args.db_name))

    token = None
    if args.skip_auth:
        results.append(CheckResult("auth login", True, "skipped"))
    elif not args.email or not args.password:
        results.append(CheckResult("auth login", False, "TEST_ADMIN_EMAIL and TEST_ADMIN_PASSWORD are required"))
    else:
        login, body = _check_http(
            "auth login",
            "POST",
            f"{base_url}/api/auth/login",
            payload={"email": args.email, "password": args.password},
        )
        results.append(login)
        if isinstance(body, dict):
            token = body.get("access_token")
        if not token:
            results.append(CheckResult("auth token", False, "missing access_token"))

    if token:
        endpoints = [
            ("auth me", "/api/auth/me"),
            ("dashboard stats", "/api/dashboard/stats"),
            ("dashboard operational", "/api/dashboard/operational?period=all"),
            ("coa list", "/api/coa-reconciliation?page=1&page_size=1"),
            ("coa kpis", "/api/coa-reconciliation/kpis"),
            ("management report", "/api/reports/management?period=all"),
        ]
        for name, path in endpoints:
            check, _ = _check_http(name, "GET", f"{base_url}{path}", token=token)
            results.append(check)

    if args.record_status:
        record_payload = _payload(
            started_at=started_at,
            finished_at=_now_iso(),
            base_url=base_url,
            frontend_url=args.frontend_url,
            results=results,
        )
        if not token:
            results.append(CheckResult("record smoke status", False, "admin token unavailable"))
        else:
            record_check, _ = _check_http(
                "record smoke status",
                "POST",
                f"{base_url}/api/admin/runtime/smoke-report",
                payload=record_payload,
                token=token,
            )
            results.append(record_check)

    final_payload = _payload(
        started_at=started_at,
        finished_at=_now_iso(),
        base_url=base_url,
        frontend_url=args.frontend_url,
        results=results,
    )

    if args.json_output:
        _write_json_output(args.json_output, final_payload)

    width = max(len(result.name) for result in results)
    for result in results:
        status = "PASS" if result.ok else "FAIL"
        print(f"{status} {result.name:<{width}} {result.detail}")

    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
