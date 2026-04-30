"""Read/write vendor/checksums.json."""

from __future__ import annotations

from pathlib import Path

from assay_pdf.models import VendorChecksums, repo_root


def vendor_checksums_path() -> Path:
    return repo_root() / "vendor" / "checksums.json"


def load_vendor_checksums(path: Path | None = None) -> VendorChecksums:
    p = path or vendor_checksums_path()
    return VendorChecksums.model_validate_json(p.read_text(encoding="utf-8"))


def save_vendor_checksums(manifest: VendorChecksums, path: Path | None = None) -> Path:
    p = path or vendor_checksums_path()
    p.write_text(manifest.model_dump_json(indent=2, by_alias=True) + "\n", encoding="utf-8")
    return p
