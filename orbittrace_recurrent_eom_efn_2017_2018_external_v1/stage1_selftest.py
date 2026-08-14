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


def make_csv(extra_column: bool = False, duplicate: bool = False, invalid_lsun: str | None = None) -> bytes:
    buf = io.StringIO()
    fields = ["Code", "Obs_date", "Lsun"] + (["Shower"] if extra_column else [])
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    for i in range(824):
        year = 2017 if i < 412 else 2018
        local = i if year == 2017 else i - 412
        code = f"SYN{year}_{i:04d}"
        if duplicate and i == 1:
            code = "SYN2017_0000"
        base = 536544000 if year == 2017 else 568080000
        obs_date = base + local * 6000
        if local == 0:
            sol: float | str = 20.0
        elif local == 1:
            sol = 55.0
        elif local == 2:
            sol = 19.999999
        elif local == 3:
            sol = 55.000001
        elif local == 4:
            sol = 360.0
        elif local == 5:
            sol = 361.1739
        elif local == 6:
            sol = -0.25
        elif local == 7:
            sol = 380.0  # canonical 20.0: must be excluded after modulo
        else:
            sol = (100.0 + local * 0.41) % 360.0
            if 20.0 <= sol <= 55.0:
                sol = 60.0 + local * 0.001
        if invalid_lsun is not None and i == 8:
            sol = invalid_lsun
        text_sol = str(sol) if isinstance(sol, str) else f"{sol:.6f}"
        row = {"Code": code, "Obs_date": str(obs_date), "Lsun": text_sol}
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
        except Exception as exc:
            return False, f"{type(exc).__name__}: {exc}"
    finally:
        os.chdir(old)


def expect_fail(mod, payload: bytes, root: Path, name: str) -> None:
    d = root / name
    d.mkdir()
    ok, _ = run_with(mod, payload, d)
    require(not ok, f"{name} did not fail closed")


def main() -> int:
    mod = load_module()
    require(mod.QUERY == 'SELECT Code, "Obs.date", Lsun FROM "J/A+A/667/A157/catalog"', "frozen Stage-1 query changed")
    require(mod.QUERY_COLUMNS == ["Code", "Obs.date", "Lsun"], "semantic query columns changed")
    require(mod.RETURNED_COLUMNS == ["Code", "Obs_date", "Lsun"], "VizieR returned-header mapping changed")
    require(mod.DATE_ENCODING == "VIZIER_SEC_PER_2000", "VizieR date encoding changed")
    require(mod.SOLAR_LONGITUDE_NORMALIZATION == "raw_Lsun % 360.0 per promoted recurrent-EOM normalize_event", "promoted solar-longitude normalization changed")
    require((mod.SEC_2017, mod.SEC_2018, mod.SEC_2019) == (536544000, 568080000, 599616000), "sec/2000 year boundaries changed")
    require(mod.parse_year("536544000") == 2017, "2017 lower boundary changed")
    require(mod.parse_year("568079999") == 2017, "2017 upper boundary changed")
    require(mod.parse_year("568080000") == 2018, "2018 lower boundary changed")
    require(mod.parse_year("599615999") == 2018, "2018 upper boundary changed")
    require(mod.parse_year("594264654") == 2018, "observed safe Stage-1 sec/2000 value no longer resolves to 2018")
    for bad in ("536543999", "599616000", "-1", "2018-01-01", "594264654.0", ""):
        try:
            mod.parse_year(bad)
        except Exception:
            pass
        else:
            raise RuntimeError(f"invalid/out-of-domain date did not fail closed: {bad!r}")

    cases = {
        "0.0": (0.0, False),
        "359.9": (359.9, False),
        "360.0": (0.0, True),
        "360.0466": (0.0466, True),
        "361.1739": (1.1739, True),
        "720.0": (0.0, True),
        "-0.25": (359.75, True),
        "380.0": (20.0, True),
    }
    for raw, expected in cases.items():
        sol, wrapped = mod.canonical_solar_longitude(raw, "SYN")
        require(abs(sol - expected[0]) < 1e-12 and wrapped is expected[1], f"modulo normalization changed for {raw}")
    for bad in ("nan", "inf", "-inf"):
        try:
            mod.canonical_solar_longitude(bad, "SYN_BAD")
        except Exception:
            pass
        else:
            raise RuntimeError(f"nonfinite solar longitude did not fail closed: {bad!r}")
    for forbidden in ("Lgeo-Lsun", "Bgeo", "Vgeo", "Shower", "Object", "RAgeo", "DEgeo", "Vinf"):
        require(forbidden not in mod.QUERY, f"forbidden Stage-1 column entered query: {forbidden}")

    with tempfile.TemporaryDirectory() as td_raw:
        td = Path(td_raw)
        ok, _ = run_with(mod, make_csv(), td)
        require(ok, "valid synthetic 824-row blind index failed")
        root = td / "orbittrace_recurrent_eom_efn_2017_2018_external_v1/output/stage1"
        result = json.loads((root / "STAGE1_BLIND_RECEIPT.json").read_text(encoding="utf-8"))
        require(result["rows_received"] == 824, "fixed 824-row gate changed")
        require(result["rows_by_year"] == {"2017": 412, "2018": 412}, "synthetic sec/2000 year parsing changed")
        require(result["excluded_rows_by_year"] == {"2017": 3, "2018": 3}, "modulo-before-inclusive-blind boundary changed")
        require(result["retained_rows_by_year"] == {"2017": 409, "2018": 409}, "synthetic retained counts changed")
        require(result["selected_columns"] == ["Code", "Obs.date", "Lsun"], "semantic Stage-1 column contract changed")
        require(result["returned_columns"] == ["Code", "Obs_date", "Lsun"], "returned Stage-1 column contract changed")
        require(result["vizier_returned_header_alias"] == {"Obs_date": "Obs.date"}, "VizieR date-header alias changed")
        require(result["obs_date_encoding"] == "VIZIER_SEC_PER_2000", "persisted date encoding changed")
        require(result["solar_longitude_normalization"] == "raw_Lsun % 360.0 per promoted recurrent-EOM normalize_event", "persisted solar normalization changed")
        require(result["raw_solar_longitude_required_finite_only"] is True, "finite-only raw solar contract changed")
        require(result["modulo_wrapped_rows_by_year"] == {"2017": 4, "2018": 4}, "synthetic modulo-wrap counts changed")
        require(result["modulo_wrapped_rows_total"] == 8, "synthetic modulo-wrap total changed")
        require(result["blind_exclusion_applied_after_modulo_normalization"] is True, "blind ordering changed")
        require(result["raw_response_persisted"] is False and result["solar_longitude_values_persisted"] is False, "blind response/value persistence flag changed")
        require(result["geometry_returned"] is False and result["shower_labels_returned"] is False and result["orbit_fields_returned"] is False, "forbidden Stage-1 science flag changed")
        kept17 = (root / "EFN_2017_RETAINED_IDS.txt").read_text().splitlines()
        kept18 = (root / "EFN_2018_RETAINED_IDS.txt").read_text().splitlines()
        require("SYN2017_0004" in kept17 and "SYN2017_0005" in kept17 and "SYN2017_0006" in kept17, "2017 wrapped retained rows missing")
        require("SYN2017_0007" not in kept17, "2017 raw 380/canonical 20 protected row leaked")
        require("SYN2018_0416" in kept18 and "SYN2018_0417" in kept18 and "SYN2018_0418" in kept18, "2018 wrapped retained rows missing")
        require("SYN2018_0419" not in kept18, "2018 raw 380/canonical 20 protected row leaked")

        expect_fail(mod, make_csv(extra_column=True), td, "bad-extra")
        expect_fail(mod, make_csv(duplicate=True), td, "bad-duplicate")
        short = make_csv().decode("utf-8").splitlines()
        expect_fail(mod, ("\n".join(short[:-1]) + "\n").encode(), td, "bad-short")
        expect_fail(mod, make_csv(invalid_lsun="nan"), td, "bad-nan")
        expect_fail(mod, make_csv(invalid_lsun="inf"), td, "bad-inf")

    result = {
        "verdict": "PASS_RECURRENT_EOM_EFN_STAGE1_GENERIC_MODULO_REPAIR_SYNTHETIC_AUDIT",
        "synthetic_only": True,
        "expected_catalogue_rows": 824,
        "query_columns": ["Code", "Obs.date", "Lsun"],
        "returned_columns": ["Code", "Obs_date", "Lsun"],
        "query_unchanged": True,
        "obs_date_encoding": "VIZIER_SEC_PER_2000",
        "solar_longitude_normalization": "raw_Lsun % 360.0 per promoted recurrent-EOM normalize_event",
        "finite_raw_values_only": True,
        "generic_over_360_modulo_supported": True,
        "generic_negative_modulo_supported": True,
        "diagnostic_values_360_0466_and_361_1739_supported": True,
        "canonical_20_after_modulo_excluded": True,
        "nonfinite_fails_closed": True,
        "boundary_20_excluded": True,
        "boundary_55_excluded": True,
        "extra_column_fails_closed": True,
        "duplicate_code_fails_closed": True,
        "wrong_row_count_fails_closed": True,
        "raw_response_persisted": False,
        "solar_longitude_values_persisted": False,
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
    (out / "STAGE1_GENERIC_MODULO_REPAIR_SYNTHETIC_AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
