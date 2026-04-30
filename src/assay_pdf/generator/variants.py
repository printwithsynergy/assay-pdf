"""Per-variant PDF/X-4 generation parameters.

Each VariantConfig defines what the generator must produce for a "passes everything"
positive PDF for that variant: page size, output intent ICC, max ink coverage, color
space mode (CMYK-only or CMYK+RGB), spot color allowance, etc.

Values are derived from the GWG 2022 spec workbook (Variants tab) and the explanation
PDF — committed here as the source of truth for the generator. If the spec workbook
changes, regenerate via `assay ingest` and update these defaults to match.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class VariantConfig:
    """One GWG 2022 variant's positive-PDF generation parameters."""

    name: str  # Spec literal, matches RequirementManifest.variants[].name
    kebab: str  # Filesystem-safe, matches RequirementManifest.variants[].kebab
    output_intent_icc: str  # ICC filename relative to icc-search-path
    output_condition: str  # /OutputCondition string for the PDF/X output intent
    rgb_allowed: bool  # Whether DeviceRGB is permitted (CMYK+RGB variants only)
    spots_allowed: bool  # Whether spot colors beyond DeviceCMYK are permitted
    max_tac_cmyk: int  # CMYK-only TAC ceiling (R0026 threshold A)
    max_tac_all: int  # All-separations TAC ceiling (R0025 threshold A)
    min_image_res_color: int  # ppi (R0031 warning threshold A)
    min_image_res_1bit: int  # ppi (R0032 warning threshold A)
    page_size_pts: tuple[float, float] = (595.276, 841.89)  # A4 default
    is_packaging: bool = False  # ISO 19593-1 Processing Steps required (R1001)
    notes: str = ""


VARIANTS: Final[list[VariantConfig]] = [
    VariantConfig(
        name="Magazine Ads CMYK",
        kebab="magazine-ads-cmyk",
        output_intent_icc="GRACoL2013_CRPC6.icc",
        output_condition="GRACoL2013 CRPC6",
        rgb_allowed=False,
        spots_allowed=False,
        max_tac_cmyk=300,
        max_tac_all=300,
        min_image_res_color=224,
        min_image_res_1bit=1000,
    ),
    VariantConfig(
        name="Magazine Ads CMYK + RGB",
        kebab="magazine-ads-cmyk-plus-rgb",
        output_intent_icc="GRACoL2013_CRPC6.icc",
        output_condition="GRACoL2013 CRPC6",
        rgb_allowed=True,
        spots_allowed=False,
        max_tac_cmyk=300,
        max_tac_all=300,
        min_image_res_color=224,
        min_image_res_1bit=1000,
    ),
    VariantConfig(
        name="Newspaper Ads CMYK",
        kebab="newspaper-ads-cmyk",
        output_intent_icc="FOGRA51L_coated.icc",  # Fallback — newsprint variants vary by region
        output_condition="WAN-IFRAnewspaper26v5",
        rgb_allowed=False,
        spots_allowed=False,
        max_tac_cmyk=240,
        max_tac_all=240,
        min_image_res_color=149,
        min_image_res_1bit=600,
    ),
    VariantConfig(
        name="Newspaper Ads CMYK + RGB",
        kebab="newspaper-ads-cmyk-plus-rgb",
        output_intent_icc="FOGRA51L_coated.icc",
        output_condition="WAN-IFRAnewspaper26v5",
        rgb_allowed=True,
        spots_allowed=False,
        max_tac_cmyk=240,
        max_tac_all=240,
        min_image_res_color=149,
        min_image_res_1bit=600,
    ),
    VariantConfig(
        name="SheetCMYK CMYK",
        kebab="sheetcmyk-cmyk",
        output_intent_icc="FOGRA51L_coated.icc",
        output_condition="FOGRA51L (PSO Coated v3)",
        rgb_allowed=False,
        spots_allowed=False,
        max_tac_cmyk=300,
        max_tac_all=300,
        min_image_res_color=224,
        min_image_res_1bit=1000,
    ),
    VariantConfig(
        name="SheetCMYK CMYK + RGB",
        kebab="sheetcmyk-cmyk-plus-rgb",
        output_intent_icc="FOGRA51L_coated.icc",
        output_condition="FOGRA51L (PSO Coated v3)",
        rgb_allowed=True,
        spots_allowed=False,
        max_tac_cmyk=300,
        max_tac_all=300,
        min_image_res_color=224,
        min_image_res_1bit=1000,
    ),
    VariantConfig(
        name="SheetSpot CMYK",
        kebab="sheetspot-cmyk",
        output_intent_icc="FOGRA51L_coated.icc",
        output_condition="FOGRA51L (PSO Coated v3)",
        rgb_allowed=False,
        spots_allowed=True,
        max_tac_cmyk=300,
        max_tac_all=320,
        min_image_res_color=224,
        min_image_res_1bit=1000,
    ),
    VariantConfig(
        name="SheetSpot CMYK + RGB",
        kebab="sheetspot-cmyk-plus-rgb",
        output_intent_icc="FOGRA51L_coated.icc",
        output_condition="FOGRA51L (PSO Coated v3)",
        rgb_allowed=True,
        spots_allowed=True,
        max_tac_cmyk=300,
        max_tac_all=320,
        min_image_res_color=224,
        min_image_res_1bit=1000,
    ),
    VariantConfig(
        name="WebCMYK CMYK",
        kebab="webcmyk-cmyk",
        output_intent_icc="FOGRA51L_coated.icc",
        output_condition="FOGRA51L (PSO Coated v3)",
        rgb_allowed=False,
        spots_allowed=False,
        max_tac_cmyk=300,
        max_tac_all=300,
        min_image_res_color=224,
        min_image_res_1bit=1000,
    ),
    VariantConfig(
        name="WebCMYK CMYK + RGB",
        kebab="webcmyk-cmyk-plus-rgb",
        output_intent_icc="FOGRA51L_coated.icc",
        output_condition="FOGRA51L (PSO Coated v3)",
        rgb_allowed=True,
        spots_allowed=False,
        max_tac_cmyk=300,
        max_tac_all=300,
        min_image_res_color=224,
        min_image_res_1bit=1000,
    ),
    VariantConfig(
        name="WebSpot CMYK",
        kebab="webspot-cmyk",
        output_intent_icc="FOGRA51L_coated.icc",
        output_condition="FOGRA51L (PSO Coated v3)",
        rgb_allowed=False,
        spots_allowed=True,
        max_tac_cmyk=300,
        max_tac_all=320,
        min_image_res_color=224,
        min_image_res_1bit=1000,
    ),
    VariantConfig(
        name="WebSpot CMYK + RGB",
        kebab="webspot-cmyk-plus-rgb",
        output_intent_icc="FOGRA51L_coated.icc",
        output_condition="FOGRA51L (PSO Coated v3)",
        rgb_allowed=True,
        spots_allowed=True,
        max_tac_cmyk=300,
        max_tac_all=320,
        min_image_res_color=224,
        min_image_res_1bit=1000,
    ),
    VariantConfig(
        name="WebCMYKNews CMYK",
        kebab="webcmyknews-cmyk",
        output_intent_icc="FOGRA51L_coated.icc",
        output_condition="WAN-IFRAnewspaper26v5",
        rgb_allowed=False,
        spots_allowed=False,
        max_tac_cmyk=260,
        max_tac_all=260,
        min_image_res_color=170,
        min_image_res_1bit=600,
    ),
    VariantConfig(
        name="WebCMYKNews CMYK + RGB",
        kebab="webcmyknews-cmyk-plus-rgb",
        output_intent_icc="FOGRA51L_coated.icc",
        output_condition="WAN-IFRAnewspaper26v5",
        rgb_allowed=True,
        spots_allowed=False,
        max_tac_cmyk=260,
        max_tac_all=260,
        min_image_res_color=170,
        min_image_res_1bit=600,
    ),
    VariantConfig(
        name="Packaging Offset",
        kebab="packaging-offset",
        output_intent_icc="FOGRA51L_coated.icc",
        output_condition="FOGRA51L (PSO Coated v3)",
        rgb_allowed=False,
        spots_allowed=True,
        max_tac_cmyk=300,
        max_tac_all=320,
        min_image_res_color=224,
        min_image_res_1bit=1000,
        is_packaging=True,
    ),
    VariantConfig(
        name="Packaging Gravure",
        kebab="packaging-gravure",
        output_intent_icc="FOGRA51L_coated.icc",
        output_condition="FOGRA51L (PSO Coated v3)",
        rgb_allowed=False,
        spots_allowed=True,
        max_tac_cmyk=300,
        max_tac_all=320,
        min_image_res_color=224,
        min_image_res_1bit=1000,
        is_packaging=True,
    ),
    VariantConfig(
        name="Packaging Flexo",
        kebab="packaging-flexo",
        output_intent_icc="FOGRA51L_coated.icc",
        output_condition="FOGRA51L (PSO Coated v3)",
        rgb_allowed=False,
        spots_allowed=True,
        max_tac_cmyk=300,
        max_tac_all=320,
        min_image_res_color=224,
        min_image_res_1bit=1000,
        is_packaging=True,
    ),
    VariantConfig(
        name="Label & Leaflet",
        kebab="label-leaflet",
        output_intent_icc="FOGRA51L_coated.icc",
        output_condition="FOGRA51L (PSO Coated v3)",
        rgb_allowed=False,
        spots_allowed=True,
        max_tac_cmyk=300,
        max_tac_all=320,
        min_image_res_color=224,
        min_image_res_1bit=1000,
        is_packaging=True,
    ),
    VariantConfig(
        name="Folding Carton & Corrugated Box",
        kebab="folding-carton-corrugated-box",
        output_intent_icc="FOGRA51L_coated.icc",
        output_condition="FOGRA51L (PSO Coated v3)",
        rgb_allowed=False,
        spots_allowed=True,
        max_tac_cmyk=300,
        max_tac_all=320,
        min_image_res_color=224,
        min_image_res_1bit=1000,
        is_packaging=True,
    ),
    VariantConfig(
        name="Flexible",
        kebab="flexible",
        output_intent_icc="FOGRA51L_coated.icc",
        output_condition="FOGRA51L (PSO Coated v3)",
        rgb_allowed=False,
        spots_allowed=True,
        max_tac_cmyk=300,
        max_tac_all=320,
        min_image_res_color=224,
        min_image_res_1bit=1000,
        is_packaging=True,
    ),
    VariantConfig(
        name="Corrugated Display",
        kebab="corrugated-display",
        output_intent_icc="FOGRA51L_coated.icc",
        output_condition="FOGRA51L (PSO Coated v3)",
        rgb_allowed=False,
        spots_allowed=True,
        max_tac_cmyk=300,
        max_tac_all=320,
        min_image_res_color=224,
        min_image_res_1bit=1000,
        is_packaging=True,
    ),
    VariantConfig(
        name="Digital Print",
        kebab="digital-print",
        output_intent_icc="FOGRA51L_coated.icc",
        output_condition="FOGRA51L (PSO Coated v3)",
        rgb_allowed=True,
        spots_allowed=False,
        max_tac_cmyk=300,
        max_tac_all=300,
        min_image_res_color=224,
        min_image_res_1bit=1000,
    ),
    VariantConfig(
        name="Large Format Print",
        kebab="large-format-print",
        output_intent_icc="FOGRA51L_coated.icc",
        output_condition="FOGRA51L (PSO Coated v3)",
        rgb_allowed=True,
        spots_allowed=True,
        max_tac_cmyk=300,
        max_tac_all=320,
        min_image_res_color=150,
        min_image_res_1bit=600,
    ),
]

assert len(VARIANTS) == 23, f"Expected 23 variants, got {len(VARIANTS)}"

VARIANT_BY_KEBAB: Final[dict[str, VariantConfig]] = {v.kebab: v for v in VARIANTS}
VARIANT_BY_NAME: Final[dict[str, VariantConfig]] = {v.name: v for v in VARIANTS}


def get_variant(kebab_or_name: str) -> VariantConfig:
    """Lookup a VariantConfig by either kebab or spec literal name."""
    if kebab_or_name in VARIANT_BY_KEBAB:
        return VARIANT_BY_KEBAB[kebab_or_name]
    if kebab_or_name in VARIANT_BY_NAME:
        return VARIANT_BY_NAME[kebab_or_name]
    raise KeyError(f"No variant named {kebab_or_name!r}; known: {sorted(VARIANT_BY_KEBAB)}")
