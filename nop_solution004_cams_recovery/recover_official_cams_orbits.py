from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import urllib.request
import zipfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

LOOKUP_SHA256 = "9ec720202966f1eda18c99c8decaa338d9be0bae913be4c2ff6ed34f2661282e"
YEARS = tuple(range(2011, 2017))
ARCHIVES = {
    year: f"https://ceres.ta3.sk/iaumdcdb/dataDBs/video_offline/iaumdcCAMSv3_{year}.csv.zip"
    for year in YEARS
}
USER_AGENT = "ghoststream-nop004-cams-recovery/1.0"
MAX_DT_S = 2.5
MAX_DLS_DEG = 0.02
MAX_RADIANT_DEG = 0.20
MAX_DV_KM_S = 0.25
BIG = 1.0e9
SOLUTION004 = {"q": 0.207, "e": 0.932, "i": 16.7, "peri": 310.5, "node": 58.6}


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
    with urllib.request.urlopen(request, timeout=600) as response, path.open("wb") as output:
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


def load_lookup(path: Path) -> list[dict[str, Any]]:
    if sha256(path) != LOOKUP_SHA256:
        raise RuntimeError("Exact NOP solution-004 lookup SHA-256 mismatch")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle, skipinitialspace=True):
            if (raw.get("Sode") or "").strip() != "CAMS":
                continue
            timestamp = parse_lookup_time(raw["Tobs"])
            if timestamp.year not in YEARS:
                continue
            rows.append(
                {
                    "lookup_number": int(raw["CurNum"]),
                    "source": "CAMS",
                    "time": timestamp,
                    "time_text": raw["Tobs"].strip(),
                    "year": timestamp.year,
                    "month": timestamp.month,
                    "sol": float(raw["LS"]),
                    "ra": float(raw["RA"]),
                    "dec": float(raw["DEC"]),
                    "vg": float(raw["Vg"]),
                }
            )
    return rows


def documented_columns(headers: list[str]) -> dict[str, str]:
    options = {
        "year": ("Yr", "YEAR", "Year"),
        "month": ("Mn", "MONTH", "Month"),
        "day": ("Day", "DAY"),
        "sol": ("LS", "Sol", "SOL"),
        "ra": ("RA",),
        "dec": ("DECL", "DEC", "DE"),
        "vg": ("Vg", "VG"),
        "q": ("q",),
        "e": ("e",),
        "i": ("i",),
        "peri": ("arg", "peri"),
        "node": ("nod", "node"),
        "id": ("Ano", "ID", "Id"),
    }
    available = set(headers)
    mapping: dict[str, str] = {}
    for target, candidates in options.items():
        match = next((candidate for candidate in candidates if candidate in available), None)
        if match is None:
            raise RuntimeError(f"CAMS archive is missing documented `{target}` column; headers={headers}")
        mapping[target] = match
    return mapping


def read_archive(path: Path, expected_year: int, allowed_months: set[int]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    schemas: list[dict[str, Any]] = []
    with zipfile.ZipFile(path) as bundle:
        members = [
            member for member in bundle.infolist()
            if not member.is_dir() and member.filename.lower().endswith((".csv", ".txt"))
        ]
        if not members:
            raise RuntimeError(f"No CSV/TXT members in {path.name}")
        for member in members:
            with bundle.open(member) as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="")
                header_line = next(text, "")
                first_data_line = next(text, "")
            headers = header_line.split()
            columns = documented_columns(headers)
            delimiter = max((",", ";", "\t", "|"), key=first_data_line.count)
            if first_data_line.count(delimiter) < 4:
                raise RuntimeError(f"Could not identify CAMS row delimiter in {member.filename}")
            schema = {
                "archive": path.name,
                "member": member.filename,
                "compressed_bytes": member.compress_size,
                "uncompressed_bytes": member.file_size,
                "headers": headers,
                "columns": columns,
                "delimiter": delimiter,
                "format": "fixed-width whitespace header with delimited rows",
            }
            schemas.append(schema)
            with bundle.open(member) as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="")
                next(text, None)
                reader = csv.DictReader(
                    text,
                    fieldnames=headers,
                    delimiter=delimiter,
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
                "lookup": {key: value for key, value in lookup[left].items() if key != "time"},
                "cams": {
                    "archive": event["archive"],
                    "member": event["member"],
                    "id": event["id"],
                    "time": event["time_text"],
                    "sol": event["sol"],
                    "ra": event["ra"],
                    "dec": event["dec"],
                    "vg": event["vg"],
                    "orbit": event["orbit"],
                },
                "residuals": edges[(left, event_index)],
            }
        )
    return assignments


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lookup", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)

    lookup = load_lookup(args.lookup)
    allowed_months: dict[int, set[int]] = defaultdict(set)
    for row in lookup:
        allowed_months[int(row["year"])].add(int(row["month"]))

    sources: list[dict[str, Any]] = []
    schemas: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    for year in YEARS:
        archive = args.cache / f"iaumdcCAMSv3_{year}.csv.zip"
        sources.append(fetch(ARCHIVES[year], archive))
        year_events, year_schemas = read_archive(archive, year, allowed_months.get(year, set()))
        events.extend(year_events)
        schemas.extend(year_schemas)

    assignments = assign(lookup, events)
    complete = [item for item in assignments if orbit_complete(item["cams"]["orbit"])]
    orbits = [
        {key: float(item["cams"]["orbit"][key]) for key in ("q", "e", "i", "peri", "node")}
        for item in complete
    ]
    years = sorted({int(item["lookup"]["year"]) for item in assignments})
    medoid_index: int | None = None
    medoid_orbit: dict[str, float] | None = None
    distances: list[float] = []
    if orbits:
        medoid_index, medoid_orbit = medoid(orbits)
        distances = [d_sh(orbit, SOLUTION004) for orbit in orbits]

    def residual(key: str) -> float:
        return median(item["residuals"][key] for item in assignments) if assignments else math.inf

    orbit_fraction = len(complete) / len(assignments) if assignments else 0.0
    medoid_distance = d_sh(medoid_orbit, SOLUTION004) if medoid_orbit else math.inf
    median_distance = median(distances) if distances else math.inf
    q90_distance = float(np.quantile(distances, 0.90)) if distances else math.inf
    gates = {
        "exactly_100_eligible_cams_lookup_rows": len(lookup) == 100,
        "at_least_80_unique_matches": len(assignments) >= 80,
        "at_least_five_years_represented": len(years) >= 5,
        "orbit_complete_fraction_at_least_0_95": orbit_fraction >= 0.95,
        "median_time_residual_at_most_0_50s": residual("dt_s") <= 0.50,
        "median_radiant_residual_at_most_0_05deg": residual("radiant_deg") <= 0.05,
        "median_speed_residual_at_most_0_05kms": residual("dv_km_s") <= 0.05,
        "recovered_medoid_d_sh_at_most_0_15": medoid_distance <= 0.15,
        "median_member_d_sh_at_most_0_20": median_distance <= 0.20,
        "q90_member_d_sh_at_most_0_35": q90_distance <= 0.35,
    }
    observational_keys = list(gates)[:7]
    if all(gates.values()):
        verdict = "PROCEED_TO_SOURCE_MATCHED_BRANCH_DYNAMICS"
    elif not all(gates[key] for key in observational_keys):
        verdict = "KILL_CAMS_ORBIT_RECOVERY_INSUFFICIENT"
    else:
        verdict = "KILL_CAMS_SUBSET_NOT_ORBITALLY_REPRESENTATIVE"

    payload = {
        "verdict": verdict,
        "lookup_sha256": sha256(args.lookup),
        "configuration": {
            "years": YEARS,
            "max_dt_s": MAX_DT_S,
            "max_dls_deg": MAX_DLS_DEG,
            "max_radiant_deg": MAX_RADIANT_DEG,
            "max_dv_km_s": MAX_DV_KM_S,
            "solution004": SOLUTION004,
        },
        "sources": sources,
        "schemas": schemas,
        "eligible_lookup_rows": len(lookup),
        "archive_candidate_events": len(events),
        "matched_rows": len(assignments),
        "matched_years": years,
        "orbit_complete_rows": len(complete),
        "orbit_complete_fraction": orbit_fraction,
        "median_residuals": {
            "dt_s": residual("dt_s"),
            "dls_deg": residual("dls_deg"),
            "radiant_deg": residual("radiant_deg"),
            "dv_km_s": residual("dv_km_s"),
        },
        "medoid_complete_orbit_index": medoid_index,
        "medoid_orbit": medoid_orbit,
        "medoid_d_sh_to_solution004": medoid_distance,
        "member_d_sh_to_solution004": {
            "median": median_distance,
            "q90": q90_distance,
            "minimum": min(distances) if distances else math.inf,
            "maximum": max(distances) if distances else math.inf,
        },
        "gates": gates,
        "assignments": assignments,
    }
    (args.output / "cams_orbit_recovery.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with (args.output / "matched_cams_orbits.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "lookup_number", "lookup_time", "archive", "archive_member", "archive_id", "archive_time",
            "dt_s", "dls_deg", "radiant_deg", "dv_km_s", "q", "e", "i", "peri", "node",
            "d_sh_solution004",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in assignments:
            orbit = item["cams"]["orbit"]
            complete_orbit = orbit_complete(orbit)
            writer.writerow(
                {
                    "lookup_number": item["lookup"]["lookup_number"],
                    "lookup_time": item["lookup"]["time_text"],
                    "archive": item["cams"]["archive"],
                    "archive_member": item["cams"]["member"],
                    "archive_id": item["cams"]["id"],
                    "archive_time": item["cams"]["time"],
                    "dt_s": item["residuals"]["dt_s"],
                    "dls_deg": item["residuals"]["dls_deg"],
                    "radiant_deg": item["residuals"]["radiant_deg"],
                    "dv_km_s": item["residuals"]["dv_km_s"],
                    "q": orbit.get("q"),
                    "e": orbit.get("e"),
                    "i": orbit.get("i"),
                    "peri": orbit.get("peri"),
                    "node": orbit.get("node"),
                    "d_sh_solution004": (
                        d_sh(
                            {key: float(orbit[key]) for key in ("q", "e", "i", "peri", "node")},
                            SOLUTION004,
                        )
                        if complete_orbit
                        else None
                    ),
                }
            )

    lines = [
        "# Official CAMS orbit recovery for NOP solution 004",
        "",
        f"- eligible CAMS lookup rows: **{len(lookup)}**",
        f"- archive candidate events: **{len(events):,}**",
        f"- unique matched rows: **{len(assignments)}**",
        f"- matched years: **{', '.join(map(str, years)) or 'none'}**",
        f"- orbit completeness: **{orbit_fraction:.4f}**",
        f"- median time/radiant/speed residual: **{residual('dt_s'):.4f} s / {residual('radiant_deg'):.6f}° / {residual('dv_km_s'):.6f} km/s**",
        f"- medoid D_SH to solution 004: **{medoid_distance:.6f}**",
        f"- median / q90 member D_SH: **{median_distance:.6f} / {q90_distance:.6f}**",
        "",
        "## Frozen gates",
        "",
    ]
    lines.extend(f"- {'PASS' if passed else 'FAIL'} — `{name}`" for name, passed in gates.items())
    lines.extend(["", f"Verdict: **{verdict}**", ""])
    report = "\n".join(lines)
    (args.output / "CAMS_ORBIT_RECOVERY_REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
