#!/usr/bin/env python3
"""Target-excluded deployment qualification: canonical rows -> v8 label-free graph -> v15 rank."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from orbittrace_label_free_sparse_support_v6 import run_development as v6
from orbittrace_pooled_year_centroid_v8 import run_development as v8
from orbittrace_v15_canonical_application_v1 import application

mult = v6.mult

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
EXPECTED_FAMILY_COUNT = 226
EXPECTED_QUALIFIED = 95
EXPECTED_V8_RECOVERY100 = 58
EXPECTED_V8_MRR = 0.045531138942766655
EXPECTED_V8_PRECISION = 0.6884631112636006
MIN_V15_MRR = 0.04325458199562832
MIN_V15_PRECISION = 0.6384631112636006
BROWN_EQ_TOL = 1e-10


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def compact(metric: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in metric.items() if k != "per_label"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--source-audit-json", required=True, type=Path)
    p.add_argument("--v6-result-json", required=True, type=Path)
    p.add_argument("--centroid-audit-json", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    source_audit = json.loads(args.source_audit_json.read_text())
    predecessor = json.loads(args.v6_result_json.read_text())
    centroid_audit = json.loads(args.centroid_audit_json.read_text())
    require(source_audit["verdict"] == "PASS_WAVELET_CATALOGUE_V3_SOURCE_AUDIT", "frozen source audit failed")
    require(source_audit["development_source_sha256"] == "ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51", "runtime source changed")
    require(source_audit["support_source_sha256"] == "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62", "support source changed")
    require(predecessor["verdict"] == "PASS_LABEL_FREE_SPARSE_SUPPORT_V6_DEVELOPMENT", "v6 predecessor changed")
    require(int(predecessor["family_count"]) == EXPECTED_FAMILY_COUNT, "v6 family count changed")
    require(centroid_audit["verdict"] == "PASS_COMPONENT_CENTROID_SOURCE_AUDIT", "centroid audit changed")
    require(centroid_audit["catalogue_access"] is False and centroid_audit["scientific_value_access"] is False, "centroid audit crossed data boundary")

    require(all(mult.v3.self_test().values()), "multi-anchor v3 self-test failed")
    require(all(mult.brown.self_test().values()), "Brown self-test failed")
    runtime = mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = v8.CORPUS
    support.RANKING_VARIANTS = ("persistence", "mean_year_strength", "sqrt_support_strength", "min_year_strength", "size_penalized_strength")
    v6.YEARS = YEARS
    v6.MONTH_KEYS = MONTH_KEYS
    v8.YEARS = YEARS
    v8.MONTH_KEYS = MONTH_KEYS
    mult.YEARS = YEARS
    mult.MONTH_KEYS = MONTH_KEYS
    mult.TOP_K = 100

    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "target firewall changed")
    require(int(support.MIN_FAMILY_YEARS) == 2, "family recurrence gate changed")
    require(abs(float(support.FAMILY_LINK_RADIUS) - 1.5) < 1e-15, "family link radius changed")
    require(int(support.MIN_COMPONENT_EVENTS) == 4 and int(support.MIN_COMPONENT_QUARTETS) == 2, "component gates changed")
    require(int(support.SHORTLIST_K) == v6.FIRST_SHORTLIST and int(support.AUDIT_SHORTLIST_K) == v6.AUDIT_SHORTLIST, "shortlist constants changed")
    require(int(support.MIN_ANCHOR_COUNT) == v6.MIN_ANCHOR_COUNT and int(support.MAX_QUARTETS_PER_BIN) == v6.MAX_QUARTETS_PER_BIN, "proposal retention changed")

    setattr(args, "fixed4_baseline_json", args.source_audit_json)
    _candidate, base, _scorer = support.load_sources(args)

    # Repeated access to the already-exposed target-excluded v8 development panel.
    # The parser returns labels separately, but no value from that mapping is read until all orders below are frozen.
    raw_scan, _unused_calibration, hidden_labels, sources = support.parse_catalogue(base)
    require(sorted(raw_scan) == list(YEARS), "GMN year panel changed")
    require([s["key"] for s in sources] == list(MONTH_KEYS), "GMN monthly source universe changed")

    family_box: dict[str, Any] = {}

    def exact_label_free_v8_builder(
        years: tuple[int, int], canonical_scan: dict[int, list[dict[str, Any]]]
    ) -> list[dict[str, Any]]:
        require(years == YEARS, "qualification year pair changed")
        components: list[dict[str, Any]] = []
        scan_audits: list[dict[str, Any]] = []
        passing_counts: dict[str, int] = {}
        for year in years:
            audit, passing, year_components = v6.label_free_scan_year(year, canonical_scan[year], support, base)
            require(audit["calibration_events_used"] == 0, "label-dependent calibration entered v8 generator")
            require(audit["source_labels_used_for_proposals"] is False, "source labels entered v8 proposals")
            require(audit["score_threshold_applied"] is False, "score threshold entered v8 proposals")
            scan_audits.append(audit)
            passing_counts[str(year)] = len(passing)
            components.extend(year_components)
        families, persistence = support.build_families(components, base)
        require(len(families) == EXPECTED_FAMILY_COUNT, f"v8 family count changed: {len(families)}")
        require(set(persistence["persistence"]) == {str(f["family_id"]) for f in families}, "v8 family ranking universe incomplete")
        repair = v8.repair_year_centroids(families, components, canonical_scan, support, base)
        require(repair["non_centroid_family_structure_unchanged"] is True, "v8 centroid repair changed family structure")
        require(int(repair["families_with_duplicate_same_year_components"]) > 0, "v8 centroid repair became vacuous")
        family_box.update({
            "families": families,
            "scan_audits": scan_audits,
            "passing_counts": passing_counts,
            "centroid_repair": repair,
        })
        return families

    # Common application canonicalizes every row before invoking the label-free v8 builder.
    result = application.run_pretruth(
        years=YEARS,
        scan_by_year=raw_scan,
        family_builder=exact_label_free_v8_builder,
        runtime=runtime,
        base=base,
        score_episode=mult.score_episode,
    )
    require(result["labels_read"] is False and result["survey_conditioned_science"] is False, "common application boundary changed")
    families = family_box["families"]

    # Direct v8 fixed-128 identity control, still pre-truth.
    direct_scored, direct_summary = mult.score_families(families, application.validate_pair(YEARS, raw_scan), runtime, base)
    require(int(direct_summary["families_scored"]) == EXPECTED_FAMILY_COUNT, "direct v8 scoring family count changed")
    require(direct_summary["episode_sizes"] == [128], "direct v8 fixed-cardinality identity changed")
    require(float(direct_summary["max_brown_equivalence_difference"]) <= BROWN_EQ_TOL, "direct v8 Brown equivalence failed")
    direct_order = [str(x) for x in mult.rank_scored(direct_scored, "multiplicity")]
    require(direct_order == result["component_orders"]["128"], "common cap-128 order differs from direct frozen v8")

    # FIRST use of hidden known-shower mapping in this qualification: all family and rank outputs already exist.
    direct_metric = compact(mult.evaluate_order(hidden_labels, families, direct_order))
    v15_metric = compact(mult.evaluate_order(hidden_labels, families, result["v15_order"]))

    direct_identity = {
        "family_count_exact_226": int(result["family_count"]) == EXPECTED_FAMILY_COUNT,
        "qualified_exact_95": int(direct_metric["qualified_matches"]) == EXPECTED_QUALIFIED,
        "recovered_at_100_exact_58": int(direct_metric["recovered_at_100"]) == EXPECTED_V8_RECOVERY100,
        "mrr_exact_frozen_v8": abs(float(direct_metric["mrr"]) - EXPECTED_V8_MRR) <= 1e-12,
        "precision_exact_frozen_v8": abs(float(direct_metric["top100_dominant_precision"]) - EXPECTED_V8_PRECISION) <= 1e-12,
        "cap128_order_exact_direct_v8": direct_order == result["component_orders"]["128"],
        "label_free_generator": all(
            a["calibration_events_used"] == 0 and a["source_labels_used_for_proposals"] is False and a["score_threshold_applied"] is False
            for a in family_box["scan_audits"]
        ),
    }
    preservation = {
        "recovered_at_100_at_least_58": int(v15_metric["recovered_at_100"]) >= EXPECTED_V8_RECOVERY100,
        "mrr_at_least_95pct_v8": float(v15_metric["mrr"]) >= MIN_V15_MRR,
        "top100_precision_loss_at_most_005": float(v15_metric["top100_dominant_precision"]) >= MIN_V15_PRECISION,
        "qualified_exact_95": int(v15_metric["qualified_matches"]) == EXPECTED_QUALIFIED,
        "family_universe_exact_226": int(result["family_count"]) == EXPECTED_FAMILY_COUNT,
    }

    if not all(direct_identity.values()):
        verdict = "FAIL_V15_LABEL_FREE_V8_DEPLOYMENT_INTEGRITY"
    elif all(preservation.values()):
        verdict = "PASS_V15_LABEL_FREE_V8_DEPLOYMENT_QUALIFICATION"
    else:
        verdict = "FAIL_V15_LABEL_FREE_V8_DEPLOYMENT_PERFORMANCE"

    out = {
        "verdict": verdict,
        "evidence_class": "target_excluded_deployment_qualification",
        "years": list(YEARS),
        "family_count": int(result["family_count"]),
        "family_universe_sha256": result["family_universe_sha256"],
        "component_order_sha256": {k: v["order_sha256"] for k, v in result["component_summaries"].items()},
        "v15_order_sha256": result["v15_order_sha256"],
        "direct_v8_order_sha256": canonical_sha(direct_order),
        "direct_v8_metric": direct_metric,
        "v15_metric": v15_metric,
        "direct_v8_identity_gates": direct_identity,
        "v15_preservation_gates": preservation,
        "passing_quartet_counts": family_box["passing_counts"],
        "scan_audits": family_box["scan_audits"],
        "centroid_repair": family_box["centroid_repair"],
        "canonical_projection_before_generator": True,
        "label_dependent_calibration_used": False,
        "labels_first_used_after_all_orders_frozen": True,
        "sonotaco_access": False,
        "maarsy_event_access": False,
        "dms_access": False,
        "target_information_access": False,
    }
    (args.output / "qualification.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
