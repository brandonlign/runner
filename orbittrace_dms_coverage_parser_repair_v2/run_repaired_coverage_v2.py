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
INDICES = {"year": 2, "month": 3, "day": 4, "solar_longitude": 6}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.strip().lower())


def compact_dms_schema(archive: bytes) -> dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        members = [
            info for info in zf.infolist()
            if not info.is_dir()
            and info.file_size > 0
            and info.filename.lower().endswith((".csv", ".txt", ".dat"))
        ]
        require(len(members) == 1, f"expected one DMS text member, got {len(members)}")
        info = members[0]
        raw = zf.read(info.filename)
        text, encoding = parent.decode_text(raw)
        require(encoding in {"utf-8-sig", "utf-8"}, f"unexpected DMS encoding {encoding}")
        rows = [
            row for row in csv.reader(io.StringIO(text), delimiter=";")
            if row and any(cell.strip() for cell in row)
        ]
        require(len(rows) == EXPECTED_ROWS, f"DMS nonblank row count changed: {len(rows)}")
        require({len(row) for row in rows} == {EXPECTED_WIDTH}, "DMS compact row width changed")
        require(len(rows) - 2 == EXPECTED_DATA_ROWS, "DMS public 908-row cardinality changed")

        h0, h1 = rows[0], rows[1]
        def header_matches(index: int, aliases: set[str]) -> bool:
            return any(norm(header[index]) in aliases for header in (h0, h1))

        require(header_matches(2, {"yr", "year"}), "compact DMS year header changed")
        require(header_matches(3, {"mn", "month"}), "compact DMS month header changed")
        require(header_matches(4, {"day", "decday"}), "compact DMS day header changed")
        require(header_matches(5, {"n"}), "compact DMS N guard header changed")
        require(header_matches(7, {"mv", "mvmax"}), "compact DMS magnitude guard header changed")

        # No DMS data-row value is inspected here. Column 6 is frozen as LS by
        # the preregistered compact-schema protocol before coverage is computed.
        return {
            "mode": "named_header",
            "member_name": info.filename,
            "raw": raw,
            "encoding": encoding,
            "data_start_line_index": 2,
            "header_line_index": 0,
            "delimiter": ";",
            "header": h0,
            "indices": dict(INDICES),
            "row_width": EXPECTED_WIDTH,
        }


def main() -> int:
    parent.choose_data_member = compact_dms_schema
    return parent.main()


if __name__ == "__main__":
    raise SystemExit(main())
