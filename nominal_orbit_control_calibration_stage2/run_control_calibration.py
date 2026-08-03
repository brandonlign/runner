from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import math
import re
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any

import numpy as np
from astropy import units as u
from astropy.time import Time

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from nop004_orbit_reconstruction_stage1 import reconstruct_nominal_orbits as stage1a  # noqa: E402
from nop004_orbit_reconstruction_stage1c import reconstruct_ls_reconciled_orbits as stage1c  # noqa: E402

BASE_LOOKUP_URL = "https://ceresiaumdc.ta3.sk/downloads/LuT/"
USER_AGENT = "ghoststream-nominal-orbit-control-calibration/1.0"
MAX_DOWNLOAD_BYTES = 64 * 1024 * 1024
VERDICT_PASS = "PROCEED_TO_BRANCH_SEPARATION_CONTROL_DESIGN"
VERDICT_FAIL = "KILL_GENERAL_NOMINAL_ORBIT_RECONSTRUCTION"

ALIASES = {
    "event_id": {
        "curnum",
        "eventid",
        "id",
        "number",
        "meteorid",
        "meteornumber",
    },
    "timestamp": {
        "tobs",
        "timestamp",
        "datetime",
        "datetimeutc",
        "utc",
        "utctime",
        "observationtime",
        "timeofobservation",
        "dateandtime",
        "dateutc",
    },
    "ra": {
        "ra",
        "rag",
        "rightascension",
        "radiantalpha",
        "radiantarectascension",
        "alphag",
    },
    "dec": {
        "dec",
        "de",
        "deg",
        "declination",
        "radiantdelta",
        "deltag",
    },
    "vg": {
        "vg",
        "vgeo",
        "geocentricspeed",
        "geocentricvelocity",
        "velocitygeocentric",
    },
    "sol": {
        "ls",
        "los",
        "sol",
        "sollon",
        "solarlongitude",
        "lambdasun",
        "lambda",
    },
    "source": {
        "sode",
        "source",
        "catalogue",
        "catalog",
        "network",
        "dataset",
    },
}


def normalize_header(value: str) -> str:
    text = (
        html.unescape(str(value or ""))
        .replace("λ", "lambda")
        .replace("☉", "sun")
        .replace("α", "alpha")
        .replace("δ", "delta")
        .lower()
    )
    return re.sub(r"[^a-z0-9]+", "", text)


def finite_float(value: Any) -> float | None:
    try:
        parsed = float(str(value).strip().replace("−", "-"))
    except Exception:
        return None
    return parsed if math.isfinite(parsed) else None


def parse_timestamp(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    normalized = text.replace("T", " ").replace("Z", "+00:00")
    candidates = [normalized]
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}-\d{2}:\d{2}:\d{2}(?:\.\d+)?", text):
        candidates.insert(0, text[:10] + " " + text[11:])
    if re.fullmatch(r"\d{4}/\d{2}/\d{2}[ -]\d{2}:\d{2}:\d{2}(?:\.\d+)?", text):
        candidates.insert(0, text.replace("/", "-").replace("-", " ", 1))
    for candidate in candidates:
        try:
            parsed = datetime.fromisoformat(candidate)
            if parsed.tzinfo is not None:
                parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
            return parsed
        except ValueError:
            pass
    formats = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y.%m.%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%d.%m.%Y %H:%M:%S",
        "%Y-%m-%d-%H:%M:%S",
        "%Y-%m-%d-%H:%M:%S.%f",
    )
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def parse_lookup(raw: bytes) -> tuple[list[dict[str, str]], dict[str, Any]]:
    text = raw.decode("utf-8-sig", "replace")
    low = text.lstrip().lower()
    if low.startswith("<!doctype") or low.startswith("<html") or "<body" in low[:2000]:
        raise ValueError("HTML response")
    lines = [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if len(lines) < 2:
        raise ValueError("too few non-comment rows")
    sample = "\n".join(lines[:60])
    delimiter = max((",", ";", "\t", "|"), key=sample.count)
    if sample.count(delimiter) == 0:
        raise ValueError("no supported delimiter")
    matrix = [row for row in csv.reader(lines, delimiter=delimiter) if any(cell.strip() for cell in row)]
    header_index: int | None = None
    resolved_columns: dict[str, str] = {}
    for index, row in enumerate(matrix[:10]):
        normalized = {normalize_header(cell): cell.strip() for cell in row}
        candidate: dict[str, str] = {}
        for target, aliases in ALIASES.items():
            matches = [original for norm, original in normalized.items() if norm in aliases]
            if len(matches) == 1:
                candidate[target] = matches[0]
        if all(key in candidate for key in ("timestamp", "ra", "dec", "vg", "sol")):
            header_index = index
            resolved_columns = candidate
            break
    if header_index is None:
        raise ValueError("required timestamp/RA/Dec/Vg/LS headers not found")

    headers = [cell.strip() or f"column_{idx}" for idx, cell in enumerate(matrix[header_index])]
    rows: list[dict[str, str]] = []
    for raw_row in matrix[header_index + 1 :]:
        padded = raw_row + [""] * max(0, len(headers) - len(raw_row))
        rows.append({header: padded[index].strip() for index, header in enumerate(headers)})
    return rows, {
        "delimiter": delimiter,
        "header_index": header_index,
        "headers": headers,
        "columns": resolved_columns,
    }


def lookup_candidate_urls(filename: str) -> list[str]:
    widths = [22, len(filename)] + list(range(18, 33))
    urls: list[str] = []
    seen: set[str] = set()
    for width in widths:
        padded = filename if width <= len(filename) else filename.ljust(width)
        encoded = urllib.parse.quote(padded, safe="")
        url = urllib.parse.urljoin(BASE_LOOKUP_URL, encoded)
        if url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def fetch_bytes(url: str) -> tuple[bytes | None, dict[str, Any]]:
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "text/csv,*/*;q=0.5"},
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read(MAX_DOWNLOAD_BYTES + 1)
            if len(raw) > MAX_DOWNLOAD_BYTES:
                raise RuntimeError("lookup response exceeds 64 MiB")
            record = {
                "url": url,
                "status": getattr(response, "status", 200),
                "final_url": response.geturl(),
                "content_type": response.headers.get("Content-Type"),
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "error": None,
            }
            return raw, record
    except Exception as exc:
        return None, {
            "url": url,
            "status": getattr(exc, "code", None),
            "final_url": None,
            "content_type": None,
            "bytes": 0,
            "sha256": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def normalize_rows(
    table_rows: list[dict[str, str]],
    metadata: dict[str, Any],
) -> tuple[list[dict[str, object]], dict[str, Any]]:
    columns = metadata["columns"]
    normalized: list[dict[str, object]] = []
    unique_raw: set[str] = set()
    for index, row in enumerate(table_rows, start=1):
        unique_raw.add(json.dumps(row, sort_keys=True, ensure_ascii=False))
        timestamp = parse_timestamp(row.get(columns["timestamp"], ""))
        ra = finite_float(row.get(columns["ra"], ""))
        dec = finite_float(row.get(columns["dec"], ""))
        vg = finite_float(row.get(columns["vg"], ""))
        sol = finite_float(row.get(columns["sol"], ""))
        if timestamp is None or any(value is None for value in (ra, dec, vg, sol)):
            continue
        event_value = row.get(columns.get("event_id", ""), "") if columns.get("event_id") else ""
        source_value = row.get(columns.get("source", ""), "") if columns.get("source") else ""
        try:
            event_id: int | str = int(float(event_value)) if str(event_value).strip() else index
        except Exception:
            event_id = str(event_value).strip() or index
        normalized.append(
            {
                "cur_num": event_id,
                "timestamp": timestamp,
                "ra_deg": float(ra),
                "dec_deg": float(dec),
                "vg_km_s": float(vg),
                "solar_longitude_deg": float(sol) % 360.0,
                "source": str(source_value).strip(),
            }
        )
    return normalized, {
        "parsed_rows": len(table_rows),
        "unique_raw_rows": len(unique_raw),
        "complete_rows": len(normalized),
        "complete_fraction": len(normalized) / len(table_rows) if table_rows else 0.0,
        **metadata,
    }


def retrieve_lookup(
    control: dict[str, Any],
    output_directory: Path,
) -> tuple[list[dict[str, object]] | None, dict[str, Any]]:
    attempts: list[dict[str, Any]] = []
    filename = control["lookup_filename"]
    for url in lookup_candidate_urls(filename):
        raw, record = fetch_bytes(url)
        if raw is not None:
            try:
                table_rows, parse_metadata = parse_lookup(raw)
                rows, row_metadata = normalize_rows(table_rows, parse_metadata)
                record["table"] = row_metadata
                attempts.append(record)
                if row_metadata["unique_raw_rows"] >= 50 and row_metadata["complete_rows"] >= 50:
                    output_directory.mkdir(parents=True, exist_ok=True)
                    path = output_directory / filename
                    path.write_bytes(raw)
                    return rows, {
                        "retrieved": True,
                        "selected_url": url,
                        "selected_sha256": record["sha256"],
                        "selected_bytes": record["bytes"],
                        "table": row_metadata,
                        "attempts": attempts,
                        "local_path": str(path),
                    }
            except Exception as exc:
                record["parse_error"] = f"{type(exc).__name__}: {exc}"
        attempts.append(record)
    return None, {
        "retrieved": False,
        "selected_url": None,
        "selected_sha256": None,
        "selected_bytes": 0,
        "table": None,
        "attempts": attempts,
        "local_path": None,
    }


def reconstruct_control(
    rows: list[dict[str, object]],
    target: dict[str, float],
) -> tuple[list[dict[str, object]], dict[str, Any]]:
    original_datetimes = [row["timestamp"] for row in rows]
    original_times = Time([value.isoformat(sep=" ") for value in original_datetimes], scale="utc")
    target_solar_longitude = np.array(
        [float(row["solar_longitude_deg"]) for row in rows],
        dtype=float,
    )
    reconciled_times, shifts_hours, final_residual, iterations_used = stage1c.reconcile_times(
        original_times,
        target_solar_longitude,
    )
    earth_position_eq, earth_velocity_eq, reconciled_solar_longitude = (
        stage1c.earth_heliocentric_state_and_j2000_solar_longitude(reconciled_times)
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

    reconstructed: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        elements = stage1a.state_to_elements(positions_ecliptic[index], velocities_ecliptic[index])
        reconstructed.append(
            {
                **row,
                "original_timestamp": original_datetimes[index].strftime("%Y-%m-%d %H:%M:%S"),
                "reconciled_timestamp": reconciled_datetimes[index].strftime("%Y-%m-%d %H:%M:%S.%f"),
                "timestamp_shift_hours": float(shifts_hours[index]),
                "absolute_timestamp_shift_hours": abs(float(shifts_hours[index])),
                "reconciled_solar_longitude_deg": float(reconciled_solar_longitude[index]),
                "solar_longitude_residual_deg": float(final_residual[index]),
                "calendar_year_changed": original_datetimes[index].year != reconciled_datetimes[index].year,
                **elements,
            }
        )

    finite_rows = [row for row in reconstructed if bool(row["finite"])]
    bound_rows = [row for row in finite_rows if bool(row["bound"])]
    if not bound_rows:
        raise RuntimeError("control produced no bound reconstructed rows")

    orbit = {
        "a": float(median(float(row["a_au"]) for row in bound_rows)),
        "q": float(median(float(row["q_au"]) for row in bound_rows)),
        "e": float(median(float(row["e"]) for row in bound_rows)),
        "inc": float(median(float(row["inc_deg"]) for row in bound_rows)),
        "peri": stage1a.circular_median_near(
            [float(row["peri_deg"]) for row in bound_rows],
            float(target["peri"]),
        ),
        "node": stage1a.circular_median_near(
            [float(row["node_deg"]) for row in bound_rows],
            float(target["node"]),
        ),
    }
    comparison = {
        "a_delta_au": abs(orbit["a"] - float(target["a"])),
        "q_delta_au": abs(orbit["q"] - float(target["q"])),
        "e_delta": abs(orbit["e"] - float(target["e"])),
        "inc_delta_deg": abs(orbit["inc"] - float(target["inc"])),
        "peri_delta_deg": abs(stage1a.circular_delta_deg(orbit["peri"], float(target["peri"]))),
        "node_delta_deg": abs(stage1a.circular_delta_deg(orbit["node"], float(target["node"]))),
        "d_sh": stage1a.d_sh(orbit, target),
    }
    absolute_shifts = np.abs(shifts_hours)
    absolute_residuals = np.abs(final_residual)
    metrics = {
        "newton_iterations_used": iterations_used,
        "maximum_absolute_solar_longitude_residual_deg": float(np.max(absolute_residuals)),
        "median_absolute_timestamp_shift_hours": float(np.median(absolute_shifts)),
        "p95_absolute_timestamp_shift_hours": float(np.quantile(absolute_shifts, 0.95)),
        "maximum_absolute_timestamp_shift_hours": float(np.max(absolute_shifts)),
        "calendar_year_changes": sum(bool(row["calendar_year_changed"]) for row in reconstructed),
        "finite_orbit_rows": len(finite_rows),
        "finite_orbit_fraction": len(finite_rows) / len(rows),
        "bound_orbit_rows": len(bound_rows),
        "bound_orbit_fraction": len(bound_rows) / len(rows),
        "median_reconstructed_orbit": orbit,
        "comparison": comparison,
    }
    return reconstructed, metrics


def write_reconstructed_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in fieldnames})


def control_gates(
    retrieval: dict[str, Any],
    reconstruction: dict[str, Any] | None,
) -> dict[str, bool]:
    table = retrieval.get("table") or {}
    complete_rows = int(table.get("complete_rows", 0))
    gates = {
        "official_lookup_retrieved": bool(retrieval.get("retrieved")),
        "at_least_50_unique_rows": int(table.get("unique_raw_rows", 0)) >= 50,
        "complete_fraction_at_least_0_90": float(table.get("complete_fraction", 0.0)) >= 0.90,
        "at_least_50_complete_rows": complete_rows >= 50,
    }
    if reconstruction is None:
        gates.update(
            {
                "all_ls_residuals_at_most_0_001deg": False,
                "median_absolute_timestamp_shift_at_most_1h": False,
                "p95_absolute_timestamp_shift_at_most_12h": False,
                "maximum_absolute_timestamp_shift_at_most_72h": False,
                "no_calendar_year_changes": False,
                "finite_orbit_fraction_at_least_0_95": False,
                "bound_orbit_fraction_at_least_0_90": False,
            }
        )
        return gates
    gates.update(
        {
            "all_ls_residuals_at_most_0_001deg": reconstruction["maximum_absolute_solar_longitude_residual_deg"] <= 0.001,
            "median_absolute_timestamp_shift_at_most_1h": reconstruction["median_absolute_timestamp_shift_hours"] <= 1.0,
            "p95_absolute_timestamp_shift_at_most_12h": reconstruction["p95_absolute_timestamp_shift_hours"] <= 12.0,
            "maximum_absolute_timestamp_shift_at_most_72h": reconstruction["maximum_absolute_timestamp_shift_hours"] <= 72.0,
            "no_calendar_year_changes": reconstruction["calendar_year_changes"] == 0,
            "finite_orbit_fraction_at_least_0_95": reconstruction["finite_orbit_fraction"] >= 0.95,
            "bound_orbit_fraction_at_least_0_90": reconstruction["bound_orbit_fraction"] >= 0.90,
        }
    )
    return gates


def aggregate_panel(control_results: list[dict[str, Any]]) -> dict[str, Any]:
    evaluable = [result for result in control_results if result["evaluable"]]
    d_values = np.array(
        [float(result["reconstruction"]["comparison"]["d_sh"]) for result in evaluable],
        dtype=float,
    )
    strata = sorted({result["control"]["stratum"] for result in control_results})
    evaluable_by_stratum = {
        stratum: sum(
            result["evaluable"] and result["control"]["stratum"] == stratum
            for result in control_results
        )
        for stratum in strata
    }
    passes_by_stratum = {
        stratum: sum(
            result["evaluable"]
            and result["control"]["stratum"] == stratum
            and result["reconstruction"]["comparison"]["d_sh"] <= 0.08
            for result in control_results
        )
        for stratum in strata
    }
    reconstruction_passes = sum(
        result["evaluable"] and result["reconstruction"]["comparison"]["d_sh"] <= 0.08
        for result in control_results
    )
    comparisons = [result["reconstruction"]["comparison"] for result in evaluable]

    def metric_median(key: str) -> float:
        return float(np.median([float(comparison[key]) for comparison in comparisons])) if comparisons else math.inf

    metrics = {
        "frozen_controls": len(control_results),
        "lookups_retrieved": sum(bool(result["retrieval"]["retrieved"]) for result in control_results),
        "evaluable_controls": len(evaluable),
        "evaluable_by_stratum": evaluable_by_stratum,
        "d_sh_passes_at_0_08": reconstruction_passes,
        "d_sh_passes_by_stratum": passes_by_stratum,
        "median_d_sh": float(np.median(d_values)) if len(d_values) else math.inf,
        "p90_d_sh": float(np.quantile(d_values, 0.90)) if len(d_values) else math.inf,
        "maximum_d_sh": float(np.max(d_values)) if len(d_values) else math.inf,
        "median_q_delta_au": metric_median("q_delta_au"),
        "median_e_delta": metric_median("e_delta"),
        "median_inc_delta_deg": metric_median("inc_delta_deg"),
        "median_peri_delta_deg": metric_median("peri_delta_deg"),
        "median_node_delta_deg": metric_median("node_delta_deg"),
    }
    gates = {
        "all_12_lookups_retrieved": metrics["lookups_retrieved"] == 12,
        "at_least_10_evaluable_controls": metrics["evaluable_controls"] >= 10,
        "at_least_2_evaluable_per_stratum": all(value >= 2 for value in evaluable_by_stratum.values()),
        "at_least_9_of_12_d_sh_at_most_0_08": reconstruction_passes >= 9,
        "at_least_2_d_sh_passes_per_stratum": all(value >= 2 for value in passes_by_stratum.values()),
        "median_d_sh_at_most_0_04": metrics["median_d_sh"] <= 0.04,
        "p90_d_sh_at_most_0_10": metrics["p90_d_sh"] <= 0.10,
        "no_evaluable_d_sh_above_0_20": metrics["maximum_d_sh"] <= 0.20,
        "median_q_delta_at_most_0_03au": metrics["median_q_delta_au"] <= 0.03,
        "median_e_delta_at_most_0_05": metrics["median_e_delta"] <= 0.05,
        "median_inc_delta_at_most_3deg": metrics["median_inc_delta_deg"] <= 3.0,
        "median_peri_delta_at_most_5deg": metrics["median_peri_delta_deg"] <= 5.0,
        "median_node_delta_at_most_1deg": metrics["median_node_delta_deg"] <= 1.0,
    }
    return {"metrics": metrics, "gates": gates, "verdict": VERDICT_PASS if all(gates.values()) else VERDICT_FAIL}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    controls = manifest["controls"]
    if len(controls) != 12:
        raise RuntimeError(f"Expected 12 frozen controls, found {len(controls)}")
    args.output.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    for control in controls:
        rows, retrieval = retrieve_lookup(control, args.output / "lookups")
        reconstruction: dict[str, Any] | None = None
        reconstruction_error: str | None = None
        if rows is not None:
            try:
                reconstructed_rows, reconstruction = reconstruct_control(rows, control["target"])
                write_reconstructed_rows(
                    args.output / "controls" / f"{control['code']}_{control['solution']}_reconstructed.csv",
                    reconstructed_rows,
                )
            except Exception as exc:
                reconstruction_error = f"{type(exc).__name__}: {exc}"
        gates = control_gates(retrieval, reconstruction)
        evaluable = all(gates.values())
        results.append(
            {
                "control": control,
                "retrieval": retrieval,
                "reconstruction": reconstruction,
                "reconstruction_error": reconstruction_error,
                "gates": gates,
                "evaluable": evaluable,
            }
        )
        (args.output / "partial_results.json").write_text(
            json.dumps(results, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )

    panel = aggregate_panel(results)
    payload = {
        "schema_version": 1,
        "manifest": manifest,
        "control_results": results,
        "panel": panel,
    }
    (args.output / "control_calibration.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# LS-reconciled nominal-orbit reconstruction control calibration",
        "",
        f"- frozen controls: **{panel['metrics']['frozen_controls']}**",
        f"- official lookups retrieved: **{panel['metrics']['lookups_retrieved']}**",
        f"- evaluable controls: **{panel['metrics']['evaluable_controls']}**",
        f"- D_SH passes at 0.08: **{panel['metrics']['d_sh_passes_at_0_08']} / 12**",
        f"- median D_SH: **{panel['metrics']['median_d_sh']:.6f}**",
        f"- p90 D_SH: **{panel['metrics']['p90_d_sh']:.6f}**",
        f"- maximum evaluable D_SH: **{panel['metrics']['maximum_d_sh']:.6f}**",
        "",
        "## Controls",
        "",
    ]
    for result in results:
        control = result["control"]
        reconstruction = result["reconstruction"]
        d_value = reconstruction["comparison"]["d_sh"] if reconstruction else math.nan
        lines.append(
            f"- `{control['code']}_{control['solution']}` ({control['stratum']}): "
            f"retrieved={'yes' if result['retrieval']['retrieved'] else 'no'}, "
            f"evaluable={'yes' if result['evaluable'] else 'no'}, D_SH={d_value:.6f}"
        )
        if result["reconstruction_error"]:
            lines.append(f"  - reconstruction error: `{result['reconstruction_error']}`")
        failed = [name for name, passed in result["gates"].items() if not passed]
        if failed:
            lines.append("  - failed gates: " + ", ".join(f"`{name}`" for name in failed))
    lines.extend(["", "## Panel gates", ""])
    lines.extend(
        f"- {'PASS' if passed else 'FAIL'} — `{name}`"
        for name, passed in panel["gates"].items()
    )
    lines.extend(["", f"Verdict: **{panel['verdict']}**", ""])
    report = "\n".join(lines)
    (args.output / "CONTROL_CALIBRATION_REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
