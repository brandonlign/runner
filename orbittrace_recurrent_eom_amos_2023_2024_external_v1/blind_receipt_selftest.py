#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECEIPT = HERE / "blind_receipt.py"


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def write_index(path: Path, year: int) -> None:
    rows = [
        (f"Y{year}_A", f"{year}-01-01T00:00:00Z", "0.0"),
        (f"Y{year}_B", f"{year}-02-01T00:00:00Z", "19.999999"),
        (f"Y{year}_P20", f"{year}-03-01T00:00:00Z", "20.0"),
        (f"Y{year}_P30", f"{year}-04-01T00:00:00Z", "30.0"),
        (f"Y{year}_P55", f"{year}-05-01T00:00:00Z", "55.0"),
        (f"Y{year}_C", f"{year}-06-01T00:00:00Z", "55.000001"),
        (f"Y{year}_D", f"{year}-12-31T23:59:59Z", "359.999999"),
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["event_id", "utc_time", "solar_longitude_deg"])
        w.writerows(rows)


def run_receipt(index: Path, year: int, out: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RECEIPT), "--index", str(index), "--year", str(year), "--output", str(out)],
        check=False,
        capture_output=True,
        text=True,
    )


def main() -> int:
    require(hashlib.sha1(RECEIPT.read_bytes()).hexdigest() != "", "receipt source unreadable")
    with tempfile.TemporaryDirectory() as td_raw:
        td = Path(td_raw)
        for year in (2023, 2024):
            index = td / f"index_{year}.csv"
            out = td / f"out_{year}"
            write_index(index, year)
            p = run_receipt(index, year, out)
            require(p.returncode == 0, f"blind receipt failed synthetic {year}: {p.stderr}")
            result = json.loads((out / f"AMOS_{year}_BLIND_RECEIPT.json").read_text(encoding="utf-8"))
            kept = (out / f"AMOS_{year}_RETAINED_IDS.txt").read_text(encoding="utf-8").splitlines()
            expected = [f"Y{year}_A", f"Y{year}_B", f"Y{year}_C", f"Y{year}_D"]
            require(kept == sorted(expected), f"inclusive protected-boundary behavior changed for {year}: {kept}")
            require(result["rows"] == 7 and result["excluded_rows"] == 3 and result["retained_rows"] == 4, f"synthetic counts changed for {year}")
            require(result["protected_interval_inclusive"] == [20.0, 55.0], "protected interval changed")
            require(result["parsed_columns"] == ["event_id", "utc_time", "solar_longitude_deg"], "parsed index schema changed")
            require(result["scientific_values_emitted"] is False and result["labels_opened"] is False, "receipt emitted forbidden scientific state")
            expected_hash = hashlib.sha256(("\n".join(sorted(expected)) + "\n").encode()).hexdigest()
            require(result["retained_ids_sha256"] == expected_hash, "retained-ID hash changed")

        # Wrong-year timestamps must fail closed.
        wrong = td / "wrong_year.csv"
        wrong.write_text("event_id,utc_time,solar_longitude_deg\nBAD,2022-01-01T00:00:00Z,10.0\n", encoding="utf-8")
        require(run_receipt(wrong, 2023, td / "wrong_out").returncode != 0, "wrong-year timestamp did not fail closed")

        # Duplicate IDs must fail closed.
        dup = td / "duplicate.csv"
        dup.write_text("event_id,utc_time,solar_longitude_deg\nDUP,2023-01-01T00:00:00Z,10.0\nDUP,2023-02-01T00:00:00Z,60.0\n", encoding="utf-8")
        require(run_receipt(dup, 2023, td / "dup_out").returncode != 0, "duplicate event ID did not fail closed")

        # Any extra column must fail exact-header validation.
        extra = td / "extra.csv"
        extra.write_text("event_id,utc_time,solar_longitude_deg,ra\nX,2023-01-01T00:00:00Z,10.0,123.0\n", encoding="utf-8")
        require(run_receipt(extra, 2023, td / "extra_out").returncode != 0, "extra scientific column did not fail closed")

    result = {
        "verdict": "PASS_RECURRENT_EOM_AMOS_BLIND_RECEIPT_SYNTHETIC_AUDIT",
        "synthetic_only": True,
        "years_tested": [2023, 2024],
        "protected_interval_inclusive": [20.0, 55.0],
        "boundary_20_excluded": True,
        "boundary_55_excluded": True,
        "wrong_year_fails_closed": True,
        "duplicate_id_fails_closed": True,
        "extra_column_fails_closed": True,
        "amos_event_rows_accessed": False,
        "amos_geometry_accessed": False,
        "amos_labels_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "orbittrace_target_access": False,
    }
    out = HERE / "output"
    out.mkdir(parents=True, exist_ok=True)
    (out / "BLIND_RECEIPT_SYNTHETIC_AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
