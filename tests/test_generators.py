"""Smoke tests for the generator framework."""

from __future__ import annotations

from pathlib import Path

import pikepdf
import pytest

from assay_pdf.generator.registry import RULE_GENERATORS
from assay_pdf.generator.variants import VARIANT_BY_KEBAB, VARIANTS, get_variant


class TestVariants:
    def test_count(self) -> None:
        assert len(VARIANTS) == 23

    def test_kebab_unique(self) -> None:
        kebabs = [v.kebab for v in VARIANTS]
        assert len(kebabs) == len(set(kebabs))

    def test_kebab_lookup(self) -> None:
        v = get_variant("sheetcmyk-cmyk")
        assert v.name == "SheetCMYK CMYK"

    def test_name_lookup(self) -> None:
        v = get_variant("Magazine Ads CMYK")
        assert v.kebab == "magazine-ads-cmyk"

    def test_unknown_raises(self) -> None:
        with pytest.raises(KeyError):
            get_variant("nonexistent")

    def test_packaging_flag_set(self) -> None:
        assert VARIANT_BY_KEBAB["packaging-offset"].is_packaging
        assert not VARIANT_BY_KEBAB["sheetcmyk-cmyk"].is_packaging


class TestRegistry:
    def test_baseline_registered(self) -> None:
        assert ("BASELINE", "positive") in RULE_GENERATORS

    def test_r0014_registered(self) -> None:
        assert ("R0014", "negative") in RULE_GENERATORS


class TestGeneration:
    @pytest.fixture
    def temp_repo(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        from assay_pdf import models

        real_root = models.repo_root()
        (tmp_path / "src").symlink_to(real_root / "src")
        (tmp_path / "spec").symlink_to(real_root / "spec")
        (tmp_path / "vendor").symlink_to(real_root / "vendor")
        (tmp_path / "corpus").mkdir()
        monkeypatch.setattr(models, "repo_root", lambda: tmp_path)
        return tmp_path

    def test_baseline_produces_valid_pdf(self, temp_repo: Path) -> None:
        from assay_pdf.generator.orchestrator import generate_corpus

        manifest = generate_corpus(
            only_rule="BASELINE", only_variant="sheetcmyk-cmyk", seed=0, write_manifest=False
        )
        assert len(manifest.files) == 1
        pdf_path = temp_repo / manifest.files[0].path
        assert pdf_path.exists()

        with pikepdf.open(pdf_path) as pdf:
            assert pdf.pdf_version >= "1.6"
            assert "/OutputIntents" in pdf.Root
            page = pdf.pages[0]
            assert "/MediaBox" in page
            assert "/TrimBox" in page

    def test_r0014_includes_courier(self, temp_repo: Path) -> None:
        from assay_pdf.generator.orchestrator import generate_corpus

        manifest = generate_corpus(
            only_rule="R0014", only_variant="sheetcmyk-cmyk", seed=0, write_manifest=False
        )
        # BASELINE always runs (it's the positive). Filter to R0014.
        r0014 = [e for e in manifest.files if e.primary_rule_id == "R0014"]
        assert len(r0014) == 1
        pdf_path = temp_repo / r0014[0].path

        with pikepdf.open(pdf_path) as pdf:
            page = pdf.pages[0]
            font_dict = page.Resources["/Font"]
            font_names = [str(font_dict[k]["/BaseFont"]) for k in font_dict]
            assert any("Courier" in name for name in font_names), (
                f"Courier not found in {font_names}"
            )
