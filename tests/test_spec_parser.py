"""Test the GWG 2022 spec parser against the committed workbook."""

from __future__ import annotations

from pathlib import Path

import pytest

from assay_pdf.models import RequirementManifest, Severity
from assay_pdf.spec.parser import _kebab, _parse_additional_values, parse_workbook


class TestKebab:
    @pytest.mark.parametrize(
        ("input_name", "expected"),
        [
            ("Magazine Ads CMYK", "magazine-ads-cmyk"),
            ("Magazine Ads CMYK + RGB", "magazine-ads-cmyk-plus-rgb"),
            ("SheetCMYK CMYK", "sheetcmyk-cmyk"),
            ("Folding Carton & Corrugated Box", "folding-carton-corrugated-box"),
            ("Label & Leaflet", "label-leaflet"),
            ("Large Format Print", "large-format-print"),
            ("Flexible", "flexible"),
        ],
    )
    def test_known_variants_normalize(self, input_name: str, expected: str) -> None:
        assert _kebab(input_name) == expected


class TestAdditionalValues:
    def test_empty(self) -> None:
        assert _parse_additional_values(None) == {}
        assert _parse_additional_values("") == {}

    def test_single_kv(self) -> None:
        assert _parse_additional_values("A = 224ppi") == {"A": "224ppi"}

    def test_comma_separated(self) -> None:
        assert _parse_additional_values("A = 280, B = 5mm") == {"A": "280", "B": "5mm"}

    def test_newline_separated(self) -> None:
        assert _parse_additional_values("A = 224ppi\nB = 5") == {"A": "224ppi", "B": "5"}

    def test_iso_value_with_dash(self) -> None:
        assert _parse_additional_values("A = ISO 15930-7") == {"A": "ISO 15930-7"}


class TestParseWorkbook:
    @pytest.fixture
    def manifest(self, spec_xlsx: Path) -> RequirementManifest:
        return parse_workbook(spec_xlsx)

    def test_returns_requirement_manifest(self, manifest: RequirementManifest) -> None:
        assert isinstance(manifest, RequirementManifest)

    def test_has_23_variants(self, manifest: RequirementManifest) -> None:
        assert len(manifest.variants) == 23

    def test_first_variant_is_magazine_ads_cmyk(self, manifest: RequirementManifest) -> None:
        assert manifest.variants[0].name == "Magazine Ads CMYK"
        assert manifest.variants[0].kebab == "magazine-ads-cmyk"

    def test_has_39_requirements(self, manifest: RequirementManifest) -> None:
        assert len(manifest.requirements) == 39

    def test_r0001_is_pdfx4_iso(self, manifest: RequirementManifest) -> None:
        r0001 = next(r for r in manifest.requirements if r.id == "R0001")
        assert r0001.title == "Base ISO standards"
        assert "MagazineAds_CMYK" not in r0001.applicability  # spec-literal name
        assert "Magazine Ads CMYK" in r0001.applicability
        assert r0001.applicability["Magazine Ads CMYK"].severity == Severity.error
        assert r0001.applicability["Magazine Ads CMYK"].additional_values == {"A": "ISO 15930-7"}

    def test_r0007_universal_error(self, manifest: RequirementManifest) -> None:
        """White text overprint is an error in every variant."""
        r0007 = next(r for r in manifest.requirements if r.id == "R0007")
        assert len(r0007.applicability) == 23
        for app in r0007.applicability.values():
            assert app.severity == Severity.error

    def test_r0006_ignored_for_ad_variants(self, manifest: RequirementManifest) -> None:
        """R0006 (single page) is 'ignore' for sheet/web/digital variants — they're omitted from applicability."""
        r0006 = next(r for r in manifest.requirements if r.id == "R0006")
        # 'ignore' cells produce no applicability entry — these variants are excluded.
        assert "SheetCMYK CMYK" not in r0006.applicability
        assert "Digital Print" not in r0006.applicability
        # But Magazine Ads CMYK still applies as error.
        assert r0006.applicability["Magazine Ads CMYK"].severity == Severity.error

    def test_r0031_dual_band_severity(self, manifest: RequirementManifest) -> None:
        """R0031 image resolution is a dual-band rule: 'error' below threshold A, 'warning' between A and B."""
        r0031 = next(r for r in manifest.requirements if r.id == "R0031")
        sheet = r0031.applicability["SheetCMYK CMYK"]
        news = r0031.applicability["Newspaper Ads CMYK"]
        assert sheet.severity == Severity.error_and_warning
        assert news.severity == Severity.error_and_warning
        # Threshold A is the spec-defined warning band cutoff.
        assert sheet.additional_values.get("A") == "224ppi"
        assert news.additional_values.get("A") == "149ppi"

    def test_processing_steps_rules_present(self, manifest: RequirementManifest) -> None:
        rids = {r.id for r in manifest.requirements}
        assert "R1001" in rids
        assert "R1002" in rids

    def test_sha256_recorded(self, manifest: RequirementManifest) -> None:
        assert len(manifest.spec_xlsx_sha256) == 64

    def test_serializes_round_trip(self, manifest: RequirementManifest) -> None:
        as_json = manifest.model_dump_json()
        rehydrated = RequirementManifest.model_validate_json(as_json)
        assert rehydrated.spec_xlsx_sha256 == manifest.spec_xlsx_sha256
        assert len(rehydrated.requirements) == len(manifest.requirements)
