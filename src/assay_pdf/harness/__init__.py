"""Engine harness — runs preflight engines against the corpus and scores results."""

from assay_pdf.harness.runners.base import Runner
from assay_pdf.harness.scorer import score_engine_run

__all__ = ["Runner", "score_engine_run"]
