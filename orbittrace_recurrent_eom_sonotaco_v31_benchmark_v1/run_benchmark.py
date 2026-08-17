#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability
from scipy.optimize import linear_sum_assignment

from orbittrace_recurrent_eom_hdbscan_v1.recurrent_eom import eom_labels, recurrent_stability, selected_eom_nodes

YEARS = (2013, 2014)
ROUTES = ("sugar", "hdbscan")
PANELS = (("sugar", 2013), ("sugar", 2014), ("hdbscan", 2013), ("hdbscan", 2014))
BLIND = (20.0, 55.0)
MIN_CLUSTER_SIZE = 10
MIN_SAMPLES = 10

LABEL_FREE_MANIFEST_SHA = "0a24077f352ddba91c5fea2a102f996d6bea154b1bc769235a4dd916850dba2b"
LABEL_FREE_ROWS_SHA = {
    ("sugar", 2013): "47fb0b700fbf710c7b061eead343016bd8d182756eb0c7f406507c5739e4c4f8",
    ("sugar", 2014): "bc83c113e9a14b1c6e1ef460ca9a40e05df77f3a449fec6064f8910add04c912",
    ("hdbscan", 2013): "2433b556d4a859580ef5431d2307ef34c8fa4c15d42841a2ec7b0c11e5f1f158",
    ("hdbscan", 2014): "206692292b2ca252777e40c13c367880740d8e2576d27615f7ea94b7790e3f55",
}
EXPECTED_COUNTS = {
    ("sugar", 2013): 18638,
    ("sugar", 2014): 15400,
    ("hdbscan", 2013): 16028,
    ("hdbscan", 2014): 13283,
}
V31_RESULT_SHA = "f69555d443f453fd40a769da09b2bbec8bf62cd4a932cd84278bb23305b5ac8e"
V31 = {
    ("sugar", 2013): {"budget": 34, "macro_f1": 0.2719801488280529, "recovered": 16},
    ("sugar", 2014): {"budget": 46, "macro_f1": 0.31529041952487225, "recovered": 17},
    ("hdbscan", 2013): {"budget": 11, "macro_f1": 0.14888037368183737, "recovered": 9},
    ("hdbscan", 2014): {"budget": 9, "macro_f1": 0.15198123772301594, "recovered": 9},
}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def event_field(row: dict[str, Any], name: str) -> float:
    req(name in row and row[name] is not None, f"missing {name}")
    x = float(row[name])
    req(math.isfinite(x), f"nonfinite {name}")
    return x


def normalize_event(row: dict[str, Any], year: int) -> dict[str, Any]:
    eid = str(row["id"])
    row_year = int(row["year"])
    req(row_year == year, f"row year mismatch: {eid} {row_year} != {year}")
    req(eid.startswith(f"SNT{year}:"), f"SonotaCo ID/year mismatch: {eid}")
    sol = event_field(row, "sol") % 360.0
    lon = event_field(row, "sun_lon")
    lat = event_field(row, "ecl_lat")
    vg = event_field(row, "vg")
    req(vg > 0.0, f"nonpositive vg: {eid}")
    req(not (BLIND[0] <= sol <= BLIND[1]), f"protected-region event reached benchmark: {eid}")
    return {"id": eid, "year": year, "sol": sol, "lon": lon, "lat": lat, "vg": vg}


def geo_matrix(events: list[dict[str, Any]]) -> np.ndarray:
    sol = np.radians(np.asarray([e["sol"] for e in events], dtype=float))
    lon = np.radians(np.asarray([e["lon"] for e in events], dtype=float))
    lat = np.radians(np.asarray([e["lat"] for e in events], dtype=float))
    vg = np.asarray([e["vg"] for e in events], dtype=float)
    return np.column_stack((
        np.cos(sol),
        np.sin(sol),
        np.sin(lon) * np.cos(lat),
        np.cos(lon) * np.cos(lat),
        np.sin(lat),
        vg / 72.0,
    ))


def canonical_partition(labels: np.ndarray) -> tuple[tuple[int, ...], ...]:
    groups = []
    for lab in sorted(int(x) for x in np.unique(labels) if int(x) >= 0):
        groups.append(tuple(np.flatnonzero(labels == lab).tolist()))
    return tuple(sorted(groups))


def family_id(route: str, members: tuple[str, ...]) -> str:
    return hashlib.sha256((f"SNT-REOM1|{route}|" + "|".join(members)).encode()).hexdigest()[:20]


def recurrent_candidates(route: str, rows_by_year: dict[int, list[dict[str, Any]]]) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    for year in YEARS:
        events.extend(normalize_event(row, year) for row in rows_by_year[year])
    req(len({e["id"] for e in events}) == len(events), f"duplicate pooled IDs in {route}")
    years = np.asarray([e["year"] for e in events], dtype=np.int64)
    X = geo_matrix(events)
    model = hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(X)
    tree = model.condensed_tree_._raw_tree
    ordinary = compute_stability(tree)
    parent_labels = eom_labels(tree, ordinary)
    req(canonical_partition(model.labels_) == canonical_partition(parent_labels), f"vanilla HDBSCAN extraction mismatch in {route}")
    parent_nodes = selected_eom_nodes(tree, ordinary)
    recurrent, annual = recurrent_stability(tree, years)
    labels = eom_labels(tree, recurrent)
    nodes = selected_eom_nodes(tree, recurrent)
    positive_labels = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive_labels == list(range(len(nodes))), f"compact-label/node mapping changed in {route}")

    candidates: list[dict[str, Any]] = []
    for lab, node in enumerate(nodes):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(events[int(i)]["id"] for i in idx))
        req(len(members) >= MIN_CLUSTER_SIZE, f"subminimum selected cluster {route} node={node}")
        candidates.append({
            "family_id": family_id(route, members),
            "rank": 0,
            "node_id": int(node),
            "event_ids": list(members),
            "member_count": len(members),
            "recurrent_stability": float(recurrent[float(node)]),
            "ordinary_stability": float(ordinary[float(node)]),
        })
    candidates.sort(key=lambda f: (-f["recurrent_stability"], -f["ordinary_stability"], -f["member_count"], f["family_id"]))
    for rank, row in enumerate(candidates, 1):
        row["rank"] = rank
    return {
        "events": len(events),
        "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
        "parent_selected_nodes": list(parent_nodes),
        "successor_selected_nodes": list(nodes),
        "mechanism_active": parent_nodes != nodes,
        "candidate_count": len(candidates),
        "candidate_order_sha256": hashlib.sha256("\n".join(f["family_id"] for f in candidates).encode()).hexdigest(),
        "candidates": candidates,
        "annual_recurrent_stability_sha256": canonical_sha({str(k): list(v) for k, v in sorted(annual.items())}),
    }


def run_pretruth(rows_root: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = rows_root / "label_free_preparation_manifest.json"
    req(sha(manifest_path) == LABEL_FREE_MANIFEST_SHA, "label-free preparation manifest changed")
    manifest = json.loads(manifest_path.read_text())
    req(manifest["verdict"] == "PASS_FINAL_SONOTACO_LABEL_FREE_PREPARATION", "label-free preparation did not pass")
    req(manifest["shower_truth_accessed"] is False, "label-free preparation accessed shower truth")
    req(manifest["target_information_access"] is False, "label-free preparation accessed target information")
    req(manifest["target_region_retained"] is False, "protected target region retained")
    req(manifest["maarsy_scientific_access"] is False, "MAARSY accessed in label-free preparation")

    routes: dict[str, Any] = {}
    for route in ROUTES:
        rows_by_year: dict[int, list[dict[str, Any]]] = {}
        for year in YEARS:
            path = rows_root / f"{route}_{year}.json"
            req(sha(path) == LABEL_FREE_ROWS_SHA[(route, year)], f"{route} {year} label-free rows changed")
            rows = json.loads(path.read_text())
            req(isinstance(rows, list) and len(rows) == EXPECTED_COUNTS[(route, year)], f"{route} {year} row count changed")
            req(all(str(r.get("complex_key")) == "HIDDEN" for r in rows), f"{route} {year} complex key unexpectedly revealed")
            rows_by_year[year] = rows
        routes[route] = recurrent_candidates(route, rows_by_year)

    result = {
        "scientific_role": "PRETRUTH_FROZEN_RECURRENT_EOM_SONOTACO_V31_BENCHMARK_V1",
        "sonotaco_role": "EXPOSED_DEVELOPMENT_ONLY",
        "routes": routes,
        "frozen_hdbscan": {
            "representation": "GEO6",
            "min_cluster_size": MIN_CLUSTER_SIZE,
            "min_samples": MIN_SAMPLES,
            "metric": "euclidean",
            "cluster_selection_method": "eom",
            "cluster_selection_epsilon": 0.0,
            "allow_single_cluster": False,
            "ranking": "recurrent_stability desc, ordinary_stability desc, member_count desc, family_id asc",
        },
        "blind_exclusion": list(BLIND),
        "truth_accessed": False,
        "v31_result_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    path = output / "RECURRENT_EOM_SONOTACO_V1_PRETRUTH.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "pretruth_sha256": sha(path),
        "routes": {r: {k: v for k, v in routes[r].items() if k not in {"candidates", "parent_selected_nodes", "successor_selected_nodes"}} for r in ROUTES},
    }, indent=2, sort_keys=True))
    return 0


def evaluate(families: list[dict[str, Any]], truth: dict[str, str], budget: int) -> dict[str, Any]:
    # Exact v22/v31 evaluator semantics (source blob 88e67cbb3429de701f7e774ad108f2080b4ffb1b).
    from collections import Counter

    counts = Counter(v for v in truth.values() if v != "SPORADIC")
    labels = sorted(k for k, n in counts.items() if n >= 4)
    truth_sets = {label: {eid for eid, value in truth.items() if value == label} for label in labels}
    truth_ids = set(truth)
    active = []
    for family in families:
        members = set(map(str, family["event_ids"])) & truth_ids
        if members:
            active.append((int(family["rank"]), str(family["family_id"]), members))
    active = sorted(active, key=lambda x: (x[0], x[1]))[:int(budget)]
    mat = np.zeros((len(labels), len(active)), dtype=np.float64)
    for i, label in enumerate(labels):
        actual = truth_sets[label]
        for j, (_rank, _fid, pred) in enumerate(active):
            overlap = len(actual & pred)
            if overlap:
                precision = overlap / len(pred)
                recall = overlap / len(actual)
                mat[i, j] = 2 * precision * recall / (precision + recall)
    n = max(len(labels), len(active))
    cost = np.zeros((n, n), dtype=np.float64)
    cost[:len(labels), :len(active)] = -mat
    ri, cj = linear_sum_assignment(cost)
    vals = [float(mat[i, j]) if j < len(active) else 0.0 for i, j in zip(ri.tolist(), cj.tolist()) if i < len(labels)]
    return {
        "eligible_showers": len(labels),
        "macro_f1": float(np.mean(vals)) if vals else 0.0,
        "recovered_f1_gt_0_5": int(sum(x > 0.5 for x in vals)),
        "candidate_used": len(active),
    }


def verify_v31(v31_path: Path) -> dict[tuple[str, int], dict[str, Any]]:
    req(sha(v31_path) == V31_RESULT_SHA, "authoritative v31 result JSON changed")
    result = json.loads(v31_path.read_text())
    req(result["verdict"] == "FAIL_V31_LOCAL_GEOMETRY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT", "unexpected v31 verdict")
    req(int(result["panel_wins"]) == 2, "unexpected v31 panel-win count")
    got: dict[tuple[str, int], dict[str, Any]] = {}
    for panel in result["panels"]:
        key = (str(panel["comparator"]), int(panel["year"]))
        got[key] = panel
    req(set(got) == set(PANELS), "v31 panel set changed")
    for key in PANELS:
        exp = V31[key]
        panel = got[key]
        req(int(panel["budget"]) == exp["budget"], f"v31 budget changed for {key}")
        req(float(panel["candidate_macro_f1"]) == exp["macro_f1"], f"v31 macro-F1 changed for {key}")
        req(int(panel["candidate_recovered_f1_gt_0_5"]) == exp["recovered"], f"v31 recovery changed for {key}")
    return got


def run_evaluate(pretruth_path: Path, truth_root: Path, v31_path: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    pretruth = json.loads(pretruth_path.read_text())
    req(pretruth["scientific_role"] == "PRETRUTH_FROZEN_RECURRENT_EOM_SONOTACO_V31_BENCHMARK_V1", "wrong pretruth role")
    req(pretruth["truth_accessed"] is False and pretruth["v31_result_accessed"] is False, "pretruth payload already exposed")
    req(pretruth["blind_exclusion"] == list(BLIND), "pretruth blind exclusion changed")
    v31 = verify_v31(v31_path)

    panels = []
    for route, year in PANELS:
        truth = json.loads((truth_root / f"truth_{route}_{year}.json").read_text())
        frozen_eval = json.loads((truth_root / f"evaluation_{route}_{year}.json").read_text())
        budget = int(frozen_eval["candidate_budget"]["comparator_budget"])
        req(budget == V31[(route, year)]["budget"], f"established comparator budget changed for {(route, year)}")
        current = evaluate(pretruth["routes"][route]["candidates"], truth, budget)
        lit = frozen_eval["comparator_summary"]
        vm = V31[(route, year)]["macro_f1"]
        vr = V31[(route, year)]["recovered"]
        cm = float(current["macro_f1"])
        cr = int(current["recovered_f1_gt_0_5"])
        lm = float(lit["macro_f1"])
        lr = int(lit["recovered_f1_gt_0_5"])
        panels.append({
            "comparator": route,
            "year": year,
            "budget": budget,
            "recurrent_eom_macro_f1": cm,
            "recurrent_eom_recovered_f1_gt_0_5": cr,
            "v31_macro_f1": vm,
            "v31_recovered_f1_gt_0_5": vr,
            "literature_macro_f1": lm,
            "literature_recovered_f1_gt_0_5": lr,
            "v31_superiority_pair_pass": bool(cm > vm and cr >= vr),
            "literature_superiority_pair_pass": bool(cm > lm and cr >= lr),
            "macro_f1_delta_vs_v31": cm - vm,
            "recovered_delta_vs_v31": cr - vr,
        })

    v31_wins = sum(int(x["v31_superiority_pair_pass"]) for x in panels)
    literature_wins = sum(int(x["literature_superiority_pair_pass"]) for x in panels)
    passed = v31_wins == 4
    result = {
        "verdict": "PASS_RECURRENT_EOM_SONOTACO_V31_SUPERIORITY_V1" if passed else "FAIL_RECURRENT_EOM_SONOTACO_V31_SUPERIORITY_V1",
        "scientific_role": "EXPOSED_SONOTACO_2013_2014_PORTABILITY_AND_V31_COMPARISON_ONLY",
        "sonotaco_role": "EXPOSED_DEVELOPMENT_ONLY",
        "pretruth_sha256": sha(pretruth_path),
        "v31_result_sha256": sha(v31_path),
        "v31_panel_wins": v31_wins,
        "literature_panel_wins": literature_wins,
        "panels": panels,
        "primary_gate": "macro_f1 > exact_v31 AND recovered_f1_gt_0_5 >= exact_v31 on all four panels",
        "method_changed_after_gmn_result": False,
        "post_result_parameter_search": False,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    path = output / "RECURRENT_EOM_SONOTACO_V31_BENCHMARK_V1.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    pre = sub.add_parser("pretruth")
    pre.add_argument("--rows-root", type=Path, required=True)
    pre.add_argument("--output", type=Path, required=True)
    ev = sub.add_parser("evaluate")
    ev.add_argument("--pretruth", type=Path, required=True)
    ev.add_argument("--truth-root", type=Path, required=True)
    ev.add_argument("--v31-result", type=Path, required=True)
    ev.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.command == "pretruth":
        return run_pretruth(a.rows_root, a.output)
    return run_evaluate(a.pretruth, a.truth_root, a.v31_result, a.output)


if __name__ == "__main__":
    raise SystemExit(main())
