#!/usr/bin/env python3
"""Conservative known-shower association screen for the frozen locked-RRF catalogue.

This is not a duplicate classifier. It is deliberately broader: its job is to
prevent a recurrent GMN cluster from being called novel merely because it misses
a strict orbit/radiant duplicate threshold. XLI is used only as a positive
association-control after the candidate catalogue itself was already frozen.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
from pathlib import Path
from typing import Any


def circ_diff(a: float, b: float) -> float:
    return (float(a) - float(b) + 180.0) % 360.0 - 180.0


def circ_mean(values: list[float]) -> float:
    if not values:
        raise ValueError("empty circular mean")
    s = sum(math.sin(math.radians(v)) for v in values) / len(values)
    c = sum(math.cos(math.radians(v)) for v in values) / len(values)
    return math.degrees(math.atan2(s, c)) % 360.0


def spherical_sep_deg(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    a1, b1, a2, b2 = map(math.radians, [lon1, lat1, lon2, lat2])
    cosine = math.sin(b1) * math.sin(b2) + math.cos(b1) * math.cos(b2) * math.cos(a1 - a2)
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def source_region(lon: float, beta: float, speed: float) -> str | None:
    lon %= 360.0
    if abs(circ_diff(lon, 180.0)) <= 30.0 and abs(beta) <= 25.0 and speed < 40.0:
        return "ANTIHELION"
    if abs(circ_diff(lon, 0.0)) <= 30.0 and abs(beta) <= 25.0 and speed < 40.0:
        return "HELION"
    if abs(circ_diff(lon, 270.0)) <= 40.0 and abs(beta) <= 35.0 and speed >= 40.0:
        return "APEX"
    if abs(circ_diff(lon, 270.0)) <= 50.0 and abs(beta) > 30.0 and speed >= 35.0:
        return "TOROIDAL"
    return None


def finite(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def interval_distance(value: float, start: float | None, end: float | None, center: float | None) -> tuple[float, bool]:
    """Circular solar-longitude distance to a reported activity interval/center."""
    if start is not None and end is not None:
        span = (end - start) % 360.0
        offset = (value - start) % 360.0
        if offset <= span:
            return 0.0, True
        return min(abs(circ_diff(value, start)), abs(circ_diff(value, end))), False
    if center is not None:
        return abs(circ_diff(value, center)), False
    return 180.0, False


def family_summary(family: dict[str, Any]) -> dict[str, Any]:
    centroids = list(family["centroids"].values())
    sol = circ_mean([float(c["sol"]) for c in centroids])
    slon = circ_mean([float(c["sun_lon"]) for c in centroids])
    beta = sum(float(c["ecl_lat"]) for c in centroids) / len(centroids)
    vg = sum(float(c["vg"]) for c in centroids) / len(centroids)
    max_dsol = max(abs(circ_diff(float(c["sol"]), sol)) for c in centroids)
    max_dslon = max(abs(circ_diff(float(c["sun_lon"]), slon)) for c in centroids)
    max_dbeta = max(abs(float(c["ecl_lat"]) - beta) for c in centroids)
    max_dvg = max(abs(float(c["vg"]) - vg) for c in centroids)
    coherence = max(max_dsol / 5.0, max_dslon / 4.0, max_dbeta / 4.0, max_dvg / 3.0)
    return {
        "family_id": family["family_id"],
        "locked_rrf_rank": int(family["locked_rrf_rank"]),
        "year_count": int(family["year_count"]),
        "years": family["years"],
        "event_count": int(family["event_count"]),
        "sol": sol,
        "sun_lon": slon,
        "ecl_lat": beta,
        "vg": vg,
        "max_year_scatter": {
            "sol": max_dsol,
            "sun_lon": max_dslon,
            "ecl_lat": max_dbeta,
            "vg": max_dvg,
            "normalized": coherence,
        },
        "sporadic_source_region": source_region(slon, beta, vg),
    }


def flatten_mdc(document: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for shower in document.get("data", []):
        for solution in shower.get("solution", []) or []:
            los = finite(solution.get("LoS"))
            slor = finite(solution.get("S_LoR"))
            lar = finite(solution.get("LaR"))
            vg = finite(solution.get("Vg"))
            if None in {los, slor, lar, vg}:
                continue
            out.append({
                "iau_no": str(shower.get("IAUNo") or "").strip(),
                "code": str(shower.get("Code") or "").strip(),
                "name": str(shower.get("Name") or shower.get("ProvName") or "").strip(),
                "adno": str(solution.get("AdNo") or "").strip(),
                "status": str(solution.get("s") if solution.get("s") is not None else shower.get("s") or "").strip(),
                "activity": str(solution.get("activity") or "").strip(),
                "LoSb": finite(solution.get("LoSb")),
                "LoSe": finite(solution.get("LoSe")),
                "LoS": los,
                "S_LoR": slor,
                "LaR": lar,
                "Vg": vg,
                "N": finite(solution.get("N")),
                "references": solution.get("References") or [],
            })
    return out


def association(candidate: dict[str, Any], solution: dict[str, Any]) -> dict[str, Any]:
    timing, inside = interval_distance(candidate["sol"], solution["LoSb"], solution["LoSe"], solution["LoS"])
    radiant = spherical_sep_deg(candidate["sun_lon"], candidate["ecl_lat"], solution["S_LoR"], solution["LaR"])
    dv = abs(candidate["vg"] - solution["Vg"])

    # Deliberately broader than a duplicate screen. This is a novelty-veto triage.
    if timing <= 8.0 and radiant <= 6.0 and dv <= 5.0:
        tier = "STRONG"
    elif timing <= 15.0 and radiant <= 10.0 and dv <= 8.0:
        tier = "PLAUSIBLE"
    elif timing <= 25.0 and radiant <= 15.0 and dv <= 12.0:
        tier = "LOOSE"
    else:
        tier = "NONE"
    score = math.sqrt((timing / 15.0) ** 2 + (radiant / 10.0) ** 2 + (dv / 8.0) ** 2)
    return {
        "tier": tier,
        "score": score,
        "timing_delta_deg": timing,
        "inside_reported_activity_interval": inside,
        "radiant_sep_deg": radiant,
        "speed_delta_km_s": dv,
        **solution,
    }


def best_associations(candidate: dict[str, Any], solutions: list[dict[str, Any]], k: int = 10) -> list[dict[str, Any]]:
    matches = [association(candidate, solution) for solution in solutions]
    matches.sort(key=lambda x: (x["score"], x["radiant_sep_deg"], x["speed_delta_km_s"], x["timing_delta_deg"]))
    return matches[:k]


def tier_rank(tier: str) -> int:
    return {"NONE": 0, "LOOSE": 1, "PLAUSIBLE": 2, "STRONG": 3}[tier]


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# OrbitTrace new-discovery association screen",
        "",
        f"IAU MDC snapshot: **{result['mdc_version']}**; {result['mdc_solution_count']:,} usable mean solutions.",
        "",
        "This is a broad known-association veto, not a duplicate classifier. It intentionally errs toward flagging possible known showers before novelty claims.",
        "",
        f"XLI positive control: **{result['xli_positive_control']['verdict']}**.",
        "",
        "## Current shortlist",
        "",
        "Candidates below are recurrent in at least 3 years, outside the broad sporadic-source boxes, compact across yearly centroids, have 12-200 members, and have no STRONG/PLAUSIBLE IAU association under the frozen broad screen.",
        "",
        "| RRF rank | family | years | events | λ☉ | SLoR | β | Vg | nearest IAU | tier | Δλ☉ | radiant | ΔVg |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---|---|---:|---:|---:|",
    ]
    for c in result["shortlist"]:
        b = c["best_associations"][0]
        label = "/".join(x for x in [b.get("iau_no"), b.get("code")] if x and x != "-") or b.get("name") or "unknown"
        lines.append(
            f"| {c['locked_rrf_rank']} | `{c['family_id']}` | {c['year_count']} | {c['event_count']} | "
            f"{c['sol']:.1f} | {c['sun_lon']:.1f} | {c['ecl_lat']:.1f} | {c['vg']:.1f} | "
            f"{label} | {b['tier']} | {b['timing_delta_deg']:.1f} | {b['radiant_sep_deg']:.1f}° | {b['speed_delta_km_s']:.1f} |"
        )
    lines += ["", "## XLI control detail", ""]
    x = result["xli_positive_control"]
    lines.append(f"Locked-RRF rank 46 family: `{x['family_id']}`. Best XLI solution tier: **{x['best_xli']['tier']}**; Δλ☉={x['best_xli']['timing_delta_deg']:.2f}°, radiant={x['best_xli']['radiant_sep_deg']:.2f}°, ΔVg={x['best_xli']['speed_delta_km_s']:.2f} km/s.")
    lines += ["", "## Interpretation", "", "A shortlist entry is only a candidate for deeper adjudication. It still needs orbit-level comparison, local-background tests, per-year activity/radiant drift fits, and independent-network checking before it can be described as an uncatalogued shower."]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan", required=True)
    parser.add_argument("--mdc", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    scan_path = Path(args.scan)
    opener = gzip.open if scan_path.suffix == ".gz" else open
    with opener(scan_path, "rt", encoding="utf-8") as handle:
        scan = json.load(handle)
    mdc = json.loads(Path(args.mdc).read_text(encoding="utf-8"))
    solutions = flatten_mdc(mdc)

    families = {f["family_id"]: f for f in scan["families"]}
    order = scan["rankings"]["locked_rrf"]
    screened: list[dict[str, Any]] = []
    for expected_rank, family_id in enumerate(order, start=1):
        summary = family_summary(families[family_id])
        if summary["locked_rrf_rank"] != expected_rank:
            raise RuntimeError(f"rank mismatch for {family_id}: {summary['locked_rrf_rank']} != {expected_rank}")
        best = best_associations(summary, solutions)
        summary["best_associations"] = best
        summary["best_association_tier"] = max((x["tier"] for x in best), key=tier_rank)
        screened.append(summary)

    # Positive control: rank 46 is the already-revealed OrbitTrace/XLI family.
    control = screened[45]
    xli = [association(control, s) for s in solutions if s["code"].upper() == "XLI" or s["iau_no"].lstrip("0") == "140"]
    if not xli:
        raise RuntimeError("XLI / IAU 140 absent from current MDC snapshot")
    xli.sort(key=lambda x: x["score"])
    best_xli = xli[0]
    control_verdict = "PASS" if tier_rank(best_xli["tier"]) >= tier_rank("PLAUSIBLE") else "FAIL"

    shortlist = []
    for candidate in screened:
        if candidate["year_count"] < 3:
            continue
        if not 12 <= candidate["event_count"] <= 200:
            continue
        if candidate["sporadic_source_region"] is not None:
            continue
        if candidate["max_year_scatter"]["normalized"] > 2.0:
            continue
        if any(tier_rank(m["tier"]) >= tier_rank("PLAUSIBLE") for m in candidate["best_associations"]):
            continue
        shortlist.append(candidate)

    result = {
        "screen_version": "2026-08-28-v1",
        "screen_role": "broad known-association novelty veto; not duplicate classification",
        "mdc_version": str(mdc.get("version") or "unknown"),
        "mdc_shower_count": int(mdc.get("count") or 0),
        "mdc_solution_count": len(solutions),
        "locked_rrf_family_count": len(screened),
        "association_tiers": {
            "STRONG": {"timing_deg": 8, "radiant_deg": 6, "speed_km_s": 5},
            "PLAUSIBLE": {"timing_deg": 15, "radiant_deg": 10, "speed_km_s": 8},
            "LOOSE": {"timing_deg": 25, "radiant_deg": 15, "speed_km_s": 12},
        },
        "xli_positive_control": {
            "family_id": control["family_id"],
            "locked_rrf_rank": control["locked_rrf_rank"],
            "verdict": control_verdict,
            "best_xli": best_xli,
        },
        "shortlist_count": len(shortlist),
        "shortlist": shortlist,
        "all_screened": screened,
    }

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "KNOWN_ASSOCIATION_SCREEN.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "KNOWN_ASSOCIATION_SCREEN.md").write_text(render_markdown(result), encoding="utf-8")
    print(json.dumps({
        "mdc_version": result["mdc_version"],
        "mdc_solution_count": result["mdc_solution_count"],
        "xli_positive_control": control_verdict,
        "shortlist_count": len(shortlist),
        "shortlist_ranks": [x["locked_rrf_rank"] for x in shortlist],
    }, indent=2))
    if control_verdict != "PASS":
        raise SystemExit("XLI positive control failed; do not use shortlist")


if __name__ == "__main__":
    main()
