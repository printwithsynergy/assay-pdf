"""Rule generator registry.

Each generator is registered against a rule ID and a kind ("positive" or "negative").
The corpus builder (`assay generate`) iterates the registry, calls each generator,
and produces the corresponding PDF + ManifestEntry.

A generator's signature is fixed:

    def gen(*, variant: VariantConfig, output_path: Path, repo_root: Path, seed: int) -> ManifestEntry: ...

This lets us treat all 39+ generators uniformly without per-rule special cases at the
dispatch layer.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Final, Literal, Protocol

from assay_pdf.generator.variants import VariantConfig
from assay_pdf.models import ManifestEntry


class RuleGenerator(Protocol):
    """The shape every rule generator must implement."""

    def __call__(
        self,
        *,
        variant: VariantConfig,
        output_path: Path,
        repo_root: Path,
        seed: int,
    ) -> ManifestEntry: ...


GeneratorKind = Literal["positive", "negative"]

RULE_GENERATORS: Final[dict[tuple[str, GeneratorKind], Callable[..., ManifestEntry]]] = {}


def register(
    rule_id: str, kind: GeneratorKind = "negative"
) -> Callable[[Callable[..., ManifestEntry]], Callable[..., ManifestEntry]]:
    """Decorator: register a function as the generator for (rule_id, kind)."""

    def _decorator(fn: Callable[..., ManifestEntry]) -> Callable[..., ManifestEntry]:
        key = (rule_id, kind)
        if key in RULE_GENERATORS:
            raise ValueError(f"Generator already registered for {key}")
        RULE_GENERATORS[key] = fn
        return fn

    return _decorator
