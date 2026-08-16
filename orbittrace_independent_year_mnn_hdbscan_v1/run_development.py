#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability

import orbittrace_recurrent_eom_hdbscan_v1.run_development as parent
from recurrent_eom import eom_labels, selected_eom_nodes

YEARS = parent.YEARS
MONTH_KEYS = parent.MONTH_KEYS
BLIND = parent.BLIND
MIN_CLUSTER_SIZE = parent.MIN_CLUSTER_SIZE
MIN_SAMPLES = parent.MIN_SAMPLES
WINNER_PRELABEL_SHA = "efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993"
WINNER_RESULT_SHA = "ca6aeed2b82739003ea5d39b59e869df876de2962164344a938fe4935ea38711"
WINNER_MEMBERSHIP_SHA = "e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2"
BASELINE_TOTAL_AT100 = 179
REQUIRED_TOTAL_AT100 = 184


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha(tree: np.ndarray) -> str:
    return hashlib.sha256(tree.tobytes()).hexdigest()


def ordered_membership_sha(candidates: list[dict[str, Any]]) -> str:
    payload = "\n".join("|".join(str(x) for x in row["event_ids"]) for row in candidates)
    return hashlib.sha256(payload.encode()).hexdigest()


def partition_signature(labels: np.ndarray) -> tuple[tuple[int, ...], ...]:
    labs = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    groups = [tuple(int(i) for i in np.flatnonzero(labels == lab)) for lab in labs]
    return tuple(sorted(groups))


def annual_clusters(year: int, events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    X = np.asarray(parent.geo_matrix(events), dtype=np.float64)
    req(X.shape == (len(events), 6), f"{year} GEO6 shape changed: {X.shape}")
    req(np.all(np.isfinite(X)), f"{year} GEO6 contains non-finite values")

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
    stability = compute_stability(tree)
    nodes = selected_eom_nodes(tree, stability)
    labels = eom_labels(tree, stability)

    custom_sig = partition_signature(labels)
    canonical_sig = partition_signature(np.asarray(model.labels_, dtype=np.int64))
    req(custom_sig == canonical_sig, f"{year} custom ordinary-EOM partition differs from canonical HDBSCAN")
    req(len(nodes) == len(custom_sig), f"{year} selected-node/partition count mismatch")

    out: list[dict[str, Any]] = []
    n = float(len(events))
    for lab, node in enumerate(nodes):
        idx = np.flatnonzero(labels == lab)
        req(len(idx) >= MIN_CLUSTER_SIZE, f"{year} selected cluster below minimum")
        members = tuple(sorted(str(events[int(i)]["id"]) for i in idx))
        centroid = np.mean(X[idx], axis=0, dtype=np.float64)
        req(np.all(np.isfinite(centroid)), f"{year} non-finite centroid")
        raw_stability = float(stability[float(node)])
        req(np.isfinite(raw_stability) and raw_stability >= 0.0, f"{year} invalid EOM stability")
        cid = parent.member_hash(f"IYMNN-{year}", members)
        out.append({
            "annual_cluster_id": cid,
            "node_id": int(node),
            "event_ids": list(members),
            "member_count": len(members),
            "eom_stability": raw_stability,
            "normalized_stability": raw_stability / n,
            "geo6_centroid": [float(x) for x in centroid],
        })

    # Stable ID order defines exact nearest-neighbor tie semantics.
    out.sort(key=lambda r: str(r["annual_cluster_id"]))
    audit = {
        "year": year,
        "events": len(events),
        "condensed_tree_sha256": tree_sha(tree),
        "selected_nodes": [int(x) for x in nodes],
        "selected_cluster_count": len(out),
        "canonical_partition_identity": True,
        "noise_events": int(np.sum(labels < 0)),
    }
    return out, audit


def nearest_maps(a: list[dict[str, Any]], b: list[dict[str, Any]]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    req(a and b, "annual cluster universe is empty")
    A = np.asarray([r["geo6_centroid"] for r in a], dtype=np.float64)
    B = np.asarray([r["geo6_centroid"] for r in b], dtype=np.float64)
    # Exact squared Euclidean centroid distances; clip roundoff below zero only.
    d2 = np.sum(A * A, axis=1)[:, None] + np.sum(B * B, axis=1)[None, :] - 2.0 * (A @ B.T)
    d2 = np.maximum(d2, 0.0)
    req(np.all(np.isfinite(d2)), "non-finite annual centroid distance matrix")
    a_to_b = np.argmin(d2, axis=1).astype(np.int64)
    b_to_a = np.argmin(d2, axis=0).astype(np.int64)
    return a_to_b, b_to_a, d2


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--winner-prelabel-json", type=Path, required=True)
    p.add_argument("--winner-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha(a.quality_source) == parent.QUALITY_SHA, "frozen GMN utility source changed")
    req(sha(a.v8_result_json) == parent.V8_RESULT_SHA, "frozen GMN support result changed")
    req(sha(a.winner_prelabel_json) == WINNER_PRELABEL_SHA, "binding winner prelabel changed")
    req(sha(a.winner_result_json) == WINNER_RESULT_SHA, "binding winner result changed")
    winner_pre = json.loads(a.winner_prelabel_json.read_text())
    winner_result = json.loads(a.winner_result_json.read_text())
    req(winner_pre["successor_ordered_membership_sha256"] == WINNER_MEMBERSHIP_SHA, "winner membership hash changed")
    req(winner_result["successor_ordered_membership_sha256"] == WINNER_MEMBERSHIP_SHA, "winner result membership hash changed")
    baseline = winner_result["successor_metrics"]
    req(sum(int(baseline[str(y)]["recovered_at_100"]) for y in YEARS) == BASELINE_TOTAL_AT100, "binding baseline total changed")
    req(int(baseline["2022"]["recovered_at_100"]) == 89, "binding 2022 @100 changed")
    req(int(baseline["2023"]["recovered_at_100"]) == 90, "binding 2023 @100 changed")

    qmod = parent.load_module(a.quality_source, "independent_year_mnn_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-independent-year-mnn-hdbscan-v1-development-2022-2023-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_sealed, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), f"GMN runtime accessed wrong years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events_by_year: dict[int, list[dict[str, Any]]] = {}
    all_events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        rows = [parent.normalize_event(row, year) for row in raw]
        req(len(rows) == len(raw), f"event normalization changed {year} event count")
        req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in rows), f"protected region survived parser in {year}")
        events_by_year[year] = rows
        all_events.extend(rows)
    req(len(events_by_year[2022]) == 315024, "accessible 2022 event count changed")
    req(len(events_by_year[2023]) == 423658, "accessible 2023 event count changed")
    req(len(all_events) == 738682, "accessible pooled event count changed")
    req(len({e["id"] for e in all_events}) == len(all_events), "duplicate pooled event IDs")

    annual: dict[int, list[dict[str, Any]]] = {}
    annual_audit: dict[str, Any] = {}
    for year in YEARS:
        annual[year], annual_audit[str(year)] = annual_clusters(year, events_by_year[year])

    a22 = annual[2022]
    a23 = annual[2023]
    map22, map23, d2 = nearest_maps(a22, a23)

    reciprocal: list[dict[str, Any]] = []
    used22: set[int] = set()
    used23: set[int] = set()
    for i, j_raw in enumerate(map22):
        j = int(j_raw)
        if int(map23[j]) != i:
            continue
        req(i not in used22 and j not in used23, "reciprocal nearest matching lost one-to-one property")
        used22.add(i)
        used23.add(j)
        r22 = a22[i]
        r23 = a23[j]
        members = tuple(sorted(set(str(x) for x in r22["event_ids"]) | set(str(x) for x in r23["event_ids"])))
        req(len(members) == int(r22["member_count"]) + int(r23["member_count"]), "cross-year member IDs overlap unexpectedly")
        s22 = float(r22["normalized_stability"])
        s23 = float(r23["normalized_stability"])
        fid = parent.member_hash("IYMNN1", members)
        reciprocal.append({
            "family_id": fid,
            "annual_cluster_id_2022": r22["annual_cluster_id"],
            "annual_cluster_id_2023": r23["annual_cluster_id"],
            "node_id_2022": int(r22["node_id"]),
            "node_id_2023": int(r23["node_id"]),
            "event_ids": list(members),
            "member_count": len(members),
            "normalized_stability_2022": s22,
            "normalized_stability_2023": s23,
            "recurrence_score": min(s22, s23),
            "stability_sum": s22 + s23,
            "centroid_distance": float(np.sqrt(d2[i, j])),
        })

    reciprocal.sort(key=lambda r: (
        -float(r["recurrence_score"]),
        -float(r["stability_sum"]),
        -int(r["member_count"]),
        str(r["family_id"]),
    ))
    candidate_count = len(reciprocal)
    largest = max((int(r["member_count"]) for r in reciprocal), default=0)
    membership_sha = ordered_membership_sha(reciprocal)

    nearest_22 = [
        {
            "cluster_id_2022": a22[i]["annual_cluster_id"],
            "nearest_cluster_id_2023": a23[int(j)]["annual_cluster_id"],
            "centroid_distance": float(np.sqrt(d2[i, int(j)])),
        }
        for i, j in enumerate(map22)
    ]
    nearest_23 = [
        {
            "cluster_id_2023": a23[j]["annual_cluster_id"],
            "nearest_cluster_id_2022": a22[int(i)]["annual_cluster_id"],
            "centroid_distance": float(np.sqrt(d2[int(i), j])),
        }
        for j, i in enumerate(map23)
    ]

    structural = {
        "at_least_100_reciprocal_families": candidate_count >= 100,
        "largest_family_at_most_1pct_all_events": largest <= int(np.floor(0.01 * len(all_events))),
        "annual_clusters_one_to_one": len(used22) == candidate_count and len(used23) == candidate_count,
        "differs_from_binding_winner": membership_sha != WINNER_MEMBERSHIP_SHA,
        "annual_partition_identity_2022": bool(annual_audit["2022"]["canonical_partition_identity"]),
        "annual_partition_identity_2023": bool(annual_audit["2023"]["canonical_partition_identity"]),
    }

    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_INDEPENDENT_YEAR_MNN_HDBSCAN_V1",
        "representation": "INHERITED_GEO6_UNCHANGED",
        "architecture": "independent_annual_hdbscan_eom_then_reciprocal_nearest_centroid_pairing",
        "matching": "mutual_nearest_geo6_centroid_no_threshold",
        "ranking": "min_annual_eom_stability_divided_by_annual_event_count",
        "events_total": len(all_events),
        "events_by_year": {str(y): len(events_by_year[y]) for y in YEARS},
        "annual_audit": annual_audit,
        "annual_clusters": {"2022": a22, "2023": a23},
        "nearest_map_2022_to_2023": nearest_22,
        "nearest_map_2023_to_2022": nearest_23,
        "candidate_count": candidate_count,
        "largest_family_members": largest,
        "ordered_membership_sha256": membership_sha,
        "binding_winner_ordered_membership_sha256": WINNER_MEMBERSHIP_SHA,
        "structural_gates": structural,
        "candidates": reciprocal,
        "known_shower_labels_indexed": False,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_access": False,
        "efn_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "INDEPENDENT_YEAR_MNN_HDBSCAN_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    # Truth stays sealed until both annual trees, pair mapping, memberships and rank are durable.
    hidden = hidden_sealed
    ids_by_year = {y: {str(e["id"]) for e in events_by_year[y]} for y in YEARS}
    req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden), "label outside accessible pooled event IDs")
    successor = {str(y): parent.metrics(reciprocal, hidden, ids_by_year[y]) for y in YEARS}
    annual_gates = {str(y): parent.annual_gate(baseline[str(y)], successor[str(y)]) for y in YEARS}
    successor_total = sum(int(successor[str(y)]["recovered_at_100"]) for y in YEARS)
    gain = successor_total - BASELINE_TOTAL_AT100
    passed = bool(
        all(structural.values())
        and successor_total >= REQUIRED_TOTAL_AT100
        and all(all(g.values()) for g in annual_gates.values())
    )
    verdict = "PASS_INDEPENDENT_YEAR_MNN_HDBSCAN_V1_GMN_DEVELOPMENT" if passed else "FAIL_INDEPENDENT_YEAR_MNN_HDBSCAN_V1_GMN_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "prelabel_sha256": prelabel_sha,
        "architecture": prelabel["architecture"],
        "matching": prelabel["matching"],
        "ranking": prelabel["ranking"],
        "annual_selected_cluster_counts": {str(y): int(annual_audit[str(y)]["selected_cluster_count"]) for y in YEARS},
        "candidate_count": candidate_count,
        "largest_family_members": largest,
        "ordered_membership_sha256": membership_sha,
        "binding_winner_ordered_membership_sha256": WINNER_MEMBERSHIP_SHA,
        "structural_gates": structural,
        "baseline_metrics": baseline,
        "successor_metrics": successor,
        "annual_gates": annual_gates,
        "baseline_total_recovered_at_100": BASELINE_TOTAL_AT100,
        "successor_total_recovered_at_100": successor_total,
        "recovered_at_100_gain": gain,
        "required_total_recovered_at_100": REQUIRED_TOTAL_AT100,
        "required_gain": REQUIRED_TOTAL_AT100 - BASELINE_TOTAL_AT100,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_access": False,
        "efn_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    (a.output / "INDEPENDENT_YEAR_MNN_HDBSCAN_V1_GMN_DEVELOPMENT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(json.dumps({
        "verdict": verdict,
        "annual_selected_cluster_counts": result["annual_selected_cluster_counts"],
        "candidate_count": candidate_count,
        "largest_family_members": largest,
        "baseline_total_at100": BASELINE_TOTAL_AT100,
        "successor_total_at100": successor_total,
        "gain": gain,
        "structural_gates": structural,
        "2022": {k: successor["2022"][k] for k in ("recovered_at_50","recovered_at_100","top100_dominant_precision","mrr","fragmentation_median_top500")},
        "2023": {k: successor["2023"][k] for k in ("recovered_at_50","recovered_at_100","top100_dominant_precision","mrr","fragmentation_median_top500")},
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
