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
EXPECTED_PARENT_PRELABEL_SHA256 = "efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993"
EXPECTED_PARENT_RESULT_SHA256 = "ca6aeed2b82739003ea5d39b59e869df876de2962164344a938fe4935ea38711"
EXPECTED_PARENT_ORDERED_MEMBERSHIP_SHA256 = "e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2"
EXPECTED_EVENTS_BY_YEAR = {2022: 315024, 2023: 423658}
EXPECTED_EVENTS_TOTAL = 738682


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def eligible_labels(hidden: dict[str, str], annual_ids: set[str]) -> dict[str, int]:
    counts = Counter(label for eid, label in hidden.items() if eid in annual_ids and label != "SPORADIC")
    return {label: n for label, n in counts.items() if n >= 4}


def truth(f: dict[str, Any], hidden: dict[str, str], eligible: dict[str, int]) -> dict[str, Any]:
    ids = [str(x) for x in f["event_ids"]]
    counts = Counter(hidden.get(eid, "SPORADIC") for eid in ids)
    rows = []
    for label, total in eligible.items():
        ov = int(counts.get(label, 0))
        if ov <= 0:
            continue
        p = ov / max(len(ids), 1)
        r = ov / total
        f1 = 2 * p * r / (p + r) if p + r else 0.0
        rows.append((f1, p, ov, label, r))
    if not rows:
        return {"positive": False, "best_label": None, "dominant_precision": 0.0}
    f1, p, ov, label, r = max(rows, key=lambda x: (x[0], x[1], x[2], x[3]))
    non = counts.copy()
    non.pop("SPORADIC", None)
    dominant = max(non.values(), default=0) / max(len(ids), 1)
    return {
        "positive": bool(p >= 0.5 and ov >= 4),
        "best_label": label,
        "f1": float(f1),
        "precision": float(p),
        "recall": float(r),
        "overlap": int(ov),
        "dominant_precision": float(dominant),
    }


def metrics(pooled: list[dict[str, Any]], hidden: dict[str, str], annual_ids: set[str]) -> dict[str, Any]:
    eligible = eligible_labels(hidden, annual_ids)
    first: dict[str, int | None] = {label: None for label in eligible}
    fragments: Counter[str] = Counter()
    top_prec: list[float] = []
    for rank, pooled_f in enumerate(pooled, 1):
        annual_f = {
            "family_id": pooled_f["family_id"],
            "event_ids": [eid for eid in pooled_f["event_ids"] if eid in annual_ids],
        }
        t = truth(annual_f, hidden, eligible)
        if rank <= 100:
            top_prec.append(float(t["dominant_precision"]))
        if t["positive"] and t["best_label"] in eligible:
            label = str(t["best_label"])
            fragments[label] += int(rank <= 500)
            if first[label] is None:
                first[label] = rank
    represented = [label for label, rank in first.items() if rank is not None]
    frag = [fragments[label] for label in represented if first[label] is not None and first[label] <= 500]
    rr_mass = float(sum(1.0 / float(r) for r in first.values() if r is not None))
    eligible_count = len(eligible)
    qualified_count = len(represented)
    conditional_mrr = float(rr_mass / qualified_count) if qualified_count else 0.0
    zero_mrr = float(rr_mass / eligible_count) if eligible_count else 0.0
    return {
        "eligible_labels": eligible_count,
        "qualified_matches": qualified_count,
        "recovered_at_25": sum(r is not None and r <= 25 for r in first.values()),
        "recovered_at_50": sum(r is not None and r <= 50 for r in first.values()),
        "recovered_at_100": sum(r is not None and r <= 100 for r in first.values()),
        "recovered_at_500": sum(r is not None and r <= 500 for r in first.values()),
        "top100_dominant_precision": float(np.mean(top_prec)) if top_prec else 0.0,
        "conditional_mrr": conditional_mrr,
        "reciprocal_rank_mass": rr_mass,
        "zero_filled_mrr": zero_mrr,
        "fragmentation_median_top500": float(np.median(frag)) if frag else 0.0,
        "first_rank_by_label": first,
    }


def close(a: float, b: float, atol: float = 1e-15) -> bool:
    return bool(np.isclose(float(a), float(b), rtol=0.0, atol=atol))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prelabel", type=Path, required=True)
    ap.add_argument("--parent-prelabel", type=Path, required=True)
    ap.add_argument("--parent-result", type=Path, required=True)
    ap.add_argument("--parent-runner", type=Path, required=True)
    ap.add_argument("--quality-source", type=Path, required=True)
    ap.add_argument("--support-source-parts", type=Path, required=True)
    ap.add_argument("--candidate-payload", type=Path, required=True)
    ap.add_argument("--baseline-payload", type=Path, required=True)
    ap.add_argument("--scorer-parts", type=Path, required=True)
    ap.add_argument("--v8-result-json", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(sha256(a.parent_prelabel) == EXPECTED_PARENT_PRELABEL_SHA256, "binding parent prelabel changed")
    req(sha256(a.parent_result) == EXPECTED_PARENT_RESULT_SHA256, "binding parent result changed")
    req(sha256(a.quality_source) == QUALITY_SHA256, "frozen GMN runtime utility changed")
    req(sha256(a.v8_result_json) == V8_RESULT_SHA256, "frozen GMN support artifact changed")

    frozen = json.loads(a.prelabel.read_text())
    req(frozen["schema"] == "ORBITTRACE_RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1_PRELABEL", "wrong successor prelabel schema")
    req(frozen["scientific_role"] == "PRELABEL_TARGET_EXCLUDED_FIXED_RANK_MEMBERSHIP_REPRESENTATION", "wrong successor prelabel role")
    req(frozen["shower_truth_used"] is False, "prelabel reports shower-truth use")
    req(frozen["target_information_access"] is False and frozen["target_region_events_accessed"] is False, "prelabel firewall failed")
    req(frozen["parent_ordered_membership_sha256"] == EXPECTED_PARENT_ORDERED_MEMBERSHIP_SHA256, "prelabel parent order changed")
    parents = list(frozen["parent_candidates"])
    successor = list(frozen["successor_candidates"])
    req(len(parents) == len(successor) == 2094, "fixed catalogue slot count changed")
    req([int(r["rank"]) for r in successor] == list(range(1, len(successor) + 1)), "successor rank order changed")
    for p, s in zip(parents, successor):
        req(str(p["family_id"]) == str(s["parent_family_id"]) == str(s["family_id"]), "parent identity changed")
        req(set(s["event_ids"]).issubset(set(p["event_ids"])), "successor escaped same-rank parent")

    parent_binding_result = json.loads(a.parent_result.read_text())
    parent_binding_pre = json.loads(a.parent_prelabel.read_text())
    req(parent_binding_result["verdict"] == "PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_GMN_DEVELOPMENT", "parent binding verdict changed")
    req(parent_binding_pre["successor_ordered_membership_sha256"] == EXPECTED_PARENT_ORDERED_MEMBERSHIP_SHA256, "binding parent membership hash changed")

    parent_runner = load_module(a.parent_runner, "local_trunk_truth_parent")
    req(tuple(parent_runner.YEARS) == YEARS and tuple(parent_runner.BLIND) == BLIND, "truth parent constants changed")
    qmod = load_module(a.quality_source, "local_trunk_truth_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-recurrent-local-topomodal-trunk-v1-binding-truth"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), f"wrong GMN years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    annual_ids: dict[int, set[str]] = {}
    all_ids: set[str] = set()
    for year in YEARS:
        raw = list(scan[year])
        rows = [parent_runner.normalize_event(row, year) for row in raw]
        annual_ids[year] = {str(e["id"]) for e in rows}
        req(len(annual_ids[year]) == EXPECTED_EVENTS_BY_YEAR[year], f"annual event count changed {year}")
        all_ids.update(annual_ids[year])
    req(len(all_ids) == EXPECTED_EVENTS_TOTAL, "pooled event count changed")
    req(all(eid in all_ids for eid in hidden), "label outside accessible event universe")

    parent_metrics = {str(y): metrics(parents, hidden, annual_ids[y]) for y in YEARS}
    successor_metrics = {str(y): metrics(successor, hidden, annual_ids[y]) for y in YEARS}

    for y in YEARS:
        py = parent_metrics[str(y)]
        sealed = parent_binding_result["successor_metrics"][str(y)]
        for key in ("eligible_labels", "qualified_matches", "recovered_at_25", "recovered_at_50", "recovered_at_100", "recovered_at_500"):
            req(int(py[key]) == int(sealed[key]), f"parent truth reproduction changed {y} {key}: {py[key]} != {sealed[key]}")
        req(close(py["top100_dominant_precision"], sealed["top100_dominant_precision"]), f"parent precision changed {y}")
        req(close(py["conditional_mrr"], sealed["mrr"]), f"parent historical conditional MRR changed {y}")
        req(close(py["fragmentation_median_top500"], sealed["fragmentation_median_top500"]), f"parent fragmentation changed {y}")
        req(py["first_rank_by_label"] == sealed["first_rank_by_label"], f"parent first-rank map changed {y}")

    annual_gates: dict[str, dict[str, bool]] = {}
    gate_records: list[dict[str, Any]] = []
    for y in YEARS:
        p = parent_metrics[str(y)]
        s = successor_metrics[str(y)]
        gates = {
            "qualified_recovery_not_lower": int(s["qualified_matches"]) >= int(p["qualified_matches"]),
            "recovered_at_25_not_lower": int(s["recovered_at_25"]) >= int(p["recovered_at_25"]),
            "recovered_at_50_not_lower": int(s["recovered_at_50"]) >= int(p["recovered_at_50"]),
            "recovered_at_100_not_lower": int(s["recovered_at_100"]) >= int(p["recovered_at_100"]),
            "zero_filled_mrr_not_lower": float(s["zero_filled_mrr"]) >= float(p["zero_filled_mrr"]),
            "top100_precision_not_lower": float(s["top100_dominant_precision"]) >= float(p["top100_dominant_precision"]),
            "fragmentation_not_higher": float(s["fragmentation_median_top500"]) <= float(p["fragmentation_median_top500"]),
        }
        annual_gates[str(y)] = gates
        for name, passed in gates.items():
            gate_records.append({"gate": f"{y}:{name}", "passed": bool(passed)})

    mechanism_active = bool(int(frozen["changed_slot_count"]) > 0 and frozen["mechanism_active"])
    strict_zero = any(float(successor_metrics[str(y)]["zero_filled_mrr"]) > float(parent_metrics[str(y)]["zero_filled_mrr"]) for y in YEARS)
    global_gates = {
        "representation_mechanism_active": mechanism_active,
        "strict_zero_filled_mrr_improvement_some_year": strict_zero,
    }
    for name, passed in global_gates.items():
        gate_records.append({"gate": f"global:{name}", "passed": bool(passed)})
    req(len(gate_records) == 16, f"binding gate count changed: {len(gate_records)}")
    passed_count = sum(int(r["passed"]) for r in gate_records)
    verdict = "PASS_RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1" if passed_count == 16 else "FAIL_RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1"

    result = {
        "schema": "ORBITTRACE_RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1_BINDING_RESULT",
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_FIXED_RANK_MEMBERSHIP_BINDING",
        "verdict": verdict,
        "prelabel_sha256": sha256(a.prelabel),
        "parent_binding_run_id": 31852836840,
        "parent_binding_artifact_id": 9238142199,
        "parent_binding_artifact_digest": "sha256:918992863d019baf3bbb5eadd83ecaa32cabea3d9bd7d9d43735b26474e8ed60",
        "parent_metrics": parent_metrics,
        "successor_metrics": successor_metrics,
        "annual_gates": annual_gates,
        "global_gates": global_gates,
        "gates": gate_records,
        "passed_gate_count": passed_count,
        "total_gate_count": 16,
        "changed_slot_count": int(frozen["changed_slot_count"]),
        "mechanism_active": mechanism_active,
        "historical_conditional_mrr_is_diagnostic_only": True,
        "binding_retrieval_metric": "zero_filled_eligible_query_mrr",
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_event_level_access": False,
        "efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    compact = lambda m: {k: v for k, v in m.items() if k != "first_rank_by_label"}
    print(json.dumps({
        "verdict": verdict,
        "passed_gate_count": passed_count,
        "total_gate_count": 16,
        "changed_slot_count": int(frozen["changed_slot_count"]),
        "parent": {str(y): compact(parent_metrics[str(y)]) for y in YEARS},
        "successor": {str(y): compact(successor_metrics[str(y)]) for y in YEARS},
        "annual_gates": annual_gates,
        "global_gates": global_gates,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
