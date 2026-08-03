from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from statistics import median

import numpy as np
from astropy import units as u
from astropy.coordinates import get_body_barycentric_posvel, solar_system_ephemeris
from astropy.time import Time

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from nop004_orbit_reconstruction_stage1 import reconstruct_nominal_orbits as stage1a  # noqa: E402

STAGE1A_SOURCE_COMMIT = "20553c89f52aaa9b5f9b0ceaea019f759c3506af"
VERDICT_PASS = "PROCEED_TO_NOMINAL_ORBIT_BRANCH_CALIBRATION_J2000"
VERDICT_FAIL = "KILL_NOMINAL_ORBIT_RECONSTRUCTION_J2000"


def reconstruct(rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], dict[str, object]]:
    timestamps = [row["timestamp"].isoformat(sep=" ") for row in rows]
    times = Time(timestamps, scale="utc")

    with solar_system_ephemeris.set("builtin"):
        earth_position, earth_velocity = get_body_barycentric_posvel("earth", times)
        sun_position, sun_velocity = get_body_barycentric_posvel("sun", times)

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

    positions_ecliptic = stage1a.equatorial_to_ecliptic(earth_helio_position_eq)
    velocities_ecliptic = stage1a.equatorial_to_ecliptic(meteoroid_helio_velocity_eq)

    # The MDC lookup convention is the mean ecliptic of epoch J2000. The
    # geocentric Sun vector is the negative of Earth's heliocentric position.
    sun_geocentric_ecliptic = -positions_ecliptic
    timestamp_solar_longitude = (
        np.degrees(
            np.arctan2(
                sun_geocentric_ecliptic[:, 1],
                sun_geocentric_ecliptic[:, 0],
            )
        )
        % 360.0
    )

    results: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        elements = stage1a.state_to_elements(positions_ecliptic[index], velocities_ecliptic[index])
        lookup_solar_longitude = float(row["solar_longitude_deg"])
        results.append(
            {
                **row,
                "timestamp": row["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp_solar_longitude_deg": float(timestamp_solar_longitude[index]),
                "solar_longitude_error_deg": abs(
                    stage1a.circular_delta_deg(
                        float(timestamp_solar_longitude[index]),
                        lookup_solar_longitude,
                    )
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
        "peri": stage1a.circular_median_near(
            [float(row["peri_deg"]) for row in bound_rows],
            stage1a.TARGET["peri"],
        ),
        "node": stage1a.circular_median_near(
            [float(row["node_deg"]) for row in bound_rows],
            stage1a.TARGET["node"],
        ),
    }
    solar_errors = np.array([float(row["solar_longitude_error_deg"]) for row in results], dtype=float)
    comparison = {
        "a_delta_au": abs(median_orbit["a"] - stage1a.TARGET["a"]),
        "q_delta_au": abs(median_orbit["q"] - stage1a.TARGET["q"]),
        "e_delta": abs(median_orbit["e"] - stage1a.TARGET["e"]),
        "inc_delta_deg": abs(median_orbit["inc"] - stage1a.TARGET["inc"]),
        "peri_delta_deg": abs(
            stage1a.circular_delta_deg(median_orbit["peri"], stage1a.TARGET["peri"])
        ),
        "node_delta_deg": abs(
            stage1a.circular_delta_deg(median_orbit["node"], stage1a.TARGET["node"])
        ),
        "d_sh": stage1a.d_sh(median_orbit, stage1a.TARGET),
    }
    summary = {
        "formulation": "stage1b_j2000_solar_longitude_correction",
        "stage1a_source_commit": STAGE1A_SOURCE_COMMIT,
        "solar_longitude_reference": "mean_ecliptic_epoch_J2000",
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
        "target_solution004": stage1a.TARGET,
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
    verdict = VERDICT_PASS if all(gates.values()) else VERDICT_FAIL
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
    with (output / "reconstructed_nominal_orbits.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in fieldnames})

    orbit = summary["median_reconstructed_orbit"]
    comparison = summary["comparison"]
    lines = [
        "# NOP solution 004 nominal-orbit reconstruction: J2000 correction",
        "",
        f"- input rows: **{summary['input_rows']}**",
        f"- finite reconstructed orbits: **{summary['finite_orbit_rows']} ({summary['finite_orbit_fraction']:.4f})**",
        f"- bound reconstructed orbits: **{summary['bound_orbit_rows']} ({summary['bound_orbit_fraction']:.4f})**",
        f"- median J2000 timestamp/lookup solar-longitude error: **{summary['solar_longitude_error_median_deg']:.6f}°**",
        f"- p95 J2000 timestamp/lookup solar-longitude error: **{summary['solar_longitude_error_p95_deg']:.6f}°**",
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
    report = "\n".join(lines)
    (output / "RECONSTRUCTION_REPORT.md").write_text(report, encoding="utf-8")
    print(report)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lookup", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = stage1a.read_lookup(args.lookup)
    reconstructed, summary = reconstruct(rows)
    write_outputs(args.output, reconstructed, summary)


if __name__ == "__main__":
    main()
