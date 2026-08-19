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
INTERNAL_PRE_SHA = "7b1ddfcd32cd0b52321e3b3dfc614a88dd9b973f947c1d4d0de74fddf26b59cd"
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
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
    label_ix = {lab: i for i, lab in enumerate(labels)}
    for j, cand in enumerate(cands):
        ids = [str(x) for x in cand["event_ids"] if str(x) in annual]
        n = len(ids)
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
            p[i, j] = pp
            r[i, j] = rr
            f[i, j] = ff
    return {"labels": labels, "counts": counts, "f": f, "p": p, "r": r}


def assigned(m: dict[str, Any]) -> dict[str, Any]:
    f, p, r = m["f"], m["p"], m["r"]
    L, C = f.shape
    af = np.zeros(L, dtype=float)
    ap = np.zeros(L, dtype=float)
    ar = np.zeros(L, dtype=float)
    candidate_by_label = np.full(L, -1, dtype=int)
    if C:
        ri, cj = linear_sum_assignment(f, maximize=True)
        for i, j in zip(ri, cj):
            af[i], ap[i], ar[i] = f[i, j], p[i, j], r[i, j]
            candidate_by_label[i] = int(j)
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
        "candidate_by_label": candidate_by_label,
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
    return (
        got["mean_macro_f1"] == exp["mean_macro_f1"]
        and got["mean_macro_precision"] == exp["mean_macro_precision"]
        and got["mean_macro_recall"] == exp["mean_macro_recall"]
        and got["total_recovered_f1_gt_05"] == exp["total_recovered_f1_gt_05"]
        and got["total_recovered_f1_gt_08"] == exp["total_recovered_f1_gt_08"]
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    for n in (
        "fair-pretruth", "core-pretruth", "internal-prelabel", "parent-runner", "quality-source",
        "support-source-parts", "candidate-payload", "baseline-payload", "scorer-parts", "v8-result-json", "output",
    ):
        ap.add_argument("--" + n, type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(sha(a.fair_pretruth) == FAIR_PRETRUTH_SHA256, "fair pretruth changed")
    req(sha(a.internal_prelabel) == INTERNAL_PRE_SHA, "internal prelabel changed")
    req(sha(a.quality_source) == QUALITY_SHA and sha(a.v8_result_json) == V8_SHA, "runtime inputs changed")
    fair = json.loads(a.fair_pretruth.read_text())
    core = json.loads(a.core_pretruth.read_text())
    req(fair["scientific_role"] == "TARGET_EXCLUDED_GMN_SPARSE_LITERATURE_COMPARATORS_FROZEN_BEFORE_TRUTH", "fair pretruth role")
    req(core["scientific_role"] == "TARGET_EXCLUDED_DUAL_VIEW_M2D_ENVELOPE_CROSSYEAR_RECURRENCE_CORE_FROZEN_BEFORE_TRUTH", "core pretruth role")
    req(core["fair_pretruth_sha256"] == FAIR_PRETRUTH_SHA256, "core parent provenance")
    req(core["shower_truth_used"] is False and core["target_information_access"] is False and core["target_region_events_accessed"] is False, "core firewall")
    req(core["post_result_parameter_search"] is False, "core post-result search")

    fair_sub = {(int(s["denominator"]), int(s["bucket"])): s for s in fair["subsets"]}
    core_sub = {(int(s["denominator"]), int(s["bucket"])): s for s in core["subsets"]}
    req(set(fair_sub) == set(core_sub) == {(d, b) for d in DENOMS for b in BUCKETS}, "subset set changed")
    for key in fair_sub:
        fs, cs = fair_sub[key], core_sub[key]
        env = list(fs["successor_candidates"])
        cores = list(cs["cores"])
        req(len(env) == len(cores) == int(cs["parent_candidate_count"]), f"candidate count drift {key}")
        for i, (e, c) in enumerate(zip(env, cores), 1):
            req(int(e["internal_mass_rank"]) == int(c["rank"]) == i, f"rank drift {key} {i}")
            req(str(e["family_id"]) == str(c["family_id"]) and str(e["family_hash"]) == str(c["family_hash"]), f"identity drift {key} {i}")
            req(set(str(x) for x in c["core_event_ids"]).issubset(str(x) for x in e["event_ids"]), f"core escaped envelope {key} {i}")

    # Exact same hidden-label reconstruction as PR #1377 starts here; no detector
    # or extraction code executes after this point.
    q = load(a.quality_source, "m2d_recurrence_q")
    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    rt = q.v1.mult.load_frozen_runtime()
    support = rt.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-m2d-crossyear-recurrence-core-v1-truth"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "blind changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _cand, base, _scorer = support.load_sources(a)
    scan, _cal, hidden, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS) and [x["key"] for x in sources] == list(MONTH_KEYS), "source set changed")

    comparisons: list[dict[str, Any]] = []
    paired_by_comp: dict[str, list[dict[str, float]]] = {"sugar2017": [], "hdbscan2025": []}
    for d in DENOMS:
        for b in BUCKETS:
            fs, cs = fair_sub[(d, b)], core_sub[(d, b)]
            env_all = list(fs["successor_candidates"])
            core_all = [
                {"family_id": c["family_id"], "event_ids": c["core_event_ids"], "member_count": c["core_member_count"]}
                for c in cs["cores"]
            ]
            for y in YEARS:
                panel_key = f"d{d}_b{b}_y{y}"
                annual = set(str(x) for x in fs["annual_event_ids"][str(y)])
                pp = fair["panels"][panel_key]
                req(int(pp["event_count"]) == len(annual), f"panel event count drift {panel_key}")
                for comp in ("sugar2017", "hdbscan2025"):
                    k = len(pp[comp]["clusters"])
                    env = env_all[:k]
                    cor = core_all[:k]
                    em = matrices(env, hidden, annual)
                    cm = matrices(cor, hidden, annual)
                    req(em["labels"] == cm["labels"], "label universe mismatch")
                    ea = assigned(em)
                    ca = assigned(cm)
                    paired: list[dict[str, Any]] = []
                    for i, lab in enumerate(em["labels"]):
                        j = int(ea["candidate_by_label"][i])
                        if j < 0 or float(ea["assigned_f1"][i]) <= 0.5:
                            continue
                        row = {
                            "label": lab,
                            "candidate_index": j,
                            "candidate_rank": j + 1,
                            "parent_f1": float(em["f"][i, j]),
                            "parent_precision": float(em["p"][i, j]),
                            "parent_recall": float(em["r"][i, j]),
                            "core_f1": float(cm["f"][i, j]),
                            "core_precision": float(cm["p"][i, j]),
                            "core_recall": float(cm["r"][i, j]),
                        }
                        paired.append(row)
                        paired_by_comp[comp].append({k: float(v) for k, v in row.items() if k.endswith(("_f1", "_precision", "_recall"))})
                    comparisons.append({
                        "denominator": d,
                        "bucket": b,
                        "year": y,
                        "comparator": comp,
                        "capacity_k": k,
                        "envelope": pack(ea),
                        "core": pack(ca),
                        "paired_recovered_assignments": paired,
                    })

    req(len(comparisons) == 32, "comparison count")
    aggregates: dict[str, Any] = {}
    gates: dict[str, bool] = {}
    for comp in ("sugar2017", "hdbscan2025"):
        rows = [r for r in comparisons if r["comparator"] == comp]
        env_agg = aggregate(rows, "envelope")
        core_agg = aggregate(rows, "core")
        req(exact_parent_reproduction(comp, env_agg), f"parent reproduction failed {comp}")
        route_gates = {
            "mean_precision_strictly_higher": core_agg["mean_macro_precision"] > env_agg["mean_macro_precision"],
            "mean_f1_not_lower": core_agg["mean_macro_f1"] >= env_agg["mean_macro_f1"],
            "recovered_gt05_not_lower": core_agg["total_recovered_f1_gt_05"] >= env_agg["total_recovered_f1_gt_05"],
        }
        scale_rows: dict[str, Any] = {}
        for d in DENOMS:
            dr = [r for r in rows if r["denominator"] == d]
            de, dc = aggregate(dr, "envelope"), aggregate(dr, "core")
            sg = {
                "mean_f1_not_lower": dc["mean_macro_f1"] >= de["mean_macro_f1"],
                "recovered_gt05_not_lower": dc["total_recovered_f1_gt_05"] >= de["total_recovered_f1_gt_05"],
            }
            scale_rows[str(d)] = {"envelope": de, "core": dc, "gates": sg}
            for name, passed in sg.items():
                gates[f"{comp}_d{d}_{name}"] = bool(passed)
        paired = paired_by_comp[comp]
        req(len(paired) > 0, f"no paired recovered assignments {comp}")
        paired_summary = {
            "count": len(paired),
            "parent_mean_precision": mean(x["parent_precision"] for x in paired),
            "core_mean_precision": mean(x["core_precision"] for x in paired),
            "parent_mean_f1": mean(x["parent_f1"] for x in paired),
            "core_mean_f1": mean(x["core_f1"] for x in paired),
            "parent_mean_recall": mean(x["parent_recall"] for x in paired),
            "core_mean_recall": mean(x["core_recall"] for x in paired),
            "core_f1_strict_wins": sum(x["core_f1"] > x["parent_f1"] for x in paired),
            "core_f1_ties": sum(x["core_f1"] == x["parent_f1"] for x in paired),
            "core_f1_losses": sum(x["core_f1"] < x["parent_f1"] for x in paired),
        }
        paired_gates = {
            "paired_precision_strictly_higher": paired_summary["core_mean_precision"] > paired_summary["parent_mean_precision"],
            "paired_f1_not_lower": paired_summary["core_mean_f1"] >= paired_summary["parent_mean_f1"],
        }
        for name, passed in route_gates.items():
            gates[f"{comp}_{name}"] = bool(passed)
        for name, passed in paired_gates.items():
            gates[f"{comp}_{name}"] = bool(passed)
        gates[f"{comp}_paired_nonvacuous"] = len(paired) > 0
        aggregates[comp] = {
            "envelope": env_agg,
            "core": core_agg,
            "route_gates": route_gates,
            "scales": scale_rows,
            "paired": paired_summary,
            "paired_gates": paired_gates,
        }

    verdict = "PASS_M2D_CROSSYEAR_RECURRENCE_CORE_V1_GMN_DEVELOPMENT" if all(gates.values()) else "FAIL_M2D_CROSSYEAR_RECURRENCE_CORE_V1_GMN_DEVELOPMENT"
    out = {
        "schema": "ORBITTRACE_M2D_CROSSYEAR_RECURRENCE_CORE_V1_RESULT",
        "scientific_role": "TARGET_EXCLUDED_GENERIC_EXTRACTION_DEVELOPMENT_WITH_IMMUTABLE_M2D_ENVELOPE_RANKING",
        "verdict": verdict,
        "fair_pretruth_sha256": FAIR_PRETRUTH_SHA256,
        "core_pretruth_sha256": sha(a.core_pretruth),
        "comparisons": comparisons,
        "aggregates": aggregates,
        "gates": gates,
        "parent_ranking_changed": False,
        "core_rematching_allowed_in_full_catalogue_evaluation": True,
        "paired_evaluation_rematching_allowed": False,
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
