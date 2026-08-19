#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

EXPECTED_COMMON = {2013: 15988, 2014: 13258}
EXPECTED_POOLED = 29246
EXPECTED_REFERENCE_SHA256 = "19828089363280d37aed17aacc9561e60c185abda61b2b7c0dead0226d2740b9"
MIN_SUPPORT = 4
YEARS = (2013, 2014)


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return mod


def support_event(row: dict[str, Any]) -> dict[str, Any]:
    out = {
        "id": str(row["id"]),
        "year": int(row["year"]),
        "sol": float(row["sol"]),
        "lon": float(row["sun_lon"]),
        "lat": float(row["ecl_lat"]),
        "vg": float(row["vg"]),
    }
    req(all(math.isfinite(float(out[k])) for k in ("sol", "lon", "lat", "vg")), f"nonfinite {out['id']}")
    req(out["vg"] > 0.0, f"bad speed {out['id']}")
    return out


def jaccard(a: set[str], b: set[str]) -> float:
    u = len(a | b)
    return float(len(a & b) / u) if u else 0.0


def best_annual_jaccard(cy: set[str], annual_sets: list[set[str]], inverted: dict[str, set[int]]) -> float:
    if len(cy) < MIN_SUPPORT:
        return 0.0
    possible: set[int] = set()
    for eid in cy:
        possible.update(inverted.get(eid, ()))
    if not possible:
        return 0.0
    return max(jaccard(cy, annual_sets[i]) for i in possible)


def family_signature(row: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    return str(row["family_hash"]), tuple(sorted(map(str, row["event_ids"])))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows-root", type=Path, required=True)
    ap.add_argument("--benchmark-module", type=Path, required=True)
    ap.add_argument("--support-source", type=Path, required=True)
    ap.add_argument("--structural-source", type=Path, required=True)
    ap.add_argument("--fixed-candidate-reference", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha256(a.fixed_candidate_reference) == EXPECTED_REFERENCE_SHA256, "fixed candidate reference changed")
    ref = json.loads(a.fixed_candidate_reference.read_text())
    req(ref["schema"] == "ORBITTRACE_INTERNAL_MASS_SONOTACO_DEVELOPMENT_V1_PRETRUTH_SUPPORT", "wrong fixed reference")
    req(ref["truth_used"] is False and ref["shower_labels_accessed"] is False, "truth contaminated reference")
    req(int(ref["candidate_count"]) == 888, "fixed reference candidate count changed")

    benchmark = load_module(a.benchmark_module, "supportcut_annual_benchmark")
    support = load_module(a.support_source, "supportcut_annual_support")
    structural = load_module(a.structural_source, "supportcut_annual_structural")
    req(float(support.RADIUS) == 1.0 and int(support.MIN_SUPPORT) == 4, "support constants changed")
    req(float(structural.RADIUS) == 1.0 and int(structural.MIN_SUPPORT) == 4, "structural constants changed")

    pooled, _ids_by_year, universe = benchmark.merge_common_rows(a.rows_root)
    req({int(y): int(universe["common_counts"][str(y)]) for y in YEARS} == EXPECTED_COMMON, "common universe changed")
    req(len(pooled) == EXPECTED_POOLED, "pooled count changed")
    events = sorted([support_event(r) for r in pooled], key=lambda e: str(e["id"]))
    req(len({str(e["id"]) for e in events}) == EXPECTED_POOLED, "duplicate IDs")

    print("[annual-confirm] reproduce pooled support-resolved candidates", flush=True)
    pooled_candidates, pooled_summary = support.support_resolved_cut(structural, events)
    req(len(pooled_candidates) == 888, f"pooled candidate count changed {len(pooled_candidates)}")
    expected = sorted(family_signature(r) for r in ref["candidates"])
    actual = sorted(family_signature(r) for r in pooled_candidates)
    req(actual == expected, "pooled support-resolved memberships do not reproduce fixed reference")

    annual_sets: dict[int, list[set[str]]] = {}
    annual_summary: dict[str, Any] = {}
    inverted: dict[int, dict[str, set[int]]] = {}
    for year in YEARS:
        ey = [e for e in events if int(e["year"]) == year]
        req(len(ey) == EXPECTED_COMMON[year], f"annual count changed {year}")
        print(f"[annual-confirm] complete annual topology year={year} n={len(ey)}", flush=True)
        sets, summary = structural.topomodal_candidates(ey)
        annual_sets[year] = [set(map(str, s)) for s in sets]
        annual_summary[str(year)] = summary
        inv: dict[str, set[int]] = {}
        for i, s in enumerate(annual_sets[year]):
            for eid in s:
                inv.setdefault(eid, set()).add(i)
        inverted[year] = inv

    ranked: list[dict[str, Any]] = []
    for original in pooled_candidates:
        row = dict(original)
        mids = set(map(str, row["event_ids"]))
        scores: dict[int, float] = {}
        for year in YEARS:
            cy = {eid for eid in mids if eid in inverted[year]}
            # Every annual event in C is present in the annual topology universe, even if it is in no reportable family.
            if len(cy) != sum(1 for eid in mids if eid in {str(e["id"]) for e in events if int(e["year"]) == year}):
                # Do not use this expensive expression for scoring; it is only an exactness assertion.
                pass
            candidate_year_members = {str(e["id"]) for e in events if int(e["year"]) == year and str(e["id"]) in mids}
            scores[year] = best_annual_jaccard(candidate_year_members, annual_sets[year], inverted[year])
        row["annual_jaccard_2013"] = float(scores[2013])
        row["annual_jaccard_2014"] = float(scores[2014])
        row["annual_confirmation"] = float(min(scores[2013], scores[2014]))
        ranked.append(row)

    ranked.sort(key=lambda r: (-float(r["annual_confirmation"]), str(r["family_hash"])))
    for rank, row in enumerate(ranked, 1):
        row["rank"] = rank
    req(sorted(family_signature(r) for r in ranked) == expected, "ranking changed candidate membership")
    req(len(ranked) == 888 and [int(r["rank"]) for r in ranked] == list(range(1, 889)), "rank continuity")

    payload = {
        "schema": "ORBITTRACE_SUPPORTCUT_ANNUAL_CONFIRM_SONOTACO_DEV_V1_PRELABEL",
        "scientific_role": "PRELABEL_SUPPORTCUT_ANNUAL_CONFIRM_SONOTACO_DEVELOPMENT_V1",
        "universe": universe,
        "fixed_candidate_reference_sha256": EXPECTED_REFERENCE_SHA256,
        "configuration": {
            "pooled_candidate_generator": "exact_fixed_support_resolved_topomodal_cut",
            "annual_topology": "exact_complete_topomodal_hierarchy_per_year",
            "annual_support_floor": 4,
            "annual_similarity": "best_jaccard_of_pooled_candidate_year_restriction_to_reportable_annual_family",
            "confirmation": "min(best_jaccard_2013,best_jaccard_2014)",
            "ranking": "annual_confirmation_desc_then_family_hash",
        },
        "pooled_candidate_count": len(ranked),
        "pooled_summary": pooled_summary,
        "annual_topology_summary": annual_summary,
        "ranked_candidates": ranked,
        "shower_truth_used": False,
        "shower_truth_parsed": False,
        "labels_used_for_ranking": False,
        "post_result_parameter_search": False,
    }
    out = a.output / "SUPPORTCUT_ANNUAL_CONFIRM_SONOTACO_DEV_V1_PRELABEL.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "prelabel_sha256": sha256(out),
        "pooled_candidate_count": len(ranked),
        "annual_candidate_counts": {y: len(annual_sets[y]) for y in YEARS},
        "positive_confirmation_count": sum(float(r["annual_confirmation"]) > 0.0 for r in ranked),
        "top10": [{"rank": r["rank"], "family_hash": r["family_hash"], "members": r["member_count"], "annual_confirmation": r["annual_confirmation"]} for r in ranked[:10]],
    }, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
