from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime
from pathlib import Path
from statistics import median

import numpy as np
from astropy import units as u
from astropy.coordinates import (
    GeocentricTrueEcliptic,
    get_body_barycentric_posvel,
    get_sun,
    solar_system_ephemeris,
)
from astropy.time import Time

MU_SUN_KM3_S2 = 1.32712440018e11
OBLIQUITY_J2000_DEG = 23.439291111
TARGET = {
    "a": 2.43,
    "q": 0.207,
    "e": 0.932,
    "inc": 16.7,
    "peri": 310.5,
    "node": 58.6,
    "vg": 36.0,
    "sol": 58.6,
}


def circular_delta_deg(value: float, reference: float) -> float:
    return (value - reference + 180.0) % 360.0 - 180.0


def circular_median_near(values: list[float], reference: float) -> float:
    adjusted = [reference + circular_delta_deg(value, reference) for value in values]
    return float(median(adjusted) % 360.0)


def parse_timestamp(value: str) -> datetime:
    return datetime.strptime(value.strip(), "%Y-%m-%d-%H:%M:%S")


def read_lookup(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise RuntimeError("Lookup has no header")
        for raw in reader:
            row = {str(key).strip(): str(value).strip() for key, value in raw.items()}
            rows.append(
                {
                    "cur_num": int(row["CurNum"]),
                    "timestamp": parse_timestamp(row["Tobs"]),
                    "ra_deg": float(row["RA"]),
                    "dec_deg": float(row["DEC"]),
                    "vg_km_s": float(row["Vg"]),
                    "solar_longitude_deg": float(row["LS"]),
                    "source": row.get("Sode", ""),
                }
            )
    return rows


def equatorial_to_ecliptic(vectors: np.ndarray) -> np.ndarray:
    epsilon = math.radians(OBLIQUITY_J2000_DEG)
    cosine = math.cos(epsilon)
    sine = math.sin(epsilon)
    result = np.empty_like(vectors, dtype=float)
    result[:, 0] = vectors[:, 0]
    result[:, 1] = cosine * vectors[:, 1] + sine * vectors[:, 2]
    result[:, 2] = -sine * vectors[:, 1] + cosine * vectors[:, 2]
    return result


def state_to_elements(r_km: np.ndarray, v_km_s: np.ndarray) -> dict[str, float | bool]:
    r_norm = float(np.linalg.norm(r_km))
    v_norm = float(np.linalg.norm(v_km_s))
    h_vec = np.cross(r_km, v_km_s)
    h_norm = float(np.linalg.norm(h_vec))
    n_vec = np.array([-h_vec[1], h_vec[0], 0.0], dtype=float)
    n_norm = float(np.linalg.norm(n_vec))
    rv_dot = float(np.dot(r_km, v_km_s))
    e_vec = (((v_norm * v_norm - MU_SUN_KM3_S2 / r_norm) * r_km) - rv_dot * v_km_s) / MU_SUN_KM3_S2
    eccentricity = float(np.linalg.norm(e_vec))
    energy = 0.5 * v_norm * v_norm - MU_SUN_KM3_S2 / r_norm
    semimajor = float(-MU_SUN_KM3_S2 / (2.0 * energy)) if abs(energy) > 1e-15 else math.inf
    perihelion = float(semimajor * (1.0 - eccentricity))
    inclination = math.degrees(math.acos(float(np.clip(h_vec[2] / h_norm, -1.0, 1.0))))

    if n_norm <= 1e-12 or eccentricity <= 1e-12:
        node = math.nan
        argument_perihelion = math.nan
    else:
        node = math.degrees(math.atan2(n_vec[1], n_vec[0])) % 360.0
        cosine_argument = float(np.dot(n_vec, e_vec) / (n_norm * eccentricity))
        sine_argument = float(np.dot(np.cross(n_vec, e_vec), h_vec) / (n_norm * eccentricity * h_norm))
        argument_perihelion = math.degrees(math.atan2(sine_argument, cosine_argument)) % 360.0

    finite = all(
        math.isfinite(value)
        for value in (semimajor, perihelion, eccentricity, inclination, node, argument_perihelion)
    )
    bound = bool(finite and energy < 0.0 and 0.0 <= eccentricity < 1.0 and semimajor > 0.0)
    return {
        "a_au": semimajor / 149597870.7,
        "q_au": perihelion / 149597870.7,
        "e": eccentricity,
        "inc_deg": inclination,
        "peri_deg": argument_perihelion,
        "node_deg": node,
        "heliocentric_speed_km_s": v_norm,
        "specific_energy_km2_s2": energy,
        "finite": finite,
        "bound": bound,
    }


def d_sh(orbit_a: dict[str, float], orbit_b: dict[str, float]) -> float:
    q1, e1 = orbit_a["q"], orbit_a["e"]
    q2, e2 = orbit_b["q"], orbit_b["e"]
    i1, w1, o1 = map(math.radians, (orbit_a["inc"], orbit_a["peri"], orbit_a["node"]))
    i2, w2, o2 = map(math.radians, (orbit_b["inc"], orbit_b["peri"], orbit_b["node"]))
    delta_node = math.atan2(math.sin(o1 - o2), math.cos(o1 - o2))
    cosine_i = math.cos(i1) * math.cos(i2) + math.sin(i1) * math.sin(i2) * math.cos(delta_node)
    plane_angle = math.acos(max(-1.0, min(1.0, cosine_i)))
    denominator = max(math.cos(plane_angle / 2.0), 1e-12)
    asin_argument = math.cos((i1 + i2) / 2.0) * math.sin(delta_node / 2.0) / denominator
    peri_difference = w1 - w2 + 2.0 * math.asin(max(-1.0, min(1.0, asin_argument)))
    return math.sqrt(
        (e1 - e2) ** 2
        + (q1 - q2) ** 2
        + (2.0 * math.sin(plane_angle / 2.0)) ** 2
        + (((e1 + e2) / 2.0) * 2.0 * math.sin(peri_difference / 2.0)) ** 2
    )


def reconstruct(rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], dict[str, object]]:
    timestamps = [row["timestamp"].isoformat(sep=" ") for row in rows]
    times = Time(timestamps, scale="utc")

    with solar_system_ephemeris.set("builtin"):
        earth_position, earth_velocity = get_body_barycentric_posvel("earth", times)
        sun_position, sun_velocity = get_body_barycentric_posvel("sun", times)
        apparent_sun = get_sun(times)

    earth_helio_position_eq = (earth_position - sun_position).xyz.to_value(u.km).T
    earth_helio_velocity_eq = (earth_velocity - sun_velocity).xyz.to_value(u.km / u.s).T

    ra = np.radians(np.array([float(row["ra_deg"]) for row in rows], dtype=float))
    dec = np.radians(np.array([float(row["dec_deg"]) for row in rows], dtype=float))
    vg = np.array([float(row["vg_km_s"]) for row in rows], dtype=float)
    radiant_unit = np.column_stack(
        (
            np.cos(dec) * np.cos(ra),
            np.cos(dec) * np.sin(ra),
            np.sin(dec),
        )
    )
    geocentric_velocity_eq = -vg[:, None] * radiant_unit
    meteoroid_helio_velocity_eq = earth_helio_velocity_eq + geocentric_velocity_eq

    positions_ecliptic = equatorial_to_ecliptic(earth_helio_position_eq)
    velocities_ecliptic = equatorial_to_ecliptic(meteoroid_helio_velocity_eq)

    sun_ecliptic = apparent_sun.transform_to(GeocentricTrueEcliptic(equinox=times))
    timestamp_solar_longitude = sun_ecliptic.lon.to_value(u.deg) % 360.0

    results: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        elements = state_to_elements(positions_ecliptic[index], velocities_ecliptic[index])
        lookup_solar_longitude = float(row["solar_longitude_deg"])
        results.append(
            {
                **row,
                "timestamp": row["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp_solar_longitude_deg": float(timestamp_solar_longitude[index]),
                "solar_longitude_error_deg": abs(
                    circular_delta_deg(float(timestamp_solar_longitude[index]), lookup_solar_longitude)
                ),
                **elements,
            }
        )

    finite_rows = [row for row in results if bool(row["finite"])]
    bound_rows = [row for row in finite_rows if bool(row["bound"])]
    if not bound_rows:
        raise RuntimeError("No bound reconstructed rows")

    median_orbit = {
        "a": float(median(float(row["a_au"]) for row in bound_rows)),
        "q": float(median(float(row["q_au"]) for row in bound_rows)),
        "e": float(median(float(row["e"]) for row in bound_rows)),
        "inc": float(median(float(row["inc_deg"]) for row in bound_rows)),
        "peri": circular_median_near([float(row["peri_deg"]) for row in bound_rows], TARGET["peri"]),
        "node": circular_median_near([float(row["node_deg"]) for row in bound_rows], TARGET["node"]),
    }
    solar_errors = np.array([float(row["solar_longitude_error_deg"]) for row in results], dtype=float)
    comparison = {
        "a_delta_au": abs(median_orbit["a"] - TARGET["a"]),
        "q_delta_au": abs(median_orbit["q"] - TARGET["q"]),
        "e_delta": abs(median_orbit["e"] - TARGET["e"]),
        "inc_delta_deg": abs(median_orbit["inc"] - TARGET["inc"]),
        "peri_delta_deg": abs(circular_delta_deg(median_orbit["peri"], TARGET["peri"])),
        "node_delta_deg": abs(circular_delta_deg(median_orbit["node"], TARGET["node"])),
        "d_sh": d_sh(median_orbit, TARGET),
    }
    summary = {
        "input_rows": len(rows),
        "unique_cur_num": len({int(row["cur_num"]) for row in rows}),
        "timestamp_parse_rows": len(rows),
        "finite_orbit_rows": len(finite_rows),
        "finite_orbit_fraction": len(finite_rows) / len(rows),
        "bound_orbit_rows": len(bound_rows),
        "bound_orbit_fraction": len(bound_rows) / len(rows),
        "solar_longitude_error_median_deg": float(np.median(solar_errors)),
        "solar_longitude_error_p95_deg": float(np.quantile(solar_errors, 0.95)),
        "median_reconstructed_orbit": median_orbit,
        "target_solution004": TARGET,
        "comparison": comparison,
    }
    return results, summary


def evaluate(summary: dict[str, object]) -> dict[str, bool]:
    comparison = summary["comparison"]
    return {
        "exactly_567_unique_rows": summary["input_rows"] == 567 and summary["unique_cur_num"] == 567,
        "all_timestamps_parsed": summary["timestamp_parse_rows"] == 567,
        "solar_longitude_median_error_at_most_0_15deg": summary["solar_longitude_error_median_deg"] <= 0.15,
        "solar_longitude_p95_error_at_most_0_35deg": summary["solar_longitude_error_p95_deg"] <= 0.35,
        "finite_orbit_fraction_at_least_0_95": summary["finite_orbit_fraction"] >= 0.95,
        "bound_orbit_fraction_at_least_0_90": summary["bound_orbit_fraction"] >= 0.90,
        "median_q_delta_at_most_0_03au": comparison["q_delta_au"] <= 0.03,
        "median_e_delta_at_most_0_05": comparison["e_delta"] <= 0.05,
        "median_inc_delta_at_most_3deg": comparison["inc_delta_deg"] <= 3.0,
        "median_peri_delta_at_most_5deg": comparison["peri_delta_deg"] <= 5.0,
        "median_node_delta_at_most_1deg": comparison["node_delta_deg"] <= 1.0,
        "median_d_sh_at_most_0_08": comparison["d_sh"] <= 0.08,
    }


def write_outputs(output: Path, rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    gates = evaluate(summary)
    verdict = "PROCEED_TO_NOMINAL_ORBIT_BRANCH_CALIBRATION" if all(gates.values()) else "KILL_NOMINAL_ORBIT_RECONSTRUCTION"
    payload = {**summary, "gates": gates, "verdict": verdict}
    (output / "reconstruction_summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    fieldnames = [
        "cur_num",
        "timestamp",
        "source",
        "ra_deg",
        "dec_deg",
        "vg_km_s",
        "solar_longitude_deg",
        "timestamp_solar_longitude_deg",
        "solar_longitude_error_deg",
        "a_au",
        "q_au",
        "e",
        "inc_deg",
        "peri_deg",
        "node_deg",
        "heliocentric_speed_km_s",
        "specific_energy_km2_s2",
        "finite",
        "bound",
    ]
    with (output / "reconstructed_nominal_orbits.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in fieldnames})

    orbit = summary["median_reconstructed_orbit"]
    comparison = summary["comparison"]
    lines = [
        "# NOP solution 004 nominal-orbit reconstruction",
        "",
        f"- input rows: **{summary['input_rows']}**",
        f"- finite reconstructed orbits: **{summary['finite_orbit_rows']} ({summary['finite_orbit_fraction']:.4f})**",
        f"- bound reconstructed orbits: **{summary['bound_orbit_rows']} ({summary['bound_orbit_fraction']:.4f})**",
        f"- median timestamp/lookup solar-longitude error: **{summary['solar_longitude_error_median_deg']:.6f}°**",
        f"- p95 timestamp/lookup solar-longitude error: **{summary['solar_longitude_error_p95_deg']:.6f}°**",
        "",
        "## Reconstructed median orbit",
        "",
        f"- a: **{orbit['a']:.6f} AU** (target 2.43; |Δ| {comparison['a_delta_au']:.6f})",
        f"- q: **{orbit['q']:.6f} AU** (target 0.207; |Δ| {comparison['q_delta_au']:.6f})",
        f"- e: **{orbit['e']:.6f}** (target 0.932; |Δ| {comparison['e_delta']:.6f})",
        f"- i: **{orbit['inc']:.6f}°** (target 16.7; |Δ| {comparison['inc_delta_deg']:.6f}°)",
        f"- ω: **{orbit['peri']:.6f}°** (target 310.5; circular |Δ| {comparison['peri_delta_deg']:.6f}°)",
        f"- Ω: **{orbit['node']:.6f}°** (target 58.6; circular |Δ| {comparison['node_delta_deg']:.6f}°)",
        f"- D_SH to solution 004: **{comparison['d_sh']:.6f}**",
        "",
        "## Frozen gates",
        "",
    ]
    lines.extend(f"- {'PASS' if passed else 'FAIL'} — `{name}`" for name, passed in gates.items())
    lines.extend(["", f"Verdict: **{verdict}**", ""])
    (output / "RECONSTRUCTION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lookup", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = read_lookup(args.lookup)
    reconstructed, summary = reconstruct(rows)
    write_outputs(args.output, reconstructed, summary)


if __name__ == "__main__":
    main()
