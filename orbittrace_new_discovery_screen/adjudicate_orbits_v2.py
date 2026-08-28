#!/usr/bin/env python3
"""Corrected orbit adjudication wrapper for locked-RRF discovery leads.

This wrapper deliberately reuses the frozen-candidate plumbing in
``adjudicate_orbits.py`` while correcting two post-selection diagnostics:

1. Southworth-Hawkins D_SH is evaluated with the published Pi angle measured
   from the intersection of the two orbital planes, not the ordinary 3-D angle
   between perihelion direction vectors.
2. GMN ``iau_code`` values are three-letter shower codes. They are mapped back
   to IAU numbers through the current MDC before empirical-label comparisons.

No detector, candidate membership, ranking, or reveal rule is changed.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from orbittrace_new_discovery_screen import adjudicate_orbits as impl

CODE_TO_IAU: dict[str, int] = {}


def canonical_d_sh_matrix(a: np.ndarray, b: np.ndarray | None = None) -> np.ndarray:
    """Published Southworth-Hawkins D_SH, vectorized over two orbit arrays."""
    a = np.asarray(a, dtype=float)
    b = a if b is None else np.asarray(b, dtype=float)

    e1, q1 = a[:, 0][:, None], a[:, 1][:, None]
    e2, q2 = b[:, 0][None, :], b[:, 1][None, :]
    i1 = np.deg2rad(a[:, 2])[:, None]
    w1 = np.deg2rad(a[:, 3])[:, None]
    o1_deg = a[:, 4][:, None]
    i2 = np.deg2rad(b[:, 2])[None, :]
    w2 = np.deg2rad(b[:, 3])[None, :]
    o2_deg = b[:, 4][None, :]

    # Wrapping delta-Omega into [-180, 180) is equivalent to the published
    # plus/minus branch for node differences below/above 180 degrees.
    do_deg = (o2_deg - o1_deg + 180.0) % 360.0 - 180.0
    do = np.deg2rad(do_deg)

    cos_i = np.clip(
        np.cos(i1) * np.cos(i2) + np.sin(i1) * np.sin(i2) * np.cos(do),
        -1.0,
        1.0,
    )
    plane = np.arccos(cos_i)
    cos_half_plane = np.cos(plane / 2.0)
    safe_den = np.where(np.abs(cos_half_plane) < 1e-15, 1e-15, cos_half_plane)
    asin_arg = (
        np.cos((i1 + i2) / 2.0)
        * np.sin(do / 2.0)
        / safe_den
    )
    pi_angle = w2 - w1 + 2.0 * np.arcsin(np.clip(asin_arg, -1.0, 1.0))

    d2 = (
        (e1 - e2) ** 2
        + (q1 - q2) ** 2
        + (2.0 * np.sin(plane / 2.0)) ** 2
        + (((e1 + e2) / 2.0) * 2.0 * np.sin(pi_angle / 2.0)) ** 2
    )
    return np.sqrt(np.maximum(d2, 0.0))


def normalize_iau_number_or_code(value: Any) -> int | None:
    """Resolve either an MDC numeric identifier or a GMN three-letter code."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    text = str(value).strip().upper()
    if not text:
        return None
    if text in CODE_TO_IAU:
        return CODE_TO_IAU[text]
    if text.endswith(".0"):
        text = text[:-2]
    try:
        return int(text)
    except ValueError:
        return None


def raw_code_counts(frame: pd.DataFrame) -> dict[str, int]:
    counts = Counter()
    for value in frame["iau_code"].tolist():
        text = "" if value is None else str(value).strip().upper()
        counts[text or "<EMPTY>"] += 1
    return dict(counts.most_common())


def angular_sep_array(lon: np.ndarray, lat: np.ndarray, lon0: float, lat0: float) -> np.ndarray:
    l1 = np.deg2rad(np.asarray(lon, dtype=float))
    b1 = np.deg2rad(np.asarray(lat, dtype=float))
    l0, b0 = math.radians(lon0), math.radians(lat0)
    cosine = np.sin(b1) * math.sin(b0) + np.cos(b1) * math.cos(b0) * np.cos(l1 - l0)
    return np.rad2deg(np.arccos(np.clip(cosine, -1.0, 1.0)))


def local_template_diagnostic(
    candidate: dict[str, Any],
    family: dict[str, Any],
    all_months: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    """Descriptive fixed-scale recurrence/sideband diagnostic, not a p-value.

    The observational template uses the original physical feature scales
    (3.5 deg SLoR, 3 deg beta, 2.5 km/s Vg, 2.5 deg solar longitude) and a
    unit standardized radius. Solar-longitude analogue centers at +/- 7.5,
    12.5, 17.5, and 22.5 degrees give a same-month background comparison.
    Because the candidate was selected from these data, this is explicitly
    descriptive and is not treated as selection-adjusted significance.
    """
    center = candidate["observational_center"]
    family_ids = set(map(str, family["event_ids"]))
    months = sorted({event_id[4:6] for event_id in family_ids})
    if len(months) != 1:
        return {"status": "SKIPPED_MULTIMONTH", "months": months}
    month = months[0]

    offsets = [-22.5, -17.5, -12.5, -7.5, 7.5, 12.5, 17.5, 22.5]
    by_year: dict[str, Any] = {}
    candidate_total = 0
    analogue_totals = np.zeros(len(offsets), dtype=int)

    for year in range(2022, 2027):
        key = f"{year}-{month}"
        if key not in all_months:
            continue
        frame = all_months[key]
        qmask = impl.quality_mask(frame)
        frame = frame.loc[qmask].copy().reset_index(drop=True)
        sol = frame["sol_lon_deg"].to_numpy(float)
        slon = impl.circ_diff(frame["lamgeo_deg"].to_numpy(float), sol)
        beta = frame["betgeo_deg"].to_numpy(float)
        vg = frame["vgeo_km_s"].to_numpy(float)

        # Match the scan's residual philosophy using current-MDC code knowledge:
        # any recognized shower code is excluded; unrecognized/empty codes remain.
        residual = np.asarray([
            normalize_iau_number_or_code(v) is None
            for v in frame["iau_code"].tolist()
        ], dtype=bool)

        spatial2 = (
            (impl.circ_diff(slon, center["sun_lon"]) / 3.5) ** 2
            + ((beta - center["ecl_lat"]) / 3.0) ** 2
            + ((vg - center["vg"]) / 2.5) ** 2
        )
        target_d2 = spatial2 + (impl.circ_diff(sol, center["sol"]) / 2.5) ** 2
        target = residual & (target_d2 <= 1.0)
        target_count = int(target.sum())
        candidate_total += target_count

        analogue_counts = []
        for j, offset in enumerate(offsets):
            analogue_d2 = spatial2 + (impl.circ_diff(sol, (center["sol"] + offset) % 360.0) / 2.5) ** 2
            count = int((residual & (analogue_d2 <= 1.0)).sum())
            analogue_counts.append(count)
            analogue_totals[j] += count

        exact_family_here = int(frame[impl.ID_COLUMN].astype(str).isin(family_ids).sum())
        by_year[str(year)] = {
            "target_template_residual_count": target_count,
            "exact_frozen_family_count": exact_family_here,
            "analogue_counts": analogue_counts,
            "raw_iau_code_counts_in_month": raw_code_counts(frame),
        }

    median_analogue = float(np.median(analogue_totals)) if len(analogue_totals) else 0.0
    return {
        "status": "DESCRIPTIVE_ONLY_NOT_SELECTION_ADJUSTED",
        "month": month,
        "feature_scales": {"sun_lon": 3.5, "ecl_lat": 3.0, "vg": 2.5, "sol": 2.5},
        "template_radius": 1.0,
        "solar_analogue_offsets_deg": offsets,
        "by_year": by_year,
        "target_total": int(candidate_total),
        "analogue_totals": analogue_totals.tolist(),
        "analogue_median": median_analogue,
        "target_to_analogue_median_ratio": (
            float(candidate_total / median_analogue) if median_analogue > 0 else None
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan", required=True)
    parser.add_argument("--mdc", required=True)
    parser.add_argument("--ranks", nargs="+", type=int, default=[95, 102, 105])
    parser.add_argument("--scan-zip-sha256", default="unknown")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    scan_path = Path(args.scan)
    opener = gzip.open if scan_path.suffix == ".gz" else open
    with opener(scan_path, "rt", encoding="utf-8") as handle:
        scan = json.load(handle)
    mdc = json.loads(Path(args.mdc).read_text(encoding="utf-8"))
    solutions = impl.flatten_mdc(mdc)

    # Build an unambiguous code -> IAU number map. Every current MDC code used
    # for a shower is expected to identify one shower number.
    code_numbers: dict[str, set[int]] = {}
    for s in solutions:
        code = str(s.get("code") or "").strip().upper()
        number = impl.normalize_iau_number(s.get("iau_no"))
        if code and number is not None:
            code_numbers.setdefault(code, set()).add(number)
    ambiguous = {code: sorted(nums) for code, nums in code_numbers.items() if len(nums) != 1}
    global CODE_TO_IAU
    CODE_TO_IAU = {code: next(iter(nums)) for code, nums in code_numbers.items() if len(nums) == 1}

    # Correct only post-selection diagnostic functions in the imported module.
    impl.d_sh_matrix = canonical_d_sh_matrix
    impl.normalize_iau_number = normalize_iau_number_or_code

    families_by_id = {f["family_id"]: f for f in scan["families"]}

    # Load the full matching calendar month for every 2022-2025 year and for
    # 2026 when that month is within the Jan-Jul locked scan corpus. This lets
    # us inspect recurrence even in a year not represented in the frozen family.
    month_keys: set[str] = set()
    candidate_family_ids: dict[int, str] = {}
    for rank in args.ranks:
        family_id = scan["rankings"]["locked_rrf"][rank - 1]
        candidate_family_ids[rank] = family_id
        family = families_by_id[family_id]
        months = {event_id[4:6] for event_id in map(str, family["event_ids"])}
        for month in months:
            for year in range(2022, 2026):
                month_keys.add(f"{year}-{month}")
            if int(month) <= 7:
                month_keys.add(f"2026-{month}")
    all_months = {key: impl.read_month(key) for key in sorted(month_keys)}

    candidates = []
    for rank in args.ranks:
        result = impl.candidate_adjudication(rank, scan, all_months, solutions)
        family = families_by_id[candidate_family_ids[rank]]

        # Raw labels of the exact frozen members are useful because the locked
        # scanner itself operated on GMN rows labelled as residual/sporadic.
        ids = set(map(str, family["event_ids"]))
        member_parts = [
            frame[frame[impl.ID_COLUMN].astype(str).isin(ids)]
            for frame in all_months.values()
        ]
        members = pd.concat(member_parts, ignore_index=True) if member_parts else pd.DataFrame()
        result["exact_frozen_member_iau_code_counts"] = raw_code_counts(members) if len(members) else {}
        result["local_template_diagnostic"] = local_template_diagnostic(result, family, all_months)
        candidates.append(result)

    output = {
        "version": "2026-08-28-v2-corrected-dsh-and-gmn-codes",
        "corrections": {
            "d_sh": "published Southworth-Hawkins Pi-angle formula",
            "gmn_iau_code": "three-letter code mapped through current MDC",
        },
        "mdc_version": str(mdc.get("version") or "unknown"),
        "complete_mdc_solution_count": len(solutions),
        "mdc_code_map_size": len(CODE_TO_IAU),
        "ambiguous_mdc_codes": ambiguous,
        "scan_zip_sha256": args.scan_zip_sha256,
        "ranks": args.ranks,
        "candidates": candidates,
    }

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "ORBIT_ADJUDICATION_V2.json").write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    md = impl.render(output)
    extra = ["", "## Corrected-diagnostic addendum", ""]
    for c in candidates:
        e = c["empirical_gmn_comparison"]
        t = c["local_template_diagnostic"]
        extra.append(
            f"- Rank {c['rank']}: exact frozen-member GMN codes {c['exact_frozen_member_iau_code_counts']}; "
            f"empirical {e.get('code')} labeled count {e.get('local_labeled_count', 0)}; "
            f"fixed-template residual total {t.get('target_total')} vs analogue totals {t.get('analogue_totals')}."
        )
    md += "\n".join(extra) + "\n"
    (out / "ORBIT_ADJUDICATION_V2.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
