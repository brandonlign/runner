#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from orbittrace_ecdf_recurrent_rank_hdbscan_v1.ecdf_rank import (
    canonical_membership,
    midrank_ecdf,
    rank_candidates,
)

PASS = "PASS_ECDF_RECURRENT_RANK_HDBSCAN_V1_SYNTHETIC_AUDIT"
FAIL = "FAIL_ECDF_RECURRENT_RANK_HDBSCAN_V1_SYNTHETIC_AUDIT"


def fixture():
    rows = []
    for i, (rec, ordinary, n) in enumerate([
        (0.8, 12.0, 21),
        (0.7, 11.0, 19),
        (0.6, 10.0, 17),
        (0.5, 9.0, 15),
    ]):
        rows.append({
            "family_id": f"F{i}",
            "node_id": 100 + i,
            "event_ids": [f"E{i}-{j}" for j in range(10 + i)],
            "member_count": n,
            "ordinary_stability": ordinary,
            "recurrent_stability": rec,
        })
    # Year-2022 scale is ~1000x year-2023. Within-year ranks disagree at the extremes.
    annual = {
        100: (100.0, 0.1),
        101: (200.0, 0.2),
        102: (300.0, 0.3),
        103: (400.0, 0.1),
    }
    return rows, annual


def order(rows):
    return [str(x["family_id"]) for x in rows]


def transformed(annual, f0, f1):
    return {k: (float(f0(v[0])), float(f1(v[1]))) for k, v in annual.items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    rows, annual = fixture()
    base_members = canonical_membership(rows)
    ranked = rank_candidates(rows, annual)

    affine = transformed(annual, lambda x: 7.0 * x + 19.0, lambda x: 0.25 * x - 2.0)
    exponential = transformed(annual, lambda x: np.exp(x / 500.0), lambda x: np.exp(3.0 * x))
    ranked_affine = rank_candidates(rows, affine)
    ranked_exp = rank_candidates(rows, exponential)

    tied = midrank_ecdf([1.0, 2.0, 2.0, 5.0])
    tied_exact = bool(tied[1] == tied[2])

    # Raw-min order is deliberately dominated by the tiny second-year scale.
    raw_min_order = [
        k for k, _ in sorted(
            annual.items(),
            key=lambda kv: (-min(kv[1][0], kv[1][1]), kv[0]),
        )
    ]
    ecdf_node_order = [int(x["node_id"]) for x in ranked]

    ranked_repeat = rank_candidates(rows, annual)
    checks = {
        "candidate_membership_exactly_preserved": canonical_membership(ranked) == base_members,
        "affine_monotone_invariance": order(ranked_affine) == order(ranked),
        "exponential_monotone_invariance": order(ranked_exp) == order(ranked),
        "exact_ties_receive_identical_midrank": tied_exact,
        "discordant_scale_fixture_changes_raw_min_order": raw_min_order != ecdf_node_order,
        "deterministic_repeated_execution": order(ranked_repeat) == order(ranked),
    }
    passed = all(checks.values())
    out = {
        "verdict": PASS if passed else FAIL,
        "checks": checks,
        "base_order": order(ranked),
        "raw_min_node_order": raw_min_order,
        "ecdf_node_order": ecdf_node_order,
        "network_access": False,
        "gmn_accessed": False,
        "truth_accessed": False,
        "sonotaco_accessed": False,
        "asfn_accessed": False,
        "amos_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    (a.output / "ECDF_RECURRENT_RANK_HDBSCAN_V1_SYNTHETIC_AUDIT.json").write_text(
        json.dumps(out, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
