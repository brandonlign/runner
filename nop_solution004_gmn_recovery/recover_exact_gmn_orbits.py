from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import urllib.request
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

LOOKUP_SHA256 = "9ec720202966f1eda18c99c8decaa338d9be0bae913be4c2ff6ed34f2661282e"
GMN_URL = (
    "https://globalmeteornetwork.org/data/traj_summary_data/monthly/"
    "traj_summary_monthly_{year}{month:02d}.txt"
)
USER_AGENT = "ghoststream-nop004-gmn-recovery/1.0"
MAX_DT_S = 2.5
MAX_DLS_DEG = 0.02
MAX_RADIANT_DEG = 0.20
MAX_DV_KM_S = 0.25
BIG = 1.0e9
SOLUTION004 = {"q": 0.207, "e": 0.932, "i": 16.7, "peri": 310.5, "node": 58.6}

IDX = {
    "id": 0,
    "utc": 2,
    "sol": 5,
    "ra": 7,
    "dec": 9,
    "vg": 15,
    "a": 23,
    "e": 25,
    "i": 27,
    "peri": 29,
    "node": 31,
    "q": 37,
}


@dataclass
class SourceRecord:
    url: str
    path: str
    bytes: int
    sha256: str
    content_type: str | None
    last_modified: str | None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def as_float(value: str | None) -> float | None:
    text = (value or "").strip()
    if not text or text.lower() in {"nan", "none", "null", "na", "..."}:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def value(row: list[str], key: str) -> str | None:
    index = IDX[key]
    return row[index].strip() if index < len(row) else None


def parse_lookup_time(text: str) -> datetime:
    return datetime.strptime(text.strip(), "%Y-%m-%d-%H:%M:%S").replace(tzinfo=timezone.utc)


def parse_gmn_time(text: str) -> datetime | None:
    cleaned = text.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        for pattern in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
            try:
                parsed = datetime.strptime(cleaned, pattern)
                break
            except ValueError:
                parsed = None
        if parsed is None:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def circular_delta(a: float, b: float) -> float:
    return (a - b + 180.0) % 360.0 - 180.0


def angular_separation(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    r1, d1, r2, d2 = map(math.radians, (ra1, dec1, ra2, dec2))
    cosine = math.sin(d1) * math.sin(d2) + math.cos(d1) * math.cos(d2) * math.cos(r1 - r2)
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def d_sh(first: dict[str, float], second: dict[str, float]) -> float:
    q1, e1 = first["q"], first["e"]
    q2, e2 = second["q"], second["e"]
    i1, w1, node1 = map(math.radians, (first["i"], first["peri"], first["node"]))
    i2, w2, node2 = map(math.radians, (second["i"], second["peri"], second["node"]))
    delta_node = math.atan2(math.sin(node1 - node2), math.cos(node1 - node2))
    cos_i = math.cos(i1) * math.cos(i2) + math.sin(i1) * math.sin(i2) * math.cos(delta_node)
    mutual_i = math.acos(max(-1.0, min(1.0, cos_i)))
    denominator = max(math.cos(mutual_i / 2.0), 1.0e-12)
    argument = math.cos((i1 + i2) / 2.0) * math.sin(delta_node / 2.0) / denominator
    peri_difference = w1 - w2 + 2.0 * math.asin(max(-1.0, min(1.0, argument)))
    return math.sqrt(
        (e1 - e2) ** 2
        + (q1 - q2) ** 2
        + (2.0 * math.sin(mutual_i / 2.0)) ** 2
        + (((e1 + e2) / 2.0) * 2.0 * math.sin(peri_difference / 2.0)) ** 2
    )


def fetch(url: str, path: Path) -> SourceRecord:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    digest = hashlib.sha256()
    total = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(request, timeout=300) as response, path.open("wb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            total += len(chunk)
            output.write(chunk)
        return SourceRecord(
            url=url,
            path=str(path),
            bytes=total,
            sha256=digest.hexdigest(),
            content_type=response.headers.get("Content-Type"),
            last_modified=response.headers.get("Last-Modified"),
        )


def load_lookup(path: Path) -> list[dict[str, Any]]:
    if sha256(path) != LOOKUP_SHA256:
        raise RuntimeError("Exact solution-004 lookup SHA-256 mismatch")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle, skipinitialspace=True):
            source = (raw.get("Sode") or "").strip()
            if source != "GMN":
                continue
            timestamp = parse_lookup_time(raw["Tobs"])
            event = {
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
            rows.append(event)
    return rows


def load_gmn(path: Path, year: int, month: int) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.reader(handle, delimiter=";")
        for row_number, row in enumerate(reader, start=1):
            if not row or row[0].lstrip().startswith("#") or len(row) <= max(IDX.values()):
                continue
            timestamp = parse_gmn_time(value(row, "utc") or "")
            sol = as_float(value(row, "sol"))
            ra = as_float(value(row, "ra"))
            dec = as_float(value(row, "dec"))
            vg = as_float(value(row, "vg"))
            if timestamp is None or None in (sol, ra, dec, vg):
                continue
            if timestamp.year != year or timestamp.month != month:
                continue
            events.append(
                {
                    "index": len(events),
                    "row_number": row_number,
                    "id": value(row, "id"),
                    "time": timestamp,
                    "time_text": timestamp.isoformat(),
                    "sol": float(sol),
                    "ra": float(ra),
                    "dec": float(dec),
                    "vg": float(vg),
                    "orbit": {
                        "a": as_float(value(row, "a")),
                        "q": as_float(value(row, "q")),
                        "e": as_float(value(row, "e")),
                        "i": as_float(value(row, "i")),
                        "peri": as_float(value(row, "peri")),
                        "node": as_float(value(row, "node")),
                    },
                }
            )
    return events


def edge_metrics(lookup: dict[str, Any], event: dict[str, Any]) -> dict[str, float] | None:
    dt = abs((event["time"] - lookup["time"]).total_seconds())
    dls = abs(circular_delta(event["sol"], lookup["sol"]))
    radiant = angular_separation(event["ra"], event["dec"], lookup["ra"], lookup["dec"])
    dv = abs(event["vg"] - lookup["vg"])
    if dt > MAX_DT_S or dls > MAX_DLS_DEG or radiant > MAX_RADIANT_DEG or dv > MAX_DV_KM_S:
        return None
    cost = (dt / MAX_DT_S) ** 2 + (dls / MAX_DLS_DEG) ** 2 + (radiant / MAX_RADIANT_DEG) ** 2 + (dv / MAX_DV_KM_S) ** 2
    return {"dt_s": dt, "dls_deg": dls, "radiant_deg": radiant, "dv_km_s": dv, "cost": cost}


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
    strata = sorted({(row["year"], row["month"]) for row in lookup})
    sources: list[SourceRecord] = []
    gmn_events: list[dict[str, Any]] = []
    for year, month in strata:
        path = args.cache / f"traj_summary_monthly_{year}{month:02d}.txt"
        sources.append(fetch(GMN_URL.format(year=year, month=month), path))
        events = load_gmn(path, year, month)
        for event in events:
            event["global_index"] = len(gmn_events)
            gmn_events.append(event)

    nearby_indices: set[int] = set()
    edge_lookup: dict[tuple[int, int], dict[str, float]] = {}
    for left, row in enumerate(lookup):
        for event in gmn_events:
            if event["time"].date() != row["time"].date():
                continue
            metrics = edge_metrics(row, event)
            if metrics is None:
                continue
            nearby_indices.add(event["global_index"])
            edge_lookup[(left, event["global_index"])] = metrics

    candidate_indices = sorted(nearby_indices)
    candidate_position = {global_index: position for position, global_index in enumerate(candidate_indices)}
    width = max(len(candidate_indices), len(lookup))
    matrix = np.full((len(lookup), width), BIG, dtype=float)
    for (left, global_index), metrics in edge_lookup.items():
        matrix[left, candidate_position[global_index]] = metrics["cost"]

    row_indices, column_indices = linear_sum_assignment(matrix)
    assignments: list[dict[str, Any]] = []
    for left, column in zip(row_indices.tolist(), column_indices.tolist()):
        if column >= len(candidate_indices) or matrix[left, column] >= BIG / 2.0:
            continue
        global_index = candidate_indices[column]
        event = gmn_events[global_index]
        metrics = edge_lookup[(left, global_index)]
        assignments.append(
            {
                "lookup": {key: value for key, value in lookup[left].items() if key != "time"},
                "gmn": {
                    "id": event["id"],
                    "time": event["time_text"],
                    "row_number": event["row_number"],
                    "sol": event["sol"],
                    "ra": event["ra"],
                    "dec": event["dec"],
                    "vg": event["vg"],
                    "orbit": event["orbit"],
                },
                "residuals": metrics,
            }
        )

    complete_assignments = [item for item in assignments if orbit_complete(item["gmn"]["orbit"])]
    complete_orbits: list[dict[str, float]] = [
        {key: float(item["gmn"]["orbit"][key]) for key in ("q", "e", "i", "peri", "node")}
        for item in complete_assignments
    ]
    years = sorted({int(item["lookup"]["year"]) for item in assignments})
    medoid_orbit: dict[str, float] | None = None
    medoid_index: int | None = None
    distances: list[float] = []
    if complete_orbits:
        medoid_index, medoid_orbit = medoid(complete_orbits)
        distances = [d_sh(orbit, SOLUTION004) for orbit in complete_orbits]

    residual = lambda key: median(item["residuals"][key] for item in assignments) if assignments else math.inf
    orbit_fraction = len(complete_assignments) / len(assignments) if assignments else 0.0
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
    basic_keys = list(gates)[:7]
    if all(gates.values()):
        verdict = "PROCEED_TO_SOURCE_MATCHED_BRANCH_DYNAMICS"
    elif not all(gates[key] for key in basic_keys):
        verdict = "KILL_GMN_ORBIT_RECOVERY_INSUFFICIENT"
    else:
        verdict = "KILL_GMN_SUBSET_NOT_ORBITALLY_REPRESENTATIVE"

    payload = {
        "verdict": verdict,
        "lookup_sha256": sha256(args.lookup),
        "configuration": {
            "max_dt_s": MAX_DT_S,
            "max_dls_deg": MAX_DLS_DEG,
            "max_radiant_deg": MAX_RADIANT_DEG,
            "max_dv_km_s": MAX_DV_KM_S,
            "solution004": SOLUTION004,
        },
        "sources": [asdict(source) for source in sources],
        "lookup_gmn_rows": len(lookup),
        "candidate_gmn_events": len(gmn_events),
        "eligible_candidate_events": len(candidate_indices),
        "matched_rows": len(assignments),
        "matched_years": years,
        "orbit_complete_rows": len(complete_assignments),
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
    (args.output / "gmn_orbit_recovery.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with (args.output / "matched_gmn_orbits.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "lookup_number", "lookup_time", "gmn_id", "gmn_time", "dt_s", "dls_deg", "radiant_deg", "dv_km_s",
            "q", "e", "i", "peri", "node", "d_sh_solution004",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in assignments:
            orbit = item["gmn"]["orbit"]
            complete = orbit_complete(orbit)
            row = {
                "lookup_number": item["lookup"]["lookup_number"],
                "lookup_time": item["lookup"]["time_text"],
                "gmn_id": item["gmn"]["id"],
                "gmn_time": item["gmn"]["time"],
                "dt_s": item["residuals"]["dt_s"],
                "dls_deg": item["residuals"]["dls_deg"],
                "radiant_deg": item["residuals"]["radiant_deg"],
                "dv_km_s": item["residuals"]["dv_km_s"],
                "q": orbit.get("q"), "e": orbit.get("e"), "i": orbit.get("i"),
                "peri": orbit.get("peri"), "node": orbit.get("node"),
                "d_sh_solution004": d_sh({key: float(orbit[key]) for key in ("q", "e", "i", "peri", "node")}, SOLUTION004) if complete else None,
            }
            writer.writerow(row)

    lines = [
        "# Exact GMN orbit recovery for NOP solution 004",
        "",
        f"- exact lookup GMN rows: **{len(lookup)}**",
        f"- unique matched GMN trajectories: **{len(assignments)}**",
        f"- matched years: **{', '.join(map(str, years)) or 'none'}**",
        f"- orbit completeness: **{orbit_fraction:.4f}**",
        f"- median time residual: **{residual('dt_s'):.4f} s**",
        f"- median radiant residual: **{residual('radiant_deg'):.6f}°**",
        f"- median speed residual: **{residual('dv_km_s'):.6f} km/s**",
        f"- medoid D_SH to solution 004: **{medoid_distance:.6f}**",
        f"- median / q90 member D_SH: **{median_distance:.6f} / {q90_distance:.6f}**",
        "",
        "## Frozen gates",
        "",
    ]
    lines.extend(f"- {'PASS' if passed else 'FAIL'} — `{name}`" for name, passed in gates.items())
    lines.extend(["", f"Verdict: **{verdict}**", ""])
    report = "\n".join(lines)
    (args.output / "GMN_ORBIT_RECOVERY_REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
