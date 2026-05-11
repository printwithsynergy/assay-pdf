# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial scaffold (Commit 1): pyproject.toml (uv-managed, Python 3.12+), LICENSE (MIT), README, CHANGELOG, CONTRIBUTING, tooling configs, CI workflows, issue/PR templates.
- Project governance docs: `SECURITY.md` (vulnerability reporting policy), `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1), `SUPPORT.md` (where to ask for help), a feature-request issue template, and `ISSUE_TEMPLATE/config.yml` routing security and questions to the right channels.

## [0.1.0] — TBD

### Added
- Spec ingestion: parser for GWG 2022 multi-tab workbook → `requirement-ids.json` machine-readable manifest.
- Vendor asset fetcher: SHA-256-verified downloads of GWG 2022 spec docs + GOS 5.0 suites + Processing Steps Test Suite v1.
- Deterministic corpus generator: 175-file PDF/X-4 corpus across 39 GWG 2022 rules and 23 variants. Byte-identical reproducibility from a seed.
- Harness with three engine runners: callas pdfToolbox, Enfocus PitStop Server, lintPDF (stub).
- Per-rule, per-variant, per-engine scorer producing markdown and HTML accuracy reports.
- `verapdf` PDF/X-4 validation as part of `assay validate`.
- ICC profile bundle: GRACoL2013, FOGRA39, FOGRA51, sRGB IEC61966-2.1, AdobeRGB1998 (redistributed under upstream terms).
