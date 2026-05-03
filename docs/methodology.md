---
title: "Methodology"
description: "How AssayPDF scores a preflight engine: confusion-matrix counts per rule and variant, rule-map translation, misattribution penalties, and reproducibility guarantees."
group: "Reference"
order: 6
---

# Methodology

How AssayPDF actually scores a preflight engine.

## What gets measured

Every PDF in the corpus is one of:

- **Positive baseline** — a minimal PDF/X-4 file for one of the 23 GWG 2022 variants. Should pass every applicable rule.
- **Negative test** — a PDF that violates exactly one rule cleanly, leaving every other rule satisfied.

For each (engine × variant × rule) combination, the scorer computes a confusion matrix:

| | Engine flagged the rule | Engine did not flag |
|---|---|---|
| **Negative test for that rule** | true positive (TP) | false negative (FN) |
| **Positive baseline** | false positive (FP) | true negative (TN) |

From these:
- **Accuracy** = (TP + TN) / total
- **Precision** = TP / (TP + FP)
- **Recall** = TP / (TP + FN)
- **F1** = 2 · precision · recall / (precision + recall)

## What "engine flagged the rule" means

Preflight engines (PitStop, pdfToolbox) emit issue messages, not GWG rule IDs. AssayPDF translates each engine's message catalogue into GWG rule IDs via `src/assay_pdf/harness/rule_maps/<engine>.json` — a list of regex patterns mapped to rule IDs.

When an engine reports a rule that doesn't match any pattern in its rule map, the rule_id is `null`. That hit doesn't contribute to TP for any specific rule but does count toward overall noise (the engine flagged something on a positive baseline → FP for the unmapped rule).

This means rule-map quality directly affects scores. Rule maps are versioned in the repo and improved iteratively as actual benchmark output reveals patterns we missed.

## Why this is honest

- **No vendor mode** — every engine runs on the same corpus with the same scoring rules.
- **No engine-specific tuning** — we don't suppress an engine's noise; we count it.
- **Misattribution is penalized** — if the engine flags rule R0007 on a PDF that violates R0014, that's both an FN for R0014 *and* an FP for R0007. Wrong rule attribution is a real quality issue.
- **Stub negatives are excluded** — the v0.1.0 corpus has 18 rules where the negative is structurally a baseline (no violation injected). The scorer skips these. They're listed in the report as a coverage gap, not an engine failure.

## What it doesn't measure

AssayPDF measures **structural conformance to the GWG 2022 spec rules** — does the engine catch the cases the spec says should be errors or warnings, and does it stay quiet on cases the spec says should pass?

Things AssayPDF does **not** measure (in v0.1.0):
- **Color accuracy** — whether ICC profiles produce the same printed result.
- **Performance under load** — only single-file runtime is captured.
- **Workflow integration** — JDF/JMF, PitStop Connect, callas Switch, etc.
- **GUI usability** — only CLI invocations are benchmarked.

If you want any of those, file an issue with a methodology proposal.

## Reproducibility guarantee

Same input → same output, byte-identical:

- **Corpus generation** is deterministic. Two runs of `uv run assay generate` produce the same SHA-256 for every PDF (see `tests/test_determinism.py`).
- **Spec parsing** is deterministic. The XLSX is committed; running `uv run assay ingest` produces the same `requirement-ids.json`.
- **Vendor assets** are pinned by SHA-256 in `vendor/checksums.json`.
- **Engine versions** are recorded in every results file. If the engine version changes, the score should be re-run and the report tagged with the new version.

If you can't reproduce a published score, file an issue with your local engine version, the corpus version, and the score JSON.
