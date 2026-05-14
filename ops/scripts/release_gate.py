#!/usr/bin/env python3
"""Run the EMITS v1.4 local release gate and write evidence artifacts."""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BACKEND_TEST_GROUPS = [
    ("backend_auth", ["tests/test_auth_session.py", "tests/test_auth_roles.py"]),
    ("backend_dashboard", ["tests/test_dashboard_operational.py", "tests/test_dashboard_drilldown_filters.py"]),
    ("backend_coa_import", ["tests/test_coa_combined_workbook.py", "tests/test_coa_reconciliation.py", "tests/test_import_preview.py", "tests/test_upload_excel.py"]),
    ("backend_reports_quality", ["tests/test_management_reports.py", "tests/test_data_quality.py"]),
    ("backend_trends_advisor", ["tests/test_trend_analytics.py", "tests/test_ai_advisor_v3.py"]),
    ("backend_runtime_rekap", ["tests/test_admin_runtime_status.py", "tests/test_rekap_filters.py"]),
]

REQUIRED_TEST_ENV = [
    "TEST_ADMIN_EMAIL",
    "TEST_ADMIN_PASSWORD",
    "TEST_OPERATOR_EMAIL",
    "TEST_OPERATOR_PASSWORD",
    "TEST_VIEWER_EMAIL",
    "TEST_VIEWER_PASSWORD",
]

SECRET_MARKERS = ("PASSWORD", "TOKEN", "SECRET", "KEY", "MONGO_URL", "API_KEY")


@dataclass
class StepResult:
    name: str
    command: list[str]
    cwd: str
    status: str
    exit_code: int | None
    duration_seconds: float
    stdout_tail: str = ""
    stderr_tail: str = ""
    reason: str | None = None
    artifact: str | None = None
    warnings: list[str] = field(default_factory=list)


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> Path:
    result = subprocess.run(["git", "rev-parse", "--show-toplevel"], text=True, capture_output=True, check=True)
    return Path(result.stdout.strip())


def tail(text: str, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def safe_command(command: list[str]) -> list[str]:
    redacted = []
    redact_next = False
    sensitive_flags = {"--password", "--email", "--mongo-url", "--db-name"}
    for item in command:
        if redact_next:
            redacted.append("<redacted>")
            redact_next = False
            continue
        if item in sensitive_flags:
            redacted.append(item)
            redact_next = True
            continue
        upper = item.upper()
        if any(marker in upper for marker in SECRET_MARKERS) or "://" in item and "@" in item:
            redacted.append("<redacted>")
        else:
            redacted.append(item)
    return redacted


def run_step(name: str, command: list[str], *, cwd: Path, env: dict[str, str] | None = None, timeout: int | None = None) -> StepResult:
    started = time.monotonic()
    try:
        result = subprocess.run(command, cwd=str(cwd), env=env, text=True, capture_output=True, timeout=timeout)
        duration = time.monotonic() - started
        return StepResult(
            name=name,
            command=safe_command(command),
            cwd=str(cwd),
            status="passed" if result.returncode == 0 else "failed",
            exit_code=result.returncode,
            duration_seconds=round(duration, 2),
            stdout_tail=tail(result.stdout or ""),
            stderr_tail=tail(result.stderr or ""),
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - started
        return StepResult(
            name=name,
            command=safe_command(command),
            cwd=str(cwd),
            status="failed",
            exit_code=None,
            duration_seconds=round(duration, 2),
            stdout_tail=tail(exc.stdout or ""),
            stderr_tail=tail(exc.stderr or ""),
            reason=f"timed out after {timeout}s",
        )


def skipped_step(name: str, reason: str, command: list[str] | None = None, cwd: Path | None = None, *, warning: str | None = None) -> StepResult:
    return StepResult(
        name=name,
        command=safe_command(command or []),
        cwd=str(cwd or Path.cwd()),
        status="skipped",
        exit_code=None,
        duration_seconds=0.0,
        reason=reason,
        warnings=[warning] if warning else [],
    )


def have_test_credentials(env: dict[str, str]) -> bool:
    return all(env.get(name) for name in REQUIRED_TEST_ENV)


def port_open(url: str, timeout: float = 2.0) -> bool:
    try:
        req = urllib.request.Request(url.rstrip("/") + "/api/health", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, TimeoutError, socket.timeout, ValueError):
        return False


def git_value(root: Path, command: list[str]) -> str | None:
    result = subprocess.run(command, cwd=str(root), text=True, capture_output=True)
    value = result.stdout.strip()
    return value or None


def write_artifacts(root: Path, artifact_dir: Path, payload: dict[str, Any]) -> tuple[Path, Path]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    base = f"release-gate-{payload['started_at'].replace(':', '').replace('-', '').split('.')[0]}"
    json_path = artifact_dir / f"{base}.json"
    md_path = artifact_dir / f"{base}.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# EMITS Release Gate",
        "",
        f"- Started: `{payload['started_at']}`",
        f"- Finished: `{payload['finished_at']}`",
        f"- Status: `{payload['status']}`",
        f"- Git SHA: `{payload.get('git_sha') or 'unknown'}`",
        f"- Git tag: `{payload.get('git_tag') or 'none'}`",
        f"- Next action: {payload['next_action']}",
        "",
        "## Steps",
        "",
        "| Step | Status | Exit | Duration | Notes |",
        "|------|--------|------|----------|-------|",
    ]
    for step in payload["steps"]:
        note = step.get("reason") or "; ".join(step.get("warnings") or []) or step.get("artifact") or ""
        lines.append(
            f"| `{step['name']}` | `{step['status']}` | `{step.get('exit_code')}` | "
            f"{step['duration_seconds']}s | {note} |"
        )
    lines.extend([
        "",
        "## Skips And Warnings",
        "",
    ])
    warnings = payload.get("warnings") or []
    if warnings:
        lines.extend([f"- {item}" for item in warnings])
    else:
        lines.append("- None.")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run EMITS v1.4 release gate")
    parser.add_argument("--artifact-dir", type=Path, default=None, help="Directory for JSON/Markdown release evidence")
    parser.add_argument("--base-url", default=os.environ.get("EMITS_BASE_URL", "http://127.0.0.1:8013"))
    parser.add_argument("--frontend-url", default=os.environ.get("EMITS_FRONTEND_URL", "http://127.0.0.1:3013"))
    parser.add_argument("--skip-frontend", action="store_true")
    parser.add_argument("--skip-smoke", action="store_true")
    parser.add_argument("--record-smoke-status", action="store_true", help="Authenticate smoke check and record status through the admin API")
    parser.add_argument("--allow-skips", action="store_true", help="Do not fail the gate when a step is skipped with a reason")
    parser.add_argument("--require-smoke", action="store_true", help="Fail when backend health is unavailable for smoke")
    parser.add_argument("--timeout", type=int, default=900, help="Per-step timeout in seconds")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = repo_root()
    artifact_dir = args.artifact_dir or root / "ops" / "release-artifacts"
    started_at = utc_iso()
    env = dict(os.environ)
    backend_env = load_env_file(root / "backend" / ".env")
    for key in ["MONGO_URL", "DB_NAME", "JWT_SECRET"]:
        if not env.get(key) and backend_env.get(key):
            env[key] = backend_env[key]

    steps: list[StepResult] = []
    warnings: list[str] = []

    steps.append(run_step("repo_hygiene", [sys.executable, "scripts/check_repo_hygiene.py"], cwd=root, env=env, timeout=args.timeout))

    if have_test_credentials(env):
        for group_name, tests in BACKEND_TEST_GROUPS:
            backend_cmd = [str(root / "backend" / ".venv" / "bin" / "python"), "-m", "pytest", *tests, "-q"]
            steps.append(run_step(group_name, backend_cmd, cwd=root / "backend", env=env, timeout=args.timeout))
    elif (root / "memory" / "test_credentials.md").exists():
        for group_name, tests in BACKEND_TEST_GROUPS:
            backend_cmd = ["ops/scripts/pytest_with_local_credentials.sh", *tests, "-q"]
            steps.append(run_step(group_name, backend_cmd, cwd=root, env=env, timeout=args.timeout))
    else:
        reason = "missing TEST_* credentials and memory/test_credentials.md"
        warnings.append(f"backend_focused_pytest skipped: {reason}")
        steps.append(skipped_step("backend_focused_pytest", reason, cwd=root, warning="backend regressions require local-only test credentials"))

    if args.skip_frontend:
        reason = "--skip-frontend was provided"
        warnings.append(f"frontend_build_checked skipped: {reason}")
        steps.append(skipped_step("frontend_build_checked", reason, cwd=root / "frontend"))
    else:
        frontend_env = {**env, "CI": "false"}
        steps.append(run_step("frontend_build_checked", ["npm", "run", "build:checked"], cwd=root / "frontend", env=frontend_env, timeout=args.timeout))

    smoke_json = artifact_dir / f"smoke-{utc_stamp()}.json"
    if args.skip_smoke:
        reason = "--skip-smoke was provided"
        warnings.append(f"smoke_check skipped: {reason}")
        steps.append(skipped_step("smoke_check", reason, cwd=root))
    elif not port_open(args.base_url):
        reason = f"backend health unavailable at {args.base_url}/api/health"
        warnings.append(f"smoke_check skipped: {reason}")
        steps.append(skipped_step("smoke_check", reason, cwd=root, warning="run smoke on the production host before release"))
        if args.require_smoke:
            steps[-1] = StepResult(**{**asdict(steps[-1]), "status": "failed"})
    else:
        smoke_cmd = [
            str(root / "backend" / ".venv" / "bin" / "python"),
            "ops/scripts/smoke_check.py",
            "--base-url",
            args.base_url,
            "--frontend-url",
            args.frontend_url,
            "--json-output",
            str(smoke_json),
        ]
        if env.get("MONGO_URL"):
            smoke_cmd.extend(["--mongo-url", env["MONGO_URL"]])
        if env.get("DB_NAME"):
            smoke_cmd.extend(["--db-name", env["DB_NAME"]])
        if args.record_smoke_status and env.get("TEST_ADMIN_EMAIL") and env.get("TEST_ADMIN_PASSWORD"):
            smoke_cmd.extend(["--email", env["TEST_ADMIN_EMAIL"], "--password", env["TEST_ADMIN_PASSWORD"], "--record-status"])
        else:
            smoke_cmd.append("--skip-auth")
            if args.record_smoke_status:
                warnings.append("smoke_check auth endpoints skipped: TEST_ADMIN_EMAIL/PASSWORD unavailable")
            else:
                warnings.append("smoke_check auth endpoints skipped: --record-smoke-status not provided")
        smoke = run_step("smoke_check", smoke_cmd, cwd=root, env=env, timeout=args.timeout)
        smoke.artifact = str(smoke_json)
        steps.append(smoke)

    blocking_failed = any(step.status == "failed" for step in steps)
    skipped = [step for step in steps if step.status == "skipped"]
    status = "failed" if blocking_failed or (skipped and not args.allow_skips) else "passed"
    if skipped and status == "failed":
        warnings.append("one or more steps were skipped; rerun with required services/credentials or --allow-skips")

    payload = {
        "started_at": started_at,
        "finished_at": utc_iso(),
        "status": status,
        "git_sha": git_value(root, ["git", "rev-parse", "HEAD"]),
        "git_tag": git_value(root, ["git", "describe", "--tags", "--exact-match", "HEAD"]),
        "dirty_short": git_value(root, ["git", "status", "--short"]),
        "steps": [asdict(step) for step in steps],
        "warnings": warnings,
        "next_action": "Review artifacts, resolve failed/skipped release checks, then run production runtime_status.sh before tagging.",
    }
    json_path, md_path = write_artifacts(root, artifact_dir, payload)

    for step in steps:
        print(f"{step.status.upper():7} {step.name:<24} {step.duration_seconds:>6.2f}s")
        if step.reason:
            print(f"        reason: {step.reason}")
    print(f"Artifact JSON: {json_path}")
    print(f"Artifact MD: {md_path}")
    print(f"Release gate status: {status}")

    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
