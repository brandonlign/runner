#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability

from orbittrace_recurrent_eom_hdbscan_v1.recurrent_eom import recurrent_stability, selected_eom_nodes, eom_labels
from orbittrace_recurrent_eom_sonotaco_v31_benchmark_v1.run_benchmark import normalize_event, geo_matrix, canonical_partition

YEARS = (2013, 2014)
ROUTES = ("sugar", "hdbscan")
PANELS = (("sugar", 2013), ("sugar", 2014), ("hdbscan", 2013), ("hdbscan", 2014))
MIN_CLUSTER_SIZE = 10
MIN_SAMPLES = 10
BLIND = (20.0, 55.0)

EXPECTED_PARENT_PRETRUTH_SHA = "c6afbc0c3443b6c34e3f90b0f63453a0a35bfae3f3c84ffe8a479f8f50cffeef"
EXPECTED_RESIDUAL_SHA = "19a50655a5612e6ef00e40e0eba7c1793f5bfe298c68c082baf8b35af4856078"
EXPECTED_MANIFEST_SHA = "0a24077f352ddba91c5fea2a102f996d6bea154b1bc769235a4dd916850dba2b"
EXPECTED_ROWS_SHA = {
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
EXPECTED_TRUTH_SHA = {
    ("sugar", 2013): "e3c075e8c4b5d4020007ba31cc4c49f1161593f21b83d63b521fc668a0f26cb3",
    ("sugar", 2014): "6497a7c61d257b46a0f4f082eb05cdd2e590a6a5559cb00cb8e216a1c659c273",
    ("hdbscan", 2013): "b77cdf076ff51d81b45a38e8d6aa573f0beb43124753da7ae97e5143eb3c8f56",
    ("hdbscan", 2014): "eeeb98e249ef6be9cd9a1979316ac72da81578d9bb911752cc94b3793182c6e8",
}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hierarchy_members(tree: np.ndarray) -> dict[int, tuple[int, ...]]:
    root = int(tree["parent"].min())
    children: dict[int, list[int]] = defaultdict(list)
    nodes: set[int] = set()
    for parent, child in zip(tree["parent"], tree["child"]):
        p = int(parent)
        c = int(child)
        children[p].append(c)
        nodes.add(p)
        if c >= root:
            req(c > p, f"condensed-tree cluster order changed parent={p} child={c}")
            nodes.add(c)
    memo: dict[int, tuple[int, ...]] = {}
    for node in sorted(nodes, reverse=True):
        pts: list[int] = []
        for child in children.get(node, []):
            if child < root:
                pts.append(child)
            else:
                req(child in memo, f"missing descendant cluster {child}")
                pts.extend(memo[child])
        memo[node] = tuple(sorted(pts))
    return memo


def depths(tree: np.ndarray) -> dict[int, int]:
    root = int(tree["parent"].min())
    parent_of: dict[int, int] = {}
    nodes = {root}
    for p, c in zip(tree["parent"], tree["child"]):
        p = int(p)
        c = int(c)
        if c >= root:
            parent_of[c] = p
            nodes.add(c)
            nodes.add(p)
    out = {root: 0}
    for node in sorted(nodes):
        if node == root:
            continue
        d = 0
        cur = node
        seen = set()
        while cur != root:
            req(cur not in seen and cur in parent_of, f"broken cluster ancestry at {node}")
            seen.add(cur)
            cur = parent_of[cur]
            d += 1
        out[node] = d
    return out


def build_route(route: str, rows_root: Path, parent_pretruth: dict[str, Any]) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    for year in YEARS:
        path = rows_root / f"{route}_{year}.json"
        req(sha(path) == EXPECTED_ROWS_SHA[(route, year)], f"row input changed {route} {year}")
        rows = json.loads(path.read_text())
        req(isinstance(rows, list) and len(rows) == EXPECTED_COUNTS[(route, year)], f"row count changed {route} {year}")
        req(all(str(r.get("complex_key")) == "HIDDEN" for r in rows), f"truth leaked into rows {route} {year}")
        events.extend(normalize_event(row, year) for row in rows)

    req(len({e["id"] for e in events}) == len(events), f"duplicate IDs in {route}")
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
    req(canonical_partition(model.labels_) == canonical_partition(parent_labels), f"vanilla extraction mismatch {route}")
    recurrent, _annual = recurrent_stability(tree, years)
    labels = eom_labels(tree, recurrent)
    selected = selected_eom_nodes(tree, recurrent)
    positive = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive == list(range(len(selected))), f"selected label/node mapping changed {route}")

    members = hierarchy_members(tree)
    depth = depths(tree)
    root = int(tree["parent"].min())
    parent_families = parent_pretruth["routes"][route]["candidates"]
    req(len(parent_families) == len(selected), f"parent selected count mismatch {route}")
    by_node = {int(f["node_id"]): f for f in parent_families}
    req(set(by_node) == set(selected), f"selected node IDs changed {route}")
    for node in selected:
        got = tuple(sorted(events[i]["id"] for i in members[node]))
        exp = tuple(sorted(map(str, by_node[node]["event_ids"])))
        req(got == exp, f"selected membership mismatch {route} node={node}")

    nodes = []
    for node in sorted(members):
        if node == root:
            continue
        idx = members[node]
        if len(idx) < MIN_CLUSTER_SIZE:
            continue
        nodes.append({
            "node_id": node,
            "depth": int(depth.get(node, -1)),
            "member_count": len(idx),
            "member_indices": list(idx),
            "selected_recurrent_eom": node in by_node,
            "ordinary_stability": float(ordinary.get(float(node), 0.0)),
            "recurrent_stability": float(recurrent.get(float(node), 0.0)),
        })
    req(sum(n["selected_recurrent_eom"] for n in nodes) == len(selected), f"selected nodes missing from oracle universe {route}")
    return {
        "event_ids": [e["id"] for e in events],
        "event_years": [int(e["year"]) for e in events],
        "root_node_id": root,
        "selected_recurrent_eom_count": len(selected),
        "all_nonroot_cluster_node_count": len(nodes),
        "nodes": nodes,
    }


def run_pretruth(rows_root: Path, parent_pretruth_path: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    manifest = rows_root / "label_free_preparation_manifest.json"
    req(sha(manifest) == EXPECTED_MANIFEST_SHA, "label-free manifest changed")
    m = json.loads(manifest.read_text())
    req(m["verdict"] == "PASS_FINAL_SONOTACO_LABEL_FREE_PREPARATION", "label-free preparation not passed")
    req(m["shower_truth_accessed"] is False and m["target_information_access"] is False, "pretruth rows not clean")
    req(m["target_region_retained"] is False, "protected region retained")
    req(sha(parent_pretruth_path) == EXPECTED_PARENT_PRETRUTH_SHA, "parent pretruth changed")
    parent = json.loads(parent_pretruth_path.read_text())
    req(parent["truth_accessed"] is False and parent["blind_exclusion"] == list(BLIND), "parent pretruth boundary changed")

    routes = {route: build_route(route, rows_root, parent) for route in ROUTES}
    result = {
        "schema": "ORBITTRACE_RECURRENT_EOM_TREE_ORACLE_PRETRUTH_V1",
        "scientific_role": "PRETRUTH_EXPOSED_SONOTACO_HIERARCHY_STRUCTURE_ONLY",
        "routes": routes,
        "truth_accessed": False,
        "residual_categories_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "pristine_external_access": False,
        "blind_exclusion": list(BLIND),
    }
    path = output / "RECURRENT_EOM_TREE_ORACLE_PRETRUTH_V1.json"
    path.write_text(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
    print(json.dumps({
        "pretruth_sha256": sha(path),
        "routes": {r: {"selected": routes[r]["selected_recurrent_eom_count"], "all_nodes": routes[r]["all_nonroot_cluster_node_count"]} for r in ROUTES},
    }, indent=2, sort_keys=True))
    return 0


def node_score(indices: list[int], event_ids: list[str], truth_ids: set[str], actual: set[str]) -> tuple[float, float, float, int, int]:
    pred = {event_ids[i] for i in indices if event_ids[i] in truth_ids}
    if not pred:
        return 0.0, 0.0, 0.0, 0, 0
    ov = len(pred & actual)
    if not ov:
        return 0.0, 0.0, 0.0, len(pred), 0
    precision = ov / len(pred)
    recall = ov / len(actual)
    f1 = 2.0 * precision * recall / (precision + recall)
    return f1, precision, recall, len(pred), ov


def run_evaluate(pretruth_path: Path, residual_path: Path, truth_root: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    req(sha(residual_path) == EXPECTED_RESIDUAL_SHA, "residual diagnostic changed")
    pre = json.loads(pretruth_path.read_text())
    req(pre["schema"] == "ORBITTRACE_RECURRENT_EOM_TREE_ORACLE_PRETRUTH_V1", "wrong pretruth schema")
    req(pre["truth_accessed"] is False and pre["residual_categories_accessed"] is False, "pretruth contaminated")
    residual = json.loads(residual_path.read_text())
    req(residual["verdict"] == "DO_NOT_AUTHORIZE_RECURRENT_EOM_PHYSCORE_SUCCESSOR", "unexpected residual parent")

    panels = []
    total = Counter()
    for route, year in PANELS:
        truth_path = truth_root / f"truth_{route}_{year}.json"
        req(sha(truth_path) == EXPECTED_TRUTH_SHA[(route, year)], f"truth changed {route} {year}")
        truth = json.loads(truth_path.read_text())
        truth_ids = set(truth)
        route_pre = pre["routes"][route]
        event_ids = list(map(str, route_pre["event_ids"]))
        nodes = route_pre["nodes"]

        rp = next(p for p in residual["panels"] if p["route"] == route and int(p["year"]) == year)
        failures = [r for r in rp["records"] if r["category"] == "CANDIDATE_GENERATION_FAILURE"]
        records = []
        for r in failures:
            label = str(r["truth_label"])
            actual = {eid for eid, val in truth.items() if val == label}
            req(len(actual) == int(r["truth_member_count"]), f"truth count changed {route} {year} {label}")
            best = None
            for node in nodes:
                f1, precision, recall, pred_n, ov = node_score(node["member_indices"], event_ids, truth_ids, actual)
                key = (f1, recall, precision, -pred_n, -int(node["node_id"]))
                if best is None or key > best[0]:
                    best = (key, node, f1, precision, recall, pred_n, ov)
            req(best is not None, "empty hierarchy node universe")
            _key, node, f1, precision, recall, pred_n, ov = best
            cls = "EOM_EXTRACTION_FAILURE" if f1 > 0.5 else "HIERARCHY_ABSENT"
            if cls == "EOM_EXTRACTION_FAILURE":
                req(node["selected_recurrent_eom"] is False, "candidate-generation miss rescued by already-selected node")
            total[cls] += 1
            records.append({
                "truth_label": label,
                "truth_member_count": len(actual),
                "classification": cls,
                "best_tree_f1": f1,
                "best_tree_precision": precision,
                "best_tree_recall": recall,
                "best_tree_truth_intersection_member_count": pred_n,
                "best_tree_overlap": ov,
                "best_tree_node_id": int(node["node_id"]),
                "best_tree_node_depth": int(node["depth"]),
                "best_tree_full_member_count": int(node["member_count"]),
                "best_tree_recurrent_stability": float(node["recurrent_stability"]),
                "best_tree_ordinary_stability": float(node["ordinary_stability"]),
                "best_tree_selected_recurrent_eom": bool(node["selected_recurrent_eom"]),
                "parent_best_selected_f1": float(r["best_all_f1"]),
            })
        counts = Counter(x["classification"] for x in records)
        req(sum(counts.values()) == int(rp["category_counts"]["CANDIDATE_GENERATION_FAILURE"]), f"failure count changed {route} {year}")
        panels.append({
            "route": route,
            "year": year,
            "candidate_generation_failures": len(records),
            "tree_oracle_counts": dict(counts),
            "tree_oracle_fraction_extraction_failure": counts["EOM_EXTRACTION_FAILURE"] / len(records) if records else 0.0,
            "records": records,
        })

    req(sum(total.values()) == 58, f"pooled candidate-generation failure count changed: {sum(total.values())}")
    extraction = total["EOM_EXTRACTION_FAILURE"]
    absent = total["HIERARCHY_ABSENT"]
    result = {
        "schema": "ORBITTRACE_RECURRENT_EOM_TREE_ORACLE_DIAGNOSTIC_V1",
        "scientific_role": "EXPOSED_SONOTACO_DIAGNOSTIC_ONLY_NO_SUCCESSOR_EVALUATION",
        "candidate_generation_failures": 58,
        "eom_extraction_failures": extraction,
        "hierarchy_absent_failures": absent,
        "eom_extraction_fraction": extraction / 58.0,
        "hierarchy_absent_fraction": absent / 58.0,
        "panels": panels,
        "interpretation": (
            "Most recurrent-EOM candidate-generation misses already contain a recoverable node in the fixed condensed hierarchy; future GMN-only work should investigate extraction before changing geometry."
            if extraction > absent else
            "Most recurrent-EOM candidate-generation misses are not recoverable by any node in the fixed condensed hierarchy; changing EOM extraction alone is unlikely to solve the dominant missing-structure problem."
        ),
        "method_selected": False,
        "post_result_parameter_search": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "pristine_external_access": False,
    }
    path = output / "RECURRENT_EOM_TREE_ORACLE_DIAGNOSTIC_V1.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "result_sha256": sha(path),
        "extraction": extraction,
        "hierarchy_absent": absent,
        "fraction_extraction": extraction / 58.0,
    }, indent=2, sort_keys=True))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pretruth")
    p.add_argument("--rows-root", type=Path, required=True)
    p.add_argument("--parent-pretruth", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    e = sub.add_parser("evaluate")
    e.add_argument("--pretruth", type=Path, required=True)
    e.add_argument("--residual", type=Path, required=True)
    e.add_argument("--truth-root", type=Path, required=True)
    e.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    if a.cmd == "pretruth":
        return run_pretruth(a.rows_root, a.parent_pretruth, a.output)
    return run_evaluate(a.pretruth, a.residual, a.truth_root, a.output)


if __name__ == "__main__":
    raise SystemExit(main())
