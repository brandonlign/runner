#!/usr/bin/env python3
"""Build the frozen SonotaCo 2025 event corpus for Mondrian development."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

ARCHIVE_SHA256 = "f4eb716a4b900658fcc658a633d918eca28946f59da75935f1fd5f6bc539bf52"
MEMBER = "025a/_U2_20250101_S.csv"
MEMBER_SHA256 = "30d8cbdf414b2e9d6e587374fec7a4b6fa94c86e76a35e9b335cd4d0cbc917f7"
AUDIT_SHA256 = "f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778"
EXPECTED_ROWS = 36_826
EXPECTED_BACKGROUND = 24_052
EXPECTED_MATCHED = 10_756
BLIND_LOW = 20.0
BLIND_HIGH = 55.0
ASCII_LETTER = re.compile(r"[A-Z]")
NATIVE_TOKEN = re.compile(r"^([A-Z0-9]{3})_JA$")
REQUIRED = {
    "sol(deg)", "ra(deg)", "de(deg)", "vg(km/s)",
    "ra sd(deg)", "de sd(deg)", "vg sd(km/s)",
    "Ncam", "Er(deg)", "Shower",
}


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_float(value: str) -> float | None:
    try:
        result = float(value.strip())
    except (AttributeError, TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def background_token(token: str) -> bool:
    return token == "" or ASCII_LETTER.search(token) is None or token.startswith("SPO")


def build_mapping(audit: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for profile in audit["profiles"]:
        if not profile.get("eligible", False):
            continue
        for code in profile.get("codes", {}):
            normalized = str(code).strip().upper()
            if len(normalized) != 3:
                continue
            record = {"iau": int(profile["iau"]), "complex_key": str(profile["complex_key"])}
            if normalized in mapping and mapping[normalized] != record:
                raise RuntimeError(f"ambiguous frozen code mapping: {normalized}")
            mapping[normalized] = record
    return mapping


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    if sha256_path(args.archive) != ARCHIVE_SHA256:
        raise RuntimeError("SonotaCo archive hash mismatch")
    if sha256_path(args.audit) != AUDIT_SHA256:
        raise RuntimeError("GMN/MDC audit hash mismatch")
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    mapping = build_mapping(audit)

    with zipfile.ZipFile(args.archive) as archive:
        payload = archive.read(MEMBER)
    if hashlib.sha256(payload).hexdigest() != MEMBER_SHA256:
        raise RuntimeError("SonotaCo member hash mismatch")

    reader = csv.reader(io.StringIO(payload.decode("utf-8-sig"), newline=""), delimiter=",")
    header = [field.strip() for field in next(reader)]
    if len(set(header)) != len(header) or not REQUIRED.issubset(header):
        raise RuntimeError("unexpected SonotaCo header")
    index = {field: position for position, field in enumerate(header)}

    selected: list[dict[str, Any]] = []
    class_counts: Counter[str] = Counter()
    code_counts: Counter[str] = Counter()
    total_rows = malformed_rows = blinded_rows = 0
    for row_number, row in enumerate(reader, start=1):
        if not row or (len(row) == 1 and not row[0].strip()):
            continue
        total_rows += 1
        if len(row) != len(header):
            malformed_rows += 1
            continue
        sol = parse_float(row[index["sol(deg)"]])
        ra = parse_float(row[index["ra(deg)"]])
        dec = parse_float(row[index["de(deg)"]])
        vg = parse_float(row[index["vg(km/s)"]])
        ncam = parse_float(row[index["Ncam"]])
        ra_sigma = parse_float(row[index["ra sd(deg)"]])
        dec_sigma = parse_float(row[index["de sd(deg)"]])
        vg_sigma = parse_float(row[index["vg sd(km/s)"]])
        fiterr = parse_float(row[index["Er(deg)"]])
        if sol is None:
            class_counts["invalid_solar"] += 1
            continue
        sol %= 360.0
        if BLIND_LOW <= sol <= BLIND_HIGH:
            blinded_rows += 1
            continue
        geometry_ready = (
            ra is not None and 0.0 <= ra < 360.0
            and dec is not None and -90.0 <= dec <= 90.0
            and vg is not None and 0.0 < vg < 100.0
            and ncam is not None and ncam >= 2.0
            and ra_sigma is not None and ra_sigma >= 0.0
            and dec_sigma is not None and dec_sigma >= 0.0
            and vg_sigma is not None and vg_sigma >= 0.0
            and fiterr is not None and fiterr >= 0.0
        )
        if not geometry_ready:
            class_counts["not_reservoir_ready"] += 1
            continue

        token = row[index["Shower"]].strip().upper()
        if background_token(token):
            label = {"iau": -1, "code": "SPO", "complex_key": "SPORADIC"}
            class_counts["background"] += 1
        else:
            match = NATIVE_TOKEN.fullmatch(token)
            if match is None:
                class_counts["excluded_invalid_native_syntax"] += 1
                continue
            code = match.group(1)
            if code not in mapping:
                class_counts["excluded_unmatched_prefix"] += 1
                continue
            label = {"iau": mapping[code]["iau"], "code": code, "complex_key": mapping[code]["complex_key"]}
            class_counts["matched"] += 1
            code_counts[code] += 1

        selected.append({
            "id": f"SONOTACO2025:{row_number:06d}",
            "year": 2025,
            "month": 0,
            "sol": sol,
            "ra": ra,
            "dec": dec,
            "vg": vg,
            "ra_sigma": ra_sigma,
            "dec_sigma": dec_sigma,
            "vg_sigma": vg_sigma,
            "num_stat": int(ncam),
            "fiterr": fiterr,
            **label,
        })

    selected.sort(key=lambda event: (int(event["iau"]) == -1, str(event["code"]), float(event["sol"]), str(event["id"])))
    background_count = sum(int(event["iau"]) == -1 for event in selected)
    matched_count = len(selected) - background_count
    supported_codes = {code: count for code, count in code_counts.items() if count >= 20}
    supported_complexes = {mapping[code]["complex_key"] for code in supported_codes}

    gates = {
        "all_published_rows_parsed": total_rows == EXPECTED_ROWS and malformed_rows == 0,
        "exact_background_count": background_count == EXPECTED_BACKGROUND,
        "exact_matched_count": matched_count == EXPECTED_MATCHED,
        "supported_codes_at_least_30": len(supported_codes) >= 30,
        "supported_complexes_at_least_25": len(supported_complexes) >= 25,
        "all_selected_events_complete": all(
            event["ra"] is not None and event["dec"] is not None and event["vg"] is not None
            for event in selected
        ),
    }
    verdict = "PASS_SONOTACO_2025_EVENT_ADAPTER" if all(gates.values()) else "KILL_SONOTACO_2025_EVENT_ADAPTER"

    args.output.mkdir(parents=True, exist_ok=True)
    events_path = args.output / "selected_events.jsonl.gz"
    with events_path.open("wb") as raw_handle:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0) as compressed:
            for event in selected:
                line = json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n"
                compressed.write(line.encode("utf-8"))
    result = {
        "verdict": verdict,
        "configuration": {
            "year": 2025,
            "blind_interval_deg": [BLIND_LOW, BLIND_HIGH],
            "label_regex": NATIVE_TOKEN.pattern,
            "unmatched_labeled_rows": "excluded, never reassigned to background",
        },
        "input_hashes": {
            "archive_sha256": sha256_path(args.archive),
            "member_sha256": hashlib.sha256(payload).hexdigest(),
            "audit_sha256": sha256_path(args.audit),
        },
        "counts": {
            "total_rows": total_rows,
            "malformed_rows": malformed_rows,
            "blind_interval_rows_removed": blinded_rows,
            "selected_events": len(selected),
            "background_events": background_count,
            "matched_labeled_events": matched_count,
            "supported_codes": len(supported_codes),
            "supported_complexes": len(supported_complexes),
        },
        "class_counts": dict(sorted(class_counts.items())),
        "supported_code_counts": dict(sorted(supported_codes.items())),
        "gates": gates,
        "events_sha256": sha256_path(events_path),
    }
    (args.output / "adapter_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not all(gates.values()):
        raise SystemExit("frozen SonotaCo event adapter gate failed")


if __name__ == "__main__":
    main()
