#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np

from knn_year_mixing import candidate_knn_mixing, mixed_score

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
PARENT_PRELABEL_SHA256 = "e304f6660697ed27a7e2e546ba2b9f2ecdb43f923745cb7424a3781ad55b9ad1"
PARENT_RESULT_SHA256 = "433c641f57122b244b9476f5cbcb5e6f82956d9467270a9f24945600a32d2106"
K_BASE = 10


def req(cond: bool, msg: str) -> None:
    if not cond:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def membership_signature(rows: list[dict[str, Any]]) -> list[tuple[str, ...]]:
    return [tuple(sorted(str(x) for x in row["event_ids"])) for row in rows]


def membership_universe(rows: list[dict[str, Any]]) -> set[tuple[str, ...]]:
    return set(membership_signature(rows))


def make_successor(
    binding_candidates: list[dict[str, Any]],
    event_by_id: dict[str, dict[str, Any]],
    parent: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    out: list[dict[str, Any]] = []
    enrichments: list[float] = []
    cross_fracs: list[float] = []
    one_year = 0
    total_edges = 0

    for ordinal, source in enumerate(binding_candidates):
        members = tuple(sorted(str(x) for x in source["event_ids"]))
        req(len(members) == int(source["member_count"]), f"binding member count mismatch at candidate {ordinal}")
        req(len(set(members)) == len(members), f"duplicate event ID inside candidate {ordinal}")
        try:
            rows = [event_by_id[eid] for eid in members]
        except KeyError as exc:
            raise RuntimeError(f"binding candidate event missing from accessible GMN rows: {exc.args[0]}") from exc

        X = parent.geo_matrix(rows)
        years = np.asarray([int(row["year"]) for row in rows], dtype=np.int64)
        stat = candidate_knn_mixing(X, years, k_base=K_BASE)
        req(stat.member_count == len(members), f"kNN/member count mismatch at candidate {ordinal}")
        req(stat.directed_edges == len(members) * min(K_BASE, len(members) - 1),
            f"directed edge count mismatch at candidate {ordinal}")
        req(np.isfinite(stat.expected_cross_year_edges), f"non-finite expected edges at candidate {ordinal}")
        req(np.isfinite(stat.mixing_enrichment), f"non-finite enrichment at candidate {ordinal}")

        rec = float(source["recurrent_stability"])
        ordinary = float(source["ordinary_stability"])
        score = mixed_score(rec, stat.mixing_enrichment)
        family_id = parent.member_hash("REOMKNN1", members)
        out.append({
            "family_id": family_id,
            "parent_family_id": str(source["family_id"]),
            "node_id": int(source["node_id"]),
            "event_ids": list(members),
            "member_count": len(members),
            "ordinary_stability": ordinary,
            "recurrent_stability": rec,
            "knn_k": int(stat.k),
            "knn_directed_edges": int(stat.directed_edges),
            "knn_cross_year_edges": int(stat.cross_year_edges),
            "knn_expected_cross_year_edges": float(stat.expected_cross_year_edges),
            "knn_mixing_enrichment": float(stat.mixing_enrichment),
            "knn_mixed_score": float(score),
            "year_counts": list(stat.year_counts),
        })
        enrichments.append(float(stat.mixing_enrichment))
        cross_fracs.append(float(stat.cross_year_edges) / float(stat.directed_edges))
        one_year += int(0 in stat.year_counts)
        total_edges += int(stat.directed_edges)

    out.sort(key=lambda f: (
        -f["knn_mixed_score"],
        -f["recurrent_stability"],
        -f["ordinary_stability"],
        -f["member_count"],
        f["family_id"],
    ))
    summary = {
        "min_enrichment": float(min(enrichments)),
        "median_enrichment": float(np.median(enrichments)),
        "max_enrichment": float(max(enrichments)),
        "mean_enrichment": float(np.mean(enrichments)),
        "median_cross_year_edge_fraction": float(np.median(cross_fracs)),
        "one_year_candidates": int(one_year),
        "total_directed_edges": int(total_edges),
    }
    return out, summary


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--parent-runner", type=Path, required=True)
    p.add_argument("--parent-prelabel-json", type=Path, required=True)
    p.add_argument("--parent-result-json", type=Path, required=True)
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha(a.quality_source) == QUALITY_SHA, "frozen GMN runtime utility source changed")
    req(sha(a.v8_result_json) == V8_RESULT_SHA, "frozen GMN support artifact changed")
    req(sha(a.parent_prelabel_json) == PARENT_PRELABEL_SHA256, "binding recurrent prelabel artifact changed")
    req(sha(a.parent_result_json) == PARENT_RESULT_SHA256, "binding recurrent result artifact changed")

    parent = load_module(a.parent_runner, "reom_parent_runner_exact_knn_mix")
    binding_prelabel = json.loads(a.parent_prelabel_json.read_text())
    req(binding_prelabel["scientific_role"] == "PRELABEL_FROZEN_RECURRENT_EOM_HDBSCAN_V1",
        "binding recurrent prelabel role changed")
    binding_candidates = list(binding_prelabel["successor_candidates"])
    req(len(binding_candidates) == 2097, f"binding recurrent candidate count changed: {len(binding_candidates)}")
    req(len(membership_universe(binding_candidates)) == 2097, "binding recurrent membership universe contains duplicates")

    qmod = parent.load_module(a.quality_source, "knn_mix_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-recurrent-eom-knn-year-mixing-v1-development-2022-2023-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_sealed, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), f"GMN runtime accessed wrong years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        rows = [parent.normalize_event(row, year) for row in raw]
        req(len(rows) == len(raw), f"event normalization changed {year} event count")
        events.extend(rows)
    req(len(events) == 738682, f"pooled accessible event count changed: {len(events)}")
    req(sum(int(e["year"]) == 2022 for e in events) == 315024, "2022 accessible event count changed")
    req(sum(int(e["year"]) == 2023 for e in events) == 423658, "2023 accessible event count changed")
    req(len({str(e["id"]) for e in events}) == len(events), "duplicate pooled accessible event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected region survived parser")
    event_by_id = {str(e["id"]): e for e in events}

    binding_member_ids = [str(eid) for row in binding_candidates for eid in row["event_ids"]]
    req(all(eid in event_by_id for eid in binding_member_ids), "binding candidate contains inaccessible/missing GMN event")

    successor_candidates, mixing_summary = make_successor(binding_candidates, event_by_id, parent)
    req(len(successor_candidates) == 2097, "rank-only successor candidate count changed")
    req(membership_universe(successor_candidates) == membership_universe(binding_candidates),
        "rank-only successor changed recurrent membership universe")
    mechanism_active = membership_signature(successor_candidates) != membership_signature(binding_candidates)

    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_RECURRENT_EOM_KNN_YEAR_MIXING_V1",
        "parent_prelabel_sha256": PARENT_PRELABEL_SHA256,
        "events_total": len(events),
        "events_by_year": {"2022": 315024, "2023": 423658},
        "candidate_count": 2097,
        "membership_universe_identical": True,
        "mechanism_active": bool(mechanism_active),
        "k_base": K_BASE,
        "mixing_summary": mixing_summary,
        "parent_candidates": binding_candidates,
        "successor_candidates": successor_candidates,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "RECURRENT_EOM_KNN_YEAR_MIXING_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    # Truth-bearing recurrent result is parsed only after the complete successor
    # order has been persisted. `hidden_sealed` is not inspected before here.
    binding_result = json.loads(a.parent_result_json.read_text())
    req(binding_result["verdict"] == "PASS_RECURRENT_EOM_HDBSCAN_V1_GMN_DEVELOPMENT",
        "wrong binding recurrent parent result")

    hidden = hidden_sealed
    ids_by_year = {y: {str(e["id"]) for e in events if int(e["year"]) == y} for y in YEARS}
    req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden),
        "shower truth contains ID outside accessible pooled events")

    parent_metrics = {str(y): parent.metrics(binding_candidates, hidden, ids_by_year[y]) for y in YEARS}
    successor_metrics = {str(y): parent.metrics(successor_candidates, hidden, ids_by_year[y]) for y in YEARS}
    req(parent_metrics == binding_result["successor_metrics"],
        "binding recurrent parent metrics failed exact reproduction")

    annual_gates = {str(y): parent.annual_gate(parent_metrics[str(y)], successor_metrics[str(y)]) for y in YEARS}
    strict_100 = any(
        int(successor_metrics[str(y)]["recovered_at_100"]) > int(parent_metrics[str(y)]["recovered_at_100"])
        for y in YEARS
    )
    passed = bool(mechanism_active and strict_100 and all(all(g.values()) for g in annual_gates.values()))
    verdict = (
        "PASS_RECURRENT_EOM_KNN_YEAR_MIXING_V1_GMN_DEVELOPMENT"
        if passed
        else "FAIL_RECURRENT_EOM_KNN_YEAR_MIXING_V1_GMN_DEVELOPMENT"
    )

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "prelabel_sha256": prelabel_sha,
        "parent_prelabel_sha256": PARENT_PRELABEL_SHA256,
        "parent_result_sha256": PARENT_RESULT_SHA256,
        "events_total": len(events),
        "events_by_year": {str(y): len(ids_by_year[y]) for y in YEARS},
        "candidate_count": 2097,
        "membership_universe_identical": True,
        "mechanism_active": bool(mechanism_active),
        "strict_recovered_at_100_improvement_some_year": bool(strict_100),
        "k_base": K_BASE,
        "mixing_summary": mixing_summary,
        "parent_metrics": parent_metrics,
        "successor_metrics": successor_metrics,
        "annual_gates": annual_gates,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    result_path = a.output / "RECURRENT_EOM_KNN_YEAR_MIXING_V1_GMN_DEVELOPMENT.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")

    def compact(m: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in m.items() if k != "first_rank_by_label"}

    print(json.dumps({
        "verdict": verdict,
        "mechanism_active": mechanism_active,
        "strict_recovered_at_100_improvement_some_year": strict_100,
        "mixing_summary": mixing_summary,
        "parent": {y: compact(m) for y, m in parent_metrics.items()},
        "successor": {y: compact(m) for y, m in successor_metrics.items()},
        "annual_gates": annual_gates,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
