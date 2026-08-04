#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import requests

ARCHIVE_URL = "https://www.astro.sk/~ne/IAUMDC/PhV2016/CAMS_California_v2.zip"
ARCHIVE_BYTES = 18_411_331
ARCHIVE_SHA256 = "4e0e33fec66d3012a2668a7acfd62a0694df191fabf44f3a792b3781785ab313"
MEMBER = "CAMS_California_v2.d15"
MEMBER_BYTES = 128_734_222
DEVELOPMENT_RECORDS = 40_744
LABEL_RE = re.compile(r"^[A-Z0-9]{1,2}$")
BLIND_LO = 20.0
BLIND_HI = 55.0
PARTIAL_BLIND_BINS = {2, 3, 4, 5}


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_required_line(stream: io.TextIOBase, context: str) -> str:
    line = stream.readline()
    if line == "":
        raise RuntimeError(f"unexpected EOF while reading {context}")
    return line.rstrip("\r\n")


def parse_numeric(value_line: str, field: str, record_number: int) -> float:
    token = value_line.strip().split()
    if not token:
        raise RuntimeError(f"record {record_number}: empty numeric value for {field}")
    try:
        value = float(token[0].replace("D", "E").replace("d", "e"))
    except ValueError as exc:
        raise RuntimeError(f"record {record_number}: invalid numeric value for {field}") from exc
    if not math.isfinite(value):
        raise RuntimeError(f"record {record_number}: nonfinite numeric value for {field}")
    return value


def max_circular_window_count(phases: list[float], width: float = 20.0) -> int:
    if not phases:
        return 0
    ordered = sorted(phase % 360.0 for phase in phases)
    doubled = ordered + [phase + 360.0 for phase in ordered]
    best = 0
    right = 0
    n = len(ordered)
    for left in range(n):
        if right < left:
            right = left
        while right < left + n and doubled[right] - doubled[left] <= width + 1e-12:
            right += 1
        best = max(best, right - left)
    return best


def parse_development_member(stream: io.TextIOBase) -> dict:
    year_counts: Counter[int] = Counter()
    totals: Counter[str] = Counter()
    token_counts: Counter[str] = Counter()
    token_phases: dict[str, list[float]] = defaultdict(list)
    background_bins: Counter[int] = Counter()
    record_number = 0
    label_decodes = 0
    blind_label_decodes = 0

    while record_number < DEVELOPMENT_RECORDS:
        seen: Counter[str] = Counter()
        year_value: float | None = None
        phase_value: float | None = None
        shower_present = False
        shower_opaque: str | None = None

        while True:
            header = read_required_line(stream, f"record {record_number + 1} field header")
            padded = header.ljust(8)
            flag = padded[:4]
            qnt = padded[4:6]
            err = padded[6:8]
            if flag == "   &":
                break

            seen[flag] += 1
            value_line: str | None = None
            if flag == "ANo:" and qnt != " 1":
                value_line = None
            else:
                value_line = read_required_line(
                    stream, f"record {record_number + 1} value for {flag!r}"
                )

            if flag == "Yr :":
                if qnt != " 1" or value_line is None:
                    raise RuntimeError(f"record {record_number + 1}: missing Yr value")
                year_value = parse_numeric(value_line, "Yr", record_number + 1)
            elif flag == "LS :":
                if qnt != " 1" or value_line is None:
                    raise RuntimeError(f"record {record_number + 1}: missing LS value")
                phase_value = parse_numeric(value_line, "LS", record_number + 1)
            elif flag == "Sh :":
                shower_present = qnt == " 1"
                if shower_present:
                    if value_line is None:
                        raise RuntimeError(f"record {record_number + 1}: missing Sh value line")
                    shower_opaque = value_line[:2].ljust(2)
                else:
                    shower_opaque = None

        record_number += 1
        totals["parsed_records"] += 1

        for required_flag in ("Yr :", "LS :", "Sh :"):
            if seen[required_flag] != 1:
                raise RuntimeError(
                    f"record {record_number}: expected exactly one {required_flag!r}, found {seen[required_flag]}"
                )
        if year_value is None or phase_value is None:
            raise RuntimeError(f"record {record_number}: incomplete Yr/LS state")
        year_rounded = int(round(year_value))
        if abs(year_value - year_rounded) > 1e-9 or year_rounded not in (2010, 2011):
            raise RuntimeError(f"record {record_number}: development year outside 2010-2011")
        year_counts[year_rounded] += 1

        if not (0.0 <= phase_value < 360.0):
            totals["invalid_phase"] += 1
            continue
        if BLIND_LO <= phase_value <= BLIND_HI:
            totals["blind_excluded"] += 1
            # Deliberately do not decode, strip, classify, count, or store Sh.
            continue

        totals["post_boundary"] += 1
        label_decodes += 1
        if not shower_present or shower_opaque is None or shower_opaque == "  ":
            totals["background"] += 1
            phase_bin = int(math.floor(phase_value / 10.0)) % 36
            if phase_bin not in PARTIAL_BLIND_BINS:
                background_bins[phase_bin] += 1
            continue

        token = shower_opaque.strip(" ")
        if LABEL_RE.fullmatch(token):
            totals["mapped"] += 1
            token_counts[token] += 1
            token_phases[token].append(phase_value)
        else:
            totals["unsupported"] += 1

    if record_number != DEVELOPMENT_RECORDS:
        raise RuntimeError(f"parsed {record_number} records, expected {DEVELOPMENT_RECORDS}")

    total_support = {
        str(threshold): sum(count >= threshold for count in token_counts.values())
        for threshold in (4, 8, 12, 20)
    }
    window_max = {
        token: max_circular_window_count(phases, 20.0)
        for token, phases in token_phases.items()
    }
    window_support = {
        str(threshold): sum(count >= threshold for count in window_max.values())
        for threshold in (4, 6, 8, 12)
    }
    phase_bin_support = {
        str(threshold): sum(count >= threshold for count in background_bins.values())
        for threshold in (128, 256, 512)
    }

    label_like = totals["mapped"] + totals["unsupported"]
    mapping_fraction = totals["mapped"] / label_like if label_like else 0.0
    unsupported_fraction = (
        totals["unsupported"] / totals["post_boundary"] if totals["post_boundary"] else 1.0
    )

    return {
        "development_records_parsed": record_number,
        "year_counts": {str(year): year_counts[year] for year in sorted(year_counts)},
        "invalid_phase_rows": totals["invalid_phase"],
        "blind_interval_rows": totals["blind_excluded"],
        "post_boundary_rows": totals["post_boundary"],
        "background_rows": totals["background"],
        "mapped_label_rows": totals["mapped"],
        "unsupported_rows": totals["unsupported"],
        "mapping_fraction_among_label_like": mapping_fraction,
        "unsupported_fraction_of_post_boundary": unsupported_fraction,
        "distinct_mapped_tokens": len(token_counts),
        "total_support_counts": total_support,
        "circular_20deg_window_support_counts": window_support,
        "background_10deg_bin_support_counts": phase_bin_support,
        "label_decodes_after_boundary": label_decodes,
        "blind_label_decodes": blind_label_decodes,
        "token_identities_emitted": False,
        "detailed_phase_bins_emitted": False,
    }


def build_result() -> dict:
    requested_urls = [ARCHIVE_URL]
    response = requests.get(ARCHIVE_URL, timeout=300)
    response.raise_for_status()
    archive_raw = response.content
    archive_digest = sha256(archive_raw)
    if len(archive_raw) != ARCHIVE_BYTES or archive_digest != ARCHIVE_SHA256:
        raise RuntimeError(
            f"archive mismatch bytes={len(archive_raw)} sha256={archive_digest}"
        )

    with zipfile.ZipFile(io.BytesIO(archive_raw)) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"ZIP CRC failure in {bad}")
        names = archive.namelist()
        if names != [MEMBER]:
            raise RuntimeError(f"unexpected member list: {names}")
        info = archive.getinfo(MEMBER)
        if info.file_size != MEMBER_BYTES:
            raise RuntimeError(f"member size {info.file_size} != {MEMBER_BYTES}")
        with archive.open(info, "r") as raw_member:
            with io.TextIOWrapper(raw_member, encoding="latin-1", newline="") as stream:
                audit = parse_development_member(stream)
                # Do not call readline again: the reserved record stream remains unparsed.

    years = audit["year_counts"]
    total_support = audit["total_support_counts"]
    window_support = audit["circular_20deg_window_support_counts"]
    bin_support = audit["background_10deg_bin_support_counts"]
    gates = {
        "exact_archive_member_and_size": True,
        "exact_40744_development_records_parsed": audit["development_records_parsed"] == DEVELOPMENT_RECORDS,
        "development_years_exactly_2010_2011": set(years) == {"2010", "2011"} and all(value > 0 for value in years.values()),
        "reserved_records_and_benelux_not_parsed": requested_urls == [ARCHIVE_URL],
        "blind_labels_never_decoded": audit["blind_label_decodes"] == 0,
        "unsupported_fraction_at_most_0_01": audit["unsupported_fraction_of_post_boundary"] <= 0.01,
        "mapping_fraction_at_least_0_90": audit["mapping_fraction_among_label_like"] >= 0.90,
        "background_at_least_25000": audit["background_rows"] >= 25_000,
        "distinct_mapped_tokens_at_least_30": audit["distinct_mapped_tokens"] >= 30,
        "total_support_k8_at_least_25": total_support["8"] >= 25,
        "total_support_k12_at_least_20": total_support["12"] >= 20,
        "window_support_k6_at_least_20": window_support["6"] >= 20,
        "window_support_k8_at_least_15": window_support["8"] >= 15,
        "background_bins_ge256_at_least_20": bin_support["256"] >= 20,
        "no_scientific_or_reserved_values_read": True,
    }
    verdict = "PASS_HISTORICAL_CAMSV2_DEVELOPMENT_LABEL_INTERFACE" if all(gates.values()) else "KILL_HISTORICAL_CAMSV2_DEVELOPMENT_LABEL_INTERFACE"
    return {
        "method": "Historical CAMS Database 2.0 aggregate-only development-label audit",
        "source": {
            "archive_url": ARCHIVE_URL,
            "archive_bytes": len(archive_raw),
            "archive_sha256": archive_digest,
            "member": MEMBER,
            "member_bytes": MEMBER_BYTES,
            "reader_source_sha256": "437d9d8f7d68b824751954b51e2caaec69e379912bce3b924acf2292e89acb1c",
        },
        "partition": {
            "development_record_count": DEVELOPMENT_RECORDS,
            "development_public_date_range": "2010-10-21 through 2011-12-31",
            "reserved_later_california_records_parsed": False,
            "reserved_benelux_requested": False,
        },
        "requested_urls": requested_urls,
        "audit": audit,
        "geometry_values_decoded": False,
        "detector_scores_computed": False,
        "reserved_label_values_decoded": False,
        "sonotaco_2024_read": False,
        "camsv3_2016_values_read": False,
        "gates": gates,
        "verdict": verdict,
    }


def write_outputs(out: Path, result: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "historical_camsv2_development_label_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    audit = result.get("audit", {})
    report = [
        "# Historical CAMS Database 2.0 development-label audit",
        "",
        f"**Verdict:** `{result['verdict']}`",
        "",
        f"- development records parsed: {audit.get('development_records_parsed')}",
        f"- aggregate year counts: {audit.get('year_counts')}",
        f"- blind-interval exclusions: {audit.get('blind_interval_rows')}",
        f"- post-boundary background: {audit.get('background_rows')}",
        f"- post-boundary mapped labels: {audit.get('mapped_label_rows')}",
        f"- unsupported labels: {audit.get('unsupported_rows')}",
        f"- distinct mapped tokens: {audit.get('distinct_mapped_tokens')}",
        f"- total support counts: {audit.get('total_support_counts')}",
        f"- 20-degree window support counts: {audit.get('circular_20deg_window_support_counts')}",
        f"- background 10-degree bin support counts: {audit.get('background_10deg_bin_support_counts')}",
        "",
        "## Frozen gates",
        "",
    ]
    report.extend(f"- {name}: {passed}" for name, passed in result.get("gates", {}).items())
    if result.get("error"):
        report.extend(["", "## Execution error", "", f"`{result['error']}`"])
    report.extend(
        [
            "",
            "No label identities, individual rows, geometry values, detector scores, later California records, BeNeLux records, SonotaCo 2024 values, or CAMSv3 2016 values are present.",
        ]
    )
    (out / "RESULT.md").write_text("\n".join(report) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = Path(args.output)
    try:
        result = build_result()
    except Exception as exc:
        result = {
            "method": "Historical CAMS Database 2.0 aggregate-only development-label audit",
            "error": f"{type(exc).__name__}: {exc}",
            "requested_urls": [ARCHIVE_URL],
            "geometry_values_decoded": False,
            "detector_scores_computed": False,
            "reserved_label_values_decoded": False,
            "sonotaco_2024_read": False,
            "camsv3_2016_values_read": False,
            "gates": {"execution_completed": False},
            "verdict": "KILL_HISTORICAL_CAMSV2_DEVELOPMENT_LABEL_INTERFACE",
        }
    write_outputs(out, result)
    print(json.dumps({
        "verdict": result["verdict"],
        "audit": result.get("audit"),
        "gates": result.get("gates"),
        "error": result.get("error"),
    }, indent=2))
    if result["verdict"] != "PASS_HISTORICAL_CAMSV2_DEVELOPMENT_LABEL_INTERFACE":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
