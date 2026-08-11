#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
EXPECTED = (226, 1075, 3203, 4504)
P19_PRELABEL_SHA = "276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8"
P20_PRELABEL_SHA = "8ca358ae0f3ac96b188de9eac7bcfd6f870470873a2b7ee73b7ae76497c12734"
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
CENTROID_THRESHOLD = 1.0


def req(x: bool, msg: str) -> None:
    if not x:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def circular_delta(a: float, b: float) -> float:
    return abs((float(a) - float(b) + 180.0) % 360.0 - 180.0)


def centroid_distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    annual: list[float] = []
    for year in YEARS:
        ca = a.get("centroids", {}).get(str(year))
        cb = b.get("centroids", {}).get(str(year))
        req(ca is not None and cb is not None, f"missing centroid for {year}")
        ds = circular_delta(float(ca["sol"]), float(cb["sol"])) / 10.0
        dsu = circular_delta(float(ca["sun_lon"]), float(cb["sun_lon"])) / 4.0
        dl = abs(float(ca["ecl_lat"]) - float(cb["ecl_lat"])) / 4.0
        va = math.log(max(abs(float(ca["vg"])), 1e-6))
        vb = math.log(max(abs(float(cb["vg"])), 1e-6))
        dv = abs(va - vb) / math.log(1.10)
        annual.append(math.sqrt(ds * ds + dsu * dsu + dl * dl + dv * dv))
    return max(annual)


def load_prelabels(p19_path: Path, p20_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    req(sha(p19_path) == P19_PRELABEL_SHA, "P19 prelabel payload changed")
    req(sha(p20_path) == P20_PRELABEL_SHA, "P20 prelabel payload changed")
    p19 = json.loads(p19_path.read_text())
    p20 = json.loads(p20_path.read_text())
    hard = list(p19["hard_families"])
    s19 = list(p19["soft_families"])
    s20 = list(p20["soft_families"])
    fams = hard + s19 + s20
    req((len(hard), len(s19), len(s20), len(fams)) == EXPECTED, "candidate universe changed")
    ids = [str(f["family_id"]) for f in fams]
    req(len(ids) == len(set(ids)), "family IDs collide")
    hard20 = list(p20["hard_families"])
    req([str(f["family_id"]) for f in hard20] == [str(f["family_id"]) for f in hard], "hard family identities differ between prelabels")
    return hard, s19, s20, fams


def freeze_graph(args: argparse.Namespace) -> int:
    hard, s19, s20, fams = load_prelabels(args.p19_prelabel_json, args.p20_prelabel_json)
    by19 = {str(f["family_id"]): f for f in s19}
    by20 = {str(f["family_id"]): f for f in s20}

    p20_by_event: dict[str, list[str]] = collections.defaultdict(list)
    for f in s20:
        fid = str(f["family_id"])
        events = list(map(str, f.get("event_ids", [])))
        req(len(events) == len(set(events)), f"duplicate event ID within {fid}")
        for event_id in events:
            p20_by_event[event_id].append(fid)

    shared: dict[tuple[str, str], int] = collections.Counter()
    for f in s19:
        fid19 = str(f["family_id"])
        events = list(map(str, f.get("event_ids", [])))
        req(len(events) == len(set(events)), f"duplicate event ID within {fid19}")
        for event_id in events:
            for fid20 in p20_by_event.get(event_id, []):
                shared[(fid19, fid20)] += 1

    edges: list[dict[str, Any]] = []
    for fid19, fid20 in sorted(shared):
        d = centroid_distance(by19[fid19], by20[fid20])
        if d <= CENTROID_THRESHOLD:
            edges.append(
                {
                    "p19_family_id": fid19,
                    "p20_family_id": fid20,
                    "shared_event_count": int(shared[(fid19, fid20)]),
                    "centroid_distance": float(d),
                }
            )

    edge_lines = [
        f"{x['p19_family_id']}\t{x['p20_family_id']}\t{x['shared_event_count']}\t{x['centroid_distance']:.17g}"
        for x in edges
    ]
    canonical_sha = hashlib.sha256("\n".join(edge_lines).encode()).hexdigest()
    graph = {
        "stage": "GMN_TARGET_EXCLUDED_CROSSGENERATOR_CONSENSUS_PRETRUTH_V1",
        "pretruth_graph_frozen": True,
        "candidate_counts": {"hard": len(hard), "p19": len(s19), "p20": len(s20), "union": len(fams)},
        "edge_rule": {
            "sources": ["p19", "p20"],
            "exact_shared_event_required": True,
            "minimum_shared_event_count": 1,
            "centroid_metric": "exact #839 two-year max annual normalized Euclidean centroid distance",
            "centroid_distance_max": CENTROID_THRESHOLD,
            "threshold_inherited_from_839_diversity_scale": True,
        },
        "edge_count": len(edges),
        "canonical_edge_sha256": canonical_sha,
        "edges": edges,
        "labels_loaded": False,
        "truth_accessed": False,
        "candidate_order_evaluated": False,
        "membership_changed": False,
        "sonotaco_2013_2014_access": False,
        "sonotaco_feature_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "blind_exclusion": list(BLIND),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(graph, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"edge_count": len(edges), "canonical_edge_sha256": canonical_sha, "graph_file_sha256": sha(args.output)}, indent=2, sort_keys=True))
    return 0


def evaluate_graph(args: argparse.Namespace) -> int:
    req(sha(args.quality_source) == QUALITY_SHA, "#839 quality source changed")
    hard, s19, s20, fams = load_prelabels(args.p19_prelabel_json, args.p20_prelabel_json)
    req(sha(args.graph_json) == args.expected_graph_sha256, "pretruth graph file SHA mismatch")
    graph = json.loads(args.graph_json.read_text())
    req(graph["pretruth_graph_frozen"] is True and graph["labels_loaded"] is False and graph["truth_accessed"] is False, "graph was not frozen pretruth")
    req(graph["candidate_order_evaluated"] is False and graph["membership_changed"] is False, "graph artifact contains unauthorized ranking/membership operation")
    req(graph["candidate_counts"] == {"hard": 226, "p19": 1075, "p20": 3203, "union": 4504}, "graph candidate counts changed")
    req(graph["edge_rule"]["sources"] == ["p19", "p20"], "graph source rule changed")
    req(graph["edge_rule"]["exact_shared_event_required"] is True and graph["edge_rule"]["minimum_shared_event_count"] == 1, "graph overlap rule changed")
    req(abs(float(graph["edge_rule"]["centroid_distance_max"]) - CENTROID_THRESHOLD) < 1e-15, "graph centroid threshold changed")
    for row in graph["edges"]:
        req(set(row) == {"p19_family_id", "p20_family_id", "shared_event_count", "centroid_distance"}, "graph edge contains non-pretruth field")
        req(int(row["shared_event_count"]) >= 1 and float(row["centroid_distance"]) <= CENTROID_THRESHOLD + 1e-15, "invalid frozen edge")

    # Only now load the target-excluded GMN development labels.
    qmod = load_module(args.quality_source, "frozen_839_consensus_diagnostic")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-gmn-crossgenerator-consensus-diagnostic-v1"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(args, "fixed4_baseline_json", args.v8_result_json)
    _candidate, base, _scorer = support.load_sources(args)
    scan, _cal, labels, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS) and [x["key"] for x in sources] == list(MONTH_KEYS), "GMN development panel changed")

    eligible = qmod.v1.eligible_labels(labels)
    ids = [str(f["family_id"]) for f in fams]
    by = {str(f["family_id"]): f for f in fams}
    truths = {fid: qmod.v1.family_truth(by[fid], labels, eligible) for fid in ids}
    source: dict[str, str] = {str(f["family_id"]): "hard" for f in hard}
    source.update({str(f["family_id"]): "p19" for f in s19})
    source.update({str(f["family_id"]): "p20" for f in s20})

    qualified_ids = [fid for fid in ids if bool(truths[fid]["positive"])]
    label_to_ids: dict[str, list[str]] = collections.defaultdict(list)
    label_to_sources: dict[str, set[str]] = collections.defaultdict(set)
    for fid in qualified_ids:
        label = str(truths[fid]["best_label"])
        label_to_ids[label].append(fid)
        label_to_sources[label].add(source[fid])

    qualified_edge_count = 0
    same_label_edge_count = 0
    captured_labels: set[str] = set()
    different_label_edge_count = 0
    for row in graph["edges"]:
        a = str(row["p19_family_id"])
        b = str(row["p20_family_id"])
        req(source.get(a) == "p19" and source.get(b) == "p20", "frozen graph endpoint source mismatch")
        if bool(truths[a]["positive"]) and bool(truths[b]["positive"]):
            qualified_edge_count += 1
            la = str(truths[a]["best_label"])
            lb = str(truths[b]["best_label"])
            if la == lb:
                same_label_edge_count += 1
                captured_labels.add(la)
            else:
                different_label_edge_count += 1

    precision = float(same_label_edge_count / qualified_edge_count) if qualified_edge_count else 0.0
    crossgen_duplicate = {
        label for label, srcs in label_to_sources.items() if "p19" in srcs and "p20" in srcs
    }
    captured_crossgen = captured_labels & crossgen_duplicate
    crossgen_capture = float(len(captured_crossgen) / len(crossgen_duplicate)) if crossgen_duplicate else 0.0
    all_duplicate = {label for label, members in label_to_ids.items() if len(members) >= 2}
    captured_all = captured_labels & all_duplicate
    all_capture = float(len(captured_all) / len(all_duplicate)) if all_duplicate else 0.0

    gates = {
        "qualified_edge_count_ge_20": qualified_edge_count >= 20,
        "qualified_edge_same_label_precision_ge_0_95": precision >= 0.95,
        "crossgenerator_duplicate_label_count_ge_20": len(crossgen_duplicate) >= 20,
        "crossgenerator_duplicate_label_capture_ge_0_50": crossgen_capture >= 0.50,
        "all_duplicate_label_capture_ge_0_25": all_capture >= 0.25,
    }
    passed = all(gates.values())
    result = {
        "stage": "GMN_TARGET_EXCLUDED_CROSSGENERATOR_CONSENSUS_DIAGNOSTIC_V1",
        "verdict": "PASS_GMN_CROSSGENERATOR_CONSENSUS_DIAGNOSTIC_V1" if passed else "FAIL_GMN_CROSSGENERATOR_CONSENSUS_DIAGNOSTIC_V1",
        "graph_file_sha256": sha(args.graph_json),
        "graph_canonical_edge_sha256": graph["canonical_edge_sha256"],
        "graph_edge_count": int(graph["edge_count"]),
        "candidate_counts": {"hard": len(hard), "p19": len(s19), "p20": len(s20), "union": len(fams)},
        "eligible_label_count": len(eligible),
        "qualified_family_count": len(qualified_ids),
        "qualified_label_count": len(label_to_ids),
        "qualified_edge_count": qualified_edge_count,
        "same_label_qualified_edge_count": same_label_edge_count,
        "different_label_qualified_edge_count": different_label_edge_count,
        "qualified_edge_same_label_precision": precision,
        "crossgenerator_duplicate_label_count": len(crossgen_duplicate),
        "captured_crossgenerator_duplicate_label_count": len(captured_crossgen),
        "crossgenerator_duplicate_label_capture": crossgen_capture,
        "all_duplicate_label_count": len(all_duplicate),
        "captured_all_duplicate_label_count": len(captured_all),
        "all_duplicate_label_capture": all_capture,
        "gates": gates,
        "candidate_order_evaluated": False,
        "suppression_rule_evaluated": False,
        "merged_membership_evaluated": False,
        "component_construction_evaluated": False,
        "threshold_search": False,
        "source_quota_selected": False,
        "family_deletion": False,
        "post_result_second_graph": False,
        "sonotaco_2013_2014_access": False,
        "sonotaco_feature_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "blind_exclusion": list(BLIND),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="phase", required=True)

    freeze = sub.add_parser("freeze")
    freeze.add_argument("--p19-prelabel-json", type=Path, required=True)
    freeze.add_argument("--p20-prelabel-json", type=Path, required=True)
    freeze.add_argument("--output", type=Path, required=True)

    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--graph-json", type=Path, required=True)
    evaluate.add_argument("--expected-graph-sha256", required=True)
    evaluate.add_argument("--p19-prelabel-json", type=Path, required=True)
    evaluate.add_argument("--p20-prelabel-json", type=Path, required=True)
    evaluate.add_argument("--quality-source", type=Path, required=True)
    evaluate.add_argument("--support-source-parts", type=Path, required=True)
    evaluate.add_argument("--candidate-payload", type=Path, required=True)
    evaluate.add_argument("--baseline-payload", type=Path, required=True)
    evaluate.add_argument("--scorer-parts", type=Path, required=True)
    evaluate.add_argument("--v8-result-json", type=Path, required=True)
    evaluate.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    if args.phase == "freeze":
        return freeze_graph(args)
    return evaluate_graph(args)


if __name__ == "__main__":
    raise SystemExit(main())
