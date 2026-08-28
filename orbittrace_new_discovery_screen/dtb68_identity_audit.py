#!/usr/bin/env python3
"""Post-discovery current-MDC identity audit for DTb68bb6b678e43478."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import requests

MDC_URL = "https://ceresiaumdc.ta3.sk/downloads/lists_shw_data/streamfulldata.json"
SOL0 = 316.185573
SLON0 = 144.84784445604302
BETA0 = -53.00940285307881
VG0 = 14.934766201039407
ORBIT0 = np.asarray([0.601806, 0.947145, 17.518079, 26.456307, 136.215206], dtype=float)
MAX_PROPAGATION = 30.0
EXPLICIT = {"ECO", "FCM"}


def finite(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def first_finite(mapping: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        if key in mapping:
            value = finite(mapping.get(key))
            if value is not None:
                return value
    return None


def first_text(mapping: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = mapping.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def circ_diff(a: float | np.ndarray, b: float | np.ndarray) -> np.ndarray:
    return (np.asarray(a, dtype=float) - np.asarray(b, dtype=float) + 180.0) % 360.0 - 180.0


def spherical_sep(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    l1, b1, l2, b2 = map(math.radians, [lon1, lat1, lon2, lat2])
    c = math.sin(b1) * math.sin(b2) + math.cos(b1) * math.cos(b2) * math.cos(l1 - l2)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def equatorial_to_ecliptic(ra_deg: float, dec_deg: float) -> tuple[float, float]:
    ra = math.radians(ra_deg % 360.0)
    dec = math.radians(dec_deg)
    eps = math.radians(23.43928)
    x = math.cos(dec) * math.cos(ra)
    y = math.cos(dec) * math.sin(ra)
    z = math.sin(dec)
    xe = x
    ye = y * math.cos(eps) + z * math.sin(eps)
    ze = -y * math.sin(eps) + z * math.cos(eps)
    return math.degrees(math.atan2(ye, xe)) % 360.0, math.degrees(math.asin(max(-1.0, min(1.0, ze))))


def d_sh(one: np.ndarray, two: np.ndarray) -> float:
    e1, q1, i1d, p1d, n1d = map(float, one)
    e2, q2, i2d, p2d, n2d = map(float, two)
    i1, i2 = math.radians(i1d), math.radians(i2d)
    dn = math.radians(float(circ_diff(n1d, n2d)))
    ci = max(-1.0, min(1.0, math.cos(i1)*math.cos(i2) + math.sin(i1)*math.sin(i2)*math.cos(dn)))
    plane = math.acos(ci)
    denom = max(math.cos(plane/2.0), np.finfo(float).eps)
    common = math.cos((i1+i2)/2.0) * math.sin(dn/2.0) / denom
    dpi = math.radians(p1d-p2d) + 2.0 * math.asin(max(-1.0, min(1.0, common)))
    dpi = (dpi + math.pi) % (2.0*math.pi) - math.pi
    em = (e1+e2)/2.0
    d2 = (e1-e2)**2 + (q1-q2)**2 + (2.0*math.sin(plane/2.0))**2 + (em*2.0*math.sin(dpi/2.0))**2
    return math.sqrt(max(0.0, d2))


def interval_distance(value: float, start: float | None, end: float | None, center: float | None) -> float | None:
    if start is not None and end is not None:
        span = (end - start) % 360.0
        if span <= 120.0:
            offset = (value - start) % 360.0
            if offset <= span:
                return 0.0
            return min(abs(float(circ_diff(value, start))), abs(float(circ_diff(value, end))))
    if center is not None:
        return abs(float(circ_diff(value, center)))
    return None


def flatten(doc: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for shower in doc.get("data", []):
        code = first_text(shower, "Code", "code").upper()
        for solution in shower.get("solution", []) or []:
            item = dict(shower)
            item.pop("solution", None)
            item.update(solution)
            item["_code"] = code
            item["_iau_no"] = first_text(shower, "IAUNo", "IAU_No", "iau_no")
            item["_name"] = first_text(shower, "Name", "ProvName", "name")
            item["_status"] = first_text(solution, "s", "status") or first_text(shower, "s", "status")
            out.append(item)
    return out


def assess(row: dict[str, Any]) -> dict[str, Any]:
    code = row["_code"]
    los = first_finite(row, "LoS", "los")
    losb = first_finite(row, "LoSb", "losb")
    lose = first_finite(row, "LoSe", "lose")
    timing = interval_distance(SOL0, losb, lose, los)

    slon = first_finite(row, "S_LoR", "SLoR", "s_lor")
    beta = first_finite(row, "LaR", "beta", "la_r")
    static_sep = spherical_sep(SLON0, BETA0, slon % 360.0, beta) if slon is not None and beta is not None else None

    ra = first_finite(row, "RA", "Ra", "ra")
    dec = first_finite(row, "De", "DE", "Dec", "dec")
    dra = first_finite(row, "dRa", "dRA", "DRA", "dra")
    ddec = first_finite(row, "dDe", "dDE", "dDec", "DDE", "ddec")
    prop: dict[str, Any] | None = None
    if los is not None and ra is not None and dec is not None and (dra is not None or ddec is not None):
        delta = float(circ_diff(SOL0, los))
        if abs(delta) <= MAX_PROPAGATION:
            pra = (ra + (0.0 if dra is None else dra) * delta) % 360.0
            pdec = dec + (0.0 if ddec is None else ddec) * delta
            if -90.0 <= pdec <= 90.0:
                elon, elat = equatorial_to_ecliptic(pra, pdec)
                pslon = float(circ_diff(elon, SOL0)) % 360.0
                psep = spherical_sep(SLON0, BETA0, pslon, elat)
                prop = {
                    "delta_sol_deg": delta,
                    "ra_deg": pra,
                    "dec_deg": pdec,
                    "slon_deg": pslon,
                    "beta_deg": elat,
                    "radiant_sep_deg": psep,
                    "used_dra_deg_per_deg": 0.0 if dra is None else dra,
                    "used_ddec_deg_per_deg": 0.0 if ddec is None else ddec,
                }

    chosen_sep = prop["radiant_sep_deg"] if prop is not None else static_sep
    vg = first_finite(row, "Vg", "vg")
    speed = abs(VG0 - vg) if vg is not None else None
    score = None
    if timing is not None and chosen_sep is not None and speed is not None:
        score = math.sqrt((timing/20.0)**2 + (chosen_sep/8.0)**2 + (speed/5.0)**2)

    orbit_keys = (("e", "e"), ("q", "q"), ("incl", "i"), ("peri", "omega"), ("node", "Omega"))
    vals: list[float | None] = []
    diffs: dict[str, float | None] = {}
    for idx, (key, label) in enumerate(orbit_keys):
        value = first_finite(row, key)
        vals.append(value)
        if value is None:
            diffs[label] = None
        elif key in {"peri", "node"}:
            diffs[label] = abs(float(circ_diff(value, ORBIT0[idx])))
        else:
            diffs[label] = abs(value - float(ORBIT0[idx]))
    dsh = d_sh(ORBIT0, np.asarray(vals, dtype=float)) if all(value is not None for value in vals) else None

    return {
        "iau_no": row["_iau_no"],
        "code": code,
        "name": row["_name"],
        "solution": first_text(row, "AdNo", "adno"),
        "status": row["_status"],
        "members_catalog": first_finite(row, "N", "n"),
        "reference": first_text(row, "Ref", "Reference", "reference"),
        "remarks": first_text(row, "Remarks", "Remark", "remarks"),
        "catalog": {
            "LoSb": losb, "LoSe": lose, "LoS": los, "RA": ra, "De": dec,
            "dRa": dra, "dDe": ddec, "S_LoR": slon, "LaR": beta, "Vg": vg,
            "e": vals[0], "q": vals[1], "incl": vals[2], "peri": vals[3], "node": vals[4],
        },
        "timing_distance_deg": timing,
        "static_radiant_sep_deg": static_sep,
        "propagated": prop,
        "chosen_radiant_sep_deg": chosen_sep,
        "speed_delta_km_s": speed,
        "identity_diagnostic_score": score,
        "d_sh_if_complete": dsh,
        "orbit_component_abs_differences": diffs,
    }


def sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    score = row["identity_diagnostic_score"]
    sep = row["chosen_radiant_sep_deg"]
    speed = row["speed_delta_km_s"]
    timing = row["timing_distance_deg"]
    return (
        float("inf") if score is None else score,
        float("inf") if sep is None else sep,
        float("inf") if speed is None else speed,
        float("inf") if timing is None else timing,
        row["code"], row["solution"],
    )


def main() -> int:
    out = Path("identity_output")
    out.mkdir(parents=True, exist_ok=True)
    response = requests.get(MDC_URL, timeout=120)
    response.raise_for_status()
    document = response.json()
    assessed = [assess(row) for row in flatten(document)]
    assessed.sort(key=sort_key)
    explicit = [row for row in assessed if row["code"] in EXPLICIT]
    payload = {
        "stage": "dtb68_post_discovery_identity_audit_v1",
        "protocol": "orbittrace-raw/pipeline/discovery_search/DTB68_IDENTITY_AUDIT_PROTOCOL.md",
        "frozen_lead": "DTb68bb6b678e43478",
        "mdc_version": document.get("version"),
        "mdc_shower_count": document.get("count"),
        "solution_rows": len(assessed),
        "candidate": {"sol": SOL0, "slon": SLON0, "beta": BETA0, "vg": VG0, "orbit": ORBIT0.tolist()},
        "top_30": assessed[:30],
        "explicit_ECO_FCM": explicit,
    }
    (out / "dtb68_identity_audit.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# DTb68 post-discovery current-MDC identity audit", "",
        f"MDC version: **{document.get('version')}**. Submitted solution rows: **{len(assessed)}**.", "",
        "The score is diagnostic only. Propagated catalogue radiants use published dRA/dDec without fitting DTb68.", "",
        "| rank | shower | status | timing | radiant | dVg | score | D_SH | representation |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for rank, row in enumerate(assessed[:30], 1):
        rep = "propagated" if row["propagated"] is not None else "static"
        fnum = lambda x, n=2: "—" if x is None else f"{x:.{n}f}"
        lines.append(
            f"| {rank} | {row['iau_no']}/{row['code']} {row['name']} | {row['status']} | "
            f"{fnum(row['timing_distance_deg'])} | {fnum(row['chosen_radiant_sep_deg'])} | "
            f"{fnum(row['speed_delta_km_s'])} | {fnum(row['identity_diagnostic_score'],3)} | "
            f"{fnum(row['d_sh_if_complete'],3)} | {rep} |"
        )
    lines += ["", "## Required explicit comparators", ""]
    for row in explicit:
        lines += [
            f"### {row['iau_no']}/{row['code']} {row['name']} solution {row['solution']}", "",
            f"- status: `{row['status']}`; catalogue N: `{row['members_catalog']}`",
            f"- timing distance: `{row['timing_distance_deg']}` deg",
            f"- static radiant separation: `{row['static_radiant_sep_deg']}` deg",
            f"- propagated representation: `{row['propagated']}`",
            f"- speed difference: `{row['speed_delta_km_s']}` km/s",
            f"- diagnostic score: `{row['identity_diagnostic_score']}`",
            f"- D_SH if complete: `{row['d_sh_if_complete']}`",
            f"- orbit-component absolute differences: `{row['orbit_component_abs_differences']}`",
            f"- remarks: {row['remarks'] or '—'}", "",
        ]
    md = "\n".join(lines) + "\n"
    (out / "DTB68_IDENTITY_AUDIT.md").write_text(md, encoding="utf-8")
    print(md, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
