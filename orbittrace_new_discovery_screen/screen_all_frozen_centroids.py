#!/usr/bin/env python3
"""Compute-only mirror of orbittrace-raw prospective centroid triage.

Scientific source-of-truth lives in brandonlign/orbittrace-raw under
pipeline/discovery_search.  This public runner copy exists only because private
raw-repository Actions are currently not starting jobs.  It does not change
candidate identities, memberships, or frozen ranks.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
from pathlib import Path
from typing import Any

SPORADIC_SOURCES = {
    "HELION": (342.0, 0.0),
    "ANTIHELION": (198.0, 0.0),
    "NORTH_APEX": (271.0, 20.0),
    "SOUTH_APEX": (273.0, -20.0),
    "NORTH_TOROIDAL": (270.0, 60.0),
    "SOUTH_TOROIDAL": (270.0, -60.0),
}


def finite(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def circ_diff(a: float, b: float) -> float:
    return (float(a) - float(b) + 180.0) % 360.0 - 180.0


def weighted_circular_mean(values: list[float], weights: list[float]) -> float:
    sine = sum(w * math.sin(math.radians(v)) for v, w in zip(values, weights))
    cosine = sum(w * math.cos(math.radians(v)) for v, w in zip(values, weights))
    return math.degrees(math.atan2(sine, cosine)) % 360.0


def spherical_sep(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    l1, b1, l2, b2 = map(math.radians, [lon1, lat1, lon2, lat2])
    cosine = math.sin(b1) * math.sin(b2) + math.cos(b1) * math.cos(b2) * math.cos(l1 - l2)
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def interval_distance(value: float, start: float | None, end: float | None, center: float | None) -> float:
    if start is not None and end is not None:
        span = (end - start) % 360.0
        if span <= 120.0:
            offset = (value - start) % 360.0
            if offset <= span:
                return 0.0
            return min(abs(circ_diff(value, start)), abs(circ_diff(value, end)))
    if center is not None:
        return abs(circ_diff(value, center))
    return 180.0


def status_number(value: Any) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def flatten_observations(mdc: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for shower in mdc.get("data", []):
        for solution in shower.get("solution", []) or []:
            rows.append({
                "iau_no": str(shower.get("IAUNo") or "").strip(),
                "code": str(shower.get("Code") or "").strip(),
                "name": str(shower.get("Name") or shower.get("ProvName") or "").strip(),
                "solution": str(solution.get("AdNo") or "").strip(),
                "status": str(solution.get("s") if solution.get("s") is not None else shower.get("s") or "").strip(),
                "LoSb": finite(solution.get("LoSb")),
                "LoSe": finite(solution.get("LoSe")),
                "LoS": finite(solution.get("LoS")),
                "S_LoR": finite(solution.get("S_LoR")),
                "LaR": finite(solution.get("LaR")),
                "Vg": finite(solution.get("Vg")),
            })
    return rows


def family_center(family: dict[str, Any]) -> dict[str, float]:
    counts: dict[int, int] = {}
    for event_id in map(str, family["event_ids"]):
        year = int(event_id[:4])
        counts[year] = counts.get(year, 0) + 1
    centroid_rows = []
    for year_text, centroid in family["centroids"].items():
        centroid_rows.append((centroid, float(counts.get(int(year_text), 1))))
    weights = [w for _c, w in centroid_rows]
    weight_sum = sum(weights)
    return {
        "sol": weighted_circular_mean([float(c["sol"]) for c, _w in centroid_rows], weights),
        "sun_lon": weighted_circular_mean([float(c["sun_lon"]) for c, _w in centroid_rows], weights),
        "ecl_lat": sum(float(c["ecl_lat"]) * w for c, w in centroid_rows) / weight_sum,
        "vg": sum(float(c["vg"]) * w for c, w in centroid_rows) / weight_sum,
    }


def observational_matches(center: dict[str, float], rows: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    assessed = []
    for row in rows:
        timing = interval_distance(center["sol"], row["LoSb"], row["LoSe"], row["LoS"])
        if None not in {row["S_LoR"], row["LaR"], row["Vg"]}:
            radiant = spherical_sep(center["sun_lon"], center["ecl_lat"], row["S_LoR"], row["LaR"])
            speed = abs(center["vg"] - row["Vg"])
            score = math.sqrt((timing / 12.0) ** 2 + (radiant / 10.0) ** 2 + (speed / 8.0) ** 2)
            close = timing <= 12.0 and radiant <= 10.0 and speed <= 8.0
        else:
            radiant = speed = score = None
            close = False
        item = dict(row)
        item.update({
            "timing_delta_deg": timing,
            "radiant_sep_deg": radiant,
            "speed_delta_km_s": speed,
            "obs_score": score,
            "observational_close": close,
            "active_status": (status_number(row["status"]) or 0) >= 0,
        })
        assessed.append(item)
    assessed.sort(key=lambda x: (
        not x["observational_close"],
        float("inf") if x["obs_score"] is None else x["obs_score"],
        x["timing_delta_deg"],
    ))
    return assessed[:limit]


def source_warning(center: dict[str, float]) -> dict[str, Any]:
    rows = [
        {"source": name, "separation_deg": spherical_sep(center["sun_lon"], center["ecl_lat"], lon, lat)}
        for name, (lon, lat) in SPORADIC_SOURCES.items()
    ]
    rows.sort(key=lambda x: x["separation_deg"])
    return {"within_25_deg": rows[0]["separation_deg"] <= 25.0, "nearest": rows[0], "all": rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan", type=Path, required=True)
    parser.add_argument("--mdc", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    opener = gzip.open if args.scan.suffix == ".gz" else open
    with opener(args.scan, "rt", encoding="utf-8") as handle:
        scan = json.load(handle)
    mdc = json.loads(args.mdc.read_text(encoding="utf-8"))
    obs_rows = flatten_observations(mdc)
    output_rows = []
    for family in scan["families"]:
        center = family_center(family)
        matches = observational_matches(center, obs_rows, limit=5)
        active_close = next((m for m in matches if m["active_status"] and m["observational_close"]), None)
        output_rows.append({
            "rank": int(family["locked_rrf_rank"]),
            "family_id": family["family_id"],
            "year_count": int(family["year_count"]),
            "event_count": int(family["event_count"]),
            "years": family["years"],
            "center": center,
            "eligible": int(family["year_count"]) >= 3 and int(family["event_count"]) >= 12,
            "active_observational_association": active_close,
            "no_active_observational_association": active_close is None,
            "nearest_mdc_observational": matches,
            "sporadic_source": source_warning(center),
            "ranking_scores": family.get("ranking_scores", {}),
        })
    queue = [r for r in output_rows if r["eligible"] and r["no_active_observational_association"]]
    queue.sort(key=lambda r: (-r["year_count"], -r["event_count"], r["rank"], r["family_id"]))
    for index, row in enumerate(queue, 1):
        row["queue_rank"] = index
    output = {
        "version": "raw-mirror-centroid-screen-v1",
        "mdc_version": mdc.get("version"),
        "mdc_shower_count": mdc.get("count"),
        "mdc_solution_rows_including_incomplete_orbits": len(obs_rows),
        "family_count": len(output_rows),
        "eligible_count": sum(r["eligible"] for r in output_rows),
        "queue_count": len(queue),
        "queue_ranks": [r["rank"] for r in queue],
        "queue_family_ids": [r["family_id"] for r in queue],
        "families": sorted(output_rows, key=lambda r: r["rank"]),
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "all_family_centroid_screen.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    lines = [
        "# All 766 frozen-family centroid screen",
        "",
        f"MDC {output['mdc_version']}; families {output['family_count']}; eligible {output['eligible_count']}; exact-adjudication queue {output['queue_count']}.",
        "",
        "| queue | frozen rank | family | years | N | λ☉ | SLoR | β | Vg | source | closest MDC |",
        "|---:|---:|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for index, row in enumerate(queue[:150], 1):
        c = row["center"]
        s = row["sporadic_source"]["nearest"]
        m = row["nearest_mdc_observational"][0] if row["nearest_mdc_observational"] else {}
        score = m.get("obs_score")
        mtxt = f"{m.get('iau_no','')}/{m.get('code','')} obs={'NA' if score is None else f'{score:.2f}'}" if m else "none"
        lines.append(f"| {index} | {row['rank']} | `{row['family_id']}` | {row['year_count']} | {row['event_count']} | {c['sol']:.2f} | {c['sun_lon']:.2f} | {c['ecl_lat']:.2f} | {c['vg']:.2f} | {s['source']} ({s['separation_deg']:.1f}°) | {mtxt} |")
    markdown = "\n".join(lines) + "\n"
    (args.out / "ALL_FAMILY_CENTROID_SCREEN.md").write_text(markdown)
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
