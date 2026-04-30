# AssayPDF — task runner
# Usage: `just <task>` (install: brew install just)
# List all tasks: `just --list`

# Default — show available tasks
default:
    @just --list

# ─── Setup ──────────────────────────────────────────────────────────────────────

# Install all deps + Python 3.12 via uv
install:
    uv sync --all-extras

# Install pre-commit hooks
hooks:
    uv run pre-commit install

# Verify all required external binaries are present
check-deps:
    @echo "Checking required binaries..."
    @command -v gs >/dev/null 2>&1 && echo "  ghostscript ✓" || echo "  ghostscript ✗"
    @command -v qpdf >/dev/null 2>&1 && echo "  qpdf ✓" || echo "  qpdf ✗"
    @command -v mutool >/dev/null 2>&1 && echo "  mutool ✓" || echo "  mutool ✗"
    @command -v exiftool >/dev/null 2>&1 && echo "  exiftool ✓" || echo "  exiftool ✗"
    @command -v magick >/dev/null 2>&1 && echo "  imagemagick ✓" || echo "  imagemagick ✗"
    @command -v verapdf >/dev/null 2>&1 && echo "  verapdf ✓" || echo "  verapdf ✗"

# ─── AssayPDF lifecycle ────────────────────────────────────────────────────────

# Download GWG vendor assets (~183 MB)
fetch:
    uv run assay fetch

# Parse spec/gwg-2022-spec.xlsx → spec/requirement-ids.json
ingest:
    uv run assay ingest

# Generate the 175-file PDF corpus
generate:
    uv run assay generate

# Run an engine against the corpus (e.g. `just bench pdftoolbox sheet-cmyk-cmyk`)
bench engine profile:
    uv run assay benchmark --engine {{engine}} --profile {{profile}}

# Render scoreboard from results/
report format="md":
    uv run assay report --format {{format}}

# Validate every corpus PDF passes verapdf PDF/X-4
validate:
    uv run assay validate

# Full local cycle: ingest → generate → validate
build: ingest generate validate

# ─── Quality ────────────────────────────────────────────────────────────────────

# Run tests
test:
    uv run pytest

# Run tests with coverage
test-cov:
    uv run pytest --cov=assay_pdf --cov-report=term-missing

# Lint
lint:
    uv run ruff check .

# Format
fmt:
    uv run ruff format .

# Type check
typecheck:
    uv run mypy src

# All quality checks
check: lint typecheck test

# ─── Release ────────────────────────────────────────────────────────────────────

# Bump version (e.g. `just bump-version 0.2.0`)
bump-version version:
    @sed -i '' 's/version = "[^"]*"/version = "{{version}}"/' pyproject.toml
    @sed -i '' 's/__version__ = "[^"]*"/__version__ = "{{version}}"/' src/assay_pdf/__init__.py
    @echo "Bumped to {{version}}. Update CHANGELOG.md, then: git tag v{{version}}"

# Clean build artifacts
clean:
    rm -rf build/ dist/ *.egg-info/
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
