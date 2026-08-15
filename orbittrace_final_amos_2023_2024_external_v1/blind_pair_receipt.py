#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from datetime import datetime
from pathlib import Path

EXPECTED = ["event_id", "utc_time", "solar_longitude_deg"]
YEARS = (2023, 2024)


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def parse_ids(path: Path, year: int) -> set[str]:
    ids: set[str] = set()
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        need(r.fieldnames == EXPECTED, f"wrong Stage-1 header for {year}")
        for row in r:
            eid = row["event_id"].strip()
            need(bool(eid), f"blank event_id in {year}")
            need(eid not in ids, f"duplicate event_id within {year}: {eid}")
            ids.add(eid)
            ts = datetime.fromisoformat(row["utc_time"].strip().replace("Z", "+00:00"))
            need(ts.year == year, f"wrong-year timestamp in {year}: {eid}")
    need(bool(ids), f"empty Stage-1 index for {year}")
    return ids


def retained(path: Path) -> set[str]:
    return {x.strip() for x in path.read_text(encoding="utf-8").splitlines() if x.strip()}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--index-2023", type=Path, required=True)
    p.add_argument("--index-2024", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    ids23 = parse_ids(a.index_2023, 2023)
    ids24 = parse_ids(a.index_2024, 2024)
    overlap = ids23 & ids24
    need(not overlap, f"event_id reused across AMOS years: {sorted(overlap)[:3]}")

    receipt = Path(__file__).with_name("blind_receipt.py")
    for year, index in ((2023, a.index_2023), (2024, a.index_2024)):
        subprocess.run(
            [
                sys.executable,
                str(receipt),
                "--index",
                str(index),
                "--year",
                str(year),
                "--output",
                str(a.output),
            ],
            check=True,
        )

    kept23 = retained(a.output / "AMOS_2023_RETAINED_IDS.txt")
    kept24 = retained(a.output / "AMOS_2024_RETAINED_IDS.txt")
    need(not (kept23 & kept24), "retained ID sets overlap across years")
    need(kept23 <= ids23 and kept24 <= ids24, "receipt emitted unknown ID")

    print("PASS_FINAL_AMOS_PAIR_BLIND_RECEIPT_V1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
