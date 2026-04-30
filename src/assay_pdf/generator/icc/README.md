# ICC profiles

PDF/X-4 requires an output intent ICC profile. AssayPDF needs five for full GWG 2022
variant coverage. License terms split them into two tiers.

## Tier 1 — committed in this directory

| File | Source | License |
|---|---|---|
| `sRGB_IEC61966-2-1.icc` | W3C / IEC 61966-2-1 | Public domain |
| `AdobeRGB1998.icc` | Adobe Systems | Adobe ICC EULA — freely distributable |

Provenance + checksum: see `../../spec/checksums.json` after `assay fetch icc`.

## Tier 2 — fetched on demand to `vendor/icc/` (gitignored)

| Profile | Source | Why not committed |
|---|---|---|
| `GRACoL2013_CRPC6.icc` | IDEAlliance | ToS click-through required to download |
| `FOGRA39L_coated.icc` | ECI / FOGRA | Redistribution restricted |
| `FOGRA51L_coated.icc` | ECI / FOGRA | Redistribution restricted |

Run `uv run assay fetch icc` to download all three; they land in `vendor/icc/` with
SHA-256 verification against `vendor/icc-checksums.json`.

## Why this split

Same logic as `vendor/README.md` — never redistribute what we don't have explicit
redistribution rights to. Profiles in Tier 1 have those rights; Tier 2 don't.

If a profile's license terms change or your jurisdiction interprets them differently,
move the file by editing this README and the corresponding fetcher entry — no code
changes required.

## ICC bundling status (v0.1.0)

The ICC profile fetcher is scaffolded but not yet wired in. For v0.1.0 the generator
falls back to ghostscript's bundled sRGB if no ICC is found — which is fine for
development but produces PDFs that **will fail variant-specific verapdf validation**
for any non-sRGB output intent. This is documented in `docs/known-quirks.md` and is
the primary blocker for v0.1.0 → v0.2.0.
