"""Write sensitive exports without following repository-controlled symlinks.

POSIX uses pinned directory descriptors for traversal and atomic replacement.
The portable fallback rejects existing symlinks/reparse points and uses an
exclusive same-directory temporary file. On platforms without descriptor-
relative operations, the output directory must not be concurrently renamed or
replaced by another process; use a private export directory in that case.
"""

from __future__ import annotations

import errno
import os
import secrets
import stat
import sys
import tempfile
from contextlib import contextmanager, suppress
from pathlib import Path


def _absolute_output(path: Path) -> Path:
    # Resolve lexical dot segments without following any user-controlled links.
    absolute = Path(os.path.abspath(path))  # noqa: PTH100
    # Standard macOS filesystem aliases are OS-owned, not links supplied by
    # an analysed checkout. Preserve /tmp and tempfile/pytest paths there.
    if sys.platform == "darwin":
        for alias in ("/var", "/tmp", "/etc"):  # nosec B108
            source = Path(alias)
            expected = Path("/private") / source.name
            if absolute.is_relative_to(source) and source.resolve() == expected:
                return expected / absolute.relative_to(source)
    return absolute


def _is_link(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def _check_destination(info: os.stat_result | None, path: Path) -> None:
    if info is not None and (_is_link(info) or not stat.S_ISREG(info.st_mode)):
        raise OSError(errno.ELOOP, "Export destination must be a regular file, not a link", str(path))


def _has_dir_fd() -> bool:
    return (
        hasattr(os, "O_NOFOLLOW")
        and hasattr(os, "O_DIRECTORY")
        and {os.open, os.mkdir, os.stat, os.unlink, os.rename} <= os.supports_dir_fd
    )


@contextmanager
def _parent_fd(path: Path, *, create_parents: bool):
    """Pin every parent component, rejecting links without check/open races."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open(path.anchor, flags)
    try:
        for part in path.parent.parts[1:]:
            try:
                child = os.open(part, flags, dir_fd=fd)
            except FileNotFoundError:
                if not create_parents:
                    raise
                # The following no-follow open still validates a raced mkdir.
                with suppress(FileExistsError):
                    os.mkdir(part, mode=0o700, dir_fd=fd)
                child = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        try:
            info = os.stat(path.name, dir_fd=fd, follow_symlinks=False)
        except FileNotFoundError:
            info = None
        _check_destination(info, path)
        yield fd
    finally:
        os.close(fd)


def _prepare_portable(path: Path, *, create_parents: bool) -> None:
    current = Path(path.anchor)
    for part in path.parent.parts[1:]:
        current /= part
        try:
            info = current.lstat()
        except FileNotFoundError:
            if not create_parents:
                raise
            with suppress(FileExistsError):
                current.mkdir(mode=0o700)
            info = current.lstat()
        if _is_link(info) or not stat.S_ISDIR(info.st_mode):
            raise OSError(errno.ELOOP, "Export parent must be a directory, not a link", str(current))
    try:
        info = path.lstat()
    except FileNotFoundError:
        info = None
    _check_destination(info, path)


def prepare_output_path(path: Path) -> None:
    """Create missing private parent directories and reject unsafe links."""
    absolute = _absolute_output(path)
    if _has_dir_fd():
        with _parent_fd(absolute, create_parents=True):
            pass
    else:
        _prepare_portable(absolute, create_parents=True)


def atomic_write_text(path: Path, text: str, *, create_parents: bool = False) -> None:
    """Atomically replace a regular file with a private UTF-8 export.

    Existing regular files are replaced (including hard links, without changing
    their other names). Symlinks, devices, and directories are rejected. A
    destination changed to a symlink after validation is replaced, never opened.
    """
    absolute = _absolute_output(path)
    if not _has_dir_fd():
        _prepare_portable(absolute, create_parents=create_parents)
        fd, name = tempfile.mkstemp(prefix=".stride-export-", dir=absolute.parent)
        temporary = Path(name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(text)
                stream.flush()
                os.fsync(stream.fileno())
            _prepare_portable(absolute, create_parents=False)
            temporary.replace(absolute)
        finally:
            temporary.unlink(missing_ok=True)
        return

    with _parent_fd(absolute, create_parents=create_parents) as parent:
        name = f".stride-export-{secrets.token_hex(16)}.tmp"
        fd = os.open(
            name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600, dir_fd=parent,
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(text)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, absolute.name, src_dir_fd=parent, dst_dir_fd=parent)
        finally:
            with suppress(FileNotFoundError):
                os.unlink(name, dir_fd=parent)
