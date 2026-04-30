"""Enfocus PitStop Server CLI runner.

PitStop Server CLI invocation:
    pitstopserver --preflight=<profile> --output=<dir> --xml-report=<report> <pdf>

Output: XML report with <issue> elements containing severity/message/page.

Profile mapping: maps GWG variant kebab → PitStop preflight profile (.ppp file).
Locations vary by install; users override via env var ``ASSAY_PITSTOP_PROFILE_DIR``.
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from xml.etree import ElementTree as ET

from assay_pdf.harness.runners.base import Runner, RunnerError
from assay_pdf.logging import get_logger
from assay_pdf.models import EngineResult, RuleHit

log = get_logger(__name__)


_DEFAULT_PROFILE_NAMES: dict[str, str] = {
    "magazine-ads-cmyk": "Ghent PDF Workgroup 2022 - Magazine Ads CMYK.ppp",
    "magazine-ads-cmyk-plus-rgb": "Ghent PDF Workgroup 2022 - Magazine Ads CMYK + RGB.ppp",
    "newspaper-ads-cmyk": "Ghent PDF Workgroup 2022 - Newspaper Ads CMYK.ppp",
    "newspaper-ads-cmyk-plus-rgb": "Ghent PDF Workgroup 2022 - Newspaper Ads CMYK + RGB.ppp",
    "sheetcmyk-cmyk": "Ghent PDF Workgroup 2022 - SheetCMYK CMYK.ppp",
    "sheetcmyk-cmyk-plus-rgb": "Ghent PDF Workgroup 2022 - SheetCMYK CMYK + RGB.ppp",
    "sheetspot-cmyk": "Ghent PDF Workgroup 2022 - SheetSpot CMYK.ppp",
    "sheetspot-cmyk-plus-rgb": "Ghent PDF Workgroup 2022 - SheetSpot CMYK + RGB.ppp",
    "webcmyk-cmyk": "Ghent PDF Workgroup 2022 - WebCMYK CMYK.ppp",
    "webcmyk-cmyk-plus-rgb": "Ghent PDF Workgroup 2022 - WebCMYK CMYK + RGB.ppp",
    "webspot-cmyk": "Ghent PDF Workgroup 2022 - WebSpot CMYK.ppp",
    "webspot-cmyk-plus-rgb": "Ghent PDF Workgroup 2022 - WebSpot CMYK + RGB.ppp",
    "webcmyknews-cmyk": "Ghent PDF Workgroup 2022 - WebCMYKNews CMYK.ppp",
    "webcmyknews-cmyk-plus-rgb": "Ghent PDF Workgroup 2022 - WebCMYKNews CMYK + RGB.ppp",
    "packaging-offset": "Ghent PDF Workgroup 2022 - Packaging Offset.ppp",
    "packaging-gravure": "Ghent PDF Workgroup 2022 - Packaging Gravure.ppp",
    "packaging-flexo": "Ghent PDF Workgroup 2022 - Packaging Flexo.ppp",
    "label-leaflet": "Ghent PDF Workgroup 2022 - Label & Leaflet.ppp",
    "folding-carton-corrugated-box": "Ghent PDF Workgroup 2022 - Folding Carton & Corrugated Box.ppp",
    "flexible": "Ghent PDF Workgroup 2022 - Flexible.ppp",
    "corrugated-display": "Ghent PDF Workgroup 2022 - Corrugated Display.ppp",
    "digital-print": "Ghent PDF Workgroup 2022 - Digital Print.ppp",
    "large-format-print": "Ghent PDF Workgroup 2022 - Large Format Print.ppp",
}


class PitStopRunner(Runner):
    name = "pitstop"
    binary_name = "pitstopserver"

    def engine_version(self) -> str:
        binary = self.binary_path()
        code, stdout, stderr = self._run_subprocess([binary, "--version"], timeout=15)
        if code != 0:
            raise RunnerError(f"pitstopserver --version exited {code}: {stderr.strip()}")
        # Output typically: "PitStop Server 2024 update 1 (24.1.0)"
        match = re.search(r"PitStop Server[^\d]*([\d.]+)", stdout)
        return match.group(0) if match else stdout.strip().split("\n")[0]

    def _profile_path(self, variant_kebab: str) -> Path:
        filename = _DEFAULT_PROFILE_NAMES.get(variant_kebab)
        if filename is None:
            raise RunnerError(f"No PitStop profile mapping for variant {variant_kebab!r}")
        profile_dir = Path(
            os.environ.get(
                "ASSAY_PITSTOP_PROFILE_DIR",
                str(
                    Path.home()
                    / "Library"
                    / "Application Support"
                    / "Enfocus"
                    / "PitStop Server"
                    / "Preflight Profiles"
                ),
            )
        )
        path = profile_dir / filename
        if not path.exists():
            raise RunnerError(
                f"PitStop profile not found: {path}. "
                f"Install GWG 2022 .ppp profiles or set ASSAY_PITSTOP_PROFILE_DIR."
            )
        return path

    def run(self, pdf_path: Path, variant_kebab: str) -> EngineResult:
        binary = self.binary_path()
        profile = self._profile_path(variant_kebab)
        report_path = pdf_path.parent / f".pitstop-{pdf_path.stem}.xml"

        args = [
            binary,
            "--preflight",
            str(profile),
            "--xml-report",
            str(report_path),
            str(pdf_path),
        ]

        start = time.monotonic()
        code, stdout, stderr = self._run_subprocess(args, timeout=120)
        runtime_ms = int((time.monotonic() - start) * 1000)

        if not report_path.exists():
            raise RunnerError(
                f"PitStop report missing at {report_path}; exit={code}, stderr={stderr.strip()[:200]}"
            )

        try:
            tree = ET.parse(report_path)
        finally:
            report_path.unlink(missing_ok=True)

        hits: list[RuleHit] = []
        for issue in tree.iter("issue"):
            severity_raw = (issue.get("severity") or issue.findtext("severity") or "error").strip()
            message = (issue.findtext("message") or issue.text or "").strip()
            page_text = issue.get("page") or issue.findtext("page")
            location = f"page {page_text}" if page_text else None
            rule_id = self.map_message_to_rule(message)
            hits.append(
                RuleHit(
                    rule_id=rule_id,
                    severity=self._coerce_severity(severity_raw),
                    message=message,
                    location=location,
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
