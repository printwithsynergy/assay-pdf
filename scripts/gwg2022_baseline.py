"""Pin and diff the GWG 2022 lintpdf benchmark scores.

Produces a deterministic, comparable baseline derived from a ScoreReport
emitted by ``assay benchmark`` so that subsequent runs can be diffed
without timestamp/runtime noise.

Usage examples:
    # Pin from the most recent results/<engine>-*.score.json files.
    python scripts/gwg2022_baseline.py pin --engine lintpdf \
        --score results/lintpdf-20260507T150556Z.score.json \
        --score results/lintpdf-20260507T150357Z.score.json \
        --label sheetcmyk-cmyk \
        --label all \
        --output reports/baselines/gwg2022_baseline.json

    # Diff a fresh score report against the pinned baseline.
    python scripts/gwg2022_baseline.py diff \
        --baseline reports/baselines/gwg2022_baseline.json \
        --score results/lintpdf-<ts>.score.json \
        --label sheetcmyk-cmyk

The "comparable" payload contains only the deterministic fields:
``rule_id``, ``variant``, ``true_positives``, ``false_positives``,
``true_negatives``, ``false_negatives`` — sorted by ``(rule_id, variant)``.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any


def _load_score(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _comparable_rows(score: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in score.get("per_rule_per_variant", []):
        rows.append(
            {
                "rule_id": entry.get("rule_id"),
                "variant": entry.get("variant"),
                "true_positives": int(entry.get("true_positives") or 0),
                "false_positives": int(entry.get("false_positives") or 0),
                "true_negatives": int(entry.get("true_negatives") or 0),
                "false_negatives": int(entry.get("false_negatives") or 0),
            }
        )
    rows.sort(key=lambda row: (str(row["rule_id"] or ""), str(row["variant"] or "")))
    return rows


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "true_positives": sum(int(r["true_positives"]) for r in rows),
        "false_positives": sum(int(r["false_positives"]) for r in rows),
        "true_negatives": sum(int(r["true_negatives"]) for r in rows),
        "false_negatives": sum(int(r["false_negatives"]) for r in rows),
    }


def _profile_payload(score_path: Path, label: str) -> dict[str, Any]:
    score = _load_score(score_path)
    rows = _comparable_rows(score)
    return {
        "profile_label": label,
        "engine": score.get("engine"),
        "engine_version": score.get("engine_version"),
        "corpus_version": score.get("corpus_version"),
        "score_source": score_path.name,
        "row_count": len(rows),
        "aggregate": _aggregate(rows),
        "per_rule_per_variant": rows,
    }


def _build_baseline(
    engine: str,
    pairs: Iterable[tuple[str, Path]],
) -> dict[str, Any]:
    profiles: list[dict[str, Any]] = []
    for label, path in pairs:
        profiles.append(_profile_payload(path, label))
    profiles.sort(key=lambda p: p["profile_label"])
    return {
        "schema_version": "1.0.0",
        "report_kind": "assay-pdf.gwg2022.lintpdf-baseline",
        "engine": engine,
        "spec": "GWG 2022",
        "profiles": profiles,
    }


def _diff_profiles(
    baseline_profile: dict[str, Any], current_profile: dict[str, Any]
) -> list[dict[str, Any]]:
    diffs: list[dict[str, Any]] = []
    base_rows = {
        (r["rule_id"], r["variant"]): r for r in baseline_profile.get("per_rule_per_variant", [])
    }
    curr_rows = {
        (r["rule_id"], r["variant"]): r for r in current_profile.get("per_rule_per_variant", [])
    }
    for key in sorted(set(base_rows) - set(curr_rows)):
        diffs.append({"kind": "missing-row", "rule_id": key[0], "variant": key[1]})
    for key in sorted(set(curr_rows) - set(base_rows)):
        diffs.append({"kind": "new-row", "rule_id": key[0], "variant": key[1]})
    for key in sorted(set(base_rows) & set(curr_rows)):
        base = base_rows[key]
        curr = curr_rows[key]
        diff_fields: dict[str, Any] = {}
        for field in (
            "true_positives",
            "false_positives",
            "true_negatives",
            "false_negatives",
        ):
            if int(base[field]) != int(curr[field]):
                diff_fields[field] = {"baseline": base[field], "current": curr[field]}
        if diff_fields:
            diffs.append(
                {
                    "kind": "score-mismatch",
                    "rule_id": key[0],
                    "variant": key[1],
                    "fields": diff_fields,
                }
            )
    return diffs


def cmd_pin(args: argparse.Namespace) -> int:
    if len(args.label) != len(args.score):
        print(
            "pin: --label and --score must be supplied an equal number of times",
            file=sys.stderr,
        )
        return 2
    pairs = list(zip(args.label, [Path(p) for p in args.score], strict=True))
    payload = _build_baseline(args.engine, pairs)

    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "status": "baseline-pinned",
        "engine": args.engine,
        "output": str(output),
        "profiles": [
            {
                "label": profile["profile_label"],
                "row_count": profile["row_count"],
                "aggregate": profile["aggregate"],
            }
            for profile in payload["profiles"]
        ],
    }
    print(json.dumps(summary, indent=2))
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    if len(args.label) != len(args.score):
        print(
            "diff: --label and --score must be supplied an equal number of times",
            file=sys.stderr,
        )
        return 2

    baseline_path = Path(args.baseline).resolve()
    if not baseline_path.exists():
        print(f"diff: baseline file missing: {baseline_path}", file=sys.stderr)
        return 2
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    base_by_label = {p["profile_label"]: p for p in baseline.get("profiles", [])}

    out_root = Path(args.output) if args.output else baseline_path.parent
    out_root.mkdir(parents=True, exist_ok=True)
    summary: dict[str, Any] = {
        "status": "ok",
        "baseline": str(baseline_path),
        "profiles": [],
    }
    overall_status = 0
    for label, score_path_str in zip(args.label, args.score, strict=True):
        score_path = Path(score_path_str).resolve()
        if label not in base_by_label:
            summary["profiles"].append({"label": label, "status": "missing-from-baseline"})
            overall_status = 1 if args.fail_on_diff else overall_status
            continue
        current_profile = _profile_payload(score_path, label)
        diffs = _diff_profiles(base_by_label[label], current_profile)
        diff_path = out_root / f"diff-{label}.json"
        diff_path.write_text(
            json.dumps(
                {
                    "label": label,
                    "baseline_score_source": base_by_label[label].get("score_source"),
                    "current_score_source": score_path.name,
                    "diff_count": len(diffs),
                    "diffs": diffs,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        summary["profiles"].append(
            {
                "label": label,
                "diff_count": len(diffs),
                "diff_path": str(diff_path),
                "current_aggregate": current_profile["aggregate"],
                "baseline_aggregate": base_by_label[label]["aggregate"],
            }
        )
        if diffs and args.fail_on_diff:
            overall_status = 1

    if overall_status:
        summary["status"] = "diff"
    print(json.dumps(summary, indent=2))
    return overall_status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    pin = sub.add_parser("pin", help="Pin a baseline JSON from one or more score reports.")
    pin.add_argument("--engine", default="lintpdf")
    pin.add_argument("--score", action="append", required=True, help="Path to a *.score.json file.")
    pin.add_argument(
        "--label", action="append", required=True, help="Profile label aligned with --score."
    )
    pin.add_argument("--output", required=True, help="Destination baseline JSON path.")
    pin.set_defaults(func=cmd_pin)

    diff = sub.add_parser("diff", help="Diff a fresh score report against the pinned baseline.")
    diff.add_argument("--baseline", required=True)
    diff.add_argument("--score", action="append", required=True)
    diff.add_argument("--label", action="append", required=True)
    diff.add_argument("--output", default=None)
    diff.add_argument("--fail-on-diff", action="store_true", default=True)
    diff.add_argument("--no-fail-on-diff", dest="fail_on_diff", action="store_false")
    diff.set_defaults(func=cmd_diff)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
