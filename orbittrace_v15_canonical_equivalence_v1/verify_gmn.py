#!/usr/bin/env python3
"""Engineering-only equivalence proof for canonical-format v15 on exposed GMN 2020/2021.

This reuses the exact frozen v5 scanner/family builder used by v15 development, projects its
label-free scan rows through the canonical event interface, then runs the common v15 nominal-128
application. It never consults the hidden-label mapping returned by the frozen parser.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import run_holdout_loader_corrected as v5_loader

from orbittrace_v15_canonical_application_v1 import application

v5 = v5_loader.core

YEARS = (2020, 2021)
MONTH_KEYS = tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1, 13))
EXPECTED_FAMILY_COUNT = 92
EXPECTED_FAMILY_UNIVERSE_SHA256 = "486690de951d63a40e0c1682531a0a8d0ba3fcd17f1b026c6c3b2b8559350a7a"
EXPECTED_COMPONENT_ORDER_SHA256 = {
    128: "37d7617ba00998611bdb4709cde25df538ddab4cdaef74f37b8ac2a83fa8ac13",
    96: "56ed642de5edea87523244440d560ee0d2fecdcada46a120ab31314a6ce4cb04",
    64: "ee6b5313c9beeea8fc584a307e5b0b93d37f00fc823295eb899eb87bf667492f",
}
EXPECTED_V15_ORDER_SHA256 = "b080d8d6407823091f937a5701047922455d70f729402f15aad14515ac14084f"
EXPECTED_SUPPORT_SHA256 = "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--source-audit-json", required=True, type=Path)
    p.add_argument("--factorization-json", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    source_audit = json.loads(args.source_audit_json.read_text())
    require(source_audit["verdict"] == "PASS_MULTIPLICITY_V5_SUPPORT_SOURCE_AUDIT", "support audit did not pass")
    require(source_audit["support_sha256"] == EXPECTED_SUPPORT_SHA256, "support source hash changed")
    require(source_audit["catalogue_access"] is False, "source audit unexpectedly accessed catalogue")

    factorization = json.loads(args.factorization_json.read_text())
    require(factorization["verdict"] == "V3_NON_BROWN_TERM_RETAINS_EXPLORATORY_RANKING_SIGNAL", "factorization identity changed")
    require(factorization["blindness"]["catalogue_access"] is False, "factorization unexpectedly accessed catalogue")

    require(int(v5.EPISODE_SIZE) == 128, "frozen v5 episode identity changed")
    require(all(v5.v3.self_test().values()), "frozen multi-anchor v3 self-test failed")
    require(all(v5.brown.self_test().values()), "frozen Brown self-test failed")
    runtime = v5.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "target firewall changed")
    require(int(support.MIN_FAMILY_YEARS) == 2, "family recurrence gate changed")
    require(abs(float(support.FAMILY_LINK_RADIUS) - 1.5) < 1e-15, "family link radius changed")

    # Exact temporal substitution used by the frozen v5/v13/v15 development chain.
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    require(tuple(support.YEARS) == YEARS and tuple(support.MONTH_KEYS) == MONTH_KEYS, "GMN pair substitution failed")

    setattr(args, "fixed4_baseline_json", args.factorization_json)
    candidate, base, scorer = support.load_sources(args)

    # This is repeated access to the already-exposed v15 development corpus only.
    scan_by_year, calibration_by_year, _hidden_labels_never_read, catalogue_sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "GMN scan years changed")
    require(sorted(calibration_by_year) == list(YEARS), "GMN calibration years changed")
    require([source["key"] for source in catalogue_sources] == list(MONTH_KEYS), "GMN source universe changed")

    scan_audits: list[dict[str, Any]] = []
    passing_counts: dict[str, int] = {}

    def exact_frozen_family_builder(
        years: tuple[int, int],
        canonical_scan: dict[int, list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        require(years == YEARS, "equivalence harness year pair changed")
        components: list[dict[str, Any]] = []
        for year in YEARS:
            audit, passing, year_components = support.scan_year(
                year,
                canonical_scan[year],
                calibration_by_year[year],
                candidate,
                base,
                scorer,
            )
            scan_audits.append(audit)
            passing_counts[str(year)] = len(passing)
            components.extend(year_components)
        families, rankings = support.build_families(components, base)
        persistence = [str(x) for x in rankings["persistence"]]
        ids = [str(f["family_id"]) for f in families]
        require(set(persistence) == set(ids) and len(persistence) == len(ids), "persistence family universe mismatch")
        return families

    result = application.run_pretruth(
        years=YEARS,
        scan_by_year=scan_by_year,
        family_builder=exact_frozen_family_builder,
        runtime=runtime,
        base=base,
        score_episode=v5.score_episode,
    )

    require(result["labels_read"] is False, "common application consulted labels")
    require(result["survey_conditioned_science"] is False, "survey-conditioned science entered application")
    require(int(result["family_count"]) == EXPECTED_FAMILY_COUNT, "canonical family count differs from frozen v15")
    require(result["family_universe_sha256"] == EXPECTED_FAMILY_UNIVERSE_SHA256, "canonical family universe differs from frozen v15")
    for cap, expected in EXPECTED_COMPONENT_ORDER_SHA256.items():
        got = result["component_summaries"][str(cap)]["order_sha256"]
        require(got == expected, f"canonical component order differs at cap {cap}: {got}")
    require(result["v15_order_sha256"] == EXPECTED_V15_ORDER_SHA256, "canonical final v15 order differs from frozen v15")

    summary = {
        "verdict": "PASS_V15_CANONICAL_GMN_IMPLEMENTATION_EQUIVALENCE",
        "evidence_class": "engineering_equivalence_only",
        "years": list(YEARS),
        "family_count": int(result["family_count"]),
        "family_universe_sha256": result["family_universe_sha256"],
        "component_order_sha256": {str(cap): result["component_summaries"][str(cap)]["order_sha256"] for cap in application.COMPONENT_CAPS},
        "v15_order_sha256": result["v15_order_sha256"],
        "expected_v15_order_sha256": EXPECTED_V15_ORDER_SHA256,
        "passing_quartet_counts": passing_counts,
        "scan_audits": scan_audits,
        "canonical_projection_applied_before_family_builder": True,
        "hidden_label_mapping_read": False,
        "external_data_access": False,
        "sonotaco_2013_2014_access": False,
        "maarsy_event_access": False,
        "target_information_access": False,
    }
    (args.output / "equivalence.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
