#!/usr/bin/env python3
"""Aggregate-only SonotaCo 2025 survey-native prefix audit."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import zipfile
from collections import Counter
from pathlib import Path

ARCHIVE_SHA256 = "f4eb716a4b900658fcc658a633d918eca28946f59da75935f1fd5f6bc539bf52"
MEMBER = "025a/_U2_20250101_S.csv"
MEMBER_SHA256 = "30d8cbdf414b2e9d6e587374fec7a4b6fa94c86e76a35e9b335cd4d0cbc917f7"
AUDIT_SHA256 = "f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778"
EXPECTED_ROWS = 36_826
REQUIRED = {
    "sol(deg)",
    "ra(deg)",
    "de(deg)",
    "vg(km/s)",
    "ra sd(deg)",
    "de sd(deg)",
    "vg sd(km/s)",
    "Ncam",
    "Er(deg)",
    "Shower",
}
ASCII_LETTER = re.compile(r"[A-Z]")
NATIVE_TOKEN = re.compile(r"^([A-Z0-9]{3})_JA$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_float(value: str) -> float | None:
    try:
        result = float(value.strip())
    except (AttributeError, TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def background_token(token: str) -> bool:
    return token == "" or ASCII_LETTER.search(token) is None or token.startswith("SPO")


def native_prefix(token: str) -> str | None:
    match = NATIVE_TOKEN.fullmatch(token)
    return match.group(1) if match else None


def build_mapping(audit: dict) -> dict[str, dict]:
    mapping: dict[str, dict] = {}
    for profile in audit["profiles"]:
        if not profile.get("eligible", False):
            continue
        for code in profile.get("codes", {}):
            normalized = str(code).strip().upper()
            if len(normalized) != 3:
                continue
            if normalized in mapping and mapping[normalized]["iau"] != int(profile["iau"]):
                raise RuntimeError(f"ambiguous frozen code mapping: {normalized}")
            mapping[normalized] = {
                "iau": int(profile["iau"]),
                "complex_key": str(profile["complex_key"]),
            }
    return mapping


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    archive_hash = sha256(args.archive)
    audit_hash = sha256(args.audit)
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    mapping = build_mapping(audit)

    with zipfile.ZipFile(args.archive) as handle:
        payload = handle.read(MEMBER)
    member_hash = hashlib.sha256(payload).hexdigest()
    reader = csv.reader(io.StringIO(payload.decode("utf-8-sig"), newline=""), delimiter=",")
    raw_header = next(reader)
    header = [field.strip() for field in raw_header]
    if len(set(header)) != len(header):
        raise RuntimeError("normalized SonotaCo headers are not unique")
    index = {field: position for position, field in enumerate(header)}

    total_rows = 0
    malformed_rows = 0
    invalid_solar_rows = 0
    blinded_rows = 0
    geometry_ready = 0
    reservoir_ready = 0
    reservoir_background = 0
    reservoir_native_labeled = 0
    reservoir_matched = 0
    reservoir_unmatched = 0
    uncertainty_complete = 0
    nonbackground_label_rows = 0
    native_syntax_label_rows = 0
    label_token_counts: Counter[str] = Counter()
    class_counts: Counter[str] = Counter()
    matched_ready_counts: Counter[str] = Counter()
    complex_ready_counts: Counter[str] = Counter()

    for row in reader:
        if not row or (len(row) == 1 and not row[0].strip()):
            continue
        total_rows += 1
        if len(row) != len(header):
            malformed_rows += 1
            continue

        sol = parse_float(row[index["sol(deg)"]]) if "sol(deg)" in index else None
        if sol is None:
            invalid_solar_rows += 1
            continue
        sol %= 360.0
        if 20.0 <= sol <= 55.0:
            blinded_rows += 1
            continue

        token = row[index["Shower"]].strip().upper() if "Shower" in index else ""
        label_token_counts[token] += 1
        is_background = background_token(token)
        prefix = None if is_background else native_prefix(token)
        if not is_background:
            nonbackground_label_rows += 1
            if prefix is not None:
                native_syntax_label_rows += 1

        if is_background:
            label_class = "background"
        elif prefix is None:
            label_class = "invalid_native_syntax"
        elif prefix in mapping:
            label_class = "matched"
        else:
            label_class = "unmatched_prefix"
        class_counts[label_class] += 1

        ra = parse_float(row[index["ra(deg)"]]) if "ra(deg)" in index else None
        dec = parse_float(row[index["de(deg)"]]) if "de(deg)" in index else None
        vg = parse_float(row[index["vg(km/s)"]]) if "vg(km/s)" in index else None
        geometry = (
            0.0 <= sol < 360.0
            and ra is not None
            and 0.0 <= ra < 360.0
            and dec is not None
            and -90.0 <= dec <= 90.0
            and vg is not None
            and 0.0 < vg < 100.0
        )
        if not geometry:
            continue
        geometry_ready += 1

        ncam = parse_float(row[index["Ncam"]]) if "Ncam" in index else None
        if ncam is None or ncam < 2.0:
            continue
        reservoir_ready += 1

        uncertainty_values = [
            parse_float(row[index[name]]) if name in index else None
            for name in ("ra sd(deg)", "de sd(deg)", "vg sd(km/s)", "Er(deg)")
        ]
        if all(value is not None and value >= 0.0 for value in uncertainty_values):
            uncertainty_complete += 1

        if is_background:
            reservoir_background += 1
        elif prefix is not None:
            reservoir_native_labeled += 1
            if prefix in mapping:
                reservoir_matched += 1
                matched_ready_counts[prefix] += 1
                complex_ready_counts[mapping[prefix]["complex_key"]] += 1
            else:
                reservoir_unmatched += 1
        else:
            reservoir_unmatched += 1

    outside_blind_denominator = total_rows - blinded_rows
    geometry_fraction = (
        geometry_ready / outside_blind_denominator if outside_blind_denominator else 0.0
    )
    uncertainty_fraction = (
        uncertainty_complete / reservoir_ready if reservoir_ready else 0.0
    )
    syntax_fraction = (
        native_syntax_label_rows / nonbackground_label_rows
        if nonbackground_label_rows
        else 0.0
    )
    matched_native_fraction = (
        reservoir_matched / reservoir_native_labeled
        if reservoir_native_labeled
        else 0.0
    )
    supported_codes = {
        code: count for code, count in matched_ready_counts.items() if count >= 20
    }
    supported_complexes = {
        mapping[code]["complex_key"] for code in supported_codes
    }

    gates = {
        "exact_sonotaco_hashes": archive_hash == ARCHIVE_SHA256 and member_hash == MEMBER_SHA256,
        "exact_gmn_mdc_audit_hash": audit_hash == AUDIT_SHA256,
        "required_unique_fields": REQUIRED.issubset(index) and len(set(header)) == len(header),
        "all_published_rows_structurally_parsed": total_rows == EXPECTED_ROWS and malformed_rows == 0,
        "geometry_completeness_at_least_0_95": geometry_fraction >= 0.95,
        "reservoir_background_at_least_10000": reservoir_background >= 10_000,
        "uncertainty_completeness_at_least_0_90": uncertainty_fraction >= 0.90,
        "native_syntax_fraction_at_least_0_99": syntax_fraction >= 0.99,
        "matched_native_fraction_at_least_0_80": matched_native_fraction >= 0.80,
        "supported_matched_codes_at_least_20": len(supported_codes) >= 20,
        "supported_complexes_at_least_10": len(supported_complexes) >= 10,
    }

    result = {
        "input_hashes": {
            "archive_sha256": archive_hash,
            "member_sha256": member_hash,
            "audit_sha256": audit_hash,
        },
        "label_rule": {
            "background": "blank/no ASCII letter/SPO prefix",
            "native_regex": NATIVE_TOKEN.pattern,
            "canonical_code": "captured three-character prefix",
        },
        "counts": {
            "total_rows": total_rows,
            "malformed_rows": malformed_rows,
            "invalid_solar_rows": invalid_solar_rows,
            "blind_interval_rows_removed": blinded_rows,
            "outside_blind_denominator": outside_blind_denominator,
            "geometry_ready": geometry_ready,
            "reservoir_ready": reservoir_ready,
            "reservoir_background": reservoir_background,
            "reservoir_native_labeled": reservoir_native_labeled,
            "reservoir_matched": reservoir_matched,
            "reservoir_unmatched": reservoir_unmatched,
            "nonbackground_label_rows": nonbackground_label_rows,
            "native_syntax_label_rows": native_syntax_label_rows,
            "supported_matched_codes": len(supported_codes),
            "supported_complexes": len(supported_complexes),
        },
        "fractions": {
            "geometry_completeness": geometry_fraction,
            "uncertainty_completeness": uncertainty_fraction,
            "native_syntax_fraction": syntax_fraction,
            "matched_native_fraction": matched_native_fraction,
        },
        "label_class_counts_outside_blind": dict(sorted(class_counts.items())),
        "label_token_counts_outside_blind": dict(sorted(label_token_counts.items())),
        "supported_matched_code_counts": dict(sorted(supported_codes.items())),
        "supported_complex_keys": sorted(supported_complexes),
        "gates": gates,
        "verdict": (
            "PASS_SONOTACO_2025_NATIVE_PREFIX_AUDIT"
            if all(gates.values())
            else "KILL_SONOTACO_2025_NATIVE_PREFIX_AUDIT"
        ),
    }

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "sonotaco_2025_native_prefix_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    lines = [
        "# SonotaCo 2025 survey-native prefix audit",
        "",
        f"Verdict: **`{result['verdict']}`**",
        "",
        f"Rows: **{total_rows:,}**",
        f"Blind-interval rows removed: **{blinded_rows:,}**",
        f"Geometry completeness: **{geometry_fraction:.6f}**",
        f"Reservoir background: **{reservoir_background:,}**",
        f"Native syntax fraction: **{syntax_fraction:.6f}**",
        f"Matched native reservoir fraction: **{matched_native_fraction:.6f}**",
        f"Supported matched codes: **{len(supported_codes)}**",
        f"Supported complex keys: **{len(supported_complexes)}**",
        f"Uncertainty completeness: **{uncertainty_fraction:.6f}**",
        "",
        "## Frozen gates",
        "",
    ]
    lines.extend(
        f"- {'PASS' if value else 'FAIL'} — `{name}`"
        for name, value in gates.items()
    )
    (args.output / "SONOTACO_2025_NATIVE_PREFIX_AUDIT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if not all(gates.values()):
        raise SystemExit("frozen SonotaCo 2025 native-prefix audit failed")


if __name__ == "__main__":
    main()
