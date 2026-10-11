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

if __name__ == "__main__":
    unittest.main()
