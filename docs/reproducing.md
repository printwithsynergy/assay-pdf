---
title: "Reproducing AssayPDF"
description: "Step-by-step guide to running AssayPDF end-to-end on your machine, generating the corpus, running engine benchmarks, and reproducing a published accuracy score."
group: "Reference"
order: 7
---

# Reproducing AssayPDF

Step-by-step guide to running AssayPDF end-to-end on your machine and reproducing a published score.

## Prerequisites

### macOS

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

### Linux

```bash
sudo apt-get install ghostscript qpdf mupdf-tools libimage-exiftool-perl imagemagick
# verapdf: same headless installer as macOS
```

### Python + uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Clone + sync

```bash
git clone https://github.com/thinkneverland/assay-pdf.git
cd assay-pdf
uv sync --all-extras
```

uv will fetch Python 3.12, install all dependencies, and create `.venv/`. About 30 seconds on a fresh machine.

## Generate the corpus

```bash
uv run assay generate
```

Produces 62 PDFs in `corpus/`:
- 23 positives (one per variant)
- 39 negatives (21 concrete + 18 stubs documented for v0.1.1)
- `corpus/manifest.json` with SHA-256 of every file

The PDFs themselves are gitignored. They're regenerated deterministically from the manifest + the generator code.

## Optional: ICC profile setup

For variant-specific colorimetry, install Adobe ICC Profiles:

```bash
# macOS — install Adobe Acrobat or Photoshop, OR download Adobe ICC profiles directly
# from https://www.adobe.com/support/downloads/iccprofiles/iccprofiles_mac.html
```

Without these, AssayPDF falls back to macOS's `Generic CMYK Profile.icc`, which is structurally valid but not the spec-recommended ICC for any specific variant.

## Run a benchmark

### pdfToolbox (callas)

```bash
# Set path to your GWG 2022 profile directory if not the default
export ASSAY_PDFTOOLBOX_PROFILE_DIR="$HOME/Library/Application Support/callas software/pdfToolbox/Profiles"

uv run assay benchmark --engine pdftoolbox
```

### PitStop (Enfocus)

```bash
export ASSAY_PITSTOP_PROFILE_DIR="$HOME/Library/Application Support/Enfocus/PitStop Server/Preflight Profiles"

uv run assay benchmark --engine pitstop
```

### lintPDF

```bash
uv run assay benchmark --engine lintpdf
# Currently a stub — emits a warning per file. Real integration ships with lintPDF API.
```

Each benchmark writes:
- `results/<engine>-<timestamp>.json` — raw EngineResult per PDF
- `results/<engine>-<timestamp>.score.json` — confusion matrix per (rule, variant)

## Render the report

```bash
uv run assay report --format md > REPORT.md
uv run assay report --format html --output REPORT.html
```

The report aggregates every `*.score.json` in `results/`. To compare engines, run the benchmark for each, then re-render.

## Verify the corpus

```bash
uv run assay validate
```

Walks every PDF in `corpus/manifest.json` and verifies:
- The file exists.
- Its SHA-256 matches the manifest.
- It passes verapdf PDF/X-4 validation.

Failures are reported with the file path and the verapdf message. Used in CI on every push.

## Reproducing a published score

If a published comparison says "pdfToolbox 16.2 scored 78.3% F1 on corpus v0.1.0":

```bash
git checkout v0.1.0           # match corpus version
uv sync                        # match dependency versions
uv run assay generate          # build the same corpus
# Have pdfToolbox 16.2 installed (the version recorded in the published score)
uv run assay benchmark --engine pdftoolbox
uv run assay report --format md
```

The F1 should match within rounding (sub-0.5%). If it differs more than that, file an issue with both score JSONs.
