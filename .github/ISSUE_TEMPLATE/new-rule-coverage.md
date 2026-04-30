---
name: New rule coverage
about: Propose a new generator (rule, boundary case, or variant) for the corpus
title: "[NEW] "
labels: enhancement, corpus
---

## GWG 2022 rule(s) targeted

<!-- e.g. R0031 (Image resolution for grayscale and colour images) -->

## Variants affected

<!-- e.g. SheetCMYK_CMYK, MagazineAds_CMYK -->

## Proposed test files

| File | Boundary case | Expected outcome | Targeted rule |
|---|---|---|---|
| negative/image-resolution/r0031-200ppi-color.pdf | Below `error` threshold for sheet variant | error | R0031 |

## Why this case is signal-bearing

<!-- One sentence: why this PDF would distinguish a competent preflight engine from a sloppy one. -->

## I will / I want help to

- [ ] Submit a PR with the new generator
- [ ] Have someone else implement (issue only)
