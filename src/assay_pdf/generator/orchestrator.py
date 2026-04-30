"""Drives the full corpus generation pipeline. Imported by ``assay generate``.

Dispatch policy:
- Positive (BASELINE): generate one per variant → 23 PDFs.
- Negative (R-xxxx): generate ONE per rule, picking the first applicable variant per
  the requirement-ids.json applicability map. Default representative is
  'SheetCMYK CMYK' if the rule applies there; otherwise the first applicable variant
  in spec order.

Round 3c will extend this with boundary-stress generators (multiple negatives per
threshold rule).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from assay_pdf import models

# Importing rules.py registers all generators via decorators
from assay_pdf.generator import rules as _rules  # noqa: F401
from assay_pdf.generator.registry import RULE_GENERATORS
from assay_pdf.generator.variants import VARIANT_BY_NAME, VARIANTS, get_variant
from assay_pdf.logging import get_logger
from assay_pdf.models import CorpusManifest, ManifestEntry, RequirementManifest

log = get_logger(__name__)

DEFAULT_REPRESENTATIVE_VARIANT = "SheetCMYK CMYK"


def _output_path_for(rule_id: str, kind: str, variant_kebab: str, repo: Path) -> Path:
    if kind == "positive":
        return repo / "corpus" / "positive" / variant_kebab / f"{variant_kebab}.pdf"
    rule_slug = rule_id.lower()
    return repo / "corpus" / "negative" / rule_slug / f"{rule_slug}-{variant_kebab}.pdf"


def _load_applicability(repo: Path) -> dict[str, list[str]]:
    """Return {rule_id: [applicable variant names...]} from requirement-ids.json."""
    p = repo / "spec" / "requirement-ids.json"
    if not p.exists():
        return {}
    raw = json.loads(p.read_text(encoding="utf-8"))
    manifest = RequirementManifest.model_validate(raw)
    return {req.id: list(req.applicability.keys()) for req in manifest.requirements}


def _pick_variant_for_rule(rule_id: str, applicability: dict[str, list[str]]) -> str | None:
    """Pick the representative variant for a negative test of `rule_id`.

    Returns the variant kebab name. Returns None if no variant is applicable
    (rule applies to nothing — shouldn't happen for v0.1.0 rules but guarded).
    """
    applicable = applicability.get(rule_id, [])
    if not applicable:
        # Stub rules and rules where the JSON missed something — fall back to default.
        return VARIANT_BY_NAME[DEFAULT_REPRESENTATIVE_VARIANT].kebab
    if DEFAULT_REPRESENTATIVE_VARIANT in applicable:
        return VARIANT_BY_NAME[DEFAULT_REPRESENTATIVE_VARIANT].kebab
    return VARIANT_BY_NAME[applicable[0]].kebab


def generate_corpus(
    *,
    only_rule: str | None = None,
    only_variant: str | None = None,
    seed: int = 0,
    write_manifest: bool = True,
) -> CorpusManifest:
    """Generate the corpus and write corpus/manifest.json. Returns the manifest."""
    repo = models.repo_root()
    applicability = _load_applicability(repo)

    entries: list[ManifestEntry] = []

    for (rule_id, kind), generator in RULE_GENERATORS.items():
        # Filter by rule. BASELINE (positive) is the only generator that runs unconditionally
        # when only_rule is set to a non-BASELINE rule, so users always get a positive baseline
        # alongside any single negative they request.
        if only_rule and rule_id != only_rule and rule_id != "BASELINE":
            continue
        if only_rule and rule_id == "BASELINE" and only_rule != "BASELINE" and kind != "positive":
            continue

        # Pick variants
        if kind == "positive":
            target_variants = (
                [get_variant(only_variant)] if only_variant else list(VARIANTS)
            )
        else:
            # One negative per rule, on its representative variant
            picked = only_variant or _pick_variant_for_rule(rule_id, applicability)
            if picked is None:
                log.warning("Rule %s has no applicable variant — skipping", rule_id)
                continue
            target_variants = [get_variant(picked)]

        for variant in target_variants:
            output = _output_path_for(rule_id, kind, variant.kebab, repo)
            log.info("Generating %s [%s] %s -> %s", rule_id, kind, variant.kebab, output)
            entry = generator(variant=variant, output_path=output, repo_root=repo, seed=seed)
            entries.append(entry)

    from assay_pdf import __version__

    manifest = CorpusManifest(
        version="0.1.0",
        generated_at=datetime.now(UTC),
        tool_version=__version__,
        deterministic_seed=seed,
        files=sorted(entries, key=lambda e: e.path),
    )

    if write_manifest:
        manifest_path = repo / "corpus" / "manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")
        log.info("Wrote %s (%d files)", manifest_path, len(entries))

    return manifest
