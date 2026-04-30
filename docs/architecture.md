# Architecture

How the pieces fit together.

```
spec/gwg-2022-spec.xlsx
        │
        │ assay ingest
        ▼
spec/requirement-ids.json
        │
        ▼
src/assay_pdf/generator/
  ├ variants.py        ← 23 variant configs
  ├ rules.py           ← 39 rule generator functions
  ├ base.py            ← PDF/X-4 scaffolding (reportlab + pikepdf)
  ├ injectors.py       ← shared content-stream helpers
  ├ determinism.py     ← byte-identical metadata override
  └ orchestrator.py    ← runs all (rule × variant) combos
        │
        │ assay generate
        ▼
corpus/
  ├ manifest.json      ← committed; SHA-256 + applicability per file
  ├ positive/          ← 23 PDFs, gitignored
  └ negative/          ← 39 PDFs, gitignored
        │
        ▼
src/assay_pdf/harness/
  ├ runners/{lintpdf,pitstop,pdftoolbox}.py
  ├ rule_maps/*.json   ← engine message → R-id
  ├ scorer.py          ← per-(rule, variant) confusion matrix
  └ driver.py          ← runs an engine over the corpus
        │
        │ assay benchmark --engine X
        ▼
results/<engine>-<ts>.{json,score.json}
        │
        ▼
src/assay_pdf/reports/
  ├ generator.py       ← aggregates score JSONs
  └ templates/{markdown.j2,html.j2}
        │
        │ assay report --format md|html
        ▼
REPORT.md / REPORT.html
```

## Layer responsibilities

### Spec layer (`src/assay_pdf/spec/`)

Reads `spec/gwg-2022-spec.xlsx` and produces typed `RequirementManifest` JSON. Pure data parsing — no PDF construction.

### Generator layer (`src/assay_pdf/generator/`)

Builds the PDF corpus deterministically. The flow per rule:

1. `base.build_base_pdfx4()` constructs a minimal valid PDF/X-4 with the correct output intent.
2. The rule generator injects exactly one violation via `pikepdf` mutations + content-stream snippets.
3. `determinism.stamp_deterministic()` overrides `/Info` dates, `/ID` array, and producer string with values derived from a fixed seed.
4. The result is added to `corpus/manifest.json` with its SHA-256 + applicable variants.

Rule generators are registered via `@register("Rxxxx")` decorators in `rules.py`. Adding a rule = adding a generator function. The orchestrator picks them up automatically.

### Harness layer (`src/assay_pdf/harness/`)

Runs engines against the corpus. One `Runner` subclass per engine, each implementing:

- `binary_path()` — locate the engine's CLI.
- `engine_version()` — report the version (recorded in results).
- `run(pdf_path, variant_kebab)` — invoke the engine, parse output, return `EngineResult`.

Engine messages are translated to GWG rule IDs via `rule_maps/<engine>.json` — a regex-pattern → R-id map. Adding an engine = subclassing Runner + writing the rule map JSON.

### Scorer (`src/assay_pdf/harness/scorer.py`)

Walks `corpus/manifest.json` and a list of `EngineResult`. For each (manifest entry, engine result) pair, increments TP/FP/FN/TN counters per (rule_id, variant). Stub negatives are skipped.

Misattribution (engine flags wrong rule) is penalized: it's both an FN for the targeted rule and an FP for the rule the engine flagged.

### Reports (`src/assay_pdf/reports/`)

Loads every `results/*.score.json` and renders via Jinja2. Two templates:

- `markdown.j2` — README-embeddable, GitHub-friendly.
- `html.j2` — standalone, Tailwind via CDN, navy/lime branding.

## Models (`src/assay_pdf/models.py`)

Pydantic v2 models are the canonical data shapes. Every persisted artifact is one of these models serialized to JSON. Change the model = change the schema everywhere.

Key models:
- `RequirementManifest` — the spec
- `CorpusManifest` + `ManifestEntry` — the corpus
- `EngineResult` + `RuleHit` — one engine run on one PDF
- `ScoreReport` + `RuleScore` — aggregated benchmark output

## Determinism

Three sources of nondeterminism in PDFs:
1. Creation timestamp.
2. `/ID` array — usually MD5 of file contents.
3. Object stream ordering when `pdf.save()` rewrites cross-reference tables.

`determinism.py` handles 1 and 2 by overriding to fixed values. pikepdf's `deterministic_id=True` save option handles 3.

Tested in `tests/test_determinism.py` — generates the same PDF twice and asserts SHA-256 equality.

## Why pikepdf + reportlab + ghostscript

Each library handles what it's best at:
- **reportlab** — page layout, vector primitives, font metrics. Easy to draw stuff.
- **pikepdf** — low-level PDF object manipulation (resources, content streams, OutputIntents, OCGs, /ID arrays). Hard to do with reportlab alone.
- **ghostscript** (deferred to v0.1.1 for harder rules) — rendering complex stuff (transparency groups, OPM modes) where direct PDF construction is brittle.

The split keeps each rule generator small. Most are <50 lines.

## CI strategy

- `ci.yml` runs on every push — pytest, ruff, mypy, schema-only `assay validate`. No engine binaries in CI (commercial licenses).
- `url-liveness.yml` weekly cron — verifies all GWG asset URLs still respond 200. Files an issue if not.
- `release.yml` triggers on `v*.*.*` tags — builds wheel/sdist, drafts a GitHub release.

Engine benchmark scores are run locally and committed manually. CI never runs `assay benchmark`.
