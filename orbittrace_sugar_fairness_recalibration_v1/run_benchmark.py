#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

YEARS = (2013, 2014)
ROW_SHA = {
    2013: "47fb0b700fbf710c7b061eead343016bd8d182756eb0c7f406507c5739e4c4f8",
    2014: "bc83c113e9a14b1c6e1ef460ca9a40e05df77f3a449fec6064f8910add04c912",
}
EXPECTED = {2013: 18638, 2014: 15400}
SUGAR_SHA = "5b7699a2cf07b9b9ac6dee006c66a9b509af73ee3763093fa333d13e1deca0cb"
CALIBRATION_PERCENTILE = {
    2013: 38.63636363636363,
    2014: 40.36377293701041,
}
BUDGETS = (20, 40, 60, 80, 100)
MIN_RECURRENCE = 100
CLONES = 1000


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_rows(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for year in YEARS:
        path = root / f"sugar_{year}.json"
        require(path.exists(), f"missing {path}")
        require(sha256(path) == ROW_SHA[year], f"row hash drift for {year}")
        annual = json.loads(path.read_text())
        require(len(annual) == EXPECTED[year], f"row count drift for {year}")
        require(all(int(row.get("year", year)) == year for row in annual), f"year field drift for {year}")
        rows.extend(annual)
    ids = [str(row["id"]) for row in rows]
    require(len(ids) == len(set(ids)), "duplicate pooled IDs")
    return rows


def arrays(rows: list[dict[str, Any]]) -> tuple[np.ndarray, ...]:
    fields = ("sol", "ra", "dec", "vg", "ra_sd", "dec_sd", "vg_sd")
    out = tuple(np.asarray([float(row[field]) for row in rows], dtype=np.float64) for field in fields)
    require(all(np.all(np.isfinite(x)) for x in out), "non-finite Sugar input")
    return out


def family_hash(member_ids: list[str]) -> str:
    raw = json.dumps(sorted(member_ids), separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()[:20]


def families_from_assignment(
    rows: list[dict[str, Any]], labels: np.ndarray, probabilities: np.ndarray, masters: list[Any]
) -> list[dict[str, Any]]:
    retained = sorted(
        (m for m in masters if int(m.recurrence) >= MIN_RECURRENCE),
        key=lambda m: int(m.component_id),
    )
    recurrence_by_label = {label: int(master.recurrence) for label, master in enumerate(retained)}
    grouped: dict[int, list[int]] = defaultdict(list)
    for index, label in enumerate(labels):
        if int(label) >= 0:
            grouped[int(label)].append(index)
    families: list[dict[str, Any]] = []
    for label, indices in grouped.items():
        member_ids = sorted(str(rows[i]["id"]) for i in indices)
        probs = np.asarray([probabilities[i] for i in indices], dtype=np.float64)
        families.append({
            "family_id": "SUGAR_CAL_" + family_hash(member_ids),
            "native_label": int(label),
            "member_ids": member_ids,
            "member_count": len(member_ids),
            "recurrence": int(recurrence_by_label[label]),
            "mean_assignment_probability": float(np.mean(probs)),
        })
    families.sort(key=lambda f: (
        -int(f["recurrence"]),
        -float(f["mean_assignment_probability"]),
        -int(f["member_count"]),
        str(f["family_id"]),
    ))
    for rank, family in enumerate(families, start=1):
        family["rank"] = rank
    return families


def deterministic_families(rows: list[dict[str, Any]], sugar: Any, epsilon: float) -> list[dict[str, Any]]:
    sol, ra, dec, vg, *_ = arrays(rows)
    observed = sugar.feature_matrix_from_equatorial(sol, ra, dec, vg)
    clusters = sugar.dbscan_clusters(observed, float(epsilon))
    families: list[dict[str, Any]] = []
    for cluster in clusters:
        ids = sorted(str(rows[int(i)]["id"]) for i in cluster)
        families.append({
            "family_id": "SUGAR_DET_" + family_hash(ids),
            "member_ids": ids,
            "member_count": len(ids),
        })
    families.sort(key=lambda f: (-int(f["member_count"]), str(f["family_id"])))
    for rank, family in enumerate(families, start=1):
        family["rank"] = rank
    return families


def run_pretruth(args: argparse.Namespace) -> None:
    require(args.eval_year in YEARS, "eval year must be 2013 or 2014")
    require(abs(float(args.percentile) - CALIBRATION_PERCENTILE[args.eval_year]) < 1e-12, "calibration percentile drift")
    require(int(args.clones) == CLONES, "binding run requires exactly 1000 clones")
    require(args.sugar_source.exists(), "Sugar source missing")
    require(sha256(args.sugar_source) == SUGAR_SHA, "Sugar source hash drift")

    sugar = load_module(args.sugar_source, "sugar_uncertainty_core_fairness_recalibration")
    require(int(sugar.MIN_SAMPLES) == 5, "Sugar min_samples drift")
    require(abs(float(sugar.MERGE_OVERLAP_FRACTION) - 0.5) < 1e-15, "Sugar overlap drift")
    require(int(sugar.MIN_RECURRENCE) == MIN_RECURRENCE, "Sugar recurrence threshold drift")

    rows = load_rows(args.rows_root)
    sol, ra, dec, vg, ra_sd, dec_sd, vg_sd = arrays(rows)
    observed = sugar.feature_matrix_from_equatorial(sol, ra, dec, vg)
    from sklearn.neighbors import NearestNeighbors
    fourth = NearestNeighbors(n_neighbors=5, algorithm="auto", n_jobs=-1).fit(observed).kneighbors(
        observed, return_distance=True
    )[0][:, 4]
    epsilon = float(np.percentile(fourth, float(args.percentile)))
    require(np.isfinite(epsilon) and epsilon > 0.0, "invalid calibrated epsilon")

    merger = sugar.OverlapGraphMerger(len(rows))
    namespace = f"sonotaco-sugar-fairness-recalibration-v1-eval-{args.eval_year}"
    for iteration in range(CLONES):
        seed = sugar.stable_seed(
            20170209, namespace, 20132014, "ORBITTRACE_VS_SUGAR_CALIBRATED", iteration
        )
        features = sugar.clone_feature_matrix(sol, ra, dec, vg, ra_sd, dec_sd, vg_sd, seed=seed)
        clusters = sugar.dbscan_clusters(features, epsilon)
        merger.add_iteration(iteration, clusters)
        if (iteration + 1) % 50 == 0:
            print(json.dumps({
                "iteration": iteration + 1,
                "cluster_instances": len(merger.parent),
                "edges": merger.edge_count,
            }), flush=True)

    masters = merger.finalize()
    labels, probabilities = sugar.hard_assignment(len(rows), masters, minimum_recurrence=MIN_RECURRENCE)
    families = families_from_assignment(rows, np.asarray(labels), np.asarray(probabilities), masters)
    deterministic = deterministic_families(rows, sugar, epsilon)

    recurrent = json.loads(args.recurrent.read_text())
    require(recurrent.get("truth_accessed") is False, "recurrent pretruth contaminated")
    require(recurrent.get("target_information_access") is False, "recurrent target information accessed")
    rec_candidates = recurrent["routes"]["sugar"]["candidates"]

    result = {
        "role": "EXPOSED_CORRECTIVE_SUGAR_FAIRNESS_PRETRUTH",
        "eval_year": int(args.eval_year),
        "calibration_source_year": 2014 if args.eval_year == 2013 else 2013,
        "calibration_percentile": float(args.percentile),
        "epsilon": epsilon,
        "clone_iterations": CLONES,
        "minimum_recurrence": MIN_RECURRENCE,
        "pooled_event_count": len(rows),
        "truth_accessed_by_this_stage": False,
        "target_information_access": False,
        "sugar_source_sha256": sha256(args.sugar_source),
        "recurrent_source_pretruth_sha256": sha256(args.recurrent),
        "sugar": {
            "retained_families": families,
            "retained_family_count": len(families),
            "master_component_count": len(masters),
            "cluster_instance_count": len(merger.parent),
            "overlap_edge_count": int(merger.edge_count),
            "deterministic_observed_families": deterministic,
            "deterministic_observed_family_count": len(deterministic),
        },
        "recurrent_candidates": rec_candidates,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    path = args.output / f"PRETRUTH_{args.eval_year}.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "pretruth": str(path),
        "sha256": sha256(path),
        "sugar_families": len(families),
        "deterministic_families": len(deterministic),
        "epsilon": epsilon,
    }, indent=2))


def family_members(family: dict[str, Any]) -> set[str]:
    if "event_ids" in family:
        return set(map(str, family["event_ids"]))
    return set(map(str, family["member_ids"]))


def score(families: list[dict[str, Any]], truth: dict[str, str], budget: int | None) -> dict[str, Any]:
    counts = Counter(value for value in truth.values() if value != "SPORADIC")
    labels = sorted(label for label, count in counts.items() if count >= 4)
    ids = set(truth)
    active: list[tuple[int, str, set[str]]] = []
    for index, family in enumerate(families):
        members = family_members(family) & ids
        if members:
            active.append((int(family.get("rank", index + 1)), str(family["family_id"]), members))
    active.sort(key=lambda x: (x[0], x[1]))
    if budget is not None:
        active = active[: int(budget)]

    true_sets = {label: {eid for eid, value in truth.items() if value == label} for label in labels}
    matrix = np.zeros((len(labels), len(active)), dtype=np.float64)
    for i, label in enumerate(labels):
        actual = true_sets[label]
        for j, (_, _, predicted) in enumerate(active):
            overlap = len(actual & predicted)
            if overlap:
                precision = overlap / len(predicted)
                recall = overlap / len(actual)
                matrix[i, j] = 2.0 * precision * recall / (precision + recall)

    n = max(len(labels), len(active))
    cost = np.zeros((n, n), dtype=np.float64)
    if len(labels) and len(active):
        cost[: len(labels), : len(active)] = -matrix
    row_ind, col_ind = linear_sum_assignment(cost)
    values = [
        float(matrix[i, j]) if j < len(active) else 0.0
        for i, j in zip(row_ind.tolist(), col_ind.tolist())
        if i < len(labels)
    ]
    recovered = int(sum(value > 0.5 for value in values))
    return {
        "eligible_showers": len(labels),
        "candidate_used": len(active),
        "macro_f1": float(np.mean(values)) if values else 0.0,
        "recovered_f1_gt_0_5": recovered,
        "recovered_per_candidate": float(recovered / len(active)) if active else 0.0,
    }


def find_truth(root: Path, year: int) -> dict[str, str]:
    matches = list(root.rglob(f"truth_sugar_{year}.json"))
    require(len(matches) == 1, f"expected one truth_sugar_{year}.json, got {matches}")
    return json.loads(matches[0].read_text())


def year_verdict(rows: list[dict[str, Any]]) -> str:
    rec_all = all(
        row["recurrent"]["macro_f1"] >= row["sugar"]["macro_f1"] - 1e-15
        and row["recurrent"]["recovered_f1_gt_0_5"] >= row["sugar"]["recovered_f1_gt_0_5"]
        for row in rows
    )
    rec_strict = any(row["recurrent"]["macro_f1"] > row["sugar"]["macro_f1"] + 1e-15 for row in rows)
    sugar_all = all(
        row["sugar"]["macro_f1"] >= row["recurrent"]["macro_f1"] - 1e-15
        and row["sugar"]["recovered_f1_gt_0_5"] >= row["recurrent"]["recovered_f1_gt_0_5"]
        for row in rows
    )
    sugar_strict = any(row["sugar"]["macro_f1"] > row["recurrent"]["macro_f1"] + 1e-15 for row in rows)
    if rec_all and rec_strict:
        return "RECURRENT_EOM_MATCHED_CAPACITY_WIN"
    if sugar_all and sugar_strict:
        return "SUGAR_MATCHED_CAPACITY_WIN"
    return "MIXED"


def run_evaluate(args: argparse.Namespace) -> None:
    pre = json.loads(args.pretruth.read_text())
    year = int(pre["eval_year"])
    require(year in YEARS, "invalid pretruth eval year")
    require(pre["truth_accessed_by_this_stage"] is False, "pretruth truth flag invalid")
    truth = find_truth(args.truth_root, year)

    sugar_families = pre["sugar"]["retained_families"]
    recurrent = pre["recurrent_candidates"]
    fixed = []
    for budget in BUDGETS:
        fixed.append({
            "budget": budget,
            "sugar": score(sugar_families, truth, budget),
            "recurrent": score(recurrent, truth, budget),
        })
    result = {
        "role": "EXPOSED_CORRECTIVE_SUGAR_FAIRNESS_RESULT",
        "eval_year": year,
        "calibration_source_year": pre["calibration_source_year"],
        "calibration_percentile": pre["calibration_percentile"],
        "epsilon": pre["epsilon"],
        "verdict": year_verdict(fixed),
        "fixed_capacity": fixed,
        "full_output": {
            "sugar": score(sugar_families, truth, None),
            "recurrent": score(recurrent, truth, None),
        },
        "deterministic_observed_sugar": score(pre["sugar"]["deterministic_observed_families"], truth, None),
        "claim_boundary": "Exposed corrective comparison against the frozen Sugar reconstruction; not pristine validation and not the unpublished original-author implementation.",
    }
    args.output.mkdir(parents=True, exist_ok=True)
    path = args.output / f"RESULT_{year}.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2))


def run_summarize(args: argparse.Namespace) -> None:
    results = []
    for year in YEARS:
        matches = list(args.results_root.rglob(f"RESULT_{year}.json"))
        require(len(matches) == 1, f"expected one RESULT_{year}.json, got {matches}")
        results.append(json.loads(matches[0].read_text()))
    verdicts = [result["verdict"] for result in results]
    if verdicts == ["RECURRENT_EOM_MATCHED_CAPACITY_WIN", "RECURRENT_EOM_MATCHED_CAPACITY_WIN"]:
        overall = "RECURRENT_EOM_BETTER_FOR_RANKED_DISCOVERY"
    elif verdicts == ["SUGAR_MATCHED_CAPACITY_WIN", "SUGAR_MATCHED_CAPACITY_WIN"]:
        overall = "SUGAR_BETTER_FOR_RANKED_DISCOVERY"
    else:
        overall = "NO_UNAMBIGUOUS_WINNER"
    summary = {
        "verdict": overall,
        "year_verdicts": {str(result["eval_year"]): result["verdict"] for result in results},
        "results": results,
        "exposed_corrective_evidence": True,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    path = args.output / "SUMMARY.json"
    path.write_text(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    pre = sub.add_parser("pretruth")
    pre.add_argument("--eval-year", type=int, required=True)
    pre.add_argument("--percentile", type=float, required=True)
    pre.add_argument("--clones", type=int, default=CLONES)
    pre.add_argument("--rows-root", type=Path, required=True)
    pre.add_argument("--sugar-source", type=Path, required=True)
    pre.add_argument("--recurrent", type=Path, required=True)
    pre.add_argument("--output", type=Path, required=True)

    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--pretruth", type=Path, required=True)
    evaluate.add_argument("--truth-root", type=Path, required=True)
    evaluate.add_argument("--output", type=Path, required=True)

    summarize = sub.add_parser("summarize")
    summarize.add_argument("--results-root", type=Path, required=True)
    summarize.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "pretruth":
        run_pretruth(args)
    elif args.command == "evaluate":
        run_evaluate(args)
    else:
        run_summarize(args)


if __name__ == "__main__":
    main()
