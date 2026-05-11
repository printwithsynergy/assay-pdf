# Security Policy

## Supported versions

AssayPDF is in pre-1.0 development. Only the latest released version on
the `main` branch receives security fixes.

| Version | Supported |
|---|---|
| `0.1.x` (current) | yes |
| anything older | no |

## Reporting a vulnerability

**Please do not open a public GitHub issue for security problems.**

Email **iam@quincy.codes** with:

- a description of the issue and the impact you believe it has,
- the AssayPDF version (`uv run assay --version`) and commit SHA,
- a minimal reproduction (input PDF, command line, or code snippet),
- any logs, stack traces, or proof-of-concept output.

If you'd prefer to encrypt, request a public key in your first email and
we'll respond with one before you send details.

## What to expect

- **Acknowledgement** within 3 business days.
- **Triage and severity assessment** within 7 business days.
- **Fix or mitigation timeline** communicated once triage is done. Critical
  issues (RCE, arbitrary file write outside the working tree, credential
  exfiltration) are targeted for a patch release within 14 days.
- **Public disclosure** is coordinated with the reporter. We prefer a
  CVE + GitHub Security Advisory once a fix is available.

## Scope

In scope:

- The `assay_pdf` Python package (CLI, generator, harness, scorer).
- Vendor-asset fetcher and SHA-256 verification logic in `src/assay_pdf/vendor/`.
- CI workflows under `.github/workflows/` that have write access to the
  repository.
- Dependency confusion or typosquatting affecting `pyproject.toml` /
  `uv.lock`.

Out of scope:

- Vulnerabilities in third-party preflight engines (callas pdfToolbox,
  Enfocus PitStop, veraPDF, Ghostscript, qpdf, MuPDF). Report those
  upstream.
- Defects in the GWG 2022 specification itself.
- Findings against generated PDFs that depend on a downstream consumer
  mishandling a deliberately malformed test file — the corpus is, by
  design, full of files that violate PDF/X-4. That's the product.
- Social-engineering attacks, physical attacks, or denial-of-service
  through obviously expensive operations (`assay generate` on the full
  corpus is intentionally not free).

## Hardening notes

A few things to be aware of when running AssayPDF:

- `assay fetch` downloads assets from GWG-canonical URLs over HTTPS and
  verifies SHA-256 against `vendor/checksums.json` before writing. If a
  checksum mismatch occurs, the run aborts and nothing is unpacked.
- The harness invokes external binaries (`verapdf`, engine CLIs) with
  argument lists, never via shell. Engine output is parsed, not executed.
- Generated PDFs are written into the project's `corpus/` directory only.
  No paths are taken from network input.

## Credit

We're happy to credit reporters in the changelog and the GitHub Security
Advisory, unless you ask to remain anonymous.
