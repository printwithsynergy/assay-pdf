"""Smoke tests for report rendering."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from assay_pdf.models import RuleScore, ScoreReport


def _write_score(results_dir: Path, *, engine: str, scores: list[RuleScore]) -> Path:
    report = ScoreReport(
        engine=engine,
        engine_version="0.0",
        generated_at=datetime.now(UTC),
        corpus_version="0.1.0",
        per_rule_per_variant=scores,
        aggregate_runtime_ms=12345,
    )
    path = results_dir / f"{engine}-test.score.json"
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return path


@pytest.fixture
def temp_repo_with_results(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    from assay_pdf import models

    real_root = models.repo_root()
    (tmp_path / "src").symlink_to(real_root / "src")
    (tmp_path / "results").mkdir()
    monkeypatch.setattr(models, "repo_root", lambda: tmp_path)

    _write_score(
        tmp_path / "results",
        engine="pdftoolbox",
        scores=[
            RuleScore(
                rule_id="R0014",
                variant="SheetCMYK CMYK",
                true_positives=1,
                false_positives=0,
                true_negatives=0,
                false_negatives=0,
            ),
            RuleScore(
                rule_id="R0007",
                variant="SheetCMYK CMYK",
                true_positives=0,
                false_positives=2,
                true_negatives=0,
                false_negatives=1,
            ),
        ],
    )
    _write_score(
        tmp_path / "results",
        engine="pitstop",
        scores=[
            RuleScore(
                rule_id="R0014",
                variant="SheetCMYK CMYK",
                true_positives=1,
                false_positives=0,
                true_negatives=0,
                false_negatives=0,
            ),
        ],
    )
    return tmp_path


class TestMarkdown:
    def test_renders_with_two_engines(self, temp_repo_with_results: Path) -> None:
        from assay_pdf.reports.generator import render_report

        text = render_report(format="md")
        assert "# AssayPDF Scoreboard" in text
        assert "pdftoolbox" in text
        assert "pitstop" in text
        assert "R0014" in text
        assert "R0007" in text

    def test_handles_no_results(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from assay_pdf import models
        from assay_pdf.reports.generator import render_report

        real_root = models.repo_root()
        (tmp_path / "src").symlink_to(real_root / "src")
        (tmp_path / "results").mkdir()
        monkeypatch.setattr(models, "repo_root", lambda: tmp_path)

        text = render_report(format="md")
        assert "No score reports found" in text


class TestHTML:
    def test_renders_standalone_html(self, temp_repo_with_results: Path) -> None:
        from assay_pdf.reports.generator import render_report

        text = render_report(format="html")
        assert "<!DOCTYPE html>" in text
        assert "AssayPDF" in text
        assert "tailwindcss" in text
        assert "pdftoolbox" in text
        assert "pitstop" in text
