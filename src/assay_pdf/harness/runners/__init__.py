"""Engine runners — one per preflight engine."""

from assay_pdf.harness.runners.base import Runner, RunnerError, RunnerNotInstalledError
from assay_pdf.harness.runners.lintpdf import LintPDFRunner
from assay_pdf.harness.runners.pdftoolbox import PdfToolboxRunner
from assay_pdf.harness.runners.pitstop import PitStopRunner

__all__ = [
    "LintPDFRunner",
    "PdfToolboxRunner",
    "PitStopRunner",
    "Runner",
    "RunnerError",
    "RunnerNotInstalledError",
]


def get_runner(engine: str) -> Runner:
    """Return a Runner instance for the named engine."""
    runners: dict[str, type[Runner]] = {
        "lintpdf": LintPDFRunner,
        "pitstop": PitStopRunner,
        "pdftoolbox": PdfToolboxRunner,
    }
    cls = runners.get(engine.lower())
    if cls is None:
        raise ValueError(f"Unknown engine {engine!r}; known: {sorted(runners)}")
    return cls()
