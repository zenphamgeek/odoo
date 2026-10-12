#!/usr/bin/env python3
"""
AST-Level Secret & Scanner-Evasion Linter (Entropy Contract)
============================================================
Enforces that code does NOT construct protected identifiers or secrets
via string concatenation (e.g. 'od' + 'oo', 'pass' + 'word', '1NN0' + 'R1@2026')
to evade static string/regex security scanners.
"""

import ast
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Tuple, Optional

PROTECTED_TOKENS = {
    "odoo",
    "postgres",
    "root",
    "admin",
    "insilos",
    "password",
    "secret",
    "bearer",
    "apikey",
    "api_key",
    "1NN0R1@2026",
}


def _get_constant_str(node: ast.AST) -> Optional[str]:
    """Recursively resolves static string concatenation in AST."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left_str = _get_constant_str(node.left)
        right_str = _get_constant_str(node.right)
        if left_str is not None and right_str is not None:
            return left_str + right_str
    return None


class SecretEvasionVisitor(ast.NodeVisitor):
    def __init__(self, filename: str, lines: Optional[List[str]] = None):
        self.filename = filename
        self.lines = lines or []
        self.violations: List[Tuple[int, str, str]] = []

    def visit_BinOp(self, node: ast.BinOp):
        if isinstance(node.op, ast.Add):
            # Check if line has ignore comment
            if 0 < node.lineno <= len(self.lines):
                line_text = self.lines[node.lineno - 1]
                if "ast-evasion-ignore" in line_text or "evasion:ignore" in line_text:
                    self.generic_visit(node)
                    return
            combined = _get_constant_str(node)
            if combined:
                combined_lower = combined.lower()
                for token in PROTECTED_TOKENS:
                    if token.lower() in combined_lower:
                        self.violations.append((node.lineno, combined, token))
                        break
        self.generic_visit(node)


def scan_code(content: str, filename: str = "<string>") -> List[Tuple[str, int, str, str]]:
    """Scans in-memory Python code string for AST string concatenation evasion patterns."""
    violations = []
    try:
        tree = ast.parse(content, filename=filename)
        lines = content.splitlines()
        visitor = SecretEvasionVisitor(filename, lines=lines)
        visitor.visit(tree)
        for lineno, combined, token in visitor.violations:
            violations.append((filename, lineno, combined, token))
    except (SyntaxError, UnicodeDecodeError):
        pass  # Skip non-parsable files
    return violations


def scan_file(filepath: str) -> List[Tuple[str, int, str, str]]:
    """Scans a single python file for AST string concatenation evasion patterns."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return scan_code(content, filename=filepath)
    except (OSError, UnicodeDecodeError):
        return []


def scan_paths(paths: List[str]) -> List[Tuple[str, int, str, str]]:
    """Scans a list of files or directories in parallel."""
    files_to_scan = []
    for p in paths:
        if os.path.isfile(p) and p.endswith(".py"):
            files_to_scan.append(p)
        elif os.path.isdir(p):
            for root, _, files in os.walk(p):
                # Skip .venv, .git, node_modules, __pycache__
                if any(ignored in root for ignored in [".venv", ".git", "node_modules", "__pycache__"]):
                    continue
                for f in files:
                    if f.endswith(".py"):
                        files_to_scan.append(os.path.join(root, f))

    all_violations = []
    if not files_to_scan:
        return all_violations

    max_workers = min(os.cpu_count() or 4, len(files_to_scan), 16)
    if max_workers <= 1:
        for fpath in files_to_scan:
            all_violations.extend(scan_file(fpath))
    else:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(scan_file, f): f for f in files_to_scan}
            for future in as_completed(future_to_file):
                all_violations.extend(future.result())

    # Sort deterministically by filepath and line number
    all_violations.sort(key=lambda x: (x[0], x[1]))
    return all_violations


def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else ["tools", "enterprise"]
    print(f"[*] Running AST Secret Evasion Audit across: {targets}...")
    violations = scan_paths(targets)
    if violations:
        print(f"\n[✗] FAILED: {len(violations)} Scanner-Evasion pattern(s) detected:")
        for fpath, lineno, combined, token in violations:
            print(f"    - {fpath}:{lineno} -> '{combined}' reconstructs protected token '{token}'")
        sys.exit(1)
    print(f"[✓] Zero AST string-concatenation scanner evasions detected across all scanned files.")


if __name__ == "__main__":
    main()
