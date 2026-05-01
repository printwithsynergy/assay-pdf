# Usage walkthrough

End-to-end: fetch → generate → benchmark → report → validate. For installation, see [install.md](install.md). For per-flag CLI detail, see [cli.md](cli.md). For common errors, see [troubleshooting.md](troubleshooting.md).

## 1. Fetch vendor assets

```bash
uv run assay fetch                # add --force to re-download even if checksums match
```

Downloads the GWG 2022 spec docs, GOS 5.0 suites, and the Processing Steps Test Suite into `vendor/`. Each download is verified against `vendor/checksums.json` (SHA-256). Skipped on subsequent runs unless `--force` is passed.

## 2. Generate the corpus

```bash
uv run assay generate                                 # all 175 files
uv run assay generate --only-rule R0014               # just R0014 negatives
uv run assay generate --only-variant sheetcmyk-cmyk   # just one variant
uv run assay generate --seed 42                       # alternate deterministic seed
```

Writes PDFs into `corpus/positive/` and `corpus/negative/`, plus `corpus/manifest.json` (per-file SHA-256 and expected outcome). Variant kebab names live in `src/assay_pdf/generator/variants.py`.

## 3. Benchmark an engine

```bash
uv run assay benchmark --engine pdftoolbox            # run all variants
uv run assay benchmark --engine pitstop --profile webcmyk-cmyk
uv run assay benchmark --engine lintpdf               # stub — emits warnings until the API ships
```

Each run writes both raw `EngineResult` JSON and a confusion-matrix `*.score.json` to `results/`. Engine selection requires the engine binary on `PATH` (or pointed to via env var — see [reproducing.md](reproducing.md)). Exits **2** with a clear message if the runner isn't installed.

Aggregate output looks like:

```
✓ pdftoolbox score: TP=143 FP=2 FN=7 TN=3045 (12834ms aggregate runtime)
```

## 4. Render a report

```bash
uv run assay report --format md > REPORT.md
uv run assay report --format html --output REPORT.html
```

`assay report` aggregates **every** `results/*.score.json` it finds, so to compare engines run `assay benchmark` once per engine before rendering.

## 5. (Optional) Validate

```bash
uv run assay validate                # full verapdf PDF/X-4 walk
uv run assay validate --schema-only  # skip verapdf; check schemas only
```

Used in CI on every commit. Exits **1** if any corpus PDF fails verapdf.

## Convenience shortcuts (Justfile)

```bash
just install                          # uv sync --all-extras
just check-deps                       # verify ghostscript/qpdf/mutool/exiftool/imagemagick/verapdf
just build                            # ingest → generate → validate
just bench pdftoolbox sheetcmyk-cmyk  # uv run assay benchmark --engine ... --profile ...
just report md                        # uv run assay report --format md
```

Run `just --list` for the full task list.
