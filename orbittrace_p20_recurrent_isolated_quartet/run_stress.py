#!/usr/bin/env python3
"""Preregistered deterministic-thinning stress battery for exact frozen P20."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from orbittrace_label_free_sparse_support_v6 import run_development as v6
from orbittrace_pooled_year_centroid_v8 import run_development as v8
from orbittrace_p20_recurrent_isolated_quartet import run_development as p20

mult = v6.mult

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1, 13))
CORPUS = "orbittrace-p20-preregistered-thinning-stress"
BLIND = (20.0, 55.0)
EXPECTED_V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
PANELS = (
    ("P20-STRESS-A-10", "P20-STRESS-A", 0.10),
    ("P20-STRESS-B-10", "P20-STRESS-B", 0.10),
    ("P20-STRESS-A-20", "P20-STRESS-A", 0.20),
    ("P20-STRESS-B-20", "P20-STRESS-B", 0.20),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--support-source-parts", type=Path, required=True)
    parser.add_argument("--candidate-payload", type=Path, required=True)
    parser.add_argument("--baseline-payload", type=Path, required=True)
    parser.add_argument("--scorer-parts", type=Path, required=True)
    parser.add_argument("--v8-result-json", type=Path, required=True)
    parser.add_argument("--p20-primary-result-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def retained_by_hash(event_id: str, salt: str, drop_fraction: float) -> bool:
    digest = hashlib.sha256(f"{salt}|{event_id}".encode()).digest()
    numerator = int.from_bytes(digest[:8], byteorder="big", signed=False)
    u = numerator / float(1 << 64)
    return u >= drop_fraction


def thin_panel(
    scan_by_year: dict[int, list[dict[str, Any]]],
    hidden_labels: dict[str, str],
    salt: str,
    drop_fraction: float,
) -> tuple[dict[int, list[dict[str, Any]]], dict[str, str], dict[str, Any]]:
    thinned: dict[int, list[dict[str, Any]]] = {}
    retained_ids: set[str] = set()
    manifest: dict[str, Any] = {
        "salt": salt,
        "drop_fraction": float(drop_fraction),
        "years": {},
    }
    for year in YEARS:
        rows = [
            event for event in scan_by_year[year]
            if retained_by_hash(str(event["id"]), salt, drop_fraction)
        ]
        rows.sort(key=lambda event: str(event["id"]))
        thinned[year] = rows
        ids = [str(event["id"]) for event in rows]
        retained_ids.update(ids)
        manifest["years"][str(year)] = {
            "input_events": len(scan_by_year[year]),
            "retained_events": len(rows),
            "retained_id_sha256": canonical_sha(ids),
        }
    restricted_labels = {
        str(event_id): label
        for event_id, label in hidden_labels.items()
        if str(event_id) in retained_ids
    }
    manifest["all_retained_ids_sha256"] = canonical_sha(sorted(retained_ids))
    manifest["manifest_sha256"] = canonical_sha(manifest)
    return thinned, restricted_labels, manifest


def panel_run(
    panel_id: str,
    salt: str,
    drop_fraction: float,
    scan_by_year: dict[int, list[dict[str, Any]]],
    hidden_labels: dict[str, str],
    support: Any,
    runtime: Any,
    base: Any,
) -> dict[str, Any]:
    thinned, labels, thinning = thin_panel(scan_by_year, hidden_labels, salt, drop_fraction)
    require(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for year in YEARS for e in thinned[year]),
            f"target-region event survived inherited exclusion in {panel_id}")

    components: list[dict[str, Any]] = []
    components_by_year: dict[int, list[dict[str, Any]]] = {}
    passing_by_year: dict[int, list[dict[str, Any]]] = {}
    scan_audits: list[dict[str, Any]] = []
    for year in YEARS:
        audit, passing, year_components = v6.label_free_scan_year(year, thinned[year], support, base)
        scan_audits.append(audit)
        passing_by_year[year] = passing
        components_by_year[year] = year_components
        components.extend(year_components)

    hard_families, _support_rankings = support.build_families(components, base)
    repair = v8.repair_year_centroids(hard_families, components, thinned, support, base)
    mult.YEARS = YEARS
    mult.MONTH_KEYS = MONTH_KEYS
    mult.TOP_K = 100
    hard_scored, hard_scoring = mult.score_families(hard_families, thinned, runtime, base)
    hard_order = mult.rank_scored(hard_scored, "multiplicity")
    require(len(hard_order) == len(hard_families), f"hard order incomplete in {panel_id}")

    isolated_by_year: dict[int, list[dict[str, Any]]] = {}
    isolated_audits: dict[str, Any] = {}
    for year in YEARS:
        quartets, audit = p20.isolated_quartets(
            year,
            passing_by_year[year],
            components_by_year[year],
            thinned[year],
            support,
        )
        isolated_by_year[year] = quartets
        isolated_audits[str(year)] = audit

    soft_families, soft_diagnostics = p20.build_recurrent_isolated_quartets(
        isolated_by_year, support, base
    )
    combined_families = hard_families + soft_families
    combined_order = hard_order + [str(f["family_id"]) for f in soft_families]
    require(combined_order[:len(hard_order)] == hard_order, f"hard prefix changed in {panel_id}")
    require(len(combined_order) == len(combined_families), f"order/family mismatch in {panel_id}")

    prelabel_payload = {
        "panel_id": panel_id,
        "thinning_manifest": thinning,
        "hard_order": hard_order,
        "hard_families": [p20.structural_family_payload(f) for f in hard_families],
        "isolated_quartets": {str(year): isolated_by_year[year] for year in YEARS},
        "soft_families": [p20.structural_family_payload(f) for f in soft_families],
        "isolated_audits": isolated_audits,
        "soft_diagnostics": soft_diagnostics,
    }
    prelabel_sha = canonical_sha(prelabel_payload)

    # FIRST LABEL USE FOR THIS PANEL.
    baseline = mult.evaluate_order(labels, hard_families, hard_order)
    challenger = mult.evaluate_order(labels, combined_families, combined_order)
    baseline_annual = p20.annual_bin_metrics(labels, hard_families)
    challenger_annual = p20.annual_bin_metrics(labels, combined_families)
    annual_delta = p20.delta_bins(challenger_annual, baseline_annual)
    combined_delta = {
        str(year): float(
            p20.combined_4_24_mean(challenger_annual, year)
            - p20.combined_4_24_mean(baseline_annual, year)
        )
        for year in YEARS
    }

    retained_component_events = {
        year: {str(eid) for c in components_by_year[year] for eid in c["event_ids"]}
        for year in YEARS
    }
    integrity = {
        "target_region_absent_after_thinning": all(
            not (BLIND[0] <= float(e["sol"]) <= BLIND[1])
            for year in YEARS for e in thinned[year]
        ),
        "hard_order_is_complete_prefix": combined_order[:len(hard_order)] == hard_order,
        "all_isolated_quartets_exactly_four": all(
            len(q["quartet_ids"]) == 4 for year in YEARS for q in isolated_by_year[year]
        ),
        "all_isolated_quartets_zero_component_overlap": all(
            not (set(q["quartet_ids"]) & retained_component_events[year])
            for year in YEARS for q in isolated_by_year[year]
        ),
        "all_soft_membership_exact_4plus4": all(int(f["event_count"]) == 8 for f in soft_families),
        "all_soft_distances_within_inherited_1_5": bool(
            soft_diagnostics["all_pair_distances_within_inherited_1_5"]
        ),
        "membership_expansion_false": soft_diagnostics["membership_expansion"] is False,
        "recursion_false": soft_diagnostics["recursion"] is False,
        "new_scientific_radius_false": soft_diagnostics["new_scientific_radius"] is False,
        "prelabel_payload_frozen": bool(prelabel_sha),
        "no_target_information_access": True,
    }
    panel_gates = {
        "hard_family_universe_nonempty": len(hard_families) > 0,
        "p20_soft_path_nonempty": len(soft_families) > 0,
        "qualified_nonregression": int(challenger["qualified_matches"]) >= int(baseline["qualified_matches"]),
        "recovery100_nonregression": int(challenger["recovered_at_100"]) >= int(baseline["recovered_at_100"]),
        "top100_precision_equal_within_1e12": abs(
            float(challenger["top100_dominant_precision"])
            - float(baseline["top100_dominant_precision"])
        ) <= 1e-12,
        "macro_f1_strict_gain": float(challenger["macro_f1"]) > float(baseline["macro_f1"]),
        "combined_4_24_gain_both_years": all(combined_delta[str(year)] > 0.0 for year in YEARS),
        "evaluable_4_9_both_years": all(
            int(baseline_annual[str(year)]["4-9"]["showers"]) > 0 for year in YEARS
        ),
        "sparse_4_9_gain_both_years": all(annual_delta[str(year)]["4-9"] > 0.0 for year in YEARS),
        "sparse_4_9_no_decrement_below_minus_002": all(
            annual_delta[str(year)]["4-9"] >= -0.02 for year in YEARS
        ),
    }
    return {
        "panel_id": panel_id,
        "salt": salt,
        "drop_fraction": float(drop_fraction),
        "thinning_manifest": thinning,
        "scan_audits": scan_audits,
        "hard_family_count": len(hard_families),
        "isolated_quartet_count_by_year": {
            str(year): len(isolated_by_year[year]) for year in YEARS
        },
        "soft_family_count": len(soft_families),
        "prelabel_payload_sha256": prelabel_sha,
        "centroid_repair": repair,
        "hard_scoring_summary": hard_scoring,
        "baseline_metrics": {k: v for k, v in baseline.items() if k != "per_label"},
        "p20_metrics": {k: v for k, v in challenger.items() if k != "per_label"},
        "baseline_annual": baseline_annual,
        "p20_annual": challenger_annual,
        "annual_mean_f1_delta": annual_delta,
        "combined_4_24_mean_f1_delta": combined_delta,
        "integrity_gates": integrity,
        "panel_gates": panel_gates,
    }


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    raw_v8 = args.v8_result_json.read_bytes()
    require(hashlib.sha256(raw_v8).hexdigest() == EXPECTED_V8_RESULT_SHA256, "v8 result hash changed")
    v8_result = json.loads(raw_v8)
    require(v8_result["verdict"] == "PASS_POOLED_YEAR_CENTROID_V8_DEVELOPMENT", "v8 predecessor did not pass")

    primary = json.loads(args.p20_primary_result_json.read_text())
    require(primary["verdict"] == "PASS_P20_RECURRENT_ISOLATED_QUARTET_DEVELOPMENT", "P20 primary did not pass; stress must remain dormant")
    require(primary["configuration"]["years"] == [2022, 2023], "P20 primary years changed")
    require(primary["configuration"]["blind_exclusion"] == [20.0, 55.0], "P20 primary blind interval changed")
    require(primary["v8_predecessor"]["result_sha256"] == EXPECTED_V8_RESULT_SHA256, "P20 primary v8 ancestry changed")
    require(all(primary["integrity_gates"].values()), "P20 primary integrity failed")
    require(all(primary["scientific_gates"].values()), "P20 primary scientific gate did not pass")

    require(all(mult.v3.self_test().values()), "v3 self-test failed")
    require(all(mult.brown.self_test().values()), "Brown self-test failed")
    runtime = mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = CORPUS
    support.RANKING_VARIANTS = ("persistence",)
    require(float(support.BLIND_LOW) == BLIND[0] and float(support.BLIND_HIGH) == BLIND[1], "target exclusion changed")
    require(abs(float(support.FAMILY_LINK_RADIUS) - 1.5) < 1e-15, "family-link radius changed")
    require(int(support.MIN_COMPONENT_EVENTS) == 4, "component event floor changed")
    require(int(support.MIN_COMPONENT_QUARTETS) == 2, "component quartet floor changed")
    require(int(support.MIN_ANCHOR_COUNT) == 2, "retained anchor gate changed")
    require(int(support.MAX_QUARTETS_PER_BIN) == 512, "retained quartet cap changed")

    setattr(args, "fixed4_baseline_json", args.v8_result_json)
    _candidate, base, _scorer = support.load_sources(args)

    # FIRST DEVELOPMENT-CATALOGUE ACCESS. The inherited parser removes 20-55 first.
    scan_by_year, _calibration_by_year, hidden_labels, catalogue_sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "stress year universe changed")
    require(all(
        not (BLIND[0] <= float(e["sol"]) <= BLIND[1])
        for year in YEARS for e in scan_by_year[year]
    ), "target-region event survived inherited parser")

    panel_results = [
        panel_run(panel_id, salt, drop_fraction, scan_by_year, hidden_labels, support, runtime, base)
        for panel_id, salt, drop_fraction in PANELS
    ]

    all_integrity = all(all(panel["integrity_gates"].values()) for panel in panel_results)
    all_nonempty = all(
        panel["panel_gates"]["hard_family_universe_nonempty"]
        and panel["panel_gates"]["p20_soft_path_nonempty"]
        and panel["panel_gates"]["evaluable_4_9_both_years"]
        for panel in panel_results
    )
    sparse_positive_panels = sum(
        1 for panel in panel_results if panel["panel_gates"]["sparse_4_9_gain_both_years"]
    )
    stress_gates = {
        "all_integrity_and_target_firewalls_pass": all_integrity,
        "all_panels_structurally_interpretable": all_nonempty,
        "qualified_nonregression_all_four": all(panel["panel_gates"]["qualified_nonregression"] for panel in panel_results),
        "recovery100_nonregression_all_four": all(panel["panel_gates"]["recovery100_nonregression"] for panel in panel_results),
        "top100_precision_equal_all_four": all(panel["panel_gates"]["top100_precision_equal_within_1e12"] for panel in panel_results),
        "macro_f1_gain_all_four": all(panel["panel_gates"]["macro_f1_strict_gain"] for panel in panel_results),
        "combined_4_24_gain_both_years_all_four": all(panel["panel_gates"]["combined_4_24_gain_both_years"] for panel in panel_results),
        "sparse_4_9_gain_both_years_at_least_three_of_four": sparse_positive_panels >= 3,
        "no_sparse_4_9_decrement_below_minus_002": all(
            panel["panel_gates"]["sparse_4_9_no_decrement_below_minus_002"]
            for panel in panel_results
        ),
        "no_target_information_access": True,
    }
    passed = all(stress_gates.values())
    verdict = "PASS_P20_PREREGISTERED_THINNING_STRESS" if passed else "FAIL_P20_PREREGISTERED_THINNING_STRESS"
    result = {
        "verdict": verdict,
        "configuration": {
            "years": list(YEARS),
            "blind_exclusion": list(BLIND),
            "panels": [
                {"panel_id": panel_id, "salt": salt, "drop_fraction": drop_fraction}
                for panel_id, salt, drop_fraction in PANELS
            ],
            "thinning_position": "after inherited target exclusion and before fixed4 proposal generation",
            "hash_rule": "uint64_be(SHA256(salt|event_id)[0:8])/2^64",
            "method_change": False,
            "parameter_search": False,
            "variant_search": False,
        },
        "v8_result_sha256": EXPECTED_V8_RESULT_SHA256,
        "p20_primary_verdict": primary["verdict"],
        "catalogue_sources": catalogue_sources,
        "panels": panel_results,
        "sparse_positive_panel_count": int(sparse_positive_panels),
        "stress_gates": stress_gates,
        "claim_boundary": (
            "Preregistered deterministic thinning of the already target-excluded GMN 2022/2023 development panel. "
            "Exact frozen P20 and within-panel v8 are recomputed on identical retained event IDs. No final-test, "
            "external, target-region, or OrbitTrace target scientific value is accessed."
        ),
    }
    (args.output / "p20_preregistered_thinning_stress.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    lines = [
        "# OrbitTrace P20 preregistered thinning stress",
        "",
        f"**Verdict:** `{verdict}`",
        "",
    ]
    for panel in panel_results:
        b = panel["baseline_metrics"]
        c = panel["p20_metrics"]
        lines.extend([
            f"## {panel['panel_id']}",
            f"- hard / soft families: **{panel['hard_family_count']} / {panel['soft_family_count']}**",
            f"- qualified: **{b['qualified_matches']} -> {c['qualified_matches']}**",
            f"- recovery@100: **{b['recovered_at_100']} -> {c['recovered_at_100']}**",
            f"- macro F1: **{b['macro_f1']:.6f} -> {c['macro_f1']:.6f}**",
            f"- 2022 / 2023 4–9 deltas: **{panel['annual_mean_f1_delta']['2022']['4-9']:+.6f} / {panel['annual_mean_f1_delta']['2023']['4-9']:+.6f}**",
            "",
        ])
    lines.append("No OrbitTrace target information or target-region event was accessed.")
    (args.output / "P20_PREREGISTERED_THINNING_STRESS.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
