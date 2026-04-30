# vendor/

This directory holds large GWG-copyright reference assets that AssayPDF needs locally
but **does not redistribute**.

The contents are populated by `uv run assay fetch`, which downloads from the official
GWG endpoints and verifies SHA-256 against `vendor/checksums.json`.

## Contents (after `assay fetch`)

| File | Source | Size |
|---|---|---|
| `gos-5.0-testpages.zip` | https://gwg.org/?wpdmdl=9080 | ~24 MB |
| `gos-5.0-patches.zip` | https://gwg.org/?wpdmdl=9076 | ~132 MB |
| `processing-steps-test-suite-v1.zip` | https://gwg.org/?wpdmdl=19518 | ~26 MB |
| `extracted/` | unzipped tree of the above | grows as needed |

Total: ~183 MB. All entries gitignored except this README and `checksums.json`.

## Why not commit these?

1. **Copyright** — the Ghent Workgroup retains copyright. Redistribution may exceed fair use.
2. **Repo bloat** — 183 MB of binary blobs slow every clone.
3. **Reproducibility doesn't require commit** — checksum-pinned URLs give byte-identical reproducibility without redistribution.

If the upstream URL changes or content drifts (caught by the weekly URL-liveness CI cron),
update `vendor/checksums.json` in a PR.
