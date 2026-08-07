#!/usr/bin/env python3
"""Pre-scientific recurrence eligibility adjudication for Harvard 1968-1969.

Only public metadata/literature responses and the prior structure-audit JSON are read.
The har6869 scientific table is never downloaded, opened, or decompressed.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any

import requests

PDS_URL = "https://pds.nasa.gov/ds-view/pds/viewProfile.jsp?dsid=EAR-A-VARGBDET-5-METORB-V1.0"
# Transport-only correction after run 31226879496: use the official unauthenticated
# NTRS GET /citations/{id} API rather than the browser-route HTML page that timed out.
NTRS_URL = "https://ntrs.nasa.gov/api/citations/19760042403"
MNRAS_URL = "https://academic.oup.com/mnras/article-abstract/353/2/422/1106062"
URLS = (PDS_URL, NTRS_URL, MNRAS_URL)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def normalized_text(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="replace")
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip().lower()


def fetch(url: str) -> dict[str, Any]:
    try:
        r = requests.get(
            url,
            timeout=120,
            headers={"User-Agent": "OrbitTrace-Harvard-recurrence-metadata-audit/1.0"},
        )
        status = int(r.status_code)
        raw = r.content
        text = normalized_text(raw) if status == 200 else ""
        return {
            "url": url,
            "status": status,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "text": text,
            "error": None,
        }
    except Exception as exc:
        return {"url": url, "status": None, "sha256": None, "bytes": 0, "text": "", "error": repr(exc)}


def has_all(text: str, phrases: tuple[str, ...]) -> bool:
    return all(p.lower() in text for p in phrases)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--structure-json", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    structure = json.loads(a.structure_json.read_text())
    require(structure["verdict"] == "PASS_HARVARD_1968_1969_STRUCTURE_AUDIT", "structure prerequisite failed")
    require(structure["declared_record_counts"] == [19818], "Harvard declared record count changed")
    require(structure["target_member"]["path"].endswith("/har6869.tab"), "Harvard member changed")
    require(structure["target_member"]["opened"] is False, "Harvard table was already opened")
    require(structure["target_table_member_opened"] is False, "Harvard table was already opened")
    require(structure["scientific_event_values_inspected"] is False, "scientific values already inspected")
    require(structure["orbittrace_target_information_access"] is False, "target information entered prerequisite")

    fetched = {url: fetch(url) for url in URLS}
    pds = fetched[PDS_URL]
    ntrs = fetched[NTRS_URL]
    mnras = fetched[MNRAS_URL]

    pds_gate = pds["status"] == 200 and has_all(
        pds["text"],
        ("har6869.tab", "19,818", "harvard 1968-1969 survey"),
    )
    ntrs_gate = ntrs["status"] == 200 and has_all(
        ntrs["text"],
        ("synoptic-year sample", "19,698", "radio meteor project at havana"),
    )
    mnras_gate = mnras["status"] == 200 and (
        has_all(mnras["text"], ("synoptic year study", "synoptic year 1969", "2 × 10"))
        or has_all(mnras["text"], ("synoptic year study", "synoptic year 1969", "2 x 10"))
        or has_all(mnras["text"], ("synoptic year study", "synoptic year 1969", "close to 2"))
    )

    metadata_transport_sufficient = pds_gate and (ntrs_gate or mnras_gate)
    if not metadata_transport_sufficient:
        verdict = "INCONCLUSIVE_HARVARD_1968_1969_RECURRENCE_METADATA_TRANSPORT"
    else:
        # The fixed source facts establish one synoptic observing year spanning the
        # civil-year label 1968-1969, not two repeated annual cycles.
        verdict = "FAIL_HARVARD_1968_1969_V8_RECURRENCE_ELIGIBILITY"

    source_rows = []
    for url in URLS:
        row = dict(fetched[url])
        row.pop("text", None)
        source_rows.append(row)

    result = {
        "verdict": verdict,
        "candidate": "Harvard Radar Meteor Project 1968-1969 / har6869.tab",
        "declared_records": 19818,
        "source_checks": {
            "pds_har6869_1968_1969_19818": pds_gate,
            "ntrs_synoptic_year_1969_sample": ntrs_gate,
            "mnras_synoptic_year_1969_context": mnras_gate,
        },
        "metadata_transport_sufficient": metadata_transport_sufficient,
        "public_sources": source_rows,
        "ntrs_transport_correction_only": True,
        "prior_transport_run": 31226879496,
        "recurrence_semantics": "two genuine repeated observing-year panels required; civil-year split of one synoptic observing cycle forbidden",
        "har6869_table_downloaded": False,
        "har6869_table_opened": False,
        "scientific_event_values_inspected": False,
        "source_or_shower_labels_inspected": False,
        "method_evaluation_performed": False,
        "orbittrace_target_information_access": False,
        "claim_boundary": (
            "Public metadata/literature temporal-coverage adjudication only. The NTRS browser-route timeout from run 31226879496 is preserved; this retry changes only that transport to NASA's official unauthenticated citation API. When source transport succeeds, the Harvard 1968-1969 product is established as one synoptic-year observing program, so it cannot instantiate v8's two-independent-year recurrence test without an artificial civil-year split. No har6869 event record was downloaded or opened."
        ),
    }
    (a.output / "harvard_1968_1969_recurrence_eligibility.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    # A scientific eligibility FAIL is a successful adjudication execution.
    if verdict.startswith("INCONCLUSIVE_"):
        raise SystemExit(2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
