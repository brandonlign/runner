#!/usr/bin/env python3
"""Run frozen canonical label-free-v8 + v15 on one comparator-matched SonotaCo pair before truth."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from orbittrace_label_free_sparse_support_v6 import run_development as v6
from orbittrace_pooled_year_centroid_v8 import run_development as v8
from orbittrace_v15_canonical_application_v1 import application
from orbittrace_final_sonotaco_one_shot_v1.runtime_helpers import load_support_base, require, sha256_path

mult = v6.mult
YEARS = (2013, 2014)
BROWN_EQ_TOL = 1e-10
EXPECTED_V6_BLOB = "7995fc6b75d1fd51eb4b304ace39db28a5a1e876"
EXPECTED_V8_BLOB = "f248df78e1258b132b41aecca6a985a5eb782654"
EXPECTED_COMMON_APP_BLOB = "5b3244dfbcc7bc931925aea42866edc8205113a8"


def dump(path: Path, value: Any) -> str:
    raw = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--comparator", choices=["sugar", "hdbscan"], required=True)
    p.add_argument("--rows-2013", type=Path, required=True)
    p.add_argument("--rows-2014", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--source-audit-json", type=Path, required=True)
    p.add_argument("--v6-result-json", type=Path, required=True)
    p.add_argument("--centroid-audit-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()


def main() -> int:
    a = parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    raw_scan = {2013: json.loads(a.rows_2013.read_text()), 2014: json.loads(a.rows_2014.read_text())}
    for year in YEARS:
        require(isinstance(raw_scan[year], list) and raw_scan[year], f"empty {year} matched row universe")
        require(all(int(row.get("year")) == year for row in raw_scan[year]), f"invalid year field in {year} rows")
        forbidden = {"label", "shower", "truth", "known_shower", "native_background", "sporadic"}
        require(all(not (forbidden & {str(k).lower() for k in row}) for row in raw_scan[year]), "truth-bearing field reached v15 candidate input")

    source_audit = json.loads(a.source_audit_json.read_text())
    predecessor = json.loads(a.v6_result_json.read_text())
    centroid_audit = json.loads(a.centroid_audit_json.read_text())
    require(source_audit["verdict"] == "PASS_WAVELET_CATALOGUE_V3_SOURCE_AUDIT", "frozen source audit failed")
    require(source_audit["support_source_sha256"] == "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62", "support source changed")
    require(predecessor["verdict"] == "PASS_LABEL_FREE_SPARSE_SUPPORT_V6_DEVELOPMENT", "label-free v6 predecessor changed")
    require(centroid_audit["verdict"] == "PASS_COMPONENT_CENTROID_SOURCE_AUDIT", "centroid audit changed")
    require(centroid_audit["catalogue_access"] is False and centroid_audit["scientific_value_access"] is False, "centroid audit crossed data boundary")

    require(all(mult.v3.self_test().values()), "multi-anchor v3 self-test failed")
    require(all(mult.brown.self_test().values()), "Brown self-test failed")
    runtime, support, base, _scorer = load_support_base(
        p19_module=type("P19Shim", (), {"mult": mult})(),
        support_source_parts=a.support_source_parts,
        candidate_payload=a.candidate_payload,
        baseline_payload=a.baseline_payload,
        scorer_parts=a.scorer_parts,
    )
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

    family_box: dict[str, Any] = {}

    def exact_label_free_v8_builder(
        years: tuple[int, int], canonical_scan: dict[int, list[dict[str, Any]]]
    ) -> list[dict[str, Any]]:
        require(years == YEARS, "matched SonotaCo pair changed")
        components: list[dict[str, Any]] = []
        audits: list[dict[str, Any]] = []
        passing_counts: dict[str, int] = {}
        for year in years:
            audit, passing, year_components = v6.label_free_scan_year(year, canonical_scan[year], support, base)
            require(audit["calibration_events_used"] == 0, "label-dependent calibration entered final candidate")
            require(audit["source_labels_used_for_proposals"] is False, "labels entered final candidate proposals")
            require(audit["score_threshold_applied"] is False, "score threshold entered final candidate proposals")
            audits.append(audit)
            passing_counts[str(year)] = len(passing)
            components.extend(year_components)
        families, rankings = support.build_families(components, base)
        require(families, f"v15 produced no recurrent families on {a.comparator} matched universe")
        require(set(str(x) for x in rankings["persistence"]) == {str(f["family_id"]) for f in families}, "family universe incomplete")
        repair = v8.repair_year_centroids(families, components, canonical_scan, support, base)
        require(repair["non_centroid_family_structure_unchanged"] is True, "pooled centroid repair changed family structure")
        family_box.update({
            "families": families,
            "scan_audits": audits,
            "passing_counts": passing_counts,
            "centroid_repair": repair,
        })
        return families

    result = application.run_pretruth(
        years=YEARS,
        scan_by_year=raw_scan,
        family_builder=exact_label_free_v8_builder,
        runtime=runtime,
        base=base,
        score_episode=mult.score_episode,
    )
    require(result["labels_read"] is False, "common application read labels")
    require(result["survey_conditioned_science"] is False, "survey-conditioned science entered final candidate")
    require(all(float(summary["max_brown_equivalence_difference"]) <= BROWN_EQ_TOL for summary in result["component_summaries"].values()), "Brown equivalence failed")
    require(len(result["v15_order"]) == int(result["family_count"]), "v15 order incomplete")
    require(len(set(result["v15_order"])) == int(result["family_count"]), "v15 order duplicated family")

    by_id = {str(f["family_id"]): f for f in family_box["families"]}
    require(set(result["v15_order"]) == set(by_id), "v15/family universe mismatch")
    ordered: list[dict[str, Any]] = []
    for rank, fid in enumerate(result["v15_order"], start=1):
        family = by_id[str(fid)]
        event_ids = [str(x) for x in family["event_ids"]]
        require(event_ids and len(event_ids) == len(set(event_ids)), f"invalid member list for {fid}")
        ordered.append({
            "family_id": str(fid),
            "event_ids": event_ids,
            "rank": rank,
            "source": "label_free_v8",
        })

    canonical_scan = application.validate_pair(YEARS, raw_scan)
    source_manifest = {
        "method": "OrbitTrace v15 label-free-v8 multiscale consensus",
        "comparator_pair": a.comparator,
        "v6_source_git_blob": EXPECTED_V6_BLOB,
        "v8_source_git_blob": EXPECTED_V8_BLOB,
        "common_application_git_blob": EXPECTED_COMMON_APP_BLOB,
        "common_application_sha256": sha256_path(Path(application.__file__)),
        "canonical_adapter_sha256": sha256_path(Path(__import__("orbittrace_v15_canonical_events_v1.canonical", fromlist=["x"]).__file__)),
        "truth_labels_accepted": False,
        "label_dependent_calibration_used": False,
        "target_information_access": False,
    }
    source_sha = dump(a.output / "candidate_source_manifest.json", source_manifest)
    primary = {
        "method": "OrbitTrace v15 label-free-v8 multiscale consensus",
        "comparator_pair": a.comparator,
        "years": [2013, 2014],
        "input_counts": {str(year): len(canonical_scan[year]) for year in YEARS},
        "input_event_ids_sha256": {str(year): canonical_sha([row["id"] for row in canonical_scan[year]]) for year in YEARS},
        "candidate_counts": {"label_free_v8": int(result["family_count"]), "union": int(result["family_count"])},
        "family_universe_sha256": result["family_universe_sha256"],
        "component_summaries": result["component_summaries"],
        "application_order_sha256": result["v15_order_sha256"],
        "family_count": len(ordered),
        "families": ordered,
        "scan_audits": family_box["scan_audits"],
        "passing_quartet_counts": family_box["passing_counts"],
        "centroid_repair": family_box["centroid_repair"],
        "source_manifest_sha256": source_sha,
        "truth_accessed": False,
        "target_information_access": False,
    }
    primary_sha = dump(a.output / "candidate_primary_output.json", primary)
    summary = {
        "verdict": "PASS_FINAL_PRETRUTH_V15_OUTPUT_FREEZE",
        "comparator_pair": a.comparator,
        "primary_output_sha256": primary_sha,
        "source_manifest_sha256": source_sha,
        "family_count": len(ordered),
        "truth_accessed": False,
        "target_information_access": False,
    }
    dump(a.output / "candidate_pretruth_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
