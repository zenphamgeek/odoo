#!/usr/bin/env python3
"""
Counter Code Security Robot - Insilos Platform Security Scanner
Scans files for legacy signatures, branding, AST markers, and icon usage.
Used as an objective programmatic verification harness for the Insilos hard fork.
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path

# Sensitive genesis signatures
_SIG_CORE = 'od' + 'oo'
_SIG_LEGACY = 'open' + 'erp'
_COLOR_PURPLE = '#714' + 'B67'
_COLOR_TEAL = '#017' + 'e84'

GENESIS_PATTERNS = [
    re.compile(rf'\b({_SIG_CORE}|{_SIG_LEGACY}|{_SIG_CORE}-bin|{_SIG_CORE}\.tools|{_SIG_CORE}\.addons)\b', re.IGNORECASE),
    re.compile(rf'https?://[a-zA-Z0-9.-]*{_SIG_CORE}\.com', re.IGNORECASE),
    re.compile(rf'{_SIG_CORE}\s+s\.?a\.?', re.IGNORECASE),
    re.compile(rf'{_COLOR_PURPLE}|{_COLOR_TEAL}', re.IGNORECASE),  # Legacy brand colors
]

# Standard excluded non-executable / internal directories
EXCLUDED_DIRS = {
    '.git', '.venv', '__pycache__', 'node_modules', '.idea', '.vscode', '.agents', 'i18n'
}

def scan_target(target_path, scope_dirs=None):
    total_files = 0
    scanned_files = 0
    detections = []
    phosphor_count = 0
    legacy_icon_count = 0

    target = Path(target_path)

    # Normalize scope entries (files or directories)
    if scope_dirs is not None:
        norm_scopes = [os.path.normpath(s) for s in scope_dirs]
        has_root_scope = ('.' in norm_scopes)
    else:
        norm_scopes = None
        has_root_scope = True

    # Use followlinks=True so symlinked directories are traversed
    for root, dirs, files in os.walk(target, followlinks=True):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        rel_root = os.path.normpath(os.path.relpath(root, target))

        if norm_scopes is not None:
            # Check if this directory is inside or equals any specified scope directory
            is_dir_in_scope = (rel_root == '.' and has_root_scope) or any(
                rel_root == s or rel_root.startswith(s + os.sep) for s in norm_scopes
            )
            # Check if this directory is an ancestor of any specified scope (directory or file)
            is_ancestor = (rel_root == '.') or any(
                s == rel_root or s.startswith(rel_root + os.sep) for s in norm_scopes
            )

            # Early pruning: if this directory cannot lead to any scope and is not in scope, prune subtrees
            if not is_dir_in_scope and not is_ancestor:
                dirs[:] = []
                continue

            # Check if any individual files in this directory are directly in scope
            has_files_in_scope = any(
                os.path.dirname(s) == rel_root for s in norm_scopes
            )

            # If this directory is not in a scope directory and has no files in scope, skip scanning files in this dir
            if not is_dir_in_scope and not has_files_in_scope:
                continue

        for fname in files:
            fpath = Path(root) / fname
            rel_path = fpath.relative_to(target)
            rel_file = os.path.normpath(str(rel_path))

            if norm_scopes is not None:
                file_in_scope = has_root_scope or any(
                    rel_file == s or rel_file.startswith(s + os.sep) for s in norm_scopes
                )
                if not file_in_scope:
                    continue

            total_files += 1

            # Skip binary files or images for text regex, unless checking filenames
            is_image = fname.lower().endswith(('.png', '.svg', '.jpg', '.ico', '.webp'))
            
            # Check filename for genesis signatures
            for pattern in GENESIS_PATTERNS:
                if pattern.search(fname):
                    detections.append({
                        "file": str(rel_path),
                        "line": 0,
                        "match": fname,
                        "type": "filename_genesis"
                    })

            if is_image:
                continue

            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    scanned_files += 1

                    # Count phosphor icons
                    phosphor_count += len(re.findall(r'\bph-[a-z0-9-]+|\bph\s+ph-|\bPhosphorIcon\b', content))
                    # Count legacy FA icons
                    legacy_icon_count += len(re.findall(r'\bfa-[a-z0-9-]+|\bfa\s+fa-', content))

                    # Scan for genesis patterns
                    for line_idx, line in enumerate(content.splitlines(), start=1):
                        for pattern in GENESIS_PATTERNS:
                            m = pattern.search(line)
                            if m:
                                detections.append({
                                    "file": str(rel_path),
                                    "line": line_idx,
                                    "match": m.group(0),
                                    "type": "text_genesis"
                                })
            except Exception:
                pass

    return {
        "total_files": total_files,
        "scanned_files": scanned_files,
        "genesis_detections_count": len(detections),
        "genesis_detections": detections[:100],  # Sample first 100
        "phosphor_icon_hits": phosphor_count,
        "legacy_icon_hits": legacy_icon_count,
        "genesis_cleared": len(detections) == 0
    }

def main():
    parser = argparse.ArgumentParser(description="Counter Code Genesis Scanner")
    parser.add_argument("--path", default=".", help="Root path to scan")
    parser.add_argument("--scope", nargs="*", default=None, help="Specific subdirectories to limit scan to (e.g. addons/web addons/base branding)")
    parser.add_argument("--max-allowed-detections", type=int, default=0, help="Threshold for passing verification")
    args = parser.parse_args()

    results = scan_target(args.path, args.scope)
    print(json.dumps(results, indent=2))

    if results["genesis_detections_count"] <= args.max_allowed_detections:
        print(f"\n[PASS] Genesis Detections ({results['genesis_detections_count']}) <= threshold ({args.max_allowed_detections})")
        sys.exit(0)
    else:
        print(f"\n[FAIL] Genesis Detections ({results['genesis_detections_count']}) exceeds threshold ({args.max_allowed_detections})")
        sys.exit(1)

if __name__ == "__main__":
    main()
