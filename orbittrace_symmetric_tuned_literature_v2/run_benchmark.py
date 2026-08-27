#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability, get_clusters
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors

YEARS = (2013, 2014)
BUDGETS = (10, 20, 30, 40)
SUPPORT_GRID = ((5,5),(10,5),(10,10),(20,10),(20,20),(40,20),(40,40),(80,40),(80,80))
SUGAR_PERCENTILES = (10.0, 15.0, 20.0, 23.0, 25.0, 30.0, 35.0)
SUGAR_TUNE_CLONES = 100
SUGAR_FINAL_CLONES = 1000
SUGAR_MIN_SAMPLES = 5


def req(x: bool, msg: str) -> None:
    if not x:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def row_id(row: dict[str, Any]) -> str:
    for key in ("id", "event_id", "eventId"):
        if key in row:
            return str(row[key])
    raise RuntimeError(f"row lacks id: {sorted(row)[:20]}")


def load_rows(root: Path, route: str, year: int) -> list[dict[str, Any]]:
    p = root / f"{route}_{year}.json"
    req(p.exists(), f"missing rows {p}")
    rows = json.loads(p.read_text())
    req(isinstance(rows, list) and rows, f"invalid rows {p}")
    return rows


def merge_common_rows(root: Path) -> tuple[list[dict[str, Any]], dict[int, set[str]], dict[str, Any]]:
    pooled: list[dict[str, Any]] = []
    ids_by_year: dict[int, set[str]] = {}
    diag: dict[str, Any] = {"route_counts": {}, "common_counts": {}}
    for year in YEARS:
        sugar = {row_id(r): r for r in load_rows(root, "sugar", year)}
        hdb = {row_id(r): r for r in load_rows(root, "hdbscan", year)}
        common = sorted(set(sugar) & set(hdb))
        req(common, f"empty common universe {year}")
        ids_by_year[year] = set(common)
        diag["route_counts"][str(year)] = {"sugar": len(sugar), "hdbscan": len(hdb)}
        diag["common_counts"][str(year)] = len(common)
        for eid in common:
            merged = dict(sugar[eid])
            for k, v in hdb[eid].items():
                if k not in merged or merged[k] is None:
                    merged[k] = v
            merged["id"] = eid
            merged["year"] = year
            pooled.append(merged)
    req(len({row_id(r) for r in pooled}) == len(pooled), "duplicate pooled ids")
    return pooled, ids_by_year, diag


def find_truth(root: Path, route: str, year: int) -> dict[str, str]:
    xs = list(root.rglob(f"truth_{route}_{year}.json"))
    req(len(xs) == 1, f"truth file missing/ambiguous for {route} {year}: {xs}")
    obj = json.loads(xs[0].read_text())
    req(isinstance(obj, dict), f"truth must be dict: {xs[0]}")
    return {str(k): str(v) for k, v in obj.items()}


def common_truth(root: Path, ids_by_year: dict[int, set[str]]) -> dict[int, dict[str, str]]:
    out = {}
    for year in YEARS:
        a = find_truth(root, "sugar", year)
        b = find_truth(root, "hdbscan", year)
        ids = ids_by_year[year]
        missing = [eid for eid in ids if eid not in a or eid not in b]
        req(not missing, f"truth missing common ids {year}: {missing[:5]}")
        disagree = [eid for eid in ids if a[eid] != b[eid]]
        req(not disagree, f"truth route disagreement {year}: {disagree[:5]}")
        out[year] = {eid: a[eid] for eid in ids}
    return out


def member_hash(prefix: str, ids: Iterable[str]) -> str:
    members = tuple(sorted(map(str, ids)))
    return hashlib.sha256((prefix + "|" + "|".join(members)).encode()).hexdigest()[:20]


def families_from_labels(labels: np.ndarray, rows: list[dict[str, Any]], prefix: str,
                         primary: np.ndarray | None = None, secondary: np.ndarray | None = None) -> list[dict[str, Any]]:
    labels = np.asarray(labels, dtype=int)
    out = []
    for lab in sorted(int(x) for x in np.unique(labels) if int(x) >= 0):
        idx = np.flatnonzero(labels == lab)
        ids = [row_id(rows[int(i)]) for i in idx]
        p1 = float(np.mean(primary[idx])) if primary is not None and len(idx) else 0.0
        p2 = float(np.mean(secondary[idx])) if secondary is not None and len(idx) else 0.0
        out.append({
            "family_id": member_hash(prefix, ids),
            "member_ids": sorted(ids),
            "member_count": len(ids),
            "primary_score": p1,
            "secondary_score": p2,
        })
    out.sort(key=lambda f: (-f["primary_score"], -f["secondary_score"], -f["member_count"], f["family_id"]))
    for i, f in enumerate(out, 1):
        f["rank"] = i
    return out


def score(families: list[dict[str, Any]], truth: dict[str, str], budget: int | None) -> dict[str, Any]:
    counts = Counter(v for v in truth.values() if v != "SPORADIC")
    labels = sorted(k for k, n in counts.items() if n >= 4)
    ids = set(truth)
    active = []
    for i, f in enumerate(families):
        mem = set(map(str, f["member_ids"])) & ids
        if mem:
            active.append((int(f.get("rank", i + 1)), str(f["family_id"]), mem))
    active.sort(key=lambda z: (z[0], z[1]))
    if budget is not None:
        active = active[:budget]
    truth_sets = {lab: {eid for eid, v in truth.items() if v == lab} for lab in labels}
    mat = np.zeros((len(labels), len(active)), dtype=float)
    for i, lab in enumerate(labels):
        a = truth_sets[lab]
        for j, (_, _, p) in enumerate(active):
            ov = len(a & p)
            if ov:
                pr = ov / len(p)
                re = ov / len(a)
                mat[i, j] = 2 * pr * re / (pr + re)
    n = max(len(labels), len(active))
    if n == 0:
        return {"eligible_showers": 0, "macro_f1": 0.0, "recovered_f1_gt_0_5": 0, "candidate_used": 0}
    cost = np.zeros((n, n), dtype=float)
    cost[:len(labels), :len(active)] = -mat
    ri, cj = linear_sum_assignment(cost)
    vals = [float(mat[i, j]) if j < len(active) else 0.0 for i, j in zip(ri.tolist(), cj.tolist()) if i < len(labels)]
    return {
        "eligible_showers": len(labels),
        "macro_f1": float(np.mean(vals)) if vals else 0.0,
        "recovered_f1_gt_0_5": int(sum(v > 0.5 for v in vals)),
        "candidate_used": len(active),
    }


def curve(families: list[dict[str, Any]], truth: dict[str, str]) -> dict[str, Any]:
    panels = {str(k): score(families, truth, k) for k in BUDGETS}
    return {
        "budgets": panels,
        "auc_macro_f1": float(np.mean([panels[str(k)]["macro_f1"] for k in BUDGETS])),
        "recovered_sum": int(sum(panels[str(k)]["recovered_f1_gt_0_5"] for k in BUDGETS)),
        "native": score(families, truth, None),
        "candidate_count": len(families),
    }


def tuning_key(c: dict[str, Any]) -> tuple[float, int, float, int]:
    return (
        float(c["curve"]["auc_macro_f1"]),
        int(c["curve"]["recovered_sum"]),
        float(c["curve"]["budgets"]["40"]["macro_f1"]),
        -int(c["grid_index"]),
    )


def recurrent_outputs(rows: list[dict[str, Any]], X_geo: np.ndarray, kernel: Any) -> dict[str, list[dict[str, Any]]]:
    years = np.asarray([int(r["year"]) for r in rows], dtype=np.int64)
    outputs = {}
    for mcs, ms in SUPPORT_GRID:
        model = hdbscan.HDBSCAN(
            min_cluster_size=mcs, min_samples=ms, metric="euclidean",
            cluster_selection_method="eom", cluster_selection_epsilon=0.0,
            allow_single_cluster=False, prediction_data=False,
        ).fit(X_geo)
        tree = model.condensed_tree_._raw_tree
        recurrent, _annual = kernel.recurrent_stability(tree, years)
        labels, probs, _stabilities = get_clusters(
            tree, dict(recurrent), cluster_selection_method="eom",
            allow_single_cluster=False, match_reference_implementation=False,
            cluster_selection_epsilon=0.0, max_cluster_size=0,
        )
        labels = np.asarray(labels, dtype=int)
        probs = np.asarray(probs, dtype=float)
        nodes = kernel.selected_eom_nodes(tree, recurrent)
        pos = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
        req(pos == list(range(len(nodes))), f"recurrent compact-label mapping changed for {mcs}/{ms}")
        node_score = np.zeros(len(labels), dtype=float)
        for lab, node in enumerate(nodes):
            node_score[labels == lab] = float(recurrent[float(node)])
        outputs[f"mcs={mcs},ms={ms}"] = families_from_labels(labels, rows, "REOM2", node_score, probs)
    return outputs


def install_hdb_compat() -> None:
    import hdbscan.hdbscan_ as hi
    from sklearn.utils import check_array as sk_check_array
    def compat(*args, **kwargs):
        if "ensure_all_finite" in kwargs:
            kwargs["force_all_finite"] = kwargs.pop("ensure_all_finite")
        return sk_check_array(*args, **kwargs)
    hi.check_array = compat


def hdb_outputs(rows: list[dict[str, Any]], source: Any) -> dict[str, list[dict[str, Any]]]:
    install_hdb_compat()
    X = np.asarray(source.feature_matrix(list(rows)), dtype=float)
    req(X.ndim == 2 and len(X) == len(rows) and np.all(np.isfinite(X)), "invalid HDB feature matrix")
    outputs = {}
    for mcs, ms in SUPPORT_GRID:
        for selection in ("eom", "leaf"):
            model = hdbscan.HDBSCAN(
                min_cluster_size=mcs, min_samples=ms, metric="euclidean",
                cluster_selection_method=selection, cluster_selection_epsilon=0.0,
                allow_single_cluster=False, prediction_data=False,
            ).fit(X)
            labels = np.asarray(model.labels_, dtype=int)
            probs = np.asarray(model.probabilities_, dtype=float)
            persistence = np.asarray(model.cluster_persistence_, dtype=float)
            event_persistence = np.zeros(len(labels), dtype=float)
            for lab in range(len(persistence)):
                event_persistence[labels == lab] = float(persistence[lab])
            outputs[f"mcs={mcs},ms={ms},selection={selection}"] = families_from_labels(
                labels, rows, "HDB2", event_persistence, probs
            )
    return outputs


def sugar_arrays(rows: list[dict[str, Any]]) -> tuple[np.ndarray, ...]:
    def arr(name: str) -> np.ndarray:
        return np.asarray([float(r[name]) for r in rows], dtype=float)
    return arr("sol"), arr("ra"), arr("dec"), arr("vg"), arr("ra_sd"), arr("dec_sd"), arr("vg_sd")


def sugar_candidate_output(rows: list[dict[str, Any]], source: Any, percentile: float,
                           clones: int, seed_tag: str) -> list[dict[str, Any]]:
    sol, ra, dec, vg, ra_sd, dec_sd, vg_sd = sugar_arrays(rows)
    observed = np.asarray(source.feature_matrix_from_equatorial(sol, ra, dec, vg), dtype=float)
    req(observed.shape[0] == len(rows), "Sugar feature row mismatch")
    nn = NearestNeighbors(n_neighbors=SUGAR_MIN_SAMPLES, algorithm="auto", n_jobs=-1)
    d = nn.fit(observed).kneighbors(observed, return_distance=True)[0][:, SUGAR_MIN_SAMPLES - 1]
    eps = float(np.percentile(d, percentile))
    req(math.isfinite(eps) and eps > 0.0, "invalid Sugar epsilon")
    merger = source.OverlapGraphMerger(len(rows))
    for it in range(clones):
        seed = source.stable_seed(20170209, "orbittrace-symmetric-fair-v2", 20132014, seed_tag, it)
        feats = source.clone_feature_matrix(sol, ra, dec, vg, ra_sd, dec_sd, vg_sd, seed=seed)
        labels = DBSCAN(eps=eps, min_samples=SUGAR_MIN_SAMPLES, metric="euclidean", n_jobs=-1).fit_predict(feats)
        clusters = [np.flatnonzero(labels == lab).tolist() for lab in sorted(int(x) for x in np.unique(labels) if int(x) >= 0)]
        merger.add_iteration(it, clusters)
    masters = merger.finalize()
    min_rec = max(1, int(round(clones * 0.10)))
    labels, probs = source.hard_assignment(len(rows), masters, minimum_recurrence=min_rec)
    labels = np.asarray(labels, dtype=int)
    probs = np.asarray(probs, dtype=float)
    return families_from_labels(labels, rows, "SUGAR2", probs, np.ones(len(rows), dtype=float))


def select(outputs: dict[str, list[dict[str, Any]]], truth: dict[str, str]) -> dict[str, Any]:
    rows = []
    for i, (cfg, fam) in enumerate(outputs.items()):
        rows.append({"config": cfg, "grid_index": i, "curve": curve(fam, truth)})
    best = max(rows, key=tuning_key)
    return {"selected": best, "all": rows}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows-root", type=Path, required=True)
    ap.add_argument("--sources", type=Path, required=True)
    ap.add_argument("--truth-root", type=Path, required=True)
    ap.add_argument("--recurrent-kernel", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    sugar_source = args.sources / "sugar_uncertainty_core.py"
    hdb_source = args.sources / "hdbscan_2025_runner.py"
    req(sugar_source.exists() and hdb_source.exists(), "frozen comparator sources missing")
    sugar = load_module(sugar_source, "fairv2_sugar")
    hdb_src = load_module(hdb_source, "fairv2_hdb")
    kernel = load_module(args.recurrent_kernel, "fairv2_recurrent")

    rows, ids_by_year, universe = merge_common_rows(args.rows_root)
    truth = common_truth(args.truth_root, ids_by_year)

    sol, ra, dec, vg, *_ = sugar_arrays(rows)
    X_geo = np.asarray(sugar.feature_matrix_from_equatorial(sol, ra, dec, vg), dtype=float)
    req(X_geo.shape == (len(rows), 6), f"unexpected recurrent GEO shape {X_geo.shape}")

    recurrent = recurrent_outputs(rows, X_geo, kernel)
    hdb = hdb_outputs(rows, hdb_src)
    sugar_tune = {}
    for p in SUGAR_PERCENTILES:
        cfg = f"percentile={p:g},min_samples={SUGAR_MIN_SAMPLES},clones={SUGAR_TUNE_CLONES}"
        sugar_tune[cfg] = sugar_candidate_output(rows, sugar, p, SUGAR_TUNE_CLONES, f"tune-p{p:g}")

    folds = []
    final_sugar_cache: dict[float, list[dict[str, Any]]] = {}
    for dev_year, test_year in ((2013, 2014), (2014, 2013)):
        selections = {
            "recurrent_eom": select(recurrent, truth[dev_year]),
            "hdbscan": select(hdb, truth[dev_year]),
            "sugar": select(sugar_tune, truth[dev_year]),
        }
        chosen_rec = recurrent[selections["recurrent_eom"]["selected"]["config"]]
        chosen_hdb = hdb[selections["hdbscan"]["selected"]["config"]]
        sugar_cfg = selections["sugar"]["selected"]["config"]
        percentile = float(sugar_cfg.split(",",1)[0].split("=",1)[1])
        if percentile not in final_sugar_cache:
            final_sugar_cache[percentile] = sugar_candidate_output(
                rows, sugar, percentile, SUGAR_FINAL_CLONES, f"final-p{percentile:g}"
            )
        chosen_sugar = final_sugar_cache[percentile]
        folds.append({
            "dev_year": dev_year,
            "test_year": test_year,
            "selected_configs": {m: selections[m]["selected"] for m in selections},
            "test": {
                "recurrent_eom": curve(chosen_rec, truth[test_year]),
                "hdbscan": curve(chosen_hdb, truth[test_year]),
                "sugar": curve(chosen_sugar, truth[test_year]),
            },
            "sugar_final_clones": SUGAR_FINAL_CLONES,
        })

    methods = ("recurrent_eom", "hdbscan", "sugar")
    aggregate = {}
    for method in methods:
        aggregate[method] = {
            "mean_test_auc_macro_f1": float(np.mean([f["test"][method]["auc_macro_f1"] for f in folds])),
            "mean_test_macro_f1_at_40": float(np.mean([f["test"][method]["budgets"]["40"]["macro_f1"] for f in folds])),
            "total_test_recovered_at_40": int(sum(f["test"][method]["budgets"]["40"]["recovered_f1_gt_0_5"] for f in folds)),
            "mean_native_macro_f1": float(np.mean([f["test"][method]["native"]["macro_f1"] for f in folds])),
        }
    ordered = sorted(methods, key=lambda m: (
        aggregate[m]["mean_test_auc_macro_f1"],
        aggregate[m]["total_test_recovered_at_40"],
        aggregate[m]["mean_test_macro_f1_at_40"],
    ), reverse=True)
    winner = ordered[0]

    result = {
        "schema": "ORBITTRACE_SYMMETRIC_TUNED_LITERATURE_BENCHMARK_V2",
        "design": {
            "pooled_label_free_information": "identical common 2013+2014 event intersection for all methods",
            "cross_validation": "two-fold cross-year: tune on 2013/test 2014 and tune on 2014/test 2013",
            "tuning_objective": "maximize mean Hungarian macro-F1 over common candidate budgets 10/20/30/40; tie-break recovered sum, then K40 F1, then grid parsimony",
            "test_scoring": "same Hungarian one-to-one F1 evaluator for all methods",
            "recurrent_grid": [list(x) for x in SUPPORT_GRID],
            "hdbscan_grid": [{"min_cluster_size":a,"min_samples":b,"selection":s} for a,b in SUPPORT_GRID for s in ("eom","leaf")],
            "sugar_grid_percentiles": list(SUGAR_PERCENTILES),
            "sugar_min_samples": SUGAR_MIN_SAMPLES,
            "sugar_tuning_clones": SUGAR_TUNE_CLONES,
            "sugar_final_clones": SUGAR_FINAL_CLONES,
            "budgets": list(BUDGETS),
        },
        "universe": universe,
        "pooled_common_event_count": len(rows),
        "source_sha256": {
            "sugar_uncertainty_core.py": sha256(sugar_source),
            "hdbscan_2025_runner.py": sha256(hdb_source),
            "recurrent_kernel": sha256(args.recurrent_kernel),
        },
        "folds": folds,
        "aggregate": aggregate,
        "winner_by_prespecified_primary_metric": winner,
        "ranking": ordered,
    }
    out = args.output / "SYMMETRIC_TUNED_RESULT.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"winner": winner, "aggregate": aggregate, "selected": [f["selected_configs"] for f in folds]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
