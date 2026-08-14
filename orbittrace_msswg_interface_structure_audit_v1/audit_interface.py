#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

URL = "https://www.imo.net/observations/methods/video-observation/data/"
TARGET_TEXTS = ("readme", "msswg.txt")
OUT = Path("output")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    r = requests.get(URL, timeout=30, allow_redirects=True, headers={"User-Agent": "OrbitTrace-MSSWG-Structure-Audit/1.0"})
    body = r.content
    soup = BeautifulSoup(body, "html.parser")
    found: dict[str, list[dict[str, str]]] = {text: [] for text in TARGET_TEXTS}
    for a in soup.find_all("a"):
        text = " ".join(a.get_text(" ", strip=True).split()).lower()
        if text not in found:
            continue
        href = a.get("href")
        if not isinstance(href, str) or not href.strip():
            continue
        resolved = urljoin(r.url, href.strip())
        found[text].append({"href": href.strip(), "resolved_url": resolved})

    exact_counts = {text: len(found[text]) for text in TARGET_TEXTS}
    distinct = []
    schemes_ok = True
    for text in TARGET_TEXTS:
        if len(found[text]) == 1:
            resolved = found[text][0]["resolved_url"]
            distinct.append(resolved)
            schemes_ok = schemes_ok and urlparse(resolved).scheme in {"http", "https"}
        else:
            schemes_ok = False
    passed = bool(
        r.status_code == 200
        and all(exact_counts[text] == 1 for text in TARGET_TEXTS)
        and schemes_ok
        and len(set(distinct)) == 2
    )
    result = {
        "stage": "MSSWG_OFFICIAL_INTERFACE_STRUCTURE_AUDIT_V1",
        "verdict": "PASS_MSSWG_OFFICIAL_INTERFACE_STRUCTURE_AUDIT" if passed else "FAIL_MSSWG_OFFICIAL_INTERFACE_STRUCTURE_AUDIT",
        "request_count": 1,
        "requested_url": URL,
        "http_status": int(r.status_code),
        "final_url": str(r.url),
        "response_bytes": len(body),
        "response_sha256": hashlib.sha256(body).hexdigest(),
        "exact_anchor_counts": exact_counts,
        "anchors": found,
        "target_requests_made": False,
        "msswg_catalogue_access": False,
        "msswg_readme_access": False,
        "msswg_event_value_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    (OUT / "MSSWG_OFFICIAL_INTERFACE_STRUCTURE_AUDIT_V1.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
