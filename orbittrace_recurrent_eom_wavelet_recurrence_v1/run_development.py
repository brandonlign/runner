#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np

from wavelet_recurrence import candidate_wavelet_recurrence

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
PARENT_PRELABEL_SHA256 = "e304f6660697ed27a7e2e546ba2b9f2ecdb43f923745cb7424a3781ad55b9ad1"
PARENT_RESULT_SHA256 = "433c641f57122b244b9476f5cbcb5e6f82956d9467270a9f24945600a32d2106"
V3_SOURCE_BLOB = "2ba4835db23f8f623cdd28d0a4e6113b7954ecb2"
PARENT_TOTAL_RECOVERED_100 = 178
REQUIRED_TOTAL_RECOVERED_100_GAIN = 2


def req(cond: bool, msg: str) -> None:
    if not cond:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def membership_signature(rows: list[dict[str, Any]]) -> list[tuple[str, ...]]:
    return [tuple(sorted(str(x) for x in row["event_ids"])) for row in rows]


def membership_universe(rows: list[dict[str, Any]]) -> set[tuple[str, ...]]:
    return set(membership_signature(rows))


def make_successor(
    binding_candidates: list[dict[str, Any]],
    event_by_id: dict[str, dict[str, Any]],
    v3: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    out: list[dict[str, Any]] = []
    scores: list[float] = []
    e22: list[float] = []
    e23: list[float] = []
    zero_scores = 0
    under_four_2022 = 0
    under_four_2023 = 0

    for ordinal, source in enumerate(binding_candidates):
        members = tuple(sorted(str(x) for x in source["event_ids"]))
        req(len(members) == int(source["member_count"]), f"binding member count mismatch at candidate {ordinal}")
        req(len(set(members)) == len(members), f"duplicate event ID inside candidate {ordinal}")
        try:
            rows = [event_by_id[eid] for eid in members]
        except KeyError as exc:
            raise RuntimeError(f"binding candidate event missing from accessible GMN rows: {exc.args[0]}") from exc

        stat = candidate_wavelet_recurrence(rows, v3)
        score = float(stat.recurrence_score)
        req(np.isfinite(score) and score >= 0.0, f"invalid wavelet recurrence score at candidate {ordinal}")

        rec = float(source["recurrent_stability"])
        ordinary = float(source["ordinary_stability"])
        out.append({
            "family_id": str(source["family_id"]),
            "node_id": int(source["node_id"]),
            "event_ids": list(members),
            "member_count": len(members),
            "ordinary_stability": ordinary,
            "recurrent_stability": rec,
            "wavelet_energy_2022": float(stat.annual_energy_2022),
            "wavelet_energy_2023": float(stat.annual_energy_2023),
            "wavelet_recurrence_score": score,
            "annual_count_2022": int(stat.annual_count_2022),
            "annual_count_2023": int(stat.annual_count_2023),
        })
        scores.append(score)
        e22.append(float(stat.annual_energy_2022))
        e23.append(float(stat.annual_energy_2023))
        zero_scores += int(score == 0.0)
        under_four_2022 += int(stat.annual_count_2022 < 4)
        under_four_2023 += int(stat.annual_count_2023 < 4)

    out.sort(key=lambda f: (
        -f["wavelet_recurrence_score"],
        -f["recurrent_stability"],
        -f["ordinary_stability"],
        -f["member_count"],
        f["family_id"],
    ))
    summary = {
        "candidate_count": len(out),
        "zero_recurrence_scores": int(zero_scores),
        "under_four_members_2022": int(under_four_2022),
        "under_four_members_2023": int(under_four_2023),
        "min_recurrence_score": float(min(scores)),
        "median_recurrence_score": float(np.median(scores)),
        "mean_recurrence_score": float(np.mean(scores)),
        "max_recurrence_score": float(max(scores)),
        "median_energy_2022": float(np.median(e22)),
        "median_energy_2023": float(np.median(e23)),
    }
    return out, summary


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--parent-runner", type=Path, required=True)
    p.add_argument("--parent-prelabel-json", type=Path, required=True)
    p.add_argument("--parent-result-json", type=Path, required=True)
    p.add_argument("--v3-source", type=Path, required=True)
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha(a.quality_source) == QUALITY_SHA, "frozen GMN runtime utility source changed")
    req(sha(a.v8_result_json) == V8_RESULT_SHA, "frozen GMN support artifact changed")
    req(sha(a.parent_prelabel_json) == PARENT_PRELABEL_SHA256, "binding recurrent prelabel artifact changed")
    req(sha(a.parent_result_json) == PARENT_RESULT_SHA256, "binding recurrent result artifact changed")

    parent = load_module(a.parent_runner, "reom_parent_runner_exact_wavelet_recurrence")
    v3 = load_module(a.v3_source, "multi_anchor_energy_v3_exact")
    req(getattr(v3, "METHOD_ID", None) == "orbittrace_multi_anchor_wavelet_energy_v3", "wrong v3 method")
    req(float(v3.ANGULAR_PROBE_DEG) == 4.0, "v3 angular scale changed")
    req(float(v3.SPEED_PROBE_FRACTION) == 0.10, "v3 speed scale changed")
    req(float(v3.TRUNCATION_RADIUS) == 4.0, "v3 truncation changed")
    req(float(v3.KERNEL_DIMENSION) == 3.0, "v3 kernel dimension changed")
    req(int(v3.TOP_ANCHORS) == 4, "v3 anchor count changed")

    binding_prelabel = json.loads(a.parent_prelabel_json.read_text())
    req(binding_prelabel["scientific_role"] == "PRELABEL_FROZEN_RECURRENT_EOM_HDBSCAN_V1",
        "binding recurrent prelabel role changed")
    binding_candidates = list(binding_prelabel["successor_candidates"])
    req(len(binding_candidates) == 2097, f"binding recurrent candidate count changed: {len(binding_candidates)}")
    req(len(membership_universe(binding_candidates)) == 2097, "binding recurrent membership universe contains duplicates")

    qmod = parent.load_module(a.quality_source, "wavelet_recurrence_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-recurrent-eom-wavelet-recurrence-v1-development-2022-2023-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_sealed, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), f"GMN runtime accessed wrong years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        rows = [parent.normalize_event(row, year) for row in raw]
        req(len(rows) == len(raw), f"event normalization changed {year} event count")
        events.extend(rows)
    req(len(events) == 738682, f"pooled accessible event count changed: {len(events)}")
    req(sum(int(e["year"]) == 2022 for e in events) == 315024, "2022 accessible event count changed")
    req(sum(int(e["year"]) == 2023 for e in events) == 423658, "2023 accessible event count changed")
    req(len({str(e["id"]) for e in events}) == len(events), "duplicate pooled accessible event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected region survived parser")

    # Engineering-only identity alias required by the exact frozen v3 episode
    # interface. Parent `lon`/`lat` are already sun-centered radiant longitude
    # and ecliptic latitude; no values or units are changed here.
    scoring_events = [dict(e, sun_lon=float(e["lon"]), ecl_lat=float(e["lat"])) for e in events]
    req(all(float(e["sun_lon"]) == float(e["lon"]) for e in scoring_events), "sun-longitude alias changed values")
    req(all(float(e["ecl_lat"]) == float(e["lat"]) for e in scoring_events), "ecliptic-latitude alias changed values")
    event_by_id = {str(e["id"]): e for e in scoring_events}

    binding_member_ids = [str(eid) for row in binding_candidates for eid in row["event_ids"]]
    req(all(eid in event_by_id for eid in binding_member_ids), "binding candidate contains inaccessible/missing GMN event")

    successor_candidates, score_summary = make_successor(binding_candidates, event_by_id, v3)
    req(len(successor_candidates) == 2097, "rank-only successor candidate count changed")
    req(membership_universe(successor_candidates) == membership_universe(binding_candidates),
        "rank-only successor changed recurrent membership universe")
    mechanism_active = membership_signature(successor_candidates) != membership_signature(binding_candidates)

    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_RECURRENT_EOM_WAVELET_RECURRENCE_V1",
        "parent_prelabel_sha256": PARENT_PRELABEL_SHA256,
        "events_total": len(events),
        "events_by_year": {"2022": 315024, "2023": 423658},
        "candidate_count": 2097,
        "membership_universe_identical": True,
        "mechanism_active": bool(mechanism_active),
        "score_summary": score_summary,
        "parent_candidates": binding_candidates,
        "successor_candidates": successor_candidates,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "RECURRENT_EOM_WAVELET_RECURRENCE_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    # Truth is inspected only after the full successor order has been persisted.
    binding_result = json.loads(a.parent_result_json.read_text())
    req(binding_result["verdict"] == "PASS_RECURRENT_EOM_HDBSCAN_V1_GMN_DEVELOPMENT",
        "wrong binding recurrent parent result")
    hidden = hidden_sealed
    ids_by_year = {y: {str(e["id"]) for e in events if int(e["year"]) == y} for y in YEARS}
    req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden),
        "shower truth contains ID outside accessible pooled events")

    parent_metrics = {str(y): parent.metrics(binding_candidates, hidden, ids_by_year[y]) for y in YEARS}
    successor_metrics = {str(y): parent.metrics(successor_candidates, hidden, ids_by_year[y]) for y in YEARS}
    req(parent_metrics == binding_result["successor_metrics"],
        "binding recurrent parent metrics failed exact reproduction")

    annual_gates = {str(y): parent.annual_gate(parent_metrics[str(y)], successor_metrics[str(y)]) for y in YEARS}
    parent_total_100 = sum(int(parent_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    successor_total_100 = sum(int(successor_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    req(parent_total_100 == PARENT_TOTAL_RECOVERED_100, f"binding parent @100 total changed: {parent_total_100}")
    total_100_gain = successor_total_100 - parent_total_100
    strong_recovery_gate = total_100_gain >= REQUIRED_TOTAL_RECOVERED_100_GAIN
    passed = bool(
        mechanism_active
        and strong_recovery_gate
        and all(all(g.values()) for g in annual_gates.values())
    )
    verdict = (
        "PASS_RECURRENT_EOM_WAVELET_RECURRENCE_V1_GMN_DEVELOPMENT"
        if passed
        else "FAIL_RECURRENT_EOM_WAVELET_RECURRENCE_V1_GMN_DEVELOPMENT"
    )

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "prelabel_sha256": prelabel_sha,
        "parent_prelabel_sha256": PARENT_PRELABEL_SHA256,
        "parent_result_sha256": PARENT_RESULT_SHA256,
        "events_total": len(events),
        "events_by_year": {str(y): len(ids_by_year[y]) for y in YEARS},
        "candidate_count": 2097,
        "membership_universe_identical": True,
        "mechanism_active": bool(mechanism_active),
        "parent_total_recovered_at_100": int(parent_total_100),
        "successor_total_recovered_at_100": int(successor_total_100),
        "total_recovered_at_100_gain": int(total_100_gain),
        "required_total_recovered_at_100_gain": REQUIRED_TOTAL_RECOVERED_100_GAIN,
        "strong_recovery_gate": bool(strong_recovery_gate),
        "score_summary": score_summary,
        "parent_metrics": parent_metrics,
        "successor_metrics": successor_metrics,
        "annual_gates": annual_gates,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    result_path = a.output / "RECURRENT_EOM_WAVELET_RECURRENCE_V1_GMN_DEVELOPMENT.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")

    def compact(m: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in m.items() if k != "first_rank_by_label"}

    print(json.dumps({
        "verdict": verdict,
        "mechanism_active": mechanism_active,
        "total_recovered_at_100_gain": total_100_gain,
        "score_summary": score_summary,
        "parent": {y: compact(m) for y, m in parent_metrics.items()},
        "successor": {y: compact(m) for y, m in successor_metrics.items()},
        "annual_gates": annual_gates,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
