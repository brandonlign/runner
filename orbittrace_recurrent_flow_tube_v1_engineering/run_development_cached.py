#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np

FROZEN_SOURCE_SHA = "a5d5371f0c30a9c57ee4d8756ea41f454cd86301"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_frozen(path: Path) -> Any:
    if sha(path) != FROZEN_SOURCE_SHA:
        raise RuntimeError("frozen RFT v1 source changed")
    spec = importlib.util.spec_from_file_location("rft_v1_frozen", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_cache(mod: Any, events: list[dict[str, Any]]) -> tuple[dict[int, list[Any]], dict[tuple[int, bool], list[Any]]]:
    """Compute each perturbation and atomization once, then both ownership views.

    This intentionally calls the frozen scientific functions unchanged. Only reuse is new.
    """
    atom_cache: dict[int, list[Any]] = {}
    tube_cache: dict[tuple[int, bool], list[Any]] = {}
    for replica in range(0, mod.PERTURB_REPLICAS + 1):
        replica_events = events if replica == 0 else mod.perturb(events, replica)
        atom_list = mod.atoms(replica_events)
        atom_cache[replica] = atom_list
        tube_cache[(replica, True)] = mod.build_tubes(atom_list, ownership=True)
        tube_cache[(replica, False)] = mod.build_tubes(atom_list, ownership=False)
    return atom_cache, tube_cache


def generate_cached(
    mod: Any,
    events: list[dict[str, Any]],
    tube_cache: dict[tuple[int, bool], list[Any]],
    *,
    ownership: bool,
    do_trim: bool,
    do_persistence: bool,
) -> list[dict[str, Any]]:
    """Exact frozen generate() semantics using precomputed tube objects."""
    lookup = {e["id"]: e for e in events}
    base_tubes = tube_cache[(0, ownership)]
    replica_sets: list[list[set[str]]] = []
    if do_persistence:
        for replica in range(1, mod.PERTURB_REPLICAS + 1):
            replica_sets.append([set(t.members) for t in tube_cache[(replica, ownership)]])

    out: list[dict[str, Any]] = []
    for t in base_tubes:
        bset = set(t.members)
        if do_persistence:
            survive = 0
            for rsets in replica_sets:
                best = max((mod.jaccard(bset, s) for s in rsets), default=0.0)
                survive += int(best >= mod.PERSIST_JACCARD)
            persistence = survive / mod.PERTURB_REPLICAS
            if persistence + 1e-12 < mod.PERSIST_MIN:
                continue
        else:
            persistence = 1.0

        members, med_res = mod.fit_trim(t, lookup, do_trim=do_trim)
        if len(members) < mod.MIN_EVENTS:
            continue
        med_trans = float(np.median(t.transition_costs)) if t.transition_costs else 0.0
        score = persistence * np.log1p(len(members)) * np.log1p(t.strata) / (1.0 + med_trans + med_res)
        cid = hashlib.sha256(("RFT1|" + "|".join(members)).encode()).hexdigest()[:20]
        out.append({
            "family_id": cid,
            "event_ids": list(members),
            "score": float(score),
            "persistence": float(persistence),
            "strata": int(t.strata),
            "span": float(t.span),
            "median_transition_cost": med_trans,
            "median_trajectory_residual": float(med_res),
            "atom_ids": list(t.atom_ids),
        })
    out.sort(key=lambda f: (-f["score"], -f["persistence"], -len(f["event_ids"]), f["family_id"]))
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--frozen-source", type=Path, required=True)
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--reference-output-dir", type=Path)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    mod = load_frozen(a.frozen_source)
    mod.req(mod.sha(a.quality_source) == mod.QUALITY_SHA, "#839 utility source changed")
    mod.req(mod.sha(a.v8_result_json) == mod.V8_RESULT_SHA, "frozen GMN runtime support artifact changed")
    qmod = mod.load_module(a.quality_source, "rft_cached_frozen_839_utility")
    qmod.v1.mult.YEARS = mod.YEARS
    qmod.v1.mult.MONTH_KEYS = mod.MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = mod.YEARS
    support.MONTH_KEYS = mod.MONTH_KEYS
    support.CORPUS = "orbittrace-recurrent-flow-tube-v1-development-2022-only"
    support.RANKING_VARIANTS = ("persistence",)
    mod.req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == mod.BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden, sources = support.parse_catalogue(base)
    mod.req(sorted(scan) == [mod.YEAR], f"GMN development runtime accessed wrong years: {sorted(scan)}")
    mod.req([x["key"] for x in sources] == list(mod.MONTH_KEYS), "GMN 2022 source list changed")

    raw = list(scan[mod.YEAR])
    events = [mod.normalize_event(row) for row in raw]
    mod.req(len(events) == len(raw), "event normalization changed event count")
    mod.req(all(not (mod.BLIND[0] <= e["sol"] <= mod.BLIND[1]) for e in events), "protected region survived parser")
    mod.req(all(str(e["id"]).startswith(str(mod.YEAR)) for e in events), "non-2022 event reached development")
    mod.req(all(str(eid).startswith(str(mod.YEAR)) for eid in hidden), "non-2022 label reached development")

    atom_cache, tube_cache = build_cache(mod, events)

    fams = generate_cached(mod, events, tube_cache, ownership=True, do_trim=True, do_persistence=True)
    m = mod.metrics(fams, hidden)
    ab_no_owner = mod.metrics(generate_cached(mod, events, tube_cache, ownership=False, do_trim=True, do_persistence=True), hidden)
    ab_no_persist = mod.metrics(generate_cached(mod, events, tube_cache, ownership=True, do_trim=True, do_persistence=False), hidden)
    ab_no_trim = mod.metrics(generate_cached(mod, events, tube_cache, ownership=True, do_trim=False, do_persistence=True), hidden)

    persistence_top = [float(f["persistence"]) for f in fams[:100]]
    high_persist_share = float(np.mean([x >= 0.75 for x in persistence_top])) if persistence_top else 0.0
    viable = bool(
        int(m["qualified_matches"]) >= 120
        and int(m["recovered_at_100"]) >= 55
        and float(m["top100_dominant_precision"]) >= 0.60
        and float(m["fragmentation_median_top500"]) <= 3.0
        and high_persist_share >= 0.75
    )
    verdict = "PASS_RFT_V1_GMN2022_DEVELOPMENT_VIABILITY" if viable else "FAIL_RFT_V1_GMN2022_DEVELOPMENT_VIABILITY"
    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_DEVELOPMENT_ONLY",
        "events": len(events),
        "retained_candidates": len(fams),
        "metrics": m,
        "top100_persistence_ge_0p75_share": high_persist_share,
        "ablations": {
            "no_path_ownership": ab_no_owner,
            "no_perturbation_persistence": ab_no_persist,
            "no_trajectory_trim": ab_no_trim,
        },
        "frozen_constants": {
            "bin_width_deg": mod.BIN_WIDTH, "knn": mod.KNN, "min_atom": mod.MIN_ATOM,
            "min_strata": mod.MIN_STRATA, "min_span_deg": mod.MIN_SPAN, "min_events": mod.MIN_EVENTS,
            "perturb_replicas": mod.PERTURB_REPLICAS, "perturb_radiant_sigma_deg": mod.PERTURB_RAD_DEG,
            "perturb_speed_sigma_frac": mod.PERTURB_SPEED_FRAC, "persistence_jaccard": mod.PERSIST_JACCARD,
            "persistence_min": mod.PERSIST_MIN, "trajectory_trim": mod.TRAJECTORY_TRIM,
        },
        "blind_exclusion": list(mod.BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "sonotaco_2013_2014_access": False,
        "gmn_2023_access": False,
        "candidate_order_sha256": hashlib.sha256("\n".join(f["family_id"] for f in fams).encode()).hexdigest(),
    }

    result_path = a.output / "RFT_V1_GMN2022_DEVELOPMENT.json"
    candidates_path = a.output / "rft_v1_gmn2022_candidates.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    candidates_path.write_text(json.dumps(fams, indent=2, sort_keys=True, allow_nan=False) + "\n")

    report = {
        "role": "ENGINEERING_EQUIVALENCE_ONLY",
        "frozen_source_sha256": FROZEN_SOURCE_SHA,
        "scientific_changes": False,
        "gmn_2023_access": False,
        "sonotaco_access": False,
        "original_atom_reconstructions": 52,
        "cached_atom_reconstructions": mod.PERTURB_REPLICAS + 1,
        "original_tube_reconstructions": 52,
        "cached_tube_reconstructions": 2 * (mod.PERTURB_REPLICAS + 1),
        "cache_replica_count": mod.PERTURB_REPLICAS + 1,
        "result_sha256": sha(result_path),
        "candidates_sha256": sha(candidates_path),
    }

    if a.reference_output_dir is not None:
        ref_result = a.reference_output_dir / result_path.name
        ref_candidates = a.reference_output_dir / candidates_path.name
        mod.req(ref_result.exists() and ref_candidates.exists(), "reference output files missing")
        report["reference_result_sha256"] = sha(ref_result)
        report["reference_candidates_sha256"] = sha(ref_candidates)
        report["result_byte_identical"] = report["result_sha256"] == report["reference_result_sha256"]
        report["candidates_byte_identical"] = report["candidates_sha256"] == report["reference_candidates_sha256"]
        mod.req(bool(report["result_byte_identical"]), "cached result differs from frozen original")
        mod.req(bool(report["candidates_byte_identical"]), "cached candidates differ from frozen original")

    (a.output / "ENGINEERING_CACHE_REPORT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verdict": verdict, "events": len(events), "candidates": len(fams), "engineering": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
