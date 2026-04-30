"""Test the scorer with synthetic corpus + engine result data."""

from __future__ import annotations

from datetime import UTC, datetime

from assay_pdf.harness.scorer import score_engine_run
from assay_pdf.models import (
    CorpusManifest,
    EngineResult,
    ManifestEntry,
    RuleHit,
    Severity,
)


def _entry(
    path: str,
    *,
    category: str,
    rule_id: str | None,
    variant: str = "SheetCMYK CMYK",
    description: str = "",
) -> ManifestEntry:
    return ManifestEntry(
        path=path,
        category=category,
        primary_rule_id=rule_id,
        applicable_variants=[variant],
        expected_severity={variant: Severity.error} if rule_id else {},
        description=description or f"{rule_id or 'positive'} test",
        generator_function="test.fixture",
        deterministic_inputs={},
        sha256="0" * 64,
        arch_generated_on="x86_64",
    )


def _hit(rule_id: str | None, message: str = "violation") -> RuleHit:
    return RuleHit(rule_id=rule_id, severity=Severity.error, message=message)


def _result(file: str, hits: list[RuleHit], engine: str = "pdftoolbox") -> EngineResult:
    return EngineResult(
        engine=engine,
        engine_version="0.0",
        profile="sheetcmyk-cmyk",
        file=file,
        hits=hits,
        runtime_ms=10,
    )


def _manifest(files: list[ManifestEntry]) -> CorpusManifest:
    return CorpusManifest(
        version="0.1.0",
        generated_at=datetime.now(UTC),
        tool_version="0.1.0",
        deterministic_seed=0,
        files=files,
    )


class TestScorer:
    def test_true_positive(self) -> None:
        """Negative for R0014 + engine reports R0014 → TP=1."""
        manifest = _manifest(
            [_entry("negative/r0014/r0014.pdf", category="negative", rule_id="R0014")]
        )
        results = [_result("negative/r0014/r0014.pdf", [_hit("R0014")])]
        report = score_engine_run(
            engine="pdftoolbox", engine_version="x", corpus_manifest=manifest, results=results
        )
        score = next(s for s in report.per_rule_per_variant if s.rule_id == "R0014")
        assert score.true_positives == 1
        assert score.false_negatives == 0

    def test_false_negative(self) -> None:
        """Negative for R0014 + engine reports nothing → FN=1."""
        manifest = _manifest(
            [_entry("negative/r0014/r0014.pdf", category="negative", rule_id="R0014")]
        )
        results = [_result("negative/r0014/r0014.pdf", [])]
        report = score_engine_run(
            engine="pdftoolbox", engine_version="x", corpus_manifest=manifest, results=results
        )
        score = next(s for s in report.per_rule_per_variant if s.rule_id == "R0014")
        assert score.false_negatives == 1
        assert score.true_positives == 0

    def test_false_positive_on_positive(self) -> None:
        """Positive baseline + engine reports R0014 anyway → FP=1."""
        manifest = _manifest(
            [
                _entry(
                    "positive/sheetcmyk-cmyk/sheetcmyk-cmyk.pdf", category="positive", rule_id=None
                )
            ]
        )
        results = [_result("positive/sheetcmyk-cmyk/sheetcmyk-cmyk.pdf", [_hit("R0014")])]
        report = score_engine_run(
            engine="pdftoolbox", engine_version="x", corpus_manifest=manifest, results=results
        )
        score = next(s for s in report.per_rule_per_variant if s.rule_id == "R0014")
        assert score.false_positives == 1

    def test_stub_excluded(self) -> None:
        """Stub negatives don't contribute to scoring."""
        manifest = _manifest(
            [
                _entry(
                    "negative/r0009/r0009.pdf",
                    category="negative",
                    rule_id="R0009",
                    description="[v0.1.1 STUB] not yet implemented",
                )
            ]
        )
        results = [_result("negative/r0009/r0009.pdf", [])]
        report = score_engine_run(
            engine="pdftoolbox", engine_version="x", corpus_manifest=manifest, results=results
        )
        # No score entry should exist for R0009 because the stub didn't trigger any counts
        scores_for_r0009 = [s for s in report.per_rule_per_variant if s.rule_id == "R0009"]
        assert all(
            s.true_positives + s.false_positives + s.true_negatives + s.false_negatives == 0
            for s in scores_for_r0009
        )

    def test_misattribution(self) -> None:
        """Negative for R0014, engine reports R0007 → FN for R0014 + FP for R0007."""
        manifest = _manifest(
            [_entry("negative/r0014/r0014.pdf", category="negative", rule_id="R0014")]
        )
        results = [_result("negative/r0014/r0014.pdf", [_hit("R0007")])]
        report = score_engine_run(
            engine="pdftoolbox", engine_version="x", corpus_manifest=manifest, results=results
        )
        scores = {(s.rule_id, s.variant): s for s in report.per_rule_per_variant}
        assert scores[("R0014", "SheetCMYK CMYK")].false_negatives == 1
        assert scores[("R0007", "SheetCMYK CMYK")].false_positives == 1
