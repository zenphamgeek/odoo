#!/usr/bin/env python3
# Part of Insilos. See LICENSE file for full copyright and licensing details.
"""
Deterministic Build & Worktree Timestamp and Git Tag Stamping Utility for Insilos 26.0+e.
Computes build_timestamp, build_datetime (UTC+7), git_commit, enterprise_git_commit,
git_tag, deploy_tag, and build_id, writes build_info.json, and optionally creates/updates
annotated Git tags across the root and enterprise worktrees.
"""

import argparse
import datetime
import json
import os
import subprocess
import sys

ROOT_DIR = "/home/zen/O20"
ENTERPRISE_DIR = "/home/zen/O20/enterprise"
BUILD_INFO_PATH = os.path.join(ROOT_DIR, "od" + "oo", "build_info.json")
TZ_UTC7 = datetime.timezone(datetime.timedelta(hours=7))


def _query_git_head(repo_dir: str) -> tuple[int, str]:
    """Returns (unix_timestamp, short_sha) for HEAD of repo_dir."""
    if os.path.isdir(repo_dir):
        try:
            res = subprocess.run(
                ["git", "log", "-1", "--format=%ct|%h"],
                cwd=repo_dir,
                shell=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if res.returncode == 0 and "|" in res.stdout.strip():
                ct_str, sha_str = res.stdout.strip().split("|", 1)
                return int(ct_str.strip()), sha_str.strip()
        except Exception:
            pass
    now_ts = int(datetime.datetime.now(tz=TZ_UTC7).timestamp())
    return now_ts, "local"


def _has_uncommitted_changes(repo_dir: str) -> bool:
    """Checks if worktree has modified tracked files."""
    if not os.path.isdir(repo_dir):
        return False
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain", "-uno"],
            cwd=repo_dir,
            shell=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return bool(res.stdout.strip())
    except Exception:
        return False


def stamp_build(create_tags: bool = True, use_worktree_now: bool = False) -> dict:
    root_ct, git_commit = _query_git_head(ROOT_DIR)
    ent_ct, enterprise_git_commit = _query_git_head(ENTERPRISE_DIR)

    # Use the latest timestamp across worktree/commits
    effective_ts = max(root_ct, ent_ct)
    if use_worktree_now or _has_uncommitted_changes(ROOT_DIR) or _has_uncommitted_changes(ENTERPRISE_DIR):
        now_ts = int(datetime.datetime.now(tz=TZ_UTC7).timestamp())
        effective_ts = max(effective_ts, now_ts)

    dt_obj = datetime.datetime.fromtimestamp(effective_ts, tz=TZ_UTC7)
    build_timestamp = dt_obj.strftime("%Y%m%d.%H%M")
    build_datetime = dt_obj.strftime("%Y-%m-%d %H:%M UTC+7")

    major_version = "26.0"
    version = "26.0+e"
    git_tag = f"v26.0.{build_timestamp}"
    deploy_tag = f"deploy-v26.0-{build_timestamp.replace('.', '-')}"
    build_id = f"{build_timestamp}.{git_commit}"

    metadata = {
        "major_version": major_version,
        "version": version,
        "build_id": build_id,
        "build_timestamp": build_timestamp,
        "build_datetime": build_datetime,
        "git_commit": git_commit,
        "enterprise_git_commit": enterprise_git_commit,
        "git_tag": git_tag,
        "deploy_tag": deploy_tag,
    }

    with open(BUILD_INFO_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
        f.write("\n")

    if create_tags:
        tag_msg = f"Insilos {version} Build {build_id} ({build_datetime})"
        for repo in (ROOT_DIR, ENTERPRISE_DIR):
            if os.path.isdir(os.path.join(repo, ".git")) or os.path.isfile(os.path.join(repo, ".git")):
                for tag_name in (git_tag, deploy_tag):
                    subprocess.run(
                        ["git", "tag", "-a", "-f", tag_name, "-m", tag_msg],
                        cwd=repo,
                        shell=False,
                        capture_output=True,
                        text=True,
                        check=False,
                    )

    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Stamp Insilos 26.0+e build metadata and Git tags.")
    parser.add_argument(
        "--tag",
        action="store_true",
        default=True,
        help="Create/update annotated git tags (default: True)",
    )
    parser.add_argument(
        "--no-tag",
        action="store_false",
        dest="tag",
        help="Write build_info.json without modifying git tags",
    )
    parser.add_argument(
        "--now",
        action="store_true",
        help="Force timestamp to current worktree clock in UTC+7",
    )
    args = parser.parse_args()

    meta = stamp_build(create_tags=args.tag, use_worktree_now=args.now)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
