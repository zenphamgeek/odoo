#!/usr/bin/env python3
"""
tools/sink_centrality.py
AST Sink-Centrality Auditor for Security-Critical Primitives.
Analyzes symbol definitions and sensitive call sites (atomic_write_text, etc.)
across the tools ecosystem to map security blast radius and prioritize verification.
"""

import argparse
import ast
import collections
import os
import sys
from pathlib import Path

SENSITIVE_SINK = "atomic_write_text"

def scan(root: Path):
    counts = collections.Counter()
    call_details = collections.defaultdict(list)

    for py in root.rglob("*.py"):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                name = getattr(fn, "attr", getattr(fn, "id", None))
                if name == SENSITIVE_SINK:
                    is_sensitive = any(
                        kw.arg == "mode" for kw in node.keywords
                    )
                    weight = 2 if is_sensitive else 1
                    counts[str(py)] += weight
                    call_details[str(py)].append({
                        "line": getattr(node, "lineno", 0),
                        "is_sensitive": is_sensitive
                    })

    return counts.most_common(), call_details

def main():
    parser = argparse.ArgumentParser(description="AST Sink Centrality Auditor")
    parser.add_argument("--root", default="tools", help="Directory root to scan")
    parser.add_argument("--flag-sensitive", action="store_true", help="Flag sensitive calls")
    args = parser.parse_args()

    root_path = Path(args.root)
    if not root_path.exists():
        print(f"[!] Path not found: {root_path}")
        sys.exit(1)

    print(f"=== AST SINK CENTRALITY AUDIT (Sink: {SENSITIVE_SINK}) ===")
    ranked, details = scan(root_path)
    for path, score in ranked:
        print(f"  [{score:2d}] {path}")
        if args.flag_sensitive:
            for item in details[path]:
                marker = "🔥 SENSITIVE (mode specified)" if item["is_sensitive"] else "ℹ️ STANDARD"
                print(f"       Line {item['line']}: {marker}")
    print(f"[✓] Audited {len(ranked)} files referencing {SENSITIVE_SINK}.")

if __name__ == "__main__":
    main()
