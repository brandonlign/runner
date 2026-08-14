#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import urllib.parse
import urllib.request
from pathlib import Path

ENDPOINT = "https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync"
TABLE = "J/A+A/667/A157/catalog"
EXPECTED_ROWS = 824
EXPECTED_COLUMNS = ["Code", "Obs.date", "Lsun"]
YEARS = (2017, 2018)
BLIND = (20.0, 55.0)
QUERY = 'SELECT Code, "Obs.date", Lsun FROM "J/A+A/667/A157/catalog"'
YEAR_RE = re.compile(r"^(2017|2018)(?:-|$)")


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def query_csv() -> bytes:
    # The only live event query this program can issue is the frozen blind-index projection.
    require(QUERY == 'SELECT Code, "Obs.date", Lsun FROM "J/A+A/667/A157/catalog"', "Stage-1 ADQL changed")
    forbidden = ("Lgeo-Lsun", "Bgeo", "Vgeo", "Shower", "Object", "RAgeo", "DEgeo", "Vinf")
    require(all(x not in QUERY for x in forbidden), "Stage-1 query contains forbidden scientific column")
    body = urllib.parse.urlencode(
        {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": QUERY}
    ).encode("ascii")
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "OrbitTrace-EFN-stage1-blind/1"},
    )
    with urllib.request.urlopen(req, timeout=90) as response:
        return response.read()


def parse_year(value: str) -> int:
    s = str(value).strip()
    m = YEAR_RE.match(s)
    require(m is not None, f"unexpected Obs.date year encoding: {s!r}")
    return int(m.group(1))


def main() -> int:
    raw = query_csv()
    raw_sha = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    require(reader.fieldnames == EXPECTED_COLUMNS, f"Stage-1 returned wrong columns: {reader.fieldnames}")

    retained: dict[int, list[str]] = {2017: [], 2018: []}
    total_by_year = {2017: 0, 2018: 0}
    excluded_by_year = {2017: 0, 2018: 0}
    seen: set[str] = set()
    row_count = 0

    for row in reader:
        row_count += 1
        require(set(row) == set(EXPECTED_COLUMNS), "Stage-1 row schema changed")
        code = str(row["Code"]).strip()
        require(code and code not in seen, f"blank/duplicate EFN Code: {code!r}")
        seen.add(code)
        year = parse_year(row["Obs.date"])
        total_by_year[year] += 1
        sol = float(row["Lsun"])
        require(math.isfinite(sol) and 0.0 <= sol < 360.0, f"invalid EFN Lsun for {code}")
        if BLIND[0] <= sol <= BLIND[1]:
            excluded_by_year[year] += 1
        else:
            retained[year].append(code)

    require(row_count == EXPECTED_ROWS, f"expected fixed 824-row EFN release, got {row_count}")
    require(len(seen) == EXPECTED_ROWS, "EFN Code uniqueness changed")
    require(all(total_by_year[y] > 0 for y in YEARS), f"one frozen EFN year is empty: {total_by_year}")

    out = Path("orbittrace_recurrent_eom_efn_2017_2018_external_v1/output/stage1")
    out.mkdir(parents=True, exist_ok=True)
    retained_sha: dict[str, str] = {}
    retained_counts: dict[str, int] = {}
    for year in YEARS:
        ids = sorted(retained[year])
        data = ("\n".join(ids) + "\n").encode("utf-8")
        (out / f"EFN_{year}_RETAINED_IDS.txt").write_bytes(data)
        retained_sha[str(year)] = hashlib.sha256(data).hexdigest()
        retained_counts[str(year)] = len(ids)

    result = {
        "verdict": "PASS_RECURRENT_EOM_EFN_STAGE1_BLIND_RECEIPT",
        "scientific_role": "PRISTINE_EXTERNAL_EFN_2017_2018_STAGE1_BLIND_INDEX_ONLY",
        "catalogue": "J/A+A/667/A157",
        "table_name": TABLE,
        "catalogue_rows_expected": EXPECTED_ROWS,
        "rows_received": row_count,
        "years": [2017, 2018],
        "rows_by_year": {str(y): total_by_year[y] for y in YEARS},
        "excluded_rows_by_year": {str(y): excluded_by_year[y] for y in YEARS},
        "retained_rows_by_year": retained_counts,
        "retained_ids_sha256": retained_sha,
        "blind_index_response_sha256": raw_sha,
        "selected_columns": EXPECTED_COLUMNS,
        "blind_exclusion": [20.0, 55.0],
        "raw_response_persisted": False,
        "geometry_returned": False,
        "shower_labels_returned": False,
        "orbit_fields_returned": False,
        "target_information_access": False,
        "target_region_physical_values_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "orbittrace_target_access": False,
    }
    (out / "STAGE1_BLIND_RECEIPT.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": result["verdict"],
        "rows_received": row_count,
        "rows_by_year": result["rows_by_year"],
        "excluded_rows_by_year": result["excluded_rows_by_year"],
        "retained_rows_by_year": retained_counts,
        "retained_ids_sha256": retained_sha,
        "blind_index_response_sha256": raw_sha,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
