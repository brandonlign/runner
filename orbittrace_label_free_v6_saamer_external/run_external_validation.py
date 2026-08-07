#!/usr/bin/env python3
"""One-shot SAAMER 2020-2021 external validation of frozen label-free v6."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import heapq
import importlib.util
import json
import math
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any

import numpy as np
import requests
from scipy.stats import hypergeom

from orbittrace_label_free_sparse_support_v6 import run_development as v6
from orbittrace_sparse_support_multiplicity_v5 import run_holdout as mult

YEARS = (2020, 2021)
URLS = {
    2020: "https://ceres.ta3.sk/iaumdcdb/dataDBs/radio_offline/iaumdcSAAMER2020.zip",
    2021: "https://ceres.ta3.sk/iaumdcdb/dataDBs/radio_offline/iaumdcSAAMER2021.zip",
}
EXPECTED_ARCHIVE_SHA256 = {
    2020: "208938b6ed6c504d77eb96ae1d9a867f5957fcba48076fd1bac9632c24ff4933",
    2021: "41a1aa7d568c98f273087fd2648cf6e9aa365373bf25b3db36d54ea987dd727c",
}
EXPECTED_LEGEND_SHA256 = "afb3f9f7a3b753234db8dbb7219d14095510265293485fc1e744f659a857f48b"
EXPECTED_V6_ARTIFACT_DIGEST = "sha256:3c636b05cbfc88c6d6b2b8289b309412174b0025c305ae2f2532678927b2232b"
EXPECTED_FRESHNESS_ARTIFACT_DIGEST = "sha256:a990b5c2939d6ab9b652c4c2a97a0607b5b1417aa66d1f929c5e2f0d5e15e178"
EXPECTED_DSH_BLOB = "ab17e1205d72d8ab8361d8ba6cdad2e4c31fdcb2"
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
MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--v6-result-json", required=True, type=Path)
    p.add_argument("--freshness-json", required=True, type=Path)
    p.add_argument("--dsh-comparator", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_member(name: str) -> bool:
    p = PurePosixPath(name)
    return not p.is_absolute() and ".." not in p.parts and not name.startswith(("/", "\\"))


def month_member(year: int, month: int) -> str:
    return f"SAA{MONTHS[month - 1]}{year}.dat"


def stable_identity_hash(year: int, member: str, physical_row: int) -> int:
    payload = f"SAAMER|{year}|{member}|{physical_row}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest(), "big", signed=False)


def parse_float_token(token: bytes) -> float | None:
    try:
        value = float(token)
    except Exception:
        return None
    return value if math.isfinite(value) else None


def download_archive(year: int, root: Path) -> Path:
    path = root / f"iaumdcSAAMER{year}.zip"
    with requests.get(
        URLS[year], timeout=300, stream=True, headers={"User-Agent": "OrbitTrace-label-free-v6-external/1.0"}
    ) as response:
        response.raise_for_status()
        with path.open("wb") as fh:
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    fh.write(chunk)
    digest = sha256_file(path)
    require(digest == EXPECTED_ARCHIVE_SHA256[year], f"{year} archive SHA changed: {digest}")
    return path


def verify_archive_structure(year: int, path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as zf:
        require(zf.testzip() is None, f"{year} ZIP CRC failure")
        names = zf.namelist()
        require(all(safe_member(name) for name in names), f"{year} unsafe ZIP member")
        legends = [name for name in names if PurePosixPath(name).name.lower() == "legend.inf"]
        require(len(legends) == 1, f"{year} legend count changed")
        legend = zf.read(legends[0])
        require(hashlib.sha256(legend).hexdigest() == EXPECTED_LEGEND_SHA256, f"{year} legend SHA changed")
        expected = {month_member(year, month) for month in range(1, 13)}
        basename_to_member = {PurePosixPath(name).name: name for name in names if not name.endswith("/")}
        require(expected.issubset(basename_to_member), f"{year} expected monthly member missing")
        return {
            "year": year,
            "archive_sha256": EXPECTED_ARCHIVE_SHA256[year],
            "archive_bytes": path.stat().st_size,
            "legend_sha256": EXPECTED_LEGEND_SHA256,
            "monthly_members": [basename_to_member[month_member(year, month)] for month in range(1, 13)],
        }


def _heap_push_smallest(heap: list[tuple[int, str, dict[str, Any]]], hash_value: int, event: dict[str, Any]) -> None:
    # Negative hash makes heap[0] the largest retained original hash.
    item = (-hash_value, str(event["id"]), event)
    if len(heap) < MAX_EVENTS_PER_BIN:
        heapq.heappush(heap, item)
        return
    largest_retained = -heap[0][0]
    if hash_value < largest_retained:
        heapq.heapreplace(heap, item)


def parse_geometry_and_sample(year: int, archive_path: Path, structure: dict[str, Any], base: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    heaps: dict[int, list[tuple[int, str, dict[str, Any]]]] = {idx: [] for idx in range(36)}
    counts_by_bin = Counter()
    raw_rows = 0
    blind_removed = 0
    invalid_geometry = 0
    wrong_year_or_month = 0
    eligible_geometry = 0

    with zipfile.ZipFile(archive_path) as zf:
        for month, member in enumerate(structure["monthly_members"], start=1):
            with zf.open(member, "r") as fh:
                for physical_row, raw in enumerate(fh, start=1):
                    raw = raw.strip()
                    if not raw:
                        continue
                    raw_rows += 1
                    tokens = raw.split()
                    require(len(tokens) == 16, f"{year}:{member}:{physical_row} token width changed")

                    # Critical blindness boundary: LS is the first scientific field interpreted.
                    sol = parse_float_token(tokens[4])
                    if sol is None or not (0.0 <= sol < 360.0):
                        invalid_geometry += 1
                        continue
                    if BLIND_LOW <= sol <= BLIND_HIGH:
                        blind_removed += 1
                        continue

                    # Nominal-year/month identity is checked only after the target interval is removed.
                    row_year = parse_float_token(tokens[1])
                    row_month = parse_float_token(tokens[2])
                    if row_year is None or row_month is None or int(row_year) != year or int(row_month) != month:
                        wrong_year_or_month += 1
                        continue

                    ra = parse_float_token(tokens[6])
                    dec = parse_float_token(tokens[7])
                    vg = parse_float_token(tokens[8])
                    if not (
                        ra is not None and 0.0 <= ra < 360.0
                        and dec is not None and -90.0 <= dec <= 90.0
                        and vg is not None and 5.0 < vg < 75.0
                    ):
                        invalid_geometry += 1
                        continue

                    ecl_lon, ecl_lat = base.equatorial_to_ecliptic(ra, dec)
                    event_id = f"SAA|{year}|{PurePosixPath(member).name}|{physical_row}"
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
                    _heap_push_smallest(
                        heaps[bin_index], stable_identity_hash(year, PurePosixPath(member).name, physical_row), event
                    )

    selected_by_bin: dict[str, int] = {}
    events: list[dict[str, Any]] = []
    for bin_index in range(36):
        chosen = [item[2] for item in heaps[bin_index]]
        chosen.sort(key=lambda event: str(event["id"]))
        events.extend(chosen)
        selected_by_bin[str(bin_index)] = len(chosen)
    events.sort(key=lambda event: str(event["id"]))

    audit = {
        "year": year,
        "raw_nominal_month_rows": raw_rows,
        "blind_removed_before_radiant_speed": blind_removed,
        "invalid_geometry": invalid_geometry,
        "wrong_year_or_month": wrong_year_or_month,
        "eligible_geometry_before_density_cap": eligible_geometry,
        "eligible_by_bin_before_cap": {str(k): int(v) for k, v in sorted(counts_by_bin.items())},
        "selected_by_bin": selected_by_bin,
        "selected_events": len(events),
        "density_cap": MAX_EVENTS_PER_BIN,
        "density_selection": "10,000 smallest SHA256(identity) per fixed 10-degree bin",
        "orbital_elements_interpreted": False,
    }
    return events, audit


def load_dsh_module(path: Path) -> Any:
    require(path.is_file(), "frozen D_SH comparator source missing")
    spec = importlib.util.spec_from_file_location("frozen_orbittrace_literature_dsh", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    require(abs(float(module.RUD2014_DSH_THRESHOLD) - DSH_THRESHOLD) < 1e-15, "D_SH threshold changed")
    return module


def parse_event_id(event_id: str) -> tuple[int, str, int]:
    parts = event_id.split("|")
    require(len(parts) == 4 and parts[0] == "SAA", f"invalid SAAMER event id: {event_id}")
    return int(parts[1]), parts[2], int(parts[3])


def read_orbits_after_rank_freeze(
    archive_paths: dict[int, Path], needed_ids: set[str]
) -> tuple[dict[str, dict[str, float]], dict[str, Any]]:
    wanted_by_year_member: dict[tuple[int, str], dict[int, str]] = {}
    for event_id in needed_ids:
        year, member, row_number = parse_event_id(event_id)
        wanted_by_year_member.setdefault((year, member), {})[row_number] = event_id

    orbits: dict[str, dict[str, float]] = {}
    invalid = 0
    for (year, member), row_map in sorted(wanted_by_year_member.items()):
        with zipfile.ZipFile(archive_paths[year]) as zf:
            lookup = {PurePosixPath(name).name: name for name in zf.namelist() if not name.endswith("/")}
            require(member in lookup, f"missing orbital reread member {year}:{member}")
            with zf.open(lookup[member], "r") as fh:
                for physical_row, raw in enumerate(fh, start=1):
                    event_id = row_map.get(physical_row)
                    if event_id is None:
                        continue
                    tokens = raw.strip().split()
                    require(len(tokens) == 16, f"orbital reread width changed: {event_id}")
                    q = parse_float_token(tokens[10])
                    e = parse_float_token(tokens[11])
                    inc = parse_float_token(tokens[13])
                    peri = parse_float_token(tokens[14])
                    node = parse_float_token(tokens[15])
                    if not (
                        q is not None and q > 0.0
                        and e is not None and e >= 0.0
                        and inc is not None and 0.0 <= inc <= 180.0
                        and peri is not None
                        and node is not None
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


class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, value: int) -> int:
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def union(self, left: int, right: int) -> None:
        a, b = self.find(left), self.find(right)
        if a == b:
            return
        if self.size[a] < self.size[b]:
            a, b = b, a
        self.parent[b] = a
        self.size[a] += self.size[b]


def orbital_corroboration(
    families: list[dict[str, Any]], orbits: dict[str, dict[str, float]], dsh: Any
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    qualified = 0
    valid_fractions: list[float] = []

    for family in families:
        family_id = str(family["family_id"])
        event_ids = [str(value) for value in family["event_ids"]]
        valid_ids = [event_id for event_id in event_ids if event_id in orbits]
        valid_fraction = len(valid_ids) / len(event_ids) if event_ids else 0.0
        valid_fractions.append(valid_fraction)
        best_component: list[str] = []
        best_counts: dict[int, int] = {}

        if len(valid_ids) >= 2:
            q = [orbits[event_id]["q"] for event_id in valid_ids]
            e = [orbits[event_id]["e"] for event_id in valid_ids]
            inc = [orbits[event_id]["i"] for event_id in valid_ids]
            peri = [orbits[event_id]["arg"] for event_id in valid_ids]
            node = [orbits[event_id]["node"] for event_id in valid_ids]
            matrix = dsh.pairwise_dsh(q, e, inc, peri, node)
            forest = UnionFind(len(valid_ids))
            ii, jj = np.where(np.triu(matrix < DSH_THRESHOLD, k=1))
            for left, right in zip(ii.tolist(), jj.tolist()):
                forest.union(int(left), int(right))
            groups: dict[int, list[str]] = {}
            for index, event_id in enumerate(valid_ids):
                groups.setdefault(forest.find(index), []).append(event_id)
            candidates: list[tuple[float, int, list[str], dict[int, int]]] = []
            for component in groups.values():
                year_counts = Counter(parse_event_id(event_id)[0] for event_id in component)
                if all(year_counts.get(year, 0) >= MIN_YEAR_ORBIT_MEMBERS for year in YEARS):
                    precision = len(component) / len(event_ids) if event_ids else 0.0
                    candidates.append((precision, len(component), component, dict(year_counts)))
            if candidates:
                _precision, _size, best_component, best_counts = max(
                    candidates, key=lambda item: (item[0], item[1], sorted(item[2]))
                )

        precision = len(best_component) / len(event_ids) if event_ids else 0.0
        is_qualified = bool(
            best_component
            and precision >= MIN_ORBITAL_PRECISION
            and all(best_counts.get(year, 0) >= MIN_YEAR_ORBIT_MEMBERS for year in YEARS)
        )
        qualified += int(is_qualified)
        rows[family_id] = {
            "family_id": family_id,
            "family_event_count": len(event_ids),
            "valid_orbit_count": len(valid_ids),
            "valid_orbit_fraction": valid_fraction,
            "largest_cross_year_dsh_component": len(best_component),
            "component_year_counts": {str(year): int(best_counts.get(year, 0)) for year in YEARS},
            "orbital_corroboration_precision": precision,
            "orbitally_corroborated": is_qualified,
            "dsh_threshold": DSH_THRESHOLD,
        }

    return rows, {
        "family_count": len(families),
        "orbitally_corroborated_families": qualified,
        "median_valid_orbit_fraction": float(np.median(valid_fractions)) if valid_fractions else None,
        "minimum_valid_orbit_fraction": float(np.min(valid_fractions)) if valid_fractions else None,
    }


def evaluate_ranking(order: list[str], corroboration: dict[str, dict[str, Any]]) -> dict[str, Any]:
    universe = set(corroboration)
    require(set(order) == universe and len(order) == len(universe), "ranking/corroboration universe mismatch")
    n = len(order)
    k = min(TOP_K, n)
    qualified_ids = {fid for fid, row in corroboration.items() if row["orbitally_corroborated"]}
    q = len(qualified_ids)
    top = order[:k]
    x = sum(fid in qualified_ids for fid in top)
    ranks = [rank for rank, fid in enumerate(order, start=1) if fid in qualified_ids]
    enrichment_p = float(hypergeom.sf(x - 1, n, q, k)) if q and k else 1.0
    return {
        "family_universe": n,
        "orbitally_corroborated_universe": q,
        "top_k": k,
        "top_k_orbitally_corroborated": x,
        "top_k_corroboration_fraction": float(x / k) if k else 0.0,
        "hypergeometric_enrichment_p": enrichment_p,
        "median_rank": float(np.median(ranks)) if ranks else None,
        "mrr": float(np.mean([1.0 / rank for rank in ranks])) if ranks else 0.0,
    }


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    # All prerequisites are checked before the first SAAMER scientific-value access.
    v6_result = json.loads(args.v6_result_json.read_text())
    require(v6_result["verdict"] == "PASS_LABEL_FREE_SPARSE_SUPPORT_V6_DEVELOPMENT", "v6 did not pass")
    require(v6_result["configuration"]["no_source_labels_in_proposal_generation"] is True, "v6 label-free guard changed")
    require(v6_result["configuration"]["max_quartets_per_bin"] == 512, "v6 quartet cap changed")
    require(v6_result["configuration"]["min_anchor_count"] == 2, "v6 anchor gate changed")
    require(v6_result["configuration"]["first_shortlist"] == 64 and v6_result["configuration"]["audit_shortlist"] == 128, "v6 shortlist changed")

    freshness = json.loads(args.freshness_json.read_text())
    require(freshness["verdict"] == "PASS_SAAMER_2020_2021_REPO_SCIENTIFIC_FRESHNESS_AUDIT", "SAAMER freshness did not pass")
    require(freshness["potential_exposure_hit_count"] == 0, "SAAMER exposure hit appeared")

    require(all(mult.v3.self_test().values()), "multi-anchor v3 self-test failed")
    require(all(mult.brown.self_test().values()), "Brown self-test failed")
    runtime = mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = tuple()
    support.CORPUS = "orbittrace-label-free-v6-saamer-2020-2021-external"
    support.RANKING_VARIANTS = (
        "persistence", "mean_year_strength", "sqrt_support_strength", "min_year_strength", "size_penalized_strength"
    )
    require(float(support.BLIND_LOW) == BLIND_LOW and float(support.BLIND_HIGH) == BLIND_HIGH, "blind interval changed")
    require(int(support.MIN_FAMILY_YEARS) == 2, "family-year minimum changed")
    require(abs(float(support.FAMILY_LINK_RADIUS) - 1.5) < 1e-15, "family link radius changed")
    require(int(support.MIN_COMPONENT_EVENTS) == 4 and int(support.MIN_COMPONENT_QUARTETS) == 2, "component gates changed")
    require(int(support.SHORTLIST_K) == 64 and int(support.AUDIT_SHORTLIST_K) == 128, "shortlists changed")
    require(int(support.MIN_ANCHOR_COUNT) == 2 and int(support.MAX_QUARTETS_PER_BIN) == 512, "proposal gates changed")

    setattr(args, "fixed4_baseline_json", args.v6_result_json)
    _candidate, base, _scorer = support.load_sources(args)
    require(abs(float(getattr(_candidate, "CANDIDATE_SCALE", 4.0)) - 4.0) < 1e-15, "candidate scale changed")
    dsh = load_dsh_module(args.dsh_comparator)

    archive_root = args.output / "_raw_saamer"
    archive_root.mkdir(exist_ok=True)
    archive_paths: dict[int, Path] = {}
    structure: dict[int, dict[str, Any]] = {}
    geometry_audits: list[dict[str, Any]] = []
    scan_by_year: dict[int, list[dict[str, Any]]] = {}

    try:
        # FIRST SAAMER SCIENTIFIC-VALUE ACCESS occurs in parse_geometry_and_sample below,
        # after protocol/source/prerequisite/ranking rules and orbital validation are fixed.
        for year in YEARS:
            archive_paths[year] = download_archive(year, archive_root)
            structure[year] = verify_archive_structure(year, archive_paths[year])
            events, audit = parse_geometry_and_sample(year, archive_paths[year], structure[year], base)
            scan_by_year[year] = events
            geometry_audits.append(audit)
            print(
                f"SAAMER {year}: eligible={audit['eligible_geometry_before_density_cap']} selected={audit['selected_events']}",
                flush=True,
            )

        components: list[dict[str, Any]] = []
        scan_audits: list[dict[str, Any]] = []
        retained_counts: dict[str, int] = {}
        for year in YEARS:
            audit, passing, year_components = v6.label_free_scan_year(year, scan_by_year[year], support, base)
            scan_audits.append(audit)
            retained_counts[str(year)] = len(passing)
            components.extend(year_components)
            print(f"SAAMER v6 {year}: quartets={len(passing)} components={len(year_components)}", flush=True)

        families, support_rankings = support.build_families(components, base)
        persistence_order = [str(value) for value in support_rankings["persistence"]]
        family_ids = [str(family["family_id"]) for family in families]
        require(set(persistence_order) == set(family_ids) and len(persistence_order) == len(family_ids), "persistence universe mismatch")

        mult.YEARS = YEARS
        mult.TOP_K = TOP_K
        scored, scoring_summary = mult.score_families(families, scan_by_year, runtime, base)
        require(len(scored) == len(families), "not every SAAMER recurrent family received a score")
        rankings = {
            "multiplicity": mult.rank_scored(scored, "multiplicity"),
            "brown": mult.rank_scored(scored, "brown"),
            "v3": mult.rank_scored(scored, "v3"),
            "label_free_persistence": persistence_order,
        }
        require(all(set(order) == set(family_ids) for order in rankings.values()), "ranking universe changed")
        rankings_frozen_before_orbit_access = True

        # FIRST ORBITAL-ELEMENT INTERPRETATION: every discovery family and ranking already exists.
        needed_ids = {str(event_id) for family in families for event_id in family["event_ids"]}
        orbits, orbit_read_audit = read_orbits_after_rank_freeze(archive_paths, needed_ids)
        corroboration, orbital_summary = orbital_corroboration(families, orbits, dsh)
        metrics = {name: evaluate_ranking(order, corroboration) for name, order in rankings.items()}

        n = len(families)
        q = int(orbital_summary["orbitally_corroborated_families"])
        scannable = all(int(a["scannable_bin_count"]) >= MIN_SCANNABLE_BINS for a in scan_audits)
        shortlist_exact = all(int(a["shortlist_audit_failures"]) == 0 for a in scan_audits)
        exact_years = all(sorted(int(y) for y in family["years"]) == list(YEARS) for family in families)
        exact_episode_sizes = scoring_summary["episode_sizes"] == [128] if families else False
        density_exact = all(
            all(int(value) <= MAX_EVENTS_PER_BIN for value in audit["selected_by_bin"].values())
            and audit["density_cap"] == MAX_EVENTS_PER_BIN
            for audit in geometry_audits
        )

        integrity_gates = {
            "frozen_v6_and_freshness_prerequisites": True,
            "exact_archive_and_legend_hashes": all(
                structure[year]["archive_sha256"] == EXPECTED_ARCHIVE_SHA256[year]
                and structure[year]["legend_sha256"] == EXPECTED_LEGEND_SHA256
                for year in YEARS
            ),
            "target_interval_removed_before_radiant_speed": all(a["blind_removed_before_radiant_speed"] >= 0 for a in geometry_audits),
            "rankings_frozen_before_orbital_interpretation": rankings_frozen_before_orbit_access and orbit_read_audit["orbital_elements_interpreted_only_after_rank_freeze"],
            "exact_10000_identity_hash_density_normalization": density_exact,
            "at_least_24_scannable_bins_each_year": scannable,
            "zero_shortlist_audit_mismatches": shortlist_exact,
            "all_recurrent_families_span_both_years": exact_years,
            "all_local_episode_sizes_exact_128": exact_episode_sizes,
            "brown_equivalence_within_1e_10": float(scoring_summary["max_brown_equivalence_difference"]) <= BROWN_EQ_TOL,
            "at_least_100_recurrent_families": n >= MIN_FAMILIES,
            "at_least_30_orbitally_corroborated_families": q >= MIN_ORBITALLY_CORROBORATED,
        }

        m = int(metrics["multiplicity"]["top_k_orbitally_corroborated"])
        b = int(metrics["brown"]["top_k_orbitally_corroborated"])
        p = int(metrics["label_free_persistence"]["top_k_orbitally_corroborated"])
        required_vs_persistence = int(math.ceil(0.90 * p))
        scientific_gates = {
            "multiplicity_topk_beats_brown_by_at_least_one": m >= b + 1,
            "multiplicity_topk_at_least_90pct_persistence": m >= required_vs_persistence,
            "multiplicity_topk_hypergeometric_enrichment_p_le_005": float(metrics["multiplicity"]["hypergeometric_enrichment_p"]) <= 0.05,
        }

        if not all(integrity_gates.values()):
            if not integrity_gates["at_least_100_recurrent_families"] or not integrity_gates["at_least_30_orbitally_corroborated_families"]:
                verdict = "INCONCLUSIVE_LABEL_FREE_V6_SAAMER_EXTERNAL_POWER"
            else:
                verdict = "FAIL_LABEL_FREE_V6_SAAMER_EXTERNAL_INTEGRITY"
        elif all(scientific_gates.values()):
            verdict = "PASS_LABEL_FREE_V6_SAAMER_EXTERNAL_VALIDATION"
        else:
            verdict = "FAIL_LABEL_FREE_V6_SAAMER_EXTERNAL_VALIDATION"

        result = {
            "verdict": verdict,
            "configuration": {
                "years": list(YEARS),
                "blind_exclusion": [BLIND_LOW, BLIND_HIGH],
                "max_events_per_10deg_bin": MAX_EVENTS_PER_BIN,
                "density_selection": "smallest SHA256 of SAAMER|year|member|physical_row_number",
                "candidate_architecture": "frozen label-free sparse-support v6",
                "primary_ranking": "worst-year multiplicity descending, geometric-mean multiplicity descending, family id",
                "multiplicity": "(multi-anchor-v3-energy / Brown-peak)^2",
                "orbital_validation": "largest cross-year D_SH<0.05 single-link component; >=4 events/year; >=0.50 family precision",
                "top_k": TOP_K,
                "no_source_labels": True,
                "no_orbits_in_candidate_or_ranking": True,
                "no_threshold_search": True,
                "no_density_search": True,
                "no_cap_search": True,
                "no_weight_search": True,
            },
            "archive_structure": [structure[year] for year in YEARS],
            "geometry_audits": geometry_audits,
            "fixed4_scan_audits": scan_audits,
            "retained_quartet_counts": retained_counts,
            "family_count": n,
            "family_scoring_summary": scoring_summary,
            "orbit_read_audit": orbit_read_audit,
            "orbital_summary": orbital_summary,
            "metrics": metrics,
            "required_multiplicity_vs_persistence": required_vs_persistence,
            "integrity_gates": integrity_gates,
            "scientific_gates": scientific_gates,
            "claim_boundary": (
                "One-shot external SAAMER 2020-2021 validation of the already-frozen label-free v6 architecture. "
                "The 20-55 degree target interval was excluded before radiant/speed use; orbital elements were first interpreted only after all discovery rankings were frozen. "
                "No OrbitTrace target information entered this run."
            ),
        }
        (args.output / "saamer_external_validation.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        (args.output / "saamer_external_rankings.json").write_text(json.dumps(rankings, indent=2) + "\n")
        (args.output / "saamer_external_orbital_corroboration.json.gz").write_bytes(
            gzip.compress(json.dumps(corroboration, separators=(",", ":")).encode("utf-8"))
        )
        (args.output / "saamer_external_families.json.gz").write_bytes(
            gzip.compress(json.dumps(families, separators=(",", ":")).encode("utf-8"))
        )
        (args.output / "saamer_external_family_scores.json.gz").write_bytes(
            gzip.compress(json.dumps(scored, separators=(",", ":")).encode("utf-8"))
        )

        lines = [
            "# OrbitTrace label-free v6 SAAMER 2020-2021 external validation",
            "",
            f"Verdict: **`{verdict}`**",
            "",
            f"- recurrent families: **{n}**",
            f"- orbitally corroborated families: **{q}**",
            f"- multiplicity top-{min(TOP_K,n)} corroborated: **{m}**; enrichment p: **{metrics['multiplicity']['hypergeometric_enrichment_p']:.6g}**",
            f"- label-free persistence top-{min(TOP_K,n)} corroborated: **{p}**",
            f"- Brown top-{min(TOP_K,n)} corroborated: **{b}**",
            f"- total-v3 top-{min(TOP_K,n)} corroborated: **{metrics['v3']['top_k_orbitally_corroborated']}**",
            f"- median valid-orbit fraction: **{orbital_summary['median_valid_orbit_fraction']:.4f}**",
            "",
            "No source shower labels were available or used. Orbital elements were validation-only after ranking freeze.",
        ]
        (args.output / "SAAMER_EXTERNAL_VALIDATION.md").write_text("\n".join(lines) + "\n")
        print("\n".join(lines), flush=True)
        return 0
    finally:
        if archive_root.exists():
            for path in archive_root.iterdir():
                path.unlink()
            archive_root.rmdir()


if __name__ == "__main__":
    raise SystemExit(main())
