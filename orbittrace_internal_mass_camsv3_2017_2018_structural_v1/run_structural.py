#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

BASE = "https://ceres.ta3.sk/iaumdcdb/dataDBs/video_offline"
YEARS = (2017, 2018)
REQUIRED = {"Yr", "Mn", "Dayy", "LS", "RA", "DECL", "Vg"}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_name(name: str) -> bool:
    p = PurePosixPath(name)
    return not p.is_absolute() and ".." not in p.parts and not name.startswith(("/", "\\"))


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "OrbitTrace-CAMSv3-structural/1.0"})
    with urllib.request.urlopen(request, timeout=300) as response:
        return response.read()


def audit_year(year: int) -> dict:
    expected = f"iaumdcCAMSv3_{year}.csv"
    url = f"{BASE}/{expected}.zip"
    raw = fetch(url)
    req(raw[:4] == b"PK\x03\x04", f"{year}: official payload is not ZIP")
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        bad = zf.testzip()
        names = zf.namelist()
        safe_paths = all(safe_name(name) for name in names)
        matches = [name for name in names if name.lower().endswith(".csv") and PurePosixPath(name).name == expected]
        req(len(matches) == 1, f"{year}: expected one {expected}; members={names}")
        member = matches[0]
        data = zf.read(member)

    # Structural-only: read header text, then only count row widths. No data-row
    # cell is interpreted, converted, compared, logged, hashed, or selected on.
    text = io.TextIOWrapper(io.BytesIO(data), encoding="utf-8-sig", newline="")
    reader = csv.reader(text, delimiter=";")
    try:
        header = next(reader)
    except StopIteration as exc:
        raise RuntimeError(f"{year}: empty CSV") from exc
    header = [x.lstrip("\ufeff").strip() for x in header]
    row_count = 0
    malformed = 0
    for row in reader:
        if not row or not any(cell.strip() for cell in row):
            continue
        row_count += 1
        malformed += int(len(row) != len(header))

    gates = {
        "zip_crc": bad is None,
        "safe_paths": safe_paths,
        "exactly_one_expected_basename": True,
        "unique_nonempty_header": bool(header) and all(header) and len(set(header)) == len(header),
        "required_structural_fields": REQUIRED.issubset(set(header)),
        "nonempty_data_rows": row_count > 0,
        "zero_row_width_mismatches": malformed == 0,
    }
    return {
        "year": year,
        "url": url,
        "archive_bytes": len(raw),
        "archive_sha256": sha256(raw),
        "member_path": member,
        "member_basename": PurePosixPath(member).name,
        "member_bytes": len(data),
        "header": header,
        "header_count": len(header),
        "row_count": row_count,
        "malformed_rows": malformed,
        "gates": gates,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    years = [audit_year(y) for y in YEARS]
    identical = years[0]["header"] == years[1]["header"]
    gates = {
        "both_years_pass_individual_structural_gates": all(all(x["gates"].values()) for x in years),
        "identical_header_2017_2018": identical,
        "exact_year_pair": [x["year"] for x in years] == [2017, 2018],
        "meteor_row_values_interpreted": False,
        "label_values_read": False,
    }
    verdict = "PASS_CAMSV3_2017_2018_STRUCTURAL_TRANSPORT_V1" if (
        gates["both_years_pass_individual_structural_gates"]
        and gates["identical_header_2017_2018"]
        and gates["exact_year_pair"]
        and not gates["meteor_row_values_interpreted"]
        and not gates["label_values_read"]
    ) else "FAIL_CAMSV3_2017_2018_STRUCTURAL_TRANSPORT_V1"
    result = {
        "schema": "ORBITTRACE_CAMSV3_2017_2018_STRUCTURAL_TRANSPORT_V1",
        "scientific_role": "STRUCTURAL_TRANSPORT_ONLY_PRE_SCIENCE",
        "verdict": verdict,
        "freshness_audit_run": 31204903047,
        "freshness_audit_artifact": 9004313104,
        "years": years,
        "canonical_header": years[0]["header"],
        "gates": gates,
        "catalogue_values_accessed": False,
        "scientific_values_read": False,
        "label_values_read": False,
        "target_information_access": False,
        "method_executed": False,
        "comparator_executed": False,
    }
    path = a.output / "CAMSV3_2017_2018_STRUCTURAL_TRANSPORT_V1.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": verdict, "gates": gates, "years": [{k:v for k,v in x.items() if k not in {"header"}} for x in years]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
