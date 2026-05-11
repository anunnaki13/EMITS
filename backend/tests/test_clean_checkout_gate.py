"""TEST-01: clean-checkout acceptance gate (structural verification).

The literal SC-1 bar -- ``pytest backend/tests -q`` exits 0 on a clean
checkout -- is a manual gate the developer runs separately (see
tests/TEST-RUNNER.md). This in-suite test verifies the STRUCTURE:
all Phase-4 test files exist, all required Wave-0 deliverables exist,
and pytest --collect-only succeeds (i.e., no import errors prevent
discovery).
"""
import subprocess
import sys
from pathlib import Path
import pytest


BACKEND_DIR = Path(__file__).parent.parent  # pltu-tenayan-full-backup/backend/
TESTS_DIR = Path(__file__).parent


PHASE4_TEST_FILES = [
    "test_conftest_lifecycle.py",
    "test_pagination_shape.py",
    "test_upload_excel.py",
    "test_ai_endpoints.py",
]

WAVE0_DELIVERABLES = [
    "fakes/ai_client.py",
    "factories/__init__.py",
    "helpers/pagination.py",
    "helpers/jwt.py",
    "fixtures/excel/vessel_minimal.xlsx",
    "fixtures/excel/barge_minimal.xlsx",
    "fixtures/excel/trucking_minimal.xlsx",
    "fixtures/excel/biomassa_minimal.xlsx",
    "fixtures/excel/HEADER_VARIANTS.md",
]


def test_all_phase4_test_files_present():
    """SC-1 structural: every Phase-4 test file exists and is non-empty."""
    missing = []
    empty = []
    for f in PHASE4_TEST_FILES:
        p = TESTS_DIR / f
        if not p.exists():
            missing.append(f)
        elif p.stat().st_size == 0:
            empty.append(f)
    assert not missing, f"Missing Phase-4 test files: {missing}"
    assert not empty, f"Empty Phase-4 test files: {empty}"


def test_all_wave0_deliverables_present():
    """SC-1 structural: every Wave-0 deliverable from 04-VALIDATION.md exists."""
    missing = []
    for f in WAVE0_DELIVERABLES:
        p = TESTS_DIR / f
        if not p.exists():
            missing.append(f)
    assert not missing, f"Missing Wave-0 deliverables: {missing}"


def test_pytest_collect_only_succeeds():
    """SC-1 structural: pytest --collect-only must succeed (no import errors).

    This catches the class of bugs where a test file imports something
    that fails at module load time. Uses an isolated subprocess so the
    outer test session is not affected.

    Uses ``--collect-only`` which does NOT trigger autouse session-scoped
    fixtures (no backend spawn, no infinite loop). Subprocess timeout=60s
    is a backstop against hangs (T-recursive-pytest-spawn-01 mitigation).
    """
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(TESTS_DIR), "--collect-only", "-q"],
        cwd=str(BACKEND_DIR),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode in (0, 5), (
        f"pytest --collect-only failed:\nreturncode={result.returncode}\n"
        f"stdout:\n{result.stdout[-1500:]}\n"
        f"stderr:\n{result.stderr[-1500:]}"
    )
    # returncode 5 = no tests collected (acceptable only if running on a
    # fresh checkout before any test file exists -- should not happen here).
    if result.returncode == 5:
        pytest.fail("pytest collected zero tests -- Wave-0 may not have landed")


def test_no_legacy_collection_reads_in_server_py():
    """DEBT-03: server.py contains zero reads against legacy collection names.

    Phase-5 Plan 05-02 replaced all `db.smart_stock`, `db.sumber_pemakaian`,
    and `db.settings.find_one({"type": "coa"})` reads with the canonical
    names (`db.smartstock`, `db.sumberpemakaian`, `db.app_settings`).

    This gate prevents regression: if anyone re-introduces a legacy read,
    this test fails immediately.

    IMPORTANT: line 2377 `if module in ["general", "smart_stock"]:` is a
    Python string literal (module-routing key), NOT a collection read —
    we use a precise grep that excludes string literals via the `db.<name>`
    access pattern.
    """
    import re
    server_py = BACKEND_DIR / "server.py"
    text = server_py.read_text(encoding="utf-8")
    # Strip Python comment lines so a "# legacy: db.smart_stock" annotation
    # in a docstring does not trip the gate (RESEARCH Anti-Pattern: grep-gate hygiene)
    non_comment_lines = [
        line for line in text.splitlines()
        if not line.lstrip().startswith("#")
    ]
    body = "\n".join(non_comment_lines)
    # The locked-out patterns: db.<legacy>. (followed by find / aggregate / etc.)
    forbidden_re = re.compile(
        r"\bdb\.(smart_stock|sumber_pemakaian)\b"
        r"|\bdb\.settings\.find_one\(\{\"type\": \"coa\"\}\)"
    )
    matches = forbidden_re.findall(body)
    assert not matches, (
        f"DEBT-03 regression: found {len(matches)} legacy collection read(s) "
        f"in server.py: {matches[:5]}. See ADR-009/010/011 and Plan 05-02 "
        f"interfaces table for the canonical replacements."
    )
