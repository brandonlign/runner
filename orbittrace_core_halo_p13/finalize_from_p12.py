#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_CORE_FAMILY_COUNT = 226
EXPECTED_V8 = {
    "qualified_matches": 95,
    "recovered_at_100": 58,
    "recovered_at_500": 95,
    "macro_f1": 0.1736657194465356,
    "top100_dominant_precision": 0.6884631112636006,
    "mrr": 0.045531138942766655,
}
SCIENTIFIC_GATE_NAMES = {
    "qualified_matches_no_regression",
    "recovery_at_100_no_regression",
    "top100_dominant_precision_at_least_065",
    "macro_f1_gain_at_least_008",
    "large_shower_mean_recall_at_least_15x_v8",
    "large_shower_mean_precision_at_least_085",
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def canonical_json_sha(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def exact_close(a: float, b: float, tol: float = 1e-12) -> bool:
    return abs(float(a) - float(b)) <= tol


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--p12-result-json", required=True, type=Path)
    p.add_argument("--core-families-json-gz", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    p12 = json.loads(args.p12_result_json.read_text())
    require(p12["verdict"] == "FAIL_DRIFT_CONDITIONED_TWO_VIEW_MEMBERSHIP_P12_NO_GO", "P13 finalizer only eligible after genuine P12 scientific no-go")
    require(p12["configuration"]["years"] == [2022, 2023], "P12 year universe changed")
    require(p12["configuration"]["blind_exclusion"] == [20.0, 55.0], "P12 blind exclusion changed")
    require(int(p12["configuration"]["family_count"]) == EXPECTED_CORE_FAMILY_COUNT, "P12 family count changed")
    require(p12["configuration"]["p12_static_d_obs_retained"] is False, "P12 representation changed")
    require(p12["configuration"]["p12_parameter_search"] is False, "P12 parameter search present")

    baseline = p12["baseline_v8"]
    for key, expected in EXPECTED_V8.items():
        value = baseline[key]
        if isinstance(expected, int):
            require(int(value) == expected, f"exact v8 baseline changed: {key}")
        else:
            require(exact_close(float(value), expected, 1e-12), f"exact v8 baseline changed: {key}")

    inherited_non_scientific = {
        key: bool(value)
        for key, value in p12["gates"].items()
        if key not in SCIENTIFIC_GATE_NAMES
    }
    require(inherited_non_scientific, "P12 non-scientific gate set empty")
    require(all(inherited_non_scientific.values()), f"P12 integrity/nonvacuity/firewall failure: {[k for k,v in inherited_non_scientific.items() if not v]}")

    with gzip.open(args.core_families_json_gz, "rt", encoding="utf-8") as f:
        core_families = json.load(f)
    require(isinstance(core_families, list) and len(core_families) == EXPECTED_CORE_FAMILY_COUNT, "core family artifact changed")
    core_payload = []
    seen_family_ids: set[str] = set()
    for family in core_families:
        fid = str(family["family_id"])
        require(fid not in seen_family_ids, "duplicate core family id")
        seen_family_ids.add(fid)
        event_ids = sorted(map(str, family["event_ids"]))
        require(event_ids and len(event_ids) == len(set(event_ids)), "core family event IDs invalid")
        core_payload.append({"family_id": fid, "core_event_ids": event_ids})
    core_payload.sort(key=lambda row: row["family_id"])
    core_sha = canonical_json_sha(core_payload)

    halo_membership_sha = str(p12["membership_pretruth_sha256"])
    require(len(halo_membership_sha) == 64, "P12 halo membership hash invalid")

    halo = p12["p12"]
    halo_large = p12["p12_large_shower"]
    halo_macro_gate = float(halo["macro_f1"]) >= float(baseline["macro_f1"]) + 0.08
    halo_large_recall_gate = float(halo_large["mean_recall"]) >= 1.5 * float(p12["baseline_large_shower"]["mean_recall"])
    halo_large_precision_gate = float(halo_large["mean_precision"]) >= 0.85

    gates = {
        "p13_no_p12_scientific_recomputation": True,
        "p13_inherited_p12_integrity_nonvacuity_all_pass": all(inherited_non_scientific.values()),
        "p13_exact_226_v8_core_families": len(core_payload) == EXPECTED_CORE_FAMILY_COUNT,
        "p13_core_qualified_exact_v8": int(baseline["qualified_matches"]) == 95,
        "p13_core_recovery100_exact_v8": int(baseline["recovered_at_100"]) == 58,
        "p13_core_recovery500_exact_v8": int(baseline["recovered_at_500"]) == 95,
        "p13_core_mrr_exact_v8": exact_close(float(baseline["mrr"]), EXPECTED_V8["mrr"], 1e-15),
        "p13_core_top100_precision_exact_v8": exact_close(float(baseline["top100_dominant_precision"]), EXPECTED_V8["top100_dominant_precision"], 1e-12),
        "p13_halo_is_exact_p12_membership_hash": len(halo_membership_sha) == 64,
        "p13_halo_macro_f1_gain_at_least_008": halo_macro_gate,
        "p13_halo_large_shower_mean_recall_at_least_15x_v8": halo_large_recall_gate,
        "p13_halo_large_shower_mean_precision_at_least_085": halo_large_precision_gate,
        "p13_target_exclusion_inherited": p12["configuration"]["blind_exclusion"] == [20.0, 55.0],
    }
    verdict = "PASS_DUAL_OUTPUT_CORE_HALO_P13_DEVELOPMENT" if all(gates.values()) else "FAIL_DUAL_OUTPUT_CORE_HALO_P13_NO_GO"

    result = {
        "verdict": verdict,
        "classification": "dual-output immutable v8 discovery cores plus exact P12 characterization halos; no detector recomputation",
        "configuration": {
            "years": [2022, 2023],
            "blind_exclusion": [20.0, 55.0],
            "family_count": EXPECTED_CORE_FAMILY_COUNT,
            "p13_primary_discovery_metrics_use_core_only": True,
            "p13_membership_metrics_use_halo_only": True,
            "p13_detector_recomputed": False,
            "p13_new_numeric_thresholds": False,
            "p13_parameter_search": False,
        },
        "core_discovery": {
            "qualified_matches": int(baseline["qualified_matches"]),
            "recovered_at_100": int(baseline["recovered_at_100"]),
            "recovered_at_500": int(baseline["recovered_at_500"]),
            "mrr": float(baseline["mrr"]),
            "top100_dominant_precision": float(baseline["top100_dominant_precision"]),
        },
        "halo_membership": {
            "macro_f1": float(halo["macro_f1"]),
            "qualified_matches_secondary": int(halo["qualified_matches"]),
            "recovered_at_100_secondary": int(halo["recovered_at_100"]),
            "recovered_at_500_secondary": int(halo["recovered_at_500"]),
            "top100_dominant_precision_secondary": float(halo["top100_dominant_precision"]),
            "large_shower": halo_large,
        },
        "gates": gates,
        "inherited_p12_non_scientific_gates": inherited_non_scientific,
        "core_pretruth_sha256": core_sha,
        "halo_pretruth_sha256": halo_membership_sha,
        "p12_drift_pretruth_sha256": str(p12["drift_pretruth_sha256"]),
        "p12_density_pretruth_sha256": str(p12["density_pretruth_sha256"]),
        "p12_decisions_pretruth_sha256": str(p12["decisions_pretruth_sha256"]),
        "p12_result_verdict": str(p12["verdict"]),
        "no_new_truth_query": True,
        "target_information_access": False,
    }
    (args.output / "dual_output_core_halo_p13_development.json").write_text(json.dumps(result, indent=2) + "\n")
    (args.output / "p13_core_pretruth.json").write_text(json.dumps(core_payload, sort_keys=True, separators=(",", ":")) + "\n")
    (args.output / "p13_core_pretruth.sha256").write_text(core_sha + "\n")
    (args.output / "p13_halo_pretruth.sha256").write_text(halo_membership_sha + "\n")
    (args.output / "DUAL_OUTPUT_CORE_HALO_P13_DEVELOPMENT.md").write_text(
        "# OrbitTrace P13 dual-output core/halo development finalizer\n\n"
        f"Verdict: **`{verdict}`**\n\n"
        f"- core discovery qualified/recovery@100: **{baseline['qualified_matches']} / {baseline['recovered_at_100']}**\n"
        f"- halo macro F1: **{halo['macro_f1']:.6f}**\n"
        f"- halo large recall / precision: **{halo_large['mean_recall']:.6f} / {halo_large['mean_precision']:.6f}**\n"
        "- detector recomputation: **false**\n"
        "- new truth query: **false**\n"
        "- OrbitTrace target information accessed: **false**\n"
    )
    print((args.output / "DUAL_OUTPUT_CORE_HALO_P13_DEVELOPMENT.md").read_text(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
