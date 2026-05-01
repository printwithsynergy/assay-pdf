# CLI reference

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

## Engine names

- `pdftoolbox` — callas pdfToolbox
- `pitstop` — Enfocus PitStop Server
- `lintpdf` — stub until the lintPDF API publishes

## Variant kebabs

One per GWG 2022 variant. Listed in [`src/assay_pdf/generator/variants.py`](../src/assay_pdf/generator/variants.py). Examples:

- `sheetcmyk-cmyk`, `sheetcmyk-cmyk-plus-rgb`
- `webcmyk-cmyk`, `webcmyk-cmyk-plus-rgb`
- `webcmyknews-cmyk`, `webcmyknews-cmyk-plus-rgb`
- `magazine-ads-cmyk`, `magazine-ads-cmyk-plus-rgb`
- `newspaper-ads-cmyk`, `newspaper-ads-cmyk-plus-rgb`
- `sheetspot-cmyk`, `sheetspot-cmyk-plus-rgb`
- `webspot-cmyk`, `webspot-cmyk-plus-rgb`
- `packaging-offset`, `packaging-gravure`, `packaging-flexo`
- `label-leaflet`, `folding-carton-corrugated-box`, `flexible`, `corrugated-display`
- `digital-print`, `large-format-print`

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | `assay validate` found at least one corpus PDF that fails verapdf |
| 2 | `assay benchmark` couldn't find the engine runner; or `assay report --format` got an unknown format |
