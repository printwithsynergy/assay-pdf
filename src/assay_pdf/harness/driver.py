"""Benchmark driver — runs an engine against the corpus and writes results."""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime

from assay_pdf import models
from assay_pdf.harness.runners import RunnerError, RunnerNotInstalledError, get_runner
from assay_pdf.harness.scorer import (
    load_corpus_manifest,
    score_engine_run,
    write_score_report,
)
from assay_pdf.logging import get_logger
from assay_pdf.models import EngineResult, ScoreReport

log = get_logger(__name__)


def benchmark(
    *,
    engine: str,
    profile: str | None = None,
) -> ScoreReport:
    """Run ``engine`` against every corpus PDF (optionally filtered by profile/variant).

    Writes:
    - ``results/<engine>-<timestamp>.json`` — raw EngineResult list
    - ``results/<engine>-<timestamp>.score.json`` — ScoreReport

    Returns the ScoreReport.
    """
    repo = models.repo_root()
    runner = get_runner(engine)

    try:
        engine_version = runner.engine_version()
    except RunnerNotInstalledError as e:
        log.error("Engine %s is not installed: %s", engine, e)
        raise
    log.info("%s version: %s", engine, engine_version)

    manifest = load_corpus_manifest(repo)
    target_entries = [
        e
        for e in manifest.files
        if profile is None or any(v == profile for v in e.applicable_variants)
        or any(_kebab_matches(v, profile) for v in e.applicable_variants)
    ]
    log.info("Running %s against %d corpus PDFs (profile=%s)", engine, len(target_entries), profile)

    results: list[EngineResult] = []
    start = time.monotonic()
    for entry in target_entries:
        pdf_path = repo / entry.path
        variant_kebab = _resolve_variant_kebab(entry.applicable_variants[0])
        try:
            result = runner.run(pdf_path, variant_kebab)
        except RunnerError as e:
            log.warning("Skipping %s: %s", entry.path, e)
            continue
        results.append(result)
    elapsed_ms = int((time.monotonic() - start) * 1000)
    log.info("Completed %d runs in %dms", len(results), elapsed_ms)

    # Persist raw results
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    raw_path = repo / "results" / f"{engine}-{timestamp}.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(
        json.dumps([r.model_dump() for r in results], indent=2, default=str),
        encoding="utf-8",
    )

    # Score and persist
    score = score_engine_run(
        engine=engine,
        engine_version=engine_version,
        corpus_manifest=manifest,
        results=results,
    )
    score_path = repo / "results" / f"{engine}-{timestamp}.score.json"
    write_score_report(score, score_path)
    log.info("Wrote raw results -> %s and score -> %s", raw_path, score_path)

    return score


def _kebab_matches(variant_name: str, profile: str) -> bool:
    """Check whether a spec-literal variant name corresponds to the given kebab profile."""
    from assay_pdf.generator.variants import VARIANT_BY_NAME

    cfg = VARIANT_BY_NAME.get(variant_name)
    return cfg is not None and cfg.kebab == profile


def _resolve_variant_kebab(variant_name: str) -> str:
    """Translate a spec-literal variant name to its kebab form."""
    from assay_pdf.generator.variants import VARIANT_BY_NAME

    cfg = VARIANT_BY_NAME.get(variant_name)
    if cfg is None:
        raise ValueError(f"Unknown variant {variant_name!r}")
    return cfg.kebab
