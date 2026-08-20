#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

YEARS = (2013, 2014)
BUDGETS = (10, 20, 30, 40)
PARENT_RANKED_SHA256 = "9be0e77d650cabd94eccf0623f005705bb86e84793c76190b0065621631f2ecd"
BASELINE_RUNNER_BLOB = "b44e0222e08ae4e85f0ea9a91c95f7b9141f3fb9"
EXPECTED_CANDIDATES = 888
EXPECTED_TOTAL = 29246
EXPECTED_COMMON = {2013: 15988, 2014: 13258}
BASELINE_M2D = {
    "mean_test_auc_macro_f1": 0.35364538749003405,
    "mean_test_macro_f1_at_40": 0.5012446318461822,
    "total_test_recovered_at_40": 58,
    "mean_native_macro_f1": 0.7266723655790133,
}
MIN_PAIRED = 20
MIN_NONEMPTY_FRACTION = 0.75
MIN_MEAN_PRECISION = 0.80
MIN_F1_RETENTION = 0.75
MIN_PRECISION_NONREGRESSION_FRACTION = 0.50
ROUTES = ("tuned_hdbscan_comparison", "fixed_modal_comparison")


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blob(path: Path) -> str:
    b = path.read_bytes()
    return hashlib.sha1(f"blob {len(b)}\0".encode() + b).hexdigest()


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def matrices(families: list[dict[str, Any]], truth: dict[str, str]) -> dict[str, Any]:
    counts = Counter(v for v in truth.values() if v != "SPORADIC")
    labels = sorted(k for k, n in counts.items() if n >= 4)
    L, C = len(labels), len(families)
    f = np.zeros((L, C), dtype=float)
    p = np.zeros_like(f)
    r = np.zeros_like(f)
    nmem = np.zeros(C, dtype=int)
    ids = set(truth)
    label_ix = {lab: i for i, lab in enumerate(labels)}
    for j, fam in enumerate(families):
        mem = [str(x) for x in fam["member_ids"] if str(x) in ids]
        nmem[j] = len(mem)
        if not mem:
            continue
        cc = Counter(truth[eid] for eid in mem)
        for lab, ov in cc.items():
            if lab not in label_ix:
                continue
            i = label_ix[lab]
            pp = ov / len(mem)
            rr = ov / counts[lab]
            ff = 2.0 * pp * rr / (pp + rr) if pp + rr else 0.0
            p[i, j], r[i, j], f[i, j] = pp, rr, ff
    return {"labels": labels, "f": f, "p": p, "r": r, "nmem": nmem}


def assign(m: dict[str, Any]) -> dict[str, Any]:
    f, p, r = m["f"], m["p"], m["r"]
    L, C = f.shape
    af = np.zeros(L, dtype=float); ap = np.zeros(L, dtype=float); ar = np.zeros(L, dtype=float)
    ai = np.full(L, -1, dtype=int)
    n = max(L, C)
    if n:
        cost = np.zeros((n, n), dtype=float)
        cost[:L, :C] = -f
        ri, cj = linear_sum_assignment(cost)
        for i, j in zip(ri, cj):
            if i < L and j < C:
                af[i], ap[i], ar[i], ai[i] = f[i, j], p[i, j], r[i, j], int(j)
    return {
        "eligible_showers": L,
        "candidate_count": C,
        "macro_f1": float(np.mean(af)) if L else 0.0,
        "macro_precision": float(np.mean(ap)) if L else 0.0,
        "macro_recall": float(np.mean(ar)) if L else 0.0,
        "recovered_f1_gt_0_5": int(np.sum(af > 0.5)),
        "assigned_f1": af,
        "assigned_precision": ap,
        "assigned_recall": ar,
        "candidate_by_label": ai,
    }


def pack(a: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in a.items() if k not in {"assigned_f1", "assigned_precision", "assigned_recall", "candidate_by_label"}}


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
        "halo_f1_strict_wins_vs_seed": sum(float(x["halo_f1"]) > float(x["seed_f1"]) for x in rows),
        "halo_f1_losses_vs_seed": sum(float(x["halo_f1"]) < float(x["seed_f1"]) for x in rows),
    }


def route_gates(s: dict[str, Any]) -> dict[str, bool]:
    return {
        "paired_count_at_least_20": s["count"] >= MIN_PAIRED,
        "nonempty_fraction_at_least_075": s["nonempty_fraction"] >= MIN_NONEMPTY_FRACTION,
        "mean_halo_precision_at_least_080": s["halo_mean_precision"] >= MIN_MEAN_PRECISION,
        "mean_halo_precision_strictly_higher_than_parent": s["halo_mean_precision"] > s["parent_mean_precision"],
        "mean_halo_f1_retains_at_least_075_parent": s["halo_mean_f1"] >= MIN_F1_RETENTION * s["parent_mean_f1"],
        "nonempty_precision_nonregression_fraction_at_least_050": s["nonempty_precision_nonregression_fraction"] >= MIN_PRECISION_NONREGRESSION_FRACTION,
        "mean_halo_f1_strictly_higher_than_seed": s["halo_mean_f1"] > s["seed_mean_f1"],
    }


def close(a: float, b: float, tol: float = 1e-12) -> bool:
    return abs(float(a) - float(b)) <= tol


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows-root", type=Path, required=True)
    ap.add_argument("--truth-root", type=Path, required=True)
    ap.add_argument("--parent-ranked", type=Path, required=True)
    ap.add_argument("--halo-pretruth", type=Path, required=True)
    ap.add_argument("--baseline-runner", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(sha(a.parent_ranked) == PARENT_RANKED_SHA256, "parent ranked pretruth changed")
    req(blob(a.baseline_runner) == BASELINE_RUNNER_BLOB, "baseline helper changed")
    parent = json.loads(a.parent_ranked.read_text())
    halo = json.loads(a.halo_pretruth.read_text())
    req(parent["scientific_role"] == "ZERO_LABEL_EXACT_INTERNAL_MASS_RANKING", "wrong parent role")
    req(parent["truth_used"] is False and parent["shower_labels_accessed"] is False, "parent firewall")
    req(halo["scientific_role"] == "NO_RETUNING_SONOTACO_BASELINE_M2D_FIXED4_SEED_OAS_95PCT_DRIFT_HALOS_FROZEN_BEFORE_TRUTH", "wrong halo role")
    req(halo["parent_ranked_sha256"] == PARENT_RANKED_SHA256, "halo parent provenance")
    req(halo["candidate_count"] == EXPECTED_CANDIDATES and len(halo["halos"]) == EXPECTED_CANDIDATES, "halo candidate count")
    req(halo["truth_artifact_downloaded"] is False and halo["truth_used"] is False and halo["shower_labels_accessed"] is False, "halo truth firewall")
    req(halo["post_result_parameter_search"] is False, "halo post-result search")

    ranked = list(parent["candidates"])
    halos = list(halo["halos"])
    req([int(r["internal_mass_rank"]) for r in ranked] == list(range(1, EXPECTED_CANDIDATES + 1)), "parent rank sequence")
    for i, (p, h) in enumerate(zip(ranked, halos), 1):
        req(int(h["rank"]) == i and str(h["family_id"]) == str(p["family_id"]) and str(h["family_hash"]) == str(p["family_hash"]), f"halo identity/rank mismatch {i}")
        pset = set(str(x) for x in p["event_ids"])
        req(set(h["seed_event_ids"]).issubset(pset) and set(h["halo_event_ids"]).issubset(pset), f"halo escaped parent {i}")
        req(set(h["seed_event_ids"]).issubset(h["halo_event_ids"]), f"seed not retained {i}")

    baseline = load(a.baseline_runner, "drift_sonotaco_truth_helper")
    pooled, ids_by_year, universe = baseline.merge_common(a.rows_root)
    req(len(pooled) == EXPECTED_TOTAL and universe["common_counts"] == {str(y): EXPECTED_COMMON[y] for y in YEARS}, "common universe changed")

    # First known-shower truth access occurs here, after the complete halo pretruth is frozen.
    truth = baseline.common_truth(a.truth_root, ids_by_year)
    parent_fam = [{"family_id": r["family_id"], "member_ids": r["event_ids"], "rank": int(r["internal_mass_rank"])} for r in ranked]
    seed_fam = [{"family_id": h["family_id"], "member_ids": h["seed_event_ids"], "rank": int(h["rank"])} for h in halos]
    halo_fam = [{"family_id": h["family_id"], "member_ids": h["halo_event_ids"], "rank": int(h["rank"])} for h in halos]

    # Exact baseline parent aggregate reproduction uses the already-frozen helper.
    parent_curves = {y: baseline.curve(parent_fam, truth[y]) for y in YEARS}
    parent_agg = baseline.aggregate(parent_curves)
    for k, v in BASELINE_M2D.items():
        req((parent_agg[k] == v) if isinstance(v, int) else close(parent_agg[k], v), f"baseline M2D reproduction mismatch {k}: {parent_agg[k]} {v}")

    panels: list[dict[str, Any]] = []
    paired: list[dict[str, Any]] = []
    for y in YEARS:
        for budget in BUDGETS:
            pm = matrices(parent_fam[:budget], truth[y])
            sm = matrices(seed_fam[:budget], truth[y])
            hm = matrices(halo_fam[:budget], truth[y])
            req(pm["labels"] == sm["labels"] == hm["labels"], "truth label universe mismatch")
            pa = assign(pm); ha = assign(hm)
            local: list[dict[str, Any]] = []
            for i, label in enumerate(pm["labels"]):
                j = int(pa["candidate_by_label"][i])
                if j < 0 or float(pa["assigned_f1"][i]) <= 0.5:
                    continue
                row = {
                    "year": y,
                    "budget": budget,
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
                paired.append(row)
            panels.append({
                "year": y,
                "budget": budget,
                "parent": pack(pa),
                "rematched_halo_diagnostic": pack(ha),
                "paired_parent_recovered": local,
            })

    summary = paired_summary(paired)
    gates_one = route_gates(summary)
    # Both frozen SonotaCo comparison routes use the same exact common-universe parent
    # budget panels. We report them independently without inventing route-specific
    # candidate generation or membership differences.
    routes = {route: {"paired_same_discovery": summary, "gates": dict(gates_one), "panel_identity": "same_symmetric_common_universe_parent_budgets"} for route in ROUTES}
    gates = {f"{route}_{k}": bool(v) for route in ROUTES for k, v in gates_one.items()}
    verdict = "PASS_M2D_FIXED4_DRIFT_HALO_V1_SONOTACO_TRANSFER" if all(gates.values()) else "FAIL_M2D_FIXED4_DRIFT_HALO_V1_SONOTACO_TRANSFER"

    result = {
        "schema": "ORBITTRACE_M2D_FIXED4_DRIFT_HALO_V1_SONOTACO_RESULT",
        "scientific_role": "NO_RETUNING_CROSS_SURVEY_MEMBERSHIP_TRANSFER_ON_EXPOSED_SYMMETRIC_COMMON_UNIVERSE",
        "verdict": verdict,
        "parent_ranked_sha256": PARENT_RANKED_SHA256,
        "halo_pretruth_sha256": sha(a.halo_pretruth),
        "candidate_count": EXPECTED_CANDIDATES,
        "common_universe": universe,
        "parent_aggregate": parent_agg,
        "parent_curves": {str(y): parent_curves[y] for y in YEARS},
        "panels": panels,
        "routes": routes,
        "gates": gates,
        "thresholds": {
            "minimum_paired_assignments": MIN_PAIRED,
            "minimum_nonempty_fraction": MIN_NONEMPTY_FRACTION,
            "minimum_mean_precision": MIN_MEAN_PRECISION,
            "minimum_f1_retention_fraction": MIN_F1_RETENTION,
            "minimum_precision_nonregression_fraction": MIN_PRECISION_NONREGRESSION_FRACTION,
        },
        "parent_discovery_membership_changed": False,
        "parent_rank_changed": False,
        "halo_rematching_can_rescue": False,
        "method_changed_after_truth": False,
        "post_result_parameter_search": False,
        "target_information_access": False,
    }
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": verdict, "parent_aggregate": parent_agg, "paired": summary, "gates": gates, "result_sha256": sha(a.output)}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
