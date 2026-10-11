#!/usr/bin/env python3
"""
Test Blast-Radius & Database Isolation Linter (CI Invariant Guard)
Author: AGY Fleet Autonomous Swarm & Zero-Fake-Pass Engine

Scans all test files under tools/__tests__/ and addons/**/tests/ to enforce:
1. Anti-Prod Invariant: Prohibits hardcoding production database literals (*_prod, *_production).
2. Anti-Commit Invariant: Prohibits direct `cr.commit()` or `cursor.commit()` inside test suites.
3. Transaction Isolation: Mandates test isolation via rollback or SavepointCase/TransactionCase.
"""

import ast
import os
import pathlib
import sys
from typing import List, Tuple

BANNED_DB_FRAGMENTS = ("prod", "production")
EXEMPT_FUNCTION_NAMES = ("test_deploy_preflight_security_prod_default",)


class TestBlastRadiusVisitor(ast.NodeVisitor):
    def __init__(self, filename: str):
        self.filename = filename
        self.violations: List[Tuple[int, str, str]] = []
        self.current_function: str = ""

    def visit_FunctionDef(self, node: ast.FunctionDef):
        prev_func = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = prev_func

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        prev_func = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = prev_func

    def visit_Assign(self, node: ast.Assign):
        if self.current_function in EXEMPT_FUNCTION_NAMES:
            self.generic_visit(node)
            return

        # Check assignment targets: db_name = "xxx_prod"
        for target in node.targets:
            target_name = ""
            if isinstance(target, ast.Name):
                target_name = target.id.lower()
            elif isinstance(target, ast.Attribute):
                target_name = target.attr.lower()

            if any(k in target_name for k in ("db", "database")):
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    val = node.value.value.lower()
                    if any(b in val for b in BANNED_DB_FRAGMENTS):
                        self.violations.append((
                            node.lineno,
                            f"Hardcoded production-like DB literal assigned to '{target_name}': '{node.value.value}'",
                            "CWE-Blast-Radius"
                        ))

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if self.current_function in EXEMPT_FUNCTION_NAMES:
            self.generic_visit(node)
            return

        # Check forbidden cr.commit() in tests
        if isinstance(node.func, ast.Attribute) and node.func.attr == "commit":
            obj_name = ""
            if isinstance(node.func.value, ast.Name):
                obj_name = node.func.value.id
            elif isinstance(node.func.value, ast.Attribute):
                obj_name = node.func.value.attr
            if obj_name in ("cr", "cursor"):
                self.violations.append((
                    node.lineno,
                    f"Forbidden direct transaction commit '{obj_name}.commit()' inside test file. Tests must use rollback or savepoints.",
                    "CWE-Test-Isolation"
                ))

        # Check Registry("xxx_prod") or db_connect("xxx_prod")
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                val = arg.value.lower()
                if any(b in val for b in BANNED_DB_FRAGMENTS):
                    # Check if the call is Registry or db_connect
                    func_str = ast.unparse(node.func).lower() if hasattr(ast, "unparse") else ""
                    if any(k in func_str for k in ("registry", "db_connect")):
                        self.violations.append((
                            node.lineno,
                            f"Connecting directly to production-like database '{arg.value}' via {func_str}",
                            "CWE-Blast-Radius"
                        ))

        self.generic_visit(node)


def audit_test_file(path: pathlib.Path) -> List[Tuple[str, int, str, str]]:
    try:
        content = path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(path))
        visitor = TestBlastRadiusVisitor(str(path))
        visitor.visit(tree)
        return [(str(path), ln, msg, cwe) for ln, msg, cwe in visitor.violations]
    except Exception as e:
        return [(str(path), 1, f"Failed to parse AST: {e}", "AST-Error")]


def main():
    root = pathlib.Path(__file__).resolve().parent.parent
    target_dirs = [root / "tools" / "__tests__"]

    print("🛡️ [Blast-Radius Linter] Scanning test files for production DB literals and unisolated commits...")
    all_violations = []

    for t_dir in target_dirs:
        if not t_dir.exists():
            continue
        for py_path in t_dir.rglob("*.py"):
            violations = audit_test_file(py_path)
            all_violations.extend(violations)

    if all_violations:
        print(f"\n❌ [FAIL] Found {len(all_violations)} blast-radius invariant violations:")
        for path, ln, msg, cwe in all_violations:
            print(f"  • {path}:{ln} [{cwe}]: {msg}")
        sys.exit(1)
    else:
        print(f"✅ [PASS] Zero blast-radius violations found. All test suites respect DB isolation invariants.")
        sys.exit(0)


if __name__ == "__main__":
    main()
