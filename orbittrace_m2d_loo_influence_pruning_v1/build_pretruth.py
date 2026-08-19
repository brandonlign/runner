#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np

CMR_PRETRUTH_SHA = "8b77e80f305c6f47fc70b359bf03ebadcd6263b5d5ee6a6b9c30efda658bffcb"
BIF_ENDPOINT_SHA = "95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c"
SUPPORT_PRUNED_SHA = "57a6fd0fa680fb56b3d6a8a984682213e0235baadf14b27f241927b2dbb4b50f"
DENOMS = (128, 1024)
BUCKETS = (0, 1, 2, 3)
MIN_SUPPORT = 4


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def members(row: dict[str, Any]) -> frozenset[str]:
    return frozenset(str(x) for x in row["event_ids"])


def member_hash(ids: set[str] | frozenset[str]) -> str:
    return hashlib.sha256(("\n".join(sorted(ids)) + "\n").encode()).hexdigest()[:20]


def family_id(ids: set[str] | frozenset[str]) -> str:
    return hashlib.sha256(("M2D_LOIP_V1|" + "\n".join(sorted(ids)) + "\n").encode()).hexdigest()[:20]


def q90(values: list[int]) -> float:
    req(bool(values), "empty size list")
    return float(np.quantile(np.asarray(values, dtype=float), 0.90))


def burden(values: list[int]) -> float:
    req(bool(values) and all(v > 0 for v in values), "bad size list")
    return float(sum(v * v for v in values) / sum(values))


def exact_m2d(candidate: frozenset[str], bif_rows: list[dict[str, Any]]) -> tuple[float, int, float]:
    n = len(candidate)
    req(n >= MIN_SUPPORT, "candidate below support")
    weighted = 0.0
    raw_area = 0.0
    count = 0
    for row in bif_rows:
        witness = members(row)
        if witness.issubset(candidate):
            area = float(row["persistence_area"])
            req(len(witness) >= MIN_SUPPORT and area > 0.0 and math.isfinite(area), "bad witness")
            weighted += (len(witness) / n) * area
            raw_area += area
            count += 1
    return float(weighted), int(count), float(raw_area)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmr-pretruth", type=Path, required=True)
    ap.add_argument("--bif-endpoint-prelabel", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(sha(a.cmr_pretruth) == CMR_PRETRUTH_SHA, "frozen CMR transport changed")
    req(sha(a.bif_endpoint_prelabel) == BIF_ENDPOINT_SHA, "frozen bifiltration endpoint changed")
    cmr = json.loads(a.cmr_pretruth.read_text())
    bif = json.loads(a.bif_endpoint_prelabel.read_text())

    req(cmr.get("schema") == "ORBITTRACE_CORE_MAJORITY_REGROWTH_V1_PRETRUTH", "wrong CMR schema")
    req(cmr.get("support_pruned_pretruth_sha256") == SUPPORT_PRUNED_SHA, "support-pruned source changed")
    req(
        cmr.get("shower_truth_used") is False
        and cmr.get("target_information_access") is False
        and cmr.get("target_region_events_accessed") is False
        and cmr.get("orbittrace_reveal_access") is False
        and cmr.get("sonotaco_scientific_access") is False,
        "CMR transport firewall failed",
    )
    req(bif.get("schema") == "ORBITTRACE_ANNUAL_DENSITY_BIFILTRATION_GMN_RANKING_V1_PRELABEL", "wrong bif schema")
    req(
        bif.get("shower_truth_used") is False
        and bif.get("target_information_access") is False
        and bif.get("target_region_events_accessed") is False
        and bif.get("sonotaco_2013_2014_access") is False,
        "bif source firewall failed",
    )

    cm = {(int(s["denominator"]), int(s["bucket"])): s for s in cmr["subsets"]}
    fm = {(int(s["denominator"]), int(s["bucket"])): s for s in bif["subsets"]}
    keys = {(d, b) for d in DENOMS for b in BUCKETS}
    req(set(cm) == set(fm) == keys, "panel set changed")

    subsets: list[dict[str, Any]] = []
    loip_top_sizes_all: list[int] = []
    baseline_top_sizes_all: list[int] = []
    total_parent_count = 0
    changed_parent_count = 0
    total_removed_events = 0
    max_removed_events = 0
    all_outputs_supported = True
    all_changed_child_m2d_strictly_higher = True
    recompute_match_max_abs = 0.0
    retained_fractions: list[float] = []

    for key in sorted(keys):
        cs, fs = cm[key], fm[key]
        req(int(cs["event_count"]) == int(fs["event_count"]), f"event count mismatch {key}")
        req(
            {str(y): list(map(str, cs["annual_event_ids"][str(y)])) for y in (2022, 2023)}
            == {str(y): list(map(str, fs["annual_event_ids"][str(y)])) for y in (2022, 2023)},
            f"annual universe mismatch {key}",
        )
        bif_rows = list(fs["bifiltration_candidates"])
        parents = list(cs["support_pruned_baseline_candidates"])
        req(parents and bif_rows, "empty source catalogue")

        rows: list[dict[str, Any]] = []
        panel_changed = 0
        panel_removed = 0
        for parent_rank, parent in enumerate(parents, 1):
            total_parent_count += 1
            parent_set = members(parent)
            parent_n = len(parent_set)
            req(parent_n == int(parent["member_count"]) and parent_n >= MIN_SUPPORT, "parent size/support mismatch")
            req(int(parent["internal_mass_rank"]) == parent_rank, "promoted parent order changed")
            parent_score, parent_witness_count, parent_raw_area = exact_m2d(parent_set, bif_rows)
            recompute_match_max_abs = max(recompute_match_max_abs, abs(parent_score - float(parent["internal_2d_mass"])))
            req(math.isclose(parent_score, float(parent["internal_2d_mass"]), rel_tol=0.0, abs_tol=1e-15), "parent M2D recompute mismatch")

            removed: list[str] = []
            loo_scores: dict[str, float] = {}
            if parent_n > MIN_SUPPORT:
                for event_id in sorted(parent_set):
                    reduced = frozenset(x for x in parent_set if x != event_id)
                    score_minus, _count_minus, _area_minus = exact_m2d(reduced, bif_rows)
                    loo_scores[event_id] = score_minus
                    if score_minus > parent_score:
                        removed.append(event_id)
            keep = frozenset(x for x in parent_set if x not in set(removed))
            output_supported = len(keep) >= MIN_SUPPORT
            all_outputs_supported = all_outputs_supported and output_supported
            req(output_supported, "LOIP produced sub-support output; fail closed")

            child_score, child_witness_count, child_raw_area = exact_m2d(keep, bif_rows)
            changed = keep != parent_set
            if changed:
                changed_parent_count += 1
                panel_changed += 1
                panel_removed += len(removed)
                total_removed_events += len(removed)
                max_removed_events = max(max_removed_events, len(removed))
                retained_fractions.append(len(keep) / parent_n)
                if not child_score > parent_score:
                    all_changed_child_m2d_strictly_higher = False
            else:
                req(not removed, "unchanged membership with removals")

            row = {
                "family_id": family_id(keep),
                "family_hash": member_hash(keep),
                "event_ids": sorted(keep),
                "member_count": len(keep),
                # Discovery rank remains exactly the promoted parent M2D rank/score.
                "internal_2d_mass": float(parent["internal_2d_mass"]),
                "internal_mass_rank": parent_rank,
                "rank": parent_rank,
                "loip_parent_family_hash": str(parent["family_hash"]),
                "loip_parent_family_id": str(parent["family_id"]),
                "loip_parent_member_count": parent_n,
                "loip_parent_m2d_recomputed": parent_score,
                "loip_child_m2d_recomputed": child_score,
                "loip_parent_witness_count": parent_witness_count,
                "loip_child_witness_count": child_witness_count,
                "loip_parent_raw_area_sum": parent_raw_area,
                "loip_child_raw_area_sum": child_raw_area,
                "loip_removed_event_ids": removed,
                "loip_removed_event_count": len(removed),
                "loip_changed": changed,
                "loip_rule": "remove v iff exact M2D(parent_without_v) > exact M2D(parent); simultaneous one-shot",
                "loip_parent_order_preserved": True,
            }
            rows.append(row)

        req(len(rows) == len(parents), "LOIP candidate cardinality changed")
        req(len({str(r["loip_parent_family_hash"]) for r in rows}) == len(rows), "duplicate parent mapping")
        k = int(cs["equal_budget_k"])
        req(k > 0 and len(rows) >= min(k, len(parents)), "LOIP capacity collapsed")
        loip_sizes = [int(r["member_count"]) for r in rows[:k]]
        base_sizes = [int(p["member_count"]) for p in parents[:k]]
        loip_top_sizes_all.extend(loip_sizes)
        baseline_top_sizes_all.extend(base_sizes)

        subsets.append({
            "denominator": key[0],
            "bucket": key[1],
            "event_count": int(cs["event_count"]),
            "annual_event_ids": cs["annual_event_ids"],
            "equal_budget_k": k,
            "loip_candidates": rows,
            "support_pruned_baseline_candidates": parents,
            "mechanism": {
                "parent_count": len(parents),
                "changed_parent_count": panel_changed,
                "removed_event_instances": panel_removed,
            },
            "capacity": {
                "loip_available": len(rows),
                "support_pruned_available": len(parents),
                "budget_k": k,
            },
            "top_budget_size": {
                "loip_mean": mean(loip_sizes),
                "support_pruned_mean": mean(base_sizes),
                "loip_p90": q90(loip_sizes),
                "support_pruned_p90": q90(base_sizes),
                "loip_max": max(loip_sizes),
                "support_pruned_max": max(base_sizes),
                "loip_burden": burden(loip_sizes),
                "support_pruned_burden": burden(base_sizes),
            },
        })

    size_summary = {
        "loip_mean_top_budget_member_count": mean(loip_top_sizes_all),
        "support_pruned_mean_top_budget_member_count": mean(baseline_top_sizes_all),
        "loip_p90_top_budget_member_count": q90(loip_top_sizes_all),
        "support_pruned_p90_top_budget_member_count": q90(baseline_top_sizes_all),
        "loip_max_top_budget_member_count": max(loip_top_sizes_all),
        "support_pruned_max_top_budget_member_count": max(baseline_top_sizes_all),
        "loip_size_biased_top_budget_member_burden": burden(loip_top_sizes_all),
        "support_pruned_size_biased_top_budget_member_burden": burden(baseline_top_sizes_all),
    }
    mechanism_summary = {
        "total_parent_count": total_parent_count,
        "changed_parent_count": changed_parent_count,
        "unchanged_parent_count": total_parent_count - changed_parent_count,
        "total_removed_event_instances": total_removed_events,
        "max_removed_events_from_one_parent": max_removed_events,
        "changed_mean_retained_fraction": mean(retained_fractions) if retained_fractions else None,
        "changed_min_retained_fraction": min(retained_fractions) if retained_fractions else None,
        "max_parent_m2d_recompute_abs_difference": recompute_match_max_abs,
        "ranking_changed_from_support_pruned": False,
    }
    structural_gates = {
        "mechanism_active": changed_parent_count > 0,
        "all_outputs_support_at_least_4": all_outputs_supported,
        "all_changed_child_m2d_strictly_higher": all_changed_child_m2d_strictly_higher,
        "mean_size_strictly_lower_than_support_pruned": size_summary["loip_mean_top_budget_member_count"] < size_summary["support_pruned_mean_top_budget_member_count"],
        "p90_size_strictly_lower_than_support_pruned": size_summary["loip_p90_top_budget_member_count"] < size_summary["support_pruned_p90_top_budget_member_count"],
        "max_size_strictly_lower_than_support_pruned": size_summary["loip_max_top_budget_member_count"] < size_summary["support_pruned_max_top_budget_member_count"],
        "size_biased_burden_strictly_lower_than_support_pruned": size_summary["loip_size_biased_top_budget_member_burden"] < size_summary["support_pruned_size_biased_top_budget_member_burden"],
    }
    structural_pass = all(structural_gates.values())

    out = {
        "schema": "ORBITTRACE_M2D_LOO_INFLUENCE_PRUNING_V1_PRETRUTH",
        "scientific_role": "TARGET_EXCLUDED_GMN_M2D_LOIP_V1_DEVELOPMENT_RANKING",
        "development_status": "GMN_2022_2023_EXPOSED_DEVELOPMENT_AFTER_ECT_V1; NON_GMN_TRANSFER_REQUIRED_FOR_GENERALIZATION",
        "cmr_transport_pretruth_sha256": CMR_PRETRUTH_SHA,
        "bif_endpoint_prelabel_sha256": BIF_ENDPOINT_SHA,
        "support_pruned_pretruth_sha256": SUPPORT_PRUNED_SHA,
        "configuration": {
            "membership_rule": "simultaneous one-shot deletion of each event whose independent exact leave-one-out deletion strictly increases parent M2D",
            "influence_comparison": "exact float: M2D(P\\{v}) > M2D(P)",
            "recursive_recompute": False,
            "ranking_rule": "exact promoted support-pruned parent M2D order",
            "one_candidate_per_parent": True,
            "minimum_support": MIN_SUPPORT,
            "new_tuned_parameters": [],
        },
        "mechanism_summary": mechanism_summary,
        "size_summary": size_summary,
        "structural_gates": structural_gates,
        "structural_pass": structural_pass,
        "subsets": subsets,
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "orbittrace_reveal_access": False,
        "sonotaco_scientific_access": False,
        "post_result_parameter_search": False,
        "interpretation_boundary": "LOIP v1 is designed after prior target-excluded GMN development results. GMN is development evidence only. Any pass must transfer frozen to the designated non-GMN validation stage before OrbitTrace characterization.",
    }
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"structural_pass": structural_pass, "mechanism_summary": mechanism_summary, "size_summary": size_summary, "structural_gates": structural_gates}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
