#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlencode

import requests

OUT = Path(__file__).resolve().parent / "results"
BASES = ["https://data.mendeley.com/oai", "https://data.mendeley.com/oai/request"]
TARGETS = ("t2rrdtzd8h", "10.17632/t2rrdtzd8h.1", "meteor shower look-up table")


def fetch(base: str, params: dict[str, str]) -> dict[str, object]:
    url = base + "?" + urlencode(params)
    response = requests.get(url, timeout=180, headers={"User-Agent": "GhostStream-reproducibility-audit/1.0"})
    return {
        "url": url,
        "status": response.status_code,
        "content_type": response.headers.get("content-type"),
        "bytes": len(response.content),
        "sha256": hashlib.sha256(response.content).hexdigest(),
        "text": response.text[:5_000_000],
    }


def record_fragments(text: str) -> list[str]:
    lowered = text.lower()
    if not any(target.lower() in lowered for target in TARGETS):
        return []
    fragments = []
    for match in re.finditer(r"<record\b.*?</record>", text, flags=re.I | re.S):
        fragment = match.group(0)
        if any(target.lower() in fragment.lower() for target in TARGETS):
            fragments.append(fragment)
    if not fragments:
        for target in TARGETS:
            index = lowered.find(target.lower())
            if index >= 0:
                fragments.append(text[max(0, index-5000):index+10000])
    return fragments


def extract(fragment: str) -> dict[str, object]:
    urls = sorted(set(re.findall(r"https?://[^<\s\"']+", fragment)))
    uuids = sorted(set(re.findall(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b", fragment)))
    identifiers = re.findall(r"<identifier[^>]*>(.*?)</identifier>", fragment, flags=re.I | re.S)
    return {"urls": urls, "uuids": uuids, "identifiers": identifiers, "fragment": fragment}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    attempts = []
    found = []
    for base in BASES:
        requests_to_try = [
            {"verb": "Identify"},
            {"verb": "ListRecords", "metadataPrefix": "oai_dc", "from": "2018-02-26", "until": "2018-03-01"},
            {"verb": "ListIdentifiers", "metadataPrefix": "oai_dc", "from": "2018-02-26", "until": "2018-03-01"},
        ]
        for identifier in (
            "oai:data.mendeley.com:t2rrdtzd8h",
            "oai:data.mendeley.com:10.17632/t2rrdtzd8h.1",
            "oai:data.mendeley.com:dataset-t2rrdtzd8h",
        ):
            requests_to_try.append({"verb": "GetRecord", "metadataPrefix": "oai_dc", "identifier": identifier})
        for params in requests_to_try:
            try:
                result = fetch(base, params)
                fragments = record_fragments(str(result["text"]))
                attempts.append({key: value for key, value in result.items() if key != "text"} | {"params": params, "target_fragments": len(fragments), "prefix": str(result["text"])[:1000]})
                found.extend(extract(fragment) for fragment in fragments)
            except Exception as error:
                attempts.append({"base": base, "params": params, "error": repr(error)})
    all_urls = sorted({url for item in found for url in item["urls"]})
    all_uuids = sorted({uuid for item in found for uuid in item["uuids"]})
    payload = {
        "attempts": attempts,
        "records_found": len(found),
        "urls": all_urls,
        "uuids": all_uuids,
        "records": found,
    }
    (OUT / "oai_lookup_probe.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    useful = [url for url in all_urls if any(token in url.lower() for token in ("download", "file", "dans", "archive"))]
    verdict = "OAI_FILE_ROUTE_FOUND" if useful or all_uuids else ("OAI_RECORD_FOUND_NO_FILE_ROUTE" if found else "OAI_RECORD_NOT_FOUND")
    (OUT / "OAI_LOOKUP_PROBE.md").write_text(
        "# OAI metadata probe\n\n"
        f"**Verdict:** `{verdict}`\n\n"
        f"- Target records found: **{len(found)}**\n"
        f"- UUIDs found: **{len(all_uuids)}**\n"
        f"- URLs found: **{len(all_urls)}**\n"
        f"- File/archive-like URLs: **{len(useful)}**\n",
        encoding="utf-8",
    )
    print(json.dumps({"verdict": verdict, "records": len(found), "uuids": all_uuids, "useful_urls": useful}, indent=2))


if __name__ == "__main__":
    main()
