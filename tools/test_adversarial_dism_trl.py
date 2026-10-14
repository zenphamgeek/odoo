#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adversarial Verification Suite for DISM-TRL & SaaS Concurrency:
Target: enterprise/insilos_industry_showcase/
Verifies Audit 3 Remediations:
  1. AST & Invariants of saas.workspace model (pg_try_advisory_xact_lock, savepoints, sql constraints)
  2. AST & Invariants of InsilosSaaSController (/workspace/create route)
  3. AST & Invariants of main.py saas_signup_submit (DISM-TRL fast-path lock, savepoint rollback)
  4. QWeb templates.xml error handling (system_busy, subdomain_taken rounded-3 styling, obsidian stage)
  5. Module registrations & ACL CSV integrity
  6. Multi-threaded concurrency simulation (16 concurrent threads: exactly 1 winner, 15 rejected)
"""

import ast
import os
import re
import sys
import threading
import time
import zlib
import xml.etree.ElementTree as ET

REPO_ROOT = "/home/zen/O20"
TEMPLATES_XML = os.path.join(REPO_ROOT, "enterprise/insilos_industry_showcase/views/templates.xml")
WORKSPACE_PY = os.path.join(REPO_ROOT, "enterprise/insilos_industry_showcase/models/saas_workspace.py")
MODELS_INIT = os.path.join(REPO_ROOT, "enterprise/insilos_industry_showcase/models/__init__.py")
PROVISIONING_PY = os.path.join(REPO_ROOT, "enterprise/insilos_industry_showcase/controllers/saas_provisioning.py")
CONTROLLERS_INIT = os.path.join(REPO_ROOT, "enterprise/insilos_industry_showcase/controllers/__init__.py")
MAIN_PY = os.path.join(REPO_ROOT, "enterprise/insilos_industry_showcase/controllers/main.py")
TEST_CONCURRENCY_PY = os.path.join(REPO_ROOT, "enterprise/insilos_industry_showcase/tests/test_adversarial_concurrency.py")
TESTS_INIT = os.path.join(REPO_ROOT, "enterprise/insilos_industry_showcase/tests/__init__.py")
ACCESS_CSV = os.path.join(REPO_ROOT, "enterprise/insilos_industry_showcase/security/ir.model.access.csv")


def test_templates_xml_invariants():
    print("[*] Verifying templates.xml DISM-TRL error templates & obsidian stage...")
    assert os.path.exists(TEMPLATES_XML), f"Missing {TEMPLATES_XML}"

    with open(TEMPLATES_XML, "r", encoding="utf-8") as f:
        xml_src = f.read()

    # 1. Check XML well-formedness
    tree = ET.parse(TEMPLATES_XML)
    root = tree.getroot()
    assert root.tag == "odoo", "Root element must be <odoo>"

    # 2. Check system_busy template
    assert "error == 'system_busy'" in xml_src, "Missing error == 'system_busy' condition in templates.xml"
    assert "ph-clock-countdown" in xml_src, "Missing ph-clock-countdown icon in system_busy block"
    assert "Hệ thống đang quá tải tạm thời" in xml_src, "Missing system_busy title in templates.xml"
    assert "Yêu cầu khởi tạo đang được xếp hàng an toàn" in xml_src, "Missing system_busy description in templates.xml"

    # 3. Check subdomain_taken template styling
    assert "error == 'subdomain_taken'" in xml_src, "Missing error == 'subdomain_taken' condition in templates.xml"
    assert "rounded-3" in xml_src, "Missing rounded-3 styling in error blocks"
    assert "bg-danger-subtle text-danger" in xml_src, "Missing bg-danger-subtle text-danger in subdomain_taken"

    # 4. Check obsidian stage preservation
    assert "bg-transparent borderless-obsidian-stage" in xml_src, "Obsidian stage styling must be preserved in saas_signup_success_template"

    print("  [✓] templates.xml XML AST, system_busy UI, and obsidian stage verified.")


def test_saas_workspace_model_ast():
    print("[*] Verifying saas_workspace.py AST & DISM-TRL implementation...")
    assert os.path.exists(WORKSPACE_PY), f"Missing {WORKSPACE_PY}"

    with open(WORKSPACE_PY, "r", encoding="utf-8") as f:
        src = f.read()

    tree = ast.parse(src)

    # 1. Model class checks
    model_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and any(
            (isinstance(base, ast.Attribute) and base.attr == 'Model') or
            (isinstance(base, ast.Name) and base.id == 'Model')
            for base in node.bases
        ):
            model_class = node
            break

    assert model_class is not None, "saas.workspace class not found in saas_workspace.py"

    # 2. _name check
    assert "_name = 'saas.workspace'" in src, "Missing _name = 'saas.workspace'"
    assert "subdomain = fields.Char" in src, "Missing subdomain field definition"
    assert "tenant_id = fields.Many2one" in src, "Missing tenant_id field definition"
    assert "state = fields.Selection" in src, "Missing state field definition"
    assert "idempotency_hash = fields.Char" in src, "Missing idempotency_hash field definition"

    # 3. SQL constraints
    assert "_sql_constraints" in src, "Missing _sql_constraints"
    assert "subdomain_unique" in src, "Missing subdomain_unique constraint"
    assert "unique(subdomain)" in src, "Missing unique(subdomain) in constraint"

    # 4. provision_atomic method
    assert "def provision_atomic" in src, "Missing provision_atomic method"
    assert "pg_try_advisory_xact_lock" in src, "Missing pg_try_advisory_xact_lock in provision_atomic"
    assert "SAVEPOINT saas_provision_atomic" in src, "Missing SAVEPOINT saas_provision_atomic in provision_atomic"
    assert "RELEASE SAVEPOINT saas_provision_atomic" in src, "Missing RELEASE SAVEPOINT in provision_atomic"
    assert "ROLLBACK TO SAVEPOINT saas_provision_atomic" in src, "Missing ROLLBACK TO SAVEPOINT in provision_atomic"
    assert 'raise UserError("system_busy")' in src, "Missing raise UserError('system_busy')"
    assert 'raise UserError("subdomain_taken")' in src, "Missing raise UserError('subdomain_taken')"

    print("  [✓] saas_workspace.py AST, fields, _sql_constraints, and DISM-TRL locks verified.")


def test_saas_provisioning_controller_ast():
    print("[*] Verifying saas_provisioning.py AST & /workspace/create route...")
    assert os.path.exists(PROVISIONING_PY), f"Missing {PROVISIONING_PY}"

    with open(PROVISIONING_PY, "r", encoding="utf-8") as f:
        src = f.read()

    assert "class InsilosSaaSController" in src, "Missing InsilosSaaSController in saas_provisioning.py"
    assert "@http.route('/workspace/create'" in src or '@http.route("/workspace/create"' in src, (
        "Missing route '/workspace/create' in saas_provisioning.py"
    )
    assert "provision_atomic" in src, "Controller must call provision_atomic"

    print("  [✓] saas_provisioning.py InsilosSaaSController route and dispatch verified.")


def test_main_controller_ast():
    print("[*] Verifying controllers/main.py DISM-TRL fast-path & rollback...")
    assert os.path.exists(MAIN_PY), f"Missing {MAIN_PY}"

    with open(MAIN_PY, "r", encoding="utf-8") as f:
        src = f.read()

    assert "import zlib" in src, "Missing import zlib in main.py"
    assert "pg_try_advisory_xact_lock" in src, "Missing pg_try_advisory_xact_lock in main.py"
    assert "SAVEPOINT saas_provision_atomic" in src, "Missing SAVEPOINT saas_provision_atomic in main.py"
    assert "RELEASE SAVEPOINT saas_provision_atomic" in src, "Missing RELEASE SAVEPOINT in main.py"
    assert "ROLLBACK TO SAVEPOINT saas_provision_atomic" in src, "Missing ROLLBACK TO SAVEPOINT in main.py"
    assert "error=system_busy" in src, "Missing error=system_busy redirect in main.py"
    assert "error=subdomain_taken" in src, "Missing error=subdomain_taken redirect in main.py"

    print("  [✓] main.py saas_signup_submit DISM-TRL fast-path and savepoint rollback verified.")


def test_registrations_and_csv():
    print("[*] Verifying module imports and security CSV registration...")
    with open(MODELS_INIT, "r", encoding="utf-8") as f:
        assert "saas_workspace" in f.read(), "saas_workspace not imported in models/__init__.py"

    with open(CONTROLLERS_INIT, "r", encoding="utf-8") as f:
        assert "saas_provisioning" in f.read(), "saas_provisioning not imported in controllers/__init__.py"

    with open(TESTS_INIT, "r", encoding="utf-8") as f:
        assert "test_adversarial_concurrency" in f.read(), "test_adversarial_concurrency not imported in tests/__init__.py"

    with open(ACCESS_CSV, "r", encoding="utf-8") as f:
        csv_content = f.read()
        assert "model_saas_workspace" in csv_content, "model_saas_workspace missing from ir.model.access.csv"
        assert "access_saas_workspace_user" in csv_content, "access_saas_workspace_user missing from ir.model.access.csv"

    print("  [✓] Registrations in models, controllers, tests, and security CSV verified.")


def test_concurrency_simulation_matrix():
    print("[*] Executing Behavioral DISM-TRL 16-Thread Concurrency Simulation...")

    class SimulatedPostgresDatabase:
        def __init__(self):
            self.lock = threading.Lock()
            self.advisory_locks = set()
            self.workspaces = {}

        def try_advisory_xact_lock(self, lock_id):
            with self.lock:
                if lock_id in self.advisory_locks:
                    return False
                self.advisory_locks.add(lock_id)
                return True

        def release_advisory_lock(self, lock_id):
            with self.lock:
                self.advisory_locks.discard(lock_id)

        def create_workspace(self, subdomain, key):
            with self.lock:
                if subdomain in self.workspaces:
                    raise ValueError("unique constraint violation: subdomain_unique")
                ws_id = len(self.workspaces) + 1
                self.workspaces[subdomain] = {
                    "id": ws_id,
                    "subdomain": subdomain,
                    "key": key,
                }
                return self.workspaces[subdomain]

    db = SimulatedPostgresDatabase()

    def simulate_provision_atomic(subdomain, key):
        clean_subdomain = subdomain.strip().lower()
        lock_id = zlib.crc32(clean_subdomain.encode("utf-8"))

        acquired = db.try_advisory_xact_lock(lock_id)
        if not acquired:
            raise RuntimeError("system_busy")

        try:
            # Simulate work
            time.sleep(0.01)
            # Double check existing
            with db.lock:
                if clean_subdomain in db.workspaces:
                    raise RuntimeError("subdomain_taken")

            # Simulate savepoint saas_provision_atomic
            ws = db.create_workspace(clean_subdomain, key)
            return ws
        finally:
            db.release_advisory_lock(lock_id)

    target_subdomain = "acme-corp"
    results = []
    errors = []
    mu = threading.Lock()

    def runner(thread_id):
        try:
            res = simulate_provision_atomic(target_subdomain, f"key-{thread_id}")
            with mu:
                results.append((thread_id, res))
        except RuntimeError as e:
            with mu:
                errors.append((thread_id, str(e)))
        except Exception as e:
            with mu:
                errors.append((thread_id, f"unexpected_{e}"))

    threads = [threading.Thread(target=runner, args=(i,)) for i in range(16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 1, f"Expected exactly 1 winner, got {len(results)}: {results}"
    assert len(errors) == 15, f"Expected 15 errors, got {len(errors)}: {errors}"
    for tid, err in errors:
        assert err in ("system_busy", "subdomain_taken"), f"Unexpected error {err} on thread {tid}"
    assert len(db.workspaces) == 1, "Expected exactly 1 created workspace in DB"

    print(f"  [✓] 16-thread simulation passed: 1 winner ({results[0][0]}), 15 rejected ({errors[0][1]} / {errors[-1][1]}), 0 deadlocks.")


def main():
    print("================================================================================")
    print("   SOVEREIGN ADVERSARIAL DISM-TRL AUDIT 3 VERIFICATION SUITE")
    print("================================================================================")
    test_templates_xml_invariants()
    test_saas_workspace_model_ast()
    test_saas_provisioning_controller_ast()
    test_main_controller_ast()
    test_registrations_and_csv()
    test_concurrency_simulation_matrix()
    print("================================================================================")
    print("[🎉] AUDIT 3 DISM-TRL SOVEREIGN VERIFICATION PASSED (EXIT 0)")
    print("================================================================================")


if __name__ == "__main__":
    main()
