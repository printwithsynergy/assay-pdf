"""Scorer — compares engine results against the corpus manifest.

Per (engine, variant, rule_id) computes:
- TP (true positive)  : negative test for that rule, engine flagged the rule (or any hit)
- FP (false positive) : positive baseline, engine flagged this rule
- FN (false negative) : negative test for that rule, engine missed it (no hit for this rule)
- TN (true negative)  : positive baseline, engine did not flag this rule

The scoring is rule-aware: an engine reporting a different rule for the same PDF
counts as a FN for the targeted rule AND a FP for the rule it actually reported.
This is the right behaviour because incorrect rule attribution is itself a quality issue.

Stub negatives (manifest description starts with "[v0.1.1 STUB]") are excluded from
scoring — they don't have actual violations injected, so any engine result against
them is meaningless. They appear in reports as a coverage-gap callout.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from assay_pdf.logging import get_logger
from assay_pdf.models import (
    CorpusManifest,
    EngineResult,
    ManifestEntry,
    RuleScore,
    ScoreReport,
)

log = get_logger(__name__)


def _is_stub(entry: ManifestEntry) -> bool:
    return entry.description.startswith("[v0.1.1 STUB]")


def score_engine_run(
    *,
    engine: str,
    engine_version: str,
    corpus_manifest: CorpusManifest,
    results: list[EngineResult],
) -> ScoreReport:
    """Compute a per-(rule, variant) ScoreReport for one engine run."""
    # Index results by file path
    results_by_path: dict[str, EngineResult] = {
        Path(r.file).relative_to(Path(r.file).anchor).as_posix() if Path(r.file).is_absolute() else r.file: r
        for r in results
    }
    # Try a more forgiving match: just basename → result
    results_by_basename: dict[str, EngineResult] = {Path(r.file).name: r for r in results}

    # Count TP/FP/FN/TN per (rule_id, variant)
    counts: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    )
    aggregate_runtime_ms = sum(r.runtime_ms for r in results)

    # Build the universe of (rule, variant) combinations from manifest
    all_rule_variants: set[tuple[str, str]] = set()
    for entry in corpus_manifest.files:
        if entry.primary_rule_id:
            for variant in entry.applicable_variants:
                all_rule_variants.add((entry.primary_rule_id, variant))

    for entry in corpus_manifest.files:
        if _is_stub(entry):
            continue

        # Resolve which engine result corresponds to this manifest entry
        result = results_by_path.get(entry.path) or results_by_basename.get(Path(entry.path).name)
        if result is None:
            log.debug("No engine result for %s — skipping in score", entry.path)
            continue

        hit_rule_ids = {h.rule_id for h in result.hits if h.rule_id}

        if entry.category == "negative" and entry.primary_rule_id is not None:
            rule_id = entry.primary_rule_id
            for variant in entry.applicable_variants:
                key = (rule_id, variant)
                if rule_id in hit_rule_ids:
                    counts[key]["tp"] += 1
                else:
                    counts[key]["fn"] += 1
                # FP: engine flagged a different rule on this PDF
                for other_rule in hit_rule_ids - {rule_id}:
                    other_key = (other_rule, variant)
                    counts[other_key]["fp"] += 1
                    all_rule_variants.add(other_key)

        elif entry.category == "positive":
            # Positive baseline — every hit is a false positive
            for variant in entry.applicable_variants:
                for hit_rule in hit_rule_ids:
                    counts[(hit_rule, variant)]["fp"] += 1
                # TN for every applicable rule that wasn't hit
                for rule_id, var in all_rule_variants:
                    if var != variant:
                        continue
                    if rule_id not in hit_rule_ids:
                        counts[(rule_id, variant)]["tn"] += 1

    # Materialize as a list of RuleScore
    scores = [
        RuleScore(
            rule_id=rid,
            variant=var,
            true_positives=cnt["tp"],
            false_positives=cnt["fp"],
            true_negatives=cnt["tn"],
            false_negatives=cnt["fn"],
        )
        for (rid, var), cnt in sorted(counts.items())
    ]

    return ScoreReport(
        engine=engine,
        engine_version=engine_version,
        generated_at=datetime.now(UTC),
        corpus_version=corpus_manifest.version,
        per_rule_per_variant=scores,
        aggregate_runtime_ms=aggregate_runtime_ms,
    )


def write_score_report(report: ScoreReport, output_path: Path) -> Path:
    """Persist a ScoreReport as JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return output_path


def load_corpus_manifest(repo: Path) -> CorpusManifest:
    """Load corpus/manifest.json."""
    p = repo / "corpus" / "manifest.json"
    return CorpusManifest.model_validate_json(p.read_text(encoding="utf-8"))


def load_results(results_path: Path) -> list[EngineResult]:
    """Load a JSON-encoded list of EngineResult from disk."""
    raw = json.loads(results_path.read_text(encoding="utf-8"))
    return [EngineResult.model_validate(item) for item in raw]
