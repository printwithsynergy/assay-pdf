#!/usr/bin/env bash
# scripts/bootstrap.sh
#
# Set up an AssayPDF dev environment from a fresh clone:
# - Verifies required brew packages (macOS) or apt packages (Linux)
# - Installs Python 3.12 + dependencies via uv
# - Optionally fetches verapdf if missing
#
# Usage:
#   ./scripts/bootstrap.sh [--no-verapdf]

set -euo pipefail

SKIP_VERAPDF=0
for arg in "$@"; do
  case "$arg" in
    --no-verapdf) SKIP_VERAPDF=1 ;;
    *) echo "Unknown arg: $arg"; exit 1 ;;
  esac
done

OS="$(uname -s)"

# ─── External binaries ────────────────────────────────────────────────────────

REQUIRED=(gs qpdf mutool exiftool magick)
MISSING=()
for bin in "${REQUIRED[@]}"; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    MISSING+=("$bin")
  fi
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo "Missing binaries: ${MISSING[*]}"
  if [[ "$OS" == "Darwin" ]]; then
    echo "Run: brew install ghostscript qpdf mupdf-tools exiftool imagemagick"
  else
    echo "Run: sudo apt-get install ghostscript qpdf mupdf-tools libimage-exiftool-perl imagemagick"
  fi
  exit 1
fi

if [[ $SKIP_VERAPDF -eq 0 ]] && ! command -v verapdf >/dev/null 2>&1; then
  echo "verapdf not found on PATH."
  echo "Download from https://software.verapdf.org/rel/verapdf-installer.zip"
  echo "Or pass --no-verapdf to skip this check."
  exit 1
fi

# ─── uv + Python ──────────────────────────────────────────────────────────────

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Installing..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

uv sync --all-extras
uv run pre-commit install || true

echo "✓ AssayPDF dev environment ready."
echo "Try: uv run assay generate"
