#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import json
import math
import urllib.parse
import urllib.request
from pathlib import Path

ENDPOINT = "https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync"
QUERY = 'SELECT Code, "Obs.date", Lsun FROM "J/A+A/667/A157/catalog"'
RETURNED_COLUMNS = ["Code", "Obs_date", "Lsun"]
EXPECTED_ROWS = 824


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def query_csv() -> bytes:
    require(QUERY == 'SELECT Code, "Obs.date", Lsun FROM "J/A+A/667/A157/catalog"', "diagnostic ADQL changed")
    for forbidden in ("Lgeo-Lsun", "Bgeo", "Vgeo", "Shower", "Object", "RAgeo", "DEgeo", "Vinf"):
        require(forbidden not in QUERY, f"forbidden diagnostic field in query: {forbidden}")
    body = urllib.parse.urlencode(
        {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": QUERY}
    ).encode("ascii")
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "OrbitTrace-EFN-stage1-lsun-diagnostic/1"},
    )
    with urllib.request.urlopen(req, timeout=90) as response:
        return response.read()


def classify(raw: str) -> tuple[bool, str]:
    s = str(raw).strip()
    try:
        value = float(s)
    except Exception:
        return False, "NON_NUMERIC"
    if not math.isfinite(value):
        return False, "NON_FINITE"
    if value < 0.0:
        return False, "NEGATIVE"
    if value >= 360.0:
        return False, "GE_360"
    return True, "VALID_0_LE_LSUN_LT_360"


def main() -> int:
    raw = query_csv()
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    require(reader.fieldnames == RETURNED_COLUMNS, f"diagnostic returned wrong columns: {reader.fieldnames}")
    seen: set[str] = set()
    invalid: list[dict[str, str]] = []
    rows = 0
    for row in reader:
        rows += 1
        require(set(row) == set(RETURNED_COLUMNS), "diagnostic row schema changed")
        code = str(row["Code"]).strip()
        require(code and code not in seen, f"blank/duplicate EFN Code: {code!r}")
        seen.add(code)
        valid, reason = classify(row["Lsun"])
        if not valid:
            invalid.append({"Code": code, "raw_Lsun": str(row["Lsun"]), "reason": reason})
    require(rows == EXPECTED_ROWS and len(seen) == EXPECTED_ROWS, f"expected 824 unique rows, got rows={rows}, unique={len(seen)}")

    result = {
        "verdict": "PASS_RECURRENT_EOM_EFN_STAGE1_LSUN_TRANSPORT_DIAGNOSTIC",
        "scientific_role": "ENGINEERING_ONLY_STAGE1_BLIND_FIELD_TRANSPORT_DIAGNOSTIC",
        "catalogue": "J/A+A/667/A157",
        "query": QUERY,
        "returned_columns": RETURNED_COLUMNS,
        "rows_received": rows,
        "invalid_lsun_count": len(invalid),
        "invalid_lsun_rows": invalid,
        "valid_stage1_endpoint": False,
        "retained_ids_frozen": False,
        "raw_response_persisted": False,
        "valid_row_lsun_values_persisted": False,
        "geometry_returned": False,
        "shower_labels_returned": False,
        "orbit_fields_returned": False,
        "target_information_access": False,
        "target_region_physical_values_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "orbittrace_target_access": False,
    }
    out = Path("orbittrace_recurrent_eom_efn_2017_2018_external_v1/output/lsun_diagnostic")
    out.mkdir(parents=True, exist_ok=True)
    (out / "STAGE1_LSUN_TRANSPORT_DIAGNOSTIC.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": result["verdict"], "rows_received": rows, "invalid_lsun_count": len(invalid), "invalid_lsun_rows": invalid}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
