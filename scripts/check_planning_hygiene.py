#!/usr/bin/env python3
"""Check GSD planning metadata and archive hygiene."""

from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PLANNING = ROOT / ".planning"

EXPECTED_PHASE_ARCHIVES = {
    "v1.3": [f"{phase:02d}" for phase in range(1, 29)],
    "v1.4": [str(phase) for phase in range(29, 34)],
}
ACTIVE_PHASE_RANGE = range(29, 34)
REQUIRED_TEMPLATES = [
    PLANNING / "templates" / "PHASE-SUMMARY-TEMPLATE.md",
    PLANNING / "templates" / "PHASE-VALIDATION-TEMPLATE.md",
    PLANNING / "templates" / "PHASE-VERIFICATION-TEMPLATE.md",
]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def frontmatter(text: str) -> str | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    return text[4:end]


def check_validation_metadata(errors: list[str]) -> None:
    for path in sorted(PLANNING.rglob("*VALIDATION.md")):
        text = read(path)
        fm = frontmatter(text)
        if fm is None:
            errors.append(f"{rel(path)} missing YAML frontmatter")
            continue
        if "nyquist_status:" not in fm and "nyquist_compliant:" not in fm:
            errors.append(f"{rel(path)} missing nyquist_status or nyquist_compliant")


def check_archive_index(errors: list[str]) -> None:
    milestones = PLANNING / "MILESTONES.md"
    milestones_text = read(milestones) if milestones.exists() else ""

    for version, phases in EXPECTED_PHASE_ARCHIVES.items():
        index = PLANNING / "milestones" / f"{version}-phases" / "INDEX.md"
        if not index.exists():
            errors.append(f"{rel(index)} missing")
            continue

        text = read(index)
        for phase in phases:
            if f"| {phase} |" not in text:
                errors.append(f"{rel(index)} missing phase {phase}")

        if milestones_text and f"{version}-phases/INDEX.md" not in milestones_text:
            errors.append(f"{rel(milestones)} does not link {version} phase archive index")


def check_active_phase_workspace(errors: list[str]) -> None:
    active_root = PLANNING / "phases"
    for path in active_root.iterdir():
        if path.name == ".gitkeep":
            continue
        if not path.is_dir():
            errors.append(f"{rel(path)} is an unexpected file in active phase workspace")
            continue
        match = re.match(r"^(\d+)-", path.name)
        if not match:
            errors.append(f"{rel(path)} does not start with a phase number")
            continue
        phase = int(match.group(1))
        if phase not in ACTIVE_PHASE_RANGE:
            errors.append(f"{rel(path)} is not an active v1.4 phase directory")


def check_templates(errors: list[str]) -> None:
    for path in REQUIRED_TEMPLATES:
        if not path.exists():
            errors.append(f"{rel(path)} missing")
            continue
        text = read(path)
        for required in ("requirements:", "Residual Risks"):
            if required not in text:
                errors.append(f"{rel(path)} missing {required!r}")


def check_current_state(errors: list[str]) -> None:
    state = read(PLANNING / "STATE.md")
    roadmap = read(PLANNING / "ROADMAP.md")
    requirements_path = PLANNING / "REQUIREMENTS.md"
    requirements = read(requirements_path) if requirements_path.exists() else ""

    stale_patterns = [
        "$gsd-execute-phase 29",
        "$gsd-execute-phase 30",
        "Phase 29 ready",
        "Phase 30 Plan 30-01 is ready for execution",
        "Plan 30-01 ready for execution",
    ]
    for pattern in stale_patterns:
        if pattern in state or pattern in roadmap:
            errors.append(f"current planning state still contains stale text: {pattern}")

    awaiting_next = "awaiting_next_milestone" in state or "$gsd-new-milestone" in state + roadmap

    if requirements and "| META4-01..04 | Phase 30 | Complete |" not in requirements:
        errors.append("REQUIREMENTS.md does not mark META4-01..04 complete")

    if not requirements and "v1.4-REQUIREMENTS.md" not in roadmap:
        errors.append("current roadmap does not link archived v1.4 requirements")

    if awaiting_next:
        if "$gsd-new-milestone" not in state + roadmap:
            errors.append("awaiting-next-milestone state does not route to $gsd-new-milestone")
        return

    valid_routes = tuple(
        f"$gsd-{action}-phase {phase}"
        for phase in range(31, 34)
        for action in ("plan", "execute")
    )
    if not any(route in state for route in valid_routes):
        errors.append("STATE.md does not route next work to a current v1.4 phase")
    if not any(route in roadmap for route in valid_routes):
        errors.append("ROADMAP.md does not route next work to a current v1.4 phase")


def main() -> int:
    errors: list[str] = []
    check_validation_metadata(errors)
    check_archive_index(errors)
    check_active_phase_workspace(errors)
    check_templates(errors)
    check_current_state(errors)

    if errors:
        print("Planning hygiene check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("Planning hygiene check passed.")
    print("Validated: validation metadata, phase archive indexes, active phase workspace, templates, and current next-step state.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
