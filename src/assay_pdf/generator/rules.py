"""GWG 2022 rule generators — one negative per rule.

Convention:
- ``gen_positive_baseline`` produces the per-variant positive (passes everything).
- ``gen_rNNNN_<slug>`` each target ONE rule's failure mode cleanly.
- Every generator returns a ``ManifestEntry``.

v0.1.0 coverage:
- Concrete generators: R0001-R0008, R0014, R0015, R0020, R0024, R0025, R0026, R0027,
  R0031, R0032, R0034, R0035, R0037, R1001
- Scoped stubs (require complex transparency / spot DeviceN / multi-page setup; tracked
  for v0.1.1): R0009-R0013, R0016-R0019, R0021-R0023, R0028, R0029, R0030, R0033, R0036, R1002

Stubs produce a structurally valid PDF/X-4 (so the corpus is internally consistent and
verapdf-clean), tagged with ``primary_rule_id`` and a description noting "stub for v0.1.1".
The manifest lists them as expected to fail — they just don't yet contain the actual
violation. Engines won't flag them, which we score as a known coverage gap, not as a
false negative against the engine.
"""

from __future__ import annotations

import platform
from pathlib import Path

import pikepdf

from assay_pdf.generator.base import build_base_pdfx4
from assay_pdf.generator.determinism import stamp_deterministic
from assay_pdf.generator.injectors import (
    add_extgstate,
    add_font_resource,
    append_content_stream,
    cmyk_fill_op,
)
from assay_pdf.generator.registry import register
from assay_pdf.generator.variants import VariantConfig
from assay_pdf.hashing import sha256_file
from assay_pdf.models import ManifestEntry, Severity

# ─── Helpers ──────────────────────────────────────────────────────────────────


def _build_entry(
    *,
    output_path: Path,
    repo_root: Path,
    category: str,
    primary_rule_id: str | None,
    variant: VariantConfig,
    description: str,
    generator_function: str,
    seed: int,
    expected_severity: dict[str, Severity] | None = None,
) -> ManifestEntry:
    return ManifestEntry(
        path=str(output_path.relative_to(repo_root)),
        category=category,
        primary_rule_id=primary_rule_id,
        applicable_variants=[variant.name],
        expected_severity=expected_severity or ({variant.name: Severity.error} if primary_rule_id else {}),
        description=description,
        generator_function=generator_function,
        deterministic_inputs={"seed": seed, "variant": variant.kebab},
        sha256=sha256_file(output_path),
        arch_generated_on=platform.machine(),
    )


def _stub_negative(
    *,
    rule_id: str,
    description: str,
    variant: VariantConfig,
    output_path: Path,
    repo_root: Path,
    seed: int,
) -> ManifestEntry:
    """Build a structurally-valid PDF/X-4 placeholder for rules deferred to v0.1.1.

    The PDF is tagged in /Info with the rule ID so anyone inspecting it knows it's a
    stub; the manifest entry's description makes the gap explicit.
    """
    title = f"AssayPDF {rule_id} stub — full violation injection lands in v0.1.1"
    build_base_pdfx4(
        output_path,
        variant=variant,
        repo_root=repo_root,
        title=title,
        page_text=f"{rule_id} STUB | {variant.name}",
    )
    stamp_deterministic(output_path, rule_id=rule_id, variant_kebab=variant.kebab, seed=seed, title=title)
    return _build_entry(
        output_path=output_path,
        repo_root=repo_root,
        category="negative",
        primary_rule_id=rule_id,
        variant=variant,
        description=f"[v0.1.1 STUB] {description} — no actual rule violation injected; engines will not flag.",
        generator_function=f"assay_pdf.generator.rules._stub_negative({rule_id})",
        seed=seed,
    )


# ─── Positive baseline ────────────────────────────────────────────────────────


@register("BASELINE", kind="positive")
def gen_positive_baseline(
    *,
    variant: VariantConfig,
    output_path: Path,
    repo_root: Path,
    seed: int = 0,
) -> ManifestEntry:
    """One per variant — minimal PDF/X-4 that passes every applicable GWG 2022 rule."""
    title = f"AssayPDF {variant.kebab} positive baseline"
    build_base_pdfx4(
        output_path,
        variant=variant,
        repo_root=repo_root,
        title=title,
        page_text=f"AssayPDF positive baseline | {variant.name}",
    )
    stamp_deterministic(output_path, rule_id="BASELINE", variant_kebab=variant.kebab, seed=seed, title=title)
    return _build_entry(
        output_path=output_path,
        repo_root=repo_root,
        category="positive",
        primary_rule_id=None,
        variant=variant,
        description=f"Minimal PDF/X-4 baseline for variant {variant.name!r} — should pass every rule.",
        generator_function="assay_pdf.generator.rules.gen_positive_baseline",
        seed=seed,
    )


# ─── R0001: Base ISO standards (PDF/X-4 required) ────────────────────────────


@register("R0001")
def gen_r0001_not_pdfx4(
    *, variant: VariantConfig, output_path: Path, repo_root: Path, seed: int = 0
) -> ManifestEntry:
    """R0001: produce a PDF that lacks PDF/X-4 conformance markers entirely."""
    title = "AssayPDF R0001 negative — not PDF/X-4 conformant"
    build_base_pdfx4(output_path, variant=variant, repo_root=repo_root, title=title)
    # Strip the PDF/X markers
    with pikepdf.open(output_path, allow_overwriting_input=True) as pdf:
        if "/OutputIntents" in pdf.Root:
            del pdf.Root["/OutputIntents"]
        with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
            for k in list(meta.keys()):
                if "PDFXVersion" in k:
                    del meta[k]
        pdf.save(output_path, object_stream_mode=pikepdf.ObjectStreamMode.preserve)
    stamp_deterministic(output_path, rule_id="R0001", variant_kebab=variant.kebab, seed=seed, title=title)
    return _build_entry(
        output_path=output_path, repo_root=repo_root, category="negative", primary_rule_id="R0001",
        variant=variant, description="PDF lacks /OutputIntents and PDF/X-4 XMP — not conformant to ISO 15930-7.",
        generator_function="assay_pdf.generator.rules.gen_r0001_not_pdfx4", seed=seed,
    )


# ─── R0002: UserUnit ──────────────────────────────────────────────────────────


@register("R0002")
def gen_r0002_user_unit(
    *, variant: VariantConfig, output_path: Path, repo_root: Path, seed: int = 0
) -> ManifestEntry:
    """R0002: page dictionary contains a UserUnit key."""
    title = "AssayPDF R0002 negative — UserUnit set"
    build_base_pdfx4(output_path, variant=variant, repo_root=repo_root, title=title)
    with pikepdf.open(output_path, allow_overwriting_input=True) as pdf:
        pdf.pages[0]["/UserUnit"] = 2.0
        pdf.save(output_path, object_stream_mode=pikepdf.ObjectStreamMode.preserve)
    stamp_deterministic(output_path, rule_id="R0002", variant_kebab=variant.kebab, seed=seed, title=title)
    return _build_entry(
        output_path=output_path, repo_root=repo_root, category="negative", primary_rule_id="R0002",
        variant=variant, description="Page dictionary has /UserUnit 2.0 — forbidden by R0002.",
        generator_function="assay_pdf.generator.rules.gen_r0002_user_unit", seed=seed,
    )


# ─── R0003: CropBox != MediaBox ───────────────────────────────────────────────


@register("R0003")
def gen_r0003_cropbox_mismatch(
    *, variant: VariantConfig, output_path: Path, repo_root: Path, seed: int = 0
) -> ManifestEntry:
    """R0003: CropBox does not coincide with MediaBox."""
    title = "AssayPDF R0003 negative — CropBox smaller than MediaBox"
    build_base_pdfx4(output_path, variant=variant, repo_root=repo_root, title=title)
    with pikepdf.open(output_path, allow_overwriting_input=True) as pdf:
        page = pdf.pages[0]
        mb = page.MediaBox
        # Inset CropBox by 18pt all sides — clearly different
        page.CropBox = pikepdf.Array([
            float(mb[0]) + 18, float(mb[1]) + 18,
            float(mb[2]) - 18, float(mb[3]) - 18,
        ])
        pdf.save(output_path, object_stream_mode=pikepdf.ObjectStreamMode.preserve)
    stamp_deterministic(output_path, rule_id="R0003", variant_kebab=variant.kebab, seed=seed, title=title)
    return _build_entry(
        output_path=output_path, repo_root=repo_root, category="negative", primary_rule_id="R0003",
        variant=variant, description="CropBox inset 18pt from MediaBox — violates R0003.",
        generator_function="assay_pdf.generator.rules.gen_r0003_cropbox_mismatch", seed=seed,
    )


# ─── R0004: TrimBox missing or rotated ────────────────────────────────────────


@register("R0004")
def gen_r0004_no_trimbox(
    *, variant: VariantConfig, output_path: Path, repo_root: Path, seed: int = 0
) -> ManifestEntry:
    """R0004: TrimBox missing AND page is rotated."""
    title = "AssayPDF R0004 negative — TrimBox missing + Rotate 90"
    build_base_pdfx4(output_path, variant=variant, repo_root=repo_root, title=title)
    with pikepdf.open(output_path, allow_overwriting_input=True) as pdf:
        page = pdf.pages[0]
        if "/TrimBox" in page:
            del page.TrimBox
        page.Rotate = 90
        pdf.save(output_path, object_stream_mode=pikepdf.ObjectStreamMode.preserve)
    stamp_deterministic(output_path, rule_id="R0004", variant_kebab=variant.kebab, seed=seed, title=title)
    return _build_entry(
        output_path=output_path, repo_root=repo_root, category="negative", primary_rule_id="R0004",
        variant=variant, description="TrimBox absent and /Rotate 90 — violates R0004 on two counts.",
        generator_function="assay_pdf.generator.rules.gen_r0004_no_trimbox", seed=seed,
    )


# ─── R0005: Empty page ────────────────────────────────────────────────────────


@register("R0005")
def gen_r0005_empty_page(
    *, variant: VariantConfig, output_path: Path, repo_root: Path, seed: int = 0
) -> ManifestEntry:
    """R0005: Page with TAC=0 (truly empty, no marks)."""
    title = "AssayPDF R0005 negative — empty page (TAC = 0)"
    # Build base WITHOUT page_text so reportlab produces no marks
    build_base_pdfx4(output_path, variant=variant, repo_root=repo_root, title=title, page_text=None)
    stamp_deterministic(output_path, rule_id="R0005", variant_kebab=variant.kebab, seed=seed, title=title)
    return _build_entry(
        output_path=output_path, repo_root=repo_root, category="negative", primary_rule_id="R0005",
        variant=variant, description="Page contains no marking operators — Total Ink Coverage = 0.",
        generator_function="assay_pdf.generator.rules.gen_r0005_empty_page", seed=seed,
    )


# ─── R0006: Single page ───────────────────────────────────────────────────────


@register("R0006")
def gen_r0006_two_pages(
    *, variant: VariantConfig, output_path: Path, repo_root: Path, seed: int = 0
) -> ManifestEntry:
    """R0006: PDF has more than one page."""
    title = "AssayPDF R0006 negative — 2-page PDF"
    build_base_pdfx4(output_path, variant=variant, repo_root=repo_root, title=title)
    with pikepdf.open(output_path, allow_overwriting_input=True) as pdf:
        # Duplicate page 1 within the same PDF
        pdf.pages.append(pdf.pages[0])
        pdf.save(output_path, object_stream_mode=pikepdf.ObjectStreamMode.preserve)
    stamp_deterministic(output_path, rule_id="R0006", variant_kebab=variant.kebab, seed=seed, title=title)
    return _build_entry(
        output_path=output_path, repo_root=repo_root, category="negative", primary_rule_id="R0006",
        variant=variant, description="PDF contains 2 pages — R0006 requires exactly 1.",
        generator_function="assay_pdf.generator.rules.gen_r0006_two_pages", seed=seed,
    )


# ─── R0007: White text overprint ─────────────────────────────────────────────


@register("R0007")
def gen_r0007_white_text_op(
    *, variant: VariantConfig, output_path: Path, repo_root: Path, seed: int = 0
) -> ManifestEntry:
    """R0007: white-filled text element with overprint enabled."""
    title = "AssayPDF R0007 negative — white text with /op true"
    build_base_pdfx4(output_path, variant=variant, repo_root=repo_root, title=title)
    with pikepdf.open(output_path, allow_overwriting_input=True) as pdf:
        page = pdf.pages[0]
        add_extgstate(page, name="GSwop", op_fill=True, opm=1)
        add_font_resource(page, name="HelvW", base_font="Helvetica")
        height = float(page.MediaBox[3])
        y = height - 96
        content = (
            b"q\n"
            b"/GSwop gs\n"
            + cmyk_fill_op(0, 0, 0, 0)  # white in CMYK
            + b"BT\n/HelvW 14 Tf\n"
            + f"36 {y:.2f} Td\n".encode()
            + b"(R0007: white text with overprint) Tj\nET\nQ\n"
        )
        append_content_stream(pdf, page, content)
        pdf.save(output_path, object_stream_mode=pikepdf.ObjectStreamMode.preserve)
    stamp_deterministic(output_path, rule_id="R0007", variant_kebab=variant.kebab, seed=seed, title=title)
    return _build_entry(
        output_path=output_path, repo_root=repo_root, category="negative", primary_rule_id="R0007",
        variant=variant, description="White-filled text element with ExtGState /op true — disappears on press.",
        generator_function="assay_pdf.generator.rules.gen_r0007_white_text_op", seed=seed,
    )


# ─── R0008: White path overprint ─────────────────────────────────────────────


@register("R0008")
def gen_r0008_white_path_op(
    *, variant: VariantConfig, output_path: Path, repo_root: Path, seed: int = 0
) -> ManifestEntry:
    """R0008: white-filled path element with overprint enabled."""
    title = "AssayPDF R0008 negative — white path with /op true"
    build_base_pdfx4(output_path, variant=variant, repo_root=repo_root, title=title)
    with pikepdf.open(output_path, allow_overwriting_input=True) as pdf:
        page = pdf.pages[0]
        add_extgstate(page, name="GSwop", op_fill=True, opm=1)
        content = (
            b"q\n"
            b"/GSwop gs\n"
            + cmyk_fill_op(0, 0, 0, 0)
            + b"100 200 200 100 re f\nQ\n"
        )
        append_content_stream(pdf, page, content)
        pdf.save(output_path, object_stream_mode=pikepdf.ObjectStreamMode.preserve)
    stamp_deterministic(output_path, rule_id="R0008", variant_kebab=variant.kebab, seed=seed, title=title)
    return _build_entry(
        output_path=output_path, repo_root=repo_root, category="negative", primary_rule_id="R0008",
        variant=variant, description="White-filled rectangle path with ExtGState /op true.",
        generator_function="assay_pdf.generator.rules.gen_r0008_white_path_op", seed=seed,
    )


# ─── R0014: Courier font ──────────────────────────────────────────────────────


@register("R0014")
def gen_r0014_courier_text(
    *, variant: VariantConfig, output_path: Path, repo_root: Path, seed: int = 0
) -> ManifestEntry:
    """R0014: text element using the Courier font."""
    title = "AssayPDF R0014 negative — Courier font present"
    build_base_pdfx4(output_path, variant=variant, repo_root=repo_root, title=title)
    with pikepdf.open(output_path, allow_overwriting_input=True) as pdf:
        page = pdf.pages[0]
        add_font_resource(page, name="Cour", base_font="Courier")
        height = float(page.MediaBox[3])
        y = height - 72
        content = (
            b"q\nBT\n/Cour 10 Tf\n"
            + f"36 {y:.2f} Td\n".encode()
            + b"(R0014: this text uses the forbidden Courier font) Tj\nET\nQ\n"
        )
        append_content_stream(pdf, page, content)
        pdf.save(output_path, object_stream_mode=pikepdf.ObjectStreamMode.preserve)
    stamp_deterministic(output_path, rule_id="R0014", variant_kebab=variant.kebab, seed=seed, title=title)
    return _build_entry(
        output_path=output_path, repo_root=repo_root, category="negative", primary_rule_id="R0014",
        variant=variant, description="Page contains a text element using the Courier font.",
        generator_function="assay_pdf.generator.rules.gen_r0014_courier_text", seed=seed,
    )


# ─── R0015: Rich black text ───────────────────────────────────────────────────


@register("R0015")
def gen_r0015_rich_black_text(
    *, variant: VariantConfig, output_path: Path, repo_root: Path, seed: int = 0
) -> ManifestEntry:
    """R0015: small text uses CMYK 100/100/100/100 (rich black) instead of /Black."""
    title = "AssayPDF R0015 negative — rich black text"
    build_base_pdfx4(output_path, variant=variant, repo_root=repo_root, title=title)
    with pikepdf.open(output_path, allow_overwriting_input=True) as pdf:
        page = pdf.pages[0]
        add_font_resource(page, name="HelvR", base_font="Helvetica")
        height = float(page.MediaBox[3])
        y = height - 120
        content = (
            b"q\n"
            + cmyk_fill_op(1.0, 1.0, 1.0, 1.0)  # 100/100/100/100 — rich black
            + b"BT\n/HelvR 7 Tf\n"
            + f"36 {y:.2f} Td\n".encode()
            + b"(R0015: 7pt CMYK 100/100/100/100 rich black text) Tj\nET\nQ\n"
        )
        append_content_stream(pdf, page, content)
        pdf.save(output_path, object_stream_mode=pikepdf.ObjectStreamMode.preserve)
    stamp_deterministic(output_path, rule_id="R0015", variant_kebab=variant.kebab, seed=seed, title=title)
    return _build_entry(
        output_path=output_path, repo_root=repo_root, category="negative", primary_rule_id="R0015",
        variant=variant, description="7pt text filled with CMYK 100/100/100/100 — should use single black ink.",
        generator_function="assay_pdf.generator.rules.gen_r0015_rich_black_text", seed=seed,
    )


# ─── R0020: Spot color count ─────────────────────────────────────────────────


@register("R0020")
def gen_r0020_too_many_spots(
    *, variant: VariantConfig, output_path: Path, repo_root: Path, seed: int = 0
) -> ManifestEntry:
    """R0020: PDF declares more spot colors than allowed by the variant."""
    title = "AssayPDF R0020 negative — excessive spot color count"
    build_base_pdfx4(output_path, variant=variant, repo_root=repo_root, title=title)
    # Reference 12 named spots in resources — most variants cap at 0-12 active spots
    with pikepdf.open(output_path, allow_overwriting_input=True) as pdf:
        page = pdf.pages[0]
        if "/Resources" not in page:
            page.Resources = pikepdf.Dictionary({})
        if "/ColorSpace" not in page.Resources:
            page.Resources["/ColorSpace"] = pikepdf.Dictionary({})
        for i in range(12):
            spot_name = f"PANTONE_{100 + i}_C"
            page.Resources["/ColorSpace"][f"/CS{i}"] = pikepdf.Array([
                pikepdf.Name("/Separation"),
                pikepdf.Name(f"/{spot_name}"),
                pikepdf.Name("/DeviceCMYK"),
                pikepdf.Dictionary({
                    "/FunctionType": 2,
                    "/Domain": pikepdf.Array([0.0, 1.0]),
                    "/C0": pikepdf.Array([0.0, 0.0, 0.0, 0.0]),
                    "/C1": pikepdf.Array([0.5, 0.5, 0.0, 0.0]),
                    "/N": 1.0,
                }),
            ])
        pdf.save(output_path, object_stream_mode=pikepdf.ObjectStreamMode.preserve)
    stamp_deterministic(output_path, rule_id="R0020", variant_kebab=variant.kebab, seed=seed, title=title)
    return _build_entry(
        output_path=output_path, repo_root=repo_root, category="negative", primary_rule_id="R0020",
        variant=variant, description="12 distinct PANTONE spot color separations declared as resources.",
        generator_function="assay_pdf.generator.rules.gen_r0020_too_many_spots", seed=seed,
    )


# ─── R0024: All-spot ──────────────────────────────────────────────────────────


@register("R0024")
def gen_r0024_all_spot(
    *, variant: VariantConfig, output_path: Path, repo_root: Path, seed: int = 0
) -> ManifestEntry:
    """R0024: page references the spot color named "All"."""
    title = 'AssayPDF R0024 negative — Spot Color "All" used'
    build_base_pdfx4(output_path, variant=variant, repo_root=repo_root, title=title)
    with pikepdf.open(output_path, allow_overwriting_input=True) as pdf:
        page = pdf.pages[0]
        if "/Resources" not in page:
            page.Resources = pikepdf.Dictionary({})
        if "/ColorSpace" not in page.Resources:
            page.Resources["/ColorSpace"] = pikepdf.Dictionary({})
        page.Resources["/ColorSpace"]["/AllSep"] = pikepdf.Array([
            pikepdf.Name("/Separation"),
            pikepdf.Name("/All"),
            pikepdf.Name("/DeviceCMYK"),
            pikepdf.Dictionary({
                "/FunctionType": 2, "/Domain": pikepdf.Array([0.0, 1.0]),
                "/C0": pikepdf.Array([0.0, 0.0, 0.0, 0.0]),
                "/C1": pikepdf.Array([1.0, 1.0, 1.0, 1.0]), "/N": 1.0,
            }),
        ])
        # Use it
        content = b"q\n/AllSep cs 1 sc\n100 100 100 100 re f\nQ\n"
        append_content_stream(pdf, page, content)
        pdf.save(output_path, object_stream_mode=pikepdf.ObjectStreamMode.preserve)
    stamp_deterministic(output_path, rule_id="R0024", variant_kebab=variant.kebab, seed=seed, title=title)
    return _build_entry(
        output_path=output_path, repo_root=repo_root, category="negative", primary_rule_id="R0024",
        variant=variant, description='Page uses /Separation /All — registration colour, forbidden in production.',
        generator_function="assay_pdf.generator.rules.gen_r0024_all_spot", seed=seed,
    )


# ─── R0025/R0026: TAC ─────────────────────────────────────────────────────────


@register("R0025")
def gen_r0025_tac_overflow(
    *, variant: VariantConfig, output_path: Path, repo_root: Path, seed: int = 0
) -> ManifestEntry:
    """R0025: large area painted with cmyk 90/90/90/90 = 360% TAC."""
    title = "AssayPDF R0025 negative — 360% all-separations TAC"
    build_base_pdfx4(output_path, variant=variant, repo_root=repo_root, title=title)
    with pikepdf.open(output_path, allow_overwriting_input=True) as pdf:
        page = pdf.pages[0]
        # Half-page rectangle at 90/90/90/90
        content = b"q\n" + cmyk_fill_op(0.9, 0.9, 0.9, 0.9) + b"100 200 400 400 re f\nQ\n"
        append_content_stream(pdf, page, content)
        pdf.save(output_path, object_stream_mode=pikepdf.ObjectStreamMode.preserve)
    stamp_deterministic(output_path, rule_id="R0025", variant_kebab=variant.kebab, seed=seed, title=title)
    return _build_entry(
        output_path=output_path, repo_root=repo_root, category="negative", primary_rule_id="R0025",
        variant=variant,
        description=f"Half-page rectangle at CMYK 90/90/90/90 = 360% TAC; variant ceiling = {variant.max_tac_all}%.",
        generator_function="assay_pdf.generator.rules.gen_r0025_tac_overflow", seed=seed,
    )


@register("R0026")
def gen_r0026_cmyk_tac_overflow(
    *, variant: VariantConfig, output_path: Path, repo_root: Path, seed: int = 0
) -> ManifestEntry:
    """R0026: same as R0025 — exceeds CMYK-only TAC ceiling."""
    title = "AssayPDF R0026 negative — 350% CMYK TAC"
    build_base_pdfx4(output_path, variant=variant, repo_root=repo_root, title=title)
    with pikepdf.open(output_path, allow_overwriting_input=True) as pdf:
        page = pdf.pages[0]
        content = b"q\n" + cmyk_fill_op(0.95, 0.85, 0.85, 0.85) + b"50 50 500 500 re f\nQ\n"
        append_content_stream(pdf, page, content)
        pdf.save(output_path, object_stream_mode=pikepdf.ObjectStreamMode.preserve)
    stamp_deterministic(output_path, rule_id="R0026", variant_kebab=variant.kebab, seed=seed, title=title)
    return _build_entry(
        output_path=output_path, repo_root=repo_root, category="negative", primary_rule_id="R0026",
        variant=variant,
        description=f"Large area at CMYK 95/85/85/85 = 350% > {variant.max_tac_cmyk}% (variant CMYK ceiling).",
        generator_function="assay_pdf.generator.rules.gen_r0026_cmyk_tac_overflow", seed=seed,
    )


# ─── R0027: Forbidden colour space (early binding) ────────────────────────────


@register("R0027")
def gen_r0027_devicergb(
    *, variant: VariantConfig, output_path: Path, repo_root: Path, seed: int = 0
) -> ManifestEntry:
    """R0027: page element uses DeviceRGB as fill color space."""
    title = "AssayPDF R0027 negative — DeviceRGB fill"
    build_base_pdfx4(output_path, variant=variant, repo_root=repo_root, title=title)
    with pikepdf.open(output_path, allow_overwriting_input=True) as pdf:
        page = pdf.pages[0]
        # /DeviceRGB rg uses RGB color
        content = b"q\n/DeviceRGB cs 0.8 0.2 0.2 sc\n200 300 200 100 re f\nQ\n"
        append_content_stream(pdf, page, content)
        pdf.save(output_path, object_stream_mode=pikepdf.ObjectStreamMode.preserve)
    stamp_deterministic(output_path, rule_id="R0027", variant_kebab=variant.kebab, seed=seed, title=title)
    return _build_entry(
        output_path=output_path, repo_root=repo_root, category="negative", primary_rule_id="R0027",
        variant=variant, description="Path filled with DeviceRGB color — forbidden by R0027 in early-binding mode.",
        generator_function="assay_pdf.generator.rules.gen_r0027_devicergb", seed=seed,
    )


# ─── R0031: Image resolution ──────────────────────────────────────────────────


@register("R0031")
def gen_r0031_low_res_color_image(
    *, variant: VariantConfig, output_path: Path, repo_root: Path, seed: int = 0
) -> ManifestEntry:
    """R0031: embed a tiny color image, then place it large — yields low effective ppi."""
    title = "AssayPDF R0031 negative — color image well below threshold"
    build_base_pdfx4(output_path, variant=variant, repo_root=repo_root, title=title)
    with pikepdf.open(output_path, allow_overwriting_input=True) as pdf:
        page = pdf.pages[0]
        # 50x50 device CMYK image, drawn as 400x400 page units → ~9 ppi effective
        # (well under the 224 ppi threshold for sheet variants)
        width_px, height_px = 50, 50
        # Solid magenta CMYK image: each pixel C=0 M=255 Y=0 K=0 (4 bytes/pixel)
        pixel_bytes = bytes([0, 255, 0, 0]) * (width_px * height_px)
        img_stream = pdf.make_stream(
            pixel_bytes,
            Type=pikepdf.Name("/XObject"),
            Subtype=pikepdf.Name("/Image"),
            Width=width_px,
            Height=height_px,
            BitsPerComponent=8,
            ColorSpace=pikepdf.Name("/DeviceCMYK"),
        )
        if "/Resources" not in page:
            page.Resources = pikepdf.Dictionary({})
        if "/XObject" not in page.Resources:
            page.Resources["/XObject"] = pikepdf.Dictionary({})
        page.Resources["/XObject"]["/Im0"] = img_stream
        # Draw the image scaled to 400x400 pts at (50, 50)
        content = b"q\n400 0 0 400 50 50 cm\n/Im0 Do\nQ\n"
        append_content_stream(pdf, page, content)
        pdf.save(output_path, object_stream_mode=pikepdf.ObjectStreamMode.preserve)
    stamp_deterministic(output_path, rule_id="R0031", variant_kebab=variant.kebab, seed=seed, title=title)
    return _build_entry(
        output_path=output_path, repo_root=repo_root, category="negative", primary_rule_id="R0031",
        variant=variant,
        description=f"50x50 DeviceCMYK image scaled to 400pt = ~9 ppi effective; threshold A = {variant.min_image_res_color} ppi.",
        generator_function="assay_pdf.generator.rules.gen_r0031_low_res_color_image", seed=seed,
    )


# ─── R0032: 1-bit image resolution ────────────────────────────────────────────


@register("R0032")
def gen_r0032_low_res_1bit(
    *, variant: VariantConfig, output_path: Path, repo_root: Path, seed: int = 0
) -> ManifestEntry:
    """R0032: low-res 1-bit (bitmap) image."""
    title = "AssayPDF R0032 negative — low-res 1-bit image"
    build_base_pdfx4(output_path, variant=variant, repo_root=repo_root, title=title)
    with pikepdf.open(output_path, allow_overwriting_input=True) as pdf:
        page = pdf.pages[0]
        # 100x100 1-bit image, drawn at 400x400 → 72 ppi vs ~1000 ppi requirement
        width_px, height_px = 100, 100
        # 1 bit per pixel, packed: 100/8 = 12.5 → 13 bytes/row, 100 rows = 1300 bytes
        row_bytes = (width_px + 7) // 8
        bitmap = b"\xaa" * (row_bytes * height_px)
        img_stream = pdf.make_stream(
            bitmap,
            Type=pikepdf.Name("/XObject"),
            Subtype=pikepdf.Name("/Image"),
            Width=width_px,
            Height=height_px,
            BitsPerComponent=1,
            ColorSpace=pikepdf.Name("/DeviceGray"),
        )
        if "/Resources" not in page:
            page.Resources = pikepdf.Dictionary({})
        if "/XObject" not in page.Resources:
            page.Resources["/XObject"] = pikepdf.Dictionary({})
        page.Resources["/XObject"]["/Im1bit"] = img_stream
        content = b"q\n400 0 0 400 50 350 cm\n/Im1bit Do\nQ\n"
        append_content_stream(pdf, page, content)
        pdf.save(output_path, object_stream_mode=pikepdf.ObjectStreamMode.preserve)
    stamp_deterministic(output_path, rule_id="R0032", variant_kebab=variant.kebab, seed=seed, title=title)
    return _build_entry(
        output_path=output_path, repo_root=repo_root, category="negative", primary_rule_id="R0032",
        variant=variant,
        description=f"100x100 1-bit image scaled to 400pt = 18 ppi; threshold A = {variant.min_image_res_1bit} ppi.",
        generator_function="assay_pdf.generator.rules.gen_r0032_low_res_1bit", seed=seed,
    )


# ─── R0034: Optional content (OCG) without proper Configs ─────────────────────


@register("R0034")
def gen_r0034_ocg_no_configs(
    *, variant: VariantConfig, output_path: Path, repo_root: Path, seed: int = 0
) -> ManifestEntry:
    """R0034: OCProperties present but malformed (missing /Configs array)."""
    title = "AssayPDF R0034 negative — OCProperties without Configs"
    build_base_pdfx4(output_path, variant=variant, repo_root=repo_root, title=title)
    with pikepdf.open(output_path, allow_overwriting_input=True) as pdf:
        ocg = pdf.make_indirect(pikepdf.Dictionary({
            "/Type": pikepdf.Name("/OCG"),
            "/Name": pikepdf.String("LayerA"),
        }))
        pdf.Root["/OCProperties"] = pikepdf.Dictionary({
            "/OCGs": pikepdf.Array([ocg]),
            "/D": pikepdf.Dictionary({
                "/Order": pikepdf.Array([ocg]),
                "/ON": pikepdf.Array([ocg]),
                "/OFF": pikepdf.Array([]),
            }),
            # Intentionally NO /Configs key
        })
        pdf.save(output_path, object_stream_mode=pikepdf.ObjectStreamMode.preserve)
    stamp_deterministic(output_path, rule_id="R0034", variant_kebab=variant.kebab, seed=seed, title=title)
    return _build_entry(
        output_path=output_path, repo_root=repo_root, category="negative", primary_rule_id="R0034",
        variant=variant, description="OCProperties present, /Configs array missing — violates R0034 structural requirement.",
        generator_function="assay_pdf.generator.rules.gen_r0034_ocg_no_configs", seed=seed,
    )


# ─── R0035: Wrong output intent colour space ──────────────────────────────────


@register("R0035")
def gen_r0035_rgb_output_intent(
    *, variant: VariantConfig, output_path: Path, repo_root: Path, seed: int = 0
) -> ManifestEntry:
    """R0035: PDF/X output intent uses RGB colour space instead of CMYK."""
    title = "AssayPDF R0035 negative — RGB output intent"
    build_base_pdfx4(output_path, variant=variant, repo_root=repo_root, title=title)
    with pikepdf.open(output_path, allow_overwriting_input=True) as pdf:
        # Synthesize a tiny "ICC" stream marked as 3-component (RGB) — verapdf will see /N 3
        fake_rgb_icc = pdf.make_stream(b"\x00" * 256)
        fake_rgb_icc["/N"] = 3
        oi = pikepdf.Dictionary({
            "/Type": pikepdf.Name("/OutputIntent"),
            "/S": pikepdf.Name("/GTS_PDFX"),
            "/OutputCondition": pikepdf.String("sRGB IEC61966-2.1"),
            "/OutputConditionIdentifier": pikepdf.String("sRGB IEC61966-2.1"),
            "/RegistryName": pikepdf.String("http://www.color.org"),
            "/DestOutputProfile": fake_rgb_icc,
        })
        pdf.Root["/OutputIntents"] = pikepdf.Array([oi])
        pdf.save(output_path, object_stream_mode=pikepdf.ObjectStreamMode.preserve)
    stamp_deterministic(output_path, rule_id="R0035", variant_kebab=variant.kebab, seed=seed, title=title)
    return _build_entry(
        output_path=output_path, repo_root=repo_root, category="negative", primary_rule_id="R0035",
        variant=variant, description="OutputIntent /DestOutputProfile has /N 3 (RGB) — R0035 requires CMYK (/N 4).",
        generator_function="assay_pdf.generator.rules.gen_r0035_rgb_output_intent", seed=seed,
    )


# ─── R0037: Sign/display scaling missing ──────────────────────────────────────


@register("R0037")
def gen_r0037_no_scaling(
    *, variant: VariantConfig, output_path: Path, repo_root: Path, seed: int = 0
) -> ManifestEntry:
    """R0037: sign/display variant requires Scaling Factor + Viewing Distance metadata."""
    title = "AssayPDF R0037 negative — Scaling Factor and Viewing Distance absent"
    # Just the baseline; the absence of the required XMP keys IS the violation
    build_base_pdfx4(output_path, variant=variant, repo_root=repo_root, title=title)
    stamp_deterministic(output_path, rule_id="R0037", variant_kebab=variant.kebab, seed=seed, title=title)
    return _build_entry(
        output_path=output_path, repo_root=repo_root, category="negative", primary_rule_id="R0037",
        variant=variant,
        description="No Scaling Factor (D0025) or Viewing Distance (D0026) metadata — required for sign/display.",
        generator_function="assay_pdf.generator.rules.gen_r0037_no_scaling", seed=seed,
    )


# ─── R1001: Missing processing steps ──────────────────────────────────────────


@register("R1001")
def gen_r1001_no_processing_steps(
    *, variant: VariantConfig, output_path: Path, repo_root: Path, seed: int = 0
) -> ManifestEntry:
    """R1001: packaging variant PDF without ISO 19593-1 Processing Steps OCG layers."""
    title = "AssayPDF R1001 negative — packaging without processing steps"
    build_base_pdfx4(output_path, variant=variant, repo_root=repo_root, title=title)
    stamp_deterministic(output_path, rule_id="R1001", variant_kebab=variant.kebab, seed=seed, title=title)
    return _build_entry(
        output_path=output_path, repo_root=repo_root, category="negative", primary_rule_id="R1001",
        variant=variant,
        description="Packaging-variant PDF lacks ISO 19593-1 Processing Steps layer (Cutting/Creasing/etc.).",
        generator_function="assay_pdf.generator.rules.gen_r1001_no_processing_steps", seed=seed,
    )


# ─── Stubs for v0.1.1 rules ───────────────────────────────────────────────────
# Each stub registers a generator that produces a tagged-but-clean PDF/X-4.
# The manifest description makes the gap explicit. Engines won't flag these,
# which the scorer treats as a known coverage gap, not as engine failure.


def _make_stub(rule_id: str, description: str):  # type: ignore[no-untyped-def]
    @register(rule_id)
    def _stub(
        *, variant: VariantConfig, output_path: Path, repo_root: Path, seed: int = 0
    ) -> ManifestEntry:
        return _stub_negative(
            rule_id=rule_id, description=description, variant=variant,
            output_path=output_path, repo_root=repo_root, seed=seed,
        )
    return _stub


_STUB_RULES: list[tuple[str, str]] = [
    ("R0009", "Pure black text overprint — needs ExtGState OPM modeling per variant"),
    ("R0010", "Pure black thin lines overprint"),
    ("R0011", "Pure black small text in DeviceGray — stroke overprint variant"),
    ("R0012", "Pure black thin lines in DeviceGray — stroke overprint variant"),
    ("R0013", "DeviceGray fill overprint"),
    ("R0016", "Registration-problems small white text (4.99pt threshold case)"),
    ("R0017", "Registration-problems small multi-channel text"),
    ("R0018", "Registration-problems thin white lines"),
    ("R0019", "Registration-problems thin multi-channel lines"),
    ("R0021", "Spot color suffix inconsistency (PANTONE 638 C vs Pantone 638 C)"),
    ("R0022", "Spot color case-sensitive collision"),
    ("R0023", "Visually identical spot colors"),
    ("R0028", "Intermediate-binding image with CalRGB"),
    ("R0029", "Late-binding image with Indexed-DeviceRGB"),
    ("R0030", "Transparency blend space with /CS DeviceRGB"),
    ("R0033", "Rasterized page (full-page raster)"),
    ("R0036", "Hidden OCG (intent=Hidden)"),
    ("R1002", "Folding carton without required Creasing layer"),
]
for _rid, _desc in _STUB_RULES:
    _make_stub(_rid, _desc)
