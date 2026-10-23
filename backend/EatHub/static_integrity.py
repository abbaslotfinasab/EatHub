"""Deterministic integrity manifests for collected Django static files.

This module intentionally uses only the Python standard library so it can run
inside the backend image without loading Django settings or contacting services.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
from pathlib import Path

ALGORITHM = "eathub-static-manifest-v1"
CHUNK_SIZE = 1024 * 1024


class StaticIntegrityError(ValueError):
    """Raised when the static tree cannot be safely and completely measured."""


def _validate_relative_path(path: str) -> bytes:
    if not path or "\\" in path or any(ord(char) < 32 or ord(char) == 127 for char in path):
        raise StaticIntegrityError("unsafe static relative path")
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts) or path.startswith("/"):
        raise StaticIntegrityError("unsafe static relative path")
    try:
        return path.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise StaticIntegrityError("static path is not valid UTF-8") from exc


def _hash_file(path: Path, expected_stat: os.stat_result) -> tuple[str, int]:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise StaticIntegrityError(f"cannot safely open static file: {path.name}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise StaticIntegrityError("static tree contains a non-regular file")
        if (before.st_dev, before.st_ino) != (expected_stat.st_dev, expected_stat.st_ino):
            raise StaticIntegrityError("static file changed while being enumerated")
        digest = hashlib.sha256()
        size = 0
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            while chunk := stream.read(CHUNK_SIZE):
                digest.update(chunk)
                size += len(chunk)
        after = os.fstat(descriptor)
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ) or size != after.st_size:
            raise StaticIntegrityError("static file changed while being hashed")
        return digest.hexdigest(), size
    finally:
        os.close(descriptor)


def build_manifest(root: str | os.PathLike[str]) -> dict[str, object]:
    """Return a canonical manifest summary for a non-empty static tree."""
    root_path = Path(root)
    try:
        root_stat = root_path.lstat()
    except OSError as exc:
        raise StaticIntegrityError("static root is unavailable") from exc
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        raise StaticIntegrityError("static root must be a real directory")

    entries: list[tuple[bytes, dict[str, object]]] = []

    def raise_walk_error(error: OSError) -> None:
        raise StaticIntegrityError("cannot enumerate static tree") from error

    try:
        for current, directories, filenames in os.walk(
            root_path, followlinks=False, onerror=raise_walk_error
        ):
            current_path = Path(current)
            for name in directories:
                child = current_path / name
                if stat.S_ISLNK(child.lstat().st_mode):
                    raise StaticIntegrityError("static tree contains a symbolic link")
            for name in filenames:
                file_path = current_path / name
                relative = file_path.relative_to(root_path).as_posix()
                sort_key = _validate_relative_path(relative)
                file_stat = file_path.lstat()
                if stat.S_ISLNK(file_stat.st_mode) or not stat.S_ISREG(file_stat.st_mode):
                    raise StaticIntegrityError("static tree contains a non-regular file")
                file_digest, size = _hash_file(file_path, file_stat)
                entries.append(
                    (
                        sort_key,
                        {"path": relative, "size": size, "sha256": file_digest},
                    )
                )
    except OSError as exc:
        raise StaticIntegrityError("cannot enumerate static tree") from exc

    if not entries:
        raise StaticIntegrityError("static tree contains no files")
    entries.sort(key=lambda item: item[0])
    files = [entry for _, entry in entries]
    canonical = json.dumps(
        {"algorithm": ALGORITHM, "files": files},
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return {
        "algorithm": ALGORITHM,
        "files": len(files),
        "bytes": sum(int(entry["size"]) for entry in files),
        "sha256": hashlib.sha256(canonical).hexdigest(),
    }


def format_summary(manifest: dict[str, object]) -> str:
    return "\n".join(
        (
            f"algorithm={manifest['algorithm']}",
            f"files={manifest['files']}",
            f"bytes={manifest['bytes']}",
            f"sha256={manifest['sha256']}",
        )
    )


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: static_integrity.py <static-root>", file=sys.stderr)
        return 2
    try:
        summary = format_summary(build_manifest(args[0]))
    except StaticIntegrityError as exc:
        print(f"static integrity verification failed: {exc}", file=sys.stderr)
        return 1
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
