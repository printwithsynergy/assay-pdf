"""callas pdfToolbox CLI runner.

pdfToolbox CLI invocation:
    pdfToolbox --report=JSON,Path=/tmp/report.json --profile <profile_path> <pdf_path>

Output: JSON report with hits[], each having type/severity/message/page.

Profile mapping: maps GWG 2022 variant kebab → pdfToolbox profile path. v0.1.0
uses the "Ghent PDF Workgroup 2022" profile family; users override via env var
``ASSAY_PDFTOOLBOX_PROFILE_DIR`` or by editing this module.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from assay_pdf.harness.runners.base import Runner, RunnerError
from assay_pdf.logging import get_logger
from assay_pdf.models import EngineResult, RuleHit

log = get_logger(__name__)


# Mapping GWG variant kebab → pdfToolbox profile filename. Defaults assume
# the user has GWG 2022 profiles installed in pdfToolbox's profile directory.
# Overrideable via env var to point at a custom location.
_DEFAULT_PROFILE_NAMES: dict[str, str] = {
    "magazine-ads-cmyk": "GWG_MagazineAds_CMYK_2022.kfpx",
    "magazine-ads-cmyk-plus-rgb": "GWG_MagazineAds_CMYK_RGB_2022.kfpx",
    "newspaper-ads-cmyk": "GWG_NewspaperAds_CMYK_2022.kfpx",
    "newspaper-ads-cmyk-plus-rgb": "GWG_NewspaperAds_CMYK_RGB_2022.kfpx",
    "sheetcmyk-cmyk": "GWG_SheetCMYK_CMYK_2022.kfpx",
    "sheetcmyk-cmyk-plus-rgb": "GWG_SheetCMYK_CMYK_RGB_2022.kfpx",
    "sheetspot-cmyk": "GWG_SheetSpot_CMYK_2022.kfpx",
    "sheetspot-cmyk-plus-rgb": "GWG_SheetSpot_CMYK_RGB_2022.kfpx",
    "webcmyk-cmyk": "GWG_WebCMYK_CMYK_2022.kfpx",
    "webcmyk-cmyk-plus-rgb": "GWG_WebCMYK_CMYK_RGB_2022.kfpx",
    "webspot-cmyk": "GWG_WebSpot_CMYK_2022.kfpx",
    "webspot-cmyk-plus-rgb": "GWG_WebSpot_CMYK_RGB_2022.kfpx",
    "webcmyknews-cmyk": "GWG_WebCMYKNews_CMYK_2022.kfpx",
    "webcmyknews-cmyk-plus-rgb": "GWG_WebCMYKNews_CMYK_RGB_2022.kfpx",
    "packaging-offset": "GWG_PackagingOffset_2022.kfpx",
    "packaging-gravure": "GWG_PackagingGravure_2022.kfpx",
    "packaging-flexo": "GWG_PackagingFlexo_2022.kfpx",
    "label-leaflet": "GWG_LabelLeaflet_2022.kfpx",
    "folding-carton-corrugated-box": "GWG_FoldingCartonCorrugatedBox_2022.kfpx",
    "flexible": "GWG_Flexible_2022.kfpx",
    "corrugated-display": "GWG_CorrugatedDisplay_2022.kfpx",
    "digital-print": "GWG_DigitalPrint_2022.kfpx",
    "large-format-print": "GWG_LargeFormatPrint_2022.kfpx",
}


class PdfToolboxRunner(Runner):
    name = "pdftoolbox"
    binary_name = "pdfToolbox"

    def engine_version(self) -> str:
        binary = self.binary_path()
        code, stdout, stderr = self._run_subprocess([binary, "--version"], timeout=15)
        if code != 0:
            raise RunnerError(f"pdfToolbox --version exited {code}: {stderr.strip()}")
        return stdout.strip().split("\n")[0]

    def _profile_path(self, variant_kebab: str) -> Path:
        filename = _DEFAULT_PROFILE_NAMES.get(variant_kebab)
        if filename is None:
            raise RunnerError(f"No pdfToolbox profile mapping for variant {variant_kebab!r}")
        profile_dir = Path(
            os.environ.get(
                "ASSAY_PDFTOOLBOX_PROFILE_DIR",
                str(Path.home() / "Library" / "Application Support" / "callas software" / "pdfToolbox" / "Profiles"),
            )
        )
        path = profile_dir / filename
        if not path.exists():
            raise RunnerError(
                f"pdfToolbox profile not found: {path}. "
                f"Install GWG 2022 profiles or set ASSAY_PDFTOOLBOX_PROFILE_DIR."
            )
        return path

    def run(self, pdf_path: Path, variant_kebab: str) -> EngineResult:
        binary = self.binary_path()
        profile = self._profile_path(variant_kebab)

        report_path = pdf_path.parent / f".pdftoolbox-{pdf_path.stem}.json"
        args = [
            binary,
            "--analyze",
            f"--report=JSON,Path={report_path}",
            "--profile", str(profile),
            str(pdf_path),
        ]

        start = time.monotonic()
        code, stdout, stderr = self._run_subprocess(args, timeout=120)
        runtime_ms = int((time.monotonic() - start) * 1000)

        if not report_path.exists():
            raise RunnerError(
                f"pdfToolbox report missing at {report_path}; exit={code}, stderr={stderr.strip()[:200]}"
            )

        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        finally:
            report_path.unlink(missing_ok=True)

        hits: list[RuleHit] = []
        for issue in report.get("hits", []) or report.get("issues", []):
            severity_raw = str(issue.get("severity", "error"))
            message = str(issue.get("message", "")).strip()
            location = issue.get("location") or (
                f"page {issue['page']}" if "page" in issue else None
            )
            rule_id = self.map_message_to_rule(message)
            hits.append(
                RuleHit(
                    rule_id=rule_id,
                    severity=self._coerce_severity(severity_raw),
                    message=message,
                    location=location,
                    raw=issue if isinstance(issue, dict) else {},
                )
            )

        return EngineResult(
            engine=self.name,
            engine_version=self.engine_version(),
            profile=variant_kebab,
            file=str(pdf_path),
            hits=hits,
            runtime_ms=runtime_ms,
            raw_output=stdout[-500:] if stdout else None,
        )
