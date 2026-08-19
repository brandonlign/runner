#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import re
import zipfile
from typing import Any

from orbittrace_v15_dms_coverage_eligibility_v1 import audit_coverage as parent

EXPECTED_ROWS = 910
EXPECTED_WIDTH = 42
EXPECTED_DATA_ROWS = parent.OFFICIAL_ORBIT_COUNT
DELIMITER = ";"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.strip().lower())


def choose_data_member_two_row(archive: bytes) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    aliases = {
        "year": {"yr", "year"},
        "month": {"mn", "month"},
        "day": {"day", "decday"},
        "solar_longitude": {"ls", "solarlongitude", "solarlon"},
    }

    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        members = [
            info
            for info in zf.infolist()
            if not info.is_dir()
            and info.file_size > 0
            and info.filename.lower().endswith((".csv", ".txt", ".dat"))
        ]
        require(len(members) == 1, f"expected exactly one DMS text member, got {len(members)}")
        info = members[0]
        raw = zf.read(info.filename)
        text, encoding = parent.decode_text(raw)
        require(encoding in {"utf-8-sig", "utf-8"}, f"unexpected DMS encoding {encoding}")
        rows = [
            row
            for row in csv.reader(io.StringIO(text), delimiter=DELIMITER)
            if row and any(cell.strip() for cell in row)
        ]
        require(len(rows) == EXPECTED_ROWS, f"DMS nonblank row count changed: {len(rows)}")
        require({len(row) for row in rows} == {EXPECTED_WIDTH}, "DMS semicolon row width changed")
        require(len(rows) - 2 == EXPECTED_DATA_ROWS, "DMS public 908-row cardinality changed")

        resolved: dict[str, int] = {}
        header_rows = rows[:2]
        for concept, names in aliases.items():
            hits: list[int] = []
            for column in range(EXPECTED_WIDTH):
                if any(norm(header[column]) in names for header in header_rows):
                    hits.append(column)
            hits = sorted(set(hits))
            require(len(hits) == 1, f"could not uniquely resolve DMS allowed field {concept}: {hits}")
            resolved[concept] = hits[0]
        require(len(set(resolved.values())) == 4, "DMS allowed fields do not resolve to distinct columns")

        # Do not inspect or parse any data-row cell here. The unchanged parent
        # coverage parser will interpret only these four resolved positions.
        candidates.append(
            {
                "mode": "named_header",
                "member_name": info.filename,
                "raw": raw,
                "encoding": encoding,
                "data_start_line_index": 2,
                "header_line_index": 0,
                "delimiter": DELIMITER,
                "header": header_rows[0],
                "indices": resolved,
                "row_width": EXPECTED_WIDTH,
            }
        )

    require(len(candidates) == 1, "two-row DMS resolver produced wrong candidate count")
    return candidates[0]


def main() -> int:
    parent.choose_data_member = choose_data_member_two_row
    return parent.main()


if __name__ == "__main__":
    raise SystemExit(main())
