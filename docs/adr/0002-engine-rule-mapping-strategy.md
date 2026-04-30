# ADR-0002: Engine rule mapping via regex patterns vs. structured outputs

**Status:** Accepted, v0.1.0.

**Context:** Preflight engines (PitStop, pdfToolbox) emit issue messages tied to *their* rule catalogues, not GWG rule IDs. To compute TP/FP/FN/TN per GWG rule, AssayPDF must translate engine output into GWG rule IDs.

Three options:

1. **A: Regex pattern matching on message strings.** A JSON file per engine maps regex → GWG rule ID. Easy to start, brittle to engine release notes that change wording.
2. **B: Engine-internal rule IDs (where available).** PitStop ships an issue catalogue with internal IDs; pdfToolbox has check IDs. Map those to GWG rule IDs once, then never touch the message strings.
3. **C: Spec-aware AST diff.** Round-trip the PDF through the engine's "fix" mode (where available), structurally diff the input vs. output, infer which rule fired from what changed.

**Decision:** Option A for v0.1.0 with intent to migrate to Option B for engines that expose stable rule IDs.

## Reasoning

- **Option A starts with zero engine knowledge.** We can run the harness against a real PDF, see what the engine reports, and write rule-map entries that target the actual messages we observe. No need to read engine documentation or reverse-engineer internal IDs.
- **Engine-internal IDs aren't always exposed.** pdfToolbox's JSON report has `type` and `severity` fields but the rule identifier varies by check. PitStop's XML reports have an `issueID` attribute on some checks but not all. Option B requires per-engine investigation that we'd rather defer.
- **Structured AST diff is overkill.** Option C is a research project. Doable but expensive, and the fix-then-diff round-trip introduces its own noise.
- **Rule maps are versioned and improvable.** When we see a PitStop message we don't have a pattern for, the rule_id comes back as `null`. The scorer treats unmapped hits as ambiguous noise (counted toward FP if on a positive baseline, ignored otherwise). Add the missing pattern to the JSON, re-run.

## What option A costs

- **Brittleness to vendor wording changes.** If pdfToolbox 16 → 17 reformats "white object set to overprint" to "Overprint enabled on white-filled element", our pattern misses it until we update. Mitigation: rule maps are tested against actual benchmark output; CI doesn't run benchmarks but local benchmark output is reviewed at every release.
- **False mapping risk.** A regex too liberal can map a different issue to the wrong rule, inflating FP. Mitigation: keep patterns tight and rule-specific; add element-type discriminators where messages overlap (e.g. `text.*overprint` vs `path.*overprint`).
- **Duplicate hit handling.** Engines sometimes emit multiple issues for one violation (e.g., one general "color space" issue plus one per object). Currently we count each hit as a separate `RuleHit`; the scorer counts a TP if *any* hit matches the rule. Multiple hits for the same rule on the same PDF count as one TP, not many.

## Migration path to option B

When an engine exposes a stable rule-ID system, the runner can read those IDs and the rule_map becomes a `{engine_internal_id: gwg_rule_id}` lookup instead of regex patterns. The Runner protocol already separates "produce hits with rule_ids" from "score those hits", so the change is local to one Runner subclass.

For lintPDF specifically (sister project), we'll publish stable rule IDs from day one and the runner can use option B directly.

## Implementation reference

See `src/assay_pdf/harness/runners/base.py:Runner.map_message_to_rule()` and `src/assay_pdf/harness/rule_maps/{pdftoolbox,pitstop}.json`.
