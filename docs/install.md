---
title: "Installing AssayPDF"
description: "Prerequisites for AssayPDF: Python with uv, system binaries (ghostscript, qpdf, mupdf-tools, exiftool, imagemagick, verapdf), and optional preflight engines for benchmarking."
group: "Getting started"
order: 2
---

# Installing AssayPDF

Prerequisites and initial setup. For the end-to-end workflow once you're installed, see [usage.md](usage.md).

## Prerequisites

### Python + uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

uv fetches Python 3.12, installs all dependencies, and creates `.venv/` on `uv sync`. About 30 seconds on a fresh machine.

### System binaries

AssayPDF shells out to several PDF and imaging tools at runtime: `ghostscript`, `qpdf`, `mupdf-tools` (`mutool`), `exiftool`, `imagemagick`, and `verapdf`.

#### macOS

```bash
brew install ghostscript qpdf mupdf-tools exiftool imagemagick
```

veraPDF is not in core Homebrew. Install via the headless installer:

```bash
cd /tmp
curl -L -o verapdf-installer.zip https://software.verapdf.org/rel/verapdf-installer.zip
unzip -o verapdf-installer.zip
# Follow on-screen prompts or use the auto-install XML approach in scripts/bootstrap.sh
```

#### Linux

```bash
sudo apt-get install ghostscript qpdf mupdf-tools libimage-exiftool-perl imagemagick
# verapdf: same headless installer as macOS
```

#### Verify

```bash
just check-deps
```

Prints a check or cross for each binary.

### Preflight engine (only for `assay benchmark`)

You only need an engine if you plan to run `assay benchmark`. Generation, validation, and reporting work without one.

| Engine | Status | License | Notes |
|---|---|---|---|
| callas pdfToolbox | working | trial or commercial | CLI invocation |
| Enfocus PitStop Server | working | trial or commercial | CLI invocation |
| lintPDF | stub | — | API not yet published; runner is scaffolded |

Engine-specific env vars (set before `assay benchmark`):

```bash
export ASSAY_PDFTOOLBOX_PROFILE_DIR="$HOME/Library/Application Support/callas software/pdfToolbox/Profiles"
export ASSAY_PITSTOP_PROFILE_DIR="$HOME/Library/Application Support/Enfocus/PitStop Server/Preflight Profiles"
```

## Clone and sync

```bash
git clone https://github.com/thinkneverland/assay-pdf.git
cd assay-pdf
uv sync --all-extras
```

That's it. Continue with the [usage walkthrough](usage.md).

## Optional: ICC profile setup

For variant-specific colorimetry, install Adobe ICC Profiles. Without these, AssayPDF falls back to a generic CMYK profile which is structurally valid but not the spec-recommended ICC for any specific variant. Details in [reproducing.md](reproducing.md#optional-icc-profile-setup).
