#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

YEARS = (2017, 2019)
CORPUS = "sonotaco-2017-2019-promoted-v8-transfer-baseline"
BLIND = [20.0, 55.0]
ARCHIVE_SHA256 = {
    2017: "1db43348806a44490fde8936529541754411b16825f2caea240378cda11c77cf",
    2019: "d49c37f5a9f7f089973d7029b840283f26ca9d915c137152a6f4368bbf5aabb4",
}
MAPPING_AUDIT_SHA256 = "f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778"
V8_SOURCE_COMMIT = "c9d6c44704013ba0c9430100e98a29a56b453304"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def hidden_geometry(event: dict[str, Any], year: int) -> dict[str, Any]:
    return {
        "id": str(event["id"]),
        "year": int(year),
        "sol": float(event["sol"]),
        "sun_lon": float(event["sun_lon"]),
        "ecl_lat": float(event["ecl_lat"]),
        "vg": float(event["vg"]),
        "iau": 0,
        "complex_key": "HIDDEN",
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--v8-runner", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--parser-2017", required=True, type=Path)
    p.add_argument("--parser-2019", required=True, type=Path)
    p.add_argument("--mapping-audit", required=True, type=Path)
    p.add_argument("--archive-2017", required=True, type=Path)
    p.add_argument("--archive-2019", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def recovery_at(per_label: list[dict[str, Any]], k: int) -> int:
    return int(sum(bool(row.get("qualified", False)) and row.get("rank") is not None and int(row["rank"]) <= k for row in per_label))


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    require(sha256_file(args.mapping_audit) == MAPPING_AUDIT_SHA256, "mapping audit hash changed")
    archives = {2017: args.archive_2017, 2019: args.archive_2019}
    parsers = {2017: args.parser_2017, 2019: args.parser_2019}
    for year in YEARS:
        require(sha256_file(archives[year]) == ARCHIVE_SHA256[year], f"archive hash changed {year}")

    v8 = load_module(args.v8_runner, "orbittrace_exact_promoted_v8_transfer")
    v8.YEARS = YEARS
    v8.MONTH_KEYS = tuple()
    require(all(v8.mult.v3.self_test().values()), "v3 self-test failed")
    require(all(v8.mult.brown.self_test().values()), "Brown self-test failed")
    runtime = v8.mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = tuple()
    support.CORPUS = CORPUS
    support.RANKING_VARIANTS = ("persistence", "mean_year_strength", "sqrt_support_strength", "min_year_strength", "size_penalized_strength")
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "blind interval changed")
    require(int(support.MIN_FAMILY_YEARS) == 2, "family-year minimum changed")
    require(abs(float(support.FAMILY_LINK_RADIUS) - 1.5) <= 1e-15, "family link radius changed")
    require(int(support.MIN_COMPONENT_EVENTS) == 4 and int(support.MIN_COMPONENT_QUARTETS) == 2, "component gates changed")
    require(int(support.MIN_ANCHOR_COUNT) == v8.v6.MIN_ANCHOR_COUNT, "minimum anchor count changed")
    require(int(support.MAX_QUARTETS_PER_BIN) == v8.v6.MAX_QUARTETS_PER_BIN, "quartet cap changed")
    _candidate, base, _scorer = support.load_sources(args)
    require(abs(float(getattr(_candidate, "CANDIDATE_SCALE", 4.0)) - 4.0) <= 1e-15, "fixed4 candidate scale changed")

    scan_by_year: dict[int, list[dict[str, Any]]] = {}
    hidden_labels: dict[str, str] = {}
    parser_audits: dict[str, Any] = {}
    seen: set[str] = set()
    for year in YEARS:
        parser = load_module(parsers[year], f"orbittrace_v8_transfer_parser_{year}")
        require(int(parser.YEAR) == year, f"parser year mismatch {year}")
        require(float(parser.BLIND_SOLAR_MIN) == 20.0 and float(parser.BLIND_SOLAR_MAX) == 55.0, f"parser blind changed {year}")
        labeled, sporadic, audit = getattr(parser, f"parse_sonotaco_{year}_events")(archives[year], args.mapping_audit, base)
        require(isinstance(audit.get("gates"), dict) and all(audit["gates"].values()), f"catalogue-v6 transport parser gates failed {year}")
        require("at_least_30_supported_native_codes" not in audit["gates"], "obsolete fixed4 code gate remained fatal")
        scan: list[dict[str, Any]] = []
        for event in labeled:
            event_id = str(event["id"])
            require(event_id not in seen, f"duplicate event id {event_id}")
            seen.add(event_id)
            label = str(event.get("complex_key", "")).strip()
            require(label and label != "SPORADIC", f"mapped label missing {event_id}")
            hidden_labels[event_id] = label
            scan.append(hidden_geometry(event, year))
        for event in sporadic:
            event_id = str(event["id"])
            require(event_id not in seen, f"duplicate event id {event_id}")
            seen.add(event_id)
            hidden_labels[event_id] = "SPORADIC"
            scan.append(hidden_geometry(event, year))
        scan.sort(key=lambda e: (float(e["sol"]), str(e["id"])))
        require(all(not (20.0 <= float(e["sol"]) <= 55.0) for e in scan), f"target interval entered v8 scan {year}")
        scan_by_year[year] = scan
        parser_audits[str(year)] = {
            "gates": dict(audit["gates"]),
            "fixed4_supported_native_code_gate_report_only": bool(audit["fixed4_supported_native_code_gate_report_only"]),
            "counts": dict(audit["counts"]),
            "native_syntax_fraction": float(audit["native_syntax_fraction"]),
            "mapped_nonbackground_fraction": float(audit["mapped_nonbackground_fraction"]),
        }

    components: list[dict[str, Any]] = []
    scan_audits: list[dict[str, Any]] = []
    retained_quartets: dict[str, int] = {}
    for year in YEARS:
        audit, passing, year_components = v8.v6.label_free_scan_year(year, scan_by_year[year], support, base)
        require(audit["source_labels_used_for_proposals"] is False, f"labels entered v8 proposals {year}")
        require(audit["score_threshold_applied"] is False, f"score threshold entered v8 proposals {year}")
        scan_audits.append(audit)
        retained_quartets[str(year)] = len(passing)
        components.extend(year_components)
        print(f"V8_TRANSFER_YEAR year={year} quartets={len(passing)} components={len(year_components)}", flush=True)

    families, support_rankings = support.build_families(components, base)
    persistence_order = [str(x) for x in support_rankings["persistence"]]
    require(set(persistence_order) == {str(f["family_id"]) for f in families}, "persistence universe mismatch")
    repair = v8.repair_year_centroids(families, components, scan_by_year, support, base)

    v8.mult.YEARS = YEARS
    v8.mult.MONTH_KEYS = tuple()
    v8.mult.TOP_K = 100
    scored, scoring_summary = v8.mult.score_families(families, scan_by_year, runtime, base)
    multiplicity_order = v8.mult.rank_scored(scored, "multiplicity")
    require(len(multiplicity_order) == len(families), "not every v8 family ranked")
    pretruth_payload = {
        "years": list(YEARS),
        "family_ids": [str(f["family_id"]) for f in families],
        "multiplicity_order": list(multiplicity_order),
        "family_event_ids": {str(f["family_id"]): list(f["event_ids"]) for f in families},
        "repair": repair,
        "scoring_summary": scoring_summary,
    }
    pretruth_sha = canonical_sha(pretruth_payload)

    metrics_full = v8.mult.evaluate_order(hidden_labels, families, multiplicity_order)
    metrics = {k: v for k, v in metrics_full.items() if k != "per_label"}
    metrics["recovered_at_25"] = recovery_at(metrics_full["per_label"], 25)
    metrics["recovered_at_50"] = recovery_at(metrics_full["per_label"], 50)
    metrics["recovered_at_100"] = recovery_at(metrics_full["per_label"], 100)
    integrity = {
        "target_interval_absent": all(all(not (20.0 <= float(e["sol"]) <= 55.0) for e in scan_by_year[y]) for y in YEARS),
        "labels_not_used_for_proposals": all(a["source_labels_used_for_proposals"] is False for a in scan_audits),
        "no_score_threshold_in_core_generation": all(a["score_threshold_applied"] is False for a in scan_audits),
        "all_recurrent_families_span_both_years": all(sorted(int(y) for y in f["years"]) == list(YEARS) for f in families),
        "all_local_episode_sizes_exact_128": scoring_summary["episode_sizes"] == [128] if families else True,
        "brown_equivalence_within_1e_10": float(scoring_summary["max_brown_equivalence_difference"]) <= 1e-10,
        "rank_frozen_before_label_evaluation": len(pretruth_sha) == 64,
        "exact_promoted_v8_source_commit_required_by_execution": True,
    }
    require(all(integrity.values()), f"v8 transfer integrity failed: {integrity}")
    result = {
        "verdict": "PASS_PROMOTED_V8_SONOTACO_2017_2019_SAME_UNIVERSE_BASELINE",
        "classification": "exact promoted-v8 no-retuning baseline on catalogue-v6 transfer universe",
        "years": list(YEARS),
        "blind_exclusion": BLIND,
        "v8_source_commit": V8_SOURCE_COMMIT,
        "archive_sha256": {str(y): ARCHIVE_SHA256[y] for y in YEARS},
        "parser_audits": parser_audits,
        "scan_events": {str(y): len(scan_by_year[y]) for y in YEARS},
        "retained_quartets": retained_quartets,
        "component_count": len(components),
        "family_count": len(families),
        "pretruth_ranking_sha256": pretruth_sha,
        "metrics": metrics,
        "integrity": integrity,
        "target_information_accessed": False,
    }
    out = args.output / "promoted_v8_sonotaco_2017_2019_baseline.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("PROMOTED_V8_TRANSFER_BASELINE_BEGIN")
    print(json.dumps({"family_count": len(families), "metrics": metrics, "pretruth_sha256": pretruth_sha}, indent=2, sort_keys=True))
    print("PROMOTED_V8_TRANSFER_BASELINE_END")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
