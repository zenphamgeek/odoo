#!/usr/bin/env python3
"""
AST-Level Secret & Scanner-Evasion Linter (Entropy Contract)
============================================================
Enforces that code does NOT construct protected framework identifiers
or secrets via string assembly evasion patterns (e.g. 'od' + 'oo',
''.join(['pass', 'word']), f'sec{""}ret', or '%s%s' % ('od', 'oo'))
to evade static string/regex security scanners (CWE-693 / CWE-259).

Notice: This is best-effort static analysis against typical obfuscation/evasion
primitives in Python AST; motivated adversaries can use dynamic evaluation
(e.g., eval, base64) which should be caught by separate dynamic taint analysis.
"""

import ast
import hashlib
import io
import os
import sys
import tokenize
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Tuple, Optional, Dict

PROTECTED_TOKENS = {
    "odoo",
    "postgres",
    "admin",
    "insilos",
    "password",
    "secret",
    "bearer",
    "apikey",
    "api_key",
}

# SHA-256 fingerprints of known-sensitive secret values. Plaintext secrets
# must never live in source; compare resolved strings against these digests (CWE-259).
# Populate via: python3 -c "import hashlib; print(hashlib.sha256(b'<secret>').hexdigest())"
PROTECTED_SECRET_DIGESTS = {
    # Legacy leaked password fingerprint (pre-rotation)
    "1e923bfedc220f6747aa0824df6bc496f16820a24816004c93e2abb43ed0a08c",
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


def extract_comments_by_line(content: str) -> Dict[int, str]:
    """Extracts actual Python comment tokens mapped by line number (ignores '#' in string literals)."""
    comments: Dict[int, str] = {}
    try:
        tokens = tokenize.tokenize(io.BytesIO(content.encode("utf-8")).readline)
        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                comments[tok.start[0]] = tok.string
    except Exception:
        pass
    return comments


class SecretEvasionVisitor(ast.NodeVisitor):
    def __init__(self, filename: str, content: str = "", comments: Optional[Dict[int, str]] = None):
        self.filename = filename
        self.content = content
        self._comments = comments
        self.violations: List[Tuple[int, str, str]] = []
        self.suppressions: List[Tuple[int, str]] = []

    @property
    def comments(self) -> Dict[int, str]:
        if self._comments is None:
            if "#" in self.content:
                self._comments = extract_comments_by_line(self.content)
            else:
                self._comments = {}
        return self._comments

    def _is_suppressed(self, lineno: int) -> bool:
        """Checks for audit-scoped suppression directive strictly in a genuine Python comment."""
        comment = self.comments.get(lineno, "")
        if "ast-evasion-ignore" in comment or "evasion:ignore" in comment:
            self.suppressions.append((lineno, comment.strip()))
            return True
        return False

    def _check_combined(self, combined: str, lineno: int):
        if not combined:
            return
        # 1. Check against sensitive secret SHA-256 digests (masked output, zero plaintext in source)
        digest = hashlib.sha256(combined.encode("utf-8")).hexdigest()
        if digest in PROTECTED_SECRET_DIGESTS:
            masked = (combined[:3] + "..." + combined[-2:]) if len(combined) > 5 else "***"
            self.violations.append((lineno, masked, "secret-digest-match"))
            return

        # 2. Check against protected framework identifiers / tokens
        combined_lower = combined.lower()
        for token in PROTECTED_TOKENS:
            if token.lower() in combined_lower:
                self.violations.append((lineno, combined, token))
                break

    def visit_BinOp(self, node: ast.BinOp):
        if self._is_suppressed(node.lineno):
            self.generic_visit(node)
            return

        if isinstance(node.op, ast.Add):
            # Check string addition ('a' + 'b')
            combined = _get_constant_str(node)
            if combined:
                self._check_combined(combined, node.lineno)
        elif isinstance(node.op, ast.Mod):
            # Check string formatting ('od%soo' % '')
            left_str = _get_constant_str(node.left)
            if left_str is not None:
                if isinstance(node.right, ast.Constant) and isinstance(node.right.value, str):
                    try:
                        formatted = left_str % node.right.value
                        self._check_combined(formatted, node.lineno)
                    except Exception:
                        pass
                elif isinstance(node.right, ast.Tuple):
                    vals = []
                    for elt in node.right.elts:
                        if isinstance(elt, ast.Constant):
                            vals.append(elt.value)
                        else:
                            break
                    if len(vals) == len(node.right.elts):
                        try:
                            formatted = left_str % tuple(vals)
                            self._check_combined(formatted, node.lineno)
                        except Exception:
                            pass

        self.generic_visit(node)

    def visit_JoinedStr(self, node: ast.JoinedStr):
        # Check contiguous runs of constant segments in f-strings like f"od{''}oo" or f"{'pass'}{'word'}"
        if self._is_suppressed(node.lineno):
            self.generic_visit(node)
            return

        current_run = []
        for val in node.values:
            if isinstance(val, ast.Constant) and isinstance(val.value, str):
                current_run.append(val.value)
            elif isinstance(val, ast.FormattedValue) and isinstance(val.value, ast.Constant) and isinstance(val.value.value, str):
                current_run.append(val.value.value)
            else:
                if len(current_run) >= 2:
                    self._check_combined("".join(current_run), node.lineno)
                current_run = []
        if len(current_run) >= 2:
            self._check_combined("".join(current_run), node.lineno)

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Check str.join calls like ''.join(['pass', 'word'])
        if self._is_suppressed(node.lineno):
            self.generic_visit(node)
            return

        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and func.attr == "join"
            and isinstance(func.value, ast.Constant)
            and isinstance(func.value.value, str)
            and node.args
            and isinstance(node.args[0], (ast.List, ast.Tuple))
        ):
            sep = func.value.value
            elems = []
            for elt in node.args[0].elts:
                c = _get_constant_str(elt)
                if c is not None:
                    elems.append(c)
                else:
                    break
            if len(elems) == len(node.args[0].elts) and len(elems) >= 2:
                combined = sep.join(elems)
                self._check_combined(combined, node.lineno)

        self.generic_visit(node)


def scan_code(content: str, filename: str = "<string>") -> List[Tuple[str, int, str, str]]:
    """Scans in-memory Python code string for AST string assembly evasion patterns."""
    violations = []
    try:
        tree = ast.parse(content, filename=filename)
        visitor = SecretEvasionVisitor(filename, content=content)
        visitor.visit(tree)
        for lineno, combined, token in visitor.violations:
            violations.append((filename, lineno, combined, token))
    except (SyntaxError, UnicodeDecodeError):
        pass  # Skip non-parsable files
    return violations


def scan_file(filepath: str) -> List[Tuple[str, int, str, str]]:
    """Scans a single python file for AST string assembly evasion patterns."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return scan_code(content, filename=filepath)
    except (OSError, UnicodeDecodeError):
        return []


def scan_paths(paths: List[str]) -> Tuple[List[Tuple[str, int, str, str]], int]:
    """Scans a list of files or directories in parallel. Returns (violations, total_scanned)."""
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
        return all_violations, 0

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
    return all_violations, len(files_to_scan)


def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else ["tools", "enterprise"]
    print(f"[*] Running AST Secret Evasion Audit across: {targets}...")
    violations, total = scan_paths(targets)
    if violations:
        print(f"\n[✗] FAILED: {len(violations)} Scanner-Evasion pattern(s) detected across {total} files:")
        for fpath, lineno, combined, token in violations:
            print(f"    - {fpath}:{lineno} -> '{combined}' reconstructs protected token '{token}'")
        sys.exit(1)
    print(f"[✓] Zero AST string-concatenation/assembly scanner evasions detected across {total} files.")


if __name__ == "__main__":
    main()
