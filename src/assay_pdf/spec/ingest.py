"""`assay ingest` — parse spec/gwg-2022-spec.xlsx → spec/requirement-ids.json."""

from __future__ import annotations

from pathlib import Path

from assay_pdf.logging import get_logger
from assay_pdf.models import repo_root
from assay_pdf.spec.parser import parse_workbook

log = get_logger(__name__)


def ingest(
    xlsx_path: Path | None = None,
    output_path: Path | None = None,
) -> Path:
    """Parse the GWG 2022 workbook and write requirement-ids.json. Returns output path."""
    root = repo_root()
    xlsx = xlsx_path or root / "spec" / "gwg-2022-spec.xlsx"
    out = output_path or root / "spec" / "requirement-ids.json"

    manifest = parse_workbook(xlsx)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        manifest.model_dump_json(indent=2, exclude_none=False) + "\n",
        encoding="utf-8",
    )
    log.info(
        "Wrote %s (%d requirements, %d variants)",
        out,
        len(manifest.requirements),
        len(manifest.variants),
    )
    return out
