#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ADAPTER = HERE / "adapter"
if str(ADAPTER) not in sys.path:
    sys.path.insert(0, str(ADAPTER))

from transform import canonical_geometry  # noqa: E402
from orbittrace_recurrent_eom_hdbscan_v1.run_development import geo_matrix  # noqa: E402


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def expected_geo6(sol: float, sun_lon: float, ecl_lat: float, vg: float) -> np.ndarray:
    sr = math.radians(sol)
    lr = math.radians(sun_lon)
    br = math.radians(ecl_lat)
    return np.asarray(
        [
            math.cos(sr),
            math.sin(sr),
            math.sin(lr) * math.cos(br),
            math.cos(lr) * math.cos(br),
            math.sin(br),
            vg / 72.0,
        ],
        dtype=float,
    )


def csv(path: Path, header: str, rows: list[str]) -> None:
    path.write_text(header + "\n" + "\n".join(rows) + "\n", encoding="utf-8")


def main() -> int:
    # Synthetic geometry only. These values are invented and are not AMOS observations.
    cases = [
        (10.0, 0.0, 0.0, 36.0),
        (120.0, 90.0, 0.0, 48.0),
        (300.0, 271.25, -21.5, 61.25),
        (359.5, 42.75, 67.0, 19.0),
    ]
    canonical = [canonical_geometry(*x) for x in cases]
    events = [
        {"id": f"SYN{i}", "year": 2023 + (i % 2), "sol": sol, "lon": lon, "lat": lat, "vg": vg}
        for i, (sol, lon, lat, vg) in enumerate(canonical)
    ]
    got = geo_matrix(events)
    expected = np.vstack([expected_geo6(sol, lon, lat, vg) for sol, lon, lat, vg in canonical])
    require(np.array_equal(got, expected), "AMOS canonical coordinates do not map exactly to promoted GEO6 arithmetic")

    # End-to-end synthetic receipt: protected index row exists, but its geometry is never supplied/opened.
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        index = td / "index.csv"
        geometry = td / "geometry.csv"
        output = td / "canonical.json"
        csv(
            index,
            "event_id,utc_time,solar_longitude_deg",
            [
                "KEEP_A,2023-01-10T00:00:00Z,10.0",
                "PROTECTED,2023-02-10T00:00:00Z,30.0",
                "KEEP_B,2023-08-10T00:00:00Z,120.0",
            ],
        )
        csv(
            geometry,
            "event_id,ra_j2000_deg,dec_j2000_deg,vg_km_s",
            [
                "KEEP_A,0.0,0.0,36.0",
                "KEEP_B,90.0,0.0,48.0",
            ],
        )
        subprocess.run(
            [sys.executable, str(ADAPTER / "adapt.py"), "--index", str(index), "--geometry", str(geometry), "--year", "2023", "--output", str(output)],
            check=True,
            capture_output=True,
            text=True,
        )
        rows = json.loads(output.read_text(encoding="utf-8"))
        require([r["id"] for r in rows] == ["KEEP_A", "KEEP_B"], "protected synthetic ID survived adapter")
        require(all(r["complex_key"] == "HIDDEN" and int(r["iau"]) == 0 for r in rows), "adapter exposed label state")
        for r in rows:
            require(not (20.0 <= float(r["sol"]) <= 55.0), "protected synthetic longitude survived adapter")

        # The exact adapter must fail closed if physical geometry contains a non-retained/protected ID.
        bad_geometry = td / "bad_geometry.csv"
        csv(
            bad_geometry,
            "event_id,ra_j2000_deg,dec_j2000_deg,vg_km_s",
            [
                "KEEP_A,0.0,0.0,36.0",
                "PROTECTED,10.0,10.0,40.0",
                "KEEP_B,90.0,0.0,48.0",
            ],
        )
        bad = subprocess.run(
            [sys.executable, str(ADAPTER / "adapt.py"), "--index", str(index), "--geometry", str(bad_geometry), "--year", "2023", "--output", str(td / "bad.json")],
            check=False,
            capture_output=True,
            text=True,
        )
        require(bad.returncode != 0, "adapter did not fail closed on protected/non-retained geometry ID")

    out = {
        "verdict": "PASS_RECURRENT_EOM_AMOS_2023_2024_PRE_DATA_MAPPING_AUDIT",
        "synthetic_only": True,
        "amos_event_rows_accessed": False,
        "amos_labels_accessed": False,
        "amos_orbit_elements_accessed": False,
        "geo6_exact_array_identity": True,
        "protected_geometry_fail_closed": True,
        "years_frozen": [2023, 2024],
        "blind_exclusion": [20.0, 55.0],
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "orbittrace_target_access": False,
    }
    out_dir = HERE / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "PRE_DATA_MAPPING_AUDIT.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
