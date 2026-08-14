#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
import os
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "stage2_geometry.py"


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def load_module():
    spec = importlib.util.spec_from_file_location("efn_stage2_under_test", SOURCE)
    require(spec is not None and spec.loader is not None, "cannot import Stage-2 source")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_stage1(root: Path) -> tuple[Path, Path, Path, dict[int, list[str]]]:
    ids = {2017: [f"SYN2017_{i:03d}" for i in range(12)], 2018: [f"SYN2018_{i:03d}" for i in range(12)]}
    paths = {}
    hashes = {}
    for year in (2017, 2018):
        p = root / f"EFN_{year}_RETAINED_IDS.txt"
        data = ("\n".join(ids[year]) + "\n").encode()
        p.write_bytes(data)
        paths[year] = p
        hashes[str(year)] = hashlib.sha256(data).hexdigest()
    result = {
        "verdict": "PASS_RECURRENT_EOM_EFN_STAGE1_BLIND_RECEIPT",
        "scientific_role": "PRISTINE_EXTERNAL_EFN_2017_2018_STAGE1_BLIND_INDEX_ONLY",
        "catalogue": "J/A+A/667/A157",
        "rows_received": 824,
        "years": [2017, 2018],
        "retained_rows_by_year": {"2017": 12, "2018": 12},
        "retained_ids_sha256": hashes,
        "blind_exclusion": [20.0, 55.0],
        "solar_longitude_normalization": "raw_Lsun % 360.0 per promoted recurrent-EOM normalize_event",
        "blind_exclusion_applied_after_modulo_normalization": True,
        "raw_response_persisted": False,
        "solar_longitude_values_persisted": False,
        "geometry_returned": False,
        "shower_labels_returned": False,
        "orbit_fields_returned": False,
    }
    stage1 = root / "STAGE1_BLIND_RECEIPT.json"
    stage1.write_text(json.dumps(result, sort_keys=True) + "\n")
    return stage1, paths[2017], paths[2018], ids


def make_rows(ids: dict[int, list[str]], *, protected=False, bad_vg=False, missing=False, extra=False):
    rows = []
    for year in (2017, 2018):
        base = 536544000 if year == 2017 else 568080000
        for i, code in enumerate(ids[year]):
            sol = 361.1739 if i == 0 else 100.0 + i
            if protected and year == 2017 and i == 1:
                sol = 380.0  # canonical protected 20
            row = {
                "Code": code,
                "Obs_date": str(base + i * 1000),
                "Lsun": str(sol),
                "Lgeo-Lsun": str(-40.0 + i * 2.0),
                "Bgeo": str(-15.0 + i),
                "Vgeo": "0.0" if bad_vg and year == 2018 and i == 2 else str(25.0 + i),
            }
            if extra:
                row["Shower"] = "BAD"
            rows.append(row)
    if missing:
        rows = rows[:-1]
    return rows


def csv_for_requested(rows, requested: list[str]) -> bytes:
    wanted = set(requested)
    selected = [r for r in rows if r["Code"] in wanted]
    if rows:
        fields = list(rows[0].keys())
    else:
        fields = ["Code", "Obs_date", "Lsun", "Lgeo-Lsun", "Bgeo", "Vgeo"]
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    for row in selected:
        w.writerow(row)
    return b.getvalue().encode()


def run_case(mod, td: Path, rows, name: str) -> tuple[bool, Path, str]:
    case = td / name
    case.mkdir()
    stage1, ids17, ids18, _ = write_stage1(case)
    out = case / "out"
    mod.query_batch = lambda requested: csv_for_requested(rows, requested)
    old = os.getcwd()
    cap = io.StringIO()
    try:
        os.chdir(case)
        import sys
        old_argv = sys.argv
        sys.argv = [str(SOURCE), "--stage1-result", str(stage1), "--ids-2017", str(ids17), "--ids-2018", str(ids18), "--output", str(out)]
        try:
            with redirect_stdout(cap):
                mod.main()
            ok = True
        except Exception as exc:
            ok = False
            cap.write(f"{type(exc).__name__}: {exc}")
        finally:
            sys.argv = old_argv
    finally:
        os.chdir(old)
    return ok, out, cap.getvalue()


def main() -> int:
    mod = load_module()
    require(mod.QUERY_COLUMNS == ["Code", "Obs.date", "Lsun", "Lgeo-Lsun", "Bgeo", "Vgeo"], "Stage-2 semantic columns changed")
    require(mod.RETURNED_COLUMNS == ["Code", "Obs_date", "Lsun", "Lgeo-Lsun", "Bgeo", "Vgeo"], "Stage-2 returned columns changed")
    require(mod.QUERY_BATCH_SIZE == 150, "Stage-2 deterministic batch size changed")
    q = mod.build_query(["SYN_A", "SYN_B"])
    require("Code IN ('SYN_A','SYN_B')" in q, "Stage-2 query is not retained-ID restricted")
    require("Lsun <" not in q and "Lsun >" not in q, "raw-longitude Stage-2 filter survived")
    require("Shower" not in q and "Object" not in q, "truth-bearing field entered Stage 2")
    require(mod.quote_adql_string("A'B") == "'A''B'", "ADQL string escaping changed")
    for raw, expected in (("360.0466", 0.0466), ("361.1739", 1.1739), ("-0.25", 359.75), ("380", 20.0)):
        sol, wrapped = mod.canonical_solar_longitude(raw, "SYN")
        require(abs(sol - expected) < 1e-12 and wrapped is True, f"Stage-2 generic modulo changed for {raw}")
    for bad in ("nan", "inf", "-inf"):
        try:
            mod.canonical_solar_longitude(bad, "BAD")
        except Exception:
            pass
        else:
            raise RuntimeError(f"Stage-2 nonfinite Lsun did not fail: {bad}")

    with tempfile.TemporaryDirectory() as td_raw:
        td = Path(td_raw)
        seed = td / "seed"; seed.mkdir()
        _, _, _, ids = write_stage1(seed)
        ok, out, text = run_case(mod, td, make_rows(ids), "valid")
        require(ok, f"valid synthetic Stage 2 failed: {text}")
        result = json.loads((out / "STAGE2_RETAINED_GEOMETRY.json").read_text())
        require(result["verdict"] == "PASS_RECURRENT_EOM_EFN_STAGE2_RETAINED_NATIVE_GEOMETRY", "wrong Stage-2 verdict")
        require(result["rows_by_year"] == {"2017": 12, "2018": 12}, "Stage-2 counts changed")
        require(result["returned_columns"] == ["Code", "Obs_date", "Lsun", "Lgeo-Lsun", "Bgeo", "Vgeo"], "literal-hyphen returned-header mapping changed")
        require(result["server_side_access_restriction"] == "frozen Stage-1 retained-ID allowlist only", "Stage-2 access restriction changed")
        require(result["native_mapping"] == {"sol": "Lsun % 360.0", "sun_lon": "Lgeo-Lsun", "ecl_lat": "Bgeo", "vg": "Vgeo"}, "native mapping changed")
        require(result["modulo_wrapped_rows_by_year"] == {"2017": 1, "2018": 1}, "Stage-2 wrap counts changed")
        require(result["labels_accessed"] is False and result["shower_column_returned"] is False and result["orbit_fields_returned"] is False, "Stage 2 exposed truth/orbit state")
        for year in (2017, 2018):
            out_rows = json.loads((out / f"EFN_{year}_CANONICAL_GEOMETRY.json").read_text())
            require([r["id"] for r in out_rows] == ids[year], f"Stage-2 output ID order changed {year}")
            require(all(r["iau"] == 0 and r["complex_key"] == "HIDDEN" for r in out_rows), "Stage-2 output exposed labels")
            require(all(not (20.0 <= float(r["sol"]) <= 55.0) for r in out_rows), "protected canonical geometry survived Stage 2")

        for name, rows in (
            ("extra-column", make_rows(ids, extra=True)),
            ("protected-row", make_rows(ids, protected=True)),
            ("nonpositive-vg", make_rows(ids, bad_vg=True)),
            ("missing-id", make_rows(ids, missing=True)),
        ):
            ok, _, _ = run_case(mod, td, rows, name)
            require(not ok, f"Stage-2 negative case did not fail closed: {name}")

    result = {
        "verdict": "PASS_RECURRENT_EOM_EFN_STAGE2_LITERAL_HYPHEN_HEADER_REPAIR_SYNTHETIC_AUDIT",
        "synthetic_only": True,
        "native_geometry_only": True,
        "returned_columns": ["Code", "Obs_date", "Lsun", "Lgeo-Lsun", "Bgeo", "Vgeo"],
        "literal_hyphen_lgeo_header_exercised": True,
        "server_side_access_restriction": "frozen Stage-1 retained-ID allowlist only",
        "raw_longitude_server_filter_removed": True,
        "stage1_allowlist_hash_binding": True,
        "exact_retained_id_equality_required": True,
        "csv_schema_boundary_exercised": True,
        "per_batch_id_boundary_exercised": True,
        "solar_longitude_normalization": "raw_Lsun % 360.0 per promoted recurrent-EOM normalize_event",
        "generic_over_360_modulo_supported": True,
        "protected_canonical_row_fails_closed": True,
        "extra_column_fails_closed": True,
        "missing_retained_id_fails_closed": True,
        "nonpositive_velocity_fails_closed": True,
        "quality_filter_used": False,
        "survey_calibration_used": False,
        "efn_event_rows_accessed": False,
        "efn_geometry_accessed": False,
        "efn_shower_labels_accessed": False,
        "target_information_access": False,
        "target_region_physical_values_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "orbittrace_target_access": False
    }
    out = HERE / "output"
    out.mkdir(parents=True, exist_ok=True)
    (out / "STAGE2_HEADER_REPAIR_SYNTHETIC_AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
