#!/usr/bin/env python3
"""One-shot AMOR 1996+1998 external validation of pooled-year-centroid v8."""
from __future__ import annotations

import argparse
import hashlib
import heapq
import importlib.util
import json
import math
import shutil
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any

import numpy as np
import requests

from orbittrace_label_free_sparse_support_v6 import run_development as v6
from orbittrace_pooled_year_centroid_v8 import run_development as v8

mult = v8.mult

YEARS = (1996, 1998)
URLS = {
    1996: "https://ceres.ta3.sk/iaumdcdb/dataDBs/radio_offline/iaumdcamor1996.zip",
    1998: "https://ceres.ta3.sk/iaumdcdb/dataDBs/radio_offline/iaumdcamor1998.zip",
}
EXPECTED_ARCHIVE_SHA256 = {
    1996: "d2444969fff5f99bd74f94b5742f07f36a6ce5dec040adf4832bf7e8ea116de1",
    1998: "f65a562d37d55d0d751d30213350dc333a3620717d3236436a35154e73c3f054",
}
EXPECTED_MEMBER = {1996: "amor1996.csv", 1998: "amor1998.csv"}
EXPECTED_HEADER = (
    "DB", "IC", "Yr", "Mn", "Day", "LS", "RA", "dRA", "DECL", "dDECL", "Vg", "Vh",
    "q", "e", "a", "i", "arg", "nod",
)
EXPECTED_OPAQUE_RECORDS = {1996: 129_210, 1998: 112_159}
EXPECTED_WIDTH_COUNTS_INCLUDING_HEADER = {
    1996: {17: 546, 18: 128_665},
    1998: {17: 371, 18: 111_789},
}
BLIND_LOW = 20.0
BLIND_HIGH = 55.0
MAX_EVENTS_PER_BIN = 10_000
TOP_K = 100
MIN_SCANNABLE_BINS = 24
MIN_FAMILIES = 100
MIN_ORBITALLY_CORROBORATED = 30
DSH_THRESHOLD = 0.05
MIN_YEAR_ORBIT_MEMBERS = 4
MIN_ORBITAL_PRECISION = 0.50
BROWN_EQ_TOL = 1e-10

EXPECTED_V8_ARTIFACT_DIGEST = "sha256:88d2d607e05d027015c338f7e23b64a6195e55ae24f1b2ac745f5e9bc6df599e"
EXPECTED_STRUCTURE_ARTIFACT_DIGEST = "sha256:9f3646a37e519b2de121b0e4083cc92b795ec72f09e3f0ce0fafc48c2aed12dc"
EXPECTED_SAAMER_EVALUATOR_BLOB = "16a4e832893cbc689ff084510f792349035e5ff7"
EXPECTED_DSH_BLOB = "ab17e1205d72d8ab8361d8ba6cdad2e4c31fdcb2"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--v8-result-json", required=True, type=Path)
    p.add_argument("--structure-json", required=True, type=Path)
    p.add_argument("--saamer-evaluator", required=True, type=Path)
    p.add_argument("--dsh-comparator", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_module(path: Path, name: str) -> Any:
    require(path.is_file(), f"missing frozen source: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def parse_float_token(token: bytes) -> float | None:
    try:
        value = float(token)
    except Exception:
        return None
    return value if math.isfinite(value) else None


def stable_identity_hash(year: int, member: str, physical_row: int) -> int:
    payload = f"AMOR|{year}|{member}|{physical_row}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest(), "big", signed=False)


def _heap_push_smallest(heap: list[tuple[int, str, dict[str, Any]]], hash_value: int, event: dict[str, Any]) -> None:
    item = (-hash_value, str(event["id"]), event)
    if len(heap) < MAX_EVENTS_PER_BIN:
        heapq.heappush(heap, item)
        return
    if hash_value < -heap[0][0]:
        heapq.heapreplace(heap, item)


def download_archive(year: int, root: Path) -> Path:
    path = root / f"iaumdcamor{year}.zip"
    with requests.get(URLS[year], timeout=300, stream=True, headers={"User-Agent": "OrbitTrace-v8-AMOR-external/1.0"}) as response:
        response.raise_for_status()
        with path.open("wb") as fh:
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    fh.write(chunk)
    digest = sha256_file(path)
    require(digest == EXPECTED_ARCHIVE_SHA256[year], f"AMOR {year} archive SHA changed: {digest}")
    require(zipfile.is_zipfile(path), f"AMOR {year} archive is not ZIP")
    with zipfile.ZipFile(path) as zf:
        require(zf.testzip() is None, f"AMOR {year} ZIP CRC failure")
        names = [PurePosixPath(name).name for name in zf.namelist() if not name.endswith("/")]
        require(names == [EXPECTED_MEMBER[year]], f"AMOR {year} member set changed: {names}")
    return path


def split_csv(raw: bytes) -> list[bytes]:
    return [token.strip() for token in raw.rstrip(b"\r\n").split(b",")]


def verify_header_and_widths(year: int, path: Path) -> dict[str, Any]:
    widths = Counter()
    nonempty = 0
    header_seen = False
    with zipfile.ZipFile(path) as zf, zf.open(EXPECTED_MEMBER[year], "r") as fh:
        for physical_row, raw in enumerate(fh, start=1):
            if not raw.strip():
                continue
            nonempty += 1
            tokens = split_csv(raw)
            widths[len(tokens)] += 1
            if not header_seen:
                decoded = tuple(token.decode("utf-8", errors="strict") for token in tokens)
                require(decoded == EXPECTED_HEADER, f"AMOR {year} header changed: {decoded}")
                require(physical_row == 1, f"AMOR {year} header not first physical row")
                header_seen = True
    require(header_seen, f"AMOR {year} header missing")
    require(nonempty - 1 == EXPECTED_OPAQUE_RECORDS[year], f"AMOR {year} opaque row count changed")
    require(dict(widths) == EXPECTED_WIDTH_COUNTS_INCLUDING_HEADER[year], f"AMOR {year} structural width counts changed: {dict(widths)}")
    return {
        "year": year,
        "member": EXPECTED_MEMBER[year],
        "header": list(EXPECTED_HEADER),
        "nonempty_lines": nonempty,
        "opaque_data_records": nonempty - 1,
        "width_counts_including_header": {str(k): int(v) for k, v in sorted(widths.items())},
        "accepted_width": 18,
        "malformed_width_policy": "drop_without_repair_or_scientific_interpretation",
    }


def parse_geometry_and_sample(year: int, archive_path: Path, base: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    heaps: dict[int, list[tuple[int, str, dict[str, Any]]]] = {idx: [] for idx in range(36)}
    counts_by_bin = Counter()
    raw_data_rows = 0
    malformed_width_dropped = 0
    blind_removed = 0
    invalid_sol = 0
    invalid_geometry = 0
    wrong_year_or_month = 0
    eligible_geometry = 0
    member = EXPECTED_MEMBER[year]

    with zipfile.ZipFile(archive_path) as zf, zf.open(member, "r") as fh:
        for physical_row, raw in enumerate(fh, start=1):
            if not raw.strip():
                continue
            tokens = split_csv(raw)
            if physical_row == 1:
                decoded = tuple(token.decode("utf-8", errors="strict") for token in tokens)
                require(decoded == EXPECTED_HEADER, f"AMOR {year} header changed during scientific pass")
                continue
            raw_data_rows += 1
            if len(tokens) != 18:
                malformed_width_dropped += 1
                continue

            # CRITICAL BLINDNESS BOUNDARY: LS is the first data value interpreted.
            sol = parse_float_token(tokens[5])
            if sol is None or not (0.0 <= sol < 360.0):
                invalid_sol += 1
                continue
            if BLIND_LOW <= sol <= BLIND_HIGH:
                blind_removed += 1
                continue

            # No radiant, speed, orbit, or nominal date field is interpreted before the blind cut above.
            row_year = parse_float_token(tokens[2])
            row_month = parse_float_token(tokens[3])
            if row_year is None or row_month is None or int(row_year) != year or not (1 <= int(row_month) <= 12):
                wrong_year_or_month += 1
                continue

            ra = parse_float_token(tokens[6])
            dec = parse_float_token(tokens[8])
            vg = parse_float_token(tokens[10])
            if not (
                ra is not None and 0.0 <= ra < 360.0
                and dec is not None and -90.0 <= dec <= 90.0
                and vg is not None and 5.0 < vg < 75.0
            ):
                invalid_geometry += 1
                continue

            ecl_lon, ecl_lat = base.equatorial_to_ecliptic(ra, dec)
            event_id = f"AMOR|{year}|{member}|{physical_row}"
            event = {
                "id": event_id,
                "year": year,
                "sol": float(sol),
                "sun_lon": float(base.wrap180(float(ecl_lon) - float(sol))),
                "ecl_lat": float(ecl_lat),
                "vg": float(vg),
            }
            bin_index = int(sol // 10.0) % 36
            counts_by_bin[bin_index] += 1
            eligible_geometry += 1
            _heap_push_smallest(heaps[bin_index], stable_identity_hash(year, member, physical_row), event)

    events: list[dict[str, Any]] = []
    selected_by_bin: dict[str, int] = {}
    for bin_index in range(36):
        chosen = [item[2] for item in heaps[bin_index]]
        chosen.sort(key=lambda event: str(event["id"]))
        events.extend(chosen)
        selected_by_bin[str(bin_index)] = len(chosen)
    events.sort(key=lambda event: str(event["id"]))

    return events, {
        "year": year,
        "member": member,
        "raw_data_rows": raw_data_rows,
        "malformed_width_dropped_before_any_scientific_conversion": malformed_width_dropped,
        "invalid_sol": invalid_sol,
        "blind_removed_before_radiant_speed_or_date": blind_removed,
        "wrong_year_or_month_after_blind": wrong_year_or_month,
        "invalid_geometry_after_blind": invalid_geometry,
        "eligible_geometry_before_density_cap": eligible_geometry,
        "eligible_by_bin_before_cap": {str(k): int(v) for k, v in sorted(counts_by_bin.items())},
        "selected_by_bin": selected_by_bin,
        "selected_events": len(events),
        "density_cap": MAX_EVENTS_PER_BIN,
        "density_selection": "10,000 smallest SHA256(AMOR|year|member|physical_row) per fixed 10-degree bin",
        "radiant_speed_interpreted_only_after_blind": True,
        "orbital_elements_interpreted": False,
    }


def apply_pooled_year_centroids(
    families: list[dict[str, Any]],
    components: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
    support: Any,
    base: Any,
) -> dict[str, Any]:
    component_by_id = {str(c["component_id"]): c for c in components}
    require(len(component_by_id) == len(components), "component IDs are not unique")
    event_lookup = {year: {str(e["id"]): e for e in scan_by_year[year]} for year in YEARS}
    duplicate_families = 0
    duplicate_family_years = 0
    single_distances: list[float] = []
    duplicate_distances: list[float] = []

    for family in families:
        pooled: dict[str, dict[str, float]] = {}
        family_has_duplicate = False
        for year in YEARS:
            year_components = [
                component_by_id[str(cid)] for cid in family["component_ids"]
                if int(component_by_id[str(cid)]["year"]) == year
            ]
            require(year_components, f"family {family['family_id']} missing {year} component")
            if len(year_components) > 1:
                family_has_duplicate = True
                duplicate_family_years += 1
            event_ids = sorted(set().union(*(set(str(x) for x in c["event_ids"]) for c in year_components)))
            require(event_ids and all(eid in event_lookup[year] for eid in event_ids), "pooled family-year event lookup failed")
            center = v8.pooled_centroid([event_lookup[year][eid] for eid in event_ids], support)
            pooled[str(year)] = center
            if len(year_components) == 1:
                single_distances.append(float(support.centroid_distance(center, year_components[0]["centroid"], base)))
            else:
                duplicate_distances.append(float(support.centroid_distance(center, family["centroids"][str(year)], base)))
        if family_has_duplicate:
            duplicate_families += 1
        family["centroids"] = pooled

    max_single = max(single_distances) if single_distances else 0.0
    require(max_single <= 1e-12, f"pooled centroid lost single-component equivalence: {max_single}")
    return {
        "families_with_duplicate_same_year_components": duplicate_families,
        "duplicate_family_years": duplicate_family_years,
        "single_component_family_years": len(single_distances),
        "max_single_component_centroid_distance": float(max_single),
        "duplicate_year_old_to_pooled_distance_median": float(np.median(duplicate_distances)) if duplicate_distances else None,
        "duplicate_year_old_to_pooled_distance_max": float(max(duplicate_distances)) if duplicate_distances else None,
        "pooling_statistic": {"sol": "circular_mean_deg", "sun_lon": "circular_mean_deg", "ecl_lat": "median", "vg": "median"},
    }


def parse_event_id(event_id: str) -> tuple[int, str, int]:
    parts = event_id.split("|")
    require(len(parts) == 4 and parts[0] == "AMOR", f"invalid AMOR event id: {event_id}")
    return int(parts[1]), parts[2], int(parts[3])


def read_orbits_after_rank_freeze(
    archive_paths: dict[int, Path], needed_ids: set[str]
) -> tuple[dict[str, dict[str, float]], dict[str, Any]]:
    wanted: dict[tuple[int, str], dict[int, str]] = {}
    for event_id in needed_ids:
        year, member, row = parse_event_id(event_id)
        wanted.setdefault((year, member), {})[row] = event_id

    orbits: dict[str, dict[str, float]] = {}
    invalid = 0
    for (year, member), row_map in sorted(wanted.items()):
        require(member == EXPECTED_MEMBER[year], f"unexpected orbital reread member {year}:{member}")
        with zipfile.ZipFile(archive_paths[year]) as zf, zf.open(member, "r") as fh:
            for physical_row, raw in enumerate(fh, start=1):
                event_id = row_map.get(physical_row)
                if event_id is None:
                    continue
                tokens = split_csv(raw)
                require(len(tokens) == 18, f"ranked event changed width on orbital reread: {event_id}")
                q = parse_float_token(tokens[12])
                e = parse_float_token(tokens[13])
                inc = parse_float_token(tokens[15])
                peri = parse_float_token(tokens[16])
                node = parse_float_token(tokens[17])
                if not (
                    q is not None and q > 0.0
                    and e is not None and e >= 0.0
                    and inc is not None and 0.0 <= inc <= 180.0
                    and peri is not None and node is not None
                ):
                    invalid += 1
                    continue
                orbits[event_id] = {
                    "q": float(q), "e": float(e), "i": float(inc),
                    "arg": float(peri % 360.0), "node": float(node % 360.0),
                }
    return orbits, {
        "needed_family_events": len(needed_ids),
        "valid_orbital_events": len(orbits),
        "invalid_or_missing_orbital_events": len(needed_ids) - len(orbits),
        "explicit_invalid_orbital_rows": invalid,
        "orbital_elements_interpreted_only_after_rank_freeze": True,
    }


def ranking_digest(order: list[str]) -> str:
    payload = json.dumps(order, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    # Every prerequisite below is checked before the first AMOR numeric scientific token is read.
    v8_result = json.loads(args.v8_result_json.read_text())
    require(v8_result["verdict"] == "PASS_POOLED_YEAR_CENTROID_V8_DEVELOPMENT", "v8 did not pass")
    require(all(v8_result["integrity_gates"].values()) and all(v8_result["scientific_gates"].values()), "v8 gates changed")
    require(v8_result["family_count"] == 226, "v8 family baseline changed")
    require(v8_result["configuration"]["family_builder"] == "exact passed-v6 connected recurrent family graph", "v8 topology changed")
    require(v8_result["configuration"]["centroid_statistic"] == {"sol":"circular_mean_deg","sun_lon":"circular_mean_deg","ecl_lat":"median","vg":"median"}, "v8 centroid statistic changed")

    structure_result = json.loads(args.structure_json.read_text())
    require(structure_result["verdict"] == "PASS_AMOR_1990_1999_STRUCTURE_AUDIT", "AMOR structure audit did not pass")
    require(structure_result["selected_years"] == list(YEARS), "AMOR selected panel changed")
    require(structure_result["scientific_value_interpretation"] is False, "structure audit interpreted values")
    require(structure_result["scientific_token_conversion_performed"] is False, "structure audit converted scientific tokens")
    require(structure_result["target_information_access"] is False, "structure audit accessed target")
    structure_by_year = {int(a["year"]): a for a in structure_result["archives"]}
    for year in YEARS:
        require(structure_by_year[year]["url"] == URLS[year], f"AMOR {year} URL changed")
        require(structure_by_year[year]["archive_sha256"] == EXPECTED_ARCHIVE_SHA256[year], f"AMOR {year} structure SHA changed")
        require(int(structure_by_year[year]["opaque_data_record_count"]) == EXPECTED_OPAQUE_RECORDS[year], f"AMOR {year} record count changed")

    require(all(mult.v3.self_test().values()), "multi-anchor v3 self-test failed")
    require(all(mult.brown.self_test().values()), "Brown self-test failed")
    runtime = mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = tuple()
    support.CORPUS = "orbittrace-v8-amor-1996-1998-external"
    support.RANKING_VARIANTS = ("persistence", "mean_year_strength", "sqrt_support_strength", "min_year_strength", "size_penalized_strength")
    require(float(support.BLIND_LOW) == BLIND_LOW and float(support.BLIND_HIGH) == BLIND_HIGH, "blind interval changed")
    require(int(support.MIN_FAMILY_YEARS) == 2, "family-year minimum changed")
    require(abs(float(support.FAMILY_LINK_RADIUS) - 1.5) < 1e-15, "family link radius changed")
    require(int(support.MIN_COMPONENT_EVENTS) == 4 and int(support.MIN_COMPONENT_QUARTETS) == 2, "component gates changed")
    require(int(support.SHORTLIST_K) == 64 and int(support.AUDIT_SHORTLIST_K) == 128, "shortlists changed")
    require(int(support.MIN_ANCHOR_COUNT) == 2 and int(support.MAX_QUARTETS_PER_BIN) == 512, "proposal gates changed")

    setattr(args, "fixed4_baseline_json", args.v8_result_json)
    _candidate, base, _scorer = support.load_sources(args)
    require(abs(float(getattr(_candidate, "CANDIDATE_SCALE", 4.0)) - 4.0) < 1e-15, "fixed4 candidate scale changed")

    saamer = load_module(args.saamer_evaluator, "frozen_saamer_external_evaluator")
    require(float(saamer.DSH_THRESHOLD) == DSH_THRESHOLD, "SAAMER D_SH threshold changed")
    require(int(saamer.MIN_YEAR_ORBIT_MEMBERS) == MIN_YEAR_ORBIT_MEMBERS, "SAAMER per-year orbital floor changed")
    require(float(saamer.MIN_ORBITAL_PRECISION) == MIN_ORBITAL_PRECISION, "SAAMER orbital precision changed")
    require(int(saamer.TOP_K) == TOP_K, "SAAMER top-K changed")
    dsh = saamer.load_dsh_module(args.dsh_comparator)
    saamer.YEARS = YEARS
    saamer.TOP_K = TOP_K
    saamer.parse_event_id = parse_event_id

    archive_root = args.output / "_raw_amor"
    archive_root.mkdir(exist_ok=True)
    archive_paths: dict[int, Path] = {}
    structure_checks: list[dict[str, Any]] = []
    geometry_audits: list[dict[str, Any]] = []
    scan_by_year: dict[int, list[dict[str, Any]]] = {}

    try:
        # Archive transport/hashes are non-scientific. FIRST AMOR SCIENTIFIC-VALUE ACCESS is inside parse_geometry_and_sample.
        for year in YEARS:
            archive_paths[year] = download_archive(year, archive_root)
            structure_checks.append(verify_header_and_widths(year, archive_paths[year]))

        for year in YEARS:
            events, audit = parse_geometry_and_sample(year, archive_paths[year], base)
            scan_by_year[year] = events
            geometry_audits.append(audit)
            print(f"AMOR {year}: eligible={audit['eligible_geometry_before_density_cap']} selected={audit['selected_events']}", flush=True)

        components: list[dict[str, Any]] = []
        scan_audits: list[dict[str, Any]] = []
        retained_counts: dict[str, int] = {}
        for year in YEARS:
            audit, passing, year_components = v6.label_free_scan_year(year, scan_by_year[year], support, base)
            scan_audits.append(audit)
            retained_counts[str(year)] = len(passing)
            components.extend(year_components)
            print(f"AMOR v8 {year}: quartets={len(passing)} components={len(year_components)}", flush=True)

        # Exact v6 connected-family topology, then the sole v8 pooled-year centroid repair.
        families, support_rankings = support.build_families(components, base)
        persistence_order = [str(value) for value in support_rankings["persistence"]]
        family_ids = [str(family["family_id"]) for family in families]
        require(set(persistence_order) == set(family_ids) and len(persistence_order) == len(family_ids), "persistence universe mismatch")
        pooled_audit = apply_pooled_year_centroids(families, components, scan_by_year, support, base)

        mult.YEARS = YEARS
        mult.TOP_K = TOP_K
        scored, scoring_summary = mult.score_families(families, scan_by_year, runtime, base)
        require(len(scored) == len(families), "not every AMOR recurrent family received a score")
        rankings = {
            "multiplicity": mult.rank_scored(scored, "multiplicity"),
            "brown": mult.rank_scored(scored, "brown"),
            "v3": mult.rank_scored(scored, "v3"),
            "label_free_persistence": persistence_order,
        }
        require(all(set(order) == set(family_ids) and len(order) == len(family_ids) for order in rankings.values()), "ranking universe changed")
        ranking_hashes = {name: ranking_digest(order) for name, order in rankings.items()}
        rankings_frozen_before_orbit_access = True

        # FIRST ORBITAL-ELEMENT INTERPRETATION: all discovery families and all rankings are immutable above.
        needed_ids = {str(event_id) for family in families for event_id in family["event_ids"]}
        orbits, orbit_read_audit = read_orbits_after_rank_freeze(archive_paths, needed_ids)
        corroboration, orbital_summary = saamer.orbital_corroboration(families, orbits, dsh)
        metrics = {name: saamer.evaluate_ranking(order, corroboration) for name, order in rankings.items()}

        n = len(families)
        q = int(orbital_summary["orbitally_corroborated_families"])
        k = min(TOP_K, n)
        multiplicity_x = int(metrics["multiplicity"]["top_k_orbitally_corroborated"])
        brown_x = int(metrics["brown"]["top_k_orbitally_corroborated"])
        persistence_x = int(metrics["label_free_persistence"]["top_k_orbitally_corroborated"])
        required_vs_persistence = int(math.ceil(0.90 * persistence_x))

        density_exact = all(
            audit["density_cap"] == MAX_EVENTS_PER_BIN
            and all(int(value) <= MAX_EVENTS_PER_BIN for value in audit["selected_by_bin"].values())
            for audit in geometry_audits
        )
        exact_years = all(sorted(int(y) for y in family["years"]) == list(YEARS) for family in families)
        scannable = all(int(a["scannable_bin_count"]) >= MIN_SCANNABLE_BINS for a in scan_audits)
        shortlist_exact = all(int(a["shortlist_audit_failures"]) == 0 for a in scan_audits)
        exact_episode_sizes = scoring_summary["episode_sizes"] == [128] if families else False
        width_policy_exact = all(
            int(a["malformed_width_dropped_before_any_scientific_conversion"])
            == EXPECTED_WIDTH_COUNTS_INCLUDING_HEADER[int(a["year"])][17]
            for a in geometry_audits
        )

        integrity_gates = {
            "passed_frozen_v8_prerequisite": True,
            "passed_structure_only_prerequisite_and_exact_selected_panel": True,
            "exact_selected_archive_hashes_members_headers_and_widths": all(
                check["header"] == list(EXPECTED_HEADER) and check["accepted_width"] == 18 for check in structure_checks
            ),
            "malformed_width_rows_dropped_without_repair": width_policy_exact,
            "target_interval_removed_before_radiant_speed_or_date": all(a["radiant_speed_interpreted_only_after_blind"] is True for a in geometry_audits),
            "identity_hash_density_normalization_exact_10000": density_exact,
            "at_least_24_scannable_bins_each_year": scannable,
            "shortlist_audit_failures_zero": shortlist_exact,
            "all_families_span_exact_selected_years": exact_years,
            "v8_pooled_centroid_statistic_exact": pooled_audit["pooling_statistic"] == {"sol":"circular_mean_deg","sun_lon":"circular_mean_deg","ecl_lat":"median","vg":"median"},
            "single_component_centroid_equivalence": float(pooled_audit["max_single_component_centroid_distance"]) <= 1e-12,
            "all_local_episode_sizes_exact_128": exact_episode_sizes,
            "brown_equivalence_within_1e_10": float(scoring_summary["max_brown_equivalence_difference"]) <= BROWN_EQ_TOL,
            "rankings_frozen_before_orbit_access": rankings_frozen_before_orbit_access and orbit_read_audit["orbital_elements_interpreted_only_after_rank_freeze"] is True,
            "no_label_input": True,
            "no_target_information_input": True,
        }
        power_gates = {
            "at_least_100_recurrent_families": n >= MIN_FAMILIES,
            "at_least_30_orbitally_corroborated_families": q >= MIN_ORBITALLY_CORROBORATED,
        }
        scientific_gates = {
            "multiplicity_topk_at_least_brown_plus_one": multiplicity_x >= brown_x + 1,
            "multiplicity_topk_at_least_90pct_persistence": multiplicity_x >= required_vs_persistence,
            "multiplicity_hypergeometric_enrichment_p_at_most_005": float(metrics["multiplicity"]["hypergeometric_enrichment_p"]) <= 0.05,
        }

        if not all(integrity_gates.values()):
            verdict = "FAIL_V8_AMOR_EXTERNAL_INTEGRITY"
        elif not all(power_gates.values()):
            verdict = "INCONCLUSIVE_V8_AMOR_EXTERNAL_POWER"
        elif all(scientific_gates.values()):
            verdict = "PASS_V8_AMOR_EXTERNAL_VALIDATION"
        else:
            verdict = "FAIL_V8_AMOR_EXTERNAL_VALIDATION"

        result = {
            "verdict": verdict,
            "configuration": {
                "years": list(YEARS),
                "blind_exclusion": [BLIND_LOW, BLIND_HIGH],
                "accepted_csv_width": 18,
                "malformed_width_policy": "drop_without_repair_or_inference",
                "density_cap_per_10deg_bin": MAX_EVENTS_PER_BIN,
                "density_selection": "smallest SHA256 fixed row identity",
                "family_builder": "exact v6 connected recurrent family graph",
                "family_link_radius": 1.5,
                "centroid_repair": "exact v8 pooled same-year unique-event centroid",
                "centroid_statistic": pooled_audit["pooling_statistic"],
                "episode_size": 128,
                "primary_ranking": "multiplicity",
                "top_k_rule": "min(100,N)",
                "dsh_threshold": DSH_THRESHOLD,
                "minimum_orbit_members_each_year": MIN_YEAR_ORBIT_MEMBERS,
                "minimum_orbital_component_precision": MIN_ORBITAL_PRECISION,
                "no_threshold_radius_cap_pooling_weight_or_endpoint_search": True,
                "no_rrf": True,
            },
            "prerequisites": {
                "v8_artifact_digest": EXPECTED_V8_ARTIFACT_DIGEST,
                "structure_artifact_digest": EXPECTED_STRUCTURE_ARTIFACT_DIGEST,
                "saamer_evaluator_blob": EXPECTED_SAAMER_EVALUATOR_BLOB,
                "dsh_comparator_blob": EXPECTED_DSH_BLOB,
            },
            "structure_checks": structure_checks,
            "geometry_audits": geometry_audits,
            "retained_quartet_counts": retained_counts,
            "scan_audits": scan_audits,
            "family_count": n,
            "pooled_centroid_audit": pooled_audit,
            "family_scoring_summary": scoring_summary,
            "ranking_sha256_before_orbit_access": ranking_hashes,
            "orbital_read_audit": orbit_read_audit,
            "orbital_summary": orbital_summary,
            "metrics": metrics,
            "top_k": k,
            "required_multiplicity_topk_vs_persistence": required_vs_persistence,
            "integrity_gates": integrity_gates,
            "power_gates": power_gates,
            "scientific_gates": scientific_gates,
            "claim_boundary": "One-shot external AMOR validation of frozen pooled-year-centroid v8. The 20-55 degree target interval was removed before radiant/speed/date interpretation; no source label or OrbitTrace target information entered proposal generation, family formation, pooled centroids, scoring, or ranking. Orbital elements were first interpreted only after all rankings were frozen. A powered pass authorizes a separately frozen target-free GMN discovery scan, not target reveal.",
        }
        args.output.joinpath("v8_amor_1996_1998_external_validation.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        args.output.joinpath("v8_amor_rankings.json").write_text(json.dumps(rankings, indent=2, sort_keys=True) + "\n")
        args.output.joinpath("v8_amor_orbital_corroboration.json").write_text(json.dumps(corroboration, indent=2, sort_keys=True) + "\n")
        md = [
            "# v8 AMOR 1996+1998 external validation",
            "",
            f"**Verdict:** `{verdict}`",
            "",
            f"- recurrent families N: {n}",
            f"- orbitally corroborated families Q: {q}",
            f"- K: {k}",
            f"- multiplicity / Brown / persistence corroborated@K: {multiplicity_x} / {brown_x} / {persistence_x}",
            f"- multiplicity enrichment p: {metrics['multiplicity']['hypergeometric_enrichment_p']:.6g}",
            f"- duplicate-family-years pooled: {pooled_audit['duplicate_family_years']}",
            "",
            "No OrbitTrace target information entered this run.",
        ]
        args.output.joinpath("V8_AMOR_1996_1998_EXTERNAL_VALIDATION.md").write_text("\n".join(md) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    finally:
        shutil.rmtree(archive_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
