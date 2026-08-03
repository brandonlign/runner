from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
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
STAGE1B_SOURCE_COMMIT = "aada89b4bfdb9a15da51333b07ec0f765bb94531"
VERDICT_PASS = "PROCEED_TO_CONTROL_CALIBRATION_WITH_LS_RECONCILED_NOMINAL_ORBITS"
VERDICT_FAIL = "KILL_LS_RECONCILED_NOMINAL_ORBIT_ROUTE"
MAX_ITERATIONS = 8
DERIVATIVE_STEP_DAYS = 0.01


def circular_delta_array(values: np.ndarray, references: np.ndarray) -> np.ndarray:
    return (values - references + 180.0) % 360.0 - 180.0


def earth_heliocentric_state_and_j2000_solar_longitude(
    times: Time,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    with solar_system_ephemeris.set("builtin"):
        earth_position, earth_velocity = get_body_barycentric_posvel("earth", times)
        sun_position, sun_velocity = get_body_barycentric_posvel("sun", times)

    earth_position_eq = (earth_position - sun_position).xyz.to_value(u.km).T
    earth_velocity_eq = (earth_velocity - sun_velocity).xyz.to_value(u.km / u.s).T
    earth_position_ecliptic = stage1a.equatorial_to_ecliptic(earth_position_eq)
    sun_geocentric_ecliptic = -earth_position_ecliptic
    solar_longitude = (
        np.degrees(
            np.arctan2(
                sun_geocentric_ecliptic[:, 1],
                sun_geocentric_ecliptic[:, 0],
            )
        )
        % 360.0
    )
    return earth_position_eq, earth_velocity_eq, solar_longitude


def reconcile_times(
    original_times: Time,
    target_solar_longitude_deg: np.ndarray,
) -> tuple[Time, np.ndarray, np.ndarray, int]:
    reconciled = original_times.copy()
    iterations_used = 0

    for iteration in range(1, MAX_ITERATIONS + 1):
        _, _, current_longitude = earth_heliocentric_state_and_j2000_solar_longitude(reconciled)
        residual = circular_delta_array(target_solar_longitude_deg, current_longitude)
        iterations_used = iteration
        if float(np.max(np.abs(residual))) <= 1e-10:
            break

        probe_times = reconciled + DERIVATIVE_STEP_DAYS * u.day
        _, _, probe_longitude = earth_heliocentric_state_and_j2000_solar_longitude(probe_times)
        rate_deg_per_day = circular_delta_array(probe_longitude, current_longitude) / DERIVATIVE_STEP_DAYS
        if not np.all(np.isfinite(rate_deg_per_day)) or np.any(np.abs(rate_deg_per_day) < 0.5):
            raise RuntimeError("Invalid solar-longitude derivative during timestamp reconciliation")
        reconciled = reconciled + (residual / rate_deg_per_day) * u.day

    _, _, final_longitude = earth_heliocentric_state_and_j2000_solar_longitude(reconciled)
    final_residual = circular_delta_array(target_solar_longitude_deg, final_longitude)
    shifts_hours = (reconciled - original_times).to_value(u.hour)
    return reconciled, shifts_hours, final_residual, iterations_used


def reconstruct(rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], dict[str, object]]:
    original_datetimes = [row["timestamp"] for row in rows]
    original_times = Time([value.isoformat(sep=" ") for value in original_datetimes], scale="utc")
    target_solar_longitude = np.array(
        [float(row["solar_longitude_deg"]) for row in rows],
        dtype=float,
    )
    reconciled_times, shifts_hours, final_residual, iterations_used = reconcile_times(
        original_times,
        target_solar_longitude,
    )

    earth_position_eq, earth_velocity_eq, reconciled_solar_longitude = (
        earth_heliocentric_state_and_j2000_solar_longitude(reconciled_times)
    )

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
    meteoroid_velocity_eq = earth_velocity_eq + geocentric_velocity_eq
    positions_ecliptic = stage1a.equatorial_to_ecliptic(earth_position_eq)
    velocities_ecliptic = stage1a.equatorial_to_ecliptic(meteoroid_velocity_eq)

    reconciled_datetimes = reconciled_times.utc.to_datetime()
    results: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        elements = stage1a.state_to_elements(positions_ecliptic[index], velocities_ecliptic[index])
        original_datetime = original_datetimes[index]
        reconciled_datetime = reconciled_datetimes[index]
        results.append(
            {
                **row,
                "original_timestamp": original_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                "reconciled_timestamp": reconciled_datetime.strftime("%Y-%m-%d %H:%M:%S.%f"),
                "timestamp_shift_hours": float(shifts_hours[index]),
                "absolute_timestamp_shift_hours": abs(float(shifts_hours[index])),
                "reconciled_solar_longitude_deg": float(reconciled_solar_longitude[index]),
                "solar_longitude_residual_deg": float(final_residual[index]),
                "calendar_year_changed": original_datetime.year != reconciled_datetime.year,
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

    absolute_shifts = np.abs(shifts_hours)
    absolute_residuals = np.abs(final_residual)
    by_source_values: dict[str, list[float]] = defaultdict(list)
    for row in results:
        by_source_values[str(row["source"])].append(float(row["absolute_timestamp_shift_hours"]))
    by_source = {
        source: {
            "count": len(values),
            "median_absolute_shift_hours": float(np.median(values)),
            "p95_absolute_shift_hours": float(np.quantile(values, 0.95)),
            "maximum_absolute_shift_hours": float(np.max(values)),
        }
        for source, values in sorted(by_source_values.items())
    }

    summary = {
        "formulation": "stage1c_ls_reconciled_epoch",
        "stage1a_source_commit": STAGE1A_SOURCE_COMMIT,
        "stage1b_source_commit": STAGE1B_SOURCE_COMMIT,
        "input_rows": len(rows),
        "unique_cur_num": len({int(row["cur_num"]) for row in rows}),
        "timestamp_parse_rows": len(rows),
        "newton_iterations_used": iterations_used,
        "maximum_absolute_solar_longitude_residual_deg": float(np.max(absolute_residuals)),
        "median_absolute_timestamp_shift_hours": float(np.median(absolute_shifts)),
        "p95_absolute_timestamp_shift_hours": float(np.quantile(absolute_shifts, 0.95)),
        "maximum_absolute_timestamp_shift_hours": float(np.max(absolute_shifts)),
        "calendar_year_changes": sum(bool(row["calendar_year_changed"]) for row in results),
        "timestamp_reconciliation_by_source": by_source,
        "finite_orbit_rows": len(finite_rows),
        "finite_orbit_fraction": len(finite_rows) / len(rows),
        "bound_orbit_rows": len(bound_rows),
        "bound_orbit_fraction": len(bound_rows) / len(rows),
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
        "all_ls_residuals_at_most_0_001deg": summary["maximum_absolute_solar_longitude_residual_deg"] <= 0.001,
        "median_absolute_timestamp_shift_at_most_1h": summary["median_absolute_timestamp_shift_hours"] <= 1.0,
        "p95_absolute_timestamp_shift_at_most_12h": summary["p95_absolute_timestamp_shift_hours"] <= 12.0,
        "maximum_absolute_timestamp_shift_at_most_72h": summary["maximum_absolute_timestamp_shift_hours"] <= 72.0,
        "no_calendar_year_changes": summary["calendar_year_changes"] == 0,
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
    (output / "timestamp_reconciliation_by_source.json").write_text(
        json.dumps(summary["timestamp_reconciliation_by_source"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    fieldnames = [
        "cur_num",
        "source",
        "original_timestamp",
        "reconciled_timestamp",
        "timestamp_shift_hours",
        "absolute_timestamp_shift_hours",
        "ra_deg",
        "dec_deg",
        "vg_km_s",
        "solar_longitude_deg",
        "reconciled_solar_longitude_deg",
        "solar_longitude_residual_deg",
        "calendar_year_changed",
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
    with (output / "reconciled_nominal_orbits.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in fieldnames})

    orbit = summary["median_reconstructed_orbit"]
    comparison = summary["comparison"]
    lines = [
        "# NOP solution 004 LS-reconciled nominal-orbit reconstruction",
        "",
        f"- input rows: **{summary['input_rows']}**",
        f"- maximum final LS residual: **{summary['maximum_absolute_solar_longitude_residual_deg']:.9f}°**",
        f"- median absolute timestamp shift: **{summary['median_absolute_timestamp_shift_hours']:.6f} h**",
        f"- p95 absolute timestamp shift: **{summary['p95_absolute_timestamp_shift_hours']:.6f} h**",
        f"- maximum absolute timestamp shift: **{summary['maximum_absolute_timestamp_shift_hours']:.6f} h**",
        f"- calendar-year changes: **{summary['calendar_year_changes']}**",
        f"- finite reconstructed orbits: **{summary['finite_orbit_rows']} ({summary['finite_orbit_fraction']:.4f})**",
        f"- bound reconstructed orbits: **{summary['bound_orbit_rows']} ({summary['bound_orbit_fraction']:.4f})**",
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
        "## Timestamp shifts by source",
        "",
    ]
    for source, values in summary["timestamp_reconciliation_by_source"].items():
        lines.append(
            f"- {source}: n={values['count']}, median={values['median_absolute_shift_hours']:.6f} h, "
            f"p95={values['p95_absolute_shift_hours']:.6f} h, max={values['maximum_absolute_shift_hours']:.6f} h"
        )
    lines.extend(["", "## Frozen gates", ""])
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
