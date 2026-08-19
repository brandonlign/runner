#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
DENOMS = (128, 1024)
BUCKETS = (0, 1, 2, 3)
FAIR_PRETRUTH_SHA256 = "8b0f4629659c1bfd750747303ad04ff67355adf66d4dbe474ce7fba788f5bae5"
INTERNAL_PRE_SHA256 = "7b1ddfcd32cd0b52321e3b3dfc614a88dd9b973f947c1d4d0de74fddf26b59cd"
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
EXPECTED_PARENT = {
    "sugar2017": {
        "mean_macro_f1": 0.5608353827866924,
        "mean_macro_precision": 0.546515915964596,
        "mean_macro_recall": 0.6006608502900602,
        "total_recovered_f1_gt_05": 164,
        "total_recovered_f1_gt_08": 112,
    },
    "hdbscan2025": {
        "mean_macro_f1": 0.03799360813979141,
        "mean_macro_precision": 0.034748036963226744,
        "mean_macro_recall": 0.04201631001380206,
        "total_recovered_f1_gt_05": 28,
        "total_recovered_f1_gt_08": 28,
    },
}
MIN_PAIRED = 20
MIN_NONEMPTY_FRACTION = 0.75
MIN_MEAN_PRECISION = 0.80
MIN_F1_RETENTION = 0.75
MIN_PRECISION_NONREGRESSION_FRACTION = 0.50


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def matrices(cands: list[dict[str, Any]], hidden: dict[str, str], annual: set[str]) -> dict[str, Any]:
    counts = Counter(v for k, v in hidden.items() if k in annual and v != "SPORADIC")
    labels = sorted(k for k, n in counts.items() if n >= 4)
    L, C = len(labels), len(cands)
    f = np.zeros((L, C), dtype=float)
    p = np.zeros_like(f)
    r = np.zeros_like(f)
    nmem = np.zeros(C, dtype=int)
    label_ix = {lab: i for i, lab in enumerate(labels)}
    for j, cand in enumerate(cands):
        ids = [str(x) for x in cand["event_ids"] if str(x) in annual]
        n = len(ids)
        nmem[j] = n
        if n == 0:
            continue
        cc = Counter(hidden.get(eid, "SPORADIC") for eid in ids)
        for lab, ov in cc.items():
            if lab not in label_ix:
                continue
            i = label_ix[lab]
            pp = ov / n
            rr = ov / counts[lab]
            ff = 2.0 * pp * rr / (pp + rr) if pp + rr else 0.0
            p[i, j], r[i, j], f[i, j] = pp, rr, ff
    return {"labels": labels, "f": f, "p": p, "r": r, "nmem": nmem}


def assigned(m: dict[str, Any]) -> dict[str, Any]:
    f, p, r = m["f"], m["p"], m["r"]
    L, C = f.shape
    af, ap, ar = np.zeros(L), np.zeros(L), np.zeros(L)
    ai = np.full(L, -1, dtype=int)
    if C:
        ri, cj = linear_sum_assignment(f, maximize=True)
        for i, j in zip(ri, cj):
            af[i], ap[i], ar[i], ai[i] = f[i, j], p[i, j], r[i, j], int(j)
    return {
        "eligible_showers": L,
        "candidate_count": C,
        "macro_f1": float(np.mean(af)) if L else 0.0,
        "macro_precision": float(np.mean(ap)) if L else 0.0,
        "macro_recall": float(np.mean(ar)) if L else 0.0,
        "recovered_f1_gt_05": int(np.sum(af > 0.5)),
        "recovered_f1_gt_08": int(np.sum(af > 0.8)),
        "assigned_f1": af,
        "assigned_precision": ap,
        "assigned_recall": ar,
        "candidate_by_label": ai,
    }


def pack(x: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in x.items() if k not in {"assigned_f1", "assigned_precision", "assigned_recall", "candidate_by_label"}}


def aggregate(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    vals = [r[key] for r in rows]
    return {
        "panels": len(vals),
        "mean_macro_f1": mean(float(v["macro_f1"]) for v in vals),
        "mean_macro_precision": mean(float(v["macro_precision"]) for v in vals),
        "mean_macro_recall": mean(float(v["macro_recall"]) for v in vals),
        "total_recovered_f1_gt_05": sum(int(v["recovered_f1_gt_05"]) for v in vals),
        "total_recovered_f1_gt_08": sum(int(v["recovered_f1_gt_08"]) for v in vals),
    }


def exact_parent_reproduction(comp: str, got: dict[str, Any]) -> bool:
    exp = EXPECTED_PARENT[comp]
    return all(got[k] == exp[k] for k in exp)


def paired_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    nonempty = [x for x in rows if int(x["halo_member_count"]) > 0]
    return {
        "count": len(rows),
        "nonempty_count": len(nonempty),
        "nonempty_fraction": float(len(nonempty) / len(rows)) if rows else 0.0,
        "parent_mean_precision": mean(float(x["parent_precision"]) for x in rows) if rows else 0.0,
        "seed_mean_precision": mean(float(x["seed_precision"]) for x in rows) if rows else 0.0,
        "halo_mean_precision": mean(float(x["halo_precision"]) for x in rows) if rows else 0.0,
        "parent_mean_recall": mean(float(x["parent_recall"]) for x in rows) if rows else 0.0,
        "seed_mean_recall": mean(float(x["seed_recall"]) for x in rows) if rows else 0.0,
        "halo_mean_recall": mean(float(x["halo_recall"]) for x in rows) if rows else 0.0,
        "parent_mean_f1": mean(float(x["parent_f1"]) for x in rows) if rows else 0.0,
        "seed_mean_f1": mean(float(x["seed_f1"]) for x in rows) if rows else 0.0,
        "halo_mean_f1": mean(float(x["halo_f1"]) for x in rows) if rows else 0.0,
        "nonempty_precision_nonregression_fraction": float(sum(float(x["halo_precision"]) >= float(x["parent_precision"]) for x in nonempty) / len(nonempty)) if nonempty else 0.0,
        "halo_precision_strict_wins_vs_parent": sum(float(x["halo_precision"]) > float(x["parent_precision"]) for x in rows),
        "halo_f1_strict_wins_vs_seed": sum(float(x["halo_f1"]) > float(x["seed_f1"]) for x in rows),
        "halo_f1_losses_vs_seed": sum(float(x["halo_f1"]) < float(x["seed_f1"]) for x in rows),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    for n in (
        "fair-pretruth", "halo-pretruth", "internal-prelabel", "parent-runner", "quality-source",
        "support-source-parts", "candidate-payload", "baseline-payload", "scorer-parts", "v8-result-json", "output",
    ):
        ap.add_argument("--" + n, type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(sha(a.fair_pretruth) == FAIR_PRETRUTH_SHA256, "fair pretruth changed")
    req(sha(a.internal_prelabel) == INTERNAL_PRE_SHA256, "internal prelabel changed")
    req(sha(a.quality_source) == QUALITY_SHA256 and sha(a.v8_result_json) == V8_SHA256, "runtime changed")
    fair = json.loads(a.fair_pretruth.read_text())
    halo = json.loads(a.halo_pretruth.read_text())
    req(halo["scientific_role"] == "TARGET_EXCLUDED_IMMUTABLE_M2D_ENVELOPE_FIXED4_SEED_OAS_95PCT_DRIFT_HALO_FROZEN_BEFORE_TRUTH", "wrong halo role")
    req(halo["fair_pretruth_sha256"] == FAIR_PRETRUTH_SHA256, "halo parent changed")
    req(halo["confidence"] == 0.95 and halo["dimension"] == 3, "halo confidence changed")
    req(halo["parent_discovery_membership_changed"] is False and halo["parent_rank_changed"] is False, "parent discovery changed")
    req(halo["shower_truth_used"] is False and halo["target_information_access"] is False and halo["target_region_events_accessed"] is False, "halo firewall")
    req(halo["post_result_parameter_search"] is False, "halo search")

    fair_sub = {(int(s["denominator"]), int(s["bucket"])): s for s in fair["subsets"]}
    halo_sub = {(int(s["denominator"]), int(s["bucket"])): s for s in halo["subsets"]}
    req(set(fair_sub) == set(halo_sub) == {(d, b) for d in DENOMS for b in BUCKETS}, "subset mismatch")
    for key in fair_sub:
        parents, hs = list(fair_sub[key]["successor_candidates"]), list(halo_sub[key]["halos"])
        req(len(parents) == len(hs), f"candidate count changed {key}")
        for i, (p, h) in enumerate(zip(parents, hs), 1):
            req(int(p["internal_mass_rank"]) == int(h["rank"]) == i, f"rank changed {key} {i}")
            req(str(p["family_id"]) == str(h["family_id"]) and str(p["family_hash"]) == str(h["family_hash"]), f"identity changed {key} {i}")
            pset = set(str(x) for x in p["event_ids"])
            req(set(str(x) for x in h["seed_event_ids"]).issubset(pset), f"seed escaped parent {key} {i}")
            req(set(str(x) for x in h["halo_event_ids"]).issubset(pset), f"halo escaped parent {key} {i}")
            req(set(str(x) for x in h["seed_event_ids"]).issubset(str(x) for x in h["halo_event_ids"]), f"seed not retained {key} {i}")

    # Truth starts only here. Halo membership is already complete/frozen.
    q = load(a.quality_source, "m2d_fixed4_drift_truth_q")
    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    rt = q.v1.mult.load_frozen_runtime()
    support = rt.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-m2d-fixed4-drift-halo-v1-truth"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "blind changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _cand, base, _scorer = support.load_sources(a)
    scan, _cal, hidden, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS) and [x["key"] for x in sources] == list(MONTH_KEYS), "source set changed")

    comparisons: list[dict[str, Any]] = []
    paired: dict[str, list[dict[str, Any]]] = {"sugar2017": [], "hdbscan2025": []}
    for d in DENOMS:
        for b in BUCKETS:
            fs, hs = fair_sub[(d, b)], halo_sub[(d, b)]
            parents_all = list(fs["successor_candidates"])
            seeds_all = [{"family_id": h["family_id"], "event_ids": h["seed_event_ids"]} for h in hs["halos"]]
            halos_all = [{"family_id": h["family_id"], "event_ids": h["halo_event_ids"]} for h in hs["halos"]]
            for y in YEARS:
                key = f"d{d}_b{b}_y{y}"
                annual = set(str(x) for x in fs["annual_event_ids"][str(y)])
                pp = fair["panels"][key]
                req(int(pp["event_count"]) == len(annual), f"panel count changed {key}")
                for comp in ("sugar2017", "hdbscan2025"):
                    k = len(pp[comp]["clusters"])
                    pm = matrices(parents_all[:k], hidden, annual)
                    sm = matrices(seeds_all[:k], hidden, annual)
                    hm = matrices(halos_all[:k], hidden, annual)
                    req(pm["labels"] == sm["labels"] == hm["labels"], "truth universe mismatch")
                    pa, ha = assigned(pm), assigned(hm)
                    local: list[dict[str, Any]] = []
                    for i, label in enumerate(pm["labels"]):
                        j = int(pa["candidate_by_label"][i])
                        if j < 0 or float(pa["assigned_f1"][i]) <= 0.5:
                            continue
                        row = {
                            "denominator": d,
                            "bucket": b,
                            "year": y,
                            "label": label,
                            "candidate_index": j,
                            "candidate_rank": j + 1,
                            "parent_member_count": int(pm["nmem"][j]),
                            "seed_member_count": int(sm["nmem"][j]),
                            "halo_member_count": int(hm["nmem"][j]),
                            "parent_precision": float(pm["p"][i, j]),
                            "parent_recall": float(pm["r"][i, j]),
                            "parent_f1": float(pm["f"][i, j]),
                            "seed_precision": float(sm["p"][i, j]),
                            "seed_recall": float(sm["r"][i, j]),
                            "seed_f1": float(sm["f"][i, j]),
                            "halo_precision": float(hm["p"][i, j]),
                            "halo_recall": float(hm["r"][i, j]),
                            "halo_f1": float(hm["f"][i, j]),
                        }
                        local.append(row)
                        paired[comp].append(row)
                    comparisons.append({
                        "denominator": d,
                        "bucket": b,
                        "year": y,
                        "comparator": comp,
                        "capacity_k": k,
                        "parent": pack(pa),
                        "rematched_halo_diagnostic": pack(ha),
                        "paired_parent_recovered": local,
                    })

    req(len(comparisons) == 32, "comparison count")
    aggregates: dict[str, Any] = {}
    gates: dict[str, bool] = {}
    for comp in ("sugar2017", "hdbscan2025"):
        cr = [r for r in comparisons if r["comparator"] == comp]
        parent_agg = aggregate(cr, "parent")
        req(exact_parent_reproduction(comp, parent_agg), f"parent reproduction failed {comp}")
        rematched = aggregate(cr, "rematched_halo_diagnostic")
        ps = paired_summary(paired[comp])
        route_gates = {
            "paired_count_at_least_20": ps["count"] >= MIN_PAIRED,
            "nonempty_fraction_at_least_075": ps["nonempty_fraction"] >= MIN_NONEMPTY_FRACTION,
            "mean_halo_precision_at_least_080": ps["halo_mean_precision"] >= MIN_MEAN_PRECISION,
            "mean_halo_precision_strictly_higher_than_parent": ps["halo_mean_precision"] > ps["parent_mean_precision"],
            "mean_halo_f1_retains_at_least_075_parent": ps["halo_mean_f1"] >= MIN_F1_RETENTION * ps["parent_mean_f1"],
            "nonempty_precision_nonregression_fraction_at_least_050": ps["nonempty_precision_nonregression_fraction"] >= MIN_PRECISION_NONREGRESSION_FRACTION,
            "mean_halo_f1_strictly_higher_than_seed": ps["halo_mean_f1"] > ps["seed_mean_f1"],
        }
        for k, v in route_gates.items():
            gates[f"{comp}_{k}"] = bool(v)
        by_scale = {str(d): paired_summary([x for x in paired[comp] if int(x["denominator"]) == d]) for d in DENOMS}
        by_year = {str(y): paired_summary([x for x in paired[comp] if int(x["year"]) == y]) for y in YEARS}
        aggregates[comp] = {
            "parent": parent_agg,
            "rematched_halo_diagnostic": rematched,
            "paired_same_discovery": ps,
            "paired_by_scale": by_scale,
            "paired_by_year": by_year,
            "gates": route_gates,
        }

    verdict = "PASS_M2D_FIXED4_DRIFT_HALO_V1_GMN_DEVELOPMENT" if all(gates.values()) else "FAIL_M2D_FIXED4_DRIFT_HALO_V1_GMN_DEVELOPMENT"
    out = {
        "schema": "ORBITTRACE_M2D_FIXED4_DRIFT_HALO_V1_RESULT",
        "scientific_role": "TARGET_EXCLUDED_DUAL_OUTPUT_EVENT_MEMBERSHIP_DEVELOPMENT_PRIMARY_M2D_DISCOVERY_UNCHANGED",
        "verdict": verdict,
        "fair_pretruth_sha256": FAIR_PRETRUTH_SHA256,
        "halo_pretruth_sha256": sha(a.halo_pretruth),
        "thresholds": {
            "minimum_paired_assignments": MIN_PAIRED,
            "minimum_nonempty_fraction": MIN_NONEMPTY_FRACTION,
            "minimum_mean_precision": MIN_MEAN_PRECISION,
            "minimum_f1_retention_fraction": MIN_F1_RETENTION,
            "minimum_precision_nonregression_fraction": MIN_PRECISION_NONREGRESSION_FRACTION,
        },
        "comparisons": comparisons,
        "aggregates": aggregates,
        "gates": gates,
        "primary_discovery_membership_changed": False,
        "primary_discovery_rank_changed": False,
        "paired_halo_rematching_allowed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_scientific_access": False,
        "external_survey_scientific_access": False,
        "post_result_parameter_search": False,
    }
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": verdict, "aggregates": aggregates, "gates": gates, "result_sha256": sha(a.output)}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
