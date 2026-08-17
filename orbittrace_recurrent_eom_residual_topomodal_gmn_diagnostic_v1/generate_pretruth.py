#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
STRUCTURAL_RESULT_SHA256 = "e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497"
COARSE_D = 128
FINE_D = 1024
BUCKETS = (0, 1, 2, 3)


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def universe_hash(ids: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()


def family_rows(families: list[frozenset[str]], prefix: str, member_hash: Any) -> list[dict[str, Any]]:
    rows = []
    for members in families:
        rows.append({
            "family_id": f"{prefix}-{member_hash(members)}",
            "family_hash": member_hash(members),
            "member_count": len(members),
            "event_ids": sorted(members),
        })
    rows.sort(key=lambda r: (-int(r["member_count"]), str(r["family_hash"])))
    return rows


def dump(path: Path, obj: Any) -> str:
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hierarchy-runner", type=Path, required=True)
    ap.add_argument("--parent-runner", type=Path, required=True)
    ap.add_argument("--quality-source", type=Path, required=True)
    ap.add_argument("--support-source-parts", type=Path, required=True)
    ap.add_argument("--candidate-payload", type=Path, required=True)
    ap.add_argument("--baseline-payload", type=Path, required=True)
    ap.add_argument("--scorer-parts", type=Path, required=True)
    ap.add_argument("--v8-result-json", type=Path, required=True)
    ap.add_argument("--structural-result-json", type=Path, required=True)
    ap.add_argument("--protocol", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha(a.quality_source) == QUALITY_SHA256, "frozen GMN runtime utility changed")
    req(sha(a.v8_result_json) == V8_RESULT_SHA256, "frozen GMN support artifact changed")
    req(sha(a.structural_result_json) == STRUCTURAL_RESULT_SHA256, "frozen hierarchy-scale result changed")

    hier = load_module(a.hierarchy_runner, "residual_topomodal_hierarchy")
    parent = load_module(a.parent_runner, "residual_topomodal_parent")
    req(tuple(hier.YEARS) == YEARS and tuple(hier.BLIND) == BLIND, "hierarchy constants changed")
    req(tuple(parent.YEARS) == YEARS and tuple(parent.BLIND) == BLIND, "parent constants changed")
    req(int(hier.COARSE_D) == COARSE_D and int(hier.FINE_D) == FINE_D and tuple(hier.BUCKETS) == BUCKETS, "sparse panels changed")
    req(int(hier.MIN_SUPPORT) == 4 and float(hier.RADIUS) == 1.0, "TopoModal support/radius changed")

    structural = json.loads(a.structural_result_json.read_text())
    req(structural["schema"] == "ORBITTRACE_TOPOMODAL_HIERARCHY_SCALE_V1", "wrong structural schema")
    expected = {(int(r["denominator"]), int(r["bucket"])): r for r in structural["fits"]}
    req(set(expected) == {(d, b) for d in (COARSE_D, FINE_D) for b in BUCKETS}, "structural panels changed")

    qmod = load_module(a.quality_source, "residual_topomodal_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-recurrent-eom-residual-topomodal-gmn-diagnostic-v1-pretruth"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_unused, sources = support.parse_catalogue(base)
    del hidden_unused
    req(sorted(scan) == list(YEARS), f"wrong GMN years {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        norm = [parent.normalize_event(row, year) for row in raw]
        req(len(norm) == len(raw), f"normalization count changed {year}")
        events.extend(norm)
    req(len(events) == 738682, f"pooled event count changed {len(events)}")
    req(len({str(e["id"]) for e in events}) == len(events), "duplicate event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected event reached pretruth")

    Xfull = parent.geo_matrix(events)
    years_full = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    ids_full = [str(e["id"]) for e in events]
    hashes = np.asarray([hier.event_hash_u64(eid) for eid in ids_full], dtype=np.uint64)

    panels = []
    activation = True
    for d in (COARSE_D, FINE_D):
        for b in BUCKETS:
            ix = hier.selected_indices(hashes, d, b)
            sub_events = [events[int(i)] for i in ix]
            X = np.asarray(Xfull[ix], dtype=float)
            yrs = np.asarray(years_full[ix], dtype=np.int64)
            ids = [ids_full[int(i)] for i in ix]
            exp = expected[(d, b)]
            req(len(ids) == int(exp["events_total"]), f"panel count drift d{d}b{b}")
            req({str(y): int(np.sum(yrs == y)) for y in YEARS} == {str(k): int(v) for k, v in exp["events_by_year"].items()}, f"annual panel count drift d{d}b{b}")
            req(all(np.any(yrs == y) for y in YEARS), f"panel lost year d{d}b{b}")

            recurrent, rsum = hier.recurrent_candidates(parent, X, yrs, ids)
            req(int(rsum["candidate_count"]) == int(exp["recurrent_eom"]["candidate_count"]), f"Recurrent-EOM candidate count drift d{d}b{b}")
            req(rsum["candidate_rows"] == exp["recurrent_eom"]["candidate_rows"], f"Recurrent-EOM candidate identity drift d{d}b{b}")
            accepted = frozenset().union(*recurrent) if recurrent else frozenset()
            universe = frozenset(ids)
            req(accepted.issubset(universe), "accepted set leaves panel universe")
            residual_ids = universe.difference(accepted)
            req(accepted.isdisjoint(residual_ids) and accepted.union(residual_ids) == universe, "residual partition failed")
            residual_events = [e for e in sub_events if str(e["id"]) in residual_ids]

            topo: list[frozenset[str]] = []
            tsum: dict[str, Any]
            if len(residual_events) >= 4:
                topo, tsum = hier.topomodal_candidates(residual_events)
            else:
                tsum = {"candidate_count": 0, "reason": "residual_below_min_support"}

            rrows = family_rows(recurrent, "REOM", hier.member_hash)
            trows = family_rows(topo, "RESIDTM", hier.member_hash)
            panel_ok = len(recurrent) >= 1 and len(residual_events) >= 4 and len(topo) >= 1
            activation = activation and panel_ok
            row = {
                "denominator": d,
                "bucket": b,
                "events_total": len(ids),
                "events_by_year": {str(y): int(np.sum(yrs == y)) for y in YEARS},
                "event_universe_sha256": universe_hash(ids),
                "recurrent_candidate_count": len(recurrent),
                "recurrent_candidates": rrows,
                "accepted_event_count": len(accepted),
                "accepted_event_sha256": universe_hash(list(accepted)),
                "residual_event_count": len(residual_ids),
                "residual_event_sha256": universe_hash(list(residual_ids)),
                "residual_topomodal_candidate_count": len(topo),
                "residual_topomodal_candidates": trows,
                "residual_topomodal_summary": tsum,
                "structural_activation_pass": bool(panel_ok),
            }
            panels.append(row)
            print(f"[residual-gmn-pretruth] d={d} b={b} U={len(ids)} reom={len(recurrent)} A={len(accepted)} R={len(residual_ids)} tm={len(topo)} pass={panel_ok}", flush=True)

    verdict = "PASS_PRETRUTH_RESIDUAL_CONSTRUCTION" if activation else "FAIL_PRETRUTH_RESIDUAL_CONSTRUCTION"
    out = {
        "schema": "ORBITTRACE_RECURRENT_EOM_RESIDUAL_TOPOMODAL_GMN_DIAGNOSTIC_V1_PRETRUTH",
        "scientific_role": "TARGET_EXCLUDED_GMN_PRETRUTH_CANDIDATE_EXISTENCE_DIAGNOSTIC",
        "verdict": verdict,
        "structural_activation_pass": bool(activation),
        "panels": panels,
        "protocol_sha256": sha(a.protocol),
        "structural_result_sha256": sha(a.structural_result_json),
        "blind_exclusion": list(BLIND),
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    digest = dump(a.output / "PRETRUTH.json", out)
    print(json.dumps({"verdict": verdict, "pretruth_sha256": digest, "panels": [{k: p[k] for k in ("denominator", "bucket", "recurrent_candidate_count", "accepted_event_count", "residual_event_count", "residual_topomodal_candidate_count", "structural_activation_pass")} for p in panels]}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
