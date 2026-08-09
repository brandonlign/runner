#!/usr/bin/env python3
"""GMN development lab: can a label-free family-level switch retain P12 halo gains without losing v8 discoveries?"""
from __future__ import annotations

import argparse
import copy
import gzip
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_label_free_sparse_support_v6 import run_development as v6

mult = v6.mult

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1, 13))
CORPUS = "orbittrace-membership-switch-lab-v1"
BLIND = (20.0, 55.0)
EXPECTED_FAMILIES = 226
EXPECTED_V8_QUALIFIED = 95
EXPECTED_V8_RECOVERY100 = 58
EXPECTED_V8_MACRO_F1 = 0.1736657194465356
EXPECTED_V8_TOP100_PRECISION = 0.6884631112636006
EXPECTED_P12_QUALIFIED = 91
EXPECTED_P12_RECOVERY100 = 58
EXPECTED_P12_MACRO_F1 = 0.37661279333940806
EXPECTED_P12_TOP100_PRECISION = 0.6904890277588119
SIZE_BINS = (
    ("4-9", 4, 9),
    ("10-24", 10, 24),
    ("25-49", 25, 49),
    ("50-99", 50, 99),
    ("100+", 100, None),
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--v8-result-json", required=True, type=Path)
    p.add_argument("--p12-dir", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def load_json_gz(path: Path) -> Any:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def q(values: list[float], level: float, default: float = 0.0) -> float:
    if not values:
        return default
    return float(np.quantile(np.asarray(values, dtype=float), level))


def core_from_expanded(family: dict[str, Any]) -> dict[str, Any]:
    added = {str(x) for x in family.get("p2_added_event_ids", [])}
    out = copy.deepcopy(family)
    out["event_ids"] = [str(x) for x in family["event_ids"] if str(x) not in added]
    out["event_count"] = len(out["event_ids"])
    out["p2_added_event_ids"] = []
    out["p2_added_event_count"] = 0
    return out


def annual_bin_metrics(hidden_labels: dict[str, str], families: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for year in YEARS:
        label_counts = Counter(
            label
            for eid, label in hidden_labels.items()
            if int(str(eid)[:4]) == year and label != "SPORADIC"
        )
        rows_by_label: dict[str, dict[str, float]] = {}
        for label, total in sorted(label_counts.items()):
            if total < 4:
                continue
            best = {"f1": 0.0, "precision": 0.0, "recall": 0.0, "overlap": 0}
            for family in families:
                year_ids = [eid for eid in family["event_ids"] if int(str(eid)[:4]) == year]
                if not year_ids:
                    continue
                overlap = sum(hidden_labels.get(eid) == label for eid in year_ids)
                if overlap == 0:
                    continue
                precision = overlap / len(year_ids)
                recall = overlap / total
                f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
                if (f1, precision, overlap) > (best["f1"], best["precision"], best["overlap"]):
                    best = {
                        "f1": float(f1),
                        "precision": float(precision),
                        "recall": float(recall),
                        "overlap": int(overlap),
                    }
            rows_by_label[label] = {"total": int(total), **best}

        bins: dict[str, Any] = {}
        for name, low, high in SIZE_BINS:
            rows = [
                row
                for row in rows_by_label.values()
                if row["total"] >= low and (high is None or row["total"] <= high)
            ]
            bins[name] = {
                "showers": len(rows),
                "mean_f1": float(np.mean([row["f1"] for row in rows])) if rows else 0.0,
                "mean_precision": float(np.mean([row["precision"] for row in rows])) if rows else 0.0,
                "mean_recall": float(np.mean([row["recall"] for row in rows])) if rows else 0.0,
            }
        all_rows = list(rows_by_label.values())
        bins["all"] = {
            "showers": len(all_rows),
            "mean_f1": float(np.mean([row["f1"] for row in all_rows])) if all_rows else 0.0,
            "mean_precision": float(np.mean([row["precision"] for row in all_rows])) if all_rows else 0.0,
            "mean_recall": float(np.mean([row["recall"] for row in all_rows])) if all_rows else 0.0,
        }
        out[str(year)] = bins
    return out


def family_label_f1(hidden_labels: dict[str, str], family: dict[str, Any], total_counts: Counter[str]) -> float:
    ids = [str(x) for x in family["event_ids"]]
    if not ids:
        return 0.0
    counts = Counter(hidden_labels.get(eid, "SPORADIC") for eid in ids)
    best = 0.0
    for label, overlap in counts.items():
        if label == "SPORADIC" or total_counts.get(label, 0) < 4 or overlap <= 0:
            continue
        precision = overlap / len(ids)
        recall = overlap / total_counts[label]
        f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
        best = max(best, float(f1))
    return best


def feature_rows(
    expanded: list[dict[str, Any]],
    assignments: dict[str, dict[str, Any]],
) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for family in expanded:
        fid = str(family["family_id"])
        added = [str(x) for x in family.get("p2_added_event_ids", [])]
        core_count = int(family["event_count"]) - len(added)
        rows = []
        for eid in added:
            row = assignments.get(eid)
            require(row is not None, f"missing P12 assignment for added event {eid}")
            require(str(row["family_id"]) == fid, f"assignment/family mismatch for {eid}")
            rows.append(row)
        responsibilities = [float(row["responsibility"]) for row in rows]
        margins = [float(row["responsibility"]) - float(row["membership_floor"]) for row in rows]
        geometric = []
        for row in rows:
            obs = float(row["d_drift"]) / max(float(row["obs_ceiling"]), 1e-12)
            orb = float(row["d_orb"]) / max(float(row["orb_ceiling"]), 1e-12)
            den_thr = float(row["p11_density_threshold"])
            den = float(row["p11_density_score"]) / max(den_thr, 1e-12) if math.isfinite(den_thr) else 0.0
            geometric.append(max(obs, orb, den))
        by_target = Counter(int(row["target_year"]) for row in rows)
        out[fid] = {
            "core_count": float(core_count),
            "added_count": float(len(added)),
            "expansion_ratio": float(len(added) / max(core_count, 1)),
            "q10_responsibility": q(responsibilities, 0.10, 1.0),
            "median_responsibility": q(responsibilities, 0.50, 1.0),
            "q10_margin": q(margins, 0.10, 1.0),
            "median_margin": q(margins, 0.50, 1.0),
            "q90_geometric_ratio": q(geometric, 0.90, 0.0),
            "target_year_balance": (
                float(min(by_target.get(2022, 0), by_target.get(2023, 0)) / max(max(by_target.values(), default=1), 1))
                if rows else 1.0
            ),
        }
    return out


def threshold_grid(values: list[float], levels: tuple[float, ...], include: float | None = None) -> list[float]:
    if not values:
        return [include] if include is not None else [0.0]
    vals = [float(np.quantile(np.asarray(values, dtype=float), level)) for level in levels]
    if include is not None:
        vals.append(float(include))
    return sorted(set(vals))


def choose_policy(
    core_by_id: dict[str, dict[str, Any]],
    expanded_by_id: dict[str, dict[str, Any]],
    features: dict[str, dict[str, float]],
    max_ratio: float,
    min_q10_resp: float,
    max_geom: float,
) -> tuple[list[dict[str, Any]], list[str]]:
    families = []
    halo_ids = []
    for fid in sorted(core_by_id):
        feat = features[fid]
        use_halo = (
            feat["added_count"] > 0
            and feat["expansion_ratio"] <= max_ratio + 1e-15
            and feat["q10_responsibility"] + 1e-15 >= min_q10_resp
            and feat["q90_geometric_ratio"] <= max_geom + 1e-15
        )
        families.append(expanded_by_id[fid] if use_halo else core_by_id[fid])
        if use_halo:
            halo_ids.append(fid)
    return families, halo_ids


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    expanded = load_json_gz(args.p12_dir / "p12_expanded_families.json.gz")
    decisions = load_json_gz(args.p12_dir / "p12_decisions_pretruth.json.gz")
    require(isinstance(expanded, list) and len(expanded) == EXPECTED_FAMILIES, "P12 family universe changed")
    assignments = decisions["assignments"]
    require(isinstance(assignments, dict), "P12 assignments missing")

    core = [core_from_expanded(family) for family in expanded]
    require([str(f["family_id"]) for f in core] == [str(f["family_id"]) for f in expanded], "family IDs changed")
    core_by_id = {str(f["family_id"]): f for f in core}
    expanded_by_id = {str(f["family_id"]): f for f in expanded}

    runtime = mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = CORPUS
    support.RANKING_VARIANTS = ("persistence",)
    require(float(support.BLIND_LOW) == BLIND[0] and float(support.BLIND_HIGH) == BLIND[1], "target exclusion changed")

    setattr(args, "fixed4_baseline_json", args.v8_result_json)
    _candidate, base, _scorer = support.load_sources(args)
    scan_by_year, _calibration_by_year, hidden_labels, catalogue_sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "development years changed")
    require([row["key"] for row in catalogue_sources] == list(MONTH_KEYS), "month universe changed")

    hard_scored, scoring_summary = mult.score_families(core, scan_by_year, runtime, base)
    order = [str(x) for x in mult.rank_scored(hard_scored, "multiplicity")]
    require(len(order) == EXPECTED_FAMILIES and len(set(order)) == EXPECTED_FAMILIES, "v8 order invalid")

    baseline_eval = mult.evaluate_order(hidden_labels, core, order)
    p12_eval = mult.evaluate_order(hidden_labels, expanded, order)
    require(int(baseline_eval["qualified_matches"]) == EXPECTED_V8_QUALIFIED, "v8 qualified reproduction failed")
    require(int(baseline_eval["recovered_at_100"]) == EXPECTED_V8_RECOVERY100, "v8 recovery@100 reproduction failed")
    require(abs(float(baseline_eval["macro_f1"]) - EXPECTED_V8_MACRO_F1) < 1e-12, "v8 macro reproduction failed")
    require(abs(float(baseline_eval["top100_dominant_precision"]) - EXPECTED_V8_TOP100_PRECISION) < 1e-12, "v8 precision reproduction failed")
    require(int(p12_eval["qualified_matches"]) == EXPECTED_P12_QUALIFIED, "P12 qualified reproduction failed")
    require(int(p12_eval["recovered_at_100"]) == EXPECTED_P12_RECOVERY100, "P12 recovery@100 reproduction failed")
    require(abs(float(p12_eval["macro_f1"]) - EXPECTED_P12_MACRO_F1) < 1e-12, "P12 macro reproduction failed")
    require(abs(float(p12_eval["top100_dominant_precision"]) - EXPECTED_P12_TOP100_PRECISION) < 1e-12, "P12 precision reproduction failed")

    baseline_annual = annual_bin_metrics(hidden_labels, core)
    p12_annual = annual_bin_metrics(hidden_labels, expanded)
    features = feature_rows(expanded, assignments)

    total_counts = Counter(label for label in hidden_labels.values() if label != "SPORADIC")
    oracle = []
    oracle_halo = []
    oracle_deltas = {}
    for fid in sorted(core_by_id):
        core_f1 = family_label_f1(hidden_labels, core_by_id[fid], total_counts)
        halo_f1 = family_label_f1(hidden_labels, expanded_by_id[fid], total_counts)
        use_halo = halo_f1 > core_f1 + 1e-15
        oracle.append(expanded_by_id[fid] if use_halo else core_by_id[fid])
        if use_halo:
            oracle_halo.append(fid)
        oracle_deltas[fid] = {"core_best_f1": core_f1, "halo_best_f1": halo_f1, "delta": halo_f1 - core_f1}
    oracle_eval = mult.evaluate_order(hidden_labels, oracle, order)
    oracle_annual = annual_bin_metrics(hidden_labels, oracle)

    active = [row for row in features.values() if row["added_count"] > 0]
    ratio_grid = threshold_grid([row["expansion_ratio"] for row in active], (0.20, 0.40, 0.60, 0.80, 1.00), include=float("inf"))
    resp_grid = threshold_grid([row["q10_responsibility"] for row in active], (0.00, 0.20, 0.40, 0.60, 0.80))
    geom_grid = threshold_grid([row["q90_geometric_ratio"] for row in active], (0.20, 0.40, 0.60, 0.80, 1.00), include=float("inf"))

    candidates = []
    best = None
    for max_ratio in ratio_grid:
        for min_resp in resp_grid:
            for max_geom in geom_grid:
                families, halo_ids = choose_policy(core_by_id, expanded_by_id, features, max_ratio, min_resp, max_geom)
                ev = mult.evaluate_order(hidden_labels, families, order)
                annual = annual_bin_metrics(hidden_labels, families)
                year_gains = {
                    str(year): float(annual[str(year)]["all"]["mean_f1"] - baseline_annual[str(year)]["all"]["mean_f1"])
                    for year in YEARS
                }
                feasible = (
                    int(ev["qualified_matches"]) >= EXPECTED_V8_QUALIFIED
                    and int(ev["recovered_at_100"]) >= EXPECTED_V8_RECOVERY100
                    and float(ev["top100_dominant_precision"]) >= EXPECTED_V8_TOP100_PRECISION - 0.01
                    and all(year_gains[str(year)] > 0.0 for year in YEARS)
                )
                row = {
                    "max_expansion_ratio": max_ratio,
                    "min_q10_responsibility": min_resp,
                    "max_q90_geometric_ratio": max_geom,
                    "halo_family_count": len(halo_ids),
                    "qualified_matches": int(ev["qualified_matches"]),
                    "recovered_at_100": int(ev["recovered_at_100"]),
                    "macro_f1": float(ev["macro_f1"]),
                    "top100_dominant_precision": float(ev["top100_dominant_precision"]),
                    "annual_all_f1_gain": year_gains,
                    "feasible": bool(feasible),
                }
                candidates.append(row)
                if feasible:
                    key = (
                        float(ev["macro_f1"]),
                        min(year_gains.values()),
                        float(ev["top100_dominant_precision"]),
                        -len(halo_ids),
                    )
                    if best is None or key > best["key"]:
                        best = {
                            "key": key,
                            "row": row,
                            "families": families,
                            "halo_ids": halo_ids,
                            "evaluation": ev,
                            "annual": annual,
                        }

    candidates.sort(
        key=lambda row: (
            bool(row["feasible"]),
            float(row["macro_f1"]),
            min(row["annual_all_f1_gain"].values()),
            float(row["top100_dominant_precision"]),
        ),
        reverse=True,
    )

    best_summary = None
    if best is not None:
        best_summary = {
            **best["row"],
            "halo_family_ids": best["halo_ids"],
            "evaluation": best["evaluation"],
            "annual": best["annual"],
        }

    viability = (
        best is not None
        and float(best["evaluation"]["macro_f1"]) >= 0.30
        and int(best["evaluation"]["qualified_matches"]) >= EXPECTED_V8_QUALIFIED
        and int(best["evaluation"]["recovered_at_100"]) >= EXPECTED_V8_RECOVERY100
        and all(
            best["annual"][str(year)]["all"]["mean_f1"] > baseline_annual[str(year)]["all"]["mean_f1"]
            for year in YEARS
        )
    )
    verdict = "PASS_LABEL_FREE_FAMILY_SWITCH_FEASIBILITY" if viability else "FAIL_LABEL_FREE_FAMILY_SWITCH_FEASIBILITY"

    result = {
        "verdict": verdict,
        "scope": "target-excluded GMN 2022/2023 development-only architecture lab",
        "configuration": {
            "years": list(YEARS),
            "blind_exclusion": list(BLIND),
            "family_count": EXPECTED_FAMILIES,
            "source_membership": "exact frozen P12 drift-conditioned halo",
            "core_membership": "exact v8 core = P12 event_ids minus P12 added ids",
            "ranking": "recomputed exact v8 multiplicity order; never changed by switch",
            "switch_features": [
                "added/core expansion ratio",
                "10th-percentile P12 responsibility",
                "90th-percentile normalized P12 geometry/density slack",
            ],
            "grid_source": "empirical feature quantiles on GMN development only",
            "test_or_external_values_accessed": False,
            "target_information_accessed": False,
        },
        "baseline_v8": baseline_eval,
        "p12_full_halo": p12_eval,
        "baseline_annual": baseline_annual,
        "p12_annual": p12_annual,
        "oracle_family_switch": {
            "halo_family_count": len(oracle_halo),
            "evaluation": oracle_eval,
            "annual": oracle_annual,
            "per_family_best_f1_delta": oracle_deltas,
            "diagnostic_only_uses_development_truth": True,
        },
        "label_free_grid": {
            "candidate_count": len(candidates),
            "feasible_count": sum(bool(row["feasible"]) for row in candidates),
            "best": best_summary,
            "top20": candidates[:20],
        },
        "feature_summary": {
            key: {
                "min": float(min(row[key] for row in active)),
                "median": float(np.median([row[key] for row in active])),
                "max": float(max(row[key] for row in active)),
            }
            for key in ("expansion_ratio", "q10_responsibility", "q90_geometric_ratio")
        },
        "runtime_scoring_summary": scoring_summary,
        "claim_boundary": (
            "Development diagnostic only. It may guide a new label-free membership architecture on GMN. "
            "It does not authorize SonotaCo 2013/2014, MAARSY, or OrbitTrace access."
        ),
    }
    (args.output / "membership_switch_lab_v1.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    (args.output / "MEMBERSHIP_SWITCH_LAB_V1.md").write_text(
        "# OrbitTrace membership-switch lab v1\n\n"
        f"- verdict: `{verdict}`\n"
        f"- v8 macro F1: `{baseline_eval['macro_f1']:.6f}`; qualified `{baseline_eval['qualified_matches']}`\n"
        f"- P12 macro F1: `{p12_eval['macro_f1']:.6f}`; qualified `{p12_eval['qualified_matches']}`\n"
        f"- oracle switch macro F1: `{oracle_eval['macro_f1']:.6f}`; qualified `{oracle_eval['qualified_matches']}`\n"
        + (
            f"- best label-free switch macro F1: `{best['evaluation']['macro_f1']:.6f}`; "
            f"qualified `{best['evaluation']['qualified_matches']}`; halo families `{len(best['halo_ids'])}`\n"
            if best is not None
            else "- no label-free switch met the non-regression constraints\n"
        )
    )
    print(json.dumps({
        "verdict": verdict,
        "oracle_macro_f1": oracle_eval["macro_f1"],
        "oracle_qualified": oracle_eval["qualified_matches"],
        "best_label_free": None if best is None else best["row"],
    }, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
