#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean
from typing import Any

SOURCE_GIT_BLOB = "fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c"
RESULT_SHA256 = "9128aa8d10c87c9e173b854d48192f3d1d33ba79af8d0a415e706db28da352f2"
RESULT_SCHEMA = "ORBITTRACE_RECURRENT_TOPOMODAL_SUPPORT_MASK_V1_TRUTH"
RESULT_VERDICT = "FAIL_RECURRENT_TOPOMODAL_SUPPORT_MASK_V1"
BUCKETS = (0, 1, 2, 3)
DENOMINATORS = (128, 1024)


def req(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha1(path: Path) -> str:
    payload = path.read_bytes()
    return hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest()


def zero_filled(metrics: dict[str, Any]) -> float:
    eligible = int(metrics["eligible_labels"])
    qualified = int(metrics["qualified_matches"])
    conditional = float(metrics["mrr"])
    req(eligible >= qualified >= 0, "invalid eligible/qualified counts")
    if eligible == 0:
        return 0.0
    if qualified == 0:
        req(conditional == 0.0, "conditional MRR nonzero with no recovered labels")
        return 0.0
    return conditional * qualified / eligible


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evaluator-source", type=Path, required=True)
    ap.add_argument("--sealed-result", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    req(git_blob_sha1(args.evaluator_source) == SOURCE_GIT_BLOB, "frozen evaluator source changed")
    req(sha256(args.sealed_result) == RESULT_SHA256, "sealed support-mask result changed")

    source = args.evaluator_source.read_text()
    expected_source_fragments = [
        'represented = [label for label, rank in first.items() if rank is not None]',
        '"qualified_matches": len(represented)',
        '"mrr": float(np.mean([1.0 / r for r in first.values() if r is not None])) if represented else 0.0',
    ]
    for fragment in expected_source_fragments:
        req(fragment in source, f"expected conditional-MRR source fragment missing: {fragment}")

    result = json.loads(args.sealed_result.read_text())
    req(result["schema"] == RESULT_SCHEMA, "wrong result schema")
    req(result["verdict"] == RESULT_VERDICT, "unexpected sealed endpoint verdict")
    req(result["target_information_access"] is False, "target information accessed")
    req(result["target_region_events_accessed"] is False, "protected target events accessed")
    req(result["sonotaco_2013_2014_access"] is False, "SonotaCo accessed")
    req(result["amos_scientific_access"] is False, "AMOS accessed")
    req(result["maarsy_scientific_access"] is False, "MAARSY accessed")
    req(result["dms_scientific_access"] is False, "DMS accessed")

    panels = list(result["panels"])
    req(len(panels) == 16, "expected sixteen annual panels")
    req(
        {(int(p["denominator"]), int(p["bucket"]), int(p["year"])) for p in panels}
        == {(d, b, y) for d in DENOMINATORS for b in BUCKETS for y in (2022, 2023)},
        "panel set changed",
    )

    panel_rows = []
    scales: dict[str, Any] = {}
    for d in DENOMINATORS:
        subset = [p for p in panels if int(p["denominator"]) == d]
        req(len(subset) == 8, f"wrong panel count d={d}")
        for p in subset:
            parent = p["parent_equal_budget"]
            successor = p["successor_equal_budget"]
            req(int(parent["eligible_labels"]) == int(successor["eligible_labels"]), "eligibility changed between catalogues")
            panel_rows.append(
                {
                    "denominator": d,
                    "bucket": int(p["bucket"]),
                    "year": int(p["year"]),
                    "eligible_labels": int(parent["eligible_labels"]),
                    "parent_qualified": int(parent["qualified_matches"]),
                    "successor_qualified": int(successor["qualified_matches"]),
                    "parent_conditional_mrr": float(parent["mrr"]),
                    "successor_conditional_mrr": float(successor["mrr"]),
                    "parent_zero_filled_mrr": zero_filled(parent),
                    "successor_zero_filled_mrr": zero_filled(successor),
                }
            )

        parent_zero = [zero_filled(p["parent_equal_budget"]) for p in subset]
        successor_zero = [zero_filled(p["successor_equal_budget"]) for p in subset]
        parent_cond = [float(p["parent_equal_budget"]["mrr"]) for p in subset]
        successor_cond = [float(p["successor_equal_budget"]["mrr"]) for p in subset]
        parent_qualified = sum(int(p["parent_equal_budget"]["qualified_matches"]) for p in subset)
        successor_qualified = sum(int(p["successor_equal_budget"]["qualified_matches"]) for p in subset)
        eligible_total = sum(int(p["parent_equal_budget"]["eligible_labels"]) for p in subset)
        req(
            eligible_total == sum(int(p["successor_equal_budget"]["eligible_labels"]) for p in subset),
            "pooled eligibility changed",
        )
        parent_reciprocal_mass = sum(
            float(p["parent_equal_budget"]["mrr"]) * int(p["parent_equal_budget"]["qualified_matches"])
            for p in subset
        )
        successor_reciprocal_mass = sum(
            float(p["successor_equal_budget"]["mrr"]) * int(p["successor_equal_budget"]["qualified_matches"])
            for p in subset
        )
        scales[str(d)] = {
            "panel_count": 8,
            "eligible_total": eligible_total,
            "parent_qualified_total": parent_qualified,
            "successor_qualified_total": successor_qualified,
            "parent_conditional_mrr_panel_mean": mean(parent_cond),
            "successor_conditional_mrr_panel_mean": mean(successor_cond),
            "parent_zero_filled_mrr_panel_mean": mean(parent_zero),
            "successor_zero_filled_mrr_panel_mean": mean(successor_zero),
            "parent_zero_filled_mrr_pooled": parent_reciprocal_mass / eligible_total if eligible_total else 0.0,
            "successor_zero_filled_mrr_pooled": successor_reciprocal_mass / eligible_total if eligible_total else 0.0,
            "parent_reciprocal_mass": parent_reciprocal_mass,
            "successor_reciprocal_mass": successor_reciprocal_mass,
        }

    theorem = {
        "conditional_before": "C = S/n",
        "conditional_after_new_recovery": "C' = (S + x)/(n + 1), x = 1/r_new",
        "difference": "C' - C = (x - C)/(n + 1)",
        "conditional_decreases_iff": "1/r_new < C",
        "zero_filled_before": "Z = S/E",
        "zero_filled_after_new_recovery": "Z' = (S + x)/E",
        "zero_filled_difference": "Z' - Z = x/E > 0 for finite r_new and fixed eligible set E",
    }

    gates = {
        "source_confirms_unrecovered_excluded_from_mrr_denominator": all(f in source for f in expected_source_fragments),
        "formal_nonmonotonicity_confirmed": True,
        "fine_successor_recovery_strictly_higher": scales["1024"]["successor_qualified_total"] > scales["1024"]["parent_qualified_total"],
        "coarse_successor_recovery_strictly_higher": scales["128"]["successor_qualified_total"] > scales["128"]["parent_qualified_total"],
        "fine_conditional_mrr_lower": scales["1024"]["successor_conditional_mrr_panel_mean"] < scales["1024"]["parent_conditional_mrr_panel_mean"],
        "coarse_conditional_mrr_lower": scales["128"]["successor_conditional_mrr_panel_mean"] < scales["128"]["parent_conditional_mrr_panel_mean"],
        "fine_zero_filled_panel_mean_higher": scales["1024"]["successor_zero_filled_mrr_panel_mean"] > scales["1024"]["parent_zero_filled_mrr_panel_mean"],
        "coarse_zero_filled_panel_mean_higher": scales["128"]["successor_zero_filled_mrr_panel_mean"] > scales["128"]["parent_zero_filled_mrr_panel_mean"],
        "fine_zero_filled_pooled_higher": scales["1024"]["successor_zero_filled_mrr_pooled"] > scales["1024"]["parent_zero_filled_mrr_pooled"],
        "coarse_zero_filled_pooled_higher": scales["128"]["successor_zero_filled_mrr_pooled"] > scales["128"]["parent_zero_filled_mrr_pooled"],
    }
    verdict = "AUDIT_MRR_DEFINITION_PROBLEM_CONFIRMED" if all(gates.values()) else "AUDIT_MRR_DEFINITION_PROBLEM_NOT_CONFIRMED"

    out = {
        "schema": "ORBITTRACE_MRR_DEFINITION_AUDIT_V1",
        "scientific_role": "EVALUATION_DESIGN_AUDIT_NO_NEW_TRUTH_ACCESS",
        "verdict": verdict,
        "evaluator_source_git_blob": SOURCE_GIT_BLOB,
        "sealed_result_sha256": RESULT_SHA256,
        "theorem": theorem,
        "panels": panel_rows,
        "scales": scales,
        "gates": gates,
        "retroactive_promotion_authorized": False,
        "scientific_successor_rerun": False,
        "new_shower_truth_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_scientific_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    output_path = args.output / "MRR_DEFINITION_AUDIT_V1.json"
    output_path.write_text(json.dumps(out, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": verdict, "scales": scales, "gates": gates}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
