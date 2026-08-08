#!/usr/bin/env python3
"""Zero-catalogue terminal synthesis for the promoted OrbitTrace v8 external track."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

TERMINAL = "INCONCLUSIVE_V8_EXTERNAL_VALIDATION_NO_POWERED_PRISTINE_PANEL"
V8_PASS = "PASS_POOLED_YEAR_CENTROID_V8_DEVELOPMENT"
SAAMER20 = "INCONCLUSIVE_LABEL_FREE_V6_SAAMER_EXTERNAL_POWER"
SAAMER22 = "INCONCLUSIVE_LABEL_FREE_V6_SAAMER_2022_2023_EXTERNAL_POWER"
AMOR = "INCONCLUSIVE_V8_AMOR_EXTERNAL_POWER"
UKMON = "PASS_UKMON_2020_2021_ZERO_DATA_FRESHNESS_ADJUDICATION"
HARVARD = "FAIL_HARVARD_1968_1969_V8_RECURRENCE_ELIGIBILITY"
FRIPON = "FAIL_FRIPON_2018_2019_EXTERNAL_INTEGRITY_PREPROTOCOL_EXPOSURE"
HISSAR = "INCONCLUSIVE_V8_HISSAR_1968_1969_EXTERNAL_POWER_COVERAGE"
KNOWN_FRESHNESS_SURVEYS = (
    "amor", "cams", "camsv3", "edmond", "fripon", "harvard", "hissar",
    "saamer", "sonotaco", "ukmon",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load_exact(root: Path, filename: str, verdict: str) -> dict[str, Any]:
    path = root / filename
    require(path.is_file(), f"missing exact result file: {path}")
    obj = json.loads(path.read_text())
    require(isinstance(obj, dict), f"result is not an object: {path}")
    require(obj.get("verdict") == verdict, f"{filename} verdict changed: {obj.get('verdict')!r}")
    return obj


def orbital_q(result: dict[str, Any]) -> int:
    summary = result.get("orbital_summary", {})
    require("orbitally_corroborated_families" in summary, "missing orbital corroboration count")
    return int(summary["orbitally_corroborated_families"])


def assert_target_free_claim(result: dict[str, Any], label: str) -> None:
    direct = result.get("orbittrace_target_information_access")
    if direct is not None:
        require(direct is False, f"{label}: target-access flag not false")
        return
    claim = str(result.get("claim_boundary", ""))
    require("no orbittrace target information" in claim.lower(), f"{label}: no target-free claim found")


def inventory_freshness_refs(path: Path) -> dict[str, Any]:
    refs = [line.strip().lower() for line in path.read_text().splitlines() if line.strip()]
    freshness = sorted({r for r in refs if "orbittrace" in r and "freshness" in r})
    unknown = [r for r in freshness if not any(marker in r for marker in KNOWN_FRESHNESS_SURVEYS)]
    require(not unknown, f"unknown preregistered freshness route(s): {unknown[:20]}")
    presence = {
        marker: any(marker in r for r in freshness)
        for marker in ("amor", "cams", "edmond", "fripon", "hissar", "saamer", "sonotaco", "ukmon")
    }
    require(all(presence.values()), f"repository freshness inventory lost expected survey routes: {presence}")
    return {
        "remote_ref_count": len(refs),
        "freshness_ref_count": len(freshness),
        "unknown_freshness_routes": unknown,
        "expected_route_markers_present": presence,
        "inventory_scope": "remote branch names only; no external catalogue search",
    }


def main() -> int:
    p = argparse.ArgumentParser()
    for name in ("v8", "saamer20", "saamer22", "amor", "ukmon", "harvard", "fripon", "hissar"):
        p.add_argument(f"--{name}", required=True, type=Path)
    p.add_argument("--remote-refs", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    v8 = load_exact(a.v8, "pooled_year_centroid_v8_development.json", V8_PASS)
    s20 = load_exact(a.saamer20, "saamer_external_validation.json", SAAMER20)
    s22 = load_exact(a.saamer22, "saamer_2022_2023_external_validation.json", SAAMER22)
    amor = load_exact(a.amor, "v8_amor_1996_1998_external_validation.json", AMOR)
    ukmon = load_exact(a.ukmon, "ukmon_2020_2021_freshness_adjudication.json", UKMON)
    harvard = load_exact(a.harvard, "harvard_1968_1969_recurrence_eligibility.json", HARVARD)
    fripon = load_exact(a.fripon, "fripon_2018_2019_integrity_stop.json", FRIPON)
    hissar = load_exact(a.hissar, "hissar_v8_coverage_eligibility.json", HISSAR)

    # Promoted v8 is immutable and passed only on the target-excluded development panel.
    require(v8["configuration"]["years"] == [2022, 2023], "v8 development years changed")
    require(v8["configuration"]["blind_exclusion"] == [20.0, 55.0], "v8 blind interval changed")
    require(v8["configuration"]["family_link_radius"] == 1.5, "v8 family radius changed")
    require(v8["configuration"]["episode_size"] == 128, "v8 episode size changed")
    require(v8["configuration"]["multiplicity"] == "(multi-anchor-v3-energy / Brown-peak)^2", "v8 multiplicity changed")
    require(v8["family_count"] == 226, "v8 family universe changed")
    require(v8["metrics"]["multiplicity"]["recovered_at_100"] == 58, "v8 development multiplicity metric changed")
    require(v8["metrics"]["brown"]["recovered_at_100"] == 55, "v8 Brown metric changed")
    require(v8["metrics"]["label_free_persistence"]["recovered_at_100"] == 59, "v8 persistence metric changed")
    require(all(v8["integrity_gates"].values()), "v8 integrity gate no longer all-pass")
    require(all(v8["scientific_gates"].values()), "v8 scientific gate no longer all-pass")
    assert_target_free_claim(v8, "v8 development")

    # Inherited SAAMER power context: clean external architecture, but not direct v8 verdicts.
    require(int(s20["family_count"]) == 19 and orbital_q(s20) == 19, "SAAMER 2020/21 counts changed")
    require(s20["configuration"]["blind_exclusion"] == [20.0, 55.0], "SAAMER 2020/21 blindness changed")
    require(s20["configuration"]["no_source_labels"] is True, "SAAMER 2020/21 labels used")
    require(s20["configuration"]["no_orbits_in_candidate_or_ranking"] is True, "SAAMER 2020/21 orbit boundary changed")
    assert_target_free_claim(s20, "SAAMER 2020/21")

    require(int(s22["family_count"]) == 66 and orbital_q(s22) == 33, "SAAMER 2022/23 counts changed")
    require(s22["configuration"]["blind_exclusion"] == [20.0, 55.0], "SAAMER 2022/23 blindness changed")
    require(s22["integrity_gates"]["at_least_24_scannable_bins_each_year"] is True, "SAAMER 2022/23 coverage changed")
    require(s22["integrity_gates"]["at_least_100_recurrent_families"] is False, "SAAMER 2022/23 power reason changed")
    assert_target_free_claim(s22, "SAAMER 2022/23")

    # Direct v8 AMOR test: integrity-clean but under both immutable family-universe floors.
    require(int(amor["family_count"]) == 19 and orbital_q(amor) == 19, "AMOR v8 counts changed")
    require(amor["configuration"]["blind_exclusion"] == [20.0, 55.0], "AMOR blindness changed")
    require(all(amor["integrity_gates"].values()), "AMOR integrity no longer clean")
    require(amor["power_gates"]["at_least_100_recurrent_families"] is False, "AMOR N power reason changed")
    require(amor["power_gates"]["at_least_30_orbitally_corroborated_families"] is False, "AMOR Q power reason changed")
    require(amor["orbit_read_audit"]["orbital_elements_interpreted_only_after_rank_freeze"] is True, "AMOR orbit boundary changed")
    assert_target_free_claim(amor, "AMOR")

    # UKMON was fresh after exact-hit adjudication, but the historical interface never reached science.
    require(ukmon["raw_audit_verdict_preserved"] == "FAIL_UKMON_2020_2021_REPO_SCIENTIFIC_FRESHNESS_AUDIT", "UKMON raw audit history changed")
    require(ukmon["raw_hit_count"] == 1 and ukmon["additional_hits_forgiven"] == 0, "UKMON freshness adjudication changed")
    require(ukmon["meteor_api_contacted"] is False, "UKMON freshness contacted API")
    require(ukmon["scientific_value_access_this_adjudication"] is False, "UKMON freshness crossed science boundary")
    require(ukmon["target_information_access"] is False, "UKMON target information accessed")

    # Harvard stayed unopened and failed only the pre-scientific recurrence-panel definition.
    require(harvard["metadata_transport_sufficient"] is True, "Harvard metadata transport no longer sufficient")
    require(harvard["har6869_table_downloaded"] is False and harvard["har6869_table_opened"] is False, "Harvard event table accessed")
    require(harvard["scientific_event_values_inspected"] is False, "Harvard science accessed")
    require(harvard["method_evaluation_performed"] is False, "Harvard method evaluation occurred")
    require(harvard["orbittrace_target_information_access"] is False, "Harvard target information accessed")

    # FRIPON is terminally non-pristine; the exposure is never used to salvage or tune the method.
    require(fripon["unintended_reserved_year_web_search_exposure"] is True, "FRIPON integrity incident missing")
    require(fripon["numeric_exposed_values_copied_into_repository"] is False, "FRIPON exposed values copied")
    require(fripon["exposed_values_used_for_method_or_parser_decisions"] is False, "FRIPON exposure influenced method/parser")
    require(fripon["alternate_FRIPON_year_pair_authorized"] is False, "FRIPON post-exposure panel switching authorized")
    require(fripon["v8_scientific_evaluation_performed_on_FRIPON"] is False, "FRIPON v8 science occurred")
    require(fripon["v8_method_changed"] is False, "FRIPON changed v8")
    require(fripon["orbittrace_target_information_access"] is False, "FRIPON target information accessed")

    # Hissar is native-interface compatible but cannot mathematically meet the frozen 24-bin/year floor.
    require(hissar["frozen_min_scannable_bins_per_year"] == 24, "Hissar power floor changed")
    require(hissar["maximum_possible_1968_fixed_10deg_bins_intersected"] < 24, "Hissar metadata coverage no longer excludes powered test")
    require(hissar["coverage_gate_mathematically_possible"] is False, "Hissar coverage eligibility changed")
    require(hissar["catalogue_form_submitted"] is False and hissar["scientific_record_access"] is False, "Hissar science accessed")
    require(hissar["coverage_floor_lowered"] is False and hissar["year_panels_redefined"] is False, "Hissar rules adapted")
    require(hissar["v8_method_changed"] is False, "Hissar changed v8")
    require(hissar["orbittrace_target_information_access"] is False, "Hissar target information accessed")

    inventory = inventory_freshness_refs(a.remote_refs)

    result = {
        "verdict": TERMINAL,
        "promoted_method": "v8 pooled-year-centroid label-free sparse-support multiplicity",
        "promoted_v8_development": {
            "verdict": V8_PASS,
            "family_count": 226,
            "multiplicity_recovered_at_100": 58,
            "brown_recovered_at_100": 55,
            "persistence_recovered_at_100": 59,
            "target_excluded_years": [2022, 2023],
        },
        "external_record": {
            "saamer_2020_2021": {"role": "inherited_v6_external_power_context", "verdict": SAAMER20, "N": 19, "Q": 19},
            "saamer_2022_2023": {"role": "inherited_v6_external_power_context", "verdict": SAAMER22, "N": 66, "Q": 33},
            "amor_1996_1998": {"role": "direct_v8_external_test", "verdict": AMOR, "N": 19, "Q": 19},
            "ukmon_2020_2021": {"role": "pre_scientific_panel", "verdict": "HISTORICAL_INTERFACE_INCOMPATIBLE_BEFORE_SCIENCE"},
            "harvard_1968_1969": {"role": "pre_scientific_panel", "verdict": HARVARD},
            "fripon_2018_2019": {"role": "preprotocol_integrity_stop", "verdict": FRIPON},
            "hissar_1968_1969": {"role": "pre_scientific_power_screen", "verdict": HISSAR},
        },
        "repository_only_route_inventory": inventory,
        "powered_external_verdict_obtained": False,
        "powered_external_pass_obtained": False,
        "powered_external_scientific_fail_obtained": False,
        "direct_v8_external_test_powered": False,
        "data_availability_or_pristine_panel_limitation_reached": True,
        "v8_method_changed_from_external_results": False,
        "external_power_floors_lowered": False,
        "new_detector_developed_from_external_results": False,
        "successor_detector_authorized": False,
        "target_reveal_authorized": False,
        "orbittrace_target_information_access": False,
        "catalogue_or_web_access_this_synthesis": False,
        "scientific_value_access_this_synthesis": False,
        "claim_boundary": (
            "Immutable-artifact and repository-branch synthesis only. No powered pristine external panel produced a v8 pass or a powered v8 scientific failure. The direct AMOR v8 test was power-inconclusive; every other preregistered/reserved route was exhausted by prior use, power, interface, recurrence, coverage, availability, or integrity constraints without retuning v8. External validation therefore remains unestablished, v8 remains unchanged, no successor is authorized, and OrbitTrace remains blinded."
        ),
    }
    (a.output / "v8_external_validation_terminal_synthesis.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    (a.output / "V8_EXTERNAL_VALIDATION_TERMINAL_SYNTHESIS.md").write_text(
        "# OrbitTrace v8 external-validation terminal synthesis\n\n"
        f"**Verdict:** `{TERMINAL}`\n\n"
        "No powered external pass or powered external scientific failure was obtained. "
        "The direct v8 AMOR test was underpowered (N=19, Q=19), and the remaining preregistered/reserved routes were exhausted by independent power, interface, recurrence, coverage, availability, or integrity limits. "
        "v8 was not changed, no successor is authorized, and OrbitTrace remains blinded.\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
