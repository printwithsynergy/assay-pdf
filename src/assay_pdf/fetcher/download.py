"""`assay fetch` — download vendor assets with SHA-256 verification."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import httpx
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from assay_pdf.fetcher.manifest import (
    load_vendor_checksums,
    save_vendor_checksums,
    vendor_checksums_path,
)
from assay_pdf.hashing import sha256_file
from assay_pdf.logging import console, get_logger
from assay_pdf.models import VendorAsset, repo_root

log = get_logger(__name__)


def vendor_dir() -> Path:
    return repo_root() / "vendor"


def fetch_one(asset: VendorAsset, *, force: bool = False) -> tuple[Path, str, int]:
    """Download one vendor asset and return (path, sha256, size_bytes).

    If the file exists and its sha256 matches the manifest entry, skip download unless `force=True`.
    """
    target = vendor_dir() / asset.filename
    if not force and target.exists() and asset.sha256:
        actual = sha256_file(target)
        if actual == asset.sha256:
            log.info("[skip] %s — sha256 matches manifest", asset.filename)
            return target, actual, target.stat().st_size

    target.parent.mkdir(parents=True, exist_ok=True)
    log.info("Downloading %s from %s", asset.filename, asset.url)

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(asset.filename, total=None)
        with (
            httpx.stream("GET", asset.url, follow_redirects=True, timeout=60.0) as resp,
            target.open("wb") as f,
        ):
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0)) or None
            progress.update(task, total=total)
            for chunk in resp.iter_bytes(chunk_size=1 << 16):
                f.write(chunk)
                progress.advance(task, len(chunk))

    actual_sha = sha256_file(target)
    size = target.stat().st_size
    if asset.sha256 and actual_sha != asset.sha256:
        raise ValueError(
            f"Checksum mismatch for {asset.filename}: expected {asset.sha256}, got {actual_sha}"
        )
    return target, actual_sha, size


def fetch_all(*, force: bool = False) -> None:
    """Fetch every asset listed in vendor/checksums.json. Updates checksums on first run."""
    manifest = load_vendor_checksums()
    updated = False
    for asset in manifest.files:
        _path, sha, size = fetch_one(asset, force=force)
        if asset.sha256 != sha or asset.size_bytes != size:
            asset.sha256 = sha
            asset.size_bytes = size
            updated = True
            log.info("[checksum] %s = %s (%d bytes)", asset.filename, sha[:16] + "…", size)
    if updated:
        manifest.generated_at = datetime.now(UTC)
        save_vendor_checksums(manifest)
        log.info("Updated %s", vendor_checksums_path())
