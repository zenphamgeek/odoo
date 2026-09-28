#!/usr/bin/env python3
"""
Adversarial AST & Code Integrity Verification Harness
Challenger Track 1 — AST Integrity & Server Bootability (R3 & R4)

Executes parallel, deep AST parsing and compilation checks across:
- odoo/
- addons/web
- addons/base (including symlink resolution)
- addons/bus
- addons/mail
- addons/portal
- addons/auth_* (all 12 auth modules)
- Root scripts & utilities: insilos-bin, setup.py, install_manager.py, challenger_stress_test.py, etc.
- insilos_adapter/
"""

import ast
import concurrent.futures
import glob
import json
import os
import sys
import time
from pathlib import Path


def get_target_files(root_dir: str):
    root_path = Path(root_dir).resolve()
    target_files = {}

    # Define scopes
    scopes = {
        "odoo": root_path / "odoo",
        "addons/web": root_path / "addons" / "web",
        "addons/base": root_path / "addons" / "base",
        "addons/bus": root_path / "addons" / "bus",
        "addons/mail": root_path / "addons" / "mail",
        "addons/portal": root_path / "addons" / "portal",
    }

    # Add all addons/auth_*
    for auth_dir in sorted(glob.glob(str(root_path / "addons" / "auth_*"))):
        rel = os.path.relpath(auth_dir, root_path)
        scopes[rel] = Path(auth_dir)

    # Add insilos_adapter
    adapter_dir = root_path / "insilos_adapter"
    if adapter_dir.exists():
        scopes["insilos_adapter"] = adapter_dir

    # Gather files per scope
    for scope_name, scope_dir in scopes.items():
        if not scope_dir.exists():
            print(f"[WARN] Scope path does not exist: {scope_dir}")
            continue
        py_files = []
        for p in scope_dir.rglob("*.py"):
            # Resolve symlinks if needed, but keep file path
            if p.is_file():
                py_files.append(p)
        target_files[scope_name] = py_files

    # Root and scripts
    root_scripts = []
    root_candidates = [
        "insilos-bin",
        "setup.py",
        "install_manager.py",
        "challenger_stress_test.py",
        "update_js.py",
        "update_snippets.py",
        "scripts/counter_code_scanner.py",
        "scripts/adversarial_ast_check.py",
    ]
    for cand in root_candidates:
        cand_path = root_path / cand
        if cand_path.is_file():
            root_scripts.append(cand_path)
    target_files["root_scripts"] = root_scripts

    return target_files


def verify_file_ast(file_path_str: str):
    """
    Adversarial verification of a single Python source file.
    Tests:
    1. Raw file reading (detects encoding/read errors)
    2. ast.parse() syntax analysis
    3. AST node counting & walk
    4. PyCF_ONLY_AST compilation
    5. Standard bytecode compilation
    """
    path = Path(file_path_str)
    start_t = time.perf_counter()
    try:
        raw_bytes = path.read_bytes()
        # Decode using standard Python source decoding
        try:
            source = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            # Fallback for historical encodings with coding cookies
            source = raw_bytes.decode("latin-1")

        lines = source.count("\n") + 1

        # 1. ast.parse
        tree = ast.parse(source, filename=str(path))

        # 2. Count AST nodes
        node_count = sum(1 for _ in ast.walk(tree))

        # 3. Compilation check (bytecode generation without execution)
        code_obj = compile(source, str(path), "exec", dont_inherit=True)

        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        return {
            "path": str(path),
            "status": "PASS",
            "lines": lines,
            "bytes": len(raw_bytes),
            "nodes": node_count,
            "elapsed_ms": elapsed_ms,
            "error": None,
        }
    except SyntaxError as e:
        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        return {
            "path": str(path),
            "status": "SYNTAX_ERROR",
            "lines": 0,
            "bytes": path.stat().st_size if path.exists() else 0,
            "nodes": 0,
            "elapsed_ms": elapsed_ms,
            "error": f"SyntaxError: {e.msg} at line {e.lineno}, col {e.offset}: {e.text}",
        }
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        return {
            "path": str(path),
            "status": "ERROR",
            "lines": 0,
            "bytes": path.stat().st_size if path.exists() else 0,
            "nodes": 0,
            "elapsed_ms": elapsed_ms,
            "error": f"{type(e).__name__}: {str(e)}",
        }


def main():
    root_dir = os.environ.get("PROJECT_ROOT", "/home/zen/O20")
    print(f"=== Adversarial AST & Code Integrity Verification Harness ===")
    print(f"Target Root: {root_dir}")
    print(f"Python Interpreter: {sys.executable} (Version: {sys.version.split()[0]})")

    targets = get_target_files(root_dir)

    all_file_paths = []
    seen = set()
    scope_file_map = {}

    for scope, file_list in targets.items():
        scope_file_map[scope] = []
        for f in file_list:
            resolved = str(f.resolve())
            f_str = str(f)
            # Track scope association
            scope_file_map[scope].append(f_str)
            if resolved not in seen:
                seen.add(resolved)
                all_file_paths.append(f_str)

    total_unique_files = len(all_file_paths)
    print(f"Total Unique Python Files To Parse: {total_unique_files}")
    for scope, fl in targets.items():
        print(f"  - {scope:35s}: {len(fl):4d} files")

    # Parallel Execution using ProcessPoolExecutor for maximum throughput
    workers = min(os.cpu_count() or 4, 16)
    print(f"\nLaunching parallel verification across {workers} worker processes...")
    t0 = time.perf_counter()

    results_by_path = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        future_to_path = {executor.submit(verify_file_ast, p): p for p in all_file_paths}
        for future in concurrent.futures.as_completed(future_to_path):
            res = future.result()
            results_by_path[res["path"]] = res

    total_duration = time.perf_counter() - t0

    # Aggregate Statistics
    passed = 0
    failed = 0
    total_lines = 0
    total_bytes = 0
    total_nodes = 0
    failures = []

    for path, res in results_by_path.items():
        if res["status"] == "PASS":
            passed += 1
            total_lines += res["lines"]
            total_bytes += res["bytes"]
            total_nodes += res["nodes"]
        else:
            failed += 1
            failures.append(res)

    print(f"\n=== Verification Results ===")
    print(f"Total Files Checked: {len(results_by_path)}")
    print(f"Passed:              {passed}")
    print(f"Failed:              {failed}")
    print(f"Total Lines of Code: {total_lines:,}")
    print(f"Total Bytes Parsed:  {total_bytes:,} bytes ({total_bytes / (1024*1024):.2f} MB)")
    print(f"Total AST Nodes:     {total_nodes:,}")
    print(f"Wallclock Duration:  {total_duration:.3f}s (Throughput: {len(results_by_path)/total_duration:.1f} files/sec)")

    print(f"\n=== Breakdown by Scope ===")
    for scope, file_list in scope_file_map.items():
        scope_passed = 0
        scope_failed = 0
        scope_lines = 0
        scope_nodes = 0
        for f in file_list:
            r = results_by_path.get(f) or results_by_path.get(str(Path(f).resolve()))
            if r and r["status"] == "PASS":
                scope_passed += 1
                scope_lines += r["lines"]
                scope_nodes += r["nodes"]
            elif r:
                scope_failed += 1
        status_str = "[OK]" if scope_failed == 0 else f"[FAIL: {scope_failed}]"
        print(f"  {scope:35s}: {scope_passed:4d} passed, {scope_failed:2d} failed, {scope_lines:7,d} LOC, {scope_nodes:8,d} nodes {status_str}")

    if failures:
        print(f"\n[CRITICAL FAILURE] {len(failures)} files failed AST verification:")
        for fail in failures:
            print(f"  File: {fail['path']}")
            print(f"  Error: {fail['error']}")
        sys.exit(1)
    else:
        print(f"\n[VERDICT: AST INTEGRITY CONFIRMED] 0 syntax errors across all {total_unique_files} files.")
        sys.exit(0)


if __name__ == "__main__":
    main()
