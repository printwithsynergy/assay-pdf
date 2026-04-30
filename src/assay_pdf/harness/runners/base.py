"""Abstract base for engine runners.

Each preflight engine gets a Runner subclass that:
1. Locates the engine's CLI binary.
2. Translates a GWG variant kebab name into the engine's profile reference.
3. Invokes the engine against a PDF, capturing structured hits.
4. Maps engine-specific messages to GWG rule IDs via rule_maps/<engine>.json.

The harness driver doesn't care about engine internals — it just calls
``runner.run(pdf, variant)`` and gets back an EngineResult.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from assay_pdf.logging import get_logger
from assay_pdf.models import EngineResult, Severity, repo_root

if TYPE_CHECKING:
    pass

log = get_logger(__name__)


class RunnerError(Exception):
    """Base error raised by Runner implementations."""


class RunnerNotInstalledError(RunnerError):
    """Raised when the engine's CLI binary is not on PATH."""


class Runner(ABC):
    """Contract every engine runner satisfies."""

    name: str  # Lowercase engine identifier — must match rule_maps/<name>.json
    binary_name: str  # Expected name of the engine's CLI binary on PATH

    def __init__(self) -> None:
        self._rule_map: dict[str, str] | None = None

    # ─── Binary discovery ──────────────────────────────────────────────────

    def binary_path(self) -> str:
        """Locate the engine's CLI binary; raise if missing."""
        path = shutil.which(self.binary_name)
        if path is None:
            raise RunnerNotInstalledError(
                f"{self.name} CLI binary {self.binary_name!r} not found on PATH"
            )
        return path

    # ─── Rule map ──────────────────────────────────────────────────────────

    def rule_map(self) -> dict[str, str]:
        """Lazy-load and cache rule_maps/<name>.json. Maps regex pattern -> R-id."""
        if self._rule_map is None:
            path = repo_root() / "src" / "assay_pdf" / "harness" / "rule_maps" / f"{self.name}.json"
            if not path.exists():
                log.warning("rule_map for %s missing at %s", self.name, path)
                self._rule_map = {}
            else:
                self._rule_map = json.loads(path.read_text(encoding="utf-8"))
        return self._rule_map

    def map_message_to_rule(self, message: str) -> str | None:
        """Try to match an engine message against rule_map patterns. Returns R-id or None."""
        for pattern, rule_id in self.rule_map().items():
            if re.search(pattern, message, re.IGNORECASE):
                return rule_id
        return None

    # ─── Subprocess helper ─────────────────────────────────────────────────

    def _run_subprocess(
        self,
        args: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 120.0,
    ) -> tuple[int, str, str]:
        """Run a subprocess and return (exit_code, stdout, stderr)."""
        log.debug("Invoking %s", " ".join(args))
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            raise RunnerError(f"{self.name} timed out after {timeout}s") from e
        return result.returncode, result.stdout, result.stderr

    # ─── Subclass contract ─────────────────────────────────────────────────

    @abstractmethod
    def run(self, pdf_path: Path, variant_kebab: str) -> EngineResult:
        """Run the engine against ``pdf_path`` under the variant's profile."""
        ...

    @abstractmethod
    def engine_version(self) -> str:
        """Return the engine's reported version string."""
        ...

    # ─── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _coerce_severity(raw: str) -> Severity:
        """Normalize an engine's severity string to AssayPDF's enum."""
        text = raw.strip().lower()
        if text in {"error", "err", "fail", "failure", "critical"}:
            return Severity.error
        if text in {"warning", "warn", "info"}:
            return Severity.warning
        return Severity.error  # safe default
