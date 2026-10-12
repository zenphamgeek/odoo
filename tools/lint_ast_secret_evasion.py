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

PROTECTED_FRAMEWORK_IDENTIFIERS = {
    "odoo",
    "postgres",
    "admin",
    "insilos",
    "innoria",
}

PROTECTED_CRED_WORDS = {
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
    # Legacy leaked credential fingerprint (remediated & rotated)
    "1e923bfedc220f6747aa0824df6bc496f16820a24816004c93e2abb43ed0a08c",
}


def _get_constant_parts(node: ast.AST) -> Optional[List[str]]:
    """Recursively resolves constituent constant string parts in an AST expression."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left_parts = _get_constant_parts(node.left)
        right_parts = _get_constant_parts(node.right)
        if left_parts is not None and right_parts is not None:
            return left_parts + right_parts
    return None


def _get_constant_str(node: ast.AST) -> Optional[str]:
    """Recursively resolves static string concatenation in AST."""
    parts = _get_constant_parts(node)
    return "".join(parts) if parts is not None else None


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
            stable_hash = hashlib.sha256(f"{self.filename}:{lineno}:{comment.strip()}".encode("utf-8")).hexdigest()[:12]
            self.suppressions.append((lineno, comment.strip(), stable_hash))
            return True
        return False

    def _check_combined(self, combined: str, lineno: int, parts: Optional[List[str]] = None):
        if not combined:
            return
        # 1. Check against sensitive secret SHA-256 digests (CWE-532: Zero plaintext bytes emitted)
        digest = hashlib.sha256(combined.encode("utf-8")).hexdigest()
        if digest in PROTECTED_SECRET_DIGESTS:
            # Never re-emit any plaintext bytes of a known secret; identify by digest only
            masked = f"<secret:sha256:{digest[:12]}…>"
            self.violations.append((lineno, masked, "secret-digest-match"))
            return

        # 2. Check against protected framework identifiers (e.g. 'od' + 'oo', 'inno' + 'ria')
        combined_lower = combined.lower()
        for token in PROTECTED_FRAMEWORK_IDENTIFIERS:
            if token.lower() in combined_lower:
                self.violations.append((lineno, combined, token))
                return

        # 3. Check against protected credential words (e.g. 'pass' + 'word', 'sec' + 'ret')
        # Genuine evasion signature: assembled token spanning >= 2 parts where NO individual part contains the token.
        # Innocent prose concatenations like "Invalid " + "token" do not flag because "token" is already in part 2.
        for token in PROTECTED_CRED_WORDS:
            t_lower = token.lower()
            if t_lower in combined_lower:
                if parts and len(parts) >= 2 and not any(t_lower in p.lower() for p in parts):
                    self.violations.append((lineno, combined, token))
                    return

    def visit_BinOp(self, node: ast.BinOp):
        if self._is_suppressed(node.lineno):
            self.generic_visit(node)
            return

        if isinstance(node.op, ast.Add):
            parts = _get_constant_parts(node)
            if parts and len(parts) >= 2:
                self._check_combined("".join(parts), node.lineno, parts=parts)
        elif isinstance(node.op, ast.Mod):
            left_str = _get_constant_str(node.left)
            if left_str is not None:
                args = []
                if isinstance(node.right, ast.Tuple):
                    for elt in node.right.elts:
                        c = _get_constant_str(elt)
                        if c is not None:
                            args.append(c)
                        else:
                            break
                    if len(args) != len(node.right.elts):
                        args = []
                else:
                    c = _get_constant_str(node.right)
                    if c is not None:
                        args = [c]
                if args:
                    try:
                        formatted = left_str % tuple(args)
                        self._check_combined(formatted, node.lineno, parts=[left_str] + args)
                    except Exception:
                        pass

        self.generic_visit(node)

    def visit_JoinedStr(self, node: ast.JoinedStr):
        # Check contiguous runs of constant segments in f-strings like f"od{''}oo" or f"{'pass'}{'word'}"
        if self._is_suppressed(node.lineno):
            self.generic_visit(node)
            return

        parts: List[str] = []
        for val in node.values:
            if isinstance(val, ast.Constant) and isinstance(val.value, str):
                parts.append(val.value)
            elif isinstance(val, ast.FormattedValue):
                inner = val.value
                c = _get_constant_str(inner)
                if c is not None:
                    parts.append(c)
                else:
                    parts = []
                    break
        if len(parts) >= 2:
            self._check_combined("".join(parts), node.lineno, parts=parts)

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
                self._check_combined(combined, node.lineno, parts=elems)

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
