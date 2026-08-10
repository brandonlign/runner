#!/usr/bin/env python3
"""Evaluate already-frozen v14 orders against the frozen target-excluded v5 label mapping."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any

CAPS = (32, 64, 96, 128)
LOWER_CAPS = (96, 64, 32)
EXPECTED_FAMILY_COUNT = 92
TOP_K = 100


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def load_gzip_json(path: Path) -> Any:
    with gzip.open(path, "rt") as handle:
        return json.load(handle)


def canonical_family_projection(families: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Hash exact family membership/identity while ignoring descriptive ranking fields."""
    projected = []
    for family in families:
        projected.append({
            "family_id": str(family["family_id"]),
            "years": [int(x) for x in family["years"]],
            "event_ids": sorted(str(x) for x in family["event_ids"]),
            "component_ids": sorted(str(x) for x in family["component_ids"]),
        })
    return sorted(projected, key=lambda row: row["family_id"])


def metrics_for_order(
    order: list[str],
    frozen_per_label: list[dict[str, Any]],
    top100_precision: float,
) -> dict[str, Any]:
    require(len(order) == EXPECTED_FAMILY_COUNT and len(set(order)) == EXPECTED_FAMILY_COUNT, "invalid v14 order universe")
    rank_map = {family_id: rank for rank, family_id in enumerate(order, start=1)}
    qualified_rows = [row for row in frozen_per_label if bool(row.get("qualified"))]
    ranks: list[int] = []
    f1s: list[float] = []
    per_label: list[dict[str, Any]] = []
    for row in frozen_per_label:
        out = dict(row)
        if bool(row.get("qualified")):
            fid = str(row["family_id"])
            require(fid in rank_map, f"qualified family missing from v14 order: {fid}")
            rank = int(rank_map[fid])
            out["rank"] = rank
            ranks.append(rank)
            f1s.append(float(row["f1"]))
        elif row.get("family_id") is not None:
            fid = str(row["family_id"])
            require(fid in rank_map, f"mapped family missing from v14 order: {fid}")
            out["rank"] = int(rank_map[fid])
        per_label.append(out)

    require(len(qualified_rows) == len(ranks), "qualified-rank count mismatch")
    return {
        "eligible_labels": len(frozen_per_label),
        "qualified_matches": len(ranks),
        "recovered_at_100": sum(rank <= TOP_K for rank in ranks),
        "recovered_at_500": sum(rank <= 500 for rank in ranks),
        "mrr": float(sum(1.0 / rank for rank in ranks) / len(ranks)) if ranks else 0.0,
        "median_rank": float(statistics.median(ranks)) if ranks else None,
        "macro_f1": float(sum(f1s) / len(f1s)) if f1s else 0.0,
        # The frozen family universe has 92 families, so top-100 contains the entire
        # unchanged family universe and its mean dominant precision is order-invariant.
        "top100_dominant_precision": float(top100_precision),
        "per_label": per_label,
    }


def compact(metrics: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in metrics.items() if key != "per_label"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--orders-dir", type=Path, required=True)
    p.add_argument("--reference-dir", type=Path, required=True)
    for cap in CAPS:
        p.add_argument(f"--cap-{cap}-dir", dest=f"cap_{cap}_dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()


def main() -> int:
    a = parse_args(); a.output.mkdir(parents=True, exist_ok=True)

    # PRETRUTH FREEZE CHECKS happen before the first label-evaluation file is read.
    pretruth_audit = load_json(a.orders_dir / "v14_pretruth_audit.json")
    require(pretruth_audit["verdict"] == "PASS_V14_PRETRUTH_RANK_FREEZE", "v14 orders were not frozen pretruth")
    require(pretruth_audit["all_rankings_frozen_before_labels"] is True, "rank-before-label boundary failed")
    require(pretruth_audit["sonotaco_2013_2014_access"] is False, "SonotaCo access before v14 evaluation")
    require(pretruth_audit["maarsy_access"] is False, "MAARSY access before v14 evaluation")
    require(pretruth_audit["target_information_access"] is False, "target access before v14 evaluation")

    frozen_orders: dict[int, dict[str, Any]] = {}
    for cap in CAPS:
        payload = load_json(a.orders_dir / f"v14_order_cap{cap}.json")
        require(payload["labels_read"] is False, f"labels entered v14 cap {cap} ranking")
        require(int(payload["family_count"]) == EXPECTED_FAMILY_COUNT, f"unexpected v14 family count at cap {cap}")
        frozen_orders[cap] = payload

    # Family membership is label-free and may be audited before opening the evaluation payload.
    reference_families = load_gzip_json(a.reference_dir / "multiplicity_v5_families.json.gz")
    reference_family_projection = canonical_family_projection(reference_families)
    reference_family_sha = canonical_sha(reference_family_projection)
    require(len(reference_families) == EXPECTED_FAMILY_COUNT, "direct-v5 family count changed")
    family_identity: dict[str, bool] = {}
    for cap in CAPS:
        cap_dir = getattr(a, f"cap_{cap}_dir") / "v5"
        families = load_gzip_json(cap_dir / "multiplicity_v5_families.json.gz")
        same = canonical_sha(canonical_family_projection(families)) == reference_family_sha
        family_identity[str(cap)] = same
        require(same, f"family membership changed at cap {cap}")
        require(frozen_orders[cap]["family_universe_sha256"] == pretruth_audit["family_universe_sha256"], f"v14 order universe changed at cap {cap}")

    # FIRST LABEL-EVALUATION READ. Matching family, qualification and F1 were already
    # frozen by direct v5 and are independent of ranking; v14 changes only their ranks.
    reference_eval = load_gzip_json(a.reference_dir / "multiplicity_v5_evaluation.json.gz")
    reference_holdout = load_json(a.reference_dir / "multiplicity_v5_holdout.json")
    reference_rankings = load_json(a.reference_dir / "multiplicity_v5_rankings.json")
    reference_metrics = reference_holdout["metrics"]["multiplicity"]
    frozen_per_label = reference_eval["multiplicity"]["per_label"]
    require(EXPECTED_FAMILY_COUNT <= TOP_K, "top100 precision is not order-invariant for this family count")

    evaluated: dict[int, dict[str, Any]] = {}
    for cap in CAPS:
        order = [str(x) for x in frozen_orders[cap]["order"]]
        metrics = metrics_for_order(order, frozen_per_label, float(reference_metrics["top100_dominant_precision"]))
        evaluated[cap] = metrics

    direct_multiplicity_order = [str(x) for x in reference_rankings["multiplicity"]]
    integrity = {
        "all_family_membership_exact": all(family_identity.values()),
        "cap128_order_exact_direct_v5_multiplicity": frozen_orders[128]["order"] == direct_multiplicity_order,
        "cap128_metrics_exact_direct_v5_multiplicity": compact(evaluated[128]) == reference_metrics,
        "cap128_order_sha_exact": frozen_orders[128]["v14_order_sha256"] == canonical_sha(direct_multiplicity_order),
        "all_rankings_frozen_before_labels": pretruth_audit["all_rankings_frozen_before_labels"] is True,
        "all_q_in_range_and_between_endpoints": True,
        "q1_rows_exact_multiplicity_endpoint": True,
        "no_external_or_target_access": True,
    }
    for cap in CAPS:
        for row in frozen_orders[cap]["rows"]:
            q = float(row["q"]); rm = float(row["multiplicity_rank_zero_based"]); rf = float(row["fixed4_rank_zero_based"]); fused = float(row["v14_fused_rank_score"])
            integrity["all_q_in_range_and_between_endpoints"] &= 0.0 <= q <= 1.0 and min(rm, rf) - 1e-12 <= fused <= max(rm, rf) + 1e-12
            if abs(q - 1.0) <= 1e-12:
                integrity["q1_rows_exact_multiplicity_endpoint"] &= abs(fused - rm) <= 1e-12

    ref = evaluated[128]
    required_recovery = int(math.ceil(0.90 * int(ref["recovered_at_100"])))
    required_mrr = 0.90 * float(ref["mrr"])
    robustness: dict[str, Any] = {}
    for cap in LOWER_CAPS:
        m = evaluated[cap]
        gates = {
            "recovered_at_100_at_least_90pct_reference": int(m["recovered_at_100"]) >= required_recovery,
            "mrr_at_least_90pct_reference": float(m["mrr"]) + 1e-15 >= required_mrr,
            "top100_precision_at_least_050": float(m["top100_dominant_precision"]) >= 0.50,
            "top100_precision_loss_at_most_005": float(m["top100_dominant_precision"]) + 1e-15 >= float(ref["top100_dominant_precision"]) - 0.05,
            "qualified_count_unchanged": int(m["qualified_matches"]) == int(ref["qualified_matches"]),
        }
        robustness[str(cap)] = {"metrics": compact(m), "gates": gates, "all_pass": all(gates.values())}

    all_pass = all(integrity.values()) and all(row["all_pass"] for row in robustness.values())
    verdict = (
        "PASS_CARDINALITY_SHRUNK_RANK_V14_TARGET_EXCLUDED_DEVELOPMENT"
        if all_pass
        else "FAIL_CARDINALITY_SHRUNK_RANK_V14_TARGET_EXCLUDED_DEVELOPMENT"
    )
    result = {
        "verdict": verdict,
        "rule": "R14=q*r_M+(1-q)*r_F; q=min(year episode size)/128",
        "family_count": EXPECTED_FAMILY_COUNT,
        "family_membership_sha256": reference_family_sha,
        "reference_metrics": compact(ref),
        "required_recovery_at_100": required_recovery,
        "required_mrr": required_mrr,
        "integrity_gates": integrity,
        "family_identity_by_cap": family_identity,
        "robustness": robustness,
        "no_best_cap_selection": True,
        "rankings_frozen_before_label_evaluation": True,
        "sonotaco_2013_2014_access": False,
        "maarsy_access": False,
        "target_information_access": False,
        "claim_boundary": "Target-excluded development only; any pass requires a different untouched external validation dataset.",
    }
    (a.output / "v14_development_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
