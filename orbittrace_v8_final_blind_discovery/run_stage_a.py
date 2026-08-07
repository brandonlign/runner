#!/usr/bin/env python3
"""Frozen Stage A: target-containing, reference-free GMN v8 blind discovery."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from orbittrace_label_free_sparse_support_v6 import run_development as v6
from orbittrace_pooled_year_centroid_v8 import run_development as v8
from orbittrace_sparse_support_multiplicity_v5 import run_holdout as mult

YEARS = (2022, 2023, 2024, 2025, 2026)
MONTH_KEYS = tuple(
    [f"{year}-{month:02d}" for year in (2022, 2023, 2024, 2025) for month in range(1, 13)]
    + [f"2026-{month:02d}" for month in range(1, 8)]
)
CORPUS = "orbittrace-v8-final-blind-discovery"
FIRST_SHORTLIST = 64
AUDIT_SHORTLIST = 128
MIN_ANCHOR_COUNT = 2
MAX_QUARTETS_PER_BIN = 512
MIN_COMPONENT_EVENTS = 4
MIN_COMPONENT_QUARTETS = 2
MIN_FAMILY_YEARS = 2
FAMILY_LINK_RADIUS = 1.5
EPISODE_SIZE = 128
MIN_SCANNABLE_BINS = 24
MIN_FAMILIES = 100
BROWN_EQ_TOL = 1e-10
V8_PARENT_COMMIT = "c9d6c44704013ba0c9430100e98a29a56b453304"
V8_DEVELOPMENT_ARTIFACT_SHA256 = "88d2d607e05d027015c338f7e23b64a6195e55ae24f1b2ac745f5e9bc6df599e"
SUPPORT_SOURCE_SHA256 = "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62"
WAVELET_RUNTIME_SHA256 = "ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--source-audit-json", required=True, type=Path)
    p.add_argument("--freeze-manifest", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def geometry_column_map(frame: pd.DataFrame, support: Any) -> dict[str, str]:
    cols = list(map(str, frame.columns))
    return {
        "id": support.pick(cols, [("unique", "trajectory", "identifier"), ("trajectory", "identifier")]),
        "sol": support.pick(cols, [("sol", "lon", "deg"), ("solar", "longitude")]),
        "lam": support.pick(cols, [("lamgeo", "deg"), ("geocentric", "ecliptic", "longitude")]),
        "bet": support.pick(cols, [("betgeo", "deg"), ("geocentric", "ecliptic", "latitude")]),
        "vg": support.pick(cols, [("vgeo", "km", "s"), ("geocentric", "velocity")]),
    }


def parse_target_containing_catalogue(support: Any, base: Any) -> tuple[dict[int, list[dict[str, Any]]], list[dict[str, Any]]]:
    """First target-containing data access. No label column is resolved or read."""
    scan_by_year: dict[int, list[dict[str, Any]]] = defaultdict(list)
    sources: list[dict[str, Any]] = []
    seen: set[str] = set()
    for key in MONTH_KEYS:
        year = int(key[:4])
        text = support.dd.get_monthly_file_content_by_date(key)
        payload = text.encode("utf-8")
        frame = support.read_gmn_frame(text)
        columns = geometry_column_map(frame, support)
        data = pd.DataFrame({
            "id": frame[columns["id"]].astype(str),
            "sol": pd.to_numeric(frame[columns["sol"]], errors="coerce"),
            "lam": pd.to_numeric(frame[columns["lam"]], errors="coerce"),
            "bet": pd.to_numeric(frame[columns["bet"]], errors="coerce"),
            "vg": pd.to_numeric(frame[columns["vg"]], errors="coerce"),
        })
        valid = np.isfinite(data[["sol", "lam", "bet", "vg"]]).all(axis=1)
        valid &= data["sol"].between(0.0, 360.0)
        valid &= data["lam"].between(0.0, 360.0)
        valid &= data["bet"].between(-90.0, 90.0)
        valid &= data["vg"].between(5.0, 75.0)
        selected = data.loc[valid].copy()
        duplicate_rows = int(selected["id"].isin(seen).sum())
        selected = selected.loc[~selected["id"].isin(seen)]
        seen.update(selected["id"].tolist())
        sun_lon = base.wrap180(selected["lam"].to_numpy(float) - selected["sol"].to_numpy(float))
        events: list[dict[str, Any]] = []
        for event_id, sol, lon, bet, vg in zip(
            selected["id"].tolist(),
            selected["sol"].to_numpy(float),
            np.asarray(sun_lon, dtype=float),
            selected["bet"].to_numpy(float),
            selected["vg"].to_numpy(float),
        ):
            events.append({
                "id": str(event_id),
                "year": year,
                "sol": float(sol),
                "sun_lon": float(lon),
                "ecl_lat": float(bet),
                "vg": float(vg),
                "iau": 0,
                "complex_key": "UNAVAILABLE",
            })
        scan_by_year[year].extend(events)
        sources.append({
            "key": key,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "raw_rows": int(len(frame)),
            "selected_geometry_rows": int(len(events)),
            "duplicate_rows_removed_from_prior_months": duplicate_rows,
            "columns": columns,
            "label_column_resolved": False,
            "label_values_read": False,
        })
        print(f"stage-a catalogue {key}: raw={len(frame):,} geometry={len(events):,}", flush=True)
    require([source["key"] for source in sources] == list(MONTH_KEYS), "monthly source universe changed")
    require(sorted(scan_by_year) == list(YEARS), "year universe changed")
    for year in YEARS:
        require(len(scan_by_year[year]) >= 1000, f"insufficient geometry-valid events in {year}")
    return dict(scan_by_year), sources


def repair_pooled_year_centroids(
    families: list[dict[str, Any]],
    components: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
    support: Any,
    base: Any,
) -> dict[str, Any]:
    component_by_id = {str(c["component_id"]): c for c in components}
    require(len(component_by_id) == len(components), "component IDs are not unique")
    event_lookup = {year: {str(e["id"]): e for e in scan_by_year[year]} for year in YEARS}
    before = {str(f["family_id"]): v8.structural_snapshot(f) for f in families}
    duplicate_families = 0
    duplicate_family_years = 0
    singleton_distances: list[float] = []
    duplicate_distances: list[float] = []
    for family in families:
        pooled: dict[str, dict[str, float]] = {}
        has_duplicate = False
        family_years = sorted(int(y) for y in family["years"])
        for year in family_years:
            year_components = [
                component_by_id[str(cid)]
                for cid in family["component_ids"]
                if int(component_by_id[str(cid)]["year"]) == year
            ]
            require(year_components, f"family {family['family_id']} missing component for {year}")
            if len(year_components) > 1:
                has_duplicate = True
                duplicate_family_years += 1
            event_ids = sorted(set().union(*(set(map(str, c["event_ids"])) for c in year_components)))
            require(event_ids and all(eid in event_lookup[year] for eid in event_ids), "pooled event lookup failed")
            center = v8.pooled_centroid([event_lookup[year][eid] for eid in event_ids], support)
            pooled[str(year)] = center
            if len(year_components) == 1:
                singleton_distances.append(float(support.centroid_distance(center, year_components[0]["centroid"], base)))
            else:
                old = family["centroids"].get(str(year))
                require(old is not None, "inherited family centroid missing")
                duplicate_distances.append(float(support.centroid_distance(center, old, base)))
        if has_duplicate:
            duplicate_families += 1
        family["centroids"] = pooled
    after = {str(f["family_id"]): v8.structural_snapshot(f) for f in families}
    require(before == after, "pooled centroid repair changed non-centroid family structure")
    max_single = max(singleton_distances) if singleton_distances else 0.0
    require(max_single <= 1e-12, f"single-component pooled centroid mismatch: {max_single}")
    return {
        "families_with_duplicate_same_year_components": duplicate_families,
        "duplicate_family_years": duplicate_family_years,
        "single_component_family_years": len(singleton_distances),
        "max_single_component_centroid_distance": float(max_single),
        "duplicate_old_to_pooled_distance_median": float(np.median(duplicate_distances)) if duplicate_distances else None,
        "duplicate_old_to_pooled_distance_max": float(max(duplicate_distances)) if duplicate_distances else None,
        "non_centroid_family_structure_unchanged": True,
    }


def score_families_generic(
    families: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
    runtime: Any,
    base: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    episode_sizes: list[int] = []
    max_brown_difference = 0.0
    for index, family in enumerate(families, 1):
        years = sorted(int(y) for y in family["years"])
        require(len(years) >= MIN_FAMILY_YEARS, "family recurrence changed")
        per_year: dict[str, Any] = {}
        for year in years:
            episode, metadata = mult.build_local_episode(family, year, scan_by_year[year], runtime, base)
            v3_score, brown_score, multiplicity, difference = mult.score_episode(episode)
            max_brown_difference = max(max_brown_difference, float(difference))
            episode_sizes.append(int(metadata["episode_size"]))
            per_year[str(year)] = {
                **metadata,
                "v3_score": float(v3_score),
                "brown_score": float(brown_score),
                "multiplicity": float(multiplicity),
                "brown_equivalence_difference": float(difference),
            }
        ms = [float(per_year[str(year)]["multiplicity"]) for year in years]
        vs = [float(per_year[str(year)]["v3_score"]) for year in years]
        bs = [float(per_year[str(year)]["brown_score"]) for year in years]
        require(all(math.isfinite(x) and x > 0.0 for x in ms), "invalid multiplicity")
        scored.append({
            "family_id": str(family["family_id"]),
            "years": years,
            "per_year": per_year,
            "multiplicity_worst_year": float(min(ms)),
            "multiplicity_geometric_mean": float(math.exp(sum(math.log(x) for x in ms) / len(ms))),
            "v3_min_year_score": float(min(vs)),
            "brown_min_year_score": float(min(bs)),
        })
        if index % 25 == 0 or index == len(families):
            print(f"stage-a multiplicity scoring {index}/{len(families)}", flush=True)
    return scored, {
        "families_requested": len(families),
        "families_scored": len(scored),
        "episode_count": len(episode_sizes),
        "episode_sizes": sorted(set(episode_sizes)),
        "max_brown_equivalence_difference": float(max_brown_difference),
    }


def multiplicity_order(scored: list[dict[str, Any]]) -> list[str]:
    ordered = sorted(
        scored,
        key=lambda row: (
            -float(row["multiplicity_worst_year"]),
            -float(row["multiplicity_geometric_mean"]),
            str(row["family_id"]),
        ),
    )
    return [str(row["family_id"]) for row in ordered]


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    require(os.environ.get("PYTHONHASHSEED") == "0", "PYTHONHASHSEED must be exactly 0")
    source_audit = json.loads(args.source_audit_json.read_text())
    manifest = json.loads(args.freeze_manifest.read_text())
    require(source_audit.get("verdict") == "PASS_V8_FINAL_BLIND_SOURCE_AUDIT", "source audit did not pass")
    require(source_audit.get("target_region_data_access") is False, "source audit accessed target-region data")
    require(source_audit.get("withheld_reference_access") is False, "source audit accessed withheld reference")
    require(manifest.get("schema") == "orbittrace-v8-final-blind-freeze-v1", "wrong freeze manifest schema")
    require(manifest.get("v8_parent_commit") == V8_PARENT_COMMIT, "v8 parent changed")
    require(manifest.get("v8_development_artifact_sha256") == V8_DEVELOPMENT_ARTIFACT_SHA256, "v8 development artifact changed")

    require(all(mult.v3.self_test().values()), "multi-anchor v3 self-test failed")
    require(all(mult.brown.self_test().values()), "Brown self-test failed")
    runtime = mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    require(tuple(runtime.YEARS) == (2022, 2023), "frozen runtime source years changed")
    require(float(runtime.WINDOW_WIDTH_DEG) == 10.0 and int(runtime.EPISODE_SIZE) == EPISODE_SIZE, "episode runtime changed")
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = CORPUS
    support.RANKING_VARIANTS = ("persistence", "mean_year_strength", "sqrt_support_strength", "min_year_strength", "size_penalized_strength")
    require(int(support.SHORTLIST_K) == FIRST_SHORTLIST and int(support.AUDIT_SHORTLIST_K) == AUDIT_SHORTLIST, "shortlist changed")
    require(int(support.MIN_ANCHOR_COUNT) == MIN_ANCHOR_COUNT and int(support.MAX_QUARTETS_PER_BIN) == MAX_QUARTETS_PER_BIN, "proposal gates changed")
    require(int(support.MIN_COMPONENT_EVENTS) == MIN_COMPONENT_EVENTS and int(support.MIN_COMPONENT_QUARTETS) == MIN_COMPONENT_QUARTETS, "component gates changed")
    require(int(support.MIN_FAMILY_YEARS) == MIN_FAMILY_YEARS and abs(float(support.FAMILY_LINK_RADIUS) - FAMILY_LINK_RADIUS) < 1e-15, "family semantics changed")
    _candidate, base, _scorer = support.load_sources(args)
    require(abs(float(getattr(_candidate, "CANDIDATE_SCALE", 4.0)) - 4.0) < 1e-15, "fixed4 scale changed")

    # FIRST TARGET-CONTAINING DATA ACCESS. No withheld reference or shower labels are available here.
    scan_by_year, catalogue_sources = parse_target_containing_catalogue(support, base)

    components: list[dict[str, Any]] = []
    scan_audits: list[dict[str, Any]] = []
    retained_quartets_by_year: dict[str, int] = {}
    for year in YEARS:
        audit, passing, year_components = v6.label_free_scan_year(year, scan_by_year[year], support, base)
        require(audit["calibration_events_used"] == 0 and audit["source_labels_used_for_proposals"] is False, "proposal label boundary changed")
        require(audit["score_threshold_applied"] is False, "unexpected fixed4 score threshold")
        scan_audits.append(audit)
        retained_quartets_by_year[str(year)] = len(passing)
        components.extend(year_components)
        print(f"stage-a year {year}: quartets={len(passing)} components={len(year_components)}", flush=True)

    families, support_rankings = support.build_families(components, base)
    require(len(families) >= MIN_FAMILIES, f"too few recurrent families: {len(families)}")
    family_ids = {str(f["family_id"]) for f in families}
    require(set(map(str, support_rankings["persistence"])) == family_ids, "family universe mismatch")
    repair = repair_pooled_year_centroids(families, components, scan_by_year, support, base)

    scored, scoring_summary = score_families_generic(families, scan_by_year, runtime, base)
    order = multiplicity_order(scored)
    require(set(order) == family_ids and len(order) == len(family_ids), "ranking universe mismatch")
    rank_map = {family_id: rank for rank, family_id in enumerate(order, 1)}
    score_by_id = {str(row["family_id"]): row for row in scored}
    family_by_id = {str(f["family_id"]): f for f in families}
    frozen_families: list[dict[str, Any]] = []
    for family_id in order:
        family = family_by_id[family_id]
        frozen_families.append({
            "rank": rank_map[family_id],
            "family_id": family_id,
            "years": [int(y) for y in family["years"]],
            "year_count": int(family["year_count"]),
            "component_ids": list(family["component_ids"]),
            "component_count": int(family["component_count"]),
            "event_ids": list(map(str, family["event_ids"])),
            "event_count": int(family["event_count"]),
            "quartet_count": int(family["quartet_count"]),
            "anchor_count": int(family["anchor_count"]),
            "best_score": float(family["best_score"]),
            "year_strengths": dict(family["year_strengths"]),
            "pooled_centroids": dict(family["centroids"]),
            "multiplicity_worst_year": float(score_by_id[family_id]["multiplicity_worst_year"]),
            "multiplicity_geometric_mean": float(score_by_id[family_id]["multiplicity_geometric_mean"]),
            "per_year_scores": dict(score_by_id[family_id]["per_year"]),
        })

    scannable_ok = all(int(a["scannable_bin_count"]) >= MIN_SCANNABLE_BINS for a in scan_audits)
    exact_episodes = scoring_summary["episode_sizes"] == [EPISODE_SIZE]
    brown_ok = float(scoring_summary["max_brown_equivalence_difference"]) <= BROWN_EQ_TOL
    integrity = {
        "exact_55_month_universe": [s["key"] for s in catalogue_sources] == list(MONTH_KEYS) and len(catalogue_sources) == 55,
        "no_label_column_resolved_or_read": all(s["label_column_resolved"] is False and s["label_values_read"] is False for s in catalogue_sources),
        "no_calibration_or_score_threshold": all(a["calibration_events_used"] == 0 and a["score_threshold_applied"] is False for a in scan_audits),
        "at_least_24_scannable_bins_each_year": scannable_ok,
        "at_least_100_recurrent_families": len(families) >= MIN_FAMILIES,
        "all_local_episode_sizes_exact_128": exact_episodes,
        "brown_equivalence_within_1e_10": brown_ok,
        "all_families_min_two_years": all(int(f["year_count"]) >= MIN_FAMILY_YEARS for f in families),
        "ranking_complete_and_unique": len(order) == len(family_ids) == len(set(order)),
        "pooled_centroid_repair_structure_preserved": repair["non_centroid_family_structure_unchanged"] is True,
        "withheld_reference_loaded": False,
        "source_labels_used": False,
    }
    require(all(integrity.values()), f"Stage A integrity failure: {integrity}")

    payload = {
        "schema": "orbittrace-v8-stage-a-ranked-families-v1",
        "method": "v8 pooled-year-centroid label-free sparse-support multiplicity",
        "v8_parent_commit": V8_PARENT_COMMIT,
        "input_month_keys": list(MONTH_KEYS),
        "ranking_rule": ["multiplicity_worst_year_desc", "multiplicity_geometric_mean_desc", "family_id_asc"],
        "geometric_mean_definition": "exp(mean(log(M_year))) over family-supported years",
        "families": frozen_families,
    }
    payload_sha256 = sha256_json(payload)
    (args.output / "blind_families.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    (args.output / "blind_families_sha256.txt").write_text(payload_sha256 + "\n")
    freeze = {
        "schema": "orbittrace-v8-stage-a-freeze-v1",
        "verdict": "PASS_STAGE_A_BLIND_DISCOVERY_FREEZE",
        "v8_parent_commit": V8_PARENT_COMMIT,
        "v8_development_artifact_sha256": V8_DEVELOPMENT_ARTIFACT_SHA256,
        "support_source_sha256": SUPPORT_SOURCE_SHA256,
        "wavelet_runtime_sha256": WAVELET_RUNTIME_SHA256,
        "blind_families_sha256": payload_sha256,
        "family_count": len(families),
        "component_count": len(components),
        "retained_quartets_by_year": retained_quartets_by_year,
        "catalogue_sources": catalogue_sources,
        "scan_audits": scan_audits,
        "centroid_repair": repair,
        "scoring_summary": scoring_summary,
        "integrity_gates": integrity,
        "withheld_reference_loaded": False,
        "target_identity_available": False,
        "source_labels_used": False,
        "pythonhashseed": os.environ.get("PYTHONHASHSEED"),
        "git_commit": os.environ.get("GITHUB_SHA"),
        "freeze_manifest_sha256": hashlib.sha256(args.freeze_manifest.read_bytes()).hexdigest(),
        "source_audit_sha256": hashlib.sha256(args.source_audit_json.read_bytes()).hexdigest(),
    }
    (args.output / "stage_a_freeze.json").write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n")
    md = [
        "# Stage A blind discovery freeze",
        "",
        "`PASS_STAGE_A_BLIND_DISCOVERY_FREEZE`",
        "",
        f"- recurrent families: **{len(families)}**",
        f"- within-year components: **{len(components)}**",
        f"- ranked-family payload SHA-256: `{payload_sha256}`",
        "- withheld reference loaded: **false**",
        "- target identity available: **false**",
        "- source labels used: **false**",
        "",
        "No target-match or recovery classification is computed in Stage A.",
    ]
    (args.output / "STAGE_A_BLIND_DISCOVERY.md").write_text("\n".join(md) + "\n")
    print(json.dumps({"verdict": freeze["verdict"], "family_count": len(families), "blind_families_sha256": payload_sha256}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
