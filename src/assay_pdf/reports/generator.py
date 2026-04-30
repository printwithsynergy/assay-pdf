"""Render markdown + HTML scoreboards from results/<engine>-<ts>.score.json."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast

from jinja2 import Environment, FileSystemLoader, select_autoescape

from assay_pdf import models
from assay_pdf.logging import get_logger
from assay_pdf.models import ScoreReport

log = get_logger(__name__)


def _templates_dir() -> Path:
    return Path(__file__).resolve().parent / "templates"


def _load_all_scores(repo: Path) -> list[ScoreReport]:
    """Load every results/*.score.json into ScoreReport models."""
    results_dir = repo / "results"
    if not results_dir.exists():
        return []
    reports: list[ScoreReport] = []
    for path in sorted(results_dir.glob("*.score.json")):
        try:
            reports.append(ScoreReport.model_validate_json(path.read_text(encoding="utf-8")))
        except Exception as e:
            log.warning("Skipping malformed score file %s: %s", path, e)
    return reports


def _engine_summary(report: ScoreReport) -> dict[str, float | int]:
    """Compute engine-level aggregate metrics from per-rule scores."""
    tp = sum(s.true_positives for s in report.per_rule_per_variant)
    fp = sum(s.false_positives for s in report.per_rule_per_variant)
    fn = sum(s.false_negatives for s in report.per_rule_per_variant)
    tn = sum(s.true_negatives for s in report.per_rule_per_variant)
    total = tp + fp + tn + fn
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "total": total,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def _rule_breakdown(reports: list[ScoreReport]) -> list[dict[str, object]]:
    """Aggregate per-rule metrics across all engines.

    Returns a list of dicts, one per (rule_id), each with per-engine TP/FP/FN/TN.
    """
    # rule_id -> engine -> aggregated counts (summed across variants)
    by_rule: dict[str, dict[str, dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0})
    )
    for report in reports:
        for s in report.per_rule_per_variant:
            cell = by_rule[s.rule_id][report.engine]
            cell["tp"] += s.true_positives
            cell["fp"] += s.false_positives
            cell["fn"] += s.false_negatives
            cell["tn"] += s.true_negatives

    rows: list[dict[str, object]] = []
    for rule_id in sorted(by_rule):
        engines: dict[str, dict[str, float | int]] = {}
        for engine, cnt in by_rule[rule_id].items():
            denom_p = cnt["tp"] + cnt["fp"]
            denom_r = cnt["tp"] + cnt["fn"]
            engines[engine] = {
                **cnt,
                "precision": cnt["tp"] / denom_p if denom_p else 0.0,
                "recall": cnt["tp"] / denom_r if denom_r else 0.0,
            }
        rows.append({"rule_id": rule_id, "engines": engines})
    return rows


def _build_context(repo: Path) -> dict[str, object]:
    reports = _load_all_scores(repo)
    engines = sorted({r.engine for r in reports})
    return {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "tool_version": __import__("assay_pdf").__version__,
        "engines": engines,
        "reports": reports,
        "engine_summaries": {r.engine: _engine_summary(r) for r in reports},
        "rule_breakdown": _rule_breakdown(reports),
        "corpus_version": reports[0].corpus_version if reports else "n/a",
    }


def render_report(format: str = "md") -> str:
    """Render a scoreboard from every results/*.score.json file.

    ``format`` must be 'md' or 'html'. Validated at boundary; cast to Literal for
    template selection.
    """
    if format not in {"md", "html"}:
        raise ValueError(f"format must be 'md' or 'html', got {format!r}")
    fmt: Literal["md", "html"] = cast(Literal["md", "html"], format)
    repo = models.repo_root()
    env = Environment(
        loader=FileSystemLoader(str(_templates_dir())),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template_name = "markdown.j2" if fmt == "md" else "html.j2"
    template = env.get_template(template_name)
    return template.render(**_build_context(repo))
