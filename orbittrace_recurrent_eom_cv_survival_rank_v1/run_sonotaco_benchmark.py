#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability
from scipy.optimize import linear_sum_assignment

from orbittrace_recurrent_eom_hdbscan_v1.recurrent_eom import eom_labels, recurrent_stability, selected_eom_nodes

YEARS = (2013, 2014)
ROUTES = ("sugar", "hdbscan")
BLIND = (20.0, 55.0)
N_FOLDS = 10
MIN_CLUSTER_SIZE = 10
MIN_SAMPLES = 10

PARENT_PRETRUTH_SHA = "c6afbc0c3443b6c34e3f90b0f63453a0a35bfae3f3c84ffe8a479f8f50cffeef"
PARENT_COUNTS = {"sugar": 144, "hdbscan": 123}
LABEL_FREE_MANIFEST_SHA = "0a24077f352ddba91c5fea2a102f996d6bea154b1bc769235a4dd916850dba2b"
ROW_SHA = {
    ("sugar", 2013): "47fb0b700fbf710c7b061eead343016bd8d182756eb0c7f406507c5739e4c4f8",
    ("sugar", 2014): "bc83c113e9a14b1c6e1ef460ca9a40e05df77f3a449fec6064f8910add04c912",
    ("hdbscan", 2013): "2433b556d4a859580ef5431d2307ef34c8fa4c15d42841a2ec7b0c11e5f1f158",
    ("hdbscan", 2014): "206692292b2ca252777e40c13c367880740d8e2576d27615f7ea94b7790e3f55",
}
ROW_COUNT = {
    ("sugar", 2013): 18638,
    ("sugar", 2014): 15400,
    ("hdbscan", 2013): 16028,
    ("hdbscan", 2014): 13283,
}
BUDGET = {("sugar", 2013): 34, ("sugar", 2014): 46, ("hdbscan", 2013): 11, ("hdbscan", 2014): 9}
PARENT_METRICS = {
    ("sugar", 2013): (0.3752906816276458, 23),
    ("sugar", 2014): (0.43773122295664196, 24),
    ("hdbscan", 2013): (0.1914598192215768, 11),
    ("hdbscan", 2014): (0.1685878550176112, 9),
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


def bucket(event_id: str) -> int:
    digest = hashlib.sha256(str(event_id).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False) % N_FOLDS


def event_field(row: dict[str, Any], name: str) -> float:
    req(name in row and row[name] is not None, f"missing {name}")
    x = float(row[name])
    req(math.isfinite(x), f"nonfinite {name}")
    return x


def normalize_event(row: dict[str, Any], year: int) -> dict[str, Any]:
    eid = str(row["id"])
    req(int(row["year"]) == year, f"row year mismatch {eid}")
    req(eid.startswith(f"SNT{year}:"), f"SonotaCo ID/year mismatch {eid}")
    sol = event_field(row, "sol") % 360.0
    lon = event_field(row, "sun_lon")
    lat = event_field(row, "ecl_lat")
    vg = event_field(row, "vg")
    req(vg > 0.0, f"nonpositive vg {eid}")
    req(not (BLIND[0] <= sol <= BLIND[1]), f"protected event reached benchmark {eid}")
    return {"id": eid, "year": year, "sol": sol, "lon": lon, "lat": lat, "vg": vg}


def geo_matrix(events: list[dict[str, Any]]) -> np.ndarray:
    sol = np.radians(np.asarray([e["sol"] for e in events], dtype=float))
    lon = np.radians(np.asarray([e["lon"] for e in events], dtype=float))
    lat = np.radians(np.asarray([e["lat"] for e in events], dtype=float))
    vg = np.asarray([e["vg"] for e in events], dtype=float)
    return np.column_stack((
        np.cos(sol), np.sin(sol),
        np.sin(lon) * np.cos(lat), np.cos(lon) * np.cos(lat), np.sin(lat),
        vg / 72.0,
    ))


def canonical_partition(labels: np.ndarray) -> tuple[tuple[int, ...], ...]:
    groups = []
    for lab in sorted(int(x) for x in np.unique(labels) if int(x) >= 0):
        groups.append(tuple(np.flatnonzero(labels == lab).tolist()))
    return tuple(sorted(groups))


def family_id(route: str, members: tuple[str, ...]) -> str:
    return hashlib.sha256((f"SNT-REOM1|{route}|" + "|".join(members)).encode()).hexdigest()[:20]


def fold_candidates(route: str, rows_by_year: dict[int, list[dict[str, Any]]], fold: int) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for year in YEARS:
        for row in rows_by_year[year]:
            if bucket(str(row["id"])) != fold:
                events.append(normalize_event(row, year))
    req(len({e["id"] for e in events}) == len(events), f"duplicate retained IDs route={route} fold={fold}")
    years = np.asarray([e["year"] for e in events], dtype=np.int64)
    req(set(map(int, np.unique(years))) == set(YEARS), f"fold removed a full year route={route} fold={fold}")
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
    recurrent, _annual = recurrent_stability(tree, years)
    labels = eom_labels(tree, recurrent)
    nodes = selected_eom_nodes(tree, recurrent)
    positive = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(positive == list(range(len(nodes))), f"label/node map changed route={route} fold={fold}")
    candidates = []
    for lab, node in enumerate(nodes):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(events[int(i)]["id"] for i in idx))
        req(len(members) >= MIN_CLUSTER_SIZE, "subminimum fold candidate")
        candidates.append({
            "family_id": family_id(route, members),
            "event_ids": list(members),
            "member_count": len(members),
            "node_id": int(node),
            "recurrent_stability": float(recurrent[float(node)]),
            "ordinary_stability": float(ordinary[float(node)]),
        })
    return candidates


def fold_index(candidates: list[dict[str, Any]]) -> tuple[dict[str, int], list[set[str]]]:
    owner: dict[str, int] = {}
    sets: list[set[str]] = []
    for i, c in enumerate(candidates):
        ids = set(map(str, c["event_ids"]))
        for eid in ids:
            req(eid not in owner, "flat fold candidates overlap")
            owner[eid] = i
        sets.append(ids)
    return owner, sets


def best_jaccard(full_members: set[str], fold: int, owner: dict[str, int], sets: list[set[str]]) -> float:
    retained = {eid for eid in full_members if bucket(eid) != fold}
    req(retained, f"full parent family emptied by fold {fold}")
    overlaps: Counter[int] = Counter()
    for eid in retained:
        idx = owner.get(eid)
        if idx is not None:
            overlaps[idx] += 1
    if not overlaps:
        return 0.0
    best = 0.0
    for idx, ov in overlaps.items():
        union = len(retained) + len(sets[idx]) - ov
        req(union > 0, "invalid Jaccard union")
        best = max(best, ov / union)
    return float(best)


def membership_signature(candidates: list[dict[str, Any]]) -> str:
    rows = []
    for c in candidates:
        rows.append({"family_id": str(c["family_id"]), "event_ids": list(map(str, c["event_ids"])), "member_count": int(c["member_count"]), "node_id": int(c["node_id"])})
    rows.sort(key=lambda x: x["family_id"])
    return canonical_sha(rows)


def order_sha(candidates: list[dict[str, Any]]) -> str:
    return hashlib.sha256("\n".join(str(c["family_id"]) for c in candidates).encode()).hexdigest()


def rerank(parent: list[dict[str, Any]], survival: list[float]) -> list[dict[str, Any]]:
    req(len(parent) == len(survival), "survival length mismatch")
    rows = []
    for i, c in enumerate(parent):
        x = copy.deepcopy(c)
        s = float(survival[i])
        rec = float(c["recurrent_stability"])
        req(math.isfinite(s) and 0.0 <= s <= 1.0, "invalid survival")
        req(math.isfinite(rec) and rec >= 0.0, "invalid recurrent stability")
        x["parent_rank"] = int(c["rank"])
        x["cv_survival"] = s
        x["cv_survival_score"] = rec * s
        rows.append(x)
    rows.sort(key=lambda c: (-float(c["cv_survival_score"]), -float(c["recurrent_stability"]), -float(c["cv_survival"]), -int(c["member_count"]), str(c["family_id"])))
    for rank, c in enumerate(rows, 1):
        c["rank"] = rank
    return rows


def validate_parent_pretruth(path: Path) -> dict[str, Any]:
    req(sha(path) == PARENT_PRETRUTH_SHA, "immutable recurrent-EOM SonotaCo pretruth changed")
    p = json.loads(path.read_text())
    req(p.get("scientific_role") == "PRETRUTH_FROZEN_RECURRENT_EOM_SONOTACO_V31_BENCHMARK_V1", "wrong parent pretruth role")
    req(p.get("truth_accessed") is False, "parent pretruth accessed truth")
    req(p.get("blind_exclusion") == list(BLIND), "parent blind changed")
    req(p.get("target_information_access") is False and p.get("target_region_events_accessed") is False, "parent target firewall failed")
    for route in ROUTES:
        req(int(p["routes"][route]["candidate_count"]) == PARENT_COUNTS[route], f"parent count changed {route}")
        cands = p["routes"][route]["candidates"]
        req(len(cands) == PARENT_COUNTS[route], f"parent candidates missing {route}")
        req([int(c["rank"]) for c in cands] == list(range(1, len(cands) + 1)), f"parent ranks changed {route}")
    return p


def load_rows(root: Path) -> dict[str, dict[int, list[dict[str, Any]]]]:
    manifest = root / "label_free_preparation_manifest.json"
    req(sha(manifest) == LABEL_FREE_MANIFEST_SHA, "label-free manifest changed")
    m = json.loads(manifest.read_text())
    req(m.get("verdict") == "PASS_FINAL_SONOTACO_LABEL_FREE_PREPARATION", "label-free preparation did not pass")
    req(m.get("shower_truth_accessed") is False and m.get("target_region_retained") is False, "label-free boundary failed")
    out: dict[str, dict[int, list[dict[str, Any]]]] = {}
    for route in ROUTES:
        out[route] = {}
        for year in YEARS:
            path = root / f"{route}_{year}.json"
            req(sha(path) == ROW_SHA[(route, year)], f"row SHA changed {route} {year}")
            rows = json.loads(path.read_text())
            req(isinstance(rows, list) and len(rows) == ROW_COUNT[(route, year)], f"row count changed {route} {year}")
            req(all(str(x.get("complex_key")) == "HIDDEN" for x in rows), f"truth leaked into rows {route} {year}")
            out[route][year] = rows
    return out


def run_pretruth(rows_root: Path, parent_pretruth: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    parent_payload = validate_parent_pretruth(parent_pretruth)
    rows = load_rows(rows_root)
    routes = {}
    for route in ROUTES:
        parent = parent_payload["routes"][route]["candidates"]
        full_sets = [set(map(str, c["event_ids"])) for c in parent]
        j = np.zeros((len(parent), N_FOLDS), dtype=float)
        fold_meta = []
        for fold in range(N_FOLDS):
            fc = fold_candidates(route, rows[route], fold)
            owner, sets = fold_index(fc)
            for i, members in enumerate(full_sets):
                j[i, fold] = best_jaccard(members, fold, owner, sets)
            fold_meta.append({
                "fold": fold,
                "candidate_count": len(fc),
                "candidate_membership_sha256": membership_signature(fc),
                "candidate_order_independent_sha256": canonical_sha(sorted((str(c["family_id"]), sorted(map(str, c["event_ids"]))) for c in fc)),
            })
        survival = np.mean(j, axis=1).tolist()
        successor = rerank(parent, survival)
        req(membership_signature(successor) == membership_signature(parent), f"successor membership changed {route}")
        routes[route] = {
            "parent_candidate_count": len(parent),
            "successor_candidate_count": len(successor),
            "parent_membership_sha256": membership_signature(parent),
            "successor_membership_sha256": membership_signature(successor),
            "parent_order_sha256": order_sha(parent),
            "successor_order_sha256": order_sha(successor),
            "order_changed": order_sha(parent) != order_sha(successor),
            "folds": fold_meta,
            "jaccard_matrix_sha256": canonical_sha(j.tolist()),
            "survival_sha256": canonical_sha(survival),
            "candidates": successor,
        }
    req(any(routes[r]["order_changed"] for r in ROUTES), "CV survival order unchanged on both routes")
    result = {
        "schema": "ORBITTRACE_RECURRENT_EOM_CV_SURVIVAL_RANK_V1_SONOTACO_PRETRUTH",
        "scientific_role": "PRETRUTH_EXPOSED_SONOTACO_CV_SURVIVAL_RANK_ONLY",
        "sonotaco_role": "EXPOSED_DEVELOPMENT_ONLY",
        "parent_pretruth_sha256": PARENT_PRETRUTH_SHA,
        "score": "recurrent_stability * mean(max-Jaccard across ten deterministic deletion-fold recurrent-EOM catalogues)",
        "fold_rule": "uint64_be(sha256(utf8(event_id))[0:8]) mod 10",
        "routes": routes,
        "blind_exclusion": list(BLIND),
        "truth_accessed": False,
        "post_result_parameter_search": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    path = output / "RECURRENT_EOM_CV_SURVIVAL_RANK_V1_SONOTACO_PRETRUTH.json"
    out_sha = dump(path, result)
    print(json.dumps({"pretruth_sha256": out_sha, "routes": {r: {k: v for k, v in routes[r].items() if k not in {"candidates", "folds"}} for r in ROUTES}}, indent=2, sort_keys=True))
    return 0


def evaluate(families: list[dict[str, Any]], truth: dict[str, str], budget: int) -> dict[str, Any]:
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
        for jj, (_rank, _fid, pred) in enumerate(active):
            ov = len(actual & pred)
            if ov:
                precision = ov / len(pred)
                recall = ov / len(actual)
                mat[i, jj] = 2.0 * precision * recall / (precision + recall)
    n = max(len(labels), len(active))
    cost = np.zeros((n, n), dtype=np.float64)
    cost[:len(labels), :len(active)] = -mat
    ri, cj = linear_sum_assignment(cost)
    vals = [float(mat[i, j]) if j < len(active) else 0.0 for i, j in zip(ri.tolist(), cj.tolist()) if i < len(labels)]
    return {"eligible_showers": len(labels), "macro_f1": float(np.mean(vals)) if vals else 0.0, "recovered_f1_gt_0_5": int(sum(v > 0.5 for v in vals)), "candidate_used": len(active)}


def run_evaluate(pretruth_path: Path, expected_pretruth_sha: str, parent_pretruth_path: Path, truth_root: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    req(sha(pretruth_path) == expected_pretruth_sha, "successor pretruth changed after truth barrier")
    successor = json.loads(pretruth_path.read_text())
    req(successor.get("schema") == "ORBITTRACE_RECURRENT_EOM_CV_SURVIVAL_RANK_V1_SONOTACO_PRETRUTH", "wrong successor pretruth schema")
    req(successor.get("truth_accessed") is False, "successor pretruth accessed truth")
    parent = validate_parent_pretruth(parent_pretruth_path)
    panels = []
    all_nonregress = True
    any_strict = False
    for route in ROUTES:
        for year in YEARS:
            truth_path = truth_root / f"truth_{route}_{year}.json"
            eval_path = truth_root / f"evaluation_{route}_{year}.json"
            req(truth_path.exists() and eval_path.exists(), f"missing immutable truth panel {route} {year}")
            truth = json.loads(truth_path.read_text())
            frozen_eval = json.loads(eval_path.read_text())
            budget = int(frozen_eval["candidate_budget"]["comparator_budget"])
            req(budget == BUDGET[(route, year)], f"budget changed {route} {year}")
            pe = evaluate(parent["routes"][route]["candidates"], truth, budget)
            se = evaluate(successor["routes"][route]["candidates"], truth, budget)
            exp_f1, exp_rec = PARENT_METRICS[(route, year)]
            req(abs(float(pe["macro_f1"]) - exp_f1) <= 1e-15, f"parent F1 did not reproduce {route} {year}")
            req(int(pe["recovered_f1_gt_0_5"]) == exp_rec, f"parent recovery did not reproduce {route} {year}")
            f1_ok = float(se["macro_f1"]) >= float(pe["macro_f1"])
            rec_ok = int(se["recovered_f1_gt_0_5"]) >= int(pe["recovered_f1_gt_0_5"])
            strict = float(se["macro_f1"]) > float(pe["macro_f1"]) or int(se["recovered_f1_gt_0_5"]) > int(pe["recovered_f1_gt_0_5"])
            all_nonregress = all_nonregress and f1_ok and rec_ok
            any_strict = any_strict or strict
            panels.append({
                "route": route, "year": year, "budget": budget,
                "parent_macro_f1": float(pe["macro_f1"]), "successor_macro_f1": float(se["macro_f1"]), "macro_f1_delta": float(se["macro_f1"]) - float(pe["macro_f1"]),
                "parent_recovered": int(pe["recovered_f1_gt_0_5"]), "successor_recovered": int(se["recovered_f1_gt_0_5"]), "recovered_delta": int(se["recovered_f1_gt_0_5"]) - int(pe["recovered_f1_gt_0_5"]),
                "macro_f1_nonregression": f1_ok, "recovery_nonregression": rec_ok, "strict_improvement": strict,
            })
    membership_ok = all(successor["routes"][r]["parent_membership_sha256"] == successor["routes"][r]["successor_membership_sha256"] for r in ROUTES)
    mechanism_active = any(bool(successor["routes"][r]["order_changed"]) for r in ROUTES)
    passed = membership_ok and mechanism_active and all_nonregress and any_strict
    verdict = "PASS_RECURRENT_EOM_CV_SURVIVAL_RANK_V1_SONOTACO_DEVELOPMENT" if passed else "FAIL_RECURRENT_EOM_CV_SURVIVAL_RANK_V1_SONOTACO_DEVELOPMENT"
    result = {
        "schema": "ORBITTRACE_RECURRENT_EOM_CV_SURVIVAL_RANK_V1_SONOTACO_RESULT",
        "scientific_role": "EXPOSED_SONOTACO_2013_2014_ONE_SHOT_RANKING_PORTABILITY_ONLY",
        "sonotaco_role": "EXPOSED_DEVELOPMENT_ONLY",
        "verdict": verdict,
        "pretruth_sha256": expected_pretruth_sha,
        "parent_pretruth_sha256": PARENT_PRETRUTH_SHA,
        "panels": panels,
        "membership_universe_identical": membership_ok,
        "mechanism_active": mechanism_active,
        "all_panel_macro_f1_and_recovery_nonregression": all_nonregress,
        "any_strict_improvement": any_strict,
        "post_result_parameter_search": False,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    path = output / "RECURRENT_EOM_CV_SURVIVAL_RANK_V1_SONOTACO_RESULT.json"
    result_sha = dump(path, result)
    print(json.dumps({"verdict": verdict, "result_sha256": result_sha, "panels": panels}, indent=2, sort_keys=True))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    pre = sub.add_parser("pretruth")
    pre.add_argument("--rows-root", type=Path, required=True)
    pre.add_argument("--parent-pretruth", type=Path, required=True)
    pre.add_argument("--output", type=Path, required=True)
    ev = sub.add_parser("evaluate")
    ev.add_argument("--pretruth", type=Path, required=True)
    ev.add_argument("--expected-pretruth-sha", required=True)
    ev.add_argument("--parent-pretruth", type=Path, required=True)
    ev.add_argument("--truth-root", type=Path, required=True)
    ev.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.cmd == "pretruth":
        return run_pretruth(a.rows_root, a.parent_pretruth, a.output)
    return run_evaluate(a.pretruth, a.expected_pretruth_sha, a.parent_pretruth, a.truth_root, a.output)


if __name__ == "__main__":
    raise SystemExit(main())
