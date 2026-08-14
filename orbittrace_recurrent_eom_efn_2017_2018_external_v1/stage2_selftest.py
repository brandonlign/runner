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
    ids = {
        2017: [f"SYN2017_{i:03d}" for i in range(12)],
        2018: [f"SYN2018_{i:03d}" for i in range(12)],
    }
    id_paths = {}
    hashes = {}
    for year in (2017, 2018):
        p = root / f"EFN_{year}_RETAINED_IDS.txt"
        data = ("\n".join(ids[year]) + "\n").encode()
        p.write_bytes(data)
        id_paths[year] = p
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
    return stage1, id_paths[2017], id_paths[2018], ids


def make_geometry_csv(ids: dict[int, list[str]], *, extra: bool = False, protected: bool = False, bad_vg: bool = False, missing: bool = False) -> bytes:
    fields = ["Code", "Obs_date", "Lsun", "Lgeo_Lsun", "Bgeo", "Vgeo"] + (["Shower"] if extra else [])
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    rows = []
    for year in (2017, 2018):
        base = 536544000 if year == 2017 else 568080000
        for i, code in enumerate(ids[year]):
            sol = 360.0 if i == 0 else 100.0 + i
            if protected and year == 2017 and i == 1:
                sol = 30.0
            row = {
                "Code": code,
                "Obs_date": str(base + i * 1000),
                "Lsun": f"{sol:.6f}",
                "Lgeo_Lsun": f"{-40.0 + i * 2.0:.6f}",
                "Bgeo": f"{-15.0 + i:.6f}",
                "Vgeo": "0.0" if bad_vg and year == 2018 and i == 2 else f"{25.0 + i:.6f}",
            }
            if extra:
                row["Shower"] = "BAD"
            rows.append(row)
    if missing:
        rows = rows[:-1]
    for row in rows:
        w.writerow(row)
    return b.getvalue().encode()


def run_case(mod, td: Path, payload: bytes, name: str) -> tuple[bool, Path, str]:
    case = td / name
    case.mkdir()
    stage1, ids17, ids18, _ = write_stage1(case)
    out = case / "out"
    mod.query_csv = lambda: payload
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
    require(mod.QUERY == 'SELECT Code, "Obs.date", Lsun, "Lgeo-Lsun", Bgeo, Vgeo FROM "J/A+A/667/A157/catalog" WHERE Lsun < 20.0 OR Lsun > 55.0', "Stage-2 query changed")
    require(mod.QUERY_COLUMNS == ["Code", "Obs.date", "Lsun", "Lgeo-Lsun", "Bgeo", "Vgeo"], "Stage-2 semantic columns changed")
    require("Shower" not in mod.QUERY and "Object" not in mod.QUERY, "truth-bearing field entered Stage 2")
    sol, wrapped = mod.canonical_solar_longitude("360.0", "SYN")
    require(sol == 0.0 and wrapped is True, "Stage-2 exact-360 canonicalization changed")

    with tempfile.TemporaryDirectory() as td_raw:
        td = Path(td_raw)
        seed = td / "seed"
        seed.mkdir()
        _, _, _, ids = write_stage1(seed)
        valid_payload = make_geometry_csv(ids)
        ok, out, text = run_case(mod, td, valid_payload, "valid")
        require(ok, f"valid synthetic Stage 2 failed: {text}")
        result = json.loads((out / "STAGE2_RETAINED_GEOMETRY.json").read_text())
        require(result["verdict"] == "PASS_RECURRENT_EOM_EFN_STAGE2_RETAINED_NATIVE_GEOMETRY", "wrong Stage-2 verdict")
        require(result["rows_by_year"] == {"2017": 12, "2018": 12}, "Stage-2 counts changed")
        require(result["server_side_filter"] == "Lsun < 20.0 OR Lsun > 55.0", "Stage-2 server filter changed")
        require(result["native_mapping"] == {"sol": "Lsun % 360.0", "sun_lon": "Lgeo-Lsun", "ecl_lat": "Bgeo", "vg": "Vgeo"}, "native mapping changed")
        require(result["exact_360_wrapped_to_zero_by_year"] == {"2017": 1, "2018": 1}, "Stage-2 wrap counts changed")
        require(result["labels_accessed"] is False and result["shower_column_returned"] is False and result["orbit_fields_returned"] is False, "Stage 2 exposed truth/orbit state")
        for year in (2017, 2018):
            rows = json.loads((out / f"EFN_{year}_CANONICAL_GEOMETRY.json").read_text())
            require([r["id"] for r in rows] == ids[year], f"Stage-2 output ID order changed {year}")
            require(rows[0]["sol"] == 0.0, f"Stage-2 exact-360 row not canonical zero {year}")
            require(all(r["iau"] == 0 and r["complex_key"] == "HIDDEN" for r in rows), "Stage-2 output exposed labels")
            require(all(not (20.0 <= float(r["sol"]) <= 55.0) for r in rows), "protected canonical geometry survived Stage 2")

        for name, payload in (
            ("extra-column", make_geometry_csv(ids, extra=True)),
            ("protected-row", make_geometry_csv(ids, protected=True)),
            ("nonpositive-vg", make_geometry_csv(ids, bad_vg=True)),
            ("missing-id", make_geometry_csv(ids, missing=True)),
        ):
            ok, _, _ = run_case(mod, td, payload, name)
            require(not ok, f"Stage-2 negative case did not fail closed: {name}")

    result = {
        "verdict": "PASS_RECURRENT_EOM_EFN_STAGE2_SYNTHETIC_PREACCESS_AUDIT",
        "synthetic_only": True,
        "stage2_query": mod.QUERY,
        "server_side_protected_filter": "Lsun < 20.0 OR Lsun > 55.0",
        "native_geometry_only": True,
        "stage1_allowlist_hash_binding": True,
        "exact_retained_id_equality_required": True,
        "solar_longitude_normalization": "raw_Lsun % 360.0 per promoted recurrent-EOM normalize_event",
        "exact_360_canonicalizes_to_zero": True,
        "protected_row_fails_closed": True,
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
        "orbittrace_target_access": False,
    }
    out = HERE / "output"
    out.mkdir(parents=True, exist_ok=True)
    (out / "STAGE2_SYNTHETIC_PREACCESS_AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
