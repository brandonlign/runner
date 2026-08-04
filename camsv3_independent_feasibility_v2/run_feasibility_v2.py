#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path, PurePosixPath

import requests

BASE = "https://ceres.ta3.sk/iaumdcdb/dataDBs/video_offline"
FROZEN = {
    2011: ("de2af15ccdee9836912c1efb9fba9bdcf47e3b9d2fa7374244dc6ac69f82c118", "iaumdcCAMSv3_2011.csv", 44_998),
    2012: ("040b853d6fbcd5dfc9ef3f76be553624a9893ab9b1aac709ccebcc2498c73cb3", "iaumdcCAMSv3_2012.csv", 53_401),
    2013: ("895f58c985f730976ef6e3ca3c89cd947bd248b419101eba163eef77e951e56a", "iaumdcCAMSv3_2013.csv", 76_213),
    2014: ("0d9ba75256577e9b008786054ea13c4fa6b755d42ae65031f311bae8a0b3a928", "iaumdcCAMSv3_2014.csv", 83_336),
    2015: ("aa9a04b206e1927d7a8cb401ef22baae20061c9827dec0133e42b11790fcf61d", "iaumdcCAMSv3_2015.csv", 100_700),
    2016: ("40e901fa8c8e017e5fe6bf9e9739a2c840d7e0d259e59b57ccf374d7d9700f30", "iaumdcCAMSv3_2016.csv", 110_352),
}
REQUIRED = {"Yr", "Mn", "Dayy", "LS", "RA", "DECL", "Vg"}


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lstrip("\ufeff").strip().lower())


def safe_name(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts and not name.startswith(("/", "\\"))


def audit_year(year: int) -> dict:
    expected_hash, expected_basename, expected_rows = FROZEN[year]
    url = f"{BASE}/iaumdcCAMSv3_{year}.csv.zip"
    response = requests.get(url, timeout=300)
    response.raise_for_status()
    raw = response.content
    digest = hashlib.sha256(raw).hexdigest()
    gates = {"archive_sha256": digest == expected_hash}

    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        bad = archive.testzip()
        names = archive.namelist()
        gates["zip_crc"] = bad is None
        gates["safe_paths"] = all(safe_name(name) for name in names)
        csv_members = [name for name in names if name.lower().endswith(".csv")]
        matches = [
            name
            for name in csv_members
            if PurePosixPath(name).name == expected_basename
        ]
        gates["exactly_one_pinned_basename"] = len(matches) == 1
        if len(matches) != 1:
            raise RuntimeError(
                f"{year}: expected exactly one {expected_basename!r}; members={names}"
            )
        selected_member = matches[0]
        data = archive.read(selected_member)

    text = io.TextIOWrapper(io.BytesIO(data), encoding="utf-8-sig", newline="")
    reader = csv.reader(text, delimiter=";")
    try:
        header = next(reader)
    except StopIteration as exc:
        raise RuntimeError(f"{year}: empty CSV") from exc
    header = [field.lstrip("\ufeff").strip() for field in header]
    row_count = 0
    malformed = 0
    for row in reader:
        if not row or not any(field.strip() for field in row):
            continue
        row_count += 1
        malformed += int(len(row) != len(header))

    gates.update(
        {
            "unique_nonempty_header": bool(header) and all(header) and len(set(header)) == len(header),
            "required_geometry_fields": REQUIRED.issubset(set(header)),
            "row_count": row_count == expected_rows,
            "zero_malformed_rows": malformed == 0,
        }
    )
    return {
        "year": year,
        "url": url,
        "archive_bytes": len(raw),
        "archive_sha256": digest,
        "member_path": selected_member,
        "member_basename": PurePosixPath(selected_member).name,
        "row_count": row_count,
        "header_count": len(header),
        "header": header,
        "normalized_header": [norm(field) for field in header],
        "malformed_rows": malformed,
        "gates": gates,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    years = [audit_year(year) for year in sorted(FROZEN)]
    canonical_header = years[0]["header"]
    identical = all(item["header"] == canonical_header for item in years)
    all_year_gates = all(all(item["gates"].values()) for item in years)
    gates = {
        "all_six_years_pass_structural_gates": all_year_gates,
        "identical_header_across_years": identical,
        "six_pinned_years_present": [item["year"] for item in years] == sorted(FROZEN),
    }
    verdict = (
        "PASS_CAMSV3_STRUCTURAL_FEASIBILITY_V2"
        if all(gates.values())
        else "KILL_CAMSV3_STRUCTURAL_FEASIBILITY_V2"
    )
    result = {
        "method": "CAMSv3 structural feasibility parser v2 only",
        "years": years,
        "canonical_header": canonical_header,
        "canonical_normalized_header": years[0]["normalized_header"],
        "gates": gates,
        "verdict": verdict,
        "scientific_values_read": False,
        "label_values_read": False,
        "sonotaco_2024_read": False,
        "sole_parser_change": "exact full member path -> exact PurePosixPath basename",
    }
    (out / "camsv3_structural_feasibility_v2.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )

    report = [
        "# CAMSv3 independent-survey structural feasibility v2",
        "",
        f"**Verdict:** `{verdict}`",
        "",
        f"- years: {', '.join(str(y) for y in sorted(FROZEN))}",
        f"- identical header: {identical}",
        f"- header fields: {len(canonical_header)}",
        f"- all structural gates: {all_year_gates}",
        "",
        "## Canonical header",
        "",
        "`" + "`; `".join(canonical_header) + "`",
        "",
        "No data-column or label value was inspected by this gate.",
    ]
    (out / "RESULT.md").write_text("\n".join(report) + "\n")
    print(json.dumps({"verdict": verdict, "gates": gates, "years": years}, indent=2))
    if verdict != "PASS_CAMSV3_STRUCTURAL_FEASIBILITY_V2":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
