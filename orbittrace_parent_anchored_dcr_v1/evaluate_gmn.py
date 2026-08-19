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

PADCR_SCHEMA = "ORBITTRACE_PARENT_ANCHORED_DCR_V1_PRETRUTH"
PADCR_ROLE = "TARGET_EXCLUDED_GMN_PADCR_V1_DEVELOPMENT_RANKING"
BWM_EVALUATOR_SHA = "1578f5eb28fc7e66a2c73f3ef66a6697e20b53b992a7fc979276720047e534d6"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def renamed_comparison(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    out["padcr"] = out.pop("bwm")
    out["padcr_available_candidates"] = out.pop("bwm_available_candidates")
    out["padcr_capacity_shortfall"] = out.pop("bwm_capacity_shortfall")
    out["padcr_evaluated_candidates"] = out.pop("bwm_evaluated_candidates")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--padcr-pretruth", type=Path, required=True)
    ap.add_argument("--expected-pretruth-sha", required=True)
    ap.add_argument("--frozen-bwm-evaluator", type=Path, required=True)
    for n in (
        "literature-pretruth", "parent-runner", "quality-source", "support-source-parts",
        "candidate-payload", "baseline-payload", "scorer-parts", "v8-result-json", "output",
    ):
        ap.add_argument("--" + n, type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(sha(a.padcr_pretruth) == a.expected_pretruth_sha, "sealed PADCR ranking changed")
    req(sha(a.frozen_bwm_evaluator) == BWM_EVALUATOR_SHA, "frozen evaluator changed")
    pre = json.loads(a.padcr_pretruth.read_text())
    req(pre.get("schema") == PADCR_SCHEMA and pre.get("scientific_role") == PADCR_ROLE, "wrong PADCR identity")
    req(pre.get("structural_pass") is True, "PADCR structural gate failed")
    req(pre.get("configuration", {}).get("ranking_rule") == "exact promoted support-pruned parent M2D order; child M2D cannot change discovery rank", "PADCR ranking rule changed")
    req(pre.get("configuration", {}).get("new_tuned_parameters") == [], "unexpected PADCR tuned parameters")
    req(pre.get("configuration", {}).get("one_candidate_per_parent") is True, "PADCR candidate cardinality changed")
    req(
        pre.get("target_information_access") is False
        and pre.get("target_region_events_accessed") is False
        and pre.get("orbittrace_reveal_access") is False
        and pre.get("sonotaco_scientific_access") is False,
        "PADCR protected-data firewall",
    )

    compat = copy.deepcopy(pre)
    compat["schema"] = "ORBITTRACE_BIF_WITNESS_MODULARITY_V1_PRETRUTH"
    compat["scientific_role"] = "TARGET_EXCLUDED_GMN_BWM_V1_RANKING_FROZEN_BEFORE_SHOWER_TRUTH"
    compat["shower_truth_used"] = False
    compat["configuration"] = {"new_tuned_parameters": [], "modularity_resolution": 1.0, "community_passes": 1}
    for subset in compat["subsets"]:
        subset["bwm_candidates"] = subset["padcr_candidates"]
    ss = pre["size_summary"]
    compat["size_summary"] = {
        "bwm_max_top_budget_member_count": ss["padcr_max_top_budget_member_count"],
        "bwm_mean_top_budget_member_count": ss["padcr_mean_top_budget_member_count"],
        "bwm_p90_top_budget_member_count": ss["padcr_p90_top_budget_member_count"],
        "bwm_size_biased_top_budget_member_burden": ss["padcr_size_biased_top_budget_member_burden"],
        "support_pruned_max_top_budget_member_count": ss["support_pruned_max_top_budget_member_count"],
        "support_pruned_mean_top_budget_member_count": ss["support_pruned_mean_top_budget_member_count"],
        "support_pruned_p90_top_budget_member_count": ss["support_pruned_p90_top_budget_member_count"],
        "support_pruned_size_biased_top_budget_member_burden": ss["support_pruned_size_biased_top_budget_member_burden"],
    }
    compat["mechanism_summary"] = pre["mechanism_summary"]

    with tempfile.TemporaryDirectory(prefix="padcr-eval-") as td:
        td_path = Path(td)
        compat_path = td_path / "BWM_COMPAT_FROM_PADCR.json"
        raw_path = td_path / "BWM_COMPAT_RESULT.json"
        compat_path.write_text(json.dumps(compat, indent=2, sort_keys=True) + "\n")
        compat_sha = sha(compat_path)
        cmd = [
            sys.executable, str(a.frozen_bwm_evaluator),
            "--bwm-pretruth", str(compat_path), "--expected-pretruth-sha", compat_sha,
            "--literature-pretruth", str(a.literature_pretruth),
            "--parent-runner", str(a.parent_runner), "--quality-source", str(a.quality_source),
            "--support-source-parts", str(a.support_source_parts), "--candidate-payload", str(a.candidate_payload),
            "--baseline-payload", str(a.baseline_payload), "--scorer-parts", str(a.scorer_parts),
            "--v8-result-json", str(a.v8_result_json), "--output", str(raw_path),
        ]
        subprocess.run(cmd, check=True)
        raw = json.loads(raw_path.read_text())

    routes: dict[str, Any] = {}
    for name, rr in raw["routes"].items():
        cap = dict(rr["capacity"])
        cap["padcr_shortfall_panels"] = cap.pop("bwm_shortfall_panels")
        cap["padcr_total_shortfall"] = cap.pop("bwm_total_shortfall")
        routes[name] = {"padcr": rr["bwm"], "support_pruned": rr["support_pruned"], "literature": rr["literature"], "capacity": cap}
    scales = {name: {"padcr": rr["bwm"], "support_pruned": rr["support_pruned"]} for name, rr in raw["scales"].items()}
    comparisons = [renamed_comparison(row) for row in raw["comparisons"]]
    gates = dict(raw["gates"])
    verdict = "PASS_PARENT_ANCHORED_DCR_V1_GMN_DEVELOPMENT" if all(gates.values()) else "FAIL_PARENT_ANCHORED_DCR_V1_GMN_DEVELOPMENT"
    out = {
        "schema": "ORBITTRACE_PARENT_ANCHORED_DCR_V1_GMN_RESULT",
        "scientific_role": "TARGET_EXCLUDED_GMN_PADCR_V1_DEVELOPMENT_RESULT",
        "development_status": pre["development_status"],
        "verdict": verdict,
        "padcr_pretruth_sha256": sha(a.padcr_pretruth),
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
        "compatibility_projection_changed_memberships": False,
        "compatibility_projection_changed_ranking": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "orbittrace_reveal_access": False,
        "sonotaco_scientific_access": False,
        "post_result_parameter_search": False,
        "interpretation_boundary": "PADCR v1 was designed after the DCR GMN development failure to isolate ranking drift from membership pruning. GMN is development evidence only; a pass requires frozen non-GMN transfer.",
    }
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(verdict)
    print(json.dumps({"routes": routes, "scales": scales, "gates": gates, "size_summary": pre["size_summary"], "mechanism_summary": pre["mechanism_summary"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
