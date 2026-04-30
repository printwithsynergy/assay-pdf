## Summary

<!-- One sentence describing what this PR does. -->

## Type of change

- [ ] Bug fix
- [ ] New rule generator (specify rule ID and variant in description)
- [ ] New engine runner
- [ ] Rule-map refinement (which engine?)
- [ ] Documentation
- [ ] Build / CI / tooling
- [ ] Other (describe)

## Tests

- [ ] Added or updated unit tests
- [ ] All generated PDFs pass `verapdf` validation
- [ ] Determinism test: identical sha256 across two `assay generate` runs
- [ ] CI is green

## Checklist

- [ ] `just check` passes (lint, mypy, tests)
- [ ] CHANGELOG.md updated under `[Unreleased]`
- [ ] If a new dependency was added, it's justified in PR description
- [ ] If this affects the corpus, `corpus/manifest.json` is regenerated and committed
