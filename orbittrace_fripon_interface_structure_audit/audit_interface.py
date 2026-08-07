#!/usr/bin/env python3
"""Frozen pre-scientific FRIPON public-interface structure audit."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import urlparse

import requests

LIST_URL = "https://fireball.fripon.org/list_multiple.php"
RELEASE_URL = "https://fireball.fripon.org/list_pipeline.php"
EXAMPLE_URL = "https://fireball.fripon.org/displaymultiple.php?id=19701"
FIXED_URLS = (LIST_URL, RELEASE_URL, EXAMPLE_URL)
REQUIRED_PIPELINE_LABELS = (
    "multiple id",
    "multiple folder",
    "multiple count",
    "multiple status",
    "orbit perifocal",
    "orbit eccentricity",
    "orbit inclination",
    "orbit longitude",
    "orbit argument",
    "orbit epoch",
    "orbit semiaxis",
    "trajectory VE",
    "trajectory RadianRA",
    "trajectory RadianDec",
)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def fetch(url: str) -> dict:
    r = requests.get(
        url,
        timeout=120,
        headers={"User-Agent": "OrbitTrace-FRIPON-interface-structure-audit/1.0"},
    )
    raw = r.content
    return {
        "url": url,
        "status": int(r.status_code),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "html": raw.decode("utf-8", errors="replace"),
    }


def visible_text(source: str) -> str:
    x = re.sub(r"<script\b[^>]*>.*?</script>", " ", source, flags=re.I | re.S)
    x = re.sub(r"<style\b[^>]*>.*?</style>", " ", x, flags=re.I | re.S)
    x = re.sub(r"<[^>]+>", " ", x)
    return re.sub(r"\s+", " ", html.unescape(x)).strip()


def route_basenames(source: str) -> list[str]:
    routes = set()
    for m in re.finditer(r"[A-Za-z0-9_./?-]+\.php(?:\?[^\"'<>\s]*)?", source, flags=re.I):
        token = html.unescape(m.group(0))
        base = urlparse(token).path.rsplit("/", 1)[-1]
        if base:
            routes.add(base)
    return sorted(routes)


def script_basenames(source: str) -> list[str]:
    out = set()
    for m in re.finditer(r"<script\b[^>]*\bsrc=[\"']([^\"']+)[\"']", source, flags=re.I):
        base = urlparse(html.unescape(m.group(1))).path.rsplit("/", 1)[-1]
        if base:
            out.add(base)
    return sorted(out)


def initial_table_rows(source: str) -> int:
    bodies = re.findall(r"<tbody\b[^>]*>(.*?)</tbody>", source, flags=re.I | re.S)
    return sum(len(re.findall(r"<tr\b", body, flags=re.I)) for body in bodies)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--freshness-json", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    fresh = json.loads(a.freshness_json.read_text())
    require(fresh["verdict"] == "PASS_FRIPON_2018_2019_REPO_SCIENTIFIC_FRESHNESS_AUDIT", "freshness prerequisite failed")
    require(fresh["potential_exposure_hit_count"] == 0, "FRIPON exposure hit appeared")
    require(all(fresh["positive_controls"].values()), "freshness positive control failed")
    require(fresh["catalogue_access_this_audit"] is False, "freshness crossed catalogue boundary")
    require(fresh["fripon_web_or_api_contacted"] is False, "freshness contacted FRIPON")
    require(fresh["scientific_value_access_this_audit"] is False, "freshness inspected science")
    require(fresh["orbittrace_target_information_access"] is False, "freshness accessed target")

    # Fixed URLs are source literals. No dynamic search, event selection, or fallback exists.
    require(all("2018" not in u and "2019" not in u for u in FIXED_URLS), "reserved year in fixed URL")
    pages = {url: fetch(url) for url in FIXED_URLS}
    all_http_200 = all(pages[u]["status"] == 200 for u in FIXED_URLS)

    list_html = pages[LIST_URL]["html"]
    release_html = pages[RELEASE_URL]["html"]
    example_html = pages[EXAMPLE_URL]["html"]
    list_text = visible_text(list_html)
    release_text = visible_text(release_html)
    example_text = visible_text(example_html)

    row_count = initial_table_rows(list_html)
    list_semantics = {
        "one_multiple_event_per_row": bool(re.search(r"one\s+per\s+row", list_text, re.I)),
        "date_format_documented": "YYYY-MM-DD hh:mm:ss" in list_text,
        "id_column": bool(re.search(r"\b(?:ID|Identifier)\b", list_text)),
        "event_date_column": "Event date" in list_text,
        "count_column": bool(re.search(r"\bCount\b", list_text)),
        "status_column": bool(re.search(r"\bStatus\b", list_text)),
        "stations_column": bool(re.search(r"Station(?:s)? involved|Station involved", list_text, re.I)),
        "initial_html_has_zero_event_rows": row_count == 0,
    }
    release_semantics = {
        "yearly_release_from_2021": bool(re.search(r"From\s+2021\s+onwards.*yearly basis", release_text, re.I)),
        "orbital_parameters_named": bool(re.search(r"orbital parameters", release_text, re.I)),
        "pre_atmospheric_speed_named": bool(re.search(r"pre-atmospheric speed", release_text, re.I)),
        "radiant_named": bool(re.search(r"\bRadiant\b", release_text)),
        "radian_ra_column_named": bool(re.search(r"Radian\s+RA", release_text, re.I)),
        "radian_dec_column_named": bool(re.search(r"Radian\s+Dec", release_text, re.I)),
        "ve_column_named": bool(re.search(r"\bVE\b", release_text)),
    }
    example_structure = {
        "fixed_2022_event_header": bool(re.search(r"Multiple event\s+2022-12-25\s+17:30:48\s+UTC", example_text, re.I)),
        "pipeline_content_section": "Pipeline content" in example_text,
        "required_field_labels": {
            label: bool(re.search(rf"\b{re.escape(label)}\s*:", example_text, re.I))
            for label in REQUIRED_PIPELINE_LABELS
        },
    }

    gates = {
        "all_http_200": all_http_200,
        "multiple_list_semantics": all(list_semantics.values()),
        "data_release_semantics": all(release_semantics.values()),
        "fixed_example_structure": example_structure["fixed_2022_event_header"]
        and example_structure["pipeline_content_section"]
        and all(example_structure["required_field_labels"].values()),
        "no_reserved_year_url": all("2018" not in u and "2019" not in u for u in FIXED_URLS),
        "no_embedded_multiple_event_rows": row_count == 0,
    }
    verdict = (
        "PASS_FRIPON_PUBLIC_INTERFACE_STRUCTURE_AUDIT"
        if all(gates.values())
        else "FAIL_FRIPON_PUBLIC_INTERFACE_STRUCTURE_AUDIT"
    )

    page_provenance = {
        url: {
            "status": pages[url]["status"],
            "bytes": pages[url]["bytes"],
            "sha256": pages[url]["sha256"],
            "php_route_basenames": route_basenames(pages[url]["html"]),
            "script_basenames": script_basenames(pages[url]["html"]),
        }
        for url in FIXED_URLS
    }
    result = {
        "verdict": verdict,
        "fixed_urls": list(FIXED_URLS),
        "page_provenance": page_provenance,
        "multiple_list": list_semantics,
        "data_release": release_semantics,
        "example_event": example_structure,
        "gates": gates,
        "reserved_2018_2019_requested": False,
        "reserved_event_identifier_access": False,
        "scientific_numeric_values_parsed_or_reported": False,
        "source_or_shower_label_values_inspected": False,
        "v8_method_evaluation_performed": False,
        "orbittrace_target_information_access": False,
        "bulk_reserved_enumeration_transport_established": False,
        "geocentric_geometry_equivalence_established": False,
        "raw_html_persisted": False,
        "claim_boundary": (
            "Pre-scientific public-interface structure only. The audit queried exactly the public multiple-event index, data-release page, and one fixed released 2022 event. It records structural labels/routes/hashes only, does not parse or report numeric event science, and makes no 2018/2019 request. A pass does not yet establish reserved-year bulk enumeration or geocentric radiant/speed equivalence."
        ),
    }
    (a.output / "fripon_public_interface_structure_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if verdict.startswith("FAIL_"):
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
