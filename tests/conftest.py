"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from assay_pdf.models import repo_root


@pytest.fixture(scope="session")
def repo() -> Path:
    """Repo root."""
    return repo_root()


@pytest.fixture(scope="session")
def spec_xlsx(repo: Path) -> Path:
    """Path to the committed GWG 2022 spec workbook."""
    p = repo / "spec" / "gwg-2022-spec.xlsx"
    if not p.exists():
        pytest.skip(
            f"Spec workbook missing at {p} — run `git pull` or check Commit 1 landed cleanly."
        )
    return p


@pytest.fixture
def fixtures_dir(repo: Path) -> Path:
    return repo / "tests" / "fixtures"
