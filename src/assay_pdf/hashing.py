"""SHA-256 helpers — used by the fetcher (verify) and the generator (determinism check)."""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: Path | str, *, chunk_size: int = 1 << 20) -> str:
    """Return the lowercase-hex SHA-256 of a file, streaming via chunk reads."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Return the lowercase-hex SHA-256 of in-memory bytes."""
    return hashlib.sha256(data).hexdigest()
