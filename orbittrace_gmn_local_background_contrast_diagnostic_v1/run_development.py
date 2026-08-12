#!/usr/bin/env python3
"""Target-excluded GMN diagnostic for candidate local-background contrast."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np

import run_urc_union_ranker as q

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
LOCAL_HALF_WIDTH = 2.0
CORPUS = "orbittrace-gmn-local-background-contrast-diagnostic-v1"
EXPECTED_HARD = 226
P19_PRELABEL_SHA = "276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8"
V8_RESULT_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    for name in (
        "quality_source",
        "support_source_parts",
        "candidate_payload",
        "baseline_payload",
        "scorer_parts",
        "v8_result_json",
        "p19_prelabel_json",
        "output",
    ):
        p.add_argument("--" + name.replace("_", "-"), dest=name, type=Path, required=True)
    return p.parse_args()


def req(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def event_field(row: dict[str, Any], names: Iterable[str]) -> float:
    for name in names:
        if name in row and row[name] is not None:
            value = float(row[name])
            if math.isfinite(value):
                return value
    raise RuntimeError(f"event missing required aliases {tuple(names)}; keys={sorted(row)[:40]}")


def event_id(row: dict[str, Any]) -> str:
    for name in ("id", "event_id", "eventId"):
        if name in row:
            return str(row[name])
    raise RuntimeError("event row lacks ID")


def solar_longitude(row: dict[str, Any]) -> float:
    sol = event_field(row, ("sol", "solar_longitude", "solar_lon", "sol_lon")) % 360.0
    req(not (BLIND[0] <= sol <= BLIND[1]), f"protected-region event reached local-background diagnostic: {event_id(row)}")
    return sol


def circular_diff(a: float, b: float) -> float:
    return abs((float(a) - float(b) + 180.0) % 360.0 - 180.0)


def empirical_separation_auc(member_distances: list[float], background_distances: list[float]) -> float:
    req(bool(member_distances) and bool(background_distances), "AUC requires nonempty member/background distances")
    bg = np.sort(np.asarray(background_distances, dtype=float))
    total = 0.0
    nbg = len(bg)
    for value in member_distances:
        left = int(np.searchsorted(bg, value, side="left"))
        right = int(np.searchsorted(bg, value, side="right"))
        greater = nbg - right
        equal = right - left
        total += (greater + 0.5 * equal) / nbg
    return float(total / len(member_distances))


def annual_contrast(
    family: dict[str, Any],
    year: int,
    scan_rows: list[dict[str, Any]],
    lookup: dict[str, dict[str, Any]],
    support: Any,
    base: Any,
) -> dict[str, Any]:
    centroid = family.get("centroids", {}).get(str(year))
    req(centroid is not None, f"missing annual centroid for {family['family_id']} {year}")
    center_sol = float(centroid["sol"]) % 360.0
    req(not (BLIND[0] <= center_sol <= BLIND[1]), f"protected centroid reached diagnostic: {family['family_id']} {year}")

    ids = [str(eid) for eid in family["event_ids"] if int(str(eid)[:4]) == year]
    req(bool(ids), f"no annual members for {family['family_id']} {year}")
    member_set = set(ids)
    req(len(member_set) == len(ids), f"duplicate annual member IDs for {family['family_id']} {year}")

    member_distances: list[float] = []
    for eid in ids:
        row = lookup.get(eid)
        req(row is not None, f"candidate member absent from target-excluded scan: {eid}")
        _ = solar_longitude(row)
        d = float(support.centroid_distance(row, centroid, base))
        req(math.isfinite(d), f"nonfinite member centroid distance: {eid}")
        member_distances.append(d)

    background_distances: list[float] = []
    for row in scan_rows:
        eid = event_id(row)
        sol = solar_longitude(row)
        if eid in member_set:
            continue
        if circular_diff(sol, center_sol) > LOCAL_HALF_WIDTH:
            continue
        d = float(support.centroid_distance(row, centroid, base))
        req(math.isfinite(d), f"nonfinite background centroid distance: {eid}")
        background_distances.append(d)
    req(bool(background_distances), f"empty fixed local background for {family['family_id']} {year}")

    member_q90 = float(np.quantile(member_distances, 0.90))
    auc = empirical_separation_auc(member_distances, background_distances)
    penetration = float(np.mean(np.asarray(background_distances, dtype=float) <= member_q90))
    return {
        "member_count": len(member_distances),
        "background_count": len(background_distances),
        "member_q90": member_q90,
        "separation_auc": auc,
        "background_penetration": penetration,
    }


def contrast_features(
    family: dict[str, Any],
    scan_by_year: dict[int, list[dict[str, Any]]],
    lookup: dict[str, dict[str, Any]],
    support: Any,
    base: Any,
) -> dict[str, Any]:
    annual = [annual_contrast(family, year, scan_by_year[year], lookup, support, base) for year in YEARS]
    return {
        "worst_auc": float(min(a["separation_auc"] for a in annual)),
        "worst_penetration": float(max(a["background_penetration"] for a in annual)),
        "worst_member_q90": float(max(a["member_q90"] for a in annual)),
        "annual": annual,
    }


def contrast_order(rows: list[dict[str, Any]]) -> list[str]:
    return [
        str(row["family_id"])
        for row in sorted(
            rows,
            key=lambda row: (
                -float(row["features"]["worst_auc"]),
                float(row["features"]["worst_penetration"]),
                float(row["features"]["worst_member_q90"]),
                str(row["family_id"]),
            ),
        )
    ]


def equal_rank_fusion(hard_order: list[str], local_order: list[str]) -> list[str]:
    req(len(hard_order) == len(local_order) and set(hard_order) == set(local_order), "rank universe mismatch")
    h = {fid: i + 1 for i, fid in enumerate(hard_order)}
    c = {fid: i + 1 for i, fid in enumerate(local_order)}
    return sorted(hard_order, key=lambda fid: (h[fid] + c[fid], h[fid], fid))


def metric_subset(metrics: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in metrics.items() if k != "first_rank_by_label"}


def main() -> int:
    a = args()
    a.output.mkdir(parents=True, exist_ok=True)
    req(sha(a.quality_source) == QUALITY_SHA, "active GMN ranker source changed")
    req(sha(a.v8_result_json) == V8_RESULT_SHA, "v8 result changed")
    req(sha(a.p19_prelabel_json) == P19_PRELABEL_SHA, "P19 hard-family prelabel changed")

    payload = json.loads(a.p19_prelabel_json.read_text())
    hard = payload["hard_families"]
    hard_order = [str(x) for x in payload["hard_order"]]
    req(len(hard) == EXPECTED_HARD and len(hard_order) == EXPECTED_HARD, "hard family count changed")
    ids = [str(f["family_id"]) for f in hard]
    req(len(set(ids)) == EXPECTED_HARD and set(ids) == set(hard_order), "hard family identity changed")

    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    runtime = q.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = CORPUS
    support.RANKING_VARIANTS = ("persistence",)
    req(float(support.BLIND_LOW) == BLIND[0] and float(support.BLIND_HIGH) == BLIND[1], "blind interval changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan_by_year, _calibration_by_year, hidden_labels, sources = support.parse_catalogue(base)
    req(sorted(scan_by_year) == list(YEARS), "GMN year universe changed")
    req([row["key"] for row in sources] == list(MONTH_KEYS), "GMN month panel changed")

    # Fail closed on the protected interval before constructing any feature.
    for year in YEARS:
        for row in scan_by_year[year]:
            _ = solar_longitude(row)

    lookup = q.v2.event_lookup(scan_by_year)
    feature_rows = []
    for family in hard:
        feature_rows.append({
            "family_id": str(family["family_id"]),
            "features": contrast_features(family, scan_by_year, lookup, support, base),
        })

    prelabel = {
        "scope": "GMN 2022/2023 target-excluded hard-family local-background contrast",
        "candidate_count": EXPECTED_HARD,
        "blind_exclusion": list(BLIND),
        "local_window_width_deg": 2.0 * LOCAL_HALF_WIDTH,
        "feature_definition": "fixed +/-2 degree solar-longitude background; member-vs-background centroid-distance AUC; q90-envelope background penetration",
        "families": feature_rows,
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "GMN_LOCAL_BACKGROUND_CONTRAST_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    local_order = contrast_order(feature_rows)
    fused_order = equal_rank_fusion(hard_order, local_order)

    # Development truth is interpreted only after the complete label-free feature artifact exists.
    eligible = q.v1.eligible_labels(hidden_labels)
    by = {str(f["family_id"]): f for f in hard}
    truths = {fid: q.v1.family_truth(by[fid], hidden_labels, eligible) for fid in ids}
    base_metrics = q.v1.monotone_metrics(hard, hard_order, truths, eligible)
    local_metrics = q.v1.monotone_metrics(hard, local_order, truths, eligible)
    fused_metrics = q.v1.monotone_metrics(hard, fused_order, truths, eligible)

    gates = {
        "recovered_at_100_strictly_better": int(fused_metrics["recovered_at_100"]) > int(base_metrics["recovered_at_100"]),
        "recovered_at_50_not_worse": int(fused_metrics["recovered_at_50"]) >= int(base_metrics["recovered_at_50"]),
        "top100_precision_not_worse": float(fused_metrics["top100_dominant_precision"]) >= float(base_metrics["top100_dominant_precision"]),
        "mrr_not_worse": float(fused_metrics["mrr"]) >= float(base_metrics["mrr"]),
    }
    passed = all(gates.values())
    verdict = "PASS_GMN_LOCAL_BACKGROUND_CONTRAST_SIGNAL" if passed else "FAIL_GMN_LOCAL_BACKGROUND_CONTRAST_SIGNAL"
    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_MECHANISM_DIAGNOSTIC_ONLY",
        "candidate_count": EXPECTED_HARD,
        "blind_exclusion": list(BLIND),
        "local_window_width_deg": 2.0 * LOCAL_HALF_WIDTH,
        "prelabel_sha256": prelabel_sha,
        "hard_order_sha256": hashlib.sha256("\n".join(hard_order).encode()).hexdigest(),
        "contrast_order_sha256": hashlib.sha256("\n".join(local_order).encode()).hexdigest(),
        "fused_order_sha256": hashlib.sha256("\n".join(fused_order).encode()).hexdigest(),
        "baseline": metric_subset(base_metrics),
        "contrast_only": metric_subset(local_metrics),
        "equal_rank_fusion": metric_subset(fused_metrics),
        "pass_gates": gates,
        "parameter_search": False,
        "background_window_search": False,
        "threshold_search": False,
        "weight_search": False,
        "family_deletion": False,
        "membership_changed": False,
        "candidate_generation_recomputed": False,
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "claim_boundary": "Diagnostic only. PASS may motivate one separately frozen transfer; FAIL permanently closes this exact local-background contrast order plus equal-rank fusion.",
    }
    out = a.output / "GMN_LOCAL_BACKGROUND_CONTRAST_DIAGNOSTIC_V1.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "baseline100": base_metrics["recovered_at_100"],
        "fused100": fused_metrics["recovered_at_100"],
        "baseline50": base_metrics["recovered_at_50"],
        "fused50": fused_metrics["recovered_at_50"],
        "baseline_precision": base_metrics["top100_dominant_precision"],
        "fused_precision": fused_metrics["top100_dominant_precision"],
        "baseline_mrr": base_metrics["mrr"],
        "fused_mrr": fused_metrics["mrr"],
        "prelabel_sha256": prelabel_sha,
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
