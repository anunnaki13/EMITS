#!/usr/bin/env python3
"""Release-oriented repository hygiene check.

The check separates intentional local-only runtime state from source changes
that must be committed or cleaned before a release gate.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


INTENTIONAL_LOCAL_ONLY = {
    "README.md": "pre-existing tracked deletion; canonical repo docs live in readme.md and project docs",
    "backend/.env": "local backend runtime secrets/config; never commit real values",
    "frontend/.env": "local frontend runtime config; never commit real values",
}

PACK_CHURN_RE = re.compile(r"frontend/node_modules/\.cache/default-development/.+\.pack_?$")


@dataclass(frozen=True)
class StatusEntry:
    index: str
    worktree: str
    path: str
    raw: str


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=check)


def repo_root() -> Path:
    result = run(["git", "rev-parse", "--show-toplevel"])
    return Path(result.stdout.strip())


def parse_status(output: str) -> list[StatusEntry]:
    entries: list[StatusEntry] = []
    for line in output.splitlines():
        if not line:
            continue
        if len(line) < 4:
            entries.append(StatusEntry("?", "?", line.strip(), line))
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        entries.append(StatusEntry(line[0], line[1], path, line))
    return entries


def get_status_entries() -> list[StatusEntry]:
    result = run(["git", "status", "--porcelain=v1", "--untracked-files=normal"])
    return parse_status(result.stdout)


def classify_entries(entries: list[StatusEntry]) -> tuple[list[StatusEntry], list[StatusEntry]]:
    allowed: list[StatusEntry] = []
    blocking: list[StatusEntry] = []
    for entry in entries:
        is_local_only = entry.path in INTENTIONAL_LOCAL_ONLY
        is_worktree_only = entry.index == " " and entry.worktree in {"M", "D"}
        if is_local_only and is_worktree_only:
            allowed.append(entry)
        else:
            blocking.append(entry)
    return allowed, blocking


def check_gitignore_pack_churn(root: Path) -> list[str]:
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        return []
    offenders = []
    for line_number, line in enumerate(gitignore.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        for token in stripped.split():
            if PACK_CHURN_RE.search(token):
                offenders.append(f".gitignore:{line_number}: {stripped}")
    return offenders


def run_credential_scan(root: Path) -> tuple[bool, str]:
    scanner = root / "scripts" / "check_credentials.sh"
    result = subprocess.run(["bash", str(scanner)], text=True, capture_output=True)
    output = (result.stdout + result.stderr).strip()
    return result.returncode == 0, output


def main() -> int:
    parser = argparse.ArgumentParser(description="Check repo hygiene before release")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    root = repo_root()
    os.chdir(root)
    credential_ok, credential_output = run_credential_scan(root)
    entries = get_status_entries()
    allowed, blocking = classify_entries(entries)
    pack_churn = check_gitignore_pack_churn(root)

    ok = credential_ok and not blocking and not pack_churn
    payload = {
        "ok": ok,
        "credential_scan_ok": credential_ok,
        "allowed_local_only": [asdict(entry) | {"reason": INTENTIONAL_LOCAL_ONLY[entry.path]} for entry in allowed],
        "release_blocking": [asdict(entry) for entry in blocking],
        "gitignore_pack_churn": pack_churn,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("Repository hygiene check")
        print(f"- credential scan: {'pass' if credential_ok else 'fail'}")
        if credential_output:
            print(credential_output)
        print(f"- intentional local-only changes: {len(allowed)}")
        for entry in allowed:
            print(f"  allow {entry.raw} — {INTENTIONAL_LOCAL_ONLY[entry.path]}")
        print(f"- release-blocking changes: {len(blocking)}")
        for entry in blocking:
            print(f"  block {entry.raw}")
        print(f"- build-cache .gitignore churn: {len(pack_churn)}")
        for offender in pack_churn:
            print(f"  block {offender}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
