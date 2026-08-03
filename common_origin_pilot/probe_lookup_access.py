#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import urljoin

import requests

OUT = Path(__file__).resolve().parent / "results"
DATASET = "t2rrdtzd8h"
PAGE = f"https://data.mendeley.com/datasets/{DATASET}/1"


def clean(value: str) -> str:
    return html.unescape(value).replace("\\u002F", "/").replace("\\/", "/")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/150 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    })
    response = session.get(PAGE, timeout=120)
    response.raise_for_status()
    text = clean(response.text)
    lower = text.lower()
    anchor = lower.find("showerlookuptable")
    snippets = []
    if anchor >= 0:
        for radius in (500, 1500, 5000, 15000):
            snippets.append(text[max(0, anchor-radius):anchor+radius])
    urls = sorted(set(re.findall(r"https?://[^\"'<>\\\s]+", text)))
    relative = sorted(set(re.findall(r"(?:/[^\"'<>\\\s]+(?:file_downloaded|download)[^\"'<>\\\s]*)", text, flags=re.I)))
    uuids = sorted(set(re.findall(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b", text)))
    interesting_urls = [url for url in urls if any(token in url.lower() for token in ("download", "public-files", DATASET, "showerlookup"))]
    scripts = []
    for match in re.finditer(r"<script([^>]*)>(.*?)</script>", text, flags=re.I | re.S):
        attrs, body = match.group(1), match.group(2)
        if any(token in body.lower() for token in (DATASET, "showerlookuptable", "file_downloaded", "public-files")):
            scripts.append({"attrs": attrs[:500], "body": body[:100000]})
    probes = []
    candidate_urls = [urljoin(PAGE, path) for path in relative] + interesting_urls
    for uuid in uuids:
        candidate_urls.extend([
            f"https://data.mendeley.com/public-files/datasets/{DATASET}/files/{uuid}/file_downloaded",
            f"https://data.mendeley.com/public-files/datasets/{DATASET}/files/{uuid}/file_downloaded?version=1",
            f"https://api.data.mendeley.com/datasets/{DATASET}/files/{uuid}/file_downloaded?version=1",
        ])
    for url in dict.fromkeys(candidate_urls[:100]):
        try:
            r = session.get(url, timeout=60, allow_redirects=True, stream=True)
            first = next(r.iter_content(1024), b"")
            probes.append({
                "url": url,
                "status": r.status_code,
                "final_url": r.url,
                "content_type": r.headers.get("content-type"),
                "content_length": r.headers.get("content-length"),
                "first_sha256": hashlib.sha256(first).hexdigest(),
                "first_text": first[:300].decode("utf-8", errors="replace"),
            })
        except Exception as error:
            probes.append({"url": url, "error": repr(error)})
    payload = {
        "page": PAGE,
        "status": response.status_code,
        "content_type": response.headers.get("content-type"),
        "bytes": len(response.content),
        "sha256": hashlib.sha256(response.content).hexdigest(),
        "anchor_found": anchor >= 0,
        "uuids": uuids,
        "interesting_urls": interesting_urls,
        "relative_download_paths": relative,
        "snippets": snippets,
        "scripts": scripts,
        "probes": probes,
    }
    (OUT / "lookup_access_probe.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    viable = [probe for probe in probes if probe.get("status") == 200 and (int(probe.get("content_length") or 0) > 1000000 or "text/plain" in str(probe.get("content_type")))]
    verdict = "PUBLIC_DOWNLOAD_ROUTE_FOUND" if viable else "PUBLIC_DOWNLOAD_ROUTE_NOT_FOUND"
    (OUT / "LOOKUP_ACCESS_PROBE.md").write_text(
        "# Lookup-table public access probe\n\n"
        f"**Verdict:** `{verdict}`\n\n"
        f"- Page bytes: **{len(response.content):,}**\n"
        f"- UUIDs found: **{len(uuids)}**\n"
        f"- Candidate download paths: **{len(candidate_urls)}**\n"
        f"- Viable responses: **{len(viable)}**\n",
        encoding="utf-8",
    )
    print(json.dumps({"verdict": verdict, "uuids": uuids, "interesting_urls": interesting_urls[:20], "viable": viable}, indent=2))


if __name__ == "__main__":
    main()
