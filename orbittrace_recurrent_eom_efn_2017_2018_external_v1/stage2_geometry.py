#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
SELECT_COLUMNS = 'Code, "Obs.date", Lsun, "Lgeo-Lsun", Bgeo, Vgeo'
QUERY_COLUMNS = ["Code", "Obs.date", "Lsun", "Lgeo-Lsun", "Bgeo", "Vgeo"]
RETURNED_COLUMNS = ["Code", "Obs_date", "Lsun", "Lgeo_Lsun", "Bgeo", "Vgeo"]
YEARS = (2017, 2018)
BLIND = (20.0, 55.0)
INTEGER_RE = re.compile(r"^[0-9]+$")
DATE_ENCODING = "VIZIER_SEC_PER_2000"
SOLAR_LONGITUDE_NORMALIZATION = "raw_Lsun % 360.0 per promoted recurrent-EOM normalize_event"
QUERY_BATCH_SIZE = 150
SEC_2017 = 536544000
SEC_2018 = 568080000
SEC_2019 = 599616000


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def parse_year(value: str) -> int:
    s = str(value).strip()
    require(bool(INTEGER_RE.fullmatch(s)), f"unexpected Obs.date sec/2000 encoding: {s!r}")
    seconds = int(s)
    if SEC_2017 <= seconds < SEC_2018:
        return 2017
    if SEC_2018 <= seconds < SEC_2019:
        return 2018
    raise RuntimeError(f"Obs.date sec/2000 outside frozen 2017/2018 domain: {seconds}")


def canonical_solar_longitude(value: str, code: str) -> tuple[float, bool]:
    raw = float(value)
    require(math.isfinite(raw), f"nonfinite EFN Lsun for {code}")
    canonical = raw % 360.0
    require(0.0 <= canonical < 360.0, f"canonical EFN Lsun outside [0,360) for {code}")
    return canonical, not (0.0 <= raw < 360.0)


def finite(value: str, field: str, code: str) -> float:
    x = float(value)
    require(math.isfinite(x), f"nonfinite EFN {field} for {code}")
    return x


def load_ids(path: Path) -> list[str]:
    ids = path.read_text(encoding="utf-8").splitlines()
    require(ids and ids == sorted(ids) and len(ids) == len(set(ids)) and all(ids), f"invalid retained-ID allowlist {path}")
    return ids


def verify_stage1(stage1: Path, ids17_path: Path, ids18_path: Path) -> tuple[dict, dict[int, list[str]]]:
    r = json.loads(stage1.read_text(encoding="utf-8"))
    require(r["verdict"] == "PASS_RECURRENT_EOM_EFN_STAGE1_BLIND_RECEIPT", "Stage 1 did not pass")
    require(r["scientific_role"] == "PRISTINE_EXTERNAL_EFN_2017_2018_STAGE1_BLIND_INDEX_ONLY", "wrong Stage-1 role")
    require(r["catalogue"] == "J/A+A/667/A157" and r["rows_received"] == 824, "wrong Stage-1 catalogue/cohort")
    require(r["years"] == [2017, 2018] and r["blind_exclusion"] == [20.0, 55.0], "Stage-1 year/blind contract changed")
    require(r["solar_longitude_normalization"] == SOLAR_LONGITUDE_NORMALIZATION, "Stage-1 solar normalization changed")
    require(r["blind_exclusion_applied_after_modulo_normalization"] is True, "Stage-1 blind ordering changed")
    require(r["raw_response_persisted"] is False and r["solar_longitude_values_persisted"] is False, "Stage-1 unsafe persistence")
    require(r["geometry_returned"] is False and r["shower_labels_returned"] is False and r["orbit_fields_returned"] is False, "Stage-1 exposed forbidden fields")
    ids_by_year = {2017: load_ids(ids17_path), 2018: load_ids(ids18_path)}
    for y, path in ((2017, ids17_path), (2018, ids18_path)):
        require(len(ids_by_year[y]) == int(r["retained_rows_by_year"][str(y)]), f"Stage-1 retained count mismatch {y}")
        require(sha_file(path) == str(r["retained_ids_sha256"][str(y)]), f"Stage-1 retained hash mismatch {y}")
    require(set(ids_by_year[2017]).isdisjoint(ids_by_year[2018]), "retained Code reused across years")
    return r, ids_by_year


def quote_adql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def build_query(ids: list[str]) -> str:
    require(ids and len(ids) <= QUERY_BATCH_SIZE, "invalid Stage-2 query batch size")
    id_sql = ",".join(quote_adql_string(x) for x in ids)
    query = f'SELECT {SELECT_COLUMNS} FROM "{TABLE}" WHERE Code IN ({id_sql})'
    require("Shower" not in query and "Object" not in query, "truth-bearing EFN field entered Stage 2")
    require("Lsun <" not in query and "Lsun >" not in query, "raw-longitude Stage-2 filter reintroduced")
    return query


def query_batch(ids: list[str]) -> bytes:
    query = build_query(ids)
    body = urllib.parse.urlencode({"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": query}).encode("ascii")
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "OrbitTrace-EFN-stage2-retained-geometry/1"},
    )
    with urllib.request.urlopen(req, timeout=90) as response:
        return response.read()


def iter_returned_rows(expected_ids: list[str]):
    for start in range(0, len(expected_ids), QUERY_BATCH_SIZE):
        batch = expected_ids[start : start + QUERY_BATCH_SIZE]
        raw = query_batch(batch)
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        require(reader.fieldnames == RETURNED_COLUMNS, f"Stage-2 returned wrong columns: {reader.fieldnames}")
        batch_seen: set[str] = set()
        for row in reader:
            require(set(row) == set(RETURNED_COLUMNS), "Stage-2 row schema changed")
            code = str(row["Code"]).strip()
            require(code in set(batch) and code not in batch_seen, f"Stage-2 batch returned nonrequested/duplicate Code: {code!r}")
            batch_seen.add(code)
            yield row
        require(batch_seen == set(batch), f"Stage-2 batch retained-set mismatch: missing={len(set(batch)-batch_seen)} extra={len(batch_seen-set(batch))}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--stage1-result", type=Path, required=True)
    p.add_argument("--ids-2017", type=Path, required=True)
    p.add_argument("--ids-2018", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    stage1, ids_by_year = verify_stage1(a.stage1_result, a.ids_2017, a.ids_2018)
    expected_ids = sorted(ids_by_year[2017] + ids_by_year[2018])
    expected_union = set(expected_ids)

    rows_by_year: dict[int, list[dict]] = {2017: [], 2018: []}
    seen: set[str] = set()
    modulo_wrapped_by_year = {2017: 0, 2018: 0}
    ids_sets = {y: set(ids_by_year[y]) for y in YEARS}
    for row in iter_returned_rows(expected_ids):
        code = str(row["Code"]).strip()
        require(code and code in expected_union and code not in seen, f"Stage-2 Code not retained/unique: {code!r}")
        seen.add(code)
        year = parse_year(row["Obs_date"])
        require(code in ids_sets[year], f"Stage-2 Code/year mismatch: {code} -> {year}")
        sol, wrapped = canonical_solar_longitude(row["Lsun"], code)
        require(not (BLIND[0] <= sol <= BLIND[1]), f"protected EFN row reached Stage 2: {code}")
        if wrapped:
            modulo_wrapped_by_year[year] += 1
        lon = finite(row["Lgeo_Lsun"], "Lgeo-Lsun", code)
        lat = finite(row["Bgeo"], "Bgeo", code)
        vg = finite(row["Vgeo"], "Vgeo", code)
        require(-90.0 <= lat <= 90.0, f"invalid EFN Bgeo for {code}")
        require(vg > 0.0, f"nonpositive EFN Vgeo for {code}")
        rows_by_year[year].append({"id": code, "year": year, "sol": sol, "sun_lon": lon, "ecl_lat": lat, "vg": vg, "iau": 0, "complex_key": "HIDDEN"})

    require(seen == expected_union, f"Stage-2 retained set mismatch: missing={len(expected_union-seen)} extra={len(seen-expected_union)}")
    for y in YEARS:
        rows_by_year[y].sort(key=lambda r: r["id"])
        require([r["id"] for r in rows_by_year[y]] == ids_by_year[y], f"Stage-2 deterministic ID order mismatch {y}")

    a.output.mkdir(parents=True, exist_ok=True)
    geometry_sha: dict[str, str] = {}
    for y in YEARS:
        data = (json.dumps(rows_by_year[y], separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
        path = a.output / f"EFN_{y}_CANONICAL_GEOMETRY.json"
        path.write_bytes(data)
        geometry_sha[str(y)] = sha_bytes(data)

    result = {
        "verdict": "PASS_RECURRENT_EOM_EFN_STAGE2_RETAINED_NATIVE_GEOMETRY",
        "scientific_role": "PRISTINE_EXTERNAL_EFN_2017_2018_STAGE2_RETAINED_GEOMETRY_ONLY",
        "catalogue": "J/A+A/667/A157",
        "years": [2017, 2018],
        "stage1_result_sha256": sha_file(a.stage1_result),
        "stage1_retained_ids_sha256": {str(y): stage1["retained_ids_sha256"][str(y)] for y in YEARS},
        "rows_by_year": {str(y): len(rows_by_year[y]) for y in YEARS},
        "canonical_geometry_sha256": geometry_sha,
        "query_columns": QUERY_COLUMNS,
        "returned_columns": RETURNED_COLUMNS,
        "server_side_access_restriction": "frozen Stage-1 retained-ID allowlist only",
        "query_batch_size": QUERY_BATCH_SIZE,
        "solar_longitude_normalization": SOLAR_LONGITUDE_NORMALIZATION,
        "modulo_wrapped_rows_by_year": {str(y): modulo_wrapped_by_year[y] for y in YEARS},
        "blind_exclusion": [20.0, 55.0],
        "blind_exclusion_asserted_after_modulo_normalization": True,
        "native_mapping": {"sol": "Lsun % 360.0", "sun_lon": "Lgeo-Lsun", "ecl_lat": "Bgeo", "vg": "Vgeo"},
        "quality_filter_used": False,
        "survey_calibration_used": False,
        "labels_accessed": False,
        "shower_column_returned": False,
        "orbit_fields_returned": False,
        "target_region_physical_values_accessed": False,
        "target_information_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "orbittrace_target_access": False,
    }
    (a.output / "STAGE2_RETAINED_GEOMETRY.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": result["verdict"], "rows_by_year": result["rows_by_year"], "canonical_geometry_sha256": geometry_sha, "modulo_wrapped_rows_by_year": result["modulo_wrapped_rows_by_year"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
