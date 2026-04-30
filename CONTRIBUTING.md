# Contributing to AssayPDF

Thanks for your interest. AssayPDF welcomes three categories of contribution above all others:

1. **New rule generators** — extending coverage of GWG 2022 rules or adding boundary-case negatives.
2. **New engine runners** — adapting AssayPDF to benchmark another preflight engine.
3. **Rule-map refinements** — improving the message-pattern → GWG rule ID mapping for an existing engine.

## Development setup

```bash
git clone https://github.com/thinkneverland/copper-anvil.git # placeholder until repo is public
cd assay-pdf
uv sync --all-extras                # installs runtime + dev deps
uv run pre-commit install           # ruff + mypy + EOF/whitespace pre-commit hooks
uv run pytest                       # ~5 sec; uses tests/fixtures/ — does not require vendor assets
```

Required external binaries (install via `brew install` on macOS):

```
ghostscript qpdf mupdf-tools exiftool imagemagick
```

veraPDF must be installed separately — see [docs/reproducing.md](docs/reproducing.md).

## Adding a rule generator

Each negative test PDF targets exactly one GWG 2022 rule ID. To add one:

1. Open `src/assay_pdf/generator/rules.py`.
2. Add `gen_rNNNN_descriptive_name(variant, output_path)` returning a `ManifestEntry`.
3. The function must be deterministic — pass any randomness through the project seed (see `generator/determinism.py`).
4. Add a unit test to `tests/test_generators.py` that asserts:
   - Output is valid PDF/X-4 (run `verapdf`).
   - SHA-256 is identical across two runs with the same seed.
   - Targeted rule fires when run through at least one engine in `tests/fixtures/`.

## Adding an engine runner

1. Subclass `assay_pdf.harness.runners.base.Runner`.
2. Implement `run(pdf_path, profile)` returning an `EngineResult`.
3. Add `src/assay_pdf/harness/rule_maps/<engine>.json` mapping engine messages to GWG rule IDs.
4. Document install + license in [docs/methodology.md](docs/methodology.md).

## Code style

- `ruff` for formatting + lint
- `mypy --strict` for type checking
- Lines wrap at 100 chars
- Docstrings: Google style
- Commits: [Conventional Commits](https://www.conventionalcommits.org/)

## License

By contributing, you agree your contribution is licensed under the MIT license.
