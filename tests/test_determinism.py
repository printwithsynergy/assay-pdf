"""Determinism: two `assay generate` runs produce byte-identical output."""

from __future__ import annotations

from pathlib import Path

import pytest

from assay_pdf.generator.orchestrator import generate_corpus
from assay_pdf.generator.variants import get_variant
from assay_pdf.hashing import sha256_file


@pytest.fixture
def temp_corpus_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Run the corpus generator into a temp directory by patching repo_root()."""
    # Mirror the source repo's structure so generators can find ICCs / spec assets.
    from assay_pdf import models

    real_root = models.repo_root()
    # Symlink the parts we need
    (tmp_path / "src").symlink_to(real_root / "src")
    (tmp_path / "spec").symlink_to(real_root / "spec")
    (tmp_path / "vendor").symlink_to(real_root / "vendor")
    (tmp_path / "corpus").mkdir()

    monkeypatch.setattr(models, "repo_root", lambda: tmp_path)
    return tmp_path


def test_baseline_is_deterministic(temp_corpus_dir: Path) -> None:
    """Two runs of the positive baseline for one variant produce identical sha256."""
    variant = get_variant("sheetcmyk-cmyk")

    m1 = generate_corpus(
        only_rule="BASELINE", only_variant=variant.kebab, seed=0, write_manifest=False
    )
    sha_first = m1.files[0].sha256

    m2 = generate_corpus(
        only_rule="BASELINE", only_variant=variant.kebab, seed=0, write_manifest=False
    )
    sha_second = m2.files[0].sha256

    # Recompute fresh to make sure the manifest entry matches the file on disk
    pdf_path = temp_corpus_dir / m2.files[0].path
    assert sha256_file(pdf_path) == sha_second
    assert sha_first == sha_second, (
        "Two generate runs produced different sha256 — generator not deterministic"
    )


def test_r0014_courier_is_deterministic(temp_corpus_dir: Path) -> None:
    """The R0014 negative is also deterministic across runs."""
    variant = get_variant("sheetcmyk-cmyk")

    m1 = generate_corpus(
        only_rule="R0014", only_variant=variant.kebab, seed=0, write_manifest=False
    )
    m2 = generate_corpus(
        only_rule="R0014", only_variant=variant.kebab, seed=0, write_manifest=False
    )

    by_rule_1 = {(e.primary_rule_id or "BASELINE", e.path): e.sha256 for e in m1.files}
    by_rule_2 = {(e.primary_rule_id or "BASELINE", e.path): e.sha256 for e in m2.files}

    for key, sha in by_rule_1.items():
        assert by_rule_2.get(key) == sha, f"sha256 changed for {key}"
