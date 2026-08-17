#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
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


def universe_hash(ids: list[str] | set[str]) -> str:
    return hashlib.sha256("\n".join(sorted(map(str, ids))).encode()).hexdigest()


def dump(path: Path, obj: Any) -> str:
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def eligible_labels(hidden: dict[str, str], annual_ids: set[str]) -> dict[str, int]:
    counts = Counter(str(hidden.get(eid, "SPORADIC")) for eid in annual_ids)
    return {label: int(n) for label, n in counts.items() if label != "SPORADIC" and int(n) >= 4}


def pair_metrics(family: dict[str, Any], annual_ids: set[str], truth_ids: set[str]) -> tuple[float, float, float]:
    members = set(map(str, family["event_ids"])).intersection(annual_ids)
    if not members or not truth_ids:
        return 0.0, 0.0, 0.0
    ov = len(members.intersection(truth_ids))
    if ov <= 0:
        return 0.0, 0.0, 0.0
    precision = ov / len(members)
    recall = ov / len(truth_ids)
    f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
    return float(f1), float(precision), float(recall)


def classify_label(label: str, total: int, hidden: dict[str, str], annual_ids: set[str], recurrent: list[dict[str, Any]], residual_tm: list[dict[str, Any]]) -> dict[str, Any]:
    truth_ids = {eid for eid in annual_ids if str(hidden.get(eid, "SPORADIC")) == label}
    req(len(truth_ids) == int(total), f"truth count mismatch {label}")

    best_f1 = 0.0
    recall_rows: list[tuple[float, float, str]] = []
    for fam in recurrent:
        f1, p, r = pair_metrics(fam, annual_ids, truth_ids)
        best_f1 = max(best_f1, f1)
        recall_rows.append((r, p, str(fam["family_hash"])))
    best_recall, precision_at_recall, recall_family = max(recall_rows, key=lambda x: (x[0], x[1], x[2])) if recall_rows else (0.0, 0.0, "")

    if best_f1 > 0.5:
        state = "RECOVERABLE_IN_RECURRENT_UNIVERSE"
    elif best_recall > 0.5 and precision_at_recall <= 0.5:
        state = "MEMBERSHIP_CONTAMINATION"
    else:
        state = "CANDIDATE_GENERATION_FAILURE"

    best_tm_f1 = 0.0
    best_tm_family = None
    for fam in residual_tm:
        f1, _p, _r = pair_metrics(fam, annual_ids, truth_ids)
        if f1 > best_tm_f1:
            best_tm_f1 = f1
            best_tm_family = str(fam["family_hash"])

    return {
        "label": label,
        "truth_member_count": int(total),
        "recurrent_state": state,
        "best_recurrent_f1": float(best_f1),
        "best_recurrent_recall": float(best_recall),
        "best_recurrent_precision_at_recall": float(precision_at_recall),
        "best_recurrent_recall_family_hash": recall_family,
        "best_residual_topomodal_f1": float(best_tm_f1),
        "best_residual_topomodal_family_hash": best_tm_family,
        "residual_topomodal_complementary_recovery": bool(state == "CANDIDATE_GENERATION_FAILURE" and best_tm_f1 > 0.5),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pretruth", type=Path, required=True)
    ap.add_argument("--hierarchy-runner", type=Path, required=True)
    ap.add_argument("--parent-runner", type=Path, required=True)
    ap.add_argument("--quality-source", type=Path, required=True)
    ap.add_argument("--support-source-parts", type=Path, required=True)
    ap.add_argument("--candidate-payload", type=Path, required=True)
    ap.add_argument("--baseline-payload", type=Path, required=True)
    ap.add_argument("--scorer-parts", type=Path, required=True)
    ap.add_argument("--v8-result-json", type=Path, required=True)
    ap.add_argument("--protocol", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha(a.quality_source) == QUALITY_SHA256, "frozen GMN runtime utility changed")
    req(sha(a.v8_result_json) == V8_RESULT_SHA256, "frozen GMN support artifact changed")
    pretruth_sha = sha(a.pretruth)
    pre = json.loads(a.pretruth.read_text())
    req(pre["schema"] == "ORBITTRACE_RECURRENT_EOM_RESIDUAL_TOPOMODAL_GMN_DIAGNOSTIC_V1_PRETRUTH", "wrong pretruth schema")
    req(pre["verdict"] == "PASS_PRETRUTH_RESIDUAL_CONSTRUCTION" and pre["structural_activation_pass"] is True, "truth opened after failed pretruth")
    req(pre["protocol_sha256"] == sha(a.protocol), "protocol changed after pretruth")
    req(pre["shower_truth_used"] is False, "truth reached pretruth")
    req(pre["target_information_access"] is False and pre["target_region_events_accessed"] is False, "target access in pretruth")
    req(pre["sonotaco_2013_2014_access"] is False and pre["amos_scientific_access"] is False and pre["maarsy_scientific_access"] is False and pre["dms_scientific_access"] is False, "forbidden access in pretruth")

    hier = load_module(a.hierarchy_runner, "residual_eval_hierarchy")
    parent = load_module(a.parent_runner, "residual_eval_parent")
    qmod = load_module(a.quality_source, "residual_eval_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-recurrent-eom-residual-topomodal-gmn-diagnostic-v1-evaluation"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden, sources = support.parse_catalogue(base)
    req(isinstance(hidden, dict) and hidden, "hidden development labels unavailable")
    req(sorted(scan) == list(YEARS), "wrong GMN years")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        events.extend(parent.normalize_event(row, year) for row in list(scan[year]))
    req(len(events) == 738682, "pooled event count changed")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected event reached evaluation")
    ids_full = [str(e["id"]) for e in events]
    years_full = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    hashes = np.asarray([hier.event_hash_u64(eid) for eid in ids_full], dtype=np.uint64)

    pmap = {(int(p["denominator"]), int(p["bucket"])): p for p in pre["panels"]}
    req(set(pmap) == {(d, b) for d in (COARSE_D, FINE_D) for b in BUCKETS}, "pretruth panels changed")
    panel_years = []
    aggregate: dict[tuple[int, int], dict[str, int]] = {(d, y): {"candidate_generation_failures": 0, "complementary_recoveries": 0} for d in (COARSE_D, FINE_D) for y in YEARS}

    for d in (COARSE_D, FINE_D):
        for b in BUCKETS:
            p = pmap[(d, b)]
            ix = hier.selected_indices(hashes, d, b)
            ids = [ids_full[int(i)] for i in ix]
            yrs = np.asarray(years_full[ix], dtype=np.int64)
            req(len(ids) == int(p["events_total"]), f"panel count changed d{d}b{b}")
            req(universe_hash(ids) == p["event_universe_sha256"], f"panel universe changed d{d}b{b}")
            recurrent = list(p["recurrent_candidates"])
            residual_tm = list(p["residual_topomodal_candidates"])
            req(len(recurrent) == int(p["recurrent_candidate_count"]) and len(residual_tm) == int(p["residual_topomodal_candidate_count"]), "candidate count changed")

            for year in YEARS:
                annual_ids = {ids[int(i)] for i in np.flatnonzero(yrs == year)}
                eligible = eligible_labels(hidden, annual_ids)
                rows = [classify_label(label, total, hidden, annual_ids, recurrent, residual_tm) for label, total in sorted(eligible.items())]
                states = Counter(r["recurrent_state"] for r in rows)
                cgf = [r for r in rows if r["recurrent_state"] == "CANDIDATE_GENERATION_FAILURE"]
                recovered = [r for r in cgf if r["residual_topomodal_complementary_recovery"]]
                vals = np.asarray([float(r["best_residual_topomodal_f1"]) for r in cgf], dtype=float)
                aggregate[(d, year)]["candidate_generation_failures"] += len(cgf)
                aggregate[(d, year)]["complementary_recoveries"] += len(recovered)
                panel_years.append({
                    "denominator": d,
                    "bucket": b,
                    "year": year,
                    "eligible_shower_count": len(eligible),
                    "recurrent_recoverable_universe_count": int(states.get("RECOVERABLE_IN_RECURRENT_UNIVERSE", 0)),
                    "membership_contamination_count": int(states.get("MEMBERSHIP_CONTAMINATION", 0)),
                    "candidate_generation_failure_count": len(cgf),
                    "residual_topomodal_complementary_recovery_count": len(recovered),
                    "residual_topomodal_complementary_recovery_fraction": float(len(recovered) / len(cgf)) if cgf else 0.0,
                    "candidate_generation_failure_best_residual_topomodal_f1_median": float(np.median(vals)) if len(vals) else 0.0,
                    "candidate_generation_failure_best_residual_topomodal_f1_max": float(np.max(vals)) if len(vals) else 0.0,
                    "recurrent_candidate_count": int(p["recurrent_candidate_count"]),
                    "accepted_event_count": int(p["accepted_event_count"]),
                    "residual_event_count": int(p["residual_event_count"]),
                    "residual_topomodal_candidate_count": int(p["residual_topomodal_candidate_count"]),
                    "label_diagnostics": rows,
                })

    scale_year = []
    gates = {}
    for d in (COARSE_D, FINE_D):
        for year in YEARS:
            x = aggregate[(d, year)]
            gate = int(x["complementary_recoveries"]) >= 1
            gates[f"d{d}_year{year}_at_least_one_complementary_recovery"] = bool(gate)
            scale_year.append({"denominator": d, "year": year, **x, "transfer_gate": bool(gate)})

    verdict = "PASS_RECURRENT_EOM_RESIDUAL_TOPOMODAL_GMN_DIAGNOSTIC_V1" if all(gates.values()) else "FAIL_RECURRENT_EOM_RESIDUAL_TOPOMODAL_GMN_DIAGNOSTIC_V1"
    out = {
        "schema": "ORBITTRACE_RECURRENT_EOM_RESIDUAL_TOPOMODAL_GMN_DIAGNOSTIC_V1_RESULT",
        "scientific_role": "TARGET_EXCLUDED_GMN_CANDIDATE_EXISTENCE_TRANSFER_DIAGNOSTIC",
        "verdict": verdict,
        "pretruth_sha256": pretruth_sha,
        "panel_years": panel_years,
        "scale_year_aggregates": scale_year,
        "gates": gates,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "ranking_or_catalogue_promotion_performed": False,
        "post_result_parameter_search": False,
    }
    digest = dump(a.output / "RESULT.json", out)
    print(json.dumps({"verdict": verdict, "result_sha256": digest, "gates": gates, "scale_year_aggregates": scale_year}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
