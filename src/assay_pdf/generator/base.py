"""PDF/X-4 base scaffolding — minimal valid PDF/X-4 page that all generators start from.

The base PDF is built in two stages:
1. ``reportlab`` lays out a page (vector primitives, text, optional CMYK colors).
2. ``pikepdf`` injects PDF/X-4 conformance: /OutputIntents, /Trapped, version 1.6,
   XMP metadata stating PDF/X-4 conformance.

Generators consume ``build_base_pdfx4`` and then mutate further (e.g. inject overprint,
add Courier text, bump image resolution, etc.) before calling ``stamp_deterministic``.

veraPDF compliance: the base PDF passes verapdf PDF/X-4 validation when the output
intent ICC is provided. With the v0.1.0 sRGB fallback, verapdf will flag the missing
expected ICC profile but the structural PDF/X-4 markers are correct.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pikepdf
from reportlab.lib.colors import CMYKColor  # type: ignore[import-untyped]
from reportlab.pdfgen import canvas  # type: ignore[import-untyped]

from assay_pdf.generator.variants import VariantConfig
from assay_pdf.logging import get_logger

log = get_logger(__name__)


def _icc_search_paths(repo_root: Path) -> list[Path]:
    """Where to look for ICC profiles, in priority order.

    Project-bundled paths first (deterministic across machines), then macOS
    ColorSync system paths as fallback. Linux/Windows users need
    ``uv run assay fetch icc`` to populate ``vendor/icc/``.
    """
    paths = [
        repo_root / "src" / "assay_pdf" / "generator" / "icc",
        repo_root / "vendor" / "icc",
    ]
    # macOS ColorSync — Adobe-installed profiles live under
    # /Library/ColorSync/Profiles/Recommended on most setups.
    for macos_path in (
        Path("/Library/ColorSync/Profiles/Recommended"),
        Path("/Library/ColorSync/Profiles"),
        Path("/System/Library/ColorSync/Profiles"),
    ):
        if macos_path.is_dir():
            paths.append(macos_path)
    return paths


# Family-level fallbacks: when the variant requests a profile with this name
# and we can't find it exactly, try these in order before falling back to
# the generic CMYK ICC. Captures the Adobe naming variations (CoatedFOGRA51 vs
# FOGRA51L_coated) that vary by installation.
# Family fallback chains. Filenames on the right come from Adobe's
# /Library/ColorSync/Profiles/Recommended (the "Adobe ICC Profiles" install).
# Order = preference: closest colorimetric substitute first, generic last.
_FAMILY_FALLBACKS: dict[str, list[str]] = {
    "FOGRA51L_coated.icc": [
        "CoatedFOGRA51.icc",  # Newer Adobe install (rare yet)
        "PSOcoated_v3.icc",  # ECI's FOGRA51 release name
        "CoatedFOGRA39.icc",  # Adobe — closest sheet-fed CMYK
        "ISOcoated_v2_300_eci.icc",  # ECI alt
        "USSheetfedCoated.icc",  # Adobe US sheet-fed alt
        "USWebCoatedSWOP.icc",  # Adobe US web alt
    ],
    "FOGRA39L_coated.icc": [
        "CoatedFOGRA39.icc",
        "ISOcoated_v2_300_eci.icc",
        "USWebCoatedSWOP.icc",
    ],
    "GRACoL2013_CRPC6.icc": [
        "GRACoL2013_CRPC6.icc",
        "CoatedGRACoL2006.icc",  # Adobe naming
        "GRACoL2006_Coated1v2.icc",  # Older Adobe naming
        "USWebCoatedSWOP.icc",  # GRACoL ≈ SWOP for fallback purposes
    ],
    "sRGB_IEC61966-2-1.icc": [
        "sRGB Profile.icc",
        "sRGB IEC61966-2.1.icc",
        "Generic RGB Profile.icc",
    ],
    "AdobeRGB1998.icc": [
        "AdobeRGB1998.icc",
        "Generic RGB Profile.icc",
    ],
}

# Last-resort generic CMYK profile — almost universally present on macOS.
_GENERIC_CMYK_FALLBACK = "Generic CMYK Profile.icc"


def find_icc(filename: str, repo_root: Path) -> tuple[Path, str] | None:
    """Locate an ICC profile.

    Returns ``(path, "exact" | "family" | "generic")`` describing how it was found,
    or ``None`` if no candidate exists anywhere.
    """
    search_paths = _icc_search_paths(repo_root)

    # 1) Exact match
    for d in search_paths:
        p = d / filename
        if p.is_file():
            return p, "exact"

    # 2) Family fallback
    for candidate in _FAMILY_FALLBACKS.get(filename, []):
        if candidate == filename:
            continue
        for d in search_paths:
            p = d / candidate
            if p.is_file():
                return p, "family"

    # 3) Generic CMYK as universal CMYK fallback
    for d in search_paths:
        p = d / _GENERIC_CMYK_FALLBACK
        if p.is_file():
            return p, "generic"

    return None


def build_base_pdfx4(
    output_path: Path,
    *,
    variant: VariantConfig,
    repo_root: Path,
    title: str = "AssayPDF base",
    page_text: str | None = None,
) -> Path:
    """Build a minimal PDF/X-4 PDF at output_path. Returns the path.

    The PDF has one page at ``variant.page_size_pts``. If ``page_text`` is provided,
    it's stamped in 12pt black text near top-left as a sanity marker. Generators
    typically pass the rule ID here so the file is human-identifiable.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    width, height = variant.page_size_pts

    # Stage 1: reportlab layout
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))
    c.setTitle(title)
    c.setProducer("assay-pdf base scaffold (reportlab)")
    c.setCreator("assay-pdf")
    if page_text:
        c.setFillColor(CMYKColor(0, 0, 0, 1))
        c.setFont("Helvetica", 12)
        c.drawString(36, height - 36, page_text)
    # TrimBox = MediaBox for the simplest valid case (R0003, R0004 satisfied).
    c.bookmarkPage("page1")
    c.showPage()
    c.save()
    buf.seek(0)

    # Stage 2: pikepdf injects PDF/X-4 conformance
    with pikepdf.open(buf) as pdf:
        # Set page boxes — MediaBox = TrimBox = CropBox (PDF/X-4 minimum)
        page = pdf.pages[0]
        media_box = pikepdf.Array([0, 0, width, height])
        page.MediaBox = media_box
        page.TrimBox = media_box
        page.CropBox = media_box
        if "/BleedBox" not in page:
            page.BleedBox = media_box

        # PDF version 1.6 minimum is enforced via save(min_version=...) below.

        # /Trapped — PDF/X requires explicit value (True or False, not Unknown)
        if "/Info" in pdf.trailer:
            pdf.trailer["/Info"]["/Trapped"] = pikepdf.Name("/False")

        # /OutputIntents — exact match preferred; falls back through family
        # variants then a generic macOS ColorSync CMYK profile if needed.
        match = find_icc(variant.output_intent_icc, repo_root)
        if match is None:
            log.warning(
                "No ICC profile usable for variant %s (wanted %s). "
                "Run `uv run assay fetch icc` to populate vendor/icc/.",
                variant.kebab,
                variant.output_intent_icc,
            )
            icc_stream_obj = None
        else:
            icc_path, match_kind = match
            if match_kind == "exact":
                log.debug("ICC %s: exact match at %s", variant.output_intent_icc, icc_path)
            elif match_kind == "family":
                log.info("ICC %s: family fallback %s", variant.output_intent_icc, icc_path.name)
            else:
                log.info(
                    "ICC %s: generic CMYK fallback %s — install Adobe RGB/CMYK profiles "
                    "or `uv run assay fetch icc` for variant-specific colorimetry.",
                    variant.output_intent_icc,
                    icc_path.name,
                )
            icc_bytes = icc_path.read_bytes()
            icc_stream_obj = pdf.make_stream(icc_bytes)
            icc_stream_obj["/N"] = 4  # All variant ICCs are CMYK in v0.1.0.

        oi_dict = pikepdf.Dictionary(
            {
                "/Type": pikepdf.Name("/OutputIntent"),
                "/S": pikepdf.Name("/GTS_PDFX"),
                "/OutputCondition": pikepdf.String(variant.output_condition),
                "/OutputConditionIdentifier": pikepdf.String(variant.output_condition),
                "/RegistryName": pikepdf.String("http://www.color.org"),
            }
        )
        if icc_stream_obj is not None:
            oi_dict["/DestOutputProfile"] = icc_stream_obj
        pdf.Root.OutputIntents = pikepdf.Array([oi_dict])

        # XMP metadata — declare PDF/X-4 conformance
        with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
            meta["pdfxid:GTS_PDFXVersion"] = "PDF/X-4"
            meta["pdfx:GTS_PDFXVersion"] = "PDF/X-4"
            meta["pdf:Trapped"] = "False"
            meta["dc:title"] = title

        pdf.save(
            output_path,
            min_version="1.6",
            object_stream_mode=pikepdf.ObjectStreamMode.preserve,
        )

    return output_path
