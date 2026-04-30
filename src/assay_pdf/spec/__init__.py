"""Spec ingestion — parsing the GWG 2022 XLSX into a typed manifest."""

from assay_pdf.spec.parser import parse_workbook

__all__ = ["parse_workbook"]
