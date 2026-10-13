#!/usr/bin/env python3
"""Fail CI if any importlib.import_module() or __import__() call is passed a dynamically
constructed module path (string concat / join / format / name). Rationale: commit
99030037c obfuscated an import to evade a scanner; this guard blocks recurrence.
Exit 0 = clean, 1 = violation, 2 = usage / syntax / parse error (fail closed)."""

import ast
import io
import pathlib
import stat as _stat
import sys
import tokenize
from typing import Dict, List, Optional, Tuple


def _is_dynamic_path(node: ast.AST) -> bool:
    """Returns True if the AST node representing the module path is dynamically constructed."""
    # A single static string literal e.g. "odoo.addons.product"
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return False
    # Anything else (BinOp +, %, JoinedStr f-string, Call .join, Name variable) is dynamic
    return True


def extract_comments_by_line(content: str) -> Dict[int, str]:
    """Extracts actual Python comment tokens mapped by line number (ignores '#' in string literals)."""
    comments: Dict[int, str] = {}
    tokens = tokenize.tokenize(io.BytesIO(content.encode("utf-8")).readline)
    for tok in tokens:
        if tok.type == tokenize.COMMENT:
            comments[tok.start[0]] = tok.string
    return comments


def _target_name_arg(node: ast.Call) -> Optional[ast.expr]:
    """Return the module-name argument whether passed positionally, as name=,
    or via **kwargs unpack. Also treats an unresolved **kwargs unpack as
    suspicious so it cannot be used to smuggle dynamic names past inspection.
    """
    if node.args:
        return node.args[0]
    for kw in node.keywords:
        if kw.arg == "name":
            return kw.value
    # kw.arg is None => **kwargs unpack; name may be hidden inside it
    for kw in node.keywords:
        if kw.arg is None:
            return kw.value
    return None


def _safe_dump(node: ast.AST, limit: int = 300) -> str:
    d = ast.dump(node)
    return d if len(d) <= limit else d[:limit] + " ...<truncated>"


def scan_source(content: str, filename: str = "<source>") -> Tuple[List[str], List[str]]:
    """Scans python source for dynamic import_module or __import__ calls.
    Returns (violations, suppressions).
    """
    violations: List[str] = []
    suppressions: List[str] = []
    try:
        tree = ast.parse(content, filename=filename)
    except RecursionError:
        raise ValueError("source too deeply nested to parse safely") from None
    except MemoryError:
        raise ValueError("source exhausted memory during parse") from None
    except (SyntaxError, ValueError) as e:
        raise ValueError(f"unparseable source: {filename}: {e}")
    comments = extract_comments_by_line(content)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_target = (
            (isinstance(func, ast.Attribute) and func.attr in ("import_module", "__import__"))
            or (isinstance(func, ast.Name) and func.id in ("import_module", "__import__"))
        )
        if is_target:
            target = _target_name_arg(node)
            if target is not None and _is_dynamic_path(target):
                lineno = getattr(node, "lineno", 1)
                # Only honor suppression directive on the call's opening line for review clarity
                c = comments.get(lineno, "")
                if "import-obfuscation-ignore" in c or "ast-evasion-ignore" in c:
                    suppressions.append(f"{filename}:{lineno}: [suppressed] {c.strip()}")
                    continue
                violations.append(
                    f"{filename}:{lineno}: dynamic import path: {_safe_dump(target)}"
                )
    return violations, suppressions


MAX_SOURCE_BYTES = 5 * 1024 * 1024  # bound worst-case parse cost; fail closed if exceeded


def scan_file(path: pathlib.Path, quick_filter: bool = False) -> Tuple[List[str], List[str]]:
    st = path.stat()  # OSError here is caught fail-closed in main()
    if not _stat.S_ISREG(st.st_mode):
        raise ValueError(f"refusing to scan non-regular file (fifo/device/dir): {path}")
    size = st.st_size
    if size > MAX_SOURCE_BYTES:
        raise ValueError(f"source exceeds parse cap ({size} > {MAX_SOURCE_BYTES} bytes): {path}")
    # Read a bounded amount so a post-stat growth (TOCTOU) cannot defeat the cap
    with path.open("rb") as f:
        raw = f.read(MAX_SOURCE_BYTES + 1)
    if len(raw) > MAX_SOURCE_BYTES:
        raise ValueError(f"source grew past parse cap during read (TOCTOU): {path}")
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ValueError(f"non-utf8 source cannot be scanned safely: {path}: {e}")
    if "\x00" in content:
        raise ValueError(f"source code string cannot contain null bytes: {path}")
    if quick_filter and ("import_module" not in content and "__import__" not in content):
        return [], []
    return scan_source(content, filename=str(path))


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv
    roots = [pathlib.Path(a) for a in argv[1:]] or [pathlib.Path("tools")]
    found_violations: List[str] = []
    found_suppressions: List[str] = []

    for root in roots:
        if not root.exists():
            print(f"audit: path not found: {root}", file=sys.stderr)
            return 2
        if root.is_dir():
            py_files = [(p, True) for p in root.rglob("*.py")]
        else:
            py_files = [(root, False)] if root.suffix == ".py" else []

        for py, is_quick in py_files:
            try:
                v, s = scan_file(py, quick_filter=is_quick)
                found_violations.extend(v)
                found_suppressions.extend(s)
            except SyntaxError as exc:
                print(f"audit: unparseable {py}: {exc}", file=sys.stderr)
                return 2
            except (ValueError, tokenize.TokenError) as exc:
                # ast.parse raises ValueError for null-byte / malformed sources.
                # tokenize.TokenError covers the comment-extraction phase.
                # A .py file we cannot safely parse is suspicious -> fail closed.
                print(f"audit: rejected malformed source {py}: {exc}", file=sys.stderr)
                return 2
            except (RecursionError, MemoryError) as exc:
                # Pathologically nested / oversized AST (DoS vector) -> fail closed.
                print(f"audit: rejected pathological source {py}: {exc}", file=sys.stderr)
                return 2
            except (UnicodeDecodeError, OSError) as exc:
                # FAIL CLOSED: an unreadable .py must not silently evade the guard.
                print(f"audit: FAIL unreadable {py}: {exc}", file=sys.stderr)
                return 2

    if found_violations:
        for v in found_violations:
            print(v, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
