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

```bash
git clone https://github.com/thinkneverland/assay-pdf.git
cd assay-pdf
uv sync --all-extras                                      # install deps + Python 3.12
uv run assay fetch                                        # download GWG vendor assets (~183 MB)
uv run assay generate                                     # build the 175-file PDF/X-4 corpus
uv run assay validate                                     # verify every PDF passes verapdf
uv run assay benchmark --engine pdftoolbox --profile sheetcmyk-cmyk
uv run assay report --format md > REPORT.md
```

Detailed docs:

- [docs/install.md](docs/install.md) — prerequisites (Python+uv, system binaries, engines)
- [docs/usage.md](docs/usage.md) — end-to-end walkthrough (fetch → generate → benchmark → report → validate)
- [docs/cli.md](docs/cli.md) — per-command flags, exit codes, engine and variant kebab names
- [docs/troubleshooting.md](docs/troubleshooting.md) — common errors and fixes
- [docs/reproducing.md](docs/reproducing.md) — reproducing a published score

## What you get

```
corpus/
├── manifest.json          # every file's expected outcome, rule mapping, sha256
├── positive/              # 23 PDFs — one per GWG 2022 variant — pass every applicable rule
└── negative/              # 152 PDFs — each targeting one rule's failure mode cleanly
```

Every PDF passes `verapdf` PDF/X-4 validation (or has documented exception in the manifest). Every PDF is generated deterministically — same code, same seed, byte-identical output.

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

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). New rule generators, new engine runners, and new boundary-case test files are all welcome.

By participating in this project you agree to abide by the [Code of Conduct](CODE_OF_CONDUCT.md).

## Support and security

- Usage questions or bug reports: see [SUPPORT.md](SUPPORT.md).
- Security vulnerabilities: see [SECURITY.md](SECURITY.md) — please do **not** open a public issue.

## License

MIT — see [LICENSE](LICENSE).

ICC profiles bundled under `src/assay_pdf/generator/icc/` are redistributed under their respective upstream terms; see [src/assay_pdf/generator/icc/README.md](src/assay_pdf/generator/icc/README.md).

## Sister projects

Think Neverland's PDF tooling family:

- **lintPDF** — API-first PDF preflight SaaS this benchmark validates against. Private during development; integration runner ships when the API is published.
- **[sift-pdf](https://github.com/thinkneverland/sift-pdf)** — open-source PDF preflight engine. AssayPDF will benchmark sift-pdf alongside the commercial incumbents once a runner lands.
- **loupe-pdf** — open-source interactive PDF viewer. Public release coming soon.
