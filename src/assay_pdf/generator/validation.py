"""verapdf wrapper + manifest schema validation."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from assay_pdf import models
from assay_pdf.logging import get_logger
from assay_pdf.models import CorpusManifest

log = get_logger(__name__)

VERAPDF_FLAVOUR = "4"  # PDF/X-4


def _verapdf_binary() -> str | None:
    return shutil.which("verapdf")


def verapdf_check(pdf_path: Path) -> tuple[bool, str]:
    """Run verapdf on a single file. Returns (passed, message)."""
    binary = _verapdf_binary()
    if binary is None:
        return False, "verapdf binary not found on PATH"
    try:
        result = subprocess.run(
            [binary, "-f", VERAPDF_FLAVOUR, "--format", "text", str(pdf_path)],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False, "verapdf timed out (60s)"
    output = (result.stdout + result.stderr).strip()
    passed = "PASS " in output or "compliant" in output.lower()
    return passed, output[:500]


def validate_corpus(*, schema_only: bool = False) -> list[tuple[str, str]]:
    """Validate corpus/manifest.json.

    With ``schema_only=True`` (used by CI): only checks that the manifest parses
    cleanly against the pydantic CorpusManifest schema. Does NOT check whether
    referenced PDF files exist on disk — they're gitignored and regenerated on
    demand via `assay generate`.

    With ``schema_only=False`` (used locally after `assay generate`): also
    verifies each PDF exists and passes verapdf PDF/X-4 validation.

    Returns a list of (path, error_message). Empty list = all good.
    """
    repo = models.repo_root()
    manifest_path = repo / "corpus" / "manifest.json"
    if not manifest_path.exists():
        return [(str(manifest_path), "manifest missing — run `assay generate` first")]

    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    # If pydantic validation fails, model_validate raises — caught at CLI boundary.
    manifest = CorpusManifest.model_validate(raw)

    if schema_only:
        return []

    failures: list[tuple[str, str]] = []
    for entry in manifest.files:
        pdf_path = repo / entry.path
        if not pdf_path.exists():
            failures.append((entry.path, "file missing — run `assay generate` first"))
            continue
        passed, msg = verapdf_check(pdf_path)
        if not passed:
            failures.append((entry.path, f"verapdf: {msg}"))

    return failures
