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

def atomic_write_text(target: Path | str, data: str, encoding: str = "utf-8") -> None:
    """
    Atomically writes string data to target file.
    Creates temporary file in the same parent directory to guarantee atomic rename across POSIX mounts.
    Preserves original file permissions if file already exists.
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

        if target.exists():
            original_mode = target.stat().st_mode & 0o777
            os.chmod(tmp, original_mode)
        else:
            os.chmod(tmp, 0o644)

        os.replace(tmp, str(target))
    except BaseException:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass
        raise
