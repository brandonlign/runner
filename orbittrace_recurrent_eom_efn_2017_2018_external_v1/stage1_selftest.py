#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import io
import json
import os
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "stage1_blind_receipt.py"


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def load_module():
    spec = importlib.util.spec_from_file_location("efn_stage1_under_test", SOURCE)
    require(spec is not None and spec.loader is not None, "cannot import Stage-1 source")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_csv(extra_column: bool = False, duplicate: bool = False) -> bytes:
    buf = io.StringIO()
    fields = ["Code", "Obs.date", "Lsun"] + (["Shower"] if extra_column else [])
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    for i in range(824):
        year = 2017 if i < 412 else 2018
        code = f"SYN{year}_{i:04d}"
        if duplicate and i == 1:
            code = "SYN2017_0000"
        # Test both inclusive edges in both years. Everything else is retained.
        local = i if year == 2017 else i - 412
        if local == 0:
            sol = 20.0
        elif local == 1:
            sol = 55.0
        elif local == 2:
            sol = 19.999999
        elif local == 3:
            sol = 55.000001
        else:
            sol = (100.0 + local * 0.41) % 360.0
            if 20.0 <= sol <= 55.0:
                sol = 60.0 + local * 0.001
        row = {"Code": code, "Obs.date": f"{year}-07-01 00:00:00", "Lsun": f"{sol:.6f}"}
        if extra_column:
            row["Shower"] = "FORBIDDEN"
        w.writerow(row)
    return buf.getvalue().encode("utf-8")


def run_with(mod, payload: bytes, cwd: Path) -> tuple[bool, str]:
    old = os.getcwd()
    try:
        os.chdir(cwd)
        mod.query_csv = lambda: payload
        capture = io.StringIO()
        try:
            with redirect_stdout(capture):
                mod.main()
            return True, capture.getvalue()
        except Exception as exc:  # expected in negative synthetic cases
            return False, f"{type(exc).__name__}: {exc}"
    finally:
        os.chdir(old)


def main() -> int:
    mod = load_module()
    require(mod.QUERY == 'SELECT Code, "Obs.date", Lsun FROM "J/A+A/667/A157/catalog"', "frozen Stage-1 query changed")
    for forbidden in ("Lgeo-Lsun", "Bgeo", "Vgeo", "Shower", "Object", "RAgeo", "DEgeo", "Vinf"):
        require(forbidden not in mod.QUERY, f"forbidden Stage-1 column entered query: {forbidden}")

    with tempfile.TemporaryDirectory() as td_raw:
        td = Path(td_raw)
        ok, _ = run_with(mod, make_csv(), td)
        require(ok, "valid synthetic 824-row blind index failed")
        root = td / "orbittrace_recurrent_eom_efn_2017_2018_external_v1/output/stage1"
        result = json.loads((root / "STAGE1_BLIND_RECEIPT.json").read_text(encoding="utf-8"))
        require(result["rows_received"] == 824, "fixed 824-row gate changed")
        require(result["rows_by_year"] == {"2017": 412, "2018": 412}, "synthetic year parsing changed")
        require(result["excluded_rows_by_year"] == {"2017": 2, "2018": 2}, "inclusive blind boundary changed")
        require(result["retained_rows_by_year"] == {"2017": 410, "2018": 410}, "synthetic retained counts changed")
        require(result["selected_columns"] == ["Code", "Obs.date", "Lsun"], "Stage-1 column contract changed")
        require(result["raw_response_persisted"] is False, "raw blind-index response persistence flag changed")
        require(result["geometry_returned"] is False and result["shower_labels_returned"] is False and result["orbit_fields_returned"] is False, "forbidden Stage-1 science flag changed")
        require(len((root / "EFN_2017_RETAINED_IDS.txt").read_text().splitlines()) == 410, "2017 allowlist size changed")
        require(len((root / "EFN_2018_RETAINED_IDS.txt").read_text().splitlines()) == 410, "2018 allowlist size changed")

        bad_dir = td / "bad-extra"
        bad_dir.mkdir()
        ok_extra, _ = run_with(mod, make_csv(extra_column=True), bad_dir)
        require(not ok_extra, "extra Shower column did not fail closed")

        dup_dir = td / "bad-duplicate"
        dup_dir.mkdir()
        ok_dup, _ = run_with(mod, make_csv(duplicate=True), dup_dir)
        require(not ok_dup, "duplicate Code did not fail closed")

        short = make_csv().decode("utf-8").splitlines()
        short_payload = ("\n".join(short[:-1]) + "\n").encode()
        short_dir = td / "bad-short"
        short_dir.mkdir()
        ok_short, _ = run_with(mod, short_payload, short_dir)
        require(not ok_short, "823-row release did not fail closed")

    result = {
        "verdict": "PASS_RECURRENT_EOM_EFN_STAGE1_SYNTHETIC_AUDIT",
        "synthetic_only": True,
        "expected_catalogue_rows": 824,
        "stage1_selected_columns": ["Code", "Obs.date", "Lsun"],
        "boundary_20_excluded": True,
        "boundary_55_excluded": True,
        "extra_column_fails_closed": True,
        "duplicate_code_fails_closed": True,
        "wrong_row_count_fails_closed": True,
        "raw_response_persisted": False,
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
    (out / "STAGE1_SYNTHETIC_AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
