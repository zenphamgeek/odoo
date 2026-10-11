#!/usr/bin/env python3
"""
tools/atomic_io.py
Production-grade POSIX atomic file writing utility.

Guarantees:
1. Atomic replacement on the same filesystem (os.replace).
2. fsync flushing before inode update.
3. Preservation of original file mode and permissions (prevents mkstemp 0600 web-unreadable defect).
4. Exception-safe temporary file cleanup.
"""

import os
import tempfile
from pathlib import Path

def atomic_write_text(target: Path | str, data: str, encoding: str = "utf-8", mode: int | None = None) -> None:
    """
    Atomically writes string data to target file.
    Creates temporary file in the same parent directory to guarantee atomic rename across POSIX mounts.
    Preserves original file permissions if file already exists, or applies explicit mode (e.g. 0o600 for sensitive anchors).
    Flushes and fsyncs both the file descriptor and the parent directory for crash durability.
    """
    target = Path(target).resolve()
    parent_dir = target.parent
    parent_dir.mkdir(parents=True, exist_ok=True)

    fd, tmp = tempfile.mkstemp(dir=str(parent_dir), prefix=f".{target.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())

        if mode is not None:
            os.chmod(tmp, mode)
        elif target.exists():
            original_mode = target.stat().st_mode & 0o777
            os.chmod(tmp, original_mode)
        else:
            os.chmod(tmp, 0o644)

        os.replace(tmp, str(target))

        # Durability: fsync parent directory to flush directory entry update (Finding 1)
        try:
            dir_fd = os.open(str(parent_dir), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError:
            pass
    except BaseException:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass
        raise
