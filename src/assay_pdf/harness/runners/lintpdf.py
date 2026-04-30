"""lintPDF runner — stub for v0.1.0.

lintPDF's API is not yet published. This runner is scaffolded so that, when the
API ships, dropping in an HTTP client + result parser completes the integration.
For v0.1.0, ``run()`` raises ``RunnerNotInstalledError`` to signal the engine isn't
available — the scoring layer treats this as a benign "not implemented" rather
than a false negative.
"""

from __future__ import annotations

from pathlib import Path

from assay_pdf.harness.runners.base import Runner, RunnerNotInstalledError
from assay_pdf.models import EngineResult


class LintPDFRunner(Runner):
    name = "lintpdf"
    binary_name = "lintpdf"  # Placeholder — actual integration is HTTP API

    def engine_version(self) -> str:
        return "lintpdf-stub-0.1.0"

    def run(self, pdf_path: Path, variant_kebab: str) -> EngineResult:
        raise RunnerNotInstalledError(
            "lintPDF API client not implemented in v0.1.0 — track at "
            "https://github.com/thinkneverland/lint-pdf"
        )
