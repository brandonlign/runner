#!/usr/bin/env python3
"""Pre-scientific Hissar 1968 matched-coverage eligibility adjudication.

Only public metadata pages and frozen repository source are read. No catalogue form is
submitted and no Hissar meteor row is requested or inspected.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path

IAU_URL = "https://ceres.ta3.sk/iaumdcdb/home/catalog/radio"
JPL_URL = "https://ssd.jpl.nasa.gov/planets/approx_pos.html"
V6_BLOB_SHA = "7995fc6b75d1fd51eb4b304ace39db28a5a1e876"
REQUIRED_SCANNABLE_BINS = 24
BIN_WIDTH_DEG = 10.0
LOOSE_SOLAR_RATE_DEG_PER_DAY = 1.1

# NASA/JPL EM-barycenter Table 2a constants, 3000 BC--3000 AD.
JPL_E0 = 0.01673163
JPL_EDOT_PER_CENTURY = -0.00003661
JPL_LDOT_DEG_PER_CENTURY = 35999.37306329
JPL_VARPIDOT_DEG_PER_CENTURY = 0.31795260


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())

    def text(self) -> str:
        return " ".join(self.parts)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url: str, path: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "OrbitTrace-Hissar-coverage-adjudication/1.0"})
    with urllib.request.urlopen(req, timeout=180) as response, path.open("wb") as fh:
        if response.status != 200:
            raise RuntimeError(f"metadata GET failed: {url} status={response.status}")
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            fh.write(chunk)


def html_text(path: Path) -> str:
    parser = TextExtractor()
    parser.feed(html.unescape(path.read_text(errors="replace")))
    return re.sub(r"\s+", " ", parser.text()).strip()


def julian_day(dt: datetime) -> float:
    """Gregorian UTC-like calendar to JD; sub-second precision is immaterial here."""
    y = dt.year
    m = dt.month
    day = dt.day + (dt.hour + (dt.minute + (dt.second + dt.microsecond / 1e6) / 60.0) / 60.0) / 24.0
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + day + b - 1524.5


def century_from_j2000(dt: datetime) -> float:
    return (julian_day(dt) - 2451545.0) / 36525.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v6-source", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    # Frozen repository rule checks. git blob SHA is enforced again by workflow.
    src = args.v6_source.read_text(errors="replace")
    source_gates = {
        "min_scannable_bins_24": "MIN_SCANNABLE_BINS=24" in src,
        "exact_36_bin_loop": "for bin_index in range(36):" in src,
        "exact_10deg_bins": "low=bin_index*10.0; high=(bin_index+1)*10.0; center=low+5.0" in src,
        "anchors_inside_own_bin": "anchors=[e for e in events if low <= float(e['sol']) < high]" in src,
        "unanchored_bin_not_scannable": "if len(pool) < AUDIT_SHORTLIST or not anchors:" in src,
        "audit_shortlist_128": "AUDIT_SHORTLIST=128" in src,
        "scannable_append_after_gate": "scannable_bins.append(bin_index)" in src,
    }
    if not all(source_gates.values()):
        raise RuntimeError(f"frozen v6 coverage source gates changed: {source_gates}")

    iau_path = args.output / "iau_radio.html"
    jpl_path = args.output / "jpl_approx_pos.html"
    fetch(IAU_URL, iau_path)
    fetch(JPL_URL, jpl_path)
    iau_hash = sha256(iau_path)
    jpl_hash = sha256(jpl_path)
    iau = html_text(iau_path)
    jpl = html_text(jpl_path)

    # Metadata only: exact published overall Hissar start. No form submission.
    extent_match = re.search(
        r"Extent of data from\s+1968\s+12\s+12\.73530\s+to\s+1969\s+12\s+24\.18900",
        iau,
        re.I,
    )
    if not extent_match:
        raise RuntimeError("published Hissar extent changed or could not be verified")
    if "Hissar" not in iau or "iaumdcHIS1" not in iau:
        raise RuntimeError("Hissar metadata selector changed")

    # Verify the exact JPL Table 2a constants are still published by the primary source.
    jpl_gates = {
        "em_bary_table2a_e0": "0.01673163" in jpl,
        "em_bary_table2a_edot": "-0.00003661" in jpl,
        "em_bary_table2a_ldot": "35999.37306329" in jpl,
        "em_bary_table2a_varpidot": "0.31795260" in jpl,
        "valid_3000bc_3000ad": "3000 BC -- 3000 AD" in jpl or "3000 BC – 3000 AD" in jpl or "3000 BC — 3000 AD" in jpl,
    }
    if not all(jpl_gates.values()):
        raise RuntimeError(f"JPL primary-source constants changed or unavailable: {jpl_gates}")

    # Day 12.73530 means Dec 12 plus 0.73530 day. Give Hissar the entire rest of
    # calendar 1968, which is the most favorable possible bound for scannability.
    start = datetime(1968, 12, 12, tzinfo=timezone.utc) + timedelta(days=0.73530)
    end = datetime(1969, 1, 1, tzinfo=timezone.utc)
    duration_days = (end - start).total_seconds() / 86400.0
    if not (19.0 < duration_days < 20.0):
        raise RuntimeError(f"unexpected 1968 maximum duration: {duration_days}")

    t0 = century_from_j2000(start)
    t1 = century_from_j2000(end)
    e0 = JPL_E0 + JPL_EDOT_PER_CENTURY * t0
    e1 = JPL_E0 + JPL_EDOT_PER_CENTURY * t1
    emax = max(e0, e1)
    mean_anomaly_rate = (JPL_LDOT_DEG_PER_CENTURY - JPL_VARPIDOT_DEG_PER_CENTURY) / 36525.0
    max_true_anomaly_factor = (1.0 + emax) ** 2 / (1.0 - emax * emax) ** 1.5
    jpl_model_max_longitude_rate = (
        mean_anomaly_rate * max_true_anomaly_factor
        + abs(JPL_VARPIDOT_DEG_PER_CENTURY) / 36525.0
    )
    if not jpl_model_max_longitude_rate < LOOSE_SOLAR_RATE_DEG_PER_DAY:
        raise RuntimeError(
            f"pre-frozen 1.1 deg/day conservative envelope not above JPL model maximum: {jpl_model_max_longitude_rate}"
        )

    max_solar_arc_deg = LOOSE_SOLAR_RATE_DEG_PER_DAY * duration_days
    max_intersected_bins = math.ceil(max_solar_arc_deg / BIN_WIDTH_DEG) + 1
    eligibility = max_intersected_bins >= REQUIRED_SCANNABLE_BINS
    verdict = (
        "PASS_HISSAR_1968_COVERAGE_ELIGIBILITY"
        if eligibility
        else "FAIL_HISSAR_1968_COVERAGE_ELIGIBILITY"
    )

    result = {
        "verdict": verdict,
        "v6_blob_sha_expected": V6_BLOB_SHA,
        "source_gates": source_gates,
        "required_scannable_bins_per_year": REQUIRED_SCANNABLE_BINS,
        "fixed_bin_width_deg": BIN_WIDTH_DEG,
        "published_hissar_extent": "1968-12-12.73530 to 1969-12-24.18900",
        "maximally_favorable_1968_start_utc": start.isoformat(),
        "maximally_favorable_1968_end_utc": end.isoformat(),
        "maximally_favorable_1968_duration_days": duration_days,
        "jpl_primary_url": JPL_URL,
        "jpl_metadata_sha256": jpl_hash,
        "jpl_gates": jpl_gates,
        "jpl_eccentricity_max_1968_window": emax,
        "jpl_model_max_solar_longitude_rate_deg_per_day": jpl_model_max_longitude_rate,
        "frozen_loose_rate_envelope_deg_per_day": LOOSE_SOLAR_RATE_DEG_PER_DAY,
        "max_possible_1968_solar_longitude_arc_deg_under_loose_envelope": max_solar_arc_deg,
        "max_possible_distinct_10deg_bins_intersected": max_intersected_bins,
        "iau_primary_url": IAU_URL,
        "iau_metadata_sha256": iau_hash,
        "hissar_catalogue_form_submitted": False,
        "hissar_result_or_download_endpoint_contacted": False,
        "hissar_meteor_row_access": False,
        "scientific_event_values_inspected": False,
        "source_or_shower_labels_inspected": False,
        "excluded_interval_contents_accessed": False,
        "orbittrace_target_information_access": False,
        "v8_modified": False,
        "coverage_floor_lowered": False,
        "claim_boundary": (
            "Pre-scientific metadata/source adjudication only. The maximum possible 1968 Hissar observing duration is bounded from the published start through year-end, and a deliberately loose solar-longitude rate envelope yields an upper bound on occupied 10-degree bins. Because a scannable bin must contain anchors, the number of scannable bins cannot exceed this occupied-bin upper bound. A FAIL is a panel coverage/data-availability limitation, not a v8 performance result."
        ),
    }
    (args.output / "hissar_1968_coverage_eligibility.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))

    # Metadata pages are not retained in the artifact.
    iau_path.unlink()
    jpl_path.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
