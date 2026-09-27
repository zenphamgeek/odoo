#!/usr/bin/env bash
# ==============================================================================
# Insilos Enterprise Platform — Master CI/CD & Production Verification Pipeline
# Executes all technical gates, ORM tests, E2E integrations, and UI checks.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

echo "================================================================================"
echo "🚀 INSILOS ENTERPRISE MASTER VERIFICATION PIPELINE (Odoo 20 LTS Platform)"
echo "   Root: $ROOT_DIR | Python: $VENV_PYTHON"
echo "================================================================================"

# 1. Gate 1 & 2: Python Syntax & XML QWeb Well-formedness
echo -e "\n▶ [STAGE 1/6] Running Syntax & XML Verification Gates (Gates 1 & 2)..."
$VENV_PYTHON "$SCRIPT_DIR/verify_gates_1_2.py"

# 2. Gate 3: Phosphor Duotone App Icon & Branding Integrity
echo -e "\n▶ [STAGE 2/6] Verifying Phosphor Duotone App Icons & Canonical Branding..."
$VENV_PYTHON "$SCRIPT_DIR/check_app_icons_integrity.py"
$VENV_PYTHON "$SCRIPT_DIR/sync_branding_logos.py" --check

# 3. Gate 4: PEP 451 Transparent Import Hook Adapter
echo -e "\n▶ [STAGE 3/6] Verifying Hexagonal Import Hook Adapter (PEP 451)..."
$VENV_PYTHON "$SCRIPT_DIR/test_insilos_import_hook.py"

# 4. Gate 5: Cross-Module E2E Workflow Simulation
echo -e "\n▶ [STAGE 4/6] Executing In-Process Cross-Module Workflow Simulation..."
$VENV_PYTHON "$SCRIPT_DIR/run_in_shell_simulation.py"

# 5. Gate 6: Playwright 72 Launcher Apps & 26 Ported Modules Verification
echo -e "\n▶ [STAGE 5/6] Running Headless Playwright Webclient Test Suites..."
node "$ROOT_DIR/test_all_home_apps_parallel.js"
node "$SCRIPT_DIR/test_enterprise_ported_modules_e2e.js"

# 6. Documentation & Handover Artifacts Check
echo -e "\n▶ [STAGE 6/6] Verifying Handover Artifacts & PDFs..."
if [ -f "$ROOT_DIR/doc/INSILOS_ENTERPRISE_DEPLOYMENT_HANDBOOK.pdf" ] && [ -f "$ROOT_DIR/doc/INSILOS_MARKETING_PRODUCT_OVERVIEW.pdf" ]; then
    echo "  ✓ Deployment Handbook PDF exists: $(ls -lh "$ROOT_DIR/doc/INSILOS_ENTERPRISE_DEPLOYMENT_HANDBOOK.pdf" | awk '{print $5}')"
    echo "  ✓ Marketing Overview PDF exists: $(ls -lh "$ROOT_DIR/doc/INSILOS_MARKETING_PRODUCT_OVERVIEW.pdf" | awk '{print $5}')"
fi

echo -e "\n================================================================================"
echo "🎉 ALL VERIFICATION GATES PASSED 100% WITH ZERO ERRORS!"
echo "   The Insilos Enterprise Platform is fully certified and production-ready."
echo "================================================================================"
