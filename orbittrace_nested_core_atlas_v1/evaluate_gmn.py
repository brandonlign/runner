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

ATLAS_SCHEMA = "ORBITTRACE_NESTED_CORE_ATLAS_V1_PRETRUTH"
ATLAS_ROLE = "TARGET_EXCLUDED_GMN_PARENT_PRESERVING_NESTED_EXTRACTION_ATLAS_FROZEN_BEFORE_TRUTH"
BWM_EVALUATOR_SHA = "1578f5eb28fc7e66a2c73f3ef66a6697e20b53b992a7fc979276720047e534d6"
SUPPORT_PRUNED_SHA = "57a6fd0fa680fb56b3d6a8a984682213e0235baadf14b27f241927b2dbb4b50f"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rename_side(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    out["nca_envelope"] = out.pop("bwm")
    out["nca_envelope_available_candidates"] = out.pop("bwm_available_candidates")
    out["nca_envelope_capacity_shortfall"] = out.pop("bwm_capacity_shortfall")
    out["nca_envelope_evaluated_candidates"] = out.pop("bwm_evaluated_candidates")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--atlas-pretruth", type=Path, required=True)
    ap.add_argument("--expected-pretruth-sha", required=True)
    ap.add_argument("--frozen-bwm-evaluator", type=Path, required=True)
    for n in (
        "literature-pretruth", "parent-runner", "quality-source", "support-source-parts",
        "candidate-payload", "baseline-payload", "scorer-parts", "v8-result-json", "output",
    ):
        ap.add_argument("--" + n, type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(sha(a.atlas_pretruth) == a.expected_pretruth_sha, "sealed atlas changed")
    req(sha(a.frozen_bwm_evaluator) == BWM_EVALUATOR_SHA, "frozen evaluator changed")
    pre = json.loads(a.atlas_pretruth.read_text())
    req(pre.get("schema") == ATLAS_SCHEMA and pre.get("scientific_role") == ATLAS_ROLE, "wrong atlas identity")
    req(pre.get("support_pruned_pretruth_sha256") == SUPPORT_PRUNED_SHA, "support-pruned identity changed")
    req(pre.get("structural_pass") is True, "atlas structural gate failed")
    req(pre.get("configuration", {}).get("new_tuned_parameters") == [], "atlas tuning changed")
    req(pre.get("configuration", {}).get("branch_consumes_top_level_capacity") is False, "branch capacity semantics changed")
    req(
        pre.get("shower_truth_used") is False
        and pre.get("target_information_access") is False
        and pre.get("target_region_events_accessed") is False
        and pre.get("orbittrace_reveal_access") is False
        and pre.get("sonotaco_scientific_access") is False,
        "atlas firewall",
    )

    compat = copy.deepcopy(pre)
    compat["schema"] = "ORBITTRACE_BIF_WITNESS_MODULARITY_V1_PRETRUTH"
    compat["scientific_role"] = "TARGET_EXCLUDED_GMN_BWM_V1_RANKING_FROZEN_BEFORE_SHOWER_TRUTH"
    compat["support_pruned_pretruth_sha256"] = SUPPORT_PRUNED_SHA
    compat["configuration"] = {"new_tuned_parameters": [], "modularity_resolution": 1.0, "community_passes": 1}
    compat["shower_truth_used"] = False
    for subset in compat["subsets"]:
        env = subset["envelope_candidates"]
        subset["bwm_candidates"] = env
        subset["support_pruned_baseline_candidates"] = env
    ss = pre["structure_summary"]
    compat["size_summary"] = {
        "bwm_max_top_budget_member_count": ss["envelope_max_top_budget_member_count"],
        "bwm_mean_top_budget_member_count": ss["envelope_mean_top_budget_member_count"],
        "bwm_p90_top_budget_member_count": ss["envelope_p90_top_budget_member_count"],
        "bwm_size_biased_top_budget_member_burden": ss["envelope_size_biased_top_budget_burden"],
        "support_pruned_max_top_budget_member_count": ss["envelope_max_top_budget_member_count"],
        "support_pruned_mean_top_budget_member_count": ss["envelope_mean_top_budget_member_count"],
        "support_pruned_p90_top_budget_member_count": ss["envelope_p90_top_budget_member_count"],
        "support_pruned_size_biased_top_budget_member_burden": ss["envelope_size_biased_top_budget_burden"],
    }
    compat["mechanism_summary"] = {
        "parent_count": ss["parent_count"],
        "branch_count": ss["branch_count"],
        "top_level_identity_preserved": True,
    }

    with tempfile.TemporaryDirectory(prefix="nca-flat-eval-") as td:
        td_path = Path(td)
        compat_path = td_path / "BWM_COMPAT_FROM_NCA.json"
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
        cap["nca_envelope_shortfall_panels"] = cap.pop("bwm_shortfall_panels")
        cap["nca_envelope_total_shortfall"] = cap.pop("bwm_total_shortfall")
        routes[name] = {
            "nca_envelope": rr["bwm"],
            "support_pruned": rr["support_pruned"],
            "literature": rr["literature"],
            "capacity": cap,
        }
    scales = {
        name: {"nca_envelope": rr["bwm"], "support_pruned": rr["support_pruned"]}
        for name, rr in raw["scales"].items()
    }
    comparisons = [rename_side(row) for row in raw["comparisons"]]

    exact_equal = True
    for rr in routes.values():
        exact_equal = exact_equal and rr["nca_envelope"] == rr["support_pruned"]
    for rr in scales.values():
        exact_equal = exact_equal and rr["nca_envelope"] == rr["support_pruned"]
    gates = dict(raw["gates"])
    gates["top_level_metrics_exactly_equal_support_pruned"] = exact_equal
    gates["nested_structure_active"] = bool(pre["structural_gates"]["atlas_active"])
    verdict = "PASS_NESTED_CORE_ATLAS_V1_GMN_DEVELOPMENT" if all(gates.values()) else "FAIL_NESTED_CORE_ATLAS_V1_GMN_DEVELOPMENT"

    out = {
        "schema": "ORBITTRACE_NESTED_CORE_ATLAS_V1_GMN_RESULT",
        "scientific_role": "TARGET_EXCLUDED_GMN_PARENT_PRESERVING_ATLAS_DEVELOPMENT_RESULT",
        "verdict": verdict,
        "atlas_pretruth_sha256": sha(a.atlas_pretruth),
        "bwm_compat_projection_sha256": compat_sha,
        "frozen_evaluator_sha256": BWM_EVALUATOR_SHA,
        "capacity_semantics": raw["capacity_semantics"],
        "routes": routes,
        "scales": scales,
        "comparisons": comparisons,
        "gates": gates,
        "structure_summary": pre["structure_summary"],
        "structural_gates": pre["structural_gates"],
        "compatibility_projection_changed_top_level_memberships": False,
        "compatibility_projection_changed_top_level_ranking": False,
        "nested_branches_scored_as_flat_discoveries": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "orbittrace_reveal_access": False,
        "sonotaco_scientific_access": False,
        "post_result_parameter_search": False,
        "interpretation_boundary": "The GMN flat discovery benchmark scores only exact promoted parent envelopes, so literature superiority is preserved rather than re-earned by child substitution. Nested BWM/CMR branches are an additional extraction representation. Because GMN is development-exposed, the next scientific test is exact frozen SonotaCo transfer before any target-containing characterization.",
    }
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(verdict)
    print(json.dumps({"routes": routes, "scales": scales, "gates": gates, "structure_summary": pre["structure_summary"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
