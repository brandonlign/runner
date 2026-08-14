#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import requests

URL = "http://www.imo.net/files/data/msswg/readme"
TOKENS = ("date", "time", "solar", "longitude", "radiant", "ra", "dec", "velocity", "vg", "orbit", "shower", "code", "format", "column")
OUT = Path("output")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    r = requests.get(URL, timeout=30, allow_redirects=True, headers={"User-Agent": "OrbitTrace-MSSWG-Readme-Audit/1.0"})
    body = r.content
    if r.status_code != 200:
        raise RuntimeError(f"readme GET failed: {r.status_code}")
    try:
        text = body.decode("utf-8")
        encoding = "utf-8"
    except UnicodeDecodeError:
        text = body.decode("latin-1")
        encoding = "latin-1"
    lines = text.splitlines()
    rx = re.compile("|".join(re.escape(x) for x in TOKENS), re.I)
    selected = [{"line": i + 1, "text": line} for i, line in enumerate(lines) if rx.search(line)]
    (OUT / "MSSWG_README.txt").write_bytes(body)
    result = {
        "stage": "MSSWG_README_SCHEMA_AUDIT_V1",
        "request_count": 1,
        "requested_url": URL,
        "http_status": int(r.status_code),
        "final_url": str(r.url),
        "response_bytes": len(body),
        "response_sha256": hashlib.sha256(body).hexdigest(),
        "decoded_as": encoding,
        "line_count": len(lines),
        "fixed_schema_tokens": list(TOKENS),
        "matching_lines": selected,
        "msswg_readme_access": True,
        "msswg_catalogue_access": False,
        "msswg_catalogue_request_made": False,
        "msswg_event_value_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    (OUT / "MSSWG_README_SCHEMA_AUDIT_V1.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
