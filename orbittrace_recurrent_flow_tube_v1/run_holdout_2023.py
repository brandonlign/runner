#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from orbittrace_recurrent_flow_tube_v1 import run_development as rft

YEAR = 2023
YEARS = (YEAR,)
MONTH_KEYS = tuple(f"{YEAR}-{m:02d}" for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
RFT_PROTOCOL_BLOB = "515362e69bec642a891e44dfd87dce9693942574"
RFT_IMPLEMENTATION_BLOB = "a5d5371f0c30a9c57ee4d8756ea41f454cd86301"


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


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--development-result", type=Path, required=True)
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    # The 2022 viability authorizer is checked before any runtime catalogue source is loaded.
    dev_sha = sha(a.development_result)
    dev = json.loads(a.development_result.read_text())
    req(dev["verdict"] == "PASS_RFT_V1_GMN2022_DEVELOPMENT_VIABILITY", "RFT v1 did not pass frozen GMN 2022 viability")
    req(dev["scientific_role"] == "TARGET_EXCLUDED_GMN_2022_DEVELOPMENT_ONLY", "2022 scientific role changed")
    req(dev["gmn_2023_access"] is False, "2022 development accessed GMN 2023")
    req(dev["sonotaco_2013_2014_access"] is False, "2022 development accessed SonotaCo")
    req(dev["target_information_access"] is False and dev["target_region_events_accessed"] is False, "2022 target firewall changed")
    req(dev["maarsy_scientific_access"] is False and dev["dms_scientific_access"] is False, "2022 survey firewall changed")
    req(dev["blind_exclusion"] == [20.0, 55.0], "2022 blind exclusion changed")

    req(sha(a.quality_source) == QUALITY_SHA, "#839 utility source changed")
    req(sha(a.v8_result_json) == V8_RESULT_SHA, "frozen GMN runtime-support artifact changed")

    # Switch only the exact frozen RFT runtime year; all scientific constants/functions remain the parent bytes.
    rft.YEAR = YEAR
    rft.YEARS = YEARS
    rft.MONTH_KEYS = MONTH_KEYS
    req(rft.BLIND == BLIND, "RFT blind interval changed")
    req(rft.BIN_WIDTH == 2.0 and rft.KNN == 4 and rft.MIN_ATOM == 4, "RFT local-atom constants changed")
    req(rft.MIN_STRATA == 3 and rft.MIN_SPAN == 6.0 and rft.MIN_EVENTS == 10, "RFT tube constants changed")
    req(rft.PERTURB_REPLICAS == 16 and rft.PERTURB_RAD_DEG == 0.35 and rft.PERTURB_SPEED_FRAC == 0.01, "RFT perturbation constants changed")
    req(rft.PERSIST_JACCARD == 0.50 and rft.PERSIST_MIN == 0.50 and rft.TRAJECTORY_TRIM == 2.5, "RFT persistence/trim constants changed")

    qmod = load_module(a.quality_source, "rft_holdout_frozen_839_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-recurrent-flow-tube-v1-heldout-2023-only"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden, sources = support.parse_catalogue(base)

    req(sorted(scan) == [YEAR], f"held-out runtime accessed wrong years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN 2023 source list changed")
    raw = list(scan[YEAR])
    events = [rft.normalize_event(row) for row in raw]
    req(len(events) == len(raw), "event normalization changed event count")
    req(all(not (BLIND[0] <= e["sol"] <= BLIND[1]) for e in events), "protected region survived parser")
    req(all(str(e["id"]).startswith(str(YEAR)) for e in events), "non-2023 event reached holdout")
    req(all(str(eid).startswith(str(YEAR)) for eid in hidden), "non-2023 label reached holdout")

    # Exactly one unchanged RFT v1 held-out catalogue; no ablations are authorized on GMN 2023.
    fams = rft.generate(events, ownership=True, do_trim=True, do_persistence=True)
    m = rft.metrics(fams, hidden)

    numerical_gates = {
        "qualified_matches_ge_120": bool(int(m["qualified_matches"]) >= 120),
        "recovered_at_100_ge_58": bool(int(m["recovered_at_100"]) >= 58),
        "recovered_at_50_ge_35": bool(int(m["recovered_at_50"]) >= 35),
        "top100_dominant_precision_ge_0p65": bool(float(m["top100_dominant_precision"]) >= 0.65),
        "fragmentation_median_top500_le_3": bool(float(m["fragmentation_median_top500"]) <= 3.0),
    }
    passed_count = sum(bool(v) for v in numerical_gates.values())
    if passed_count == 5:
        verdict = "PASS_RFT_V1_GMN2023_HELDOUT"
    elif passed_count >= 4 and int(m["recovered_at_100"]) >= 52:
        verdict = "USEFUL_BUT_INSUFFICIENT_RFT_V1_GMN2023_HELDOUT"
    else:
        verdict = "FAIL_RFT_V1_GMN2023_HELDOUT"

    failure_classes = {
        "coverage_failure": bool(int(m["qualified_matches"]) < 120),
        "ranking_failure": bool(int(m["qualified_matches"]) >= 120 and int(m["recovered_at_100"]) < 58),
        "fragmentation_failure": bool(float(m["fragmentation_median_top500"]) > 3.0),
        "purity_failure": bool(float(m["top100_dominant_precision"]) < 0.65),
    }

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2023_ONE_SHOT_HELDOUT_ONLY",
        "development_result_sha256": dev_sha,
        "parent_rft_protocol_blob": RFT_PROTOCOL_BLOB,
        "parent_rft_implementation_blob": RFT_IMPLEMENTATION_BLOB,
        "events": len(events),
        "retained_candidates": len(fams),
        "metrics": m,
        "numerical_gates": numerical_gates,
        "numerical_gates_passed": passed_count,
        "failure_classes": failure_classes,
        "active_failure_class_count": sum(bool(v) for v in failure_classes.values()),
        "candidate_order_sha256": hashlib.sha256("\n".join(f["family_id"] for f in fams).encode()).hexdigest(),
        "frozen_constants": {
            "bin_width_deg": rft.BIN_WIDTH,
            "knn": rft.KNN,
            "min_atom": rft.MIN_ATOM,
            "min_strata": rft.MIN_STRATA,
            "min_span_deg": rft.MIN_SPAN,
            "min_events": rft.MIN_EVENTS,
            "perturb_replicas": rft.PERTURB_REPLICAS,
            "perturb_radiant_sigma_deg": rft.PERTURB_RAD_DEG,
            "perturb_speed_sigma_frac": rft.PERTURB_SPEED_FRAC,
            "persistence_jaccard": rft.PERSIST_JACCARD,
            "persistence_min": rft.PERSIST_MIN,
            "trajectory_trim": rft.TRAJECTORY_TRIM,
        },
        "gmn_2022_reused_for_selection_after_holdout": False,
        "gmn_2023_ablation_run": False,
        "parameter_search": False,
        "threshold_search": False,
        "score_change": False,
        "candidate_change": False,
        "rerank_used": False,
        "source_quota_selected": False,
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "blind_exclusion": [20.0, 55.0],
    }
    (a.output / "RFT_V1_GMN2023_HELDOUT.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    (a.output / "rft_v1_gmn2023_candidates.json").write_text(json.dumps(fams, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "events": len(events),
        "candidates": len(fams),
        "metrics": {k: v for k, v in m.items() if k != "first_rank_by_label"},
        "numerical_gates": numerical_gates,
        "failure_classes": failure_classes,
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
