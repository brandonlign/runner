#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import requests

URL = "https://www.nasa.gov/xls/523317main_Orbit_Table.xls"
OUT = Path("output")
KEEP = ("Content-Type", "Content-Length", "Last-Modified", "ETag", "Content-Disposition")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    r = requests.head(URL, timeout=30, allow_redirects=True, headers={"User-Agent": "OrbitTrace-NASA-ASFN-Orbit-HEAD-Audit/1.0"})
    result = {
        "stage": "NASA_ASFN_ORBIT_TABLE_HEAD_AUDIT_V1",
        "request_method": "HEAD",
        "application_request_count": 1,
        "requested_url": URL,
        "http_status": int(r.status_code),
        "final_url": str(r.url),
        "redirect_history": [{"status": int(x.status_code), "url": str(x.url)} for x in r.history],
        "selected_headers": {k: r.headers.get(k) for k in KEEP},
        "orbit_table_body_access": False,
        "asfn_event_data_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    (OUT / "NASA_ASFN_ORBIT_TABLE_HEAD_AUDIT_V1.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
