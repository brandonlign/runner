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

EMCU_SCHEMA = "ORBITTRACE_ENVELOPE_MULTICORE_UNION_V1_PRETRUTH"
EMCU_ROLE = "TARGET_EXCLUDED_GMN_EMCU_V1_HIERARCHICAL_CANDIDATES_FROZEN_BEFORE_CORE_TRUTH_TEST"
ECT_EVALUATOR_SHA = "43669902a0f891316bdff0650be36d3d7e8e5c32e44417574088d3d0fd1e00a0"
ECT_DEVELOPMENT_STATUS = "GMN_2022_2023_EXPOSED_DEVELOPMENT_AFTER_BWM_CMR_FOCR_DCR_PADCR; NON_GMN_TRANSFER_REQUIRED_FOR_GENERALIZATION"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--emcu-pretruth", type=Path, required=True)
    ap.add_argument("--expected-pretruth-sha", required=True)
    ap.add_argument("--frozen-ect-evaluator", type=Path, required=True)
    ap.add_argument("--frozen-bwm-evaluator", type=Path, required=True)
    for n in (
        "literature-pretruth", "parent-runner", "quality-source", "support-source-parts",
        "candidate-payload", "baseline-payload", "scorer-parts", "v8-result-json", "output",
    ):
        ap.add_argument("--" + n, type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(sha(a.emcu_pretruth) == a.expected_pretruth_sha, "sealed EMCU pretruth changed")
    req(sha(a.frozen_ect_evaluator) == ECT_EVALUATOR_SHA, "frozen ECT evaluator changed")
    pre = json.loads(a.emcu_pretruth.read_text())
    req(pre.get("schema") == EMCU_SCHEMA and pre.get("scientific_role") == EMCU_ROLE, "wrong EMCU identity")
    req(pre.get("structural_pass") is True, "EMCU structural gate failed")
    req(pre.get("configuration", {}).get("extraction_rule") == "set_union_of_all_frozen_CMR_regrown_branches_for_parent", "EMCU union rule changed")
    req(pre.get("configuration", {}).get("branch_selection") == "none_all_branches_included", "branch selection introduced")
    req(pre.get("configuration", {}).get("core_replaces_envelope") is False, "core replacement changed")
    req(pre.get("configuration", {}).get("core_changes_envelope_rank") is False, "core ranking role changed")
    req(pre.get("configuration", {}).get("new_tuned_parameters") == [], "unexpected EMCU tuned parameters")
    req(
        pre.get("shower_truth_used") is False
        and pre.get("target_information_access") is False
        and pre.get("target_region_events_accessed") is False
        and pre.get("orbittrace_reveal_access") is False
        and pre.get("sonotaco_scientific_access") is False,
        "EMCU protected-data firewall",
    )

    compat = copy.deepcopy(pre)
    compat["schema"] = "ORBITTRACE_ENVELOPE_CORE_TOPOMODAL_V1_PRETRUTH"
    compat["scientific_role"] = "TARGET_EXCLUDED_GMN_ECT_V1_HIERARCHICAL_CANDIDATES_FROZEN_BEFORE_CORE_TRUTH_TEST"
    compat["development_status"] = ECT_DEVELOPMENT_STATUS
    compat["configuration"] = {
        "core_replaces_envelope": False,
        "core_changes_envelope_rank": False,
        "new_tuned_parameters": [],
        "one_core_per_envelope": True,
        "core_selection": "EMCU_COMPAT:set_union_of_all_frozen_CMR_regrown_branches_for_parent",
    }

    with tempfile.TemporaryDirectory(prefix="emcu-ect-eval-") as td:
        td_path = Path(td)
        compat_path = td_path / "ECT_COMPAT_FROM_EMCU.json"
        raw_path = td_path / "ECT_COMPAT_RESULT.json"
        compat_path.write_text(json.dumps(compat, indent=2, sort_keys=True) + "\n")
        compat_sha = sha(compat_path)
        cmd = [
            sys.executable, str(a.frozen_ect_evaluator),
            "--ect-pretruth", str(compat_path),
            "--expected-pretruth-sha", compat_sha,
            "--frozen-bwm-evaluator", str(a.frozen_bwm_evaluator),
            "--literature-pretruth", str(a.literature_pretruth),
            "--parent-runner", str(a.parent_runner),
            "--quality-source", str(a.quality_source),
            "--support-source-parts", str(a.support_source_parts),
            "--candidate-payload", str(a.candidate_payload),
            "--baseline-payload", str(a.baseline_payload),
            "--scorer-parts", str(a.scorer_parts),
            "--v8-result-json", str(a.v8_result_json),
            "--output", str(raw_path),
        ]
        subprocess.run(cmd, check=True)
        raw = json.loads(raw_path.read_text())

    req(raw.get("flat_envelope_exactly_support_pruned") is True, "flat envelope identity changed in frozen ECT evaluator")
    flat_gates = dict(raw["flat_envelope_gates"])
    core_gates = dict(raw["core_gates"])
    verdict = "PASS_ENVELOPE_MULTICORE_UNION_V1_GMN_DEVELOPMENT" if all(flat_gates.values()) and all(core_gates.values()) else "FAIL_ENVELOPE_MULTICORE_UNION_V1_GMN_DEVELOPMENT"
    out = {
        "schema": "ORBITTRACE_ENVELOPE_MULTICORE_UNION_V1_GMN_RESULT",
        "scientific_role": "TARGET_EXCLUDED_GMN_EMCU_V1_HIERARCHICAL_DEVELOPMENT_RESULT",
        "verdict": verdict,
        "emcu_pretruth_sha256": sha(a.emcu_pretruth),
        "ect_compat_projection_sha256": compat_sha,
        "frozen_ect_evaluator_sha256": ECT_EVALUATOR_SHA,
        "flat_envelope_exactly_support_pruned": raw["flat_envelope_exactly_support_pruned"],
        "flat_envelope_gates": flat_gates,
        "flat_envelope_routes": raw["flat_envelope_routes"],
        "flat_envelope_scales": raw["flat_envelope_scales"],
        "core_pair_selection": raw["core_pair_selection"],
        "core_routes": raw["core_routes"],
        "core_scales": raw["core_scales"],
        "core_gates": core_gates,
        "paired_rows": raw["paired_rows"],
        "size_summary": pre["size_summary"],
        "mechanism_summary": pre["mechanism_summary"],
        "structural_gates": pre["structural_gates"],
        "compatibility_projection_changed_envelope_memberships": False,
        "compatibility_projection_changed_envelope_ranking": False,
        "compatibility_projection_changed_extraction_memberships": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "orbittrace_reveal_access": False,
        "sonotaco_scientific_access": False,
        "post_result_parameter_search": False,
        "interpretation_boundary": "EMCU is a GMN development successor to failed ECT. It preserves the promoted support-pruned discovery envelope exactly and changes only the separate extraction view from one CMR branch to the union of all frozen CMR branches. A pass authorizes exact frozen SonotaCo transfer only.",
    }
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(verdict)
    print(json.dumps({"flat_envelope_gates": flat_gates, "core_routes": out["core_routes"], "core_scales": out["core_scales"], "core_gates": core_gates, "size_summary": pre["size_summary"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
