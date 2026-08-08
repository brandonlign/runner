#!/usr/bin/env python3
"""Frozen first scientific-value stage for MAARSY 2016/2017 under promoted v8.

Reads solar longitude first, applies the frozen 20-55 degree exclusion, then reads
only retained rows' slat/slon/vels. Orbital and label fields are never opened.
"""
from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import math
import re
import tarfile
from collections import Counter
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import requests

from orbittrace_label_free_sparse_support_v6 import run_development as v6
from orbittrace_pooled_year_centroid_v8 import run_development as v8

mult = v8.mult

YEARS = (2016, 2017)
CONTENT_URL = "https://zenodo.org/api/records/15553437/files/silseth_thesis_data.tar.gz/content"
ZENODO_RECORD_URL = "https://zenodo.org/api/records/15553437"
EXPECTED_FILE_KEY = "silseth_thesis_data.tar.gz"
EXPECTED_FILE_SIZE = 21_485_785_089
EXPECTED_FILE_MD5 = "01820c6a90ea1415b011bb013a4d9213"
EXPECTED_V8_ARTIFACT_SHA256 = "88d2d607e05d027015c338f7e23b64a6195e55ae24f1b2ac745f5e9bc6df599e"
BLIND_LOW = 20.0
BLIND_HIGH = 55.0
MAX_EVENTS_PER_BIN = 10_000
MIN_SCANNABLE_BINS = 24
MIN_FAMILIES = 100
BROWN_EQ_TOL = 1e-10
TOP_K = 100
MONTH_RE = re.compile(r"^data/(2016|2017)/(0[1-9]|1[0-2])/kep_collect\.h5$")
NEXT_YEAR_PREFIX = "data/2018/"
REQUIRED_GEOMETRY_DATASETS = ("sun_lon", "slat", "slon", "vels")
FORBIDDEN_OPEN_DATASETS = (
    "kepler", "kepler_std", "t0", "fn", "cnn_input", "cnn_output", "rcs",
    "h0", "dynamic_pressure", "path_length", "bc", "max_snr", "min_anemone",
    "zenith_angle",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--source-audit-json", required=True, type=Path)
    p.add_argument("--v8-result-json", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def event_id(year: int, member: str, row_index: int) -> str:
    return f"MAARSY|{year}|{member}|{row_index}"


def identity_hash(text: str) -> int:
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest(), "big", signed=False)


def heap_push_smallest(heap: list[tuple[int, str, dict[str, Any]]], event: dict[str, Any]) -> None:
    eid = str(event["id"])
    hv = identity_hash(eid)
    item = (-hv, eid, event)
    if len(heap) < MAX_EVENTS_PER_BIN:
        heapq.heappush(heap, item)
        return
    if hv < -heap[0][0] or (hv == -heap[0][0] and eid < heap[0][1]):
        heapq.heapreplace(heap, item)


def verify_zenodo_metadata() -> dict[str, Any]:
    response = requests.get(
        ZENODO_RECORD_URL,
        timeout=120,
        headers={"Accept": "application/json", "User-Agent": "OrbitTrace-v8-MAARSY-external/1.0"},
    )
    response.raise_for_status()
    obj = response.json()
    files = obj.get("files", [])
    require(len(files) == 1, f"Zenodo file count changed: {len(files)}")
    f = files[0]
    require(f.get("key") == EXPECTED_FILE_KEY, f"Zenodo file key changed: {f.get('key')!r}")
    require(int(f.get("size")) == EXPECTED_FILE_SIZE, f"Zenodo file size changed: {f.get('size')!r}")
    checksum = str(f.get("checksum", ""))
    require(checksum == f"md5:{EXPECTED_FILE_MD5}", f"Zenodo checksum changed: {checksum!r}")
    content = str((f.get("links") or {}).get("content", ""))
    require(content == CONTENT_URL, f"Zenodo content URL changed: {content!r}")
    return {
        "record_id": int(obj.get("id")),
        "file_key": f["key"],
        "file_size": int(f["size"]),
        "checksum": checksum,
        "content_url": content,
    }


def _read_retained(ds: h5py.Dataset, indices: np.ndarray) -> np.ndarray:
    """Read only already-unblinded monotonically increasing row indices."""
    if len(indices) == 0:
        return np.asarray([], dtype=np.float64)
    require(indices.ndim == 1 and np.all(indices[1:] > indices[:-1]), "retained row indices not strictly increasing")
    return np.asarray(ds[indices], dtype=np.float64)


def parse_month_hdf5(
    path: Path,
    year: int,
    member: str,
    heaps: dict[int, list[tuple[int, str, dict[str, Any]]]],
) -> dict[str, Any]:
    digest = sha256_file(path)
    with h5py.File(path, "r") as h:
        for name in REQUIRED_GEOMETRY_DATASETS:
            require(name in h and isinstance(h[name], h5py.Dataset), f"{member}: missing dataset {name}")
        n = int(h["sun_lon"].shape[0]) if len(h["sun_lon"].shape) == 1 else -1
        require(n >= 0, f"{member}: sun_lon is not rank-1")
        for name in REQUIRED_GEOMETRY_DATASETS:
            ds = h[name]
            require(ds.shape == (n,), f"{member}: shape mismatch for {name}: {ds.shape}")
            require(ds.dtype.kind in "fi", f"{member}: nonnumeric geometry dtype for {name}: {ds.dtype}")
        # Explicit guard: no forbidden dataset is dereferenced anywhere in this function.
        present_forbidden = sorted(name for name in FORBIDDEN_OPEN_DATASETS if name in h)

        # FIRST SCIENTIFIC VALUES: solar longitude only. Radiant/speed arrays remain unread.
        sol_all = np.asarray(h["sun_lon"][()], dtype=np.float64)
        finite_sol = np.isfinite(sol_all)
        valid_sol = finite_sol & (sol_all >= 0.0) & (sol_all < 360.0)
        invalid_sol = int(np.count_nonzero(~valid_sol))
        blind = valid_sol & (sol_all >= BLIND_LOW) & (sol_all <= BLIND_HIGH)
        keep_idx = np.flatnonzero(valid_sol & ~blind).astype(np.int64)

        # FIRST RADIANT/SPEED ACCESS: retained indices only, after the blind mask is immutable.
        slat = _read_retained(h["slat"], keep_idx)
        slon = _read_retained(h["slon"], keep_idx)
        vels = _read_retained(h["vels"], keep_idx)

    require(len(slat) == len(keep_idx) == len(slon) == len(vels), f"{member}: retained geometry length mismatch")
    sol = sol_all[keep_idx]
    finite_geom = np.isfinite(slat) & np.isfinite(slon) & np.isfinite(vels)
    range_geom = (slat >= -90.0) & (slat <= 90.0) & (vels >= 5.0) & (vels <= 75.0)
    good = finite_geom & range_geom
    invalid_geometry = int(np.count_nonzero(~good))

    eligible_by_bin = Counter()
    for local_i in np.flatnonzero(good):
        row_index = int(keep_idx[int(local_i)])
        eid = event_id(year, member, row_index)
        sol_v = float(sol[int(local_i)])
        slon_v = float(slon[int(local_i)])
        slat_v = float(slat[int(local_i)])
        vg_v = float(vels[int(local_i)])
        e = {
            "id": eid,
            "year": year,
            "sol": sol_v,
            "sun_lon": float(((slon_v + 180.0) % 360.0) - 180.0),
            "ecl_lat": slat_v,
            "vg": vg_v,
        }
        bin_index = int(sol_v // 10.0) % 36
        eligible_by_bin[bin_index] += 1
        heap_push_smallest(heaps[bin_index], e)

    return {
        "year": year,
        "member": member,
        "member_sha256": digest,
        "rows": n,
        "invalid_solar_longitude_rows": invalid_sol,
        "blind_removed_before_radiant_speed_read": int(np.count_nonzero(blind)),
        "radiant_speed_rows_read": int(len(keep_idx)),
        "invalid_geometry_after_blind": invalid_geometry,
        "eligible_geometry_before_density_cap": int(np.count_nonzero(good)),
        "eligible_by_bin_before_cap": {str(k): int(v) for k, v in sorted(eligible_by_bin.items())},
        "forbidden_datasets_present_but_unopened": present_forbidden,
        "orbital_dataset_opened": False,
        "target_interval_radiant_speed_read": False,
    }


def stream_selected_panel(tmp: Path) -> tuple[dict[int, list[dict[str, Any]]], dict[str, Any]]:
    heaps_by_year = {
        year: {idx: [] for idx in range(36)} for year in YEARS
    }
    member_audits: list[dict[str, Any]] = []
    selected_months: dict[int, list[int]] = {year: [] for year in YEARS}
    selected_members: list[str] = []
    ignored_member_headers = 0
    stopped_at_2018_header: str | None = None

    with requests.get(
        CONTENT_URL,
        timeout=(60, 600),
        stream=True,
        headers={"User-Agent": "OrbitTrace-v8-MAARSY-external/1.0", "Accept-Encoding": "identity"},
    ) as response:
        response.raise_for_status()
        total = response.headers.get("Content-Length")
        if total is not None:
            require(int(total) == EXPECTED_FILE_SIZE, f"MAARSY content length changed: {total}")
        response.raw.decode_content = False
        with tarfile.open(fileobj=response.raw, mode="r|gz") as tf:
            for member in tf:
                name = member.name.lstrip("./")
                if name.startswith(NEXT_YEAR_PREFIX):
                    stopped_at_2018_header = name
                    break
                match = MONTH_RE.fullmatch(name)
                if match is None:
                    ignored_member_headers += 1
                    continue
                require(member.isfile(), f"selected MAARSY member is not regular file: {name}")
                year = int(match.group(1))
                month = int(match.group(2))
                require(month not in selected_months[year], f"duplicate selected year-month: {year}-{month:02d}")
                if selected_months[year]:
                    require(month > selected_months[year][-1], f"non-monotonic selected month order in {year}: {month}")
                selected_months[year].append(month)
                selected_members.append(name)
                extracted = tf.extractfile(member)
                require(extracted is not None, f"could not stream selected member {name}")
                local = tmp / f"{year}-{month:02d}-kep_collect.h5"
                h = hashlib.sha256()
                written = 0
                with local.open("wb") as out:
                    while True:
                        chunk = extracted.read(1024 * 1024)
                        if not chunk:
                            break
                        out.write(chunk)
                        h.update(chunk)
                        written += len(chunk)
                require(written == int(member.size), f"selected member size mismatch for {name}: {written} != {member.size}")
                audit = parse_month_hdf5(local, year, name, heaps_by_year[year])
                require(audit["member_sha256"] == h.hexdigest(), f"stream/file SHA mismatch for {name}")
                audit["member_size"] = int(member.size)
                member_audits.append(audit)
                local.unlink()
                print(
                    f"MAARSY {year}-{month:02d}: rows={audit['rows']} blind={audit['blind_removed_before_radiant_speed_read']} "
                    f"eligible={audit['eligible_geometry_before_density_cap']}",
                    flush=True,
                )

    require(stopped_at_2018_header is not None, "archive stream never reached first 2018 member")
    for year in YEARS:
        require(selected_months[year], f"no selected MAARSY kep_collect.h5 members for {year}")

    scan_by_year: dict[int, list[dict[str, Any]]] = {}
    selected_by_bin: dict[str, dict[str, int]] = {}
    for year in YEARS:
        events: list[dict[str, Any]] = []
        per_bin: dict[str, int] = {}
        for bin_index in range(36):
            chosen = [item[2] for item in heaps_by_year[year][bin_index]]
            chosen.sort(key=lambda e: str(e["id"]))
            events.extend(chosen)
            per_bin[str(bin_index)] = len(chosen)
        events.sort(key=lambda e: str(e["id"]))
        scan_by_year[year] = events
        selected_by_bin[str(year)] = per_bin

    audit = {
        "years": list(YEARS),
        "selected_months": {str(y): selected_months[y] for y in YEARS},
        "selected_members": selected_members,
        "member_audits": member_audits,
        "ignored_member_headers_before_2018": ignored_member_headers,
        "stopped_at_first_2018_member_header": stopped_at_2018_header,
        "density_cap_per_10deg_bin": MAX_EVENTS_PER_BIN,
        "density_selection": "10,000 smallest SHA256(MAARSY|year|archive_member|row_index_0based) per fixed 10-degree bin",
        "selected_by_bin_after_cap": selected_by_bin,
        "selected_events": {str(y): len(scan_by_year[y]) for y in YEARS},
        "solar_longitude_read_before_blind_only_field": True,
        "radiant_speed_read_only_for_nonblind_rows": True,
        "target_interval_radiant_speed_read": False,
        "orbital_dataset_opened": False,
        "labels_used": False,
        "target_information_access": False,
    }
    return scan_by_year, audit


def apply_pooled_year_centroids(
    families: list[dict[str, Any]],
    components: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
    support: Any,
    base: Any,
) -> dict[str, Any]:
    component_by_id = {str(c["component_id"]): c for c in components}
    require(len(component_by_id) == len(components), "component IDs not unique")
    event_lookup = {year: {str(e["id"]): e for e in scan_by_year[year]} for year in YEARS}
    duplicate_families = 0
    duplicate_family_years = 0
    single_distances: list[float] = []
    duplicate_distances: list[float] = []
    for family in families:
        pooled: dict[str, dict[str, float]] = {}
        has_duplicate = False
        for year in YEARS:
            year_components = [
                component_by_id[str(cid)] for cid in family["component_ids"]
                if int(component_by_id[str(cid)]["year"]) == year
            ]
            require(year_components, f"family {family['family_id']} missing year {year}")
            if len(year_components) > 1:
                has_duplicate = True
                duplicate_family_years += 1
            ids = sorted(set().union(*(set(str(x) for x in c["event_ids"]) for c in year_components)))
            require(ids and all(eid in event_lookup[year] for eid in ids), "pooled family-year event lookup failed")
            center = v8.pooled_centroid([event_lookup[year][eid] for eid in ids], support)
            pooled[str(year)] = center
            if len(year_components) == 1:
                single_distances.append(float(support.centroid_distance(center, year_components[0]["centroid"], base)))
            else:
                duplicate_distances.append(float(support.centroid_distance(center, family["centroids"][str(year)], base)))
        if has_duplicate:
            duplicate_families += 1
        family["centroids"] = pooled
    max_single = max(single_distances) if single_distances else 0.0
    require(max_single <= 1e-12, f"v8 pooled centroid lost single-component equivalence: {max_single}")
    return {
        "families_with_duplicate_same_year_components": duplicate_families,
        "duplicate_family_years": duplicate_family_years,
        "single_component_family_years": len(single_distances),
        "max_single_component_centroid_distance": float(max_single),
        "duplicate_year_old_to_pooled_distance_median": float(np.median(duplicate_distances)) if duplicate_distances else None,
        "duplicate_year_old_to_pooled_distance_max": float(max(duplicate_distances)) if duplicate_distances else None,
        "pooling_statistic": {"sol": "circular_mean_deg", "sun_lon": "circular_mean_deg", "ecl_lat": "median", "vg": "median"},
        "family_membership_changed": False,
    }


def canonical_sha256(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    tmp = args.output / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)

    source_audit = json.loads(args.source_audit_json.read_text())
    v8_result = json.loads(args.v8_result_json.read_text())
    require(source_audit["verdict"] == "PASS_WAVELET_CATALOGUE_V3_SOURCE_AUDIT", "frozen source audit failed")
    require(source_audit["development_source_sha256"] == "ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51", "runtime source changed")
    require(source_audit["support_source_sha256"] == "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62", "support source changed")
    require(source_audit["target_information_present"] is False, "target information entered source audit")
    require(source_audit["labels_enter_candidate_generation"] is False, "candidate-generation label boundary changed")
    require(v8_result["verdict"] == "PASS_POOLED_YEAR_CENTROID_V8_DEVELOPMENT", "promoted v8 development no longer passed")
    require(v8_result["family_count"] == 226, "promoted v8 development family universe changed")
    require(v8_result["configuration"]["family_link_radius"] == 1.5, "v8 family radius changed")
    require(v8_result["configuration"]["episode_size"] == 128, "v8 episode size changed")
    require(v8_result["configuration"]["multiplicity"] == "(multi-anchor-v3-energy / Brown-peak)^2", "v8 multiplicity changed")

    require(all(mult.v3.self_test().values()), "multi-anchor v3 self-test failed")
    require(all(mult.brown.self_test().values()), "Brown self-test failed")
    runtime = mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = tuple()
    support.CORPUS = "orbittrace-v8-maarsy-2016-2017-external-geometry-power"
    support.RANKING_VARIANTS = ("persistence", "mean_year_strength", "sqrt_support_strength", "min_year_strength", "size_penalized_strength")
    require(float(support.BLIND_LOW) == BLIND_LOW and float(support.BLIND_HIGH) == BLIND_HIGH, "blind interval changed")
    require(int(support.MIN_FAMILY_YEARS) == 2, "family-year minimum changed")
    require(abs(float(support.FAMILY_LINK_RADIUS) - 1.5) < 1e-15, "family radius changed")
    require(int(support.MIN_COMPONENT_EVENTS) == 4 and int(support.MIN_COMPONENT_QUARTETS) == 2, "component gates changed")
    require(int(support.SHORTLIST_K) == 64 and int(support.AUDIT_SHORTLIST_K) == 128, "shortlists changed")
    require(int(support.MIN_ANCHOR_COUNT) == 2 and int(support.MAX_QUARTETS_PER_BIN) == 512, "proposal gates changed")
    for name in ("feature_matrix", "exact_anchor_distances", "quartet_score", "component_records", "build_families", "centroid_distance", "circular_mean_deg"):
        require(hasattr(support, name), f"frozen support missing {name}")

    setattr(args, "fixed4_baseline_json", args.source_audit_json)
    _candidate, base, _scorer = support.load_sources(args)
    require(abs(float(getattr(_candidate, "CANDIDATE_SCALE", 4.0)) - 4.0) < 1e-15, "fixed4 candidate scale changed")

    zenodo = verify_zenodo_metadata()

    # FIRST MAARSY SCIENTIFIC-VALUE ACCESS occurs inside stream_selected_panel().
    scan_by_year, transport = stream_selected_panel(tmp)
    require(sorted(scan_by_year) == list(YEARS), "MAARSY year universe changed")
    require(transport["target_interval_radiant_speed_read"] is False, "target-interval radiant/speed was read")
    require(transport["orbital_dataset_opened"] is False, "orbital dataset opened before ranking")

    components: list[dict[str, Any]] = []
    scan_audits: list[dict[str, Any]] = []
    passing_counts: dict[str, int] = {}
    for year in YEARS:
        audit, passing, year_components = v6.label_free_scan_year(year, scan_by_year[year], support, base)
        scan_audits.append(audit)
        passing_counts[str(year)] = len(passing)
        components.extend(year_components)
        print(f"MAARSY v8 {year}: quartets={len(passing)} components={len(year_components)}", flush=True)

    families, support_rankings = support.build_families(components, base)
    require(len({str(f["family_id"]) for f in families}) == len(families), "family IDs not unique")
    require(all(sorted(int(y) for y in f["years"]) == list(YEARS) for f in families), "family outside exact 2016/2017 recurrence pair")
    persistence_order = [str(x) for x in support_rankings["persistence"]]
    require(set(persistence_order) == {str(f["family_id"]) for f in families}, "persistence family universe mismatch")
    repair = apply_pooled_year_centroids(families, components, scan_by_year, support, base)

    # Freeze full geometry-only rankings before any orbit field can be accessed later.
    mult.YEARS = YEARS
    mult.MONTH_KEYS = tuple()
    mult.TOP_K = TOP_K
    scored, scoring_summary = mult.score_families(families, scan_by_year, runtime, base)
    require(len(scored) == len(families), "not every MAARSY family scored")
    rankings = {
        "multiplicity": mult.rank_scored(scored, "multiplicity"),
        "brown": mult.rank_scored(scored, "brown"),
        "v3": mult.rank_scored(scored, "v3"),
        "label_free_persistence": persistence_order,
    }
    for name, order in rankings.items():
        require(len(order) == len(families) and set(order) == {str(f["family_id"]) for f in families}, f"incomplete {name} ranking")

    scannable = all(int(a["scannable_bin_count"]) >= MIN_SCANNABLE_BINS for a in scan_audits)
    episode_exact = bool(families) and scoring_summary["episode_sizes"] == [128]
    brown_equiv = float(scoring_summary["max_brown_equivalence_difference"]) <= BROWN_EQ_TOL
    n_families = len(families)

    interface_integrity = {
        "exact_fixed_years_2016_2017": sorted(scan_by_year) == list(YEARS),
        "selected_members_each_year_nonempty": all(bool(transport["selected_months"][str(y)]) for y in YEARS),
        "stopped_before_2018_payload": str(transport["stopped_at_first_2018_member_header"]).startswith(NEXT_YEAR_PREFIX),
        "blind_before_radiant_speed": transport["radiant_speed_read_only_for_nonblind_rows"] is True and transport["target_interval_radiant_speed_read"] is False,
        "no_orbit_access": transport["orbital_dataset_opened"] is False,
        "no_labels": transport["labels_used"] is False,
        "no_target_information": transport["target_information_access"] is False,
        "at_least_24_scannable_bins_each_year": scannable,
        "all_families_exactly_two_year_recurrent": all(sorted(int(y) for y in f["years"]) == list(YEARS) for f in families),
        "all_local_episode_sizes_exact_128": episode_exact,
        "brown_equivalence_within_1e_10": brown_equiv,
        "v8_pooling_did_not_change_family_membership": repair["family_membership_changed"] is False,
        "complete_geometry_only_rankings_frozen_before_orbit": all(len(order) == n_families for order in rankings.values()),
    }

    if not all(interface_integrity.values()):
        verdict = "FAIL_MAARSY_GEOMETRY_INTERFACE_OR_INTEGRITY"
    elif n_families < MIN_FAMILIES:
        verdict = "INCONCLUSIVE_V8_MAARSY_EXTERNAL_POWER_N"
    else:
        verdict = "PASS_V8_MAARSY_EXTERNAL_N_POWER_GATE"

    ranked_payload = {
        "schema": "orbittrace-v8-maarsy-2016-2017-geometry-ranking-v1",
        "years": list(YEARS),
        "family_count": n_families,
        "rankings": rankings,
        "families": families,
        "scored": scored,
        "orbit_access": False,
        "target_information_access": False,
    }
    ranking_sha = canonical_sha256(ranked_payload)
    ranked_path = args.output / "maarsy_v8_geometry_rankings.json"
    ranked_path.write_text(json.dumps(ranked_payload, indent=2, sort_keys=True) + "\n")

    result = {
        "schema": "orbittrace-v8-maarsy-2016-2017-geometry-power-v1",
        "verdict": verdict,
        "configuration": {
            "years": list(YEARS),
            "blind_exclusion": [BLIND_LOW, BLIND_HIGH],
            "field_mapping": {
                "sol": "HDF5 sun_lon degrees",
                "sun_lon": "wrap180(HDF5 slon), where slon is source-frozen radiant ecliptic longitude minus Sun longitude",
                "ecl_lat": "HDF5 slat degrees",
                "vg": "HDF5 vels km/s",
            },
            "density_cap_per_10deg_bin": MAX_EVENTS_PER_BIN,
            "family_builder": "exact v6 connected recurrent family graph",
            "family_link_radius": 1.5,
            "centroid_statistic": {"sol": "circular_mean_deg", "sun_lon": "circular_mean_deg", "ecl_lat": "median", "vg": "median"},
            "episode_size": 128,
            "multiplicity": "(multi-anchor-v3-energy / Brown-peak)^2",
            "primary_ranking": "multiplicity",
            "minimum_scannable_bins_each_year": MIN_SCANNABLE_BINS,
            "minimum_recurrent_families_N": MIN_FAMILIES,
            "orbital_power_floor_Q_deferred": 30,
            "no_orbits_in_this_stage": True,
            "no_labels": True,
            "no_target_information": True,
        },
        "zenodo_metadata": zenodo,
        "transport_and_parser_audit": transport,
        "scan_audits": scan_audits,
        "passing_quartets": passing_counts,
        "component_count": len(components),
        "family_count": n_families,
        "pooled_centroid_audit": repair,
        "scoring_summary": scoring_summary,
        "ranking_sha256_before_any_orbit_access": ranking_sha,
        "ranking_file": ranked_path.name,
        "integrity_gates": interface_integrity,
        "N_power_gate_passed": n_families >= MIN_FAMILIES and all(interface_integrity.values()),
        "Q_power_gate_evaluated": False,
        "external_scientific_pass_fail_evaluated": False,
        "orbit_access": False,
        "target_information_access": False,
        "v8_method_changed": False,
        "external_power_floors_lowered": False,
        "final_gmn_stage_a_authorized": False,
        "claim_boundary": (
            "Fixed 2016/2017 MAARSY geometry-only external stage. Solar longitude is read first and 20-55 degrees is removed before radiant/speed values are read. "
            "The complete v8 family universe and geometry-only rankings are frozen with no orbital, label, or OrbitTrace-target access. This stage can only decide the N>=100 external power gate; it cannot by itself establish an external v8 pass or authorize final GMN Stage A."
        ),
    }
    result_path = args.output / "v8_maarsy_2016_2017_geometry_power.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (args.output / "V8_MAARSY_2016_2017_GEOMETRY_POWER.md").write_text(
        "# OrbitTrace v8 MAARSY 2016/2017 geometry-power stage\n\n"
        f"**Verdict:** `{verdict}`\n\n"
        f"Recurrent families: **N={n_families}** (frozen power floor: N>=100).\n\n"
        "No orbit field, shower label, OrbitTrace target information, or final-GMN target-containing data was accessed. "
        f"The complete geometry-only ranking payload was frozen at SHA-256 `{ranking_sha}` before any orbital stage.\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
