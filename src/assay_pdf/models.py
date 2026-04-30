"""Pydantic data models — the canonical shapes flowing through AssayPDF.

Every persistent artifact (requirement-ids.json, corpus/manifest.json, results/*.json)
is one of these models serialized. Change a model here and the schema changes everywhere.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class Severity(StrEnum):
    """Per-variant rule outcome severity per GWG 2022 spec.

    GWG 2022 cells use four values:
    - ``error`` — rule violation is an error
    - ``warning`` — rule violation is a warning
    - ``error_and_warning`` — dual-band rule (e.g., R0031 image resolution: error below
      threshold A, warning between A and B). The Variants tab encodes this as the
      literal string "error\\nwarning"; the parser normalizes it to this value.
    - ``ignore`` cells in the spec are not represented at all — the variant is omitted
      from a rule's ``applicability`` dict, signaling "rule does not apply to this
      variant". This avoids carrying a sentinel through every downstream consumer.
    """

    error = "error"
    warning = "warning"
    error_and_warning = "error_and_warning"


class Variant(BaseModel):
    """One of the 23 GWG 2022 variants."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(description="Spec literal name, e.g. 'SheetCMYK CMYK'")
    kebab: str = Field(description="Filesystem-safe kebab-case form, e.g. 'sheetcmyk-cmyk'")


class RuleApplicability(BaseModel):
    """How a single requirement applies to a single variant."""

    severity: Severity
    additional_values: dict[str, str] = Field(
        default_factory=dict,
        description="Variant-specific parameters: e.g. {'A': '224ppi'} for image-res rules.",
    )


class Requirement(BaseModel):
    """One row of the GWG 2022 Requirements tab + its per-variant applicability."""

    id: str = Field(pattern=r"^R\d{4}$", description="GWG 2022 rule ID, e.g. 'R0007'")
    text_id: str = Field(description="Slug ID, e.g. 'r-overprint-white-text'")
    version: float
    title: str
    text: str
    notes: str | None = None
    discussion: str | None = None
    applicability: dict[str, RuleApplicability] = Field(
        default_factory=dict,
        description="Map of variant name → applicability. Missing variant = rule does not apply.",
    )


class RequirementManifest(BaseModel):
    """Top-level shape of spec/requirement-ids.json."""

    spec_version: str = "GWG 2022"
    spec_source_url: str = (
        "https://docs.google.com/spreadsheets/d/1fz7I7pVl0uOTqEqmXeFIEo2LQm97AluHnlTMikzHenI/edit"
    )
    parsed_at: datetime
    parser_version: str
    spec_xlsx_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    variants: list[Variant]
    requirements: list[Requirement]


# ─── Corpus models ─────────────────────────────────────────────────────────────


class Outcome(StrEnum):
    """What a preflight engine should report for a given test PDF."""

    pass_ = "pass"
    error = "error"
    warning = "warning"


class ManifestEntry(BaseModel):
    """One row of corpus/manifest.json."""

    path: str = Field(description="Repo-relative path to the PDF.")
    category: str = Field(pattern=r"^(positive|negative)$")
    primary_rule_id: str | None = Field(
        default=None,
        pattern=r"^R\d{4}$",
        description="The single rule this file is designed to fail (negatives only).",
    )
    applicable_variants: list[str] = Field(description="Variant names this PDF can be benchmarked under.")
    expected_severity: dict[str, Severity] = Field(
        default_factory=dict,
        description="Per-variant expected severity (negatives only).",
    )
    description: str
    generator_function: str = Field(description="Fully-qualified Python ref.")
    deterministic_inputs: dict[str, object] = Field(
        default_factory=dict,
        description="Inputs that must be byte-identical for reproducibility.",
    )
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    arch_generated_on: str = Field(description="CPU arch when this entry was generated.")


class CorpusManifest(BaseModel):
    """Top-level shape of corpus/manifest.json."""

    version: str
    spec: str = "GWG 2022"
    generated_at: datetime
    tool: str = "assay-pdf"
    tool_version: str
    deterministic_seed: int = 0
    files: list[ManifestEntry]


# ─── Engine result models ──────────────────────────────────────────────────────


class RuleHit(BaseModel):
    rule_id: str | None = None
    severity: Severity
    message: str
    location: str | None = None
    raw: dict[str, object] = Field(default_factory=dict)


class EngineResult(BaseModel):
    engine: str
    engine_version: str
    profile: str
    file: str
    hits: list[RuleHit]
    runtime_ms: int
    raw_output: str | None = None


# ─── Score / report models ─────────────────────────────────────────────────────


class RuleScore(BaseModel):
    rule_id: str
    variant: str
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0

    @property
    def accuracy(self) -> float:
        total = self.true_positives + self.false_positives + self.true_negatives + self.false_negatives
        return (self.true_positives + self.true_negatives) / total if total else 0.0

    @property
    def precision(self) -> float:
        denom = self.true_positives + self.false_positives
        return self.true_positives / denom if denom else 0.0

    @property
    def recall(self) -> float:
        denom = self.true_positives + self.false_negatives
        return self.true_positives / denom if denom else 0.0


class ScoreReport(BaseModel):
    engine: str
    engine_version: str
    generated_at: datetime
    corpus_version: str
    per_rule_per_variant: list[RuleScore]
    aggregate_runtime_ms: int


# ─── Vendor checksum models ────────────────────────────────────────────────────


class VendorAsset(BaseModel):
    filename: str
    url: str
    sha256: str | None = None
    size_bytes: int | None = None
    description: str
    license: str


class VendorChecksums(BaseModel):
    schema_url: str | None = Field(default=None, alias="$schema")
    version: str
    generated_at: datetime | None = None
    files: list[VendorAsset]


class SpecAsset(VendorAsset):
    redistributed: bool = True
    notes: str | None = None


class SpecChecksums(BaseModel):
    schema_url: str | None = Field(default=None, alias="$schema")
    version: str
    generated_at: datetime | None = None
    files: list[SpecAsset]


# ─── Helpers ───────────────────────────────────────────────────────────────────


def repo_root() -> Path:
    """Return the AssayPDF repo root by walking up from this file."""
    return Path(__file__).resolve().parent.parent.parent
