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
TABLE = "J/A+A/667/A157/catalog"
REQUIRED = {
    "Code",
    "Obs.date",
    "Lsun",
    "Lgeo-Lsun",
    "Bgeo",
    "Vgeo",
    "Shower",
}
FORBIDDEN_EVENT_TOKENS = ("select * from \"j/a+a/667/a157/catalog\"", "from \"j/a+a/667/a157/catalog\"")


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def post_adql(query: str) -> str:
    qnorm = " ".join(query.lower().split())
    require("tap_schema." in qnorm, "schema audit attempted a non-TAP_SCHEMA query")
    require(all(tok not in qnorm for tok in FORBIDDEN_EVENT_TOKENS), "schema audit attempted event-table access")
    body = urllib.parse.urlencode(
        {
            "REQUEST": "doQuery",
            "LANG": "ADQL",
            "FORMAT": "csv",
            "QUERY": query,
        }
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


def main() -> int:
    table_query = (
        "SELECT table_name, description FROM TAP_SCHEMA.tables "
        "WHERE table_name = 'J/A+A/667/A157/catalog'"
    )
    column_query = (
        "SELECT column_name, datatype, unit, description FROM TAP_SCHEMA.columns "
        "WHERE table_name = 'J/A+A/667/A157/catalog' ORDER BY column_name"
    )
    table_rows = rows(post_adql(table_query))
    column_rows = rows(post_adql(column_query))
    require(len(table_rows) == 1, f"expected exactly one EFN TAP table metadata row, got {len(table_rows)}")
    require(table_rows[0].get("table_name") == TABLE, f"unexpected table name: {table_rows[0]}")
    require(column_rows, "no TAP_SCHEMA column rows")
    names = [str(r.get("column_name", "")) for r in column_rows]
    require(len(names) == len(set(names)), "duplicate TAP column metadata")
    require(REQUIRED.issubset(set(names)), f"required EFN TAP fields missing: {sorted(REQUIRED - set(names))}")
    require("Obs.time" not in set(names), "unexpected separate Obs.time column appeared; access repair requires review")

    selected = {
        n: next(r for r in column_rows if r.get("column_name") == n)
        for n in sorted(REQUIRED)
    }
    result = {
        "verdict": "PASS_RECURRENT_EOM_EFN_TAP_SCHEMA_PREACCESS_AUDIT",
        "endpoint": ENDPOINT,
        "catalogue": "J/A+A/667/A157",
        "table_name": TABLE,
        "table_description": table_rows[0].get("description"),
        "required_columns": selected,
        "all_column_names_sha256": hashlib.sha256(("\n".join(names) + "\n").encode()).hexdigest(),
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
