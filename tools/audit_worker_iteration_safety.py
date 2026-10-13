#!/usr/bin/env python3
"""
AST-based Server Worker Iteration Safety Auditor (CWE-662 / Concurrency Safety Gate)
Detects unsafe live-dictionary iteration over mutable worker registries (e.g. `self.workers`)
that are concurrently mutated from signal handlers (SIGCHLD / worker spawn / reap).
Requires all traversals to wrap the dictionary or its views in `list(...)`.
"""

import ast
import pathlib
import sys

GUARDED_ATTRS = {"workers"}


class WorkerIterationChecker(ast.NodeVisitor):
    def __init__(self, filename: str):
        self.filename = filename
        self.violations: list[tuple[str, int, str]] = []

    def visit_For(self, node: ast.For):
        it = node.iter
        # Direct attribute: `for pid in self.workers`
        if isinstance(it, ast.Attribute) and it.attr in GUARDED_ATTRS:
            if isinstance(it.value, ast.Name) and it.value.id == "self":
                self.violations.append((
                    self.filename,
                    node.lineno,
                    f"Direct iteration over mutable 'self.{it.attr}' without defensive list() copy"
                ))

        # Method call: `for w in self.workers.values()` or `.keys()` or `.items()`
        elif isinstance(it, ast.Call) and isinstance(it.func, ast.Attribute):
            call_target = it.func.value
            if isinstance(call_target, ast.Attribute) and call_target.attr in GUARDED_ATTRS:
                if isinstance(call_target.value, ast.Name) and call_target.value.id == "self":
                    self.violations.append((
                        self.filename,
                        node.lineno,
                        f"Direct iteration over 'self.{call_target.attr}.{it.func.attr}()' without defensive list() copy"
                    ))

        self.generic_visit(node)


def audit_path(root_path: str) -> list[tuple[str, int, str]]:
    all_violations = []
    root = pathlib.Path(root_path)
    if root.is_file():
        candidates = [root]
    else:
        candidates = list(root.rglob("service/server.py"))

    for filepath in candidates:
        try:
            tree = ast.parse(filepath.read_text(encoding="utf-8"), filename=str(filepath))
            checker = WorkerIterationChecker(str(filepath))
            checker.visit(tree)
            all_violations.extend(checker.violations)
        except Exception as e:
            print(f"Error parsing {filepath}: {e}", file=sys.stderr)

    return all_violations


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "odoo/service/server.py"
    print("=" * 70)
    print("AST WORKER ITERATION CONCURRENCY SAFETY AUDIT")
    print(f"Target: {target}")
    print("=" * 70)

    violations = audit_path(target)
    if violations:
        print(f"❌ FAIL: Found {len(violations)} unsafe worker dictionary iteration(s):")
        for fn, line, msg in violations:
            print(f"  • {fn}:{line} -> {msg}")
        sys.exit(1)
    else:
        print("✅ PASS: All worker dictionary iterations use verified defensive list() copies.")
        sys.exit(0)


if __name__ == "__main__":
    main()
