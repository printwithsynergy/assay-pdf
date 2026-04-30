#!/usr/bin/env python3
"""Pre-commit hook: verify corpus/manifest.json files array stays sorted by path."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    manifest_path = repo_root / "corpus" / "manifest.json"
    if not manifest_path.exists():
        return 0

    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    paths = [f["path"] for f in raw.get("files", [])]
    sorted_paths = sorted(paths)

    if paths != sorted_paths:
        print("corpus/manifest.json files[] is not sorted by path.")
        print("Run `uv run assay generate` to regenerate it sorted.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
