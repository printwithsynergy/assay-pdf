# Known Quirks

Things that might surprise you running AssayPDF, with explanation.

## verapdf 1.30 + JDK 26 warnings

```
WARNING: Final field flavour in class org.verapdf.pdfa.validation.profiles...
```

verapdf 1.30 was released in April 2026 against JDK 21. Newer JDKs (24+) have stricter rules about reflective field mutation, which the verapdf JAXB layer hits. The warnings are informational; verapdf still validates correctly.

To silence:
```bash
export VERAPDF_JAVA_OPTS="--add-opens java.base/java.lang.reflect=ALL-UNNAMED --enable-final-field-mutation=ALL-UNNAMED"
```

## pikepdf XMP DocumentInfo warnings

```
UserWarning: The DocumentInfo field /CreationDate could not be updated from XMP
UserWarning: The DocumentInfo field /ModDate could not be updated from XMP
```

These appear during corpus generation. AssayPDF's determinism layer overrides both `/Info` and XMP metadata; pikepdf warns when XMP can't sync changes back to `/Info` (because we already wrote `/Info` directly). Harmless. Will be silenced in v0.1.1 with `warnings.filterwarnings`.

## ICC profile fallbacks

If you don't have Adobe ICC Profiles installed, the generator falls back to macOS's `Generic CMYK Profile.icc`. That's structurally a CMYK ICC and produces valid PDF/X-4, but it's not the spec-recommended profile for any specific variant (FOGRA51L for sheet, FOGRA51 for newspaper, GRACoL2013 for US sheet, etc.).

For variant-specific colorimetry: install Adobe ICC Profiles via Acrobat/Photoshop, or download from https://www.adobe.com/support/downloads/iccprofiles/iccprofiles_mac.html. AssayPDF will pick them up automatically (search paths include `/Library/ColorSync/Profiles/Recommended`).

## CoatedFOGRA51 vs CoatedFOGRA39

Adobe ships `CoatedFOGRA39.icc` in older Photoshop installs but `CoatedFOGRA51.icc` only with newer versions (or as a separate ECI download). The variant config requests FOGRA51, and AssayPDF's family fallback chain resolves to CoatedFOGRA39 if FOGRA51 isn't present. The output PDF/X-4 is structurally valid; the colorimetric reference just defaults to FOGRA39.

For exact-match fidelity to the spec: install CoatedFOGRA51 or PSOcoated_v3 from ECI's website.

## Determinism on Apple Silicon vs Intel

AssayPDF generates byte-identical PDFs across runs on the same machine. Across different CPU architectures (Intel vs Apple Silicon), there's a tiny risk of float-rounding differences in ICC transforms during PDF metadata stamping. The corpus manifest records `arch_generated_on`. If you regenerate on a different arch and the SHA-256 differs by one byte in the stream that holds the ICC `/N` value, that's expected — file an issue if it bothers you and we'll add float canonicalization.

## Stub negatives

18 of 39 rules in the v0.1.0 corpus have stub negatives — structurally valid PDF/X-4 baselines tagged with the rule ID but lacking actual rule violations. Engines won't flag them. The scorer treats this as a known coverage gap, not engine failure. Tracked for v0.1.1.

Affected rules: R0009-R0013, R0016-R0019, R0021-R0023, R0028-R0030, R0033, R0036, R1002.

## verapdf -f 4 flavour

`verapdf -f 4` defaults to **PDF/A-4** validation, not PDF/X-4. PDF/X-4 validation profiles aren't in verapdf's stock distribution. AssayPDF uses `-f 4` because the structural checks overlap heavily with PDF/X-4 — most of what fails PDF/X-4 also fails PDF/A-4 — but it's not a strict PDF/X-4 conformance check.

For strict PDF/X-4 validation, use callas pdfToolbox's PDF/X-4 conformance preflight or a custom verapdf profile. v0.1.1 will ship a custom `pdfx4.xml` validation profile alongside the corpus.

## zsh paste-as-command interactivecomments

Pasting bash comments (`# foo`) into an interactive zsh session by default produces `zsh: command not found: #`. Add to your `.zshrc`:

```bash
setopt interactivecomments
```

Doesn't affect any AssayPDF behavior; just makes paste cleaner.

## "engine not available" vs "engine ran but produced no results"

When an engine binary isn't installed, `RunnerNotInstalledError` propagates and the CLI exits with code 2. When an engine is installed but every per-file run errors (e.g., licensing issue), the driver logs warnings and reports zeros. Different end states, both expected. Score reports for the latter case will show TP/FP/FN/TN all zero — read the raw `results/<engine>-*.json` to see the per-file errors.
