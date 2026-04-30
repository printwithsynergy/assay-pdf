"""Deterministic PDF metadata + ID overrides for byte-identical reproducibility.

PDFs include creation date, mod date, and a /ID array (a unique-per-document fingerprint).
By default these vary every time the PDF is built. We override all three to fixed values
derived from the deterministic seed so two runs of `assay generate` produce sha256-identical
output — the project's reproducibility guarantee.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pikepdf

if TYPE_CHECKING:
    from pathlib import Path

# Fixed reference timestamp for all generated PDFs.
# Why this date: 2026-01-01 is after AssayPDF's first commit, before any plausible
# ship date. Holding it constant is the whole point — never change.
FIXED_CREATION_DATE = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)


def _pdf_date_string(dt: datetime) -> str:
    """Format a datetime as a PDF date string per ISO 32000-2 §7.9.4.

    Example: D:20260101000000+00'00'
    """
    return dt.strftime("D:%Y%m%d%H%M%S+00'00'")


def fingerprint_id(rule_id: str, variant_kebab: str, seed: int) -> bytes:
    """Generate a 16-byte deterministic /ID value from rule + variant + seed."""
    payload = f"assay-pdf|{rule_id}|{variant_kebab}|{seed}".encode()
    return hashlib.sha256(payload).digest()[:16]


def stamp_deterministic(
    pdf_path: Path,
    *,
    rule_id: str,
    variant_kebab: str,
    seed: int = 0,
    title: str | None = None,
) -> None:
    """In-place mutate a PDF on disk to make it byte-deterministic.

    Sets:
    - /Info CreationDate, ModDate to FIXED_CREATION_DATE
    - /Info Producer to a fixed string
    - /ID trailer array to two copies of fingerprint_id(rule_id, variant_kebab, seed)
    """
    fp = fingerprint_id(rule_id, variant_kebab, seed)
    date_str = _pdf_date_string(FIXED_CREATION_DATE)

    with pikepdf.open(pdf_path, allow_overwriting_input=True) as pdf:
        # Force /Info dictionary to deterministic values
        with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
            meta["xmp:CreateDate"] = date_str
            meta["xmp:ModifyDate"] = date_str
            meta["xmp:CreatorTool"] = "assay-pdf"
            meta["pdf:Producer"] = "assay-pdf deterministic generator"
            if title is not None:
                meta["dc:title"] = title

        # pikepdf creates docinfo on first access if absent; no need to guard.
        pdf.docinfo["/CreationDate"] = pikepdf.String(date_str)
        pdf.docinfo["/ModDate"] = pikepdf.String(date_str)
        pdf.docinfo["/Producer"] = pikepdf.String("assay-pdf deterministic generator")
        if title is not None:
            pdf.docinfo["/Title"] = pikepdf.String(title)

        # Override /ID trailer
        pdf.trailer["/ID"] = pikepdf.Array([pikepdf.String(fp), pikepdf.String(fp)])

        pdf.save(
            pdf_path,
            deterministic_id=True,
            preserve_pdfa=True,
            object_stream_mode=pikepdf.ObjectStreamMode.preserve,
        )
