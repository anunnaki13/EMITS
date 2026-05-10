#!/usr/bin/env bash
# CREDENTIAL HYGIENE SCANNER
# ---------------------------
# Scans tracked files in this (inner) git repo for credential-shaped patterns.
# Source-of-truth for the patterns AND the EXCLUDE list. The pre-commit hook
# (.git/hooks/pre-commit) shells out to this script.
#
# Patterns:
#   A — JWT-shaped string                       eyJ.<base64ish>.<base64ish>
#   B — Bearer + JWT literal                    [Bb]earer eyJ...
#   C — MongoDB URI with embedded credentials   mongodb(+srv)?://user:pass@host
#   D — Live admin password literal             adminpassword (case-sensitive)
#
# Allowlist policy:
#   The scanner itself, the hygiene contract doc, and the LOGIN_BUG audit doc
#   are exempt because they discuss the patterns verbatim. The EXCLUDE array
#   below ALSO contains pre-existing leaks (catalogued at Phase-2 plan-time)
#   that pre-date this hygiene gate. Each pre-existing entry carries an
#   explicit TODO naming the phase that will remove it. New code MUST NOT
#   add to the EXCLUDE list without writing a corresponding TODO.

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# Files exempt from scanning. ORDER:
#   1. Self-references (scanner, hygiene doc, audit trail) — always exempt.
#   2. Pre-existing technical-debt leaks — each carries a TODO phase tag.
EXCLUDE=(
    # --- self-references ---
    "scripts/check_credentials.sh"
    "docs/audit/CREDENTIAL_HYGIENE.md"
    "docs/audit/LOGIN_BUG.md"

    # --- pre-existing inline test credentials (TODO Phase 4 TEST-02: replace with env-var read) ---
    "backend/tests/test_dashboard_advanced.py"
    "backend/tests/test_coa_reconciliation.py"
    "backend/tests/test_merit_order.py"
    "backend/tests/test_po_batubara.py"

    # --- pre-existing test reports with inline credentials (TODO Phase 4 TEST-02: regenerate from sanitized fixtures) ---
    "test_reports/iteration_3.json"
    "test_reports/iteration_4.json"
    "test_reports/iteration_5.json"
    "test_reports/iteration_6.json"

    # --- pre-existing documentation with inline credentials / placeholder mongo URIs (TODO Phase 3 STAB-03: refresh docs to reference env vars) ---
    "API_REFERENCE.md"
    "DEPLOYMENT_GUIDE.md"
    "frontend/public/docs/API_REFERENCE.md"
    "frontend/public/docs/DEPLOYMENT_GUIDE.md"

    # --- canonical PRD copy (TODO Phase 3 STAB-03: redact inline test credentials block) ---
    "memory/PRD.md"
)

# Build target list: tracked files minus EXCLUDE.
# `git ls-files` is the canonical "tracked" enumeration.
exclude_file="$(mktemp)"
trap 'rm -f "$exclude_file"' EXIT
printf '%s\n' "${EXCLUDE[@]}" > "$exclude_file"

mapfile -t targets < <(git ls-files | grep -vxFf "$exclude_file" || true)

if [ "${#targets[@]}" -eq 0 ]; then
    echo "OK: no tracked files to scan after exclusions."
    exit 0
fi

fail=0

scan() {
    local label="$1"
    local pattern="$2"
    local hits
    # -E extended regex; -l list filenames with matches; -I skip binary.
    hits="$(grep -lEI "$pattern" -- "${targets[@]}" 2>/dev/null || true)"
    if [ -n "$hits" ]; then
        echo "FAIL [$label]: matches found in:"
        printf '  %s\n' $hits
        fail=1
    fi
}

scan "JWT"                    'eyJ[A-Za-z0-9._-]{20,}\.[A-Za-z0-9._-]{20,}\.[A-Za-z0-9._-]{20,}'
scan "Bearer-JWT"             '[Bb]earer[[:space:]]+eyJ[A-Za-z0-9._-]{20,}'
scan "MongoDB-URI-with-creds" 'mongodb(\+srv)?://[^[:space:]/]+:[^[:space:]/]+@'
scan "Admin-password-literal" 'adminpassword'

if [ "$fail" -eq 1 ]; then
    echo ""
    echo "Remediation: remove the literal, source from env vars (TEST_ADMIN_PASSWORD etc.), and re-stage."
    echo "Run scripts/check_credentials.sh to re-verify."
    echo "If the file is a documented pre-existing leak, see docs/audit/CREDENTIAL_HYGIENE.md"
    echo "section 'How to add a new exemption' before adding it to EXCLUDE."
    exit 1
fi

echo "OK: no tracked credential patterns found in $(git ls-files | wc -l) files (after $(printf '%s\n' "${EXCLUDE[@]}" | wc -l) exemptions)."
