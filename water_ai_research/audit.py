"""Portable identities and duplicate checks; these are not semantic detectors."""

import hashlib
import json
import unicodedata
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_fingerprint(text: str) -> str:
    """NFC, Unicode casefold, and whitespace collapse; punctuation preserved."""
    normalized = " ".join(unicodedata.normalize("NFC", text).casefold().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def cross_split_duplicates(partitions: Mapping[str, Sequence[str]]) -> dict[str, list[str]]:
    """Return normalized hashes found in multiple splits (not raw text)."""
    found: dict[str, set[str]] = defaultdict(set)
    for split, texts in partitions.items():
        for text in texts:
            found[text_fingerprint(text)].add(split)
    return {key: sorted(splits) for key, splits in sorted(found.items()) if len(splits) > 1}


def build_manifest(root: str | Path, paths: Sequence[str]) -> list[dict]:
    """Hash an explicit file allowlist under root, using portable POSIX paths.

    Symlink escapes, duplicate names and directories are rejected. A manifest
    detects changed bytes; it does not authenticate an untrusted publisher.
    """
    root = Path(root).resolve()
    rows, seen = [], set()
    for name in sorted(paths):
        requested = Path(name)
        if requested.is_absolute() or ".." in requested.parts:
            raise ValueError("manifest paths must stay relative to root")
        path = (root / requested).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f"not a file inside root: {name}")
        relative = path.relative_to(root).as_posix()
        if relative in seen:
            raise ValueError(f"duplicate file: {name}")
        seen.add(relative)
        rows.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    return rows


def verify_manifest(root: str | Path, rows: Sequence[dict]) -> None:
    names = [row["path"] for row in rows]
    actual = build_manifest(root, names)
    expected = sorted(rows, key=lambda row: row["path"])
    if actual != expected:
        raise ValueError("manifest mismatch: file content, size or identity changed")


def write_json(path: str | Path, value: object) -> None:
    """Finite JSON, stable key order, UTF-8; round-trip binary64 floats."""
    Path(path).write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
