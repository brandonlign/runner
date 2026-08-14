#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import requests

URL = "https://fireballs.ndc.nasa.gov/public_data/nasfn_2013-2019.zip"
KEEP = ("Content-Type", "Content-Length", "Last-Modified", "ETag", "Accept-Ranges", "Content-Disposition")
OUT = Path("output")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    r = requests.head(URL, timeout=30, allow_redirects=True, headers={"User-Agent": "OrbitTrace-NASA-ASFN-Bulk-HEAD-Audit/1.0"})
    content_type = (r.headers.get("Content-Type") or "").lower()
    passed = bool(r.status_code == 200 and ("zip" in content_type or str(r.url).lower().endswith(".zip")))
    result = {
        "stage": "NASA_ASFN_PRIMARY_BULK_HEAD_AUDIT_V1",
        "verdict": "PASS_NASA_ASFN_PRIMARY_BULK_HEAD_AUDIT" if passed else "BLOCKED_NASA_ASFN_PRIMARY_BULK_HEAD_AUDIT",
        "request_method": "HEAD",
        "application_request_count": 1,
        "requested_url": URL,
        "http_status": int(r.status_code),
        "final_url": str(r.url),
        "redirect_history": [{"status": int(x.status_code), "url": str(x.url)} for x in r.history],
        "selected_headers": {k: r.headers.get(k) for k in KEEP},
        "asfn_bulk_body_access": False,
        "asfn_event_value_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    (OUT / "NASA_ASFN_PRIMARY_BULK_HEAD_AUDIT_V1.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
