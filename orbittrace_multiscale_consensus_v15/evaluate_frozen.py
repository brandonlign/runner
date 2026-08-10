#!/usr/bin/env python3
"""Evaluate already-frozen v15 consensus orders against the frozen target-excluded v5 label mapping."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any

ALL_CAPS = (16, 24, 32, 48, 64, 72, 96, 128)
NOMINALS = (32, 64, 96, 128)
LOWER_NOMINALS = (96, 64, 32)
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


def family_projection(families: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        [
            {
                "family_id": str(f["family_id"]),
                "years": [int(x) for x in f["years"]],
                "event_ids": sorted(str(x) for x in f["event_ids"]),
                "component_ids": sorted(str(x) for x in f["component_ids"]),
            }
            for f in families
        ],
        key=lambda row: row["family_id"],
    )


def metrics_for_order(order: list[str], per_label: list[dict[str, Any]], top100_precision: float) -> dict[str, Any]:
    require(len(order) == EXPECTED_FAMILY_COUNT and len(set(order)) == EXPECTED_FAMILY_COUNT, "invalid v15 order universe")
    rank_map = {fid: rank for rank, fid in enumerate(order, start=1)}
    ranks: list[int] = []
    f1s: list[float] = []
    for row in per_label:
        if bool(row.get("qualified")):
            fid = str(row["family_id"])
            require(fid in rank_map, f"qualified family missing from v15 order: {fid}")
            ranks.append(int(rank_map[fid]))
            f1s.append(float(row["f1"]))
    return {
        "eligible_labels": len(per_label),
        "qualified_matches": len(ranks),
        "recovered_at_100": sum(rank <= TOP_K for rank in ranks),
        "recovered_at_500": sum(rank <= 500 for rank in ranks),
        "mrr": float(sum(1.0 / rank for rank in ranks) / len(ranks)) if ranks else 0.0,
        "median_rank": float(statistics.median(ranks)) if ranks else None,
        "macro_f1": float(sum(f1s) / len(f1s)) if f1s else 0.0,
        "top100_dominant_precision": float(top100_precision),
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--orders-dir", type=Path, required=True)
    p.add_argument("--reference-dir", type=Path, required=True)
    for cap in ALL_CAPS:
        p.add_argument(f"--cap-{cap}-dir", dest=f"cap_{cap}_dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()


def main() -> int:
    a = parse_args(); a.output.mkdir(parents=True, exist_ok=True)

    # PRETRUTH checks are complete before this process reads the frozen label-evaluation payload.
    audit = load_json(a.orders_dir / "v15_pretruth_audit.json")
    require(audit["verdict"] == "PASS_V15_PRETRUTH_CONSENSUS_FREEZE", "v15 consensus was not frozen pretruth")
    require(audit["all_v15_orders_frozen_before_labels"] is True, "v15 rank-before-label boundary failed")
    require(audit["sonotaco_2013_2014_access"] is False and audit["maarsy_access"] is False and audit["target_information_access"] is False, "external/target access in v15 rank stage")

    frozen_orders: dict[int, dict[str, Any]] = {}
    for nominal in NOMINALS:
        payload = load_json(a.orders_dir / f"v15_order_nominal{nominal}.json")
        require(payload["labels_read"] is False, f"labels entered nominal {nominal} consensus")
        require(int(payload["family_count"]) == EXPECTED_FAMILY_COUNT, f"family count changed at nominal {nominal}")
        for row in payload["rows"]:
            ranks = [int(x) for x in row["component_ranks_zero_based"]]
            require(len(ranks) == 3, "v15 component count changed")
            require(float(row["v15_median_rank_score"]) == float(statistics.median(ranks)), "v15 median-rank formula changed")
        frozen_orders[nominal] = payload

    # Label-free exact family membership audit across all eight cap artifacts.
    reference_families = load_gzip_json(a.reference_dir / "multiplicity_v5_families.json.gz")
    require(len(reference_families) == EXPECTED_FAMILY_COUNT, "direct-v5 family count changed")
    reference_family_sha = canonical_sha(family_projection(reference_families))
    family_identity: dict[str, bool] = {}
    for cap in ALL_CAPS:
        families = load_gzip_json(getattr(a, f"cap_{cap}_dir") / "v5" / "multiplicity_v5_families.json.gz")
        same = canonical_sha(family_projection(families)) == reference_family_sha
        family_identity[str(cap)] = same
        require(same, f"family membership changed at cap {cap}")

    # FIRST LABEL-EVALUATION READ.
    reference_eval = load_gzip_json(a.reference_dir / "multiplicity_v5_evaluation.json.gz")
    reference_holdout = load_json(a.reference_dir / "multiplicity_v5_holdout.json")
    direct_metrics = reference_holdout["metrics"]["multiplicity"]
    per_label = reference_eval["multiplicity"]["per_label"]
    require(EXPECTED_FAMILY_COUNT <= TOP_K, "top100 precision is not order-invariant")

    metrics: dict[int, dict[str, Any]] = {}
    for nominal in NOMINALS:
        metrics[nominal] = metrics_for_order(
            [str(x) for x in frozen_orders[nominal]["order"]],
            per_label,
            float(direct_metrics["top100_dominant_precision"]),
        )

    integrity = {
        "all_eight_family_memberships_exact": all(family_identity.values()),
        "all_four_orders_same_family_universe": len({frozen_orders[n]["family_universe_sha256"] for n in NOMINALS}) == 1,
        "all_consensus_scores_exact_three_rank_medians": True,
        "all_v15_orders_frozen_before_labels": audit["all_v15_orders_frozen_before_labels"] is True,
        "no_external_or_target_access": True,
    }

    full = metrics[128]
    full_preservation = {
        "recovered_at_100_at_least_direct_v5": int(full["recovered_at_100"]) >= int(direct_metrics["recovered_at_100"]),
        "mrr_at_least_95pct_direct_v5": float(full["mrr"]) + 1e-15 >= 0.95 * float(direct_metrics["mrr"]),
        "top100_precision_loss_at_most_005_from_direct_v5": float(full["top100_dominant_precision"]) + 1e-15 >= float(direct_metrics["top100_dominant_precision"]) - 0.05,
        "qualified_count_unchanged_from_direct_v5": int(full["qualified_matches"]) == int(direct_metrics["qualified_matches"]),
    }

    required_recovery = int(math.ceil(0.90 * int(full["recovered_at_100"])))
    required_mrr = 0.90 * float(full["mrr"])
    robustness: dict[str, Any] = {}
    for nominal in LOWER_NOMINALS:
        m = metrics[nominal]
        gates = {
            "recovered_at_100_at_least_90pct_v15_reference": int(m["recovered_at_100"]) >= required_recovery,
            "mrr_at_least_90pct_v15_reference": float(m["mrr"]) + 1e-15 >= required_mrr,
            "top100_precision_at_least_050": float(m["top100_dominant_precision"]) >= 0.50,
            "top100_precision_loss_at_most_005": float(m["top100_dominant_precision"]) + 1e-15 >= float(full["top100_dominant_precision"]) - 0.05,
            "qualified_count_unchanged": int(m["qualified_matches"]) == int(full["qualified_matches"]),
        }
        robustness[str(nominal)] = {"metrics": m, "gates": gates, "all_pass": all(gates.values())}

    all_pass = all(integrity.values()) and all(full_preservation.values()) and all(row["all_pass"] for row in robustness.values())
    verdict = "PASS_MULTISCALE_CONSENSUS_V15_TARGET_EXCLUDED_DEVELOPMENT" if all_pass else "FAIL_MULTISCALE_CONSENSUS_V15_TARGET_EXCLUDED_DEVELOPMENT"
    result = {
        "verdict": verdict,
        "rule": "median multiplicity rank across full, three-quarter, half episode cardinalities",
        "family_count": EXPECTED_FAMILY_COUNT,
        "family_membership_sha256": reference_family_sha,
        "direct_v5_reference_metrics": direct_metrics,
        "v15_nominal128_metrics": full,
        "full_cardinality_preservation_gates": full_preservation,
        "required_lower_recovery_at_100": required_recovery,
        "required_lower_mrr": required_mrr,
        "integrity_gates": integrity,
        "family_identity_by_cap": family_identity,
        "robustness": robustness,
        "no_best_cap_selection": True,
        "rankings_frozen_before_label_evaluation": True,
        "sonotaco_2013_2014_access": False,
        "maarsy_access": False,
        "target_information_access": False,
        "claim_boundary": "Target-excluded iterative development only; any pass requires a different untouched external validation dataset.",
    }
    (a.output / "v15_development_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
