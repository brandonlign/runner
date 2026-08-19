#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

CMR_SCHEMA = "ORBITTRACE_CORE_MAJORITY_REGROWTH_V1_PRETRUTH"
CMR_ROLE = "TARGET_EXCLUDED_GMN_CMR_V1_RANKING_FROZEN_BEFORE_SHOWER_TRUTH"
BWM_EVALUATOR_SHA = "1578f5eb28fc7e66a2c73f3ef66a6697e20b53b992a7fc979276720047e534d6"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def renamed_comparison(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    out["cmr"] = out.pop("bwm")
    out["cmr_available_candidates"] = out.pop("bwm_available_candidates")
    out["cmr_capacity_shortfall"] = out.pop("bwm_capacity_shortfall")
    out["cmr_evaluated_candidates"] = out.pop("bwm_evaluated_candidates")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmr-pretruth", type=Path, required=True)
    ap.add_argument("--expected-pretruth-sha", required=True)
    ap.add_argument("--frozen-bwm-evaluator", type=Path, required=True)
    for n in (
        "literature-pretruth",
        "parent-runner",
        "quality-source",
        "support-source-parts",
        "candidate-payload",
        "baseline-payload",
        "scorer-parts",
        "v8-result-json",
        "output",
    ):
        ap.add_argument("--" + n, type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(sha(a.cmr_pretruth) == a.expected_pretruth_sha, "sealed CMR pretruth changed")
    req(sha(a.frozen_bwm_evaluator) == BWM_EVALUATOR_SHA, "frozen evaluator changed")
    pre = json.loads(a.cmr_pretruth.read_text())
    req(pre.get("schema") == CMR_SCHEMA and pre.get("scientific_role") == CMR_ROLE, "wrong CMR identity")
    req(pre.get("structural_pass") is True, "CMR structural gate did not pass")
    req(
        pre.get("shower_truth_used") is False
        and pre.get("target_information_access") is False
        and pre.get("target_region_events_accessed") is False
        and pre.get("orbittrace_reveal_access") is False
        and pre.get("sonotaco_scientific_access") is False,
        "CMR pretruth firewall",
    )
    req(
        pre.get("configuration", {}).get("new_tuned_parameters") == []
        and pre.get("configuration", {}).get("one_shot") is True,
        "CMR rule changed",
    )

    compat = copy.deepcopy(pre)
    compat["schema"] = "ORBITTRACE_BIF_WITNESS_MODULARITY_V1_PRETRUTH"
    compat["scientific_role"] = "TARGET_EXCLUDED_GMN_BWM_V1_RANKING_FROZEN_BEFORE_SHOWER_TRUTH"
    compat["configuration"] = {
        "new_tuned_parameters": [],
        "modularity_resolution": 1.0,
        "community_passes": 1,
    }
    for subset in compat["subsets"]:
        subset["bwm_candidates"] = subset["cmr_candidates"]
    ss = pre["size_summary"]
    compat["size_summary"] = {
        "bwm_max_top_budget_member_count": ss["cmr_max_top_budget_member_count"],
        "bwm_mean_top_budget_member_count": ss["cmr_mean_top_budget_member_count"],
        "bwm_p90_top_budget_member_count": ss["cmr_p90_top_budget_member_count"],
        "bwm_size_biased_top_budget_member_burden": ss["cmr_size_biased_top_budget_member_burden"],
        "support_pruned_max_top_budget_member_count": ss["support_pruned_max_top_budget_member_count"],
        "support_pruned_mean_top_budget_member_count": ss["support_pruned_mean_top_budget_member_count"],
        "support_pruned_p90_top_budget_member_count": ss["support_pruned_p90_top_budget_member_count"],
        "support_pruned_size_biased_top_budget_member_burden": ss["support_pruned_size_biased_top_budget_member_burden"],
    }
    compat["mechanism_summary"] = pre["mechanism_summary"]

    with tempfile.TemporaryDirectory(prefix="cmr-eval-") as td:
        td_path = Path(td)
        compat_path = td_path / "BWM_COMPAT_FROM_CMR.json"
        raw_path = td_path / "BWM_COMPAT_RESULT.json"
        compat_path.write_text(json.dumps(compat, indent=2, sort_keys=True) + "\n")
        compat_sha = sha(compat_path)
        cmd = [
            sys.executable,
            str(a.frozen_bwm_evaluator),
            "--bwm-pretruth",
            str(compat_path),
            "--expected-pretruth-sha",
            compat_sha,
            "--literature-pretruth",
            str(a.literature_pretruth),
            "--parent-runner",
            str(a.parent_runner),
            "--quality-source",
            str(a.quality_source),
            "--support-source-parts",
            str(a.support_source_parts),
            "--candidate-payload",
            str(a.candidate_payload),
            "--baseline-payload",
            str(a.baseline_payload),
            "--scorer-parts",
            str(a.scorer_parts),
            "--v8-result-json",
            str(a.v8_result_json),
            "--output",
            str(raw_path),
        ]
        subprocess.run(cmd, check=True)
        raw = json.loads(raw_path.read_text())

    routes: dict[str, Any] = {}
    for name, rr in raw["routes"].items():
        cap = dict(rr["capacity"])
        cap["cmr_shortfall_panels"] = cap.pop("bwm_shortfall_panels")
        cap["cmr_total_shortfall"] = cap.pop("bwm_total_shortfall")
        routes[name] = {
            "cmr": rr["bwm"],
            "support_pruned": rr["support_pruned"],
            "literature": rr["literature"],
            "capacity": cap,
        }
    scales = {
        name: {"cmr": rr["bwm"], "support_pruned": rr["support_pruned"]}
        for name, rr in raw["scales"].items()
    }
    comparisons = [renamed_comparison(row) for row in raw["comparisons"]]
    gates = dict(raw["gates"])
    verdict = (
        "PASS_CORE_MAJORITY_REGROWTH_V1_GMN_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_CORE_MAJORITY_REGROWTH_V1_GMN_DEVELOPMENT"
    )
    out = {
        "schema": "ORBITTRACE_CORE_MAJORITY_REGROWTH_V1_GMN_RESULT",
        "scientific_role": "TARGET_EXCLUDED_GMN_CMR_V1_BINDING_QUALITY_DEVELOPMENT",
        "verdict": verdict,
        "cmr_pretruth_sha256": sha(a.cmr_pretruth),
        "bwm_compat_projection_sha256": compat_sha,
        "frozen_evaluator_sha256": BWM_EVALUATOR_SHA,
        "capacity_semantics": raw["capacity_semantics"],
        "routes": routes,
        "scales": scales,
        "size_summary": pre["size_summary"],
        "mechanism_summary": pre["mechanism_summary"],
        "structural_gates": pre["structural_gates"],
        "gates": gates,
        "comparisons": comparisons,
        "method_changed_after_pretruth": False,
        "compatibility_projection_changed_memberships": False,
        "compatibility_projection_changed_ranking": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "orbittrace_reveal_access": False,
        "sonotaco_scientific_access": False,
        "post_result_parameter_search": False,
        "interpretation_boundary": "Target-excluded GMN 2022/2023 is development-exposed. This binding test compares frozen CMR against promoted support-pruned M2D and published-config comparators using the exact frozen BWM evaluator semantics. A pass authorizes transfer testing, not untouched external validation.",
    }
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(verdict)
    print(json.dumps({
        "routes": routes,
        "scales": scales,
        "gates": gates,
        "size_summary": pre["size_summary"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
