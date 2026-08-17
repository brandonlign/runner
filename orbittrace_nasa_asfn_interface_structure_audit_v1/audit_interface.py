#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

URL = "https://www.nasa.gov/meteoroid-environment-office/all-sky-fireball-network/"
OUT = Path("output")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    r = requests.get(URL, timeout=30, allow_redirects=True, headers={"User-Agent": "OrbitTrace-NASA-ASFN-Structure-Audit/1.0"})
    body = r.content
    soup = BeautifulSoup(body, "html.parser")
    orbit = []
    network = []
    for a in soup.find_all("a"):
        href = a.get("href")
        if not isinstance(href, str) or not href.strip():
            continue
        text = " ".join(a.get_text(" ", strip=True).split())
        resolved = urljoin(r.url, href.strip())
        parsed = urlparse(resolved)
        row = {"text": text, "href": href.strip(), "resolved_url": resolved}
        if text.lower() == "orbit table":
            orbit.append(row)
        if parsed.hostname == "fireballs.ndc.nasa.gov":
            path = parsed.path or "/"
            if "/events/" not in path and not re.search(r"/\d{8}(?:\.html)?$", path):
                network.append(row)
    targets = orbit + network
    schemes_ok = all(urlparse(x["resolved_url"]).scheme in {"http", "https"} for x in targets)
    passed = bool(r.status_code == 200 and len(orbit) == 1 and len(network) >= 1 and schemes_ok)
    result = {
        "stage": "NASA_ASFN_OFFICIAL_INTERFACE_STRUCTURE_AUDIT_V1",
        "verdict": "PASS_NASA_ASFN_OFFICIAL_INTERFACE_STRUCTURE_AUDIT" if passed else "FAIL_NASA_ASFN_OFFICIAL_INTERFACE_STRUCTURE_AUDIT",
        "request_count": 1,
        "requested_url": URL,
        "http_status": int(r.status_code),
        "final_url": str(r.url),
        "response_bytes": len(body),
        "response_sha256": hashlib.sha256(body).hexdigest(),
        "orbit_table_anchors": orbit,
        "network_site_anchors": network,
        "target_requests_made": False,
        "asfn_event_data_access": False,
        "asfn_bulk_catalogue_access": False,
        "orbit_table_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    (OUT / "NASA_ASFN_OFFICIAL_INTERFACE_STRUCTURE_AUDIT_V1.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
