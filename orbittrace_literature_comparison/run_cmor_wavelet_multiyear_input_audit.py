#!/usr/bin/env python3
"""Audit seven-year SonotaCo support for a CMOR-style virtual-year wavelet transfer.

No wavelet coefficient, local maximum, shower label, or comparison endpoint is
computed. The audit freezes exact annual inputs and tests preregistered support
and exposure conditions that must pass before coefficient-level development.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import statistics
import zipfile
from pathlib import Path
from typing import Any

YEARS = tuple(range(2019, 2026))
BLIND_INTERVAL_DEG = (20.0, 55.0)
PUBLISHED_MINIMUM_RADIANTS = 300
PUBLISHED_MAX_TIME_GAP_DEG = 2
PUBLISHED_MINIMUM_LINKED_POINTS = 3
BREADTH_FRACTION = 0.80
MINIMUM_CONTRIBUTING_YEARS = 5
DOMINANCE_SHARE = 0.50
MAXIMUM_DOMINATED_FRACTION = 0.10
MINIMUM_THREE_POINT_CHAINS = 200


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-dir", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def finite_float(value: str) -> float:
    result = float(value.strip())
    if not math.isfinite(result):
        raise ValueError(value)
    return result


def percentile(values: list[float] | list[int], q: float) -> float:
    if not values:
        raise ValueError("empty percentile input")
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * q
    low = int(math.floor(position))
    high = int(math.ceil(position))
    if low == high:
        return ordered[low]
    weight = position - low
    return ordered[low] * (1.0 - weight) + ordered[high] * weight


def in_blind_interval(solar_longitude_deg: float) -> bool:
    low, high = BLIND_INTERVAL_DEG
    return low <= solar_longitude_deg <= high


def blind_bin(bin_index: int) -> bool:
    low, high = BLIND_INTERVAL_DEG
    return int(math.floor(low)) <= bin_index <= int(math.floor(high))


def linked_triplets(qualified: set[int]) -> set[tuple[int, int, int]]:
    chains: set[tuple[int, int, int]] = set()
    for first in range(360):
        if first not in qualified:
            continue
        for gap_one in range(1, PUBLISHED_MAX_TIME_GAP_DEG + 1):
            second = (first + gap_one) % 360
            if second not in qualified:
                continue
            for gap_two in range(1, PUBLISHED_MAX_TIME_GAP_DEG + 1):
                third = (second + gap_two) % 360
                if third in qualified:
                    chains.add((first, second, third))
    return chains


def longest_forward_chain(qualified: set[int]) -> int:
    if not qualified:
        return 0
    best = 1
    for start in sorted(qualified):
        distance_to_length = {0: 1}
        for distance in range(1, 360):
            point = (start + distance) % 360
            if point not in qualified:
                continue
            candidates = [
                distance_to_length[previous]
                for previous in (distance - 1, distance - 2)
                if previous in distance_to_length
            ]
            if candidates:
                distance_to_length[distance] = max(candidates) + 1
                best = max(best, distance_to_length[distance])
    return best


def select_annual_member(handle: zipfile.ZipFile, year: int) -> str:
    expected_suffix = f"/_U2_{year}0101_S.csv"
    candidates = [name for name in handle.namelist() if name.endswith(expected_suffix)]
    if len(candidates) != 1:
        raise RuntimeError(f"year {year}: expected one member ending {expected_suffix}, found {candidates}")
    return candidates[0]


def load_year(archive_path: Path, year: int) -> tuple[list[int], dict[str, Any]]:
    archive_payload = archive_path.read_bytes()
    archive_sha = sha256_bytes(archive_payload)
    with zipfile.ZipFile(io.BytesIO(archive_payload)) as handle:
        member = select_annual_member(handle, year)
        member_payload = handle.read(member)
    member_sha = sha256_bytes(member_payload)

    reader = csv.reader(io.StringIO(member_payload.decode("utf-8-sig"), newline=""))
    header = [field.strip() for field in next(reader)]
    index = {field: position for position, field in enumerate(header)}
    required = ("sol(deg)", "vg(km/s)", "vg sd(km/s)", "Qc(deg)")
    missing = [field for field in required if field not in index]
    if missing:
        raise RuntimeError(f"year {year}: missing fields {missing}")

    counts = [0] * 360
    audit: dict[str, Any] = {
        "year": year,
        "archive_file": archive_path.name,
        "archive_bytes": len(archive_payload),
        "archive_sha256": archive_sha,
        "member": member,
        "member_bytes": len(member_payload),
        "member_sha256": member_sha,
        "header_fields": len(header),
        "header_sha256": sha256_bytes("\n".join(header).encode()),
        "fields_read": list(required),
        "shower_label_field_read": False,
        "raw_rows": 0,
        "malformed_rows": 0,
        "nonfinite_rows": 0,
        "failed_convergence": 0,
        "failed_speed": 0,
        "failed_speed_uncertainty": 0,
        "blind_rows_removed": 0,
        "retained_rows": 0,
    }
    for row in reader:
        if not row or (len(row) == 1 and not row[0].strip()):
            continue
        audit["raw_rows"] += 1
        if len(row) != len(header):
            audit["malformed_rows"] += 1
            continue
        try:
            sol = finite_float(row[index["sol(deg)"]]) % 360.0
            vg = finite_float(row[index["vg(km/s)"]])
            vg_sd = finite_float(row[index["vg sd(km/s)"]])
            convergence = finite_float(row[index["Qc(deg)"]])
        except (ValueError, IndexError):
            audit["nonfinite_rows"] += 1
            continue
        if not convergence > 15.0:
            audit["failed_convergence"] += 1
            continue
        if not 0.0 < vg <= 75.0:
            audit["failed_speed"] += 1
            continue
        if not 0.0 <= vg_sd <= 0.10 * vg + 1.0:
            audit["failed_speed_uncertainty"] += 1
            continue
        if in_blind_interval(sol):
            audit["blind_rows_removed"] += 1
            continue
        counts[int(math.floor(sol)) % 360] += 1
        audit["retained_rows"] += 1

    if sum(counts) != audit["retained_rows"]:
        raise RuntimeError(f"year {year}: retained count mismatch")
    return counts, audit


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    protocol_payload = args.protocol.read_bytes()
    protocol = json.loads(protocol_payload)
    if protocol["status"] != "design_frozen_before_multiyear_archive_access":
        raise RuntimeError("multiyear protocol not frozen")
    if protocol["classification"] != "multiyear input and exposure feasibility audit; not a wavelet comparator result":
        raise RuntimeError("unexpected protocol classification")
    if tuple(protocol["virtual_year"]["years"]) != YEARS:
        raise RuntimeError("year set differs from frozen protocol")

    annual_counts: dict[int, list[int]] = {}
    annual_audits: list[dict[str, Any]] = []
    for year in YEARS:
        archive_path = args.archive_dir / f"{year % 100:03d}a.zip"
        if not archive_path.is_file():
            raise RuntimeError(f"missing annual archive {archive_path}")
        counts, audit = load_year(archive_path, year)
        annual_counts[year] = counts
        annual_audits.append(audit)

    available_bins = [index for index in range(360) if not blind_bin(index)]
    stacked_counts = {
        index: sum(annual_counts[year][index] for year in YEARS)
        for index in available_bins
    }
    contributing_years = {
        index: sum(annual_counts[year][index] > 0 for year in YEARS)
        for index in available_bins
    }
    maximum_year_share: dict[int, float] = {}
    dominant_year: dict[int, int | None] = {}
    for index in available_bins:
        total = stacked_counts[index]
        if total <= 0:
            maximum_year_share[index] = 0.0
            dominant_year[index] = None
            continue
        values = {year: annual_counts[year][index] for year in YEARS}
        year = max(values, key=lambda item: (values[item], -item))
        maximum_year_share[index] = values[year] / total
        dominant_year[index] = year

    supported = {index for index in available_bins if stacked_counts[index] >= PUBLISHED_MINIMUM_RADIANTS}
    multiyear_supported = {
        index for index in available_bins
        if contributing_years[index] >= MINIMUM_CONTRIBUTING_YEARS
    }
    dominated_supported = {
        index for index in supported
        if maximum_year_share[index] > DOMINANCE_SHARE
    }
    chains = linked_triplets(supported)
    longest_chain = longest_forward_chain(supported)

    total_support_fraction = len(supported) / len(available_bins)
    multiyear_support_fraction = len(multiyear_supported) / len(available_bins)
    dominated_fraction = len(dominated_supported) / len(supported) if supported else 1.0
    authorization_gates = {
        "broad_total_support": total_support_fraction >= BREADTH_FRACTION,
        "broad_multiyear_support": multiyear_support_fraction >= BREADTH_FRACTION,
        "limited_single_year_dominance": dominated_fraction <= MAXIMUM_DOMINATED_FRACTION,
        "temporal_coverage": len(chains) >= MINIMUM_THREE_POINT_CHAINS,
    }
    authorized = all(authorization_gates.values())
    decision = (
        "AUTHORIZE_SEPARATE_CMOR_WAVELET_COEFFICIENT_PROTOCOL_DEVELOPMENT"
        if authorized
        else "DEFER_FULL_CMOR_WAVELET_COMPARATOR_UNTIL_A_BETTER_EXPOSURE_CONTROLLED_MULTYEAR_SURVEY_INPUT_EXISTS"
    )

    integrity_gates = {
        "exact_seven_year_set": tuple(audit["year"] for audit in annual_audits) == YEARS,
        "one_member_per_archive": len({audit["member"] for audit in annual_audits}) == len(YEARS),
        "only_required_fields_read": all(audit["fields_read"] == ["sol(deg)", "vg(km/s)", "vg sd(km/s)", "Qc(deg)"] for audit in annual_audits),
        "shower_labels_not_read": all(audit["shower_label_field_read"] is False for audit in annual_audits),
        "blind_interval_removed_each_year": all(audit["blind_rows_removed"] > 0 for audit in annual_audits),
        "all_retained_counts_accounted": all(sum(annual_counts[audit["year"]]) == audit["retained_rows"] for audit in annual_audits),
        "no_wavelet_endpoint_computed": True,
    }
    verdict = "PASS_CMOR_WAVELET_MULTIYEAR_INPUT_AUDIT" if all(integrity_gates.values()) else "FAIL_CMOR_WAVELET_MULTIYEAR_INPUT_AUDIT"

    stack_values = [stacked_counts[index] for index in available_bins]
    contributor_values = [contributing_years[index] for index in available_bins]
    supported_shares = [maximum_year_share[index] for index in sorted(supported)]
    result = {
        "verdict": verdict,
        "decision": decision,
        "classification": protocol["classification"],
        "protocol_sha256": sha256_bytes(protocol_payload),
        "configuration": {
            "years": list(YEARS),
            "blind_interval_deg": list(BLIND_INTERVAL_DEG),
            "available_bins": len(available_bins),
            "published_minimum_radiants": PUBLISHED_MINIMUM_RADIANTS,
            "published_maximum_time_gap_deg": PUBLISHED_MAX_TIME_GAP_DEG,
            "published_minimum_linked_points": PUBLISHED_MINIMUM_LINKED_POINTS,
            "breadth_fraction_gate": BREADTH_FRACTION,
            "minimum_contributing_years": MINIMUM_CONTRIBUTING_YEARS,
            "dominance_share": DOMINANCE_SHARE,
            "maximum_dominated_fraction": MAXIMUM_DOMINATED_FRACTION,
            "minimum_three_point_chains": MINIMUM_THREE_POINT_CHAINS,
        },
        "annual_audits": annual_audits,
        "stack_summary": {
            "total_retained_events": sum(audit["retained_rows"] for audit in annual_audits),
            "annual_retained_events": {str(audit["year"]): audit["retained_rows"] for audit in annual_audits},
            "median_bin_count": float(statistics.median(stack_values)),
            "p10_bin_count": percentile(stack_values, 0.10),
            "p25_bin_count": percentile(stack_values, 0.25),
            "p75_bin_count": percentile(stack_values, 0.75),
            "p90_bin_count": percentile(stack_values, 0.90),
            "minimum_bin_count": min(stack_values),
            "maximum_bin_count": max(stack_values),
            "bins_at_or_above_300": len(supported),
            "fraction_bins_at_or_above_300": total_support_fraction,
            "bins_with_at_least_five_contributing_years": len(multiyear_supported),
            "fraction_bins_with_at_least_five_contributing_years": multiyear_support_fraction,
            "median_contributing_years": float(statistics.median(contributor_values)),
            "supported_bins_dominated_above_50_percent": len(dominated_supported),
            "fraction_supported_bins_dominated_above_50_percent": dominated_fraction,
            "median_maximum_year_share_supported_bins": float(statistics.median(supported_shares)) if supported_shares else None,
            "p90_maximum_year_share_supported_bins": percentile(supported_shares, 0.90) if supported_shares else None,
            "published_gap_three_point_chains": len(chains),
            "longest_published_gap_chain_points": longest_chain,
            "unsupported_bin_indices": sorted(set(available_bins).difference(supported)),
            "dominated_supported_bin_indices": sorted(dominated_supported),
        },
        "per_bin_records": [
            {
                "bin": index,
                "stacked_count": stacked_counts[index],
                "contributing_years": contributing_years[index],
                "maximum_year_share": maximum_year_share[index],
                "dominant_year": dominant_year[index],
                "annual_counts": {str(year): annual_counts[year][index] for year in YEARS},
            }
            for index in available_bins
        ],
        "authorization_gates": authorization_gates,
        "integrity_gates": integrity_gates,
        "interpretation": {
            "pass_meaning": "A pass authorizes writing a separate coefficient-level protocol; it is not a wavelet detection result.",
            "failure_meaning": "A failure means this optical virtual-year input is not broad or exposure-stable enough for a fair global transfer. It is not evidence against the radar method and not evidence for fixed4 superiority.",
            "post_result_relaxation": "prohibited",
        },
    }
    (args.output / "cmor_wavelet_multiyear_input_audit.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = [
        "# CMOR-style seven-year input audit",
        "",
        f"Verdict: **`{verdict}`**",
        f"Decision: **`{decision}`**",
        "",
        "This is an archive, support, and exposure audit—not a wavelet comparator result.",
        "",
        f"- years: **{YEARS[0]}–{YEARS[-1]}**",
        f"- total retained events: **{result['stack_summary']['total_retained_events']:,}**",
        f"- median / p10 / p90 stacked bin count: **{statistics.median(stack_values):.1f} / {percentile(stack_values, 0.10):.1f} / {percentile(stack_values, 0.90):.1f}**",
        f"- bins reaching 300 total events: **{len(supported)}/{len(available_bins)} ({total_support_fraction:.3f})**",
        f"- bins with at least five contributing years: **{len(multiyear_supported)}/{len(available_bins)} ({multiyear_support_fraction:.3f})**",
        f"- supported bins dominated >50% by one year: **{len(dominated_supported)}/{len(supported)} ({dominated_fraction:.3f})**",
        f"- eligible three-point chains: **{len(chains)}**",
        f"- longest eligible chain: **{longest_chain} points**",
        "",
        "## Authorization gates",
        "",
    ]
    for name, passed in authorization_gates.items():
        lines.append(f"- `{name}`: **{'PASS' if passed else 'FAIL'}**")
    (args.output / "CMOR_WAVELET_MULTIYEAR_INPUT_AUDIT.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    if verdict.startswith("FAIL"):
        raise SystemExit(verdict)


if __name__ == "__main__":
    main()
