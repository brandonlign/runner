#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
from typing import Any

import numpy as np

EXPECTED_RUN = 31195683802
EXPECTED_VERDICT = "INCONCLUSIVE_MULTIPLICITY_V5_HOLDOUT_POWER"
EXPECTED_FAMILIES = 92
EXPECTED_QUALIFIED = 56
METHODS = ("multiplicity", "brown", "v3", "fixed4_persistence")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--artifact-dir", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def compare(eval_data: dict[str, Any], comparator: str) -> dict[str, Any]:
    primary = {str(r["label"]): r for r in eval_data["multiplicity"]["per_label"] if r.get("qualified")}
    other = {str(r["label"]): r for r in eval_data[comparator]["per_label"] if r.get("qualified")}
    require(set(primary) == set(other), f"qualified label universe differs for {comparator}")
    require(len(primary) == EXPECTED_QUALIFIED, "qualified label count changed")

    rows = []
    for label in sorted(primary):
        m = primary[label]
        b = other[label]
        require(str(m["family_id"]) == str(b["family_id"]), f"best-match family changed for {label}/{comparator}")
        require(abs(float(m["f1"]) - float(b["f1"])) < 1e-15, f"F1 changed for {label}/{comparator}")
        delta = int(b["rank"]) - int(m["rank"])
        rows.append({
            "label": label,
            "family_id": str(m["family_id"]),
            "multiplicity_rank": int(m["rank"]),
            "comparator_rank": int(b["rank"]),
            "comparator_minus_multiplicity_rank": delta,
            "precision": float(m["precision"]),
            "recall": float(m["recall"]),
            "f1": float(m["f1"]),
        })

    deltas = np.asarray([r["comparator_minus_multiplicity_rank"] for r in rows], dtype=float)
    improved = int(np.sum(deltas > 0))
    worsened = int(np.sum(deltas < 0))
    tied = int(np.sum(deltas == 0))
    return {
        "comparator": comparator,
        "qualified_labels": len(rows),
        "improved": improved,
        "worsened": worsened,
        "tied": tied,
        "mean_rank_delta": float(np.mean(deltas)),
        "median_rank_delta": float(np.median(deltas)),
        "p25_rank_delta": float(np.quantile(deltas, 0.25)),
        "p75_rank_delta": float(np.quantile(deltas, 0.75)),
        "largest_improvements": sorted(rows, key=lambda r: (-r["comparator_minus_multiplicity_rank"], r["label"]))[:10],
        "largest_degradations": sorted(rows, key=lambda r: (r["comparator_minus_multiplicity_rank"], r["label"]))[:10],
        "per_label": rows,
    }


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    holdout_path = args.artifact_dir / "multiplicity_v5_holdout.json"
    evaluation_path = args.artifact_dir / "multiplicity_v5_evaluation.json.gz"
    require(holdout_path.is_file(), "missing frozen holdout JSON")
    require(evaluation_path.is_file(), "missing frozen evaluation artifact")

    holdout = json.loads(holdout_path.read_text())
    with gzip.open(evaluation_path, "rt") as f:
        evaluation = json.load(f)

    require(holdout["verdict"] == EXPECTED_VERDICT, "unexpected holdout verdict")
    require(holdout["family_count"] == EXPECTED_FAMILIES, "unexpected family count")
    require(holdout["configuration"]["years"] == [2020, 2021], "unexpected holdout years")
    require(holdout["configuration"]["blind_exclusion"] == [20.0, 55.0], "blind interval changed")
    require(set(evaluation) == set(METHODS), "evaluation methods changed")

    failed_validity = [k for k, v in holdout["validity_gates"].items() if not v]
    require(failed_validity == ["at_least_100_recurrent_families"], f"unexpected failed validity gates: {failed_validity}")
    for method in METHODS:
        require(holdout["metrics"][method]["qualified_matches"] == EXPECTED_QUALIFIED, f"qualified count changed: {method}")
        require(holdout["metrics"][method]["recovered_at_100"] == EXPECTED_QUALIFIED, f"top100 not saturated: {method}")

    comparisons = {name: compare(evaluation, name) for name in ("brown", "v3", "fixed4_persistence")}
    m = holdout["metrics"]["multiplicity"]
    b = holdout["metrics"]["brown"]
    classification = (
        "DIAGNOSIS_V5_TOP100_SATURATED_BUT_RANK_SIGNAL_PRESENT"
        if EXPECTED_FAMILIES < 100
        and all(holdout["metrics"][method]["recovered_at_100"] == EXPECTED_QUALIFIED for method in METHODS)
        and float(m["mrr"]) > float(b["mrr"])
        and float(m["median_rank"]) < float(b["median_rank"])
        else "DIAGNOSIS_V5_TOP100_SATURATED_OR_RANK_SIGNAL_MIXED"
    )

    result = {
        "verdict": classification,
        "source_run": EXPECTED_RUN,
        "blindness": {
            "artifact_only": True,
            "catalogue_access": False,
            "excluded_interval_access": False,
            "orbittrace_target_access": False,
        },
        "holdout_verdict_preserved": holdout["verdict"],
        "family_count": holdout["family_count"],
        "qualified_matches": EXPECTED_QUALIFIED,
        "failed_validity_gates": failed_validity,
        "rank_metrics": {method: {
            "mrr": holdout["metrics"][method]["mrr"],
            "median_rank": holdout["metrics"][method]["median_rank"],
        } for method in METHODS},
        "multiplicity_relative_mrr": {
            "vs_brown": float(m["mrr"] / b["mrr"] - 1.0),
            "vs_v3": float(m["mrr"] / holdout["metrics"]["v3"]["mrr"] - 1.0),
            "vs_fixed4": float(m["mrr"] / holdout["metrics"]["fixed4_persistence"]["mrr"] - 1.0),
        },
        "comparisons": comparisons,
        "interpretation": (
            "The prospective holdout remains inconclusive because N=92 made the preregistered top-100 endpoint saturate. "
            "The rank diagnostics are descriptive evidence only and cannot retrospectively promote v5."
        ),
    }
    (args.output / "multiplicity_v5_holdout_diagnostics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    lines = [
        "# OrbitTrace multiplicity-v5 holdout diagnostics",
        "",
        f"Verdict: **`{classification}`**",
        "",
        f"- frozen holdout verdict remains **`{holdout['verdict']}`**",
        f"- family count: **{EXPECTED_FAMILIES}**; qualified labels: **{EXPECTED_QUALIFIED}**",
        f"- multiplicity MRR: **{m['mrr']:.6f}** vs Brown **{b['mrr']:.6f}**, v3 **{holdout['metrics']['v3']['mrr']:.6f}**, fixed4 **{holdout['metrics']['fixed4_persistence']['mrr']:.6f}**",
        f"- multiplicity median rank: **{m['median_rank']}** vs Brown **{b['median_rank']}**, v3 **{holdout['metrics']['v3']['median_rank']}**, fixed4 **{holdout['metrics']['fixed4_persistence']['median_rank']}**",
    ]
    for name in ("brown", "v3", "fixed4_persistence"):
        c = comparisons[name]
        lines.append(f"- vs {name}: **{c['improved']} improved / {c['worsened']} worsened / {c['tied']} tied**, median comparator-minus-M rank delta **{c['median_rank_delta']:.1f}**")
    lines += [
        "",
        "These are artifact-only descriptive diagnostics. No new cutoff or pass rule was tested, and OrbitTrace remains blinded.",
    ]
    (args.output / "MULTIPLICITY_V5_HOLDOUT_DIAGNOSTICS.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
