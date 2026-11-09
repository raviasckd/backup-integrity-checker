"""Generate and verify SHA-256 manifests for backup directories."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path, PurePosixPath
import re
from typing import Any

_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


def _digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def _inventory(root: Path) -> dict[str, dict[str, Any]]:
    if not root.is_dir():
        raise NotADirectoryError(f"not a directory: {root}")

    entries: dict[str, dict[str, Any]] = {}
    for current, directories, filenames in os.walk(root, followlinks=False):
        base = Path(current)
        directories[:] = sorted(name for name in directories if not (base / name).is_symlink())
        for filename in sorted(filenames):
            path = base / filename
            if path.is_symlink() or not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            entries[relative] = {"sha256": _digest(path), "size": path.stat().st_size}
    return dict(sorted(entries.items()))


def create_manifest(root: str | Path) -> dict[str, Any]:
    """Return a versioned file inventory; file contents are never stored."""
    return {"format_version": 1, "algorithm": "sha256", "files": _inventory(Path(root))}


def _safe_manifest_path(root: Path, relative: str) -> Path:
    parsed = PurePosixPath(relative)
    if parsed.is_absolute() or not parsed.parts or ".." in parsed.parts:
        raise ValueError(f"unsafe path in manifest: {relative!r}")

    candidate = root.joinpath(*parsed.parts)
    resolved_root = root.resolve()
    resolved_candidate = candidate.resolve(strict=False)
    if resolved_candidate != resolved_root and resolved_root not in resolved_candidate.parents:
        raise ValueError(f"manifest path escapes backup root: {relative!r}")

    cursor = root
    for part in parsed.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(f"symbolic link in manifest path: {relative!r}")
    return candidate


def verify_manifest(root: str | Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Compare a backup tree with a manifest and classify integrity differences."""
    if manifest.get("format_version") != 1 or manifest.get("algorithm") != "sha256":
        raise ValueError("unsupported manifest format or hash algorithm")
    expected = manifest.get("files")
    if not isinstance(expected, dict):
        raise ValueError("manifest files must be an object")

    directory = Path(root)
    actual = _inventory(directory)
    missing: list[str] = []
    changed: list[str] = []
    for relative, metadata in expected.items():
        if not isinstance(relative, str) or not isinstance(metadata, dict):
            raise ValueError("invalid file entry in manifest")
        _safe_manifest_path(directory, relative)
        expected_hash = metadata.get("sha256")
        if not isinstance(expected_hash, str) or not _HASH_RE.fullmatch(expected_hash):
            raise ValueError(f"invalid SHA-256 value for {relative!r}")
        if relative not in actual:
            missing.append(relative)
        elif actual[relative]["sha256"] != expected_hash:
            changed.append(relative)

    missing.sort()
    changed.sort()
    unexpected = sorted(set(actual) - set(expected))
    return {
        "verified": not (missing or changed or unexpected),
        "missing": missing,
        "changed": changed,
        "unexpected": unexpected,
        "checked": len(expected),
    }
