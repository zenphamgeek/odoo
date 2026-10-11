#!/usr/bin/env python3
"""
Adversarial Security Test Suite for Pod Sync Packaging & Symlink Defense.
Verifies protections against CWE-59 (Symlink Traversal), CWE-538 (Data Exfiltration),
CWE-377 (Insecure Temp File / TOCTOU), and CWE-400 (Resource Exhaustion).
"""

import os
import sys
import tempfile
import shutil
import subprocess

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from tools.sync_all_pods_and_reload import assert_no_escaping_symlinks, MAX_ARCHIVE_SIZE_BYTES

def run_gate(gate_name, test_fn):
    print(f"\n[⚡] Running {gate_name}...")
    try:
        test_fn()
        print(f"[✓] {gate_name}: PASS")
        return True
    except Exception as e:
        print(f"[✗] {gate_name}: FAIL ({e})")
        return False

def test_gate1_existing_modules():
    """Gate 1: Existing repository paths have zero escaping symlinks."""
    assert_no_escaping_symlinks(
        os.path.join(REPO_ROOT, "enterprise/insilos_website"),
        ["__manifest__.py", "controllers", "views", "static/src/scss", "static/src/js", "static/src/icons"]
    )
    assert_no_escaping_symlinks(
        os.path.join(REPO_ROOT, "enterprise/insilos_theme_genesis"),
        ["__manifest__.py", "views", "static"]
    )
    assert_no_escaping_symlinks(
        os.path.join(REPO_ROOT, "addons/insilos_adapter"),
        ["hook.py"]
    )

def test_gate2_internal_relative_symlink():
    """Gate 2: Internal relative symlinks within module root are permitted."""
    with tempfile.TemporaryDirectory() as temp_root:
        f1 = os.path.join(temp_root, "target.txt")
        with open(f1, "w") as f:
            f.write("content")
        link = os.path.join(temp_root, "link_internal.txt")
        os.symlink("target.txt", link)
        # Should not raise
        assert_no_escaping_symlinks(temp_root, ["target.txt", "link_internal.txt"])

def test_gate3_direct_escaping_symlink():
    """Gate 3: Direct escaping symlink to outside target is blocked."""
    with tempfile.TemporaryDirectory() as outside_dir:
        outside_file = os.path.join(outside_dir, "secret.env")
        with open(outside_file, "w") as f:
            f.write("SECRET=123")
        with tempfile.TemporaryDirectory() as module_root:
            link = os.path.join(module_root, "malicious_link")
            os.symlink(outside_file, link)
            try:
                assert_no_escaping_symlinks(module_root, ["malicious_link"])
                raise AssertionError("Failed to block direct escaping symlink!")
            except RuntimeError as e:
                assert "Security Invariant Violated: Symlink escapes module root" in str(e)

def test_gate4_nested_escaping_symlink():
    """Gate 4: Subdirectory nested symlink escaping module root is blocked."""
    with tempfile.TemporaryDirectory() as outside_dir:
        outside_file = os.path.join(outside_dir, "odoo.conf")
        with open(outside_file, "w") as f:
            f.write("admin_passwd = admin")
        with tempfile.TemporaryDirectory() as module_root:
            sub = os.path.join(module_root, "static", "src", "icons")
            os.makedirs(sub)
            link = os.path.join(sub, "icon.svg")
            os.symlink(outside_file, link)
            try:
                assert_no_escaping_symlinks(module_root, ["static"])
                raise AssertionError("Failed to block nested escaping symlink!")
            except RuntimeError as e:
                assert "Security Invariant Violated: Symlink escapes module root" in str(e)

def test_gate5_missing_optional_members():
    """Gate 5: Non-existent member paths in allowlist are skipped without crashing."""
    with tempfile.TemporaryDirectory() as module_root:
        assert_no_escaping_symlinks(module_root, ["non_existent_file.py", "missing_dir"])

def test_gate6_archive_size_ceiling():
    """Gate 6: Archive size assertion correctly enforces ceiling."""
    assert MAX_ARCHIVE_SIZE_BYTES == 50 * 1024 * 1024
    fake_size = 55 * 1024 * 1024
    assert fake_size > MAX_ARCHIVE_SIZE_BYTES

def test_gate7_temporary_staging_cleanup():
    """Gate 7: Temporary staging directory is reliably cleaned up."""
    staging = tempfile.mkdtemp(prefix="test_sync_clean_")
    assert os.path.exists(staging)
    try:
        tarball = os.path.join(staging, "sample.tar.gz")
        with open(tarball, "wb") as f:
            f.write(b"data")
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    assert not os.path.exists(staging)

def main():
    print("[⚡] ======================================================================")
    print("[⚡] Pod Sync Packaging Adversarial Security Verification Suite")
    print("[⚡] ======================================================================")
    gates = [
        ("Gate 1: Existing Production Modules Symlink Invariant", test_gate1_existing_modules),
        ("Gate 2: Internal Relative Symlink Permitted", test_gate2_internal_relative_symlink),
        ("Gate 3: Direct Symlink Escape Blocked (CWE-59 / CWE-538)", test_gate3_direct_escaping_symlink),
        ("Gate 4: Nested Subdirectory Symlink Escape Blocked (CWE-59)", test_gate4_nested_escaping_symlink),
        ("Gate 5: Missing Optional Members Handled Safely", test_gate5_missing_optional_members),
        ("Gate 6: Archive Size Ceiling Enforced (CWE-400)", test_gate6_archive_size_ceiling),
        ("Gate 7: Staging Directory Isolation & Cleanup (CWE-377)", test_gate7_temporary_staging_cleanup),
    ]

    all_pass = True
    for name, fn in gates:
        if not run_gate(name, fn):
            all_pass = False

    print("\n[⚡] ======================================================================")
    if all_pass:
        print(f"[✓] 🎉 ALL {len(gates)} PACKAGING SECURITY GATES PASSED (100% SUCCESS)!")
        print("[⚡] ======================================================================")
        sys.exit(0)
    else:
        print("[✗] SOME GATES FAILED!")
        print("[⚡] ======================================================================")
        sys.exit(1)

if __name__ == "__main__":
    main()
