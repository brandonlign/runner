#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import theilslopes

SEED = 20260804
NOP_SOLUTION = np.array([0.932, 0.207, 16.7, 310.5, 58.6], dtype=float)
THRESHOLDS = (0.05, 0.10, 0.15, 0.20)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def circ_diff(value, center):
    return (np.asarray(value) - np.asarray(center) + 180.0) % 360.0 - 180.0


def angular_sep(lon1, lat1, lon2, lat2):
    a, b, c, d = map(np.deg2rad, [lon1, lat1, lon2, lat2])
    cosine = np.sin(b) * np.sin(d) + np.cos(b) * np.cos(d) * np.cos(a - c)
    return np.rad2deg(np.arccos(np.clip(cosine, -1.0, 1.0)))


def perihelion_vector(orbits: np.ndarray) -> np.ndarray:
    inc = np.deg2rad(orbits[:, 2])
    arg = np.deg2rad(orbits[:, 3])
    node = np.deg2rad(orbits[:, 4])
    return np.column_stack([
        np.cos(node) * np.cos(arg) - np.sin(node) * np.sin(arg) * np.cos(inc),
        np.sin(node) * np.cos(arg) + np.cos(node) * np.sin(arg) * np.cos(inc),
        np.sin(arg) * np.sin(inc),
    ])


def orbit_distance_matrix(a: np.ndarray, b: np.ndarray | None = None) -> np.ndarray:
    a = np.asarray(a, dtype=float)
    b = a if b is None else np.asarray(b, dtype=float)
    e1, q1 = a[:, 0][:, None], a[:, 1][:, None]
    e2, q2 = b[:, 0][None, :], b[:, 1][None, :]
    i1, n1 = np.deg2rad(a[:, 2])[:, None], np.deg2rad(a[:, 4])[:, None]
    i2, n2 = np.deg2rad(b[:, 2])[None, :], np.deg2rad(b[:, 4])[None, :]
    plane = np.arccos(np.clip(
        np.cos(i1) * np.cos(i2) + np.sin(i1) * np.sin(i2) * np.cos(n1 - n2), -1, 1
    ))
    p1, p2 = perihelion_vector(a), perihelion_vector(b)
    peri = np.arccos(np.clip(p1 @ p2.T, -1, 1))
    d2 = (
        (e1 - e2) ** 2 + (q1 - q2) ** 2 + (2 * np.sin(plane / 2)) ** 2
        + (((e1 + e2) / 2) * 2 * np.sin(peri / 2)) ** 2
    )
    return np.sqrt(np.maximum(d2, 0.0))


def pct(values) -> dict[str, float]:
    quantiles = [0, 10, 25, 50, 75, 90, 95, 99, 100]
    measured = np.percentile(np.asarray(values, float), quantiles)
    return {f"p{q:02d}": float(v) for q, v in zip(quantiles, measured)}


def event_key(value: Any) -> str:
    match = re.match(r"(\d{14})", str(value))
    return match.group(1) if match else str(value)


def shower_label(value: Any) -> str:
    if pd.isna(value):
        return "SPORADIC"
    text = str(value).strip().upper()
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return "SPORADIC" if text in {"", "-1", "0", "NONE", "NAN", "SPO", "SPORADIC", "..."} else text


def is_nop(value: Any) -> bool:
    compact = re.sub(r"[^A-Z0-9]+", "", shower_label(value))
    return compact in {"NOP", "149", "0149", "149NOP", "0149NOP"} or compact.endswith("NOP")


def load_current_gmn(output: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    from gmn_python_api import data_directory as dd
    from gmn_python_api import meteor_trajectory_reader as reader

    frames = []
    audits = []
    columns = [
        "unique_trajectory_identifier", "beginning_utc_time", "iau_code",
        "sol_lon_deg", "lamgeo_deg", "betgeo_deg", "vgeo_km_s",
        "e", "q_au", "i_deg", "peri_deg", "node_deg",
        "medianfiterr_arcsec", "num_stat", "participating_stations",
    ]
    for year in range(2018, 2027):
        for month in (5, 6):
            stamp = f"{year}-{month:02d}"
            try:
                raw = reader.read_data(
                    dd.get_monthly_file_content_by_date(stamp), output_camel_case=True
                ).reset_index(drop=False)
                missing = [column for column in columns if column not in raw.columns]
                if missing:
                    audits.append({"stamp": stamp, "status": "missing_columns", "missing": missing})
                    continue
                data = raw[columns].copy()
                numeric = [
                    "sol_lon_deg", "lamgeo_deg", "betgeo_deg", "vgeo_km_s",
                    "e", "q_au", "i_deg", "peri_deg", "node_deg",
                    "medianfiterr_arcsec", "num_stat",
                ]
                for column in numeric:
                    data[column] = pd.to_numeric(data[column], errors="coerce")
                data["label"] = data["iau_code"].map(shower_label)
                quality = np.isfinite(data[[
                    "sol_lon_deg", "lamgeo_deg", "betgeo_deg", "vgeo_km_s",
                    "e", "q_au", "i_deg", "peri_deg", "node_deg",
                ]]).all(axis=1)
                quality &= data["num_stat"].fillna(0).ge(2)
                quality &= data["medianfiterr_arcsec"].fillna(9999).le(180)
                quality &= data["sol_lon_deg"].between(40, 80)
                selected = data.loc[quality & data["iau_code"].map(is_nop)].copy()
                selected["year"] = year
                selected["month"] = month
                selected["event_key"] = selected["unique_trajectory_identifier"].map(event_key)
                selected["_fit"] = selected["medianfiterr_arcsec"].fillna(1e9)
                selected["_nst"] = selected["num_stat"].fillna(0)
                selected = selected.sort_values(
                    ["event_key", "_fit", "_nst"], ascending=[True, True, False]
                ).drop_duplicates("event_key").drop(columns=["_fit", "_nst"])
                frames.append(selected)
                audits.append({
                    "stamp": stamp, "status": "ok", "raw_rows": int(len(raw)),
                    "nop_quality_rows": int(len(selected)),
                    "labels": selected["label"].value_counts().to_dict(),
                })
            except Exception as exc:
                audits.append({"stamp": stamp, "status": "error", "error": f"{type(exc).__name__}: {exc}"})
    combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if len(combined):
        combined = combined.sort_values(
            ["event_key", "medianfiterr_arcsec", "num_stat"], ascending=[True, True, False]
        ).drop_duplicates("event_key").reset_index(drop=True)
        combined["sun_centered_lon"] = circ_diff(
            combined["lamgeo_deg"].to_numpy(float), combined["sol_lon_deg"].to_numpy(float)
        )
        combined.to_csv(output / "current_gmn_nop_members.csv", index=False)
    return combined, {
        "months": audits,
        "total_members": int(len(combined)),
        "year_counts": combined["year"].value_counts().sort_index().to_dict() if len(combined) else {},
    }


def fit_sun_model(frame, ls, lon, lat, vg):
    x = frame[ls].to_numpy(float)
    reference = float(np.median(frame[lon]))
    unwrapped = reference + circ_diff(frame[lon].to_numpy(float), reference)
    model = {}
    for name, values in [
        ("lon", unwrapped), ("lat", frame[lat].to_numpy(float)), ("vg", frame[vg].to_numpy(float))
    ]:
        fitted = theilslopes(values, x)
        model[name] = (float(fitted.slope), float(fitted.intercept))
    return model


def sun_residuals(frame, model, ls, lon, lat, vg):
    x = frame[ls].to_numpy(float)
    predicted_lon = (model["lon"][1] + model["lon"][0] * x) % 360
    predicted_lat = model["lat"][1] + model["lat"][0] * x
    predicted_vg = model["vg"][1] + model["vg"][0] * x
    return (
        angular_sep(frame[lon], frame[lat], predicted_lon, predicted_lat),
        np.abs(frame[vg].to_numpy(float) - predicted_vg),
    )


def fit_orbit_trend(frame, ls_column, mapping, prediction_longitudes):
    x = frame[ls_column].to_numpy(float)
    parameters = {}
    for target, reference in [("e", .932), ("q", .207), ("i", 16.7), ("peri", 310.5)]:
        values = frame[mapping[target]].to_numpy(float)
        if target == "peri":
            values = reference + circ_diff(values, reference)
        fitted = theilslopes(values, x)
        parameters[target] = (float(fitted.slope), float(fitted.intercept))
    xp = np.asarray(prediction_longitudes, float)
    predicted = np.column_stack([
        parameters["e"][1] + parameters["e"][0] * xp,
        parameters["q"][1] + parameters["q"][0] * xp,
        parameters["i"][1] + parameters["i"][0] * xp,
        (parameters["peri"][1] + parameters["peri"][0] * xp) % 360,
        xp % 360,
    ])
    return predicted, parameters


def compare_population(name, nop, ghost, mapping, ls_column):
    n = nop[[mapping["e"], mapping["q"], mapping["i"], mapping["peri"], mapping["node"]]].to_numpy(float)
    g = ghost[["e", "q_au", "i_deg", "peri_deg", "node_deg"]].to_numpy(float)
    cross = orbit_distance_matrix(g, n)
    within = orbit_distance_matrix(n)
    np.fill_diagonal(within, np.inf)
    predicted_n, parameters = fit_orbit_trend(nop, ls_column, mapping, nop[ls_column])
    predicted_g, _ = fit_orbit_trend(nop, ls_column, mapping, ghost["sol_lon_deg"])
    trend_n = np.diag(orbit_distance_matrix(n, predicted_n))
    trend_g = np.diag(orbit_distance_matrix(g, predicted_g))
    return {
        "name": name,
        "nop_members": int(len(n)),
        "ghost_members": int(len(g)),
        "nop_to_solution004_dsh": pct(orbit_distance_matrix(n, NOP_SOLUTION[None, :])[:, 0]),
        "ghost_to_solution004_dsh": pct(orbit_distance_matrix(g, NOP_SOLUTION[None, :])[:, 0]),
        "nop_within_nearest_neighbor_dsh": pct(within.min(axis=1)),
        "ghost_to_nop_nearest_neighbor_dsh": pct(cross.min(axis=1)),
        "cross_links": {str(t): int((cross <= t).sum()) for t in THRESHOLDS},
        "ghost_with_any_nop_neighbor": {str(t): int((cross.min(axis=1) <= t).sum()) for t in THRESHOLDS},
        "trend_parameters": {key: {"slope_per_deg": value[0], "intercept": value[1]} for key, value in parameters.items()},
        "nop_to_own_orbit_trend_dsh": pct(trend_n),
        "ghost_to_extrapolated_nop_trend_dsh": pct(trend_g),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ghost-members", type=Path, required=True)
    parser.add_argument("--ghost-lookup", type=Path, required=True)
    parser.add_argument("--nop-lookup", type=Path, required=True)
    parser.add_argument("--nop-orbits", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--skip-current-gmn", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    ghost_all = pd.read_csv(args.ghost_members)
    ghost = ghost_all.loc[ghost_all["year"].between(2022, 2026)].copy().reset_index(drop=True)
    ghost_lookup = pd.read_csv(args.ghost_lookup)
    nop_lookup = pd.read_csv(args.nop_lookup, skipinitialspace=True)
    nop_lookup.columns = [column.strip() for column in nop_lookup.columns]
    nop_orbits = pd.read_csv(args.nop_orbits).merge(
        nop_lookup[["CurNum", "LS", "RA", "DEC", "Vg", "SCLO", "LA"]],
        left_on="lookup_number", right_on="CurNum", how="left",
    )
    if (len(ghost), len(ghost_lookup), len(nop_lookup), len(nop_orbits)) != (95, 95, 567, 118):
        raise RuntimeError(
            f"Frozen counts changed: {(len(ghost), len(ghost_lookup), len(nop_lookup), len(nop_orbits))}"
        )

    model = fit_sun_model(nop_lookup, "LS", "SCLO", "LA", "Vg")
    nop_radiant, nop_speed = sun_residuals(nop_lookup, model, "LS", "SCLO", "LA", "Vg")
    ghost_radiant, ghost_speed = sun_residuals(ghost_lookup, model, "LS", "SCLO", "LA", "VG")
    rng = np.random.default_rng(SEED)
    bootstrap_indices = rng.integers(0, len(nop_radiant), size=(100_000, len(ghost_radiant)))
    bootstrap_medians = np.median(nop_radiant[bootstrap_indices], axis=1)
    ghost_median = float(np.median(ghost_radiant))
    median_p = float((np.sum(bootstrap_medians >= ghost_median) + 1) / 100_001)

    historical = compare_population(
        "exact_public_source_matches_to_solution004", nop_orbits, ghost,
        {"e": "e", "q": "q", "i": "i", "peri": "peri", "node": "node"}, "LS",
    )
    current_frame = pd.DataFrame()
    current_audit = {"skipped": True}
    current_comparison = None
    if not args.skip_current_gmn:
        current_frame, current_audit = load_current_gmn(args.output)
        current_audit["skipped"] = False
        if len(current_frame) >= 20:
            current_comparison = compare_population(
                "current_gmn_nop_labeled_population", current_frame, ghost,
                {"e": "e", "q": "q_au", "i": "i_deg", "peri": "peri_deg", "node": "node_deg"},
                "sol_lon_deg",
            )

    activity_gap = float(nop_lookup["LS"].min() - ghost_lookup["LS"].max())
    literal_identity_rejected = (
        activity_gap > 0
        and ghost_median > float(np.max(nop_radiant))
        and historical["ghost_to_nop_nearest_neighbor_dsh"]["p50"]
            > historical["nop_within_nearest_neighbor_dsh"]["p99"]
        and historical["ghost_to_extrapolated_nop_trend_dsh"]["p50"]
            > historical["nop_to_own_orbit_trend_dsh"]["p95"]
    )
    branch_plausible = historical["ghost_with_any_nop_neighbor"]["0.15"] > 0
    verdict = (
        "LITERAL_NOP004_IDENTITY_REJECTED_BRANCH_RELATION_REMAINS_PLAUSIBLE"
        if literal_identity_rejected and branch_plausible
        else "DISTINCT_VS_BRANCH_REMAINS_UNRESOLVED"
    )

    result = {
        "schema": "ghoststream-nop004-track1-v1",
        "input_sha256": {
            str(path): sha256(path)
            for path in [args.ghost_members, args.ghost_lookup, args.nop_lookup, args.nop_orbits]
        },
        "counts": {
            "ghost_orbits": len(ghost), "ghost_lookup": len(ghost_lookup),
            "nop_lookup": len(nop_lookup), "nop_recovered_orbits": len(nop_orbits),
        },
        "activity": {
            "ghost_solar_longitude_range": [float(ghost_lookup.LS.min()), float(ghost_lookup.LS.max())],
            "nop_solar_longitude_range": [float(nop_lookup.LS.min()), float(nop_lookup.LS.max())],
            "empty_gap_degrees": activity_gap,
        },
        "observational_drift_model": {
            key: {"slope_per_deg": value[0], "intercept": value[1]} for key, value in model.items()
        },
        "observational_residuals": {
            "nop_radiant_deg": pct(nop_radiant), "ghost_radiant_deg": pct(ghost_radiant),
            "nop_speed_km_s": pct(nop_speed), "ghost_speed_km_s": pct(ghost_speed),
            "ghost_members_above_nop_max_radiant_residual": int(np.sum(ghost_radiant > np.max(nop_radiant))),
            "ghost_members_above_nop_q99_radiant_residual": int(np.sum(ghost_radiant > np.quantile(nop_radiant, .99))),
            "bootstrap_p_for_ghost_median_radiant_under_nop": median_p,
        },
        "historical_orbit_population": historical,
        "current_gmn_audit": current_audit,
        "current_gmn_orbit_population": current_comparison,
        "decision": {
            "literal_identity_rejected": bool(literal_identity_rejected),
            "related_branch_still_plausible": bool(branch_plausible),
            "distinct_stream_confirmed": False,
            "verdict": verdict,
            "reason": (
                "The public populations reject literal identity, but moderate D_SH cross-links and incomplete "
                "access to the original 567 member orbits prevent a final distinct-versus-related-branch claim."
            ),
        },
    }
    (args.output / "track1_results.json").write_text(json.dumps(result, indent=2))

    h = historical
    report = [
        "# GhostStream versus NOP solution 004: Track-1 result", "",
        f"Verdict: **{verdict}**", "", "## Frozen public inputs", "",
        f"- GhostStream canonical significant-year members: **{len(ghost)}**",
        f"- official NOP solution-004 observations: **{len(nop_lookup)}**",
        f"- exact public source-matched NOP orbits: **{len(nop_orbits)}**", "",
        "## Activity and observed radiant", "",
        f"- GhostStream solar-longitude range: **{ghost_lookup.LS.min():.3f}–{ghost_lookup.LS.max():.3f}°**",
        f"- NOP solution-004 observed range: **{nop_lookup.LS.min():.3f}–{nop_lookup.LS.max():.3f}°**",
        f"- empty interval between them: **{activity_gap:.3f}°**",
        f"- median GhostStream residual from the robust NOP radiant trend: **{np.median(ghost_radiant):.3f}°**",
        f"- maximum NOP member residual from that trend: **{np.max(nop_radiant):.3f}°**",
        f"- GhostStream members above the NOP 99th-percentile residual: **{np.sum(ghost_radiant > np.quantile(nop_radiant, .99))}/{len(ghost_radiant)}**",
        f"- bootstrap probability of a NOP sample having a median residual this large: **{median_p:.6g}**", "",
        "## Orbit-population comparison", "",
        f"- NOP within-population nearest-neighbor D_SH median / p99: **{h['nop_within_nearest_neighbor_dsh']['p50']:.4f} / {h['nop_within_nearest_neighbor_dsh']['p99']:.4f}**",
        f"- GhostStream nearest-NOP D_SH median / minimum: **{h['ghost_to_nop_nearest_neighbor_dsh']['p50']:.4f} / {h['ghost_to_nop_nearest_neighbor_dsh']['p00']:.4f}**",
        f"- GhostStream members with any NOP neighbor at D_SH <= 0.10: **{h['ghost_with_any_nop_neighbor']['0.1']}/{len(ghost)}**",
        f"- GhostStream members with any NOP neighbor at D_SH <= 0.15: **{h['ghost_with_any_nop_neighbor']['0.15']}/{len(ghost)}**",
        f"- median NOP residual from its own orbital trend: **{h['nop_to_own_orbit_trend_dsh']['p50']:.4f}**",
        f"- median GhostStream residual from the extrapolated NOP orbital trend: **{h['ghost_to_extrapolated_nop_trend_dsh']['p50']:.4f}**", "",
    ]
    if current_comparison:
        c = current_comparison
        report += [
            "## Current GMN NOP-labelled population", "",
            f"- quality-controlled NOP-labelled GMN members recovered: **{c['nop_members']}**",
            f"- GhostStream nearest-current-NOP D_SH median: **{c['ghost_to_nop_nearest_neighbor_dsh']['p50']:.4f}**",
            f"- GhostStream members with current NOP neighbor at D_SH <= 0.10: **{c['ghost_with_any_nop_neighbor']['0.1']}/{len(ghost)}**", "",
        ]
    report += [
        "## Interpretation", "",
        "- The data reject the simple claim that GhostStream is merely the same NOP solution-004 population observed earlier in the year.",
        "- The two populations are separated in activity, radiant evolution and the dense part of orbital space.",
        "- A relationship within the broader Ophiuchid/antihelion complex remains plausible because moderate-threshold orbital links exist.",
        "- A definitive **distinct stream** claim still requires the original complete NOP-004 member orbits or an authoritative expert assessment.", "",
    ]
    (args.output / "TRACK1_REPORT.md").write_text("\n".join(report))
    print("\n".join(report))


if __name__ == "__main__":
    main()
