#!/usr/bin/env python3
"""Source-grounded feasibility audit for a Brown et al. (2010) CMOR-style wavelet transfer.

This script deliberately computes no wavelet coefficient, local maximum, shower
recovery, or comparison endpoint. It tests only a necessary support condition:
a published local maximum required at least 300 contributing radiants, so a
one-degree time bin with fewer than 300 total retained radiants cannot possibly
support such a maximum anywhere in radiant/velocity space.
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
from typing import Iterable

YEAR = 2025
MEMBER = "025a/_U2_20250101_S.csv"
ARCHIVE_SHA256 = "f4eb716a4b900658fcc658a633d918eca28946f59da75935f1fd5f6bc539bf52"
MEMBER_SHA256 = "30d8cbdf414b2e9d6e587374fec7a4b6fa94c86e76a35e9b335cd4d0cbc917f7"
BLIND_INTERVAL_DEG = (20.0, 55.0)
PUBLISHED_MINIMUM_RADIANTS = 300
PUBLISHED_MAX_TIME_GAP_DEG = 2
PUBLISHED_MINIMUM_LINKED_POINTS = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True, type=Path)
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


def percentile(values: list[int], q: float) -> float:
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
    # A bin is unavailable if any part of its [b,b+1) support lies in the
    # preregistered blind interval. With integer endpoints this removes bins
    # 20 through 55 inclusive, conservatively including the final edge bin.
    low, high = BLIND_INTERVAL_DEG
    return int(math.floor(low)) <= bin_index <= int(math.floor(high))


def linked_triplets(qualified: set[int]) -> set[tuple[int, int, int]]:
    """Enumerate forward three-point chains allowed by the published <=2 deg gap."""
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
                if third not in qualified:
                    continue
                # Canonicalize by the actual forward sequence; no reversal or
                # cyclic permutation is counted as a separate chain.
                chains.add((first, second, third))
    return chains


def longest_forward_chain(qualified: set[int]) -> int:
    """Maximum number of supported points connected by forward gaps <=2 deg."""
    if not qualified:
        return 0
    # Duplicate the circular year and cap traversal at 360 degrees so a cycle
    # cannot be followed indefinitely.
    best = 1
    for start in sorted(qualified):
        frontier = {start: 1}
        for offset in range(1, 360):
            point = (start + offset) % 360
            if point not in qualified:
                continue
            previous = [
                length
                for previous_point, length in frontier.items()
                if 1 <= (point - previous_point) % 360 <= PUBLISHED_MAX_TIME_GAP_DEG
            ]
            if previous:
                frontier[point] = max(previous) + 1
                best = max(best, frontier[point])
    return best


def load_counts(archive: Path) -> tuple[list[int], dict[str, object]]:
    archive_payload = archive.read_bytes()
    archive_hash = sha256_bytes(archive_payload)
    if archive_hash != ARCHIVE_SHA256:
        raise RuntimeError(f"archive hash mismatch: {archive_hash}")
    with zipfile.ZipFile(io.BytesIO(archive_payload)) as handle:
        member_payload = handle.read(MEMBER)
    member_hash = sha256_bytes(member_payload)
    if member_hash != MEMBER_SHA256:
        raise RuntimeError(f"member hash mismatch: {member_hash}")

    reader = csv.reader(io.StringIO(member_payload.decode("utf-8-sig"), newline=""))
    header = [field.strip() for field in next(reader)]
    index = {field: position for position, field in enumerate(header)}
    required = ("sol(deg)", "vg(km/s)", "vg sd(km/s)", "Qc(deg)")
    if any(field not in index for field in required):
        raise RuntimeError(f"missing required fields: {[field for field in required if field not in index]}")

    counts = [0] * 360
    raw_rows = 0
    malformed_rows = 0
    nonfinite_rows = 0
    failed_convergence = 0
    failed_speed = 0
    failed_speed_uncertainty = 0
    blind_rows_removed = 0
    retained_rows = 0

    for row in reader:
        if not row or (len(row) == 1 and not row[0].strip()):
            continue
        raw_rows += 1
        if len(row) != len(header):
            malformed_rows += 1
            continue
        try:
            sol = finite_float(row[index["sol(deg)"]]) % 360.0
            vg = finite_float(row[index["vg(km/s)"]])
            vg_sd = finite_float(row[index["vg sd(km/s)"]])
            convergence = finite_float(row[index["Qc(deg)"]])
        except (ValueError, IndexError):
            nonfinite_rows += 1
            continue
        if not convergence > 15.0:
            failed_convergence += 1
            continue
        if not (0.0 < vg <= 75.0):
            failed_speed += 1
            continue
        if not (0.0 <= vg_sd <= 0.10 * vg + 1.0):
            failed_speed_uncertainty += 1
            continue
        if in_blind_interval(sol):
            blind_rows_removed += 1
            continue
        counts[int(math.floor(sol)) % 360] += 1
        retained_rows += 1

    return counts, {
        "archive_sha256": archive_hash,
        "member": MEMBER,
        "member_sha256": member_hash,
        "header_fields": len(header),
        "fields_read": list(required),
        "shower_label_field_read": False,
        "raw_rows": raw_rows,
        "malformed_rows": malformed_rows,
        "nonfinite_rows": nonfinite_rows,
        "failed_convergence": failed_convergence,
        "failed_speed": failed_speed,
        "failed_speed_uncertainty": failed_speed_uncertainty,
        "blind_rows_removed": blind_rows_removed,
        "retained_rows": retained_rows,
    }


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    protocol_payload = args.protocol.read_bytes()
    protocol = json.loads(protocol_payload)
    published = protocol["published_design"]
    if protocol["status"] != "frozen_before_any_wavelet_coefficient_or detection endpoint":
        raise RuntimeError("wavelet feasibility protocol is not frozen")
    if protocol["classification"] != "source-grounded feasibility audit; not a scientific comparator result":
        raise RuntimeError("unexpected protocol classification")
    if published["minimum_radiants_contributing_to_coefficient"] != PUBLISHED_MINIMUM_RADIANTS:
        raise RuntimeError("published support floor mismatch")
    if published["temporal_linking"]["maximum_solar_longitude_separation_deg"] != PUBLISHED_MAX_TIME_GAP_DEG:
        raise RuntimeError("published temporal-gap mismatch")
    if published["temporal_linking"]["minimum_linked_points"] != PUBLISHED_MINIMUM_LINKED_POINTS:
        raise RuntimeError("published chain-length mismatch")

    counts, parser_audit = load_counts(args.archive)
    available_bins = [index for index in range(360) if not blind_bin(index)]
    available_counts = [counts[index] for index in available_bins]
    qualified = {
        index
        for index in available_bins
        if counts[index] >= PUBLISHED_MINIMUM_RADIANTS
    }
    strict_consecutive = {
        (start, (start + 1) % 360, (start + 2) % 360)
        for start in available_bins
        if all(
            ((start + offset) % 360) in qualified
            for offset in range(3)
        )
    }
    allowed_linked = linked_triplets(qualified)
    longest_chain = longest_forward_chain(qualified)

    necessary_support_pass = bool(allowed_linked)
    decision = (
        "PASSES_NECESSARY_SINGLE_YEAR_SUPPORT_GATE_ONLY"
        if necessary_support_pass
        else "DEFER_FULL_CMOR_WAVELET_COMPARATOR_UNTIL_A_PREREGISTERED_MULTIYEAR_STACK_AND_EXPOSURE_MODEL_EXIST"
    )
    gates = {
        "exact_archive": parser_audit["archive_sha256"] == ARCHIVE_SHA256,
        "exact_member": parser_audit["member_sha256"] == MEMBER_SHA256,
        "only_required_geometry_fields_read": parser_audit["fields_read"] == ["sol(deg)", "vg(km/s)", "vg sd(km/s)", "Qc(deg)"],
        "shower_labels_not_read": parser_audit["shower_label_field_read"] is False,
        "blind_interval_removed": parser_audit["blind_rows_removed"] > 0,
        "no_wavelet_endpoint_computed": True,
        "all_counts_accounted": sum(counts) == parser_audit["retained_rows"],
    }
    verdict = "PASS_CMOR_WAVELET_FEASIBILITY_AUDIT" if all(gates.values()) else "FAIL_CMOR_WAVELET_FEASIBILITY_AUDIT"

    result = {
        "verdict": verdict,
        "decision": decision,
        "classification": protocol["classification"],
        "protocol_sha256": sha256_bytes(protocol_payload),
        "configuration": {
            "year": YEAR,
            "blind_interval_deg": list(BLIND_INTERVAL_DEG),
            "available_one_degree_bins": len(available_bins),
            "published_minimum_radiants": PUBLISHED_MINIMUM_RADIANTS,
            "published_maximum_time_gap_deg": PUBLISHED_MAX_TIME_GAP_DEG,
            "published_minimum_linked_points": PUBLISHED_MINIMUM_LINKED_POINTS,
        },
        "parser_audit": parser_audit,
        "support_summary": {
            "median_bin_count": float(statistics.median(available_counts)),
            "p90_bin_count": percentile(available_counts, 0.90),
            "p95_bin_count": percentile(available_counts, 0.95),
            "p99_bin_count": percentile(available_counts, 0.99),
            "maximum_bin_count": max(available_counts),
            "bins_at_or_above_300": len(qualified),
            "fraction_available_bins_at_or_above_300": len(qualified) / len(available_bins),
            "strict_consecutive_three_bin_chains": len(strict_consecutive),
            "published_gap_eligible_three_point_chains": len(allowed_linked),
            "longest_published_gap_eligible_chain_points": longest_chain,
            "qualified_bin_indices": sorted(qualified),
        },
        "interpretation": {
            "necessary_not_sufficient": "Even 300 total events in a time bin is only a necessary condition because the published floor applies to radiants contributing near one wavelet test point.",
            "negative_meaning": "Failure means one SonotaCo year cannot execute the published support and linking rules faithfully. It is not evidence of poor CMOR-wavelet performance and not evidence for OrbitTrace superiority.",
            "prohibited_relaxations": protocol["decision_rule"]["no_relaxation"],
        },
        "gates": gates,
    }
    (args.output / "cmor_wavelet_feasibility_audit.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = [
        "# CMOR-style wavelet feasibility audit",
        "",
        f"Verdict: **`{verdict}`**",
        f"Decision: **`{decision}`**",
        "",
        "This is a support audit, not a wavelet comparator result.",
        "",
        f"- quality-retained, blind-interval-excluded events: **{parser_audit['retained_rows']:,}**",
        f"- available one-degree bins: **{len(available_bins)}**",
        f"- median / p95 / maximum bin count: **{statistics.median(available_counts):.1f} / {percentile(available_counts, 0.95):.1f} / {max(available_counts)}**",
        f"- bins reaching the published 300-radiant necessary floor: **{len(qualified)}**",
        f"- three-point chains allowed by the published <=2-degree gap: **{len(allowed_linked)}**",
        f"- longest supported chain: **{longest_chain} points**",
        "",
        "A negative result does not score or criticize the wavelet method; it prevents an unfair reduced-data reproduction.",
    ]
    (args.output / "CMOR_WAVELET_FEASIBILITY_AUDIT.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    if verdict.startswith("FAIL"):
        raise SystemExit(verdict)


if __name__ == "__main__":
    main()
