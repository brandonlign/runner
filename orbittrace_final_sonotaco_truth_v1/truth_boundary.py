#!/usr/bin/env python3
"""Post-output truth reader for the one-shot SonotaCo 2013/2014 final test.

This module performs no network access and cannot run a detector. It may read the SonotaCo
`shower` field only after a caller supplies a fail-closed pretruth freeze manifest proving that
the exact pairwise row universe and both primary catalogue outputs were already frozen/hashes
recorded. It then maps only those already-frozen event IDs to the pre-existing eligible MDC
complex reference used by earlier SonotaCo work.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable

from orbittrace_final_sonotaco_normalizer_v1 import normalizer

MAPPING_AUDIT_RUN_ID = 30855193522
MAPPING_AUDIT_ARTIFACT = "real-shower-meta-data-audit"
MAPPING_AUDIT_SHA256 = "f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778"
NATIVE_TOKEN = re.compile(r"^([A-Z0-9]{3})_JA$")
ASCII_LETTER = re.compile(r"[A-Z]")
COMPARATORS = {"Sugar", "catalogue HDBSCAN"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def background_token(token: str) -> bool:
    """Exact historical SonotaCo native-background syntax."""
    return token == "" or ASCII_LETTER.search(token) is None or token.startswith("SPO")


def build_mapping(audit: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Exact eligible-code -> MDC complex mapping semantics inherited from frozen SonotaCo source."""
    mapping: dict[str, dict[str, Any]] = {}
    profiles = audit.get("profiles")
    require(isinstance(profiles, list), "mapping audit missing profiles")
    for profile in profiles:
        if not isinstance(profile, dict) or not profile.get("eligible", False):
            continue
        iau = int(profile["iau"])
        complex_key = str(profile["complex_key"])
        codes = profile.get("codes", {})
        require(isinstance(codes, (dict, list)), "mapping profile codes must be dict/list")
        iterable = codes.keys() if isinstance(codes, dict) else codes
        for code in iterable:
            normalized = str(code).strip().upper()
            if len(normalized) != 3:
                continue
            record = {"iau": iau, "complex_key": complex_key}
            if normalized in mapping:
                require(mapping[normalized] == record, f"ambiguous frozen code mapping: {normalized}")
            mapping[normalized] = record
    require(mapping, "eligible mapping is empty")
    return mapping


def validate_pretruth_freeze(freeze: dict[str, Any], *, year: int, comparator: str) -> None:
    require(year in {2013, 2014}, "truth boundary restricted to final SonotaCo years")
    require(comparator in COMPARATORS, "unexpected final comparator")
    require(freeze.get("year") == year, "freeze manifest year mismatch")
    require(freeze.get("comparator") == comparator, "freeze manifest comparator mismatch")
    require(freeze.get("pretruth_outputs_frozen") is True, "catalogue outputs are not frozen")
    require(freeze.get("truth_accessed_before_freeze") is False, "truth was accessed before output freeze")
    require(freeze.get("target_information_access") is False, "target information access detected")
    require(freeze.get("target_region_access") is False, "target-region access detected")
    for key in (
        "pairwise_event_ids_sha256",
        "orbittrace_primary_output_sha256",
        "comparator_primary_output_sha256",
        "orbittrace_source_manifest_sha256",
        "comparator_source_manifest_sha256",
    ):
        value = freeze.get(key)
        require(isinstance(value, str) and HEX64.fullmatch(value) is not None, f"invalid/missing frozen hash: {key}")


def canonical_ids_sha256(ids: Iterable[str]) -> str:
    ordered = sorted(str(x) for x in ids)
    require(len(ordered) == len(set(ordered)), "duplicate pairwise event ID")
    return hashlib.sha256(("\n".join(ordered) + "\n").encode()).hexdigest()


def parse_truth_after_freeze(
    payload: bytes,
    *,
    year: int,
    comparator: str,
    requested_event_ids: list[str],
    mapping_audit: dict[str, Any],
    mapping_audit_sha256: str,
    pretruth_freeze: dict[str, Any],
    id_prefix: str | None = None,
) -> tuple[dict[str, str], dict[str, Any]]:
    """Read truth for an already-frozen pairwise row universe only.

    Returned values are either an eligible MDC complex key or `SPORADIC`. Invalid/unmapped native
    shower tokens are never reassigned to another known shower; relative to the frozen eligible
    reference they remain reference-background (`SPORADIC`) and are separately audited.
    """
    validate_pretruth_freeze(pretruth_freeze, year=year, comparator=comparator)
    require(mapping_audit_sha256 == MAPPING_AUDIT_SHA256, "mapping audit SHA mismatch")
    mapping = build_mapping(mapping_audit)
    prefix = id_prefix if id_prefix is not None else f"SNT{year}"

    requested = [str(x) for x in requested_event_ids]
    require(requested, "empty pairwise truth request")
    require(len(requested) == len(set(requested)), "duplicate pairwise truth request ID")
    require(canonical_ids_sha256(requested) == pretruth_freeze["pairwise_event_ids_sha256"],
            "pairwise event-ID freeze hash mismatch")

    row_to_id: dict[int, str] = {}
    for event_id in requested:
        expected_prefix = prefix + ":"
        require(event_id.startswith(expected_prefix), f"wrong truth event-ID prefix: {event_id}")
        try:
            physical_row = int(event_id[len(expected_prefix):])
        except ValueError as exc:
            raise RuntimeError(f"invalid physical-row event ID: {event_id}") from exc
        require(physical_row >= 2 and physical_row not in row_to_id,
                f"invalid/duplicate physical-row event ID: {event_id}")
        row_to_id[physical_row] = event_id

    text = payload.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=",")
    try:
        raw_header = next(reader)
    except StopIteration as exc:
        raise RuntimeError("empty SonotaCo final-year CSV") from exc
    header = normalizer.reconcile_header(raw_header)
    index = {field: i for i, field in enumerate(header)}
    require("soldeg" in index and "shower" in index, "truth-required SonotaCo headers missing")

    truth: dict[str, str] = {}
    status_counts: dict[str, int] = {}
    native_code_counts: dict[str, int] = {}
    found: set[str] = set()

    def bump(d: dict[str, int], key: str) -> None:
        d[key] = d.get(key, 0) + 1

    for physical_row, row in enumerate(reader, start=2):
        event_id = row_to_id.get(physical_row)
        if event_id is None:
            continue
        require(len(row) == len(header), f"malformed requested truth row: {event_id}")
        sol = normalizer.parse_float(row[index["soldeg"]])
        require(sol is not None, f"invalid solar longitude in requested truth row: {event_id}")
        sol %= 360.0
        require(not (normalizer.BLIND_LOW <= sol <= normalizer.BLIND_HIGH),
                f"requested truth row enters excluded target interval: {event_id}")
        token = row[index["shower"]].strip().upper()
        found.add(event_id)

        if background_token(token):
            truth[event_id] = "SPORADIC"
            bump(status_counts, "native_background")
            continue

        match = NATIVE_TOKEN.fullmatch(token)
        if match is None:
            truth[event_id] = "SPORADIC"
            bump(status_counts, "invalid_native_syntax_reference_background")
            continue
        code = match.group(1)
        bump(native_code_counts, code)
        record = mapping.get(code)
        if record is None:
            truth[event_id] = "SPORADIC"
            bump(status_counts, "unmapped_native_code_reference_background")
            continue
        truth[event_id] = str(record["complex_key"])
        bump(status_counts, "mapped_known_shower")

    missing = sorted(set(requested) - found)
    require(not missing, f"requested truth rows missing from annual CSV: {missing[:10]} (n={len(missing)})")
    require(set(truth) == set(requested), "truth output event-ID universe differs from frozen request")

    audit = {
        "verdict": "PASS_FINAL_SONOTACO_POSTOUTPUT_TRUTH_PARSE",
        "year": year,
        "comparator": comparator,
        "requested_event_count": len(requested),
        "truth_event_count": len(truth),
        "pairwise_event_ids_sha256": canonical_ids_sha256(requested),
        "mapping_audit_run_id": MAPPING_AUDIT_RUN_ID,
        "mapping_audit_artifact": MAPPING_AUDIT_ARTIFACT,
        "mapping_audit_sha256": MAPPING_AUDIT_SHA256,
        "native_token_regex": NATIVE_TOKEN.pattern,
        "status_counts": dict(sorted(status_counts.items())),
        "native_code_counts": dict(sorted(native_code_counts.items())),
        "known_truth_labels": len({x for x in truth.values() if x != "SPORADIC"}),
        "pretruth_outputs_frozen": True,
        "truth_accessed_before_freeze": False,
        "target_information_access": False,
        "target_region_access": False,
        "detector_rerun_or_mutation_after_truth": False,
    }
    return truth, audit


def main() -> int:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--annual-csv", type=Path, required=True)
    p.add_argument("--year", type=int, required=True, choices=[2013, 2014])
    p.add_argument("--comparator", required=True, choices=sorted(COMPARATORS))
    p.add_argument("--event-ids", type=Path, required=True)
    p.add_argument("--mapping-audit", type=Path, required=True)
    p.add_argument("--pretruth-freeze", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    require(sha256_path(a.mapping_audit) == MAPPING_AUDIT_SHA256, "mapping audit file identity changed")
    event_ids = json.loads(a.event_ids.read_text())
    require(isinstance(event_ids, list), "event-ID input must be a JSON list")
    mapping_audit = json.loads(a.mapping_audit.read_text())
    freeze = json.loads(a.pretruth_freeze.read_text())
    truth, audit = parse_truth_after_freeze(
        a.annual_csv.read_bytes(), year=a.year, comparator=a.comparator,
        requested_event_ids=event_ids, mapping_audit=mapping_audit,
        mapping_audit_sha256=MAPPING_AUDIT_SHA256, pretruth_freeze=freeze,
    )
    a.output.mkdir(parents=True, exist_ok=True)
    (a.output / f"truth_{a.comparator.replace(' ', '_').lower()}_{a.year}.json").write_text(
        json.dumps(truth, indent=2, sort_keys=True) + "\n"
    )
    (a.output / f"truth_audit_{a.comparator.replace(' ', '_').lower()}_{a.year}.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
