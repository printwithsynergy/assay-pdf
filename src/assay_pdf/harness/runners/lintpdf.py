"""lintPDF runner using the lint-pdf codex-cluster CLI contract."""

from __future__ import annotations

import json
import time
from pathlib import Path

from assay_pdf.harness.runners.base import Runner, RunnerError
from assay_pdf.models import EngineResult, RuleHit


class LintPDFRunner(Runner):
    name = "lintpdf"
    binary_name = "lint-pdf"

    def engine_version(self) -> str:
        return "lintpdf-codex-cluster-v1"

    def run(self, pdf_path: Path, variant_kebab: str) -> EngineResult:
        _ = variant_kebab  # Batch-1 adapter path uses a fixed cluster contract.
        started = time.monotonic()
        code, stdout, stderr = self._run_subprocess(
            [self.binary_path(), "codex-cluster", str(pdf_path), "--cluster", "page-geometry"],
            timeout=180.0,
        )
        if code != 0:
            raise RunnerError(f"lint-pdf codex-cluster failed: {stderr.strip()}")

        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise RunnerError("lint-pdf codex-cluster returned invalid JSON") from exc
        findings = payload.get("findings") if isinstance(payload, dict) else None
        if not isinstance(findings, list):
            findings = []

        hits: list[RuleHit] = []
        for finding in findings:
            if not isinstance(finding, dict):
                continue
            inspection_id = finding.get("inspection_id")
            message = str(finding.get("message") or "lint-pdf finding")
            severity_raw = str(finding.get("severity") or "warning")
            location = self._normalize_location(finding)
            mapped_rule_id = self.map_message_to_rule(message)
            hits.append(
                RuleHit(
                    rule_id=self._normalize_rule_id(inspection_id, mapped_rule_id),
                    severity=self._coerce_severity(severity_raw),
                    message=message,
                    location=location,
                    raw=finding,
                )
            )

        return EngineResult(
            engine=self.name,
            engine_version=self.engine_version(),
            profile="page-geometry",
            file=str(pdf_path),
            hits=hits,
            runtime_ms=int((time.monotonic() - started) * 1000),
            raw_output=stdout,
        )

    @staticmethod
    def _normalize_rule_id(inspection_id: object, mapped_rule_id: str | None) -> str | None:
        if isinstance(inspection_id, str) and inspection_id.strip():
            return inspection_id.strip()
        if mapped_rule_id:
            return mapped_rule_id
        return None

    @staticmethod
    def _normalize_location(finding: dict[str, object]) -> str:
        page_num = finding.get("page_num")
        page = int(page_num) if isinstance(page_num, int | float) else 0
        bbox = finding.get("bbox")
        if not isinstance(bbox, list | tuple) or len(bbox) != 4:
            return f"page:{page}"
        try:
            x0 = round(float(bbox[0]), 3)
            y0 = round(float(bbox[1]), 3)
            x1 = round(float(bbox[2]), 3)
            y1 = round(float(bbox[3]), 3)
        except (TypeError, ValueError):
            return f"page:{page}"
        return f"page:{page};bbox:{x0},{y0},{x1},{y1}"
