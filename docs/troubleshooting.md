---
title: "Troubleshooting"
description: "Common errors when running assay commands and how to fix them: missing engines, verapdf failures, checksum mismatches, unknown variant kebabs, and empty score reports."
group: "Reference"
order: 8
---

# Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `assay: command not found` | Run via `uv run assay …` (the entry point lives in the project venv, not your global PATH). |
| `Engine not available — …` (exit 2 from `benchmark`) | The engine binary is not on `PATH`. Install pdfToolbox / PitStop, or set the engine-specific env var (`ASSAY_PDFTOOLBOX_PROFILE_DIR`, `ASSAY_PITSTOP_PROFILE_DIR`). See [reproducing.md](reproducing.md). |
| `assay validate` fails with verapdf errors | Confirm `verapdf` is on `PATH` (`verapdf --version`). On macOS use the [headless installer](https://software.verapdf.org/rel/verapdf-installer.zip); brew core does not ship it. Use `--schema-only` to skip verapdf and isolate manifest issues. |
| `assay fetch` aborts with checksum mismatch | The upstream GWG asset moved or changed. Re-run with `--force` to redownload; if the mismatch persists, compare against `vendor/checksums.json` and open an issue. |
| `assay generate` produces a different SHA-256 than the manifest | Check Python and dependency versions (`uv sync --all-extras`). Generation is deterministic per `(seed, code, deps)` — diverging deps will diverge bytes. |
| `Unknown variant kebab` from `--profile` | Variant kebab names are listed in [`src/assay_pdf/generator/variants.py`](../src/assay_pdf/generator/variants.py). Note they are condensed (e.g. `sheetcmyk-cmyk`, not `sheet-cmyk-cmyk`). See [cli.md](cli.md#variant-kebabs). |
| `assay report` shows zero rows | No `*.score.json` in `results/`. Run `assay benchmark` first; the report aggregates whatever score files are present. |
| Missing system binary (mutool, ghostscript, etc.) | Run `just check-deps` to see what's missing, then install via brew/apt as in [install.md](install.md#system-binaries). |

For deeper debugging, re-run any command with the global `-v` / `--verbose` flag to enable DEBUG logging.

See also [known-quirks.md](known-quirks.md) for documented spec edge cases and engine-specific behaviors.
