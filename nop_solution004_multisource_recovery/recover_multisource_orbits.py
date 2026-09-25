from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

LOOKUP_SHA256 = "9ec720202966f1eda18c99c8decaa338d9be0bae913be4c2ff6ed34f2661282e"
MAX_DT_S = 2.5
MAX_DLS_DEG = 0.02
MAX_RADIANT_DEG = 0.20
MAX_DV_KM_S = 0.25
BIG = 1.0e9
USER_AGENT = "ghoststream-nop004-multisource-recovery/1.0"
SOLUTION004 = {"q": 0.207, "e": 0.932, "i": 16.7, "peri": 310.5, "node": 58.6}

EDMOND_YEARS = tuple(range(2011, 2017))
SONOTACO_YEARS = tuple(range(2011, 2021))
EDMOND_URLS = {
    year: f"https://ceres.ta3.sk/iaumdcdb/dataDBs/video_offline/iaumdcedmond{year}.csv.zip"
    for year in EDMOND_YEARS
}
SONOTACO_URLS = {
    year: f"https://ceres.ta3.sk/iaumdcdb/dataDBs/video_offline/iaumdcSNMv3_S{year % 100:02d}.csv.zip"
    for year in SONOTACO_YEARS
}
TARGET_SPECS = {
    "CAMS": set(range(2011, 2017)),
    "EDMOND": set(range(2011, 2017)),
    "SonotaCo": set(range(2011, 2021)),
    "GMN": {2019, 2020},
}
EXPECTED_TARGET_COUNTS = {"CAMS": 100, "EDMOND": 75, "SonotaCo": 60, "GMN": 35}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def as_float(value: str | None) -> float | None:
    text = (value or "").strip().replace("−", "-")
    if not text or text.lower() in {"nan", "none", "null", "na", "..."}:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def parse_lookup_time(text: str) -> datetime:
    return datetime.strptime(text.strip(), "%Y-%m-%d-%H:%M:%S").replace(tzinfo=timezone.utc)


def fractional_day_time(year: int, month: int, day_value: float) -> datetime:
    return datetime(year, month, 1, tzinfo=timezone.utc) + timedelta(days=day_value - 1.0)


def circular_delta(first: float, second: float) -> float:
    return (first - second + 180.0) % 360.0 - 180.0


def angular_separation(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    first_ra, first_dec, second_ra, second_dec = map(math.radians, (ra1, dec1, ra2, dec2))
    cosine = (
        math.sin(first_dec) * math.sin(second_dec)
        + math.cos(first_dec) * math.cos(second_dec) * math.cos(first_ra - second_ra)
    )
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def d_sh(first: dict[str, float], second: dict[str, float]) -> float:
    q1, e1 = first["q"], first["e"]
    q2, e2 = second["q"], second["e"]
    i1, w1, node1 = map(math.radians, (first["i"], first["peri"], first["node"]))
    i2, w2, node2 = map(math.radians, (second["i"], second["peri"], second["node"]))
    delta_node = math.atan2(math.sin(node1 - node2), math.cos(node1 - node2))
    cosine_i = math.cos(i1) * math.cos(i2) + math.sin(i1) * math.sin(i2) * math.cos(delta_node)
    mutual_i = math.acos(max(-1.0, min(1.0, cosine_i)))
    denominator = max(math.cos(mutual_i / 2.0), 1.0e-12)
    argument = math.cos((i1 + i2) / 2.0) * math.sin(delta_node / 2.0) / denominator
    peri_difference = w1 - w2 + 2.0 * math.asin(max(-1.0, min(1.0, argument)))
    return math.sqrt(
        (e1 - e2) ** 2
        + (q1 - q2) ** 2
        + (2.0 * math.sin(mutual_i / 2.0)) ** 2
        + (((e1 + e2) / 2.0) * 2.0 * math.sin(peri_difference / 2.0)) ** 2
    )


def fetch(url: str, path: Path) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    digest = hashlib.sha256()
    total = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(request, timeout=900) as response, path.open("wb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            total += len(chunk)
            output.write(chunk)
        return {
            "url": url,
            "path": str(path),
            "bytes": total,
            "sha256": digest.hexdigest(),
            "content_type": response.headers.get("Content-Type"),
            "last_modified": response.headers.get("Last-Modified"),
        }


def load_lookup(path: Path) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    if sha256(path) != LOOKUP_SHA256:
        raise RuntimeError("Exact NOP solution-004 lookup SHA-256 mismatch")
    all_target: list[dict[str, Any]] = []
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle, skipinitialspace=True):
            source = (raw.get("Sode") or "").strip()
            if source not in TARGET_SPECS:
                continue
            timestamp = parse_lookup_time(raw["Tobs"])
            if timestamp.year not in TARGET_SPECS[source]:
                continue
            row = {
                "lookup_number": int(raw["CurNum"]),
                "source": source,
                "time": timestamp,
                "time_text": raw["Tobs"].strip(),
                "year": timestamp.year,
                "month": timestamp.month,
                "sol": float(raw["LS"]),
                "ra": float(raw["RA"]),
                "dec": float(raw["DEC"]),
                "vg": float(raw["Vg"]),
            }
            all_target.append(row)
            by_source[source].append(row)
    return all_target, by_source


def documented_columns(headers: list[str]) -> dict[str, str]:
    options = {
        "year": ("Yr", "YEAR", "Year"),
        "month": ("Mn", "MONTH", "Month"),
        "day": ("Dayy", "Day", "DAY"),
        "sol": ("LS", "Sol", "SOL"),
        "ra": ("RA",),
        "dec": ("DECL", "DEC", "DE"),
        "vg": ("Vg", "VG"),
        "q": ("q",),
        "e": ("e",),
        "i": ("i",),
        "peri": ("arg", "peri"),
        "node": ("nod", "node"),
        "id": ("Ano", "ID", "Id", "IC"),
    }
    available = set(headers)
    mapping: dict[str, str] = {}
    for target, candidates in options.items():
        match = next((candidate for candidate in candidates if candidate in available), None)
        if match is None:
            raise RuntimeError(f"Archive is missing documented `{target}` column; headers={headers}")
        mapping[target] = match
    return mapping


def read_archive(path: Path, expected_year: int, allowed_months: set[int], source: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    schemas: list[dict[str, Any]] = []
    with zipfile.ZipFile(path) as bundle:
        members = [
            member
            for member in bundle.infolist()
            if not member.is_dir()
            and member.filename.lower().endswith((".csv", ".txt"))
            and "__MACOSX/" not in member.filename
            and not Path(member.filename).name.startswith("._")
        ]
        if not members:
            raise RuntimeError(f"No data CSV/TXT members in {path.name}")
        for member in members:
            with bundle.open(member) as raw_member:
                text = io.TextIOWrapper(raw_member, encoding="utf-8-sig", errors="replace", newline="")
                header_line = next(text, "")
                first_data_line = next(text, "")
            header_delimiter = max((";", ",", "\t", "|"), key=header_line.count)
            if header_line.count(header_delimiter) >= 4:
                headers = [
                    value.strip()
                    for value in next(csv.reader([header_line], delimiter=header_delimiter))
                ]
            else:
                headers = header_line.split()
            columns = documented_columns(headers)
            row_delimiter = max((";", ",", "\t", "|"), key=first_data_line.count)
            if first_data_line.count(row_delimiter) < 4:
                raise RuntimeError(f"Could not identify row delimiter in {member.filename}")
            schemas.append(
                {
                    "source": source,
                    "archive": path.name,
                    "member": member.filename,
                    "compressed_bytes": member.compress_size,
                    "uncompressed_bytes": member.file_size,
                    "headers": headers,
                    "columns": columns,
                    "header_delimiter": header_delimiter,
                    "row_delimiter": row_delimiter,
                }
            )
            with bundle.open(member) as raw_member:
                text = io.TextIOWrapper(raw_member, encoding="utf-8-sig", errors="replace", newline="")
                next(text, None)
                reader = csv.DictReader(
                    text,
                    fieldnames=headers,
                    delimiter=row_delimiter,
                    skipinitialspace=True,
                )
                for row in reader:
                    year_value = as_float(row.get(columns["year"]))
                    month_value = as_float(row.get(columns["month"]))
                    day_value = as_float(row.get(columns["day"]))
                    if year_value is None or month_value is None or day_value is None:
                        continue
                    year = int(round(year_value))
                    month = int(round(month_value))
                    if year != expected_year or month not in allowed_months:
                        continue
                    values = {
                        key: as_float(row.get(columns[key]))
                        for key in ("sol", "ra", "dec", "vg", "q", "e", "i", "peri", "node")
                    }
                    if any(values[key] is None for key in ("sol", "ra", "dec", "vg")):
                        continue
                    timestamp = fractional_day_time(year, month, day_value)
                    events.append(
                        {
                            "source": source,
                            "archive": path.name,
                            "member": member.filename,
                            "id": (row.get(columns["id"]) or "").strip(),
                            "time": timestamp,
                            "time_text": timestamp.isoformat(),
                            "sol": float(values["sol"]),
                            "ra": float(values["ra"]),
                            "dec": float(values["dec"]),
                            "vg": float(values["vg"]),
                            "orbit": {
                                "q": values["q"],
                                "e": values["e"],
                                "i": values["i"],
                                "peri": values["peri"],
                                "node": values["node"],
                            },
                        }
                    )
    return events, schemas


def edge_metrics(lookup: dict[str, Any], event: dict[str, Any]) -> dict[str, float] | None:
    dt = abs((event["time"] - lookup["time"]).total_seconds())
    dls = abs(circular_delta(event["sol"], lookup["sol"]))
    radiant = angular_separation(event["ra"], event["dec"], lookup["ra"], lookup["dec"])
    dv = abs(event["vg"] - lookup["vg"])
    if dt > MAX_DT_S or dls > MAX_DLS_DEG or radiant > MAX_RADIANT_DEG or dv > MAX_DV_KM_S:
        return None
    cost = (
        (dt / MAX_DT_S) ** 2
        + (dls / MAX_DLS_DEG) ** 2
        + (radiant / MAX_RADIANT_DEG) ** 2
        + (dv / MAX_DV_KM_S) ** 2
    )
    return {"dt_s": dt, "dls_deg": dls, "radiant_deg": radiant, "dv_km_s": dv, "cost": cost}


def assign(lookup: list[dict[str, Any]], events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_date: dict[Any, list[int]] = defaultdict(list)
    for index, event in enumerate(events):
        event["global_index"] = index
        by_date[event["time"].date()].append(index)
    edges: dict[tuple[int, int], dict[str, float]] = {}
    candidate_indices: set[int] = set()
    for left, row in enumerate(lookup):
        for event_index in by_date.get(row["time"].date(), []):
            event = events[event_index]
            metrics = edge_metrics(row, event)
            if metrics is None:
                continue
            edges[(left, event_index)] = metrics
            candidate_indices.add(event_index)
    ordered = sorted(candidate_indices)
    position = {event_index: column for column, event_index in enumerate(ordered)}
    width = max(len(lookup), len(ordered))
    cost = np.full((len(lookup), width), BIG, dtype=float)
    for (left, event_index), metrics in edges.items():
        cost[left, position[event_index]] = metrics["cost"]
    rows, columns = linear_sum_assignment(cost)
    assignments: list[dict[str, Any]] = []
    for left, column in zip(rows.tolist(), columns.tolist()):
        if column >= len(ordered) or cost[left, column] >= BIG / 2.0:
            continue
        event_index = ordered[column]
        event = events[event_index]
        assignments.append(
            {
                "lookup_number": lookup[left]["lookup_number"],
                "lookup_time": lookup[left]["time_text"],
                "year": lookup[left]["year"],
                "source": event["source"],
                "archive": event["archive"],
                "archive_member": event["member"],
                "archive_id": event["id"],
                "archive_time": event["time_text"],
                "residuals": edges[(left, event_index)],
                "orbit": event["orbit"],
            }
        )
    return assignments


def load_locked_matches(path: Path, source: str, expected_rows: int) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            orbit = {key: as_float(row.get(key)) for key in ("q", "e", "i", "peri", "node")}
            if any(value is None for value in orbit.values()):
                raise RuntimeError(f"Locked {source} match has incomplete orbit: {row}")
            lookup_time = row["lookup_time"].strip()
            matches.append(
                {
                    "lookup_number": int(row["lookup_number"]),
                    "lookup_time": lookup_time,
                    "year": int(lookup_time[:4]),
                    "source": source,
                    "archive": row.get("archive") or "locked-prior-artifact",
                    "archive_member": row.get("archive_member") or row.get("gmn_id") or "",
                    "archive_id": row.get("archive_id") or row.get("gmn_id") or "",
                    "archive_time": row.get("archive_time") or row.get("gmn_time") or "",
                    "residuals": {
                        "dt_s": float(row["dt_s"]),
                        "dls_deg": float(row["dls_deg"]),
                        "radiant_deg": float(row["radiant_deg"]),
                        "dv_km_s": float(row["dv_km_s"]),
                    },
                    "orbit": {key: float(orbit[key]) for key in orbit},
                }
            )
    if len(matches) != expected_rows:
        raise RuntimeError(f"Locked {source} match count mismatch: expected {expected_rows}, got {len(matches)}")
    if len({row["lookup_number"] for row in matches}) != len(matches):
        raise RuntimeError(f"Locked {source} matches reuse lookup rows")
    return matches


def orbit_complete(orbit: dict[str, float | None]) -> bool:
    return all(orbit.get(key) is not None for key in ("q", "e", "i", "peri", "node"))


def medoid(orbits: list[dict[str, float]]) -> tuple[int, dict[str, float]]:
    matrix = np.zeros((len(orbits), len(orbits)), dtype=float)
    for left in range(len(orbits)):
        for right in range(left + 1, len(orbits)):
            distance = d_sh(orbits[left], orbits[right])
            matrix[left, right] = distance
            matrix[right, left] = distance
    scores = np.median(matrix, axis=1)
    index = int(np.argmin(scores))
    return index, orbits[index]


def source_summary(assignments: list[dict[str, Any]]) -> dict[str, Any]:
    years = sorted({int(row["year"]) for row in assignments})
    complete = [row for row in assignments if orbit_complete(row["orbit"])]

    def residual(key: str) -> float:
        return median(row["residuals"][key] for row in assignments) if assignments else math.inf

    return {
        "matched_rows": len(assignments),
        "years": years,
        "orbit_complete_rows": len(complete),
        "orbit_complete_fraction": len(complete) / len(assignments) if assignments else 0.0,
        "median_residuals": {
            "dt_s": residual("dt_s"),
            "dls_deg": residual("dls_deg"),
            "radiant_deg": residual("radiant_deg"),
            "dv_km_s": residual("dv_km_s"),
        },
    }


def write_matches(path: Path, assignments: list[dict[str, Any]]) -> None:
    fields = [
        "lookup_number", "lookup_time", "year", "source", "archive", "archive_member", "archive_id",
        "archive_time", "dt_s", "dls_deg", "radiant_deg", "dv_km_s", "q", "e", "i", "peri",
        "node", "d_sh_solution004",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in sorted(assignments, key=lambda item: (item["source"], item["lookup_number"])):
            orbit = row["orbit"]
            writer.writerow(
                {
                    "lookup_number": row["lookup_number"],
                    "lookup_time": row["lookup_time"],
                    "year": row["year"],
                    "source": row["source"],
                    "archive": row["archive"],
                    "archive_member": row["archive_member"],
                    "archive_id": row["archive_id"],
                    "archive_time": row["archive_time"],
                    "dt_s": row["residuals"]["dt_s"],
                    "dls_deg": row["residuals"]["dls_deg"],
                    "radiant_deg": row["residuals"]["radiant_deg"],
                    "dv_km_s": row["residuals"]["dv_km_s"],
                    "q": orbit["q"],
                    "e": orbit["e"],
                    "i": orbit["i"],
                    "peri": orbit["peri"],
                    "node": orbit["node"],
                    "d_sh_solution004": d_sh(
                        {key: float(orbit[key]) for key in ("q", "e", "i", "peri", "node")},
                        SOLUTION004,
                    ),
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lookup", type=Path, required=True)
    parser.add_argument("--gmn-matches", type=Path, required=True)
    parser.add_argument("--cams-matches", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)

    all_target, lookup_by_source = load_lookup(args.lookup)
    target_counts = {source: len(lookup_by_source.get(source, [])) for source in EXPECTED_TARGET_COUNTS}
    locked_gmn = load_locked_matches(args.gmn_matches, "GMN", 17)
    locked_cams = load_locked_matches(args.cams_matches, "CAMS", 48)

    allowed_months: dict[str, dict[int, set[int]]] = defaultdict(lambda: defaultdict(set))
    for source in ("EDMOND", "SonotaCo"):
        for row in lookup_by_source[source]:
            allowed_months[source][int(row["year"])].add(int(row["month"]))

    sources: list[dict[str, Any]] = []
    schemas: list[dict[str, Any]] = []
    edmond_events: list[dict[str, Any]] = []
    sonotaco_events: list[dict[str, Any]] = []
    for year, url in EDMOND_URLS.items():
        archive = args.cache / f"iaumdcedmond{year}.csv.zip"
        sources.append(fetch(url, archive))
        events, year_schemas = read_archive(
            archive, year, allowed_months["EDMOND"].get(year, set()), "EDMOND"
        )
        edmond_events.extend(events)
        schemas.extend(year_schemas)
    for year, url in SONOTACO_URLS.items():
        archive = args.cache / f"iaumdcSNMv3_S{year % 100:02d}.csv.zip"
        sources.append(fetch(url, archive))
        events, year_schemas = read_archive(
            archive, year, allowed_months["SonotaCo"].get(year, set()), "SonotaCo"
        )
        sonotaco_events.extend(events)
        schemas.extend(year_schemas)

    edmond_matches = assign(lookup_by_source["EDMOND"], edmond_events)
    sonotaco_matches = assign(lookup_by_source["SonotaCo"], sonotaco_events)
    summaries = {
        "GMN": source_summary(locked_gmn),
        "CAMS": source_summary(locked_cams),
        "EDMOND": source_summary(edmond_matches),
        "SonotaCo": source_summary(sonotaco_matches),
    }

    edmond_gates = {
        "exactly_75_edmond_lookup_rows": target_counts["EDMOND"] == 75,
        "edmond_at_least_50_matches": summaries["EDMOND"]["matched_rows"] >= 50,
        "edmond_at_least_five_years": len(summaries["EDMOND"]["years"]) >= 5,
        "edmond_orbit_complete_fraction_at_least_0_95": summaries["EDMOND"]["orbit_complete_fraction"] >= 0.95,
        "edmond_median_time_residual_at_most_0_50s": summaries["EDMOND"]["median_residuals"]["dt_s"] <= 0.50,
        "edmond_median_radiant_residual_at_most_0_05deg": summaries["EDMOND"]["median_residuals"]["radiant_deg"] <= 0.05,
        "edmond_median_speed_residual_at_most_0_05kms": summaries["EDMOND"]["median_residuals"]["dv_km_s"] <= 0.05,
    }
    sonotaco_gates = {
        "exactly_60_sonotaco_lookup_rows": target_counts["SonotaCo"] == 60,
        "sonotaco_at_least_40_matches": summaries["SonotaCo"]["matched_rows"] >= 40,
        "sonotaco_at_least_eight_years": len(summaries["SonotaCo"]["years"]) >= 8,
        "sonotaco_orbit_complete_fraction_at_least_0_95": summaries["SonotaCo"]["orbit_complete_fraction"] >= 0.95,
        "sonotaco_median_time_residual_at_most_0_50s": summaries["SonotaCo"]["median_residuals"]["dt_s"] <= 0.50,
        "sonotaco_median_radiant_residual_at_most_0_05deg": summaries["SonotaCo"]["median_residuals"]["radiant_deg"] <= 0.05,
        "sonotaco_median_speed_residual_at_most_0_05kms": summaries["SonotaCo"]["median_residuals"]["dv_km_s"] <= 0.05,
    }

    combined = locked_cams + edmond_matches + sonotaco_matches + locked_gmn
    lookup_numbers = [row["lookup_number"] for row in combined]
    if len(set(lookup_numbers)) != len(lookup_numbers):
        duplicates = [number for number, count in Counter(lookup_numbers).items() if count > 1]
        raise RuntimeError(f"Combined recovery reuses lookup rows: {duplicates}")
    complete = [row for row in combined if orbit_complete(row["orbit"])]
    orbits = [
        {key: float(row["orbit"][key]) for key in ("q", "e", "i", "peri", "node")}
        for row in complete
    ]
    medoid_index: int | None = None
    medoid_orbit: dict[str, float] | None = None
    distances: list[float] = []
    if orbits:
        medoid_index, medoid_orbit = medoid(orbits)
        distances = [d_sh(orbit, SOLUTION004) for orbit in orbits]
    source_counts = Counter(row["source"] for row in combined)
    combined_years = sorted({int(row["year"]) for row in combined})
    orbit_fraction = len(complete) / len(combined) if combined else 0.0
    largest_source_fraction = max(source_counts.values()) / len(combined) if combined else 1.0
    medoid_distance = d_sh(medoid_orbit, SOLUTION004) if medoid_orbit else math.inf
    median_distance = median(distances) if distances else math.inf
    q90_distance = float(np.quantile(distances, 0.90)) if distances else math.inf

    combined_recovery_gates = {
        "exactly_270_archive_covered_lookup_rows": len(all_target) == 270 and target_counts == EXPECTED_TARGET_COUNTS,
        "combined_at_least_150_unique_matches": len(combined) >= 150,
        "all_four_sources_represented": set(source_counts) == {"CAMS", "EDMOND", "SonotaCo", "GMN"},
        "combined_at_least_nine_years": len(combined_years) >= 9,
        "combined_orbit_complete_fraction_at_least_0_95": orbit_fraction >= 0.95,
        "largest_source_fraction_at_most_0_70": largest_source_fraction <= 0.70,
    }
    combined_orbit_gates = {
        "combined_medoid_d_sh_at_most_0_15": medoid_distance <= 0.15,
        "combined_median_member_d_sh_at_most_0_20": median_distance <= 0.20,
        "combined_q90_member_d_sh_at_most_0_35": q90_distance <= 0.35,
    }

    all_recovery_gates = {**edmond_gates, **sonotaco_gates, **combined_recovery_gates}
    if all(all_recovery_gates.values()) and all(combined_orbit_gates.values()):
        verdict = "PROCEED_TO_CONTROL_CALIBRATED_BRANCH_DYNAMICS"
    elif not all(all_recovery_gates.values()):
        verdict = "KILL_MULTISOURCE_RECOVERY_INSUFFICIENT"
    else:
        verdict = "KILL_MULTISOURCE_POPULATION_NOT_ORBITALLY_REPRESENTATIVE"

    write_matches(args.output / "matched_edmond_orbits.csv", edmond_matches)
    write_matches(args.output / "matched_sonotaco_orbits.csv", sonotaco_matches)
    write_matches(args.output / "combined_source_matched_orbits.csv", combined)

    payload = {
        "verdict": verdict,
        "lookup_sha256": sha256(args.lookup),
        "configuration": {
            "max_dt_s": MAX_DT_S,
            "max_dls_deg": MAX_DLS_DEG,
            "max_radiant_deg": MAX_RADIANT_DEG,
            "max_dv_km_s": MAX_DV_KM_S,
            "solution004": SOLUTION004,
            "target_specs": {source: sorted(years) for source, years in TARGET_SPECS.items()},
        },
        "target_counts": target_counts,
        "sources": sources,
        "schemas": schemas,
        "archive_candidate_events": {
            "EDMOND": len(edmond_events),
            "SonotaCo": len(sonotaco_events),
        },
        "source_summaries": summaries,
        "edmond_gates": edmond_gates,
        "sonotaco_gates": sonotaco_gates,
        "combined": {
            "matched_rows": len(combined),
            "source_counts": dict(source_counts),
            "years": combined_years,
            "orbit_complete_rows": len(complete),
            "orbit_complete_fraction": orbit_fraction,
            "largest_source_fraction": largest_source_fraction,
            "medoid_complete_orbit_index": medoid_index,
            "medoid_orbit": medoid_orbit,
            "medoid_d_sh_to_solution004": medoid_distance,
            "member_d_sh_to_solution004": {
                "median": median_distance,
                "q90": q90_distance,
                "minimum": min(distances) if distances else math.inf,
                "maximum": max(distances) if distances else math.inf,
            },
        },
        "combined_recovery_gates": combined_recovery_gates,
        "combined_orbit_gates": combined_orbit_gates,
    }
    (args.output / "multisource_recovery.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Final multi-source orbit recovery for NOP solution 004",
        "",
        f"- target lookup rows: **{len(all_target)}**",
        f"- locked CAMS / GMN matches: **{len(locked_cams)} / {len(locked_gmn)}**",
        f"- recovered EDMOND matches: **{len(edmond_matches)}**",
        f"- recovered SonotaCo matches: **{len(sonotaco_matches)}**",
        f"- combined exact source-matched orbits: **{len(combined)}**",
        f"- source counts: **{dict(source_counts)}**",
        f"- observing years: **{', '.join(map(str, combined_years)) or 'none'}**",
        f"- combined orbit completeness: **{orbit_fraction:.4f}**",
        f"- combined medoid D_SH: **{medoid_distance:.6f}**",
        f"- combined median / q90 member D_SH: **{median_distance:.6f} / {q90_distance:.6f}**",
        "",
        "## EDMOND gates",
        "",
    ]
    lines.extend(f"- {'PASS' if passed else 'FAIL'} — `{name}`" for name, passed in edmond_gates.items())
    lines.extend(["", "## SonotaCo gates", ""])
    lines.extend(f"- {'PASS' if passed else 'FAIL'} — `{name}`" for name, passed in sonotaco_gates.items())
    lines.extend(["", "## Combined recovery gates", ""])
    lines.extend(f"- {'PASS' if passed else 'FAIL'} — `{name}`" for name, passed in combined_recovery_gates.items())
    lines.extend(["", "## Combined orbital-distribution gates", ""])
    lines.extend(f"- {'PASS' if passed else 'FAIL'} — `{name}`" for name, passed in combined_orbit_gates.items())
    lines.extend(["", f"Verdict: **{verdict}**", ""])
    report = "\n".join(lines)
    (args.output / "MULTISOURCE_RECOVERY_REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
