import json
from pathlib import Path

from assay_pdf.harness.runners.lintpdf import LintPDFRunner


def test_lint_runner_maps_codex_cluster_payload(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\n")

    payload = {
        "findings": [
            {
                "inspection_id": "LPDF_GEO_001",
                "severity": "warning",
                "message": "Trim mismatch",
                "page_num": 1,
                "bbox": [10.12549, 20.2, 30.3, 40.4],
            },
            {
                "severity": "error",
                "message": "No trim metadata found",
                "page_num": 2,
            },
        ]
    }

    runner = LintPDFRunner()
    runner.binary_path = lambda: "lint-pdf"  # type: ignore[method-assign]
    runner._run_subprocess = lambda *args, **kwargs: (  # type: ignore[method-assign]
        0,
        json.dumps(payload),
        "",
    )

    result = runner.run(pdf_path, "any-variant")
    assert result.engine == "lintpdf"
    assert result.hits[0].rule_id == "LPDF_GEO_001"
    assert result.hits[0].location == "page:1;bbox:10.125,20.2,30.3,40.4"
    assert result.hits[1].location == "page:2"
