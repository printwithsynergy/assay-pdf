# AssayPDF

> Open-source GWG 2022 conformance assay for PDF preflight engines.

[![CI](https://github.com/thinkneverland/assay-pdf/actions/workflows/ci.yml/badge.svg)](https://github.com/thinkneverland/assay-pdf/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Spec: GWG 2022](https://img.shields.io/badge/spec-GWG%202022-orange.svg)](https://gwg.org/technical-specifications/gwg-2022-specifications/)

## What this is

AssayPDF is a benchmark kit that:

1. **Generates** a deterministic PDF test corpus (~175 files) derived from the [Ghent Workgroup 2022 Specification](https://gwg.org/technical-specifications/gwg-2022-specifications/) — every file targets exactly one of the 39 rules in the spec, across all 23 GWG 2022 variants.
2. **Runs** that corpus against any preflight engine — lintPDF, Enfocus PitStop Server, callas pdfToolbox — through a uniform harness.
3. **Scores** TP / FP / FN / TN per rule, per variant, per engine, and produces reproducible markdown + HTML accuracy reports.

## Why this exists

The [GWG 2015 Compliancy Test Suite](https://gwg.org/) is gated to GWG vendor members. The GWG 2022 spec ships with no public test corpus at all. AssayPDF closes that gap so anyone can self-benchmark a preflight engine without paying for vendor membership.

It also doubles as the credibility layer for **lintPDF** (Think Neverland's PDF preflight SaaS, currently in private development) — published accuracy comparisons against incumbents that none of those incumbents publish themselves.

## Quick start

### Prerequisites

- **Python 3.12+** and [uv](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **System binaries** — `ghostscript`, `qpdf`, `mupdf-tools` (mutool), `exiftool`, `imagemagick`, `verapdf`
  - macOS: `brew install ghostscript qpdf mupdf-tools exiftool imagemagick` (verapdf via [headless installer](https://software.verapdf.org/rel/verapdf-installer.zip))
  - Linux: `sudo apt-get install ghostscript qpdf mupdf-tools libimage-exiftool-perl imagemagick` (same verapdf installer)
  - Verify with `just check-deps`
- **At least one preflight engine** — pdfToolbox, PitStop Server, or lintPDF (only needed for `assay benchmark`)

### Install and run

```bash
git clone https://github.com/thinkneverland/assay-pdf.git
cd assay-pdf
uv sync --all-extras                                      # install deps + Python 3.12 (~30s on a fresh machine)
uv run assay fetch                                        # download GWG vendor assets (~183 MB) into vendor/
uv run assay generate                                     # build the 175-file PDF/X-4 corpus into corpus/
uv run assay validate                                     # verify every PDF passes verapdf
uv run assay benchmark --engine pdftoolbox --profile sheetcmyk-cmyk
uv run assay report --format md > REPORT.md
```

A complete end-to-end walkthrough (engine config, ICC setup, reproducing a published score) lives in [docs/reproducing.md](docs/reproducing.md).

## What you get

```
corpus/
├── manifest.json          # every file's expected outcome, rule mapping, sha256
├── positive/              # 23 PDFs — one per GWG 2022 variant — pass every applicable rule
└── negative/              # 152 PDFs — each targeting one rule's failure mode cleanly
```

Every PDF passes `verapdf` PDF/X-4 validation (or has documented exception in the manifest). Every PDF is generated deterministically — same code, same seed, byte-identical output.

## Usage

### 1. Fetch vendor assets

```bash
uv run assay fetch                # add --force to re-download even if checksums match
```

Downloads the GWG 2022 spec docs, GOS 5.0 suites, and the Processing Steps Test Suite into `vendor/`. Each download is verified against `vendor/checksums.json` (SHA-256). Skipped on subsequent runs unless `--force` is passed.

### 2. Generate the corpus

```bash
uv run assay generate                                 # all 175 files
uv run assay generate --only-rule R0014               # just R0014 negatives
uv run assay generate --only-variant sheetcmyk-cmyk   # just one variant
uv run assay generate --seed 42                       # alternate deterministic seed
```

Writes PDFs into `corpus/positive/` and `corpus/negative/`, plus `corpus/manifest.json` (per-file SHA-256 and expected outcome). Variant kebab names live in `src/assay_pdf/generator/variants.py`.

### 3. Benchmark an engine

```bash
uv run assay benchmark --engine pdftoolbox            # run all variants
uv run assay benchmark --engine pitstop --profile webcmyk-cmyk
uv run assay benchmark --engine lintpdf               # stub — emits warnings until the API ships
```

Each run writes both raw `EngineResult` JSON and a confusion-matrix `*.score.json` to `results/`. Engine selection requires the engine binary on `PATH` (or pointed to via env var — see [docs/reproducing.md](docs/reproducing.md)). Exits **2** with a clear message if the runner isn't installed.

Aggregate output looks like:

```
✓ pdftoolbox score: TP=143 FP=2 FN=7 TN=3045 (12834ms aggregate runtime)
```

### 4. Render a report

```bash
uv run assay report --format md > REPORT.md
uv run assay report --format html --output REPORT.html
```

`assay report` aggregates **every** `results/*.score.json` it finds, so to compare engines run `assay benchmark` once per engine before rendering.

### 5. (Optional) Validate

```bash
uv run assay validate                # full verapdf PDF/X-4 walk
uv run assay validate --schema-only  # skip verapdf; check schemas only
```

Used in CI on every commit. Exits **1** if any corpus PDF fails verapdf.

### Convenience shortcuts (Justfile)

```bash
just install                          # uv sync --all-extras
just check-deps                       # verify ghostscript/qpdf/mutool/exiftool/imagemagick/verapdf
just build                            # ingest → generate → validate
just bench pdftoolbox sheetcmyk-cmyk  # uv run assay benchmark --engine ... --profile ...
just report md                        # uv run assay report --format md
```

## CLI reference

All commands accept a global `-v` / `--verbose` flag for debug logging.

| Command | Flags | Behavior |
|---|---|---|
| `assay version` | — | Print AssayPDF version. |
| `assay fetch` | `--force` | Download vendor assets (GOS suites, Processing Steps Test Suite) into `vendor/` with SHA-256 verification. |
| `assay ingest` | `--xlsx PATH`, `--output PATH` | Parse `spec/gwg-2022-spec.xlsx` into `spec/requirement-ids.json`. |
| `assay generate` | `--only-rule ID`, `--only-variant KEBAB`, `--seed N` | Generate the PDF/X-4 corpus into `corpus/` deterministically. |
| `assay benchmark` | `--engine {pdftoolbox,pitstop,lintpdf}` (required), `--profile KEBAB` | Run an engine against the corpus and write `results/<engine>-<timestamp>.{json,score.json}`. Exits 2 if the runner isn't installed. |
| `assay report` | `--format {md,html}`, `--output PATH` | Render scoreboard aggregating every `results/*.score.json`. Writes to stdout unless `--output` is given. |
| `assay validate` | `--schema-only` | Validate every corpus PDF against verapdf PDF/X-4. Exits 1 on any failure. |

Engine names: `pdftoolbox` (callas), `pitstop` (Enfocus), `lintpdf` (stub until the API publishes).

Variant kebabs (one per GWG 2022 variant) are listed in `src/assay_pdf/generator/variants.py` — e.g. `sheetcmyk-cmyk`, `webcmyk-cmyk-plus-rgb`, `packaging-flexo`, `digital-print`.

## Coverage

| Spec area | Rule IDs | Negatives |
|---|---|---|
| Page geometry | R0001–R0006 | 13 |
| Overprint | R0007–R0013 | 7 |
| Fonts | R0014 | 3 |
| Black, registration | R0015–R0019 | 6 |
| Spot colors | R0020–R0024 | 7 |
| Total ink coverage | R0025–R0026 | 6 |
| Color space binding | R0027–R0030 | 9 |
| Image resolution | R0031–R0033 | 6 |
| Optional content | R0034, R0036 | 3 |
| Output intent | R0035 | 3 |
| Sign/display scaling | R0037 | 2 |
| Processing steps | R1001–R1002 | 2 |
| Boundary stress (v0.1.0) | (across all rules) | +85 |

Plus 23 positive baselines, one per variant.

## Engine support

| Engine | Status | Notes |
|---|---|---|
| callas pdfToolbox | working | Trial license; CLI invocation |
| Enfocus PitStop Server | working | Trial license; CLI invocation |
| lintPDF | stub | API not yet published; runner is scaffolded |

Adding an engine = implementing one `Runner` subclass and a `rule_maps/<engine>.json` mapping. See [docs/methodology.md](docs/methodology.md).

## Reproducibility

This is not a one-off study. Every claim AssayPDF makes is reproducible:

- Spec assets fetched from GWG canonical URLs with SHA-256 verification (`vendor/checksums.json`)
- Corpus generated deterministically from a seed; manifest records expected SHA-256 per file
- CI runs `assay validate` on every commit
- A weekly cron job verifies all upstream URLs are still alive

Anyone with the same engine versions and licenses can run AssayPDF and reproduce the published accuracy numbers byte-for-byte.

## Legal posture

AssayPDF **never redistributes** GWG copyrighted materials. Vendor assets (GOS 5.0 suites, processing-steps test suite) are fetched from the official GWG endpoints. The corpus AssayPDF generates is original work derived from spec rules, not copies of the GWG 2015 test suite.

See [docs/legal-positioning.md](docs/legal-positioning.md) for the comparative-advertising / nominative-fair-use stance.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `assay: command not found` | Run via `uv run assay …` (the entry point lives in the project venv, not your global PATH). |
| `Engine not available — …` (exit 2 from `benchmark`) | The engine binary is not on `PATH`. Install pdfToolbox / PitStop, or set the engine-specific env var (`ASSAY_PDFTOOLBOX_PROFILE_DIR`, `ASSAY_PITSTOP_PROFILE_DIR`). See [docs/reproducing.md](docs/reproducing.md). |
| `assay validate` fails with verapdf errors | Confirm `verapdf` is on `PATH` (`verapdf --version`). On macOS use the [headless installer](https://software.verapdf.org/rel/verapdf-installer.zip); brew core does not ship it. Use `--schema-only` to skip verapdf and isolate manifest issues. |
| `assay fetch` aborts with checksum mismatch | The upstream GWG asset moved or changed. Re-run with `--force` to redownload; if the mismatch persists, compare against `vendor/checksums.json` and open an issue. |
| `assay generate` produces a different SHA-256 than the manifest | Check Python and dependency versions (`uv sync --all-extras`). Generation is deterministic per `(seed, code, deps)` — diverging deps will diverge bytes. |
| `Unknown variant kebab` from `--profile` | Variant kebab names are listed in `src/assay_pdf/generator/variants.py`. Note they are condensed (e.g. `sheetcmyk-cmyk`, not `sheet-cmyk-cmyk`). |
| `assay report` shows zero rows | No `*.score.json` in `results/`. Run `assay benchmark` first; the report aggregates whatever score files are present. |
| Missing system binary (mutool, ghostscript, etc.) | Run `just check-deps` to see what's missing, then install via brew/apt as in [Prerequisites](#prerequisites). |

For deeper debugging, re-run any command with the global `-v` / `--verbose` flag to enable DEBUG logging.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). New rule generators, new engine runners, and new boundary-case test files are all welcome.

## License

MIT — see [LICENSE](LICENSE).

ICC profiles bundled under `src/assay_pdf/generator/icc/` are redistributed under their respective upstream terms; see [src/assay_pdf/generator/icc/README.md](src/assay_pdf/generator/icc/README.md).

## Sister projects

Think Neverland's PDF tooling family:

- **lintPDF** — API-first PDF preflight SaaS this benchmark validates against. Private during development; integration runner ships when the API is published.
- **[sift-pdf](https://github.com/thinkneverland/sift-pdf)** — open-source PDF preflight engine. AssayPDF will benchmark sift-pdf alongside the commercial incumbents once a runner lands.
- **loupe-pdf** — open-source interactive PDF viewer. Public release coming soon.
