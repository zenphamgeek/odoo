#!/usr/bin/env python3
"""
Sovereign Build Metadata Generator & Clean Working Tree Enforcement Gate.
Prevents dirty/uncommitted git working trees from producing production release tags.
"""

import argparse
import datetime
import json
import os
import subprocess
import sys


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def enforce_clean_working_tree(strict=True, repo_root=REPO_ROOT):
    """Checks `git status --porcelain` and aborts with exit code 1 if strict=True and dirty."""
    res = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    dirty_lines = [line for line in res.stdout.splitlines() if line.strip()]
    if dirty_lines and strict:
        sys.stderr.write(
            f"ABORT: Working tree is dirty ({len(dirty_lines)} uncommitted/untracked entries). "
            "Refusing to stamp production build metadata.\n"
        )
        sys.exit(1)
    return len(dirty_lines) == 0


def generate_build_metadata(output_path="odoo/build_info.json", strict=True, repo_root=REPO_ROOT):
    is_clean = enforce_clean_working_tree(strict=strict, repo_root=repo_root)
    sha_res = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    commit_sha = sha_res.stdout.strip() or "unknown"
    payload = {
        "commit_sha": commit_sha,
        "working_tree_clean": is_clean,
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    if output_path:
        abs_out = output_path if os.path.isabs(output_path) else os.path.join(repo_root, output_path)
        os.makedirs(os.path.dirname(abs_out), exist_ok=True)
        with open(abs_out, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    return payload


def main():
    parser = argparse.ArgumentParser(description="Sovereign Build Metadata Generator")
    parser.add_argument("--output", default="", help="Optional output JSON path")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow dirty working tree (non-production local diagnostics only)",
    )
    args = parser.parse_args()
    info = generate_build_metadata(output_path=args.output or None, strict=not args.allow_dirty)
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
