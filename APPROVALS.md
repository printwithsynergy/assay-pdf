# assay-pdf — STOP-Gate Approvals (mirror)

Authoritative source: `/Users/macadmin/synergy-agents/approvals.md`. This
file mirrors the entries that affect `assay-pdf` for in-repo
discoverability.

## Entries

### GWG 2022 lintpdf baseline (criterion 5)
- gate: GWG 2022 lintpdf baseline
- decision: Approved
- date: 2026-05-07T15:08:00Z
- source: Quincy authorization in Multi-Agent Cutover Prompt
- evidence: `reports/baselines/gwg2022_baseline.json`, `reports/gwg2022/diff-sheetcmyk-cmyk.json`, `reports/gwg2022/diff-all.json`, `reports/gwg2022/run_index.json`, `scripts/gwg2022_baseline.py`, `scripts/bin/lint-pdf` (PATH shim)
- notes: PATH-shim approach keeps the MIT/AGPL boundary (subprocess only). Two deterministic reruns → diff_count=0 for both `--profile sheetcmyk-cmyk` and `all`.
