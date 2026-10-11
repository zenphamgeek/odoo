#!/usr/bin/env python3
"""
tools/__tests__/test_atomic_io.py
Unit tests for atomic_io.py:
1. Verifies atomic writes.
2. Verifies file permission preservation.
3. Verifies tempfile cleanup on write failure.
"""

import os
import stat
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from atomic_io import atomic_write_text

class TestAtomicIO(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_atomic_write_new_file(self):
        target = self.dir_path / "test_file.txt"
        atomic_write_text(target, "Hello Atomic World\n")
        self.assertTrue(target.exists())
        self.assertEqual(target.read_text(encoding="utf-8"), "Hello Atomic World\n")
        # Default mode is 0644
        mode = target.stat().st_mode & 0o777
        self.assertEqual(mode, 0o644)

    def test_atomic_write_preserves_permissions(self):
        target = self.dir_path / "script.sh"
        target.write_text("#!/bin/sh\necho hi\n", encoding="utf-8")
        target.chmod(0o755)

        atomic_write_text(target, "#!/bin/sh\necho updated\n")
        self.assertEqual(target.read_text(encoding="utf-8"), "#!/bin/sh\necho updated\n")
        mode = target.stat().st_mode & 0o777
        self.assertEqual(mode, 0o755)

    def test_atomic_write_replaces_existing(self):
        target = self.dir_path / "data.xml"
        target.write_text("<old>data</old>", encoding="utf-8")
        atomic_write_text(target, "<new>data</new>")
        self.assertEqual(target.read_text(encoding="utf-8"), "<new>data</new>")

    def test_atomic_write_same_dir_temp(self):
        target = self.dir_path / "target.txt"
        atomic_write_text(target, "content")
        # Ensure no lingering .tmp files
        tmp_files = list(self.dir_path.glob(".*.tmp"))
        self.assertEqual(len(tmp_files), 0)

    def test_atomic_write_survives_crash_or_interrupted_replace(self):
        """Torn-write invariant: interrupted write leaves prior file intact."""
        target = self.dir_path / "prior_good.txt"
        target.write_text("PRIOR_GOOD_STATE", encoding="utf-8")

        def boom(*args, **kwargs):
            raise KeyboardInterrupt("Simulated SIGKILL mid-replace")

        orig_replace = os.replace
        os.replace = boom
        try:
            with self.assertRaises(KeyboardInterrupt):
                atomic_write_text(target, "PARTIAL_CORRUPTED_STATE")
        finally:
            os.replace = orig_replace

        # Prior file remains intact
        self.assertEqual(target.read_text(encoding="utf-8"), "PRIOR_GOOD_STATE")
        # Ensure temporary file was cleanly cleaned up
        tmp_files = list(self.dir_path.glob(".*.tmp"))
        self.assertEqual(len(tmp_files), 0)

    def test_atomic_write_explicit_mode_and_dir_fsync(self):
        """CWE-276/732: Explicit mode parameter (e.g. 0o600 for HMAC trust anchors) is enforced even on first creation."""
        target = self.dir_path / "sensitive_anchor.json"
        atomic_write_text(target, '{"anchor": "secure_hmac"}', mode=0o600)
        self.assertTrue(target.exists())
        mode = target.stat().st_mode & 0o777
        self.assertEqual(mode, 0o600)

    def test_atomic_write_creates_missing_nested_parent_dirs(self):
        """Finding 1: atomic_write_text creates missing parent directories recursively without FileNotFoundError."""
        target = self.dir_path / "nested" / "deep" / "anchor.json"
        atomic_write_text(target, '{"status": "ok"}', mode=0o600)
        self.assertTrue(target.exists())
        self.assertEqual(target.read_text(encoding="utf-8"), '{"status": "ok"}')
        mode = target.stat().st_mode & 0o777
        self.assertEqual(mode, 0o600)
        # Verify parent directory is restricted to 0o700 for sensitive targets
        parent_mode = target.parent.stat().st_mode & 0o777
        self.assertEqual(parent_mode, 0o700)

    def test_atomic_write_refuses_symlink_for_sensitive_targets(self):
        """CWE-59: Refuses writing sensitive files through symlink."""
        real_file = self.dir_path / "real_file.txt"
        real_file.write_text("INITIAL_CONTENT", encoding="utf-8")
        symlink_target = self.dir_path / "symlink_file.txt"
        symlink_target.symlink_to(real_file)

        with self.assertRaises(PermissionError):
            atomic_write_text(symlink_target, "MALICIOUS_OVERWRITE", mode=0o600)

        # Real file was not overwritten
        self.assertEqual(real_file.read_text(encoding="utf-8"), "INITIAL_CONTENT")

    def test_atomic_write_warns_on_dir_fsync_oserror(self):
        """WARN-3: Directory fsync failures surface via RuntimeWarning."""
        import warnings
        target = self.dir_path / "warn_fsync.txt"
        orig_open = os.open

        def failing_open(path, flags, *args):
            if flags & getattr(os, "O_DIRECTORY", 0):
                raise OSError("Simulated mount without dir fsync support")
            return orig_open(path, flags, *args)

        os.open = failing_open
        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                atomic_write_text(target, "content_with_warning")
                self.assertTrue(target.exists())
                self.assertTrue(any(issubclass(item.category, RuntimeWarning) for item in w))
                self.assertTrue(any("crash durability not guaranteed" in str(item.message) for item in w))
        finally:
            os.open = orig_open

if __name__ == "__main__":
    unittest.main()
