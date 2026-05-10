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
