#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import json
import urllib.parse
import urllib.request
from pathlib import Path

ENDPOINT = "https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync"
CANONICAL_TABLE = "J/A+A/667/A157/catalog"
REQUIRED = {
    "Code",
    "Obs.date",
    "Lsun",
    "Lgeo-Lsun",
    "Bgeo",
    "Vgeo",
    "Shower",
}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def post_adql(query: str) -> str:
    qnorm = " ".join(query.lower().split())
    require("tap_schema." in qnorm, "schema audit attempted a non-TAP_SCHEMA query")
    require('from "j/a+a/667/a157/catalog"' not in qnorm, "schema audit attempted event-table access")
    body = urllib.parse.urlencode(
        {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": query}
    ).encode("ascii")
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "OrbitTrace-EFN-preaccess-schema-audit/1"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    text = raw.decode("utf-8-sig")
    require(text.strip(), "empty TAP_SCHEMA response")
    return text


def rows(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


def strip_quote_wrapper(value: str) -> str:
    s = str(value).strip()
    if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
        return s[1:-1]
    return s


def adql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> int:
    table_query = (
        "SELECT table_name, description FROM TAP_SCHEMA.tables "
        "WHERE table_name LIKE '%A157%' ORDER BY table_name"
    )
    table_rows_all = rows(post_adql(table_query))
    matches = [r for r in table_rows_all if strip_quote_wrapper(r.get("table_name", "")) == CANONICAL_TABLE]
    require(len(matches) == 1, f"expected one canonical EFN metadata table after normalized discovery, got {len(matches)} from {[r.get('table_name') for r in table_rows_all]}")
    table_row = matches[0]
    raw_table_name = str(table_row["table_name"])

    column_query = (
        "SELECT column_name, datatype, unit, description FROM TAP_SCHEMA.columns "
        f"WHERE table_name = {adql_string(raw_table_name)} ORDER BY column_name"
    )
    column_rows = rows(post_adql(column_query))
    require(column_rows, "no TAP_SCHEMA column rows for resolved EFN table")
    raw_names = [str(r.get("column_name", "")) for r in column_rows]
    names = [strip_quote_wrapper(n) for n in raw_names]
    require(len(names) == len(set(names)), "duplicate normalized TAP column metadata")
    require(REQUIRED.issubset(set(names)), f"required EFN TAP fields missing: {sorted(REQUIRED - set(names))}; got {names}")
    require("Obs.time" not in set(names), "unexpected separate Obs.time column appeared; access repair requires review")

    selected = {}
    for required in sorted(REQUIRED):
        i = names.index(required)
        selected[required] = {
            "raw_column_name": raw_names[i],
            "datatype": column_rows[i].get("datatype"),
            "unit": column_rows[i].get("unit"),
            "description": column_rows[i].get("description"),
        }

    result = {
        "verdict": "PASS_RECURRENT_EOM_EFN_TAP_SCHEMA_PREACCESS_AUDIT",
        "endpoint": ENDPOINT,
        "catalogue": "J/A+A/667/A157",
        "canonical_table_name": CANONICAL_TABLE,
        "tap_schema_raw_table_name": raw_table_name,
        "tap_schema_normalized_table_name": strip_quote_wrapper(raw_table_name),
        "table_description": table_row.get("description"),
        "required_columns": selected,
        "all_normalized_column_names_sha256": hashlib.sha256(("\n".join(names) + "\n").encode()).hexdigest(),
        "all_column_count": len(names),
        "obs_time_separate_column_present": False,
        "query_classes": ["TAP_SCHEMA.tables", "TAP_SCHEMA.columns"],
        "event_table_queried": False,
        "efn_event_rows_accessed": False,
        "efn_geometry_accessed": False,
        "efn_shower_labels_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "orbittrace_target_access": False,
    }
    out = Path("orbittrace_recurrent_eom_efn_2017_2018_external_v1/output")
    out.mkdir(parents=True, exist_ok=True)
    (out / "TAP_SCHEMA_AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
