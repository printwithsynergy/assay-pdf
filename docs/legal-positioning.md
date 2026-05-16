---
title: "Legal positioning"
description: "AssayPDF's legal posture: comparative-quality benchmarking under nominative fair use, no vendor redistribution, AGPL-3.0-or-later licensing, and trial-license benchmarking guidance."
group: "Project"
order: 10
---

# Legal positioning

AssayPDF is comparative-quality benchmarking. This document captures the legal posture so the project can ship and grow without surprises.

## Posture

1. **Open source benchmark, not a product certification.** AssayPDF measures conformance to a publicly-documented spec (GWG 2022). It does not certify any engine as compliant with the spec or with anything else. It is not affiliated with the Ghent Workgroup, with Enfocus, with callas software, or with any of the engines benchmarked.
2. **Reproducibility = legal armor.** Every claim is reproducible by anyone with the same engine licenses. AssayPDF doesn't ship benchmark numbers as authoritative; it ships a methodology and a tool, plus example numbers gathered locally with documented engine versions and corpus versions.
3. **Nominative fair use.** Engine names (PitStop, pdfToolbox, lintPDF) are used only to identify the products being benchmarked. No suggestion of endorsement is made or implied.
4. **No redistribution of vendor copyright.** GWG 2022 spec materials, GOS 5.0 suites, Processing Steps Test Suite — all fetched from official Ghent Workgroup endpoints with SHA-256 verification, never redistributed. The corpus AssayPDF generates is original work derived from the spec rules, not copies of any vendor's test files.

## What this means in practice

### Running benchmarks

You're free to:
- Generate the corpus locally.
- Run benchmarks against engines you've licensed.
- Publish your numbers, with engine version + corpus version + your hardware noted.

You are not free to:
- Distribute the GWG 2022 spec workbook independently of AssayPDF (GWG retains copyright).
- Distribute commercial engine output independently of your own license terms (PitStop and pdfToolbox EULAs are between you and the vendor).
- Claim AssayPDF certifies an engine — it doesn't.

### Publishing comparisons

When publishing AssayPDF-derived comparisons, include:
- Corpus version (from `corpus/manifest.json`)
- Engine versions (from `results/<engine>-*.score.json`)
- AssayPDF version
- Hardware notes if performance metrics are included
- This disclaimer:

> _Benchmark generated with [AssayPDF](https://github.com/thinkneverland/assay-pdf). AssayPDF measures structural conformance to the GWG 2022 specification and is not affiliated with the Ghent Workgroup, [Engine A], or [Engine B]. Engine names are used only to identify the products tested under nominative fair use._

## License posture

- **AssayPDF source code**: AGPL-3.0-or-later — see `LICENSE`.
- **ICC profiles in `src/assay_pdf/generator/icc/`**: redistributed under each profile's upstream terms (sRGB IEC61966-2.1 = public domain; AdobeRGB1998 = Adobe ICC EULA, freely distributable).
- **GWG 2022 spec materials in `spec/`**: copyright Ghent Workgroup. Treated as reference material under fair use for a derivative tool that implements the spec — same way an OS implementer treats ISO 32000.
- **Vendor presets in `spec/presets/`** (Adobe, Enfocus, callas): each vendor's GWG presets are distributed publicly by the vendor for use in their products. Redistributed here as reference material; if a vendor's terms change, we move that file to the `assay fetch` flow.

If a vendor has objections to inclusion of their preset bundle as committed reference material, file an issue and we'll move it to fetch-on-demand within 7 days.

## Trial license usage

Benchmarks against PitStop Server and pdfToolbox typically use the vendor's free trial license for an initial evaluation. Trial license use for comparative benchmarking falls under each vendor's standard EULA, which permits reasonable evaluation including comparison to alternatives. If your jurisdiction interprets the EULAs differently, run AssayPDF only against engines you have full commercial licenses for.

## Contact

If you have a legal concern about AssayPDF's posture or a specific use, file an issue or email iam@quincy.codes (Quincy Brooks, Think Neverland).
