"""codexPDF runner (subprocess shell-out).

AssayPDF remains MIT and does not import AGPL codex-pdf in-process.
Integration happens through the codex-pdf CLI JSON contract.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from assay_pdf.harness.runners.base import Runner, RunnerError
from assay_pdf.models import EngineResult, RuleHit, Severity


class CodexPDFRunner(Runner):
    name = "codexpdf"
    binary_name = "codex-pdf"

    def engine_version(self) -> str:
        code, stdout, stderr = self._run_subprocess([self.binary_path(), "schema", "--version", "1"])
        if code != 0:
            raise RunnerError(f"codex-pdf schema failed: {stderr.strip()}")
        # v0 contract runner: version inference is static for now.
        return "codex-contract-v1"

    def run(self, pdf_path: Path, variant_kebab: str) -> EngineResult:
        _ = variant_kebab  # codex extraction is profile-agnostic.
        started = time.monotonic()
        code, stdout, stderr = self._run_subprocess(
            [self.binary_path(), "extract", str(pdf_path)],
            timeout=180.0,
        )
        if code != 0:
            raise RunnerError(f"codex-pdf extract failed: {stderr.strip()}")
        payload = json.loads(stdout)

        hits: list[RuleHit] = []
        warnings = payload.get("extraction_warnings", [])
        for idx, warning in enumerate(warnings):
            if not isinstance(warning, dict):
                continue
            hits.append(
                RuleHit(
                    rule_id=None,
                    severity=Severity.warning,
                    message=f"CODEX_WARN_{idx}: {warning.get('message', 'extraction warning')}",
                    location=warning.get("scope"),
                    raw=warning,
                )
            )

        return EngineResult(
            engine=self.name,
            engine_version=self.engine_version(),
            profile="codex",
            file=str(pdf_path),
            hits=hits,
            runtime_ms=int((time.monotonic() - started) * 1000),
            raw_output=stdout,
        )
