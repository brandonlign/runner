from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import urllib.request
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from typing import Any, Iterator

import numpy as np
from scipy.optimize import linear_sum_assignment

from nop_solution004_gmn_recovery.recover_exact_gmn_orbits import (
    BIG,
    LOOKUP_SHA256,
    SOLUTION004,
    d_sh,
    edge_metrics,
    load_lookup,
    medoid,
    orbit_complete,
    sha256,
)

USER_AGENT = "ghoststream-nop004-iau-gmn-recovery/1.0"
ARCHIVES = {
    2019: "https://ceres.ta3.sk/iaumdcdb/dataDBs/video_offline/iaumdcgmn2019.csv.zip",
    2020: "https://ceres.ta3.sk/iaumdcdb/dataDBs/video_offline/iaumdcgmn2020.csv.zip",
}
ALIASES = {
    "year": {"yr", "year"},
    "month": {"mn", "month"},
    "day": {"day"},
    "sol": {"ls", "sol", "solarlongitude"},
    "ra": {"ra"},
    "dec": {"dec", "de"},
    "vg": {"vg"},
    "q": {"q"},
    "e": {"e"},
    "i": {"i", "inc", "inclination"},
    "peri": {"arg", "peri", "argumentofperihelion"},
    "node": {"nod", "node", "ascendingnode"},
    "id": {"ic", "ano", "id"},
}


def normalize(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").strip().lower())


def as_float(value: str | None) -> float | None:
    try:
        number = float((value or "").strip().replace("−", "-"))
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def fetch(url: str, path: Path) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
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


def map_columns(headers: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for target, aliases in ALIASES.items():
        matches = [header for header in headers if normalize(header) in aliases]
        if len(matches) == 1:
            mapping[target] = matches[0]
    return mapping


def member_rows(archive: Path) -> Iterator[tuple[str, dict[str, str], dict[str, str], dict[str, Any]]]:
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            if member.is_dir() or not member.filename.lower().endswith((".csv", ".txt")):
                continue
            with bundle.open(member) as raw:
                sample = raw.read(128 * 1024).decode("utf-8-sig", "replace")
            lines = sample.splitlines()
            header_index = None
            delimiter = None
            for index, line in enumerate(lines[:50]):
                candidate_delimiter = max((";", ",", "\t", "|"), key=line.count)
                if line.count(candidate_delimiter) < 4:
                    continue
                parsed = next(csv.reader([line], delimiter=candidate_delimiter))
                normalized = {normalize(value) for value in parsed}
                required = sum(bool(normalized & ALIASES[key]) for key in ("year", "month", "day", "ra", "dec", "vg", "q", "e", "i", "peri", "node"))
                if required >= 9:
                    header_index = index
                    delimiter = candidate_delimiter
                    break
            if header_index is None or delimiter is None:
                continue
            with bundle.open(member) as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="")
                for _ in range(header_index):
                    next(text, None)
                reader = csv.DictReader(text, delimiter=delimiter)
                headers = [header or "" for header in (reader.fieldnames or [])]
                columns = map_columns(headers)
                schema = {
                    "member": member.filename,
                    "compressed_bytes": member.compress_size,
                    "uncompressed_bytes": member.file_size,
                    "delimiter": delimiter,
                    "header_index": header_index,
                    "headers": headers,
                    "columns": columns,
                }
                for row in reader:
                    yield member.filename, row, columns, schema


def fractional_day_time(year: int, month: int, day_value: float) -> datetime:
    return datetime(year, month, 1, tzinfo=timezone.utc) + timedelta(days=day_value - 1.0)


def load_archive_events(path: Path, expected_year: int, allowed_months: set[int]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    schemas: dict[str, dict[str, Any]] = {}
    for member, row, columns, schema in member_rows(path):
        schemas[member] = schema
        if not all(key in columns for key in ("year", "month", "day", "sol", "ra", "dec", "vg", "q", "e", "i", "peri", "node")):
            continue
        year_value = as_float(row.get(columns["year"]))
        month_value = as_float(row.get(columns["month"]))
        day_value = as_float(row.get(columns["day"]))
        if year_value is None or month_value is None or day_value is None:
            continue
        year = int(round(year_value))
        month = int(round(month_value))
        if year != expected_year or month not in allowed_months:
            continue
        values = {key: as_float(row.get(columns[key])) for key in ("sol", "ra", "dec", "vg", "q", "e", "i", "peri", "node")}
        if any(values[key] is None for key in ("sol", "ra", "dec", "vg")):
            continue
        timestamp = fractional_day_time(year, month, day_value)
        event_id = row.get(columns.get("id", "")) if "id" in columns else None
        events.append(
            {
                "global_index": len(events),
                "archive_member": member,
                "id": (event_id or "").strip(),
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
    return events, list(schemas.values())


def assign(lookup: list[dict[str, Any]], events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    edges: dict[tuple[int, int], dict[str, float]] = {}
    candidate_indices: set[int] = set()
    for left, row in enumerate(lookup):
        for event in events:
            if event["time"].date() != row["time"].date():
                continue
            metrics = edge_metrics(row, event)
            if metrics is None:
                continue
            edges[(left, event["global_index"])] = metrics
            candidate_indices.add(event["global_index"])
    ordered = sorted(candidate_indices)
    position = {index: column for column, index in enumerate(ordered)}
    width = max(len(lookup), len(ordered))
    cost = np.full((len(lookup), width), BIG, dtype=float)
    for (left, event_index), metrics in edges.items():
        cost[left, position[event_index]] = metrics["cost"]
    rows, columns = linear_sum_assignment(cost)
    assignments: list[dict[str, Any]] = []
    event_map = {event["global_index"]: event for event in events}
    for left, column in zip(rows.tolist(), columns.tolist()):
        if column >= len(ordered) or cost[left, column] >= BIG / 2.0:
            continue
        event_index = ordered[column]
        event = event_map[event_index]
        assignments.append(
            {
                "lookup": {key: value for key, value in lookup[left].items() if key != "time"},
                "archive": {
                    "member": event["archive_member"],
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lookup", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)

    if sha256(args.lookup) != LOOKUP_SHA256:
        raise RuntimeError("Exact lookup hash mismatch")
    lookup = load_lookup(args.lookup)
    allowed_months: dict[int, set[int]] = {}
    for row in lookup:
        allowed_months.setdefault(int(row["year"]), set()).add(int(row["month"]))

    sources: list[dict[str, Any]] = []
    schemas: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    for year, url in ARCHIVES.items():
        archive = args.cache / Path(urllib.request.urlparse(url).path).name if hasattr(urllib.request, "urlparse") else args.cache / f"iaumdcgmn{year}.csv.zip"
        archive = args.cache / f"iaumdcgmn{year}.csv.zip"
        sources.append(fetch(url, archive))
        year_events, year_schemas = load_archive_events(archive, year, allowed_months.get(year, set()))
        for event in year_events:
            event["global_index"] = len(events)
            events.append(event)
        schemas.extend(year_schemas)

    assignments = assign(lookup, events)
    complete = [item for item in assignments if orbit_complete(item["archive"]["orbit"])]
    orbits = [
        {key: float(item["archive"]["orbit"][key]) for key in ("q", "e", "i", "peri", "node")}
        for item in complete
    ]
    years = sorted({int(item["lookup"]["year"]) for item in assignments})
    medoid_orbit = None
    medoid_index = None
    distances: list[float] = []
    if orbits:
        medoid_index, medoid_orbit = medoid(orbits)
        distances = [d_sh(orbit, SOLUTION004) for orbit in orbits]
    residual = lambda key: median(item["residuals"][key] for item in assignments) if assignments else math.inf
    orbit_fraction = len(complete) / len(assignments) if assignments else 0.0
    medoid_distance = d_sh(medoid_orbit, SOLUTION004) if medoid_orbit else math.inf
    median_distance = median(distances) if distances else math.inf
    q90_distance = float(np.quantile(distances, 0.90)) if distances else math.inf
    gates = {
        "exactly_35_gmn_lookup_rows": len(lookup) == 35,
        "at_least_30_unique_matches": len(assignments) >= 30,
        "both_2019_and_2020_represented": years == [2019, 2020],
        "orbit_complete_fraction_at_least_0_95": orbit_fraction >= 0.95,
        "median_time_residual_at_most_0_50s": residual("dt_s") <= 0.50,
        "median_radiant_residual_at_most_0_05deg": residual("radiant_deg") <= 0.05,
        "median_speed_residual_at_most_0_05kms": residual("dv_km_s") <= 0.05,
        "recovered_medoid_d_sh_at_most_0_15": medoid_distance <= 0.15,
        "median_member_d_sh_at_most_0_20": median_distance <= 0.20,
        "q90_member_d_sh_at_most_0_35": q90_distance <= 0.35,
    }
    basic = list(gates)[:7]
    if all(gates.values()):
        verdict = "PROCEED_TO_SOURCE_MATCHED_BRANCH_DYNAMICS"
    elif not all(gates[key] for key in basic):
        verdict = "KILL_IAU_GMN_ARCHIVE_RECOVERY_INSUFFICIENT"
    else:
        verdict = "KILL_IAU_GMN_ARCHIVE_SUBSET_NOT_ORBITALLY_REPRESENTATIVE"

    payload = {
        "verdict": verdict,
        "lookup_sha256": sha256(args.lookup),
        "sources": sources,
        "schemas": schemas,
        "lookup_gmn_rows": len(lookup),
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
    (args.output / "iau_gmn_archive_recovery.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with (args.output / "matched_iau_gmn_orbits.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["lookup_number", "lookup_time", "archive_member", "archive_id", "archive_time", "dt_s", "dls_deg", "radiant_deg", "dv_km_s", "q", "e", "i", "peri", "node", "d_sh_solution004"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in assignments:
            orbit = item["archive"]["orbit"]
            complete_orbit = orbit_complete(orbit)
            writer.writerow(
                {
                    "lookup_number": item["lookup"]["lookup_number"],
                    "lookup_time": item["lookup"]["time_text"],
                    "archive_member": item["archive"]["member"],
                    "archive_id": item["archive"]["id"],
                    "archive_time": item["archive"]["time"],
                    "dt_s": item["residuals"]["dt_s"],
                    "dls_deg": item["residuals"]["dls_deg"],
                    "radiant_deg": item["residuals"]["radiant_deg"],
                    "dv_km_s": item["residuals"]["dv_km_s"],
                    "q": orbit.get("q"), "e": orbit.get("e"), "i": orbit.get("i"), "peri": orbit.get("peri"), "node": orbit.get("node"),
                    "d_sh_solution004": d_sh({key: float(orbit[key]) for key in ("q", "e", "i", "peri", "node")}, SOLUTION004) if complete_orbit else None,
                }
            )

    lines = [
        "# IAU-GMN snapshot recovery for NOP solution 004",
        "",
        f"- exact lookup GMN rows: **{len(lookup)}**",
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
    (args.output / "IAU_GMN_ARCHIVE_RECOVERY_REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
