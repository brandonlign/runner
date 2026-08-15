#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def run(args: list[str], *, expect_ok: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    p = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    if expect_ok and p.returncode != 0:
        raise RuntimeError(f"command failed: {args}\nstdout={p.stdout}\nstderr={p.stderr}")
    if not expect_ok and p.returncode == 0:
        raise RuntimeError(f"command unexpectedly succeeded: {args}")
    return p


def main() -> int:
    freeze = json.loads((ROOT / "PREDATA_FREEZE.json").read_text(encoding="utf-8"))
    need(freeze["schema"] == "ORBITTRACE_FINAL_AMOS_2023_2024_PREDATA_FREEZE_V1", "freeze schema changed")
    need(freeze["primary_method"]["binding_head"] == "182f07ade6bb5d4be2c80b88df9216bb2d6eee2d", "selected method changed")
    need(freeze["final_protocol"]["allowed_years"] == [2023, 2024], "AMOS years changed")
    need(freeze["final_protocol"]["protected_solar_longitude_interval_inclusive"] == [20.0, 55.0], "blind interval changed")
    need(freeze["governance"]["amos_event_level_access_authorized_by_this_freeze"] is False, "freeze accidentally authorizes AMOS")
    need(freeze["governance"]["alternate_final_method_after_amos"] is False, "fallback method accidentally authorized")
    need(freeze["governance"]["new_external_survey_rescue"] is False, "external shopping accidentally authorized")

    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        i23 = t / "AMOS_2023_INDEX.csv"
        i24 = t / "AMOS_2024_INDEX.csv"
        out = t / "receipt"
        header = ["event_id", "utc_time", "solar_longitude_deg"]
        write_csv(
            i23,
            header,
            [
                ["a23", "2023-01-01T00:00:00Z", 19.999],
                ["b23", "2023-02-01T00:00:00Z", 20.0],
                ["c23", "2023-03-01T00:00:00Z", 37.0],
                ["d23", "2023-04-01T00:00:00Z", 55.0],
                ["e23", "2023-05-01T00:00:00Z", 55.001],
            ],
        )
        write_csv(
            i24,
            header,
            [
                ["a24", "2024-01-01T00:00:00Z", 0.0],
                ["b24", "2024-02-01T00:00:00Z", 20.0],
                ["c24", "2024-03-01T00:00:00Z", 55.0],
                ["d24", "2024-04-01T00:00:00Z", 359.999],
            ],
        )
        run([
            sys.executable,
            str(ROOT / "blind_pair_receipt.py"),
            "--index-2023", str(i23),
            "--index-2024", str(i24),
            "--output", str(out),
        ])
        kept23 = (out / "AMOS_2023_RETAINED_IDS.txt").read_text().splitlines()
        kept24 = (out / "AMOS_2024_RETAINED_IDS.txt").read_text().splitlines()
        need(kept23 == ["a23", "e23"], f"inclusive 2023 blind boundary failed: {kept23}")
        need(kept24 == ["a24", "d24"], f"inclusive 2024 blind boundary failed: {kept24}")

        # Cross-year event IDs must fail before either retained physical layer is accepted.
        i24dup = t / "AMOS_2024_INDEX_DUP.csv"
        write_csv(
            i24dup,
            header,
            [
                ["a23", "2024-01-01T00:00:00Z", 0.0],
                ["z24", "2024-02-01T00:00:00Z", 100.0],
            ],
        )
        run([
            sys.executable,
            str(ROOT / "blind_pair_receipt.py"),
            "--index-2023", str(i23),
            "--index-2024", str(i24dup),
            "--output", str(t / "dupout"),
        ], expect_ok=False)

        # Exact retained-only geometry is accepted and deterministically canonicalized.
        g23 = t / "AMOS_2023_GEOMETRY_RETAINED.csv"
        g24 = t / "AMOS_2024_GEOMETRY_RETAINED.csv"
        gheader = ["event_id", "ra_j2000_deg", "dec_j2000_deg", "vg_km_s"]
        write_csv(g23, gheader, [["a23", 120.0, 20.0, 30.0], ["e23", 250.0, -10.0, 45.0]])
        write_csv(g24, gheader, [["a24", 10.0, 5.0, 25.0], ["d24", 300.0, 40.0, 60.0]])
        env = dict(__import__("os").environ)
        env["PYTHONPATH"] = str(ROOT / "adapter")
        c23 = t / "canonical23.json"
        c24 = t / "canonical24.json"
        for year, index, geom, canonical in ((2023, i23, g23, c23), (2024, i24, g24, c24)):
            run([
                sys.executable,
                str(ROOT / "adapter" / "adapt.py"),
                "--index", str(index),
                "--geometry", str(geom),
                "--year", str(year),
                "--output", str(canonical),
            ], env=env)
            rows = json.loads(canonical.read_text())
            need(len(rows) == 2, f"unexpected canonical row count {year}")
            need(all(set(r) == {"id", "year", "sol", "sun_lon", "ecl_lat", "vg", "iau", "complex_key"} for r in rows), "canonical schema changed")
            need(all(r["iau"] == 0 and r["complex_key"] == "HIDDEN" for r in rows), "truth placeholder changed")

        # A protected/non-retained geometry ID must fail closed.
        badg = t / "bad_geometry.csv"
        write_csv(badg, gheader, [["b23", 120.0, 20.0, 30.0], ["a23", 120.0, 20.0, 30.0], ["e23", 250.0, -10.0, 45.0]])
        run([
            sys.executable,
            str(ROOT / "adapter" / "adapt.py"),
            "--index", str(i23),
            "--geometry", str(badg),
            "--year", "2023",
            "--output", str(t / "bad.json"),
        ], expect_ok=False, env=env)

    result = {
        "verdict": "PASS_ORBITTRACE_FINAL_AMOS_PREDATA_ZERO_DATA_AUDIT_V1",
        "synthetic_only": True,
        "inclusive_20_55_exclusion_verified": True,
        "cross_year_duplicate_id_fail_closed": True,
        "retained_only_geometry_verified": True,
        "protected_geometry_fail_closed": True,
        "primary_method_head": "182f07ade6bb5d4be2c80b88df9216bb2d6eee2d",
        "amos_event_rows_accessed": False,
        "amos_truth_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    out = ROOT / "output"
    out.mkdir(exist_ok=True)
    (out / "PREDATA_ZERO_DATA_AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(result["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
