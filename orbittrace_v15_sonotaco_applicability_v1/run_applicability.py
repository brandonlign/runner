#!/usr/bin/env python3
"""Pre-truth engineering applicability of canonical label-free v8 + v15 on SonotaCo 2013/2014."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from orbittrace_label_free_sparse_support_v6 import run_development as v6
from orbittrace_pooled_year_centroid_v8 import run_development as v8
from orbittrace_v15_canonical_application_v1 import application

mult = v6.mult
YEARS = (2013, 2014)
EXPECTED_PREP_ARTIFACT_ID = 9050107352
EXPECTED_PREP_ARTIFACT_DIGEST = "sha256:1296d757b5ea1dd94f9c9077fd769fdc8f00ec06d0881d8548fd1df4608344cc"
EXPECTED_FILES = {
    "base_2013.json": "f84e6db4166be065a73c7d030d66fdf796c1c6c2b5ee692f1e3299e8ae7c05ce",
    "base_2014.json": "1fab29c7368b63cc9c9d172dcadec5918d6514bfbb09f0f71e54eebb9bf32f00",
    "base_audit_2013.json": "b9ddcbfa206dc62f6e37817c006622c62a9ce94e4c6f79ad3776847d6d62faa3",
    "base_audit_2014.json": "9ed6d5ebe1e9f510ad47e461a487189020bda34df602f00ea23e80de5bebfbe1",
    "label_free_preparation_manifest.json": "0a24077f352ddba91c5fea2a102f996d6bea154b1bc769235a4dd916850dba2b",
    "source_integrity.json": "a545cd319f0c56dc6be71ebf94627152ac6d272ace75468fd57629f466843ee4",
}
EXPECTED_BASE_COUNTS = {2013: 24899, 2014: 20575}
BROWN_EQ_TOL = 1e-10


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--prepared", required=True, type=Path)
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

    for name, expected in EXPECTED_FILES.items():
        path = args.prepared / name
        require(path.is_file(), f"missing frozen SonotaCo preparation file {name}")
        require(sha256(path) == expected, f"frozen SonotaCo preparation file changed: {name}")

    manifest = json.loads((args.prepared / "label_free_preparation_manifest.json").read_text())
    require(manifest["verdict"] == "PASS_FINAL_SONOTACO_LABEL_FREE_PREPARATION", "SonotaCo preparation verdict changed")
    require(manifest["years"] == [2013, 2014], "SonotaCo preparation years changed")
    require(manifest["base_counts"] == {"2013": 24899, "2014": 20575}, "SonotaCo base counts changed")
    require(manifest["shower_truth_accessed"] is False, "SonotaCo preparation accessed truth")
    require(manifest["target_region_retained"] is False, "SonotaCo preparation retained target region")
    require(manifest["maarsy_scientific_access"] is False, "SonotaCo preparation accessed MAARSY")
    require(manifest["target_information_access"] is False, "SonotaCo preparation accessed target information")

    for year in YEARS:
        audit = json.loads((args.prepared / f"base_audit_{year}.json").read_text())
        require(audit["year"] == year, f"SonotaCo audit year changed for {year}")
        require(audit["counts"]["retained"] == EXPECTED_BASE_COUNTS[year], f"SonotaCo retained count changed for {year}")
        require(audit["shower_column_row_accessed"] is False, f"SonotaCo shower column accessed for {year}")
        require(audit["truth_mapping_accessed"] is False, f"SonotaCo truth mapping accessed for {year}")
        require(audit["target_region_non_solar_fields_decoded"] is False, f"target-region geometry decoded for {year}")

    source_audit = json.loads(args.source_audit_json.read_text())
    predecessor = json.loads(args.v6_result_json.read_text())
    centroid_audit = json.loads(args.centroid_audit_json.read_text())
    require(source_audit["verdict"] == "PASS_WAVELET_CATALOGUE_V3_SOURCE_AUDIT", "frozen source audit failed")
    require(source_audit["support_source_sha256"] == "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62", "support source changed")
    require(predecessor["verdict"] == "PASS_LABEL_FREE_SPARSE_SUPPORT_V6_DEVELOPMENT", "v6 predecessor changed")
    require(centroid_audit["verdict"] == "PASS_COMPONENT_CENTROID_SOURCE_AUDIT", "centroid audit changed")
    require(centroid_audit["catalogue_access"] is False and centroid_audit["scientific_value_access"] is False, "centroid audit crossed data boundary")

    require(all(mult.v3.self_test().values()), "multi-anchor v3 self-test failed")
    require(all(mult.brown.self_test().values()), "Brown self-test failed")
    runtime = mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1, 13))
    support.CORPUS = v8.CORPUS
    support.RANKING_VARIANTS = ("persistence",)
    v6.YEARS = YEARS
    v6.MONTH_KEYS = support.MONTH_KEYS
    v8.YEARS = YEARS
    v8.MONTH_KEYS = support.MONTH_KEYS
    mult.YEARS = YEARS
    mult.MONTH_KEYS = support.MONTH_KEYS
    mult.TOP_K = 100

    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "target firewall changed")
    require(int(support.MIN_FAMILY_YEARS) == 2, "family recurrence gate changed")
    require(abs(float(support.FAMILY_LINK_RADIUS) - 1.5) < 1e-15, "family link radius changed")
    require(int(support.MIN_COMPONENT_EVENTS) == 4 and int(support.MIN_COMPONENT_QUARTETS) == 2, "component gates changed")
    require(int(support.SHORTLIST_K) == v6.FIRST_SHORTLIST and int(support.AUDIT_SHORTLIST_K) == v6.AUDIT_SHORTLIST, "shortlist constants changed")
    require(int(support.MIN_ANCHOR_COUNT) == v6.MIN_ANCHOR_COUNT and int(support.MAX_QUARTETS_PER_BIN) == v6.MAX_QUARTETS_PER_BIN, "proposal retention changed")

    setattr(args, "fixed4_baseline_json", args.source_audit_json)
    _candidate, base, _scorer = support.load_sources(args)

    raw_scan: dict[int, list[dict[str, Any]]] = {}
    for year in YEARS:
        rows = json.loads((args.prepared / f"base_{year}.json").read_text())
        require(isinstance(rows, list) and len(rows) == EXPECTED_BASE_COUNTS[year], f"invalid frozen base rows for {year}")
        raw_scan[year] = rows

    family_box: dict[str, Any] = {}

    def exact_label_free_v8_builder(
        years: tuple[int, int], canonical_scan: dict[int, list[dict[str, Any]]]
    ) -> list[dict[str, Any]]:
        require(years == YEARS, "SonotaCo pair changed")
        components: list[dict[str, Any]] = []
        audits: list[dict[str, Any]] = []
        passing_counts: dict[str, int] = {}
        for year in years:
            audit, passing, year_components = v6.label_free_scan_year(year, canonical_scan[year], support, base)
            require(audit["calibration_events_used"] == 0, "label-dependent calibration entered SonotaCo generator")
            require(audit["source_labels_used_for_proposals"] is False, "labels entered SonotaCo proposals")
            require(audit["score_threshold_applied"] is False, "score threshold entered SonotaCo proposals")
            audits.append(audit)
            passing_counts[str(year)] = len(passing)
            components.extend(year_components)
        families, rankings = support.build_families(components, base)
        require(families, "label-free v8 generator produced no recurrent SonotaCo family")
        require(set(rankings["persistence"]) == {str(f["family_id"]) for f in families}, "SonotaCo family universe incomplete")
        repair = v8.repair_year_centroids(families, components, canonical_scan, support, base)
        require(repair["non_centroid_family_structure_unchanged"] is True, "v8 centroid repair changed SonotaCo family structure")
        family_box.update({
            "families": families,
            "scan_audits": audits,
            "passing_counts": passing_counts,
            "centroid_repair": repair,
        })
        return families

    base_projection = application.validate_pair(YEARS, raw_scan)
    input_summary = {
        str(year): {
            "count": len(base_projection[year]),
            "event_ids_sha256": canonical_sha([row["id"] for row in base_projection[year]]),
            "canonical_rows_sha256": canonical_sha(base_projection[year]),
        }
        for year in YEARS
    }

    try:
        result = application.run_pretruth(
            years=YEARS,
            scan_by_year=raw_scan,
            family_builder=exact_label_free_v8_builder,
            runtime=runtime,
            base=base,
            score_episode=mult.score_episode,
        )
        require(result["labels_read"] is False, "common application read labels")
        require(result["survey_conditioned_science"] is False, "survey-conditioned science entered common application")
        require(int(result["family_count"]) > 0, "no recurrent SonotaCo families reached v15")
        require(len(result["v15_order"]) == int(result["family_count"]), "final v15 SonotaCo order incomplete")
        require(len(set(result["v15_order"])) == int(result["family_count"]), "final v15 SonotaCo order duplicated family")
        require(all(float(s["max_brown_equivalence_difference"]) <= BROWN_EQ_TOL for s in result["component_summaries"].values()), "Brown equivalence failed")
        verdict = "PASS_V15_SONOTACO_2013_2014_ENGINEERING_APPLICABILITY"
        failure_reason = None
        payload = {
            "family_count": int(result["family_count"]),
            "family_universe_sha256": result["family_universe_sha256"],
            "component_summaries": result["component_summaries"],
            "v15_order_sha256": result["v15_order_sha256"],
            "passing_quartet_counts": family_box["passing_counts"],
            "scan_audits": family_box["scan_audits"],
            "centroid_repair": family_box["centroid_repair"],
        }
    except RuntimeError as exc:
        verdict = "FAIL_V15_SONOTACO_2013_2014_ENGINEERING_APPLICABILITY"
        failure_reason = str(exc)
        payload = {
            "family_count": len(family_box.get("families", [])),
            "passing_quartet_counts": family_box.get("passing_counts", {}),
            "scan_audits": family_box.get("scan_audits", []),
            "centroid_repair": family_box.get("centroid_repair"),
        }

    out = {
        "verdict": verdict,
        "evidence_class": "engineering_applicability_only_no_truth",
        "years": list(YEARS),
        "frozen_preparation_artifact_id": EXPECTED_PREP_ARTIFACT_ID,
        "frozen_preparation_artifact_digest": EXPECTED_PREP_ARTIFACT_DIGEST,
        "input_summary": input_summary,
        **payload,
        "failure_reason": failure_reason,
        "truth_mapping_accessed": False,
        "comparator_output_accessed": False,
        "recovery_metric_computed": False,
        "precision_metric_computed": False,
        "mrr_computed": False,
        "maarsy_event_access": False,
        "dms_access": False,
        "target_information_access": False,
    }
    (args.output / "applicability.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
