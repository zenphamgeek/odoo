#!/usr/bin/env python3
"""
tools/atomic_io.py
Production-grade POSIX atomic file writing utility.

Guarantees:
1. Atomic replacement on the same filesystem (os.replace).
2. fsync flushing before inode update.
3. Preservation of original file mode and permissions (prevents mkstemp 0600 web-unreadable defect).
4. Explicit mode enforcement (e.g. 0o600 for sensitive HMAC trust anchors).
5. CWE-59 defense: refuses symlink redirection on sensitive targets.
6. Recursive parent directory creation with secure permissions (0o700 for sensitive targets).
7. Crash durability: directory fsync with diagnostic warning on unsupported mounts.
8. Exception-safe temporary file cleanup.
"""

import logging
import os
import tempfile
import warnings
from pathlib import Path

logger = logging.getLogger("atomic_io")

def atomic_write_text(
    target: Path | str,
    data: str,
    encoding: str = "utf-8",
    mode: int | None = None,
    allow_untrusted_parent: bool = False,
) -> None:
    """
    Atomically writes string data to target file.
    Creates temporary file in the same parent directory to guarantee atomic rename across POSIX mounts.
    Preserves original file permissions if file already exists, or applies explicit mode (e.g. 0o600 for sensitive anchors).
    Flushes and fsyncs both the file descriptor and the parent directory for crash durability.
    """
    raw_target = Path(target)
    parent_dir = raw_target.parent.resolve()
    target = parent_dir / raw_target.name

    # CWE-59: Refuse symlink redirection on sensitive targets (check raw path and resolved target component)
    if mode is not None and (raw_target.is_symlink() or os.path.islink(target) or target.is_symlink()):
        raise PermissionError(f"Refusing to write sensitive file through symlink: {target}")

    # Guarantee parent chain exists; enforce 0o700 if target is sensitive
    dir_mode = 0o700 if (mode is not None and mode <= 0o600) else 0o755
    parent_dir.mkdir(parents=True, exist_ok=True, mode=dir_mode)

    # If target is sensitive, verify parent directory permissions on held descriptor (CWE-367 TOCTOU closed)
    if mode is not None and mode <= 0o600:
        dfd = os.open(str(parent_dir), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0))
        try:
            st = os.fstat(dfd)
            if st.st_uid == os.getuid():
                if st.st_mode & 0o077:
                    os.fchmod(dfd, st.st_mode & ~0o077)
            elif (st.st_mode & 0o077) and not allow_untrusted_parent:
                raise PermissionError(
                    f"Refusing to write sensitive file into non-owned, group/other-accessible directory {parent_dir} "
                    f"(dir_mode={st.st_mode & 0o777:o}, dir_uid={st.st_uid}, uid={os.getuid()}). "
                    f"Pass allow_untrusted_parent=True to override."
                )
            elif st.st_mode & 0o077:
                logger.warning(
                    "Writing sensitive file into non-owned loose directory %s (mode=%o, dir_uid=%s, uid=%s) under explicit override.",
                    parent_dir,
                    st.st_mode & 0o777,
                    st.st_uid,
                    os.getuid(),
                )
        finally:
            os.close(dfd)

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

        # Crash Durability: fsync parent directory to flush directory entry update
        try:
            dir_fd = os.open(str(parent_dir), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError as err:
            logger.warning("Directory fsync failed for %s: %s; crash durability not guaranteed", parent_dir, err)
            warnings.warn(
                f"directory fsync failed for {parent_dir}; crash durability not guaranteed",
                RuntimeWarning,
                stacklevel=2,
            )
    except BaseException:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass
        raise
