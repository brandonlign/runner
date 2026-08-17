#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability

from orbittrace_recurrent_eom_hdbscan_v1.recurrent_eom import eom_labels, recurrent_stability, selected_eom_nodes

YEARS = (2013, 2014)
ROUTES = ("sugar", "hdbscan")
BLIND = (20.0, 55.0)
MIN_CLUSTER_SIZE = 10
MIN_SAMPLES = 10
PARENT_PRETRUTH_SHA = "c6afbc0c3443b6c34e3f90b0f63453a0a35bfae3f3c84ffe8a479f8f50cffeef"
RESIDUAL_RESULT_SHA = "19a50655a5612e6ef00e40e0eba7c1793f5bfe298c68c082baf8b35af4856078"
LABEL_FREE_MANIFEST_SHA = "0a24077f352ddba91c5fea2a102f996d6bea154b1bc769235a4dd916850dba2b"
ROW_SHA = {
    ("sugar", 2013): "47fb0b700fbf710c7b061eead343016bd8d182756eb0c7f406507c5739e4c4f8",
    ("sugar", 2014): "bc83c113e9a14b1c6e1ef460ca9a40e05df77f3a449fec6064f8910add04c912",
    ("hdbscan", 2013): "2433b556d4a859580ef5431d2307ef34c8fa4c15d42841a2ec7b0c11e5f1f158",
    ("hdbscan", 2014): "206692292b2ca252777e40c13c367880740d8e2576d27615f7ea94b7790e3f55",
}
ROW_COUNT = {
    ("sugar", 2013): 18638, ("sugar", 2014): 15400,
    ("hdbscan", 2013): 16028, ("hdbscan", 2014): 13283,
}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def dump(path: Path, obj: Any) -> str:
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def field(row: dict[str, Any], name: str) -> float:
    req(name in row and row[name] is not None, f"missing {name}")
    x = float(row[name])
    req(math.isfinite(x), f"nonfinite {name}")
    return x


def normalize(row: dict[str, Any], year: int) -> dict[str, Any]:
    eid = str(row["id"])
    req(int(row["year"]) == year and eid.startswith(f"SNT{year}:"), f"ID/year mismatch {eid}")
    sol = field(row, "sol") % 360.0
    req(not (BLIND[0] <= sol <= BLIND[1]), f"protected event reached hierarchy {eid}")
    vg = field(row, "vg")
    req(vg > 0.0, f"nonpositive vg {eid}")
    return {"id": eid, "year": year, "sol": sol, "lon": field(row, "sun_lon"), "lat": field(row, "ecl_lat"), "vg": vg}


def geo(events: list[dict[str, Any]]) -> np.ndarray:
    sol = np.radians(np.asarray([e["sol"] for e in events], dtype=float))
    lon = np.radians(np.asarray([e["lon"] for e in events], dtype=float))
    lat = np.radians(np.asarray([e["lat"] for e in events], dtype=float))
    vg = np.asarray([e["vg"] for e in events], dtype=float)
    return np.column_stack((np.cos(sol), np.sin(sol), np.sin(lon)*np.cos(lat), np.cos(lon)*np.cos(lat), np.sin(lat), vg/72.0))


def family_id(route: str, members: tuple[str, ...]) -> str:
    return hashlib.sha256((f"SNT-REOM1|{route}|" + "|".join(members)).encode()).hexdigest()[:20]


def membership_signature(candidates: list[dict[str, Any]]) -> str:
    rows = []
    for c in candidates:
        rows.append({"family_id": str(c["family_id"]), "node_id": int(c["node_id"]), "member_count": int(c["member_count"]), "event_ids": list(map(str, c["event_ids"]))})
    rows.sort(key=lambda x: x["family_id"])
    return canonical_sha(rows)


def load_rows(root: Path) -> dict[str, dict[int, list[dict[str, Any]]]]:
    manifest = root / "label_free_preparation_manifest.json"
    req(sha(manifest) == LABEL_FREE_MANIFEST_SHA, "label-free manifest changed")
    m = json.loads(manifest.read_text())
    req(m.get("verdict") == "PASS_FINAL_SONOTACO_LABEL_FREE_PREPARATION", "label-free prep did not pass")
    req(m.get("shower_truth_accessed") is False and m.get("target_region_retained") is False, "label-free boundary failed")
    out: dict[str, dict[int, list[dict[str, Any]]]] = {}
    for route in ROUTES:
        out[route] = {}
        for year in YEARS:
            path = root / f"{route}_{year}.json"
            req(sha(path) == ROW_SHA[(route, year)], f"row SHA changed {route} {year}")
            rows = json.loads(path.read_text())
            req(isinstance(rows, list) and len(rows) == ROW_COUNT[(route, year)], f"row count changed {route} {year}")
            req(all(str(r.get("complex_key")) == "HIDDEN" for r in rows), f"truth leaked in label-free rows {route} {year}")
            out[route][year] = rows
    return out


def descendant_memberships(tree: np.ndarray, event_ids: list[str]) -> dict[int, tuple[str, ...]]:
    root = int(tree["parent"].min())
    req(root == len(event_ids), "condensed-tree point/root identity changed")
    children: dict[int, list[int]] = defaultdict(list)
    cluster_nodes: set[int] = set()
    for parent, child in zip(tree["parent"], tree["child"]):
        p, c = int(parent), int(child)
        children[p].append(c)
        cluster_nodes.add(p)
        if c >= root:
            req(c > p, f"condensed-tree cluster topology changed parent={p} child={c}")
            cluster_nodes.add(c)
    memo: dict[int, tuple[int, ...]] = {}
    for node in sorted(cluster_nodes, reverse=True):
        points: list[int] = []
        for child in children.get(node, []):
            if child < root:
                points.append(child)
            else:
                req(child in memo, f"missing child membership {child}")
                points.extend(memo[child])
        unique = tuple(sorted(set(points)))
        memo[node] = unique
    out = {}
    for node, idx in memo.items():
        if len(idx) >= MIN_CLUSTER_SIZE:
            out[node] = tuple(sorted(event_ids[i] for i in idx))
    return out


def build_route(route: str, rows_by_year: dict[int, list[dict[str, Any]]], parent_route: dict[str, Any]) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    for year in YEARS:
        events.extend(normalize(r, year) for r in rows_by_year[year])
    req(len({e["id"] for e in events}) == len(events), f"duplicate IDs {route}")
    X = geo(events)
    years = np.asarray([e["year"] for e in events], dtype=np.int64)
    model = hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE, min_samples=MIN_SAMPLES, metric="euclidean",
        cluster_selection_method="eom", cluster_selection_epsilon=0.0,
        allow_single_cluster=False, prediction_data=False,
    ).fit(X)
    tree = model.condensed_tree_._raw_tree
    ordinary = compute_stability(tree)
    recurrent, annual = recurrent_stability(tree, years)
    labels = eom_labels(tree, recurrent)
    selected_nodes = selected_eom_nodes(tree, recurrent)
    positive = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive == list(range(len(selected_nodes))), f"selected label/node map changed {route}")
    selected = []
    for lab, node in enumerate(selected_nodes):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(events[int(i)]["id"] for i in idx))
        selected.append({
            "family_id": family_id(route, members), "node_id": int(node), "event_ids": list(members),
            "member_count": len(members), "recurrent_stability": float(recurrent[float(node)]),
            "ordinary_stability": float(ordinary[float(node)]),
        })
    selected.sort(key=lambda c: (-c["recurrent_stability"], -c["ordinary_stability"], -c["member_count"], c["family_id"]))
    for rank, c in enumerate(selected, 1): c["rank"] = rank
    parent_candidates = parent_route["candidates"]
    req(len(selected) == int(parent_route["candidate_count"]), f"selected count did not reproduce {route}")
    req([c["family_id"] for c in selected] == [c["family_id"] for c in parent_candidates], f"selected order did not reproduce {route}")
    req(membership_signature(selected) == membership_signature(parent_candidates), f"selected membership did not reproduce {route}")

    all_members = descendant_memberships(tree, [e["id"] for e in events])
    selected_set = set(map(int, selected_nodes))
    latent = []
    for node in sorted(all_members):
        members = all_members[node]
        latent.append({
            "node_id": int(node), "event_ids": list(members), "member_count": len(members),
            "ordinary_stability": float(ordinary.get(float(node), 0.0)),
            "recurrent_stability": float(recurrent.get(float(node), 0.0)),
            "selected_by_recurrent_eom": bool(node in selected_set),
        })
    return {
        "events": len(events),
        "selected_candidate_count": len(selected),
        "selected_membership_sha256": membership_signature(selected),
        "latent_node_count": len(latent),
        "latent_catalogue_sha256": canonical_sha(latent),
        "annual_recurrent_stability_sha256": canonical_sha({str(k): list(v) for k,v in sorted(annual.items())}),
        "latent_nodes": latent,
    }


def run_pretruth(rows_root: Path, parent_pretruth_path: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    req(sha(parent_pretruth_path) == PARENT_PRETRUTH_SHA, "parent pretruth changed")
    parent = json.loads(parent_pretruth_path.read_text())
    req(parent.get("truth_accessed") is False and parent.get("blind_exclusion") == list(BLIND), "parent pretruth boundary changed")
    rows = load_rows(rows_root)
    routes = {r: build_route(r, rows[r], parent["routes"][r]) for r in ROUTES}
    result = {
        "schema": "ORBITTRACE_RECURRENT_EOM_LATENT_HIERARCHY_DIAGNOSTIC_V1_PRETRUTH",
        "scientific_role": "PRETRUTH_EXPOSED_SONOTACO_HIERARCHY_MECHANISM_DIAGNOSTIC_ONLY",
        "parent_pretruth_sha256": PARENT_PRETRUTH_SHA,
        "routes": routes,
        "blind_exclusion": list(BLIND),
        "truth_accessed": False,
        "residual_classification_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    path = output / "RECURRENT_EOM_LATENT_HIERARCHY_DIAGNOSTIC_V1_PRETRUTH.json"
    out_sha = dump(path, result)
    print(json.dumps({"pretruth_sha256": out_sha, "routes": {r:{k:v for k,v in routes[r].items() if k != "latent_nodes"} for r in ROUTES}}, indent=2, sort_keys=True))
    return 0


def f1(pred: set[str], actual: set[str]) -> float:
    ov = len(pred & actual)
    if ov == 0 or not pred or not actual: return 0.0
    precision = ov / len(pred)
    recall = ov / len(actual)
    return 2.0 * precision * recall / (precision + recall)


def run_evaluate(pretruth_path: Path, expected_pretruth_sha: str, residual_path: Path, truth_root: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    req(sha(pretruth_path) == expected_pretruth_sha, "latent pretruth changed after freeze")
    req(sha(residual_path) == RESIDUAL_RESULT_SHA, "residual analysis result changed")
    pre = json.loads(pretruth_path.read_text())
    residual = json.loads(residual_path.read_text())
    req(pre.get("truth_accessed") is False and pre.get("residual_classification_accessed") is False, "pretruth already exposed")
    records = []
    total_candidate_gen = 0
    latent_count = 0
    hierarchy_count = 0
    panel_summaries = []
    for panel in residual["panels"]:
        route = str(panel["route"]); year = int(panel["year"])
        truth = json.loads((truth_root / f"truth_{route}_{year}.json").read_text())
        truth_ids = set(truth)
        node_rows = pre["routes"][route]["latent_nodes"]
        eligible_records = [r for r in panel["records"] if r["category"] == "CANDIDATE_GENERATION_FAILURE"]
        panel_latent = 0
        panel_hierarchy = 0
        for rec in eligible_records:
            label = str(rec["truth_label"])
            actual = {eid for eid, lab in truth.items() if lab == label}
            req(len(actual) == int(rec["truth_member_count"]), f"truth member count changed {route} {year} {label}")
            best_f1 = -1.0; best_node = None; best_n = None
            for node in node_rows:
                pred = set(map(str, node["event_ids"])) & truth_ids
                value = f1(pred, actual)
                if value > best_f1 or (value == best_f1 and (best_n is None or int(node["member_count"]) < best_n)):
                    best_f1 = value; best_node = int(node["node_id"]); best_n = int(node["member_count"])
            category = "LATENT_TREE_EXTRACTION_FAILURE" if best_f1 > 0.5 else "HIERARCHY_REPRESENTATION_FAILURE"
            if category == "LATENT_TREE_EXTRACTION_FAILURE": panel_latent += 1; latent_count += 1
            else: panel_hierarchy += 1; hierarchy_count += 1
            total_candidate_gen += 1
            records.append({
                "route": route, "year": year, "truth_label": label,
                "original_category": rec["category"], "selected_best_all_f1": float(rec["best_all_f1"]),
                "best_latent_node_f1": float(best_f1), "best_latent_node_id": best_node,
                "best_latent_node_member_count": best_n, "refined_category": category,
            })
        panel_summaries.append({"route": route, "year": year, "candidate_generation_failures": len(eligible_records), "latent_tree_extraction_failures": panel_latent, "hierarchy_representation_failures": panel_hierarchy})
    req(total_candidate_gen == 58, f"candidate-generation residual count changed: {total_candidate_gen}")
    fraction = latent_count / total_candidate_gen
    guidance = "TARGET_EXISTING_HIERARCHY_EXTRACTION_PRUNING" if fraction >= 0.5 else "TARGET_NEW_HIERARCHY_CANDIDATE_CONSTRUCTION"
    result = {
        "schema": "ORBITTRACE_RECURRENT_EOM_LATENT_HIERARCHY_DIAGNOSTIC_V1_RESULT",
        "scientific_role": "EXPOSED_SONOTACO_MECHANISM_DIAGNOSTIC_ONLY",
        "pretruth_sha256": expected_pretruth_sha,
        "residual_result_sha256": RESIDUAL_RESULT_SHA,
        "candidate_generation_failures": total_candidate_gen,
        "latent_tree_extraction_failures": latent_count,
        "hierarchy_representation_failures": hierarchy_count,
        "latent_tree_fraction": fraction,
        "predeclared_guidance": guidance,
        "panel_summaries": panel_summaries,
        "records": records,
        "threshold": "best latent-node F1 > 0.5",
        "guidance_cutoff": "latent_tree_fraction >= 0.5",
        "post_result_parameter_search": False,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    path = output / "RECURRENT_EOM_LATENT_HIERARCHY_DIAGNOSTIC_V1_RESULT.json"
    result_sha = dump(path, result)
    print(json.dumps({"result_sha256": result_sha, "candidate_generation_failures": total_candidate_gen, "latent_tree_extraction_failures": latent_count, "hierarchy_representation_failures": hierarchy_count, "latent_tree_fraction": fraction, "predeclared_guidance": guidance, "panel_summaries": panel_summaries}, indent=2, sort_keys=True))
    return 0


def main() -> int:
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd", required=True)
    pre=sub.add_parser("pretruth"); pre.add_argument("--rows-root",type=Path,required=True); pre.add_argument("--parent-pretruth",type=Path,required=True); pre.add_argument("--output",type=Path,required=True)
    ev=sub.add_parser("evaluate"); ev.add_argument("--pretruth",type=Path,required=True); ev.add_argument("--expected-pretruth-sha",required=True); ev.add_argument("--residual-result",type=Path,required=True); ev.add_argument("--truth-root",type=Path,required=True); ev.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    return run_pretruth(a.rows_root,a.parent_pretruth,a.output) if a.cmd=="pretruth" else run_evaluate(a.pretruth,a.expected_pretruth_sha,a.residual_result,a.truth_root,a.output)

if __name__ == "__main__": raise SystemExit(main())
