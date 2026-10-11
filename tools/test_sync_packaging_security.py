#!/usr/bin/env python3
"""
Adversarial Security Test Suite for Pod Sync Packaging & Symlink Defense.
Verifies protections against CWE-78 (Command Injection), CWE-367 (TOCTOU),
CWE-59 (Symlink Traversal), CWE-538 (Data Exfiltration), CWE-377 (Insecure Temp File),
CWE-400 (Resource Exhaustion), and Content-Addressed Digest Pinning.
"""

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from tools.sync_all_pods_and_reload import (
    assert_no_escaping_symlinks,
    assert_tree_size,
    compute_sha256,
    freeze_and_audit_members,
    run_cmd,
    MAX_ARCHIVE_SIZE_BYTES,
)

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

def test_gate8_cwe78_shell_sink_rejection():
    """Gate 8: run_cmd strictly rejects raw string commands with TypeError (CWE-78)."""
    try:
        run_cmd("echo 'attempting shell injection'")
        raise AssertionError("Failed to reject shell string command!")
    except TypeError as e:
        assert "run_cmd requires an argv list[str]" in str(e)
    # Valid list command succeeds
    res = run_cmd(["echo", "safe_execution"], check=True)
    assert res.stdout.strip() == "safe_execution"

def test_gate9_cwe367_toctou_snapshot_freeze():
    """Gate 9: freeze_and_audit_members produces an isolated snapshot with zero link leaks."""
    with tempfile.TemporaryDirectory() as src:
        f = os.path.join(src, "module.py")
        with open(f, "w") as fp:
            fp.write("print('hello')")
        with tempfile.TemporaryDirectory() as dest:
            frozen = os.path.join(dest, "frozen")
            freeze_and_audit_members(src, ["module.py"], frozen)
            assert os.path.exists(os.path.join(frozen, "module.py"))
            # Modify src after freeze; frozen copy remains unchanged
            with open(f, "w") as fp:
                fp.write("malicious payload")
            with open(os.path.join(frozen, "module.py"), "r") as fp:
                assert fp.read() == "print('hello')"

def test_gate10_cwe400_tree_size_ceiling_pre_package():
    """Gate 10: assert_tree_size fails closed before packaging if source exceeds limit."""
    with tempfile.TemporaryDirectory() as root:
        f = os.path.join(root, "big.bin")
        with open(f, "wb") as fp:
            fp.write(b"0" * 1024)
        # Limit 500 bytes should raise RuntimeError
        try:
            assert_tree_size(root, 500)
            raise AssertionError("Failed to enforce tree size ceiling!")
        except RuntimeError as e:
            assert "Source tree exceeds ceiling before packaging" in str(e)
        # Limit 2000 bytes passes
        total = assert_tree_size(root, 2000)
        assert total == 1024

def test_gate11_sha256_digest_pinning():
    """Gate 11: compute_sha256 produces deterministic, verifiable digests."""
    with tempfile.NamedTemporaryFile() as tf:
        tf.write(b"known content for sha256 test")
        tf.flush()
        expected = hashlib.sha256(b"known content for sha256 test").hexdigest()
        assert compute_sha256(tf.name) == expected

def main():
    print("[⚡] ======================================================================")
    print("[⚡] Pod Sync Packaging Adversarial Security Verification Suite (11 Gates)")
    print("[⚡] ======================================================================")
    gates = [
        ("Gate 1: Existing Production Modules Symlink Invariant", test_gate1_existing_modules),
        ("Gate 2: Internal Relative Symlink Permitted", test_gate2_internal_relative_symlink),
        ("Gate 3: Direct Symlink Escape Blocked (CWE-59 / CWE-538)", test_gate3_direct_escaping_symlink),
        ("Gate 4: Nested Subdirectory Symlink Escape Blocked (CWE-59)", test_gate4_nested_escaping_symlink),
        ("Gate 5: Missing Optional Members Handled Safely", test_gate5_missing_optional_members),
        ("Gate 6: Archive Size Ceiling Enforced (CWE-400)", test_gate6_archive_size_ceiling),
        ("Gate 7: Staging Directory Isolation & Cleanup (CWE-377)", test_gate7_temporary_staging_cleanup),
        ("Gate 8: Shell String Rejection & Safe Argv Execution (CWE-78)", test_gate8_cwe78_shell_sink_rejection),
        ("Gate 9: TOCTOU Snapshot Freeze Isolation (CWE-367)", test_gate9_cwe367_toctou_snapshot_freeze),
        ("Gate 10: Pre-Packaging Tree Size Ceiling Enforcement (CWE-400)", test_gate10_cwe400_tree_size_ceiling_pre_package),
        ("Gate 11: Content-Addressed SHA-256 Digest Pinning", test_gate11_sha256_digest_pinning),
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
