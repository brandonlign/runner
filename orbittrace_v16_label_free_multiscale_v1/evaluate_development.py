#!/usr/bin/env python3
"""Open GMN truth only after v16 pretruth orders exist, then apply frozen two-panel gates."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import run_holdout_loader_corrected as v5_loader

v5 = v5_loader.core

MIN_FAMILIES = 100
MIN_QUALIFIED = 30
TOP_K = 100


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def compact(metrics: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in metrics.items() if key != "per_label"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--pretruth", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def brown_order_from_frozen_scores(pretruth: dict[str, Any]) -> list[str]:
    scored = pretruth["cap_scores"]["128"]
    years = tuple(int(y) for y in pretruth["years"])
    return [
        str(row["family_id"])
        for row in sorted(
            scored,
            key=lambda row: (
                -min(float(row["per_year"][str(year)]["brown_score"]) for year in years),
                str(row["family_id"]),
            ),
        )
    ]


def main() -> int:
    a = parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    # Pretruth is loaded and every evaluation order is frozen before any label-bearing parser runs.
    pretruth_bytes = a.pretruth.read_bytes()
    pretruth_sha256 = hashlib.sha256(pretruth_bytes).hexdigest()
    pretruth = json.loads(pretruth_bytes)
    years = tuple(int(y) for y in pretruth["years"])
    require(years in ((2020, 2021), (2022, 2023)), f"unexpected development pair {years}")
    require(pretruth["labels_read"] is False, "pretruth reports label access")
    require(pretruth["truth_column_resolved"] is False, "pretruth resolved truth column")
    require(pretruth["calibration_events_used"] == 0, "pretruth used calibration events")
    require(pretruth["sonotaco_access"] is False and pretruth["maarsy_access"] is False, "external data entered pretruth")
    require(pretruth["target_information_access"] is False, "target information entered pretruth")

    families = list(pretruth["families"])
    family_ids = [str(f["family_id"]) for f in families]
    universe = set(family_ids)
    require(len(family_ids) == len(universe), "pretruth family IDs duplicate")
    direct_multiplicity = [str(x) for x in pretruth["cap_orders"]["128"]]
    brown = brown_order_from_frozen_scores(pretruth)
    persistence = [str(x) for x in pretruth["family_diagnostics"]["persistence_order"]]
    consensus = {nominal: [str(x) for x in pretruth["consensus"][str(nominal)]["order"]] for nominal in (128, 96, 64, 32)}
    all_orders = {
        "direct_multiplicity_128": direct_multiplicity,
        "brown_128": brown,
        "label_free_persistence": persistence,
        **{f"v16_nominal_{nominal}": consensus[nominal] for nominal in (128, 96, 64, 32)},
    }
    require(all(len(order) == len(universe) and set(order) == universe for order in all_orders.values()), "pretruth order universe mismatch")
    order_manifest = {
        "pretruth_sha256": pretruth_sha256,
        "years": list(years),
        "family_count": len(families),
        "family_universe_sha256": canonical_sha(sorted(universe)),
        "orders": {name: canonical_sha(order) for name, order in all_orders.items()},
        "written_before_truth_access": True,
    }
    manifest_path = a.output / f"prelabel_order_manifest_{years[0]}_{years[1]}.json"
    manifest_path.write_text(json.dumps(order_manifest, indent=2, sort_keys=True) + "\n")

    # Source/runtime setup is fixed before truth access.
    require(int(v5.EPISODE_SIZE) == 128, "frozen v5 episode identity changed")
    require(all(v5.v3.self_test().values()), "multi-anchor v3 self-test failed")
    require(all(v5.brown.self_test().values()), "Brown self-test failed")
    runtime = v5.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = years
    support.MONTH_KEYS = tuple(f"{year}-{month:02d}" for year in years for month in range(1, 13))
    v5.YEARS = years
    v5.MONTH_KEYS = support.MONTH_KEYS
    v5.TOP_K = TOP_K

    class Args:
        candidate_payload = a.candidate_payload
        baseline_payload = a.baseline_payload
        scorer_parts = a.scorer_parts
        output = a.output

    _candidate, base, _scorer = support.load_sources(Args())

    # FIRST TRUTH ACCESS. All candidate/comparator orders above already exist and are hashed on disk.
    scan_by_year, _calibration_by_year, hidden_labels, sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(years), "truth parser year universe changed")
    require([source["key"] for source in sources] == [f"{year}-{month:02d}" for year in years for month in range(1, 13)], "truth parser source universe changed")
    for year in years:
        ids = sorted(str(row["id"]) for row in scan_by_year[year])
        require(canonical_sha(ids) == pretruth["scan_id_sha256"][str(year)], f"pretruth/truth geometry universe differs for {year}")
        require(len(ids) == int(pretruth["scan_count"][str(year)]), f"pretruth/truth count differs for {year}")

    metrics_full = {name: v5.evaluate_order(hidden_labels, families, order) for name, order in all_orders.items()}
    metrics = {name: compact(value) for name, value in metrics_full.items()}
    qualified_values = {int(value["qualified_matches"]) for value in metrics.values()}
    require(len(qualified_values) == 1, "qualified family matching changed across rankings")
    qualified = next(iter(qualified_values))

    direct = metrics["direct_multiplicity_128"]
    brown_metrics = metrics["brown_128"]
    persistence_metrics = metrics["label_free_persistence"]
    v16_128 = metrics["v16_nominal_128"]

    integrity_gates = {
        "pretruth_frozen_before_truth": manifest_path.is_file(),
        "pretruth_zero_label_access": pretruth["labels_read"] is False and pretruth["truth_column_resolved"] is False,
        "zero_label_dependent_calibration_events": pretruth["calibration_events_used"] == 0,
        "zero_score_threshold_in_family_generation": pretruth["family_diagnostics"]["score_threshold_applied"] is False,
        "all_scan_audits_label_free": all(
            audit["source_labels_used_for_proposals"] is False and audit["calibration_events_used"] == 0
            for audit in pretruth["family_diagnostics"]["scan_audits"]
        ),
        "at_least_24_scannable_bins_each_year": all(
            int(audit["scannable_bin_count"]) >= 24 for audit in pretruth["family_diagnostics"]["scan_audits"]
        ),
        "at_least_100_recurrent_families": len(families) >= MIN_FAMILIES,
        "at_least_30_qualified_known_showers": qualified >= MIN_QUALIFIED,
        "same_family_universe_all_caps": len({pretruth["cap_summaries"][str(cap)]["family_universe_sha256"] for cap in (16,24,32,48,64,72,96,128)}) == 1,
        "brown_equivalence_all_caps": all(
            float(pretruth["cap_summaries"][str(cap)]["max_brown_equivalence_difference"]) <= 1e-10
            for cap in (16,24,32,48,64,72,96,128)
        ),
        "pretruth_truth_geometry_universe_identical": True,
        "external_and_target_access_absent": pretruth["sonotaco_access"] is False and pretruth["maarsy_access"] is False and pretruth["target_information_access"] is False,
    }

    v6_base_gates = {
        "direct_multiplicity_recovers_at_least_one_more_than_brown": int(direct["recovered_at_100"]) >= int(brown_metrics["recovered_at_100"]) + 1,
        "direct_multiplicity_recovers_at_least_90pct_persistence": int(direct["recovered_at_100"]) >= int(math.ceil(0.90 * int(persistence_metrics["recovered_at_100"]))),
        "direct_multiplicity_top100_precision_at_least_050": float(direct["top100_dominant_precision"]) >= 0.50,
    }

    full_preservation_gates = {
        "v16_128_recovery_at_least_direct_multiplicity": int(v16_128["recovered_at_100"]) >= int(direct["recovered_at_100"]),
        "v16_128_mrr_at_least_95pct_direct": float(v16_128["mrr"]) >= 0.95 * float(direct["mrr"]),
        "v16_128_precision_loss_at_most_005": float(direct["top100_dominant_precision"]) - float(v16_128["top100_dominant_precision"]) <= 0.05,
        "v16_128_qualified_unchanged": int(v16_128["qualified_matches"]) == int(direct["qualified_matches"]),
    }

    robustness: dict[str, Any] = {}
    for nominal in (96, 64, 32):
        m = metrics[f"v16_nominal_{nominal}"]
        gates = {
            "recovery_at_least_90pct_v16_128": int(m["recovered_at_100"]) >= int(math.ceil(0.90 * int(v16_128["recovered_at_100"]))),
            "mrr_at_least_90pct_v16_128": float(m["mrr"]) >= 0.90 * float(v16_128["mrr"]),
            "top100_precision_at_least_050": float(m["top100_dominant_precision"]) >= 0.50,
            "precision_loss_at_most_005": float(v16_128["top100_dominant_precision"]) - float(m["top100_dominant_precision"]) <= 0.05,
            "qualified_unchanged": int(m["qualified_matches"]) == int(v16_128["qualified_matches"]),
        }
        robustness[str(nominal)] = {"metrics": m, "gates": gates, "pass": all(gates.values())}

    passed = (
        all(integrity_gates.values())
        and all(v6_base_gates.values())
        and all(full_preservation_gates.values())
        and all(panel["pass"] for panel in robustness.values())
    )
    verdict = "PASS_V16_LABEL_FREE_MULTISCALE_PANEL" if passed else "FAIL_V16_LABEL_FREE_MULTISCALE_PANEL"
    result = {
        "verdict": verdict,
        "years": list(years),
        "pretruth_sha256": pretruth_sha256,
        "order_manifest": order_manifest,
        "family_count": len(families),
        "qualified_known_showers": qualified,
        "metrics": metrics,
        "integrity_gates": integrity_gates,
        "v6_base_gates": v6_base_gates,
        "full_preservation_gates": full_preservation_gates,
        "robustness": robustness,
        "truth_access_after_all_orders_frozen": True,
        "sonotaco_access": False,
        "maarsy_access": False,
        "target_information_access": False,
    }
    out = a.output / f"evaluation_{years[0]}_{years[1]}.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
