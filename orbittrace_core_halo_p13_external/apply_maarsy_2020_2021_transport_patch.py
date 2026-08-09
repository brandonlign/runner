#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def replace_once(text: str, before: str, after: str, label: str) -> str:
    n = text.count(before)
    if n != 1:
        raise RuntimeError(f"P13 MAARSY transport patch anchor {label} count={n}")
    return text.replace(before, after, 1)


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_maarsy_2020_2021_transport_patch.py EXACT_P1_TRANSPORT OUTPUT")
    src = Path(sys.argv[1]).read_text(encoding="utf-8")
    out = src
    for before, after, label in (
        ("YEARS=(2018,2019)", "YEARS=(2020,2021)", "years"),
        ('MONTH_RE=re.compile(r"^data/(2018|2019)/(0[1-9]|1[0-2])/kep_collect\\.h5$")',
         'MONTH_RE=re.compile(r"^data/(2020|2021)/(0[1-9]|1[0-2])/kep_collect\\.h5$")', "month regex"),
        ('STOP_PREFIX="data/2020/"', 'STOP_PREFIX="data/2022/"', "stop prefix"),
        ('OrbitTrace-P1-MAARSY-2018-2019/1.0', 'OrbitTrace-P13-MAARSY-2020-2021/1.0', "geometry user agent"),
        ('OrbitTrace-P1-MAARSY-2018-2019-orbit/1.0', 'OrbitTrace-P13-MAARSY-2020-2021-orbit/1.0', "orbit user agent"),
        ('"arg":arg%360.0', '"peri":arg%360.0', "P12 perihelion interface key"),
        ('"stopped_at_first_2020_member_header":stop', '"stopped_at_first_2022_member_header":stop', "geometry stop audit key"),
        ('"stopped_at_first_2020_member_header":stop', '"stopped_at_first_2022_member_header":stop', "orbit stop audit key"),
    ):
        out = replace_once(out, before, after, label)
    forbidden = (
        "OrbitTrace-April",
        "target_coordinate",
        "2018,2019",
        "data/(2018|2019)",
        'STOP_PREFIX="data/2020/"',
    )
    for token in forbidden:
        if token in out:
            raise RuntimeError(f"forbidden/stale P13 MAARSY transport token survived: {token}")
    required = (
        "YEARS=(2020,2021)",
        'STOP_PREFIX="data/2022/"',
        'MAX_EVENTS_PER_BIN=10_000',
        'BLIND_LOW=20.0',
        'BLIND_HIGH=55.0',
        'REQUIRED_GEOMETRY=("sun_lon","slat","slon","vels")',
        'CONTENT_URL="https://zenodo.org/api/records/15553437/files/silseth_thesis_data.tar.gz/content"',
        'EXPECTED_FILE_MD5="01820c6a90ea1415b011bb013a4d9213"',
        '"peri":arg%360.0',
        'native_kepler_mapping":["a_m","e","i_deg","omega_deg","Omega_deg","nu_deg"]',
        'target_interval_radiant_speed_read":False',
        'target_information_access":False',
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"required P13 MAARSY transport invariant missing: {token}")
    Path(sys.argv[2]).write_text(out, encoding="utf-8")
    print("PASS_P13_MAARSY_2020_2021_TRANSPORT_SOURCE_TRANSFORM")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
