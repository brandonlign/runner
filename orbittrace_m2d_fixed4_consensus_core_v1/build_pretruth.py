#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
FAIR_PRETRUTH_SHA256 = "8b0f4629659c1bfd750747303ad04ff67355adf66d4dbe474ce7fba788f5bae5"
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
EXPECTED_COUNTS = {"2022": 315024, "2023": 423658}
EXPECTED_TOTAL = 738682
ANCHOR_MULTIPLICITY = 2
NEAREST_OTHERS = 3


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def fixed4_event(e: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(e["id"]),
        "year": int(e["year"]),
        "sol": float(e["sol"]),
        "sun_lon": float(e["lon"]),
        "ecl_lat": float(e["lat"]),
        "vg": float(e["vg"]),
    }


def annual_core(rows: list[dict[str, Any]], support: Any, base: Any) -> dict[str, Any]:
    rows = sorted(rows, key=lambda e: str(e["id"]))
    ids = [str(e["id"]) for e in rows]
    if len(rows) < 4:
        return {
            "event_ids": [],
            "member_count": 0,
            "eligible_quartet_count": 0,
            "unique_anchor_quartet_count": 0,
            "anchor_count": len(rows),
            "corroborated_quartets": [],
        }

    votes: Counter[tuple[str, ...]] = Counter()
    for i, anchor in enumerate(rows):
        others = rows[:i] + rows[i + 1 :]
        distances = np.asarray(support.exact_anchor_distances(anchor, others, base), dtype=float)
        req(distances.shape == (len(others),), "fixed4 distance shape")
        req(np.all(np.isfinite(distances)) and np.all(distances >= 0.0), "invalid fixed4 distances")
        order = np.argsort(distances, kind="stable")[:NEAREST_OTHERS]
        req(len(order) == NEAREST_OTHERS, "insufficient fixed4 neighbors")
        quartet = tuple(sorted([str(anchor["id"])] + [str(others[int(j)]["id"]) for j in order]))
        req(len(set(quartet)) == 4, "non-unique quartet")
        votes[quartet] += 1

    retained = sorted((q, n) for q, n in votes.items() if n >= ANCHOR_MULTIPLICITY)
    keep: set[str] = set()
    out_quartets: list[dict[str, Any]] = []
    for quartet, n in retained:
        keep.update(quartet)
        out_quartets.append({"event_ids": list(quartet), "anchor_votes": int(n)})
    core = sorted(keep)
    req(set(core).issubset(ids), "fixed4 core escaped envelope")
    return {
        "event_ids": core,
        "member_count": len(core),
        "eligible_quartet_count": len(retained),
        "unique_anchor_quartet_count": len(votes),
        "anchor_count": len(rows),
        "corroborated_quartets": out_quartets,
    }


def candidate_core(candidate: dict[str, Any], by_id: dict[str, dict[str, Any]], support: Any, base: Any) -> dict[str, Any]:
    envelope = [str(x) for x in candidate["event_ids"]]
    req(len(envelope) == len(set(envelope)) == int(candidate["member_count"]), "parent membership mismatch")
    annual: dict[str, Any] = {}
    combined: set[str] = set()
    for y in YEARS:
        native = [fixed4_event(by_id[eid]) for eid in envelope if int(by_id[eid]["year"]) == y]
        result = annual_core(native, support, base)
        annual[str(y)] = result
        combined.update(result["event_ids"])
    core = sorted(combined)
    req(set(core).issubset(envelope), "combined core escaped envelope")
    return {
        "family_id": str(candidate["family_id"]),
        "family_hash": str(candidate["family_hash"]),
        "rank": int(candidate["internal_mass_rank"]),
        "envelope_member_count": len(envelope),
        "core_event_ids": core,
        "core_member_count": len(core),
        "removed_member_count": len(envelope) - len(core),
        "retained_fraction": float(len(core) / len(envelope)) if envelope else 0.0,
        "annual": annual,
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    e = np.asarray([int(r["envelope_member_count"]) for r in rows], dtype=float)
    c = np.asarray([int(r["core_member_count"]) for r in rows], dtype=float)
    return {
        "candidate_count": len(rows),
        "nonempty_core_count": int(np.sum(c > 0)),
        "active_shrink_count": int(np.sum(c < e)),
        "unchanged_count": int(np.sum(c == e)),
        "mean_envelope_members": float(np.mean(e)) if len(e) else 0.0,
        "mean_core_members": float(np.mean(c)) if len(c) else 0.0,
        "median_envelope_members": float(np.median(e)) if len(e) else 0.0,
        "median_core_members": float(np.median(c)) if len(c) else 0.0,
        "p90_envelope_members": float(np.quantile(e, 0.9)) if len(e) else 0.0,
        "p90_core_members": float(np.quantile(c, 0.9)) if len(c) else 0.0,
        "max_envelope_members": int(np.max(e)) if len(e) else 0,
        "max_core_members": int(np.max(c)) if len(c) else 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fair-pretruth", type=Path, required=True)
    ap.add_argument("--geometry", type=Path, required=True)
    ap.add_argument("--quality-source", type=Path, required=True)
    ap.add_argument("--support-source-parts", type=Path, required=True)
    ap.add_argument("--candidate-payload", type=Path, required=True)
    ap.add_argument("--baseline-payload", type=Path, required=True)
    ap.add_argument("--scorer-parts", type=Path, required=True)
    ap.add_argument("--v8-result-json", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(sha(a.fair_pretruth) == FAIR_PRETRUTH_SHA256, "fair pretruth changed")
    req(sha(a.quality_source) == QUALITY_SHA256, "quality runtime changed")
    req(sha(a.v8_result_json) == V8_SHA256, "v8 support artifact changed")
    fair = json.loads(a.fair_pretruth.read_text())
    req(fair["scientific_role"] == "TARGET_EXCLUDED_GMN_SPARSE_LITERATURE_COMPARATORS_FROZEN_BEFORE_TRUTH", "wrong fair role")
    req(fair["shower_truth_used"] is False and fair["target_information_access"] is False and fair["target_region_events_accessed"] is False, "fair firewall")

    geom = json.loads(a.geometry.read_text())
    req(geom["scientific_role"] == "LABEL_FREE_TARGET_EXCLUDED_GMN_GEOMETRY_ONLY", "wrong geometry role")
    req(int(geom["events_total"]) == EXPECTED_TOTAL and geom["events_by_year"] == EXPECTED_COUNTS, "geometry counts changed")
    req(geom["blind_exclusion"] == list(BLIND) and geom["shower_truth_exported"] is False, "geometry firewall")
    events = list(geom["events"])
    req(len(events) == EXPECTED_TOTAL, "geometry row count")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected geometry survived")
    by_id = {str(e["id"]): e for e in events}
    req(len(by_id) == EXPECTED_TOTAL, "duplicate geometry IDs")

    q = load(a.quality_source, "m2d_fixed4_consensus_quality")
    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    rt = q.v1.mult.load_frozen_runtime()
    support = rt.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-m2d-fixed4-consensus-core-v1-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "support firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    req(callable(getattr(support, "exact_anchor_distances", None)), "missing exact fixed4 distance")

    subset_rows: list[dict[str, Any]] = []
    all_core_rows: list[dict[str, Any]] = []
    for subset in fair["subsets"]:
        d, b = int(subset["denominator"]), int(subset["bucket"])
        parents = list(subset["successor_candidates"])
        req([int(x["internal_mass_rank"]) for x in parents] == list(range(1, len(parents) + 1)), f"rank drift d{d}b{b}")
        cores: list[dict[str, Any]] = []
        for pos, candidate in enumerate(parents, 1):
            req(all(str(eid) in by_id for eid in candidate["event_ids"]), f"missing geometry d{d}b{b} rank{pos}")
            row = candidate_core(candidate, by_id, support, base)
            req(row["rank"] == pos, f"rank mismatch d{d}b{b} rank{pos}")
            cores.append(row)
            all_core_rows.append(row)
        s = summarize(cores)
        subset_rows.append({
            "denominator": d,
            "bucket": b,
            "event_count": int(subset["event_count"]),
            "annual_event_ids": subset["annual_event_ids"],
            "parent_candidate_count": len(parents),
            "cores": cores,
            "summary": s,
        })
        print(json.dumps({"panel": f"d{d}_b{b}", **s}, sort_keys=True), flush=True)

    payload = {
        "schema": "ORBITTRACE_M2D_FIXED4_CONSENSUS_CORE_V1_PRETRUTH",
        "scientific_role": "TARGET_EXCLUDED_M2D_ENVELOPES_WITH_EXACT_FIXED4_TWO_ANCHOR_CONSENSUS_CORES_FROZEN_BEFORE_TRUTH",
        "fair_pretruth_sha256": FAIR_PRETRUTH_SHA256,
        "geometry_sha256": sha(a.geometry),
        "quality_source_sha256": QUALITY_SHA256,
        "v8_result_sha256": V8_SHA256,
        "years": list(YEARS),
        "blind_exclusion": list(BLIND),
        "fixed4_neighbor_count": NEAREST_OTHERS,
        "fixed4_anchor_multiplicity": ANCHOR_MULTIPLICITY,
        "distance_rule": "exact_frozen_fixed4_anchor_distance_to_all_other_same_envelope_same_year_events",
        "quartet_rule": "anchor_plus_three_nearest_stable_by_sorted_event_id",
        "core_rule": "union_of_events_in_quartets_selected_by_at_least_two_distinct_anchors",
        "subsets": subset_rows,
        "overall_summary": summarize(all_core_rows),
        "parent_discovery_membership_changed": False,
        "parent_rank_changed": False,
        "fixed4_calibration_or_score_threshold_used": False,
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_scientific_access": False,
        "external_survey_scientific_access": False,
        "post_result_parameter_search": False,
    }
    a.output.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": "PASS_M2D_FIXED4_CONSENSUS_CORE_V1_PRETRUTH", "sha256": sha(a.output), "overall": payload["overall_summary"]}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
