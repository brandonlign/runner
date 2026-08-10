#!/usr/bin/env python3
"""Canonical serializer/validator for frozen pretruth catalogue outputs."""
from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def validate(payload: dict[str, Any]) -> None:
    required = {"method_id", "input_manifest_sha256", "scientific_source_sha256", "families", "truth_accessed", "target_information_accessed"}
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(f"missing required keys: {missing}")
    if payload["truth_accessed"] is not False or payload["target_information_accessed"] is not False:
        raise ValueError("pretruth output integrity flags are not false")
    families = payload["families"]
    if not isinstance(families, list):
        raise TypeError("families must be a list")
    seen_ids: set[str] = set()
    for rank, family in enumerate(families, start=1):
        if int(family.get("rank", -1)) != rank:
            raise ValueError(f"noncontiguous primary rank at {rank}")
        fid = str(family["family_id"])
        if fid in seen_ids:
            raise ValueError(f"duplicate family ID: {fid}")
        seen_ids.add(fid)
        members = [str(x) for x in family["member_ids"]]
        if members != sorted(set(members)):
            raise ValueError(f"members not sorted unique for {fid}")
        forbidden = {"label", "best_label", "shower", "iau_shower", "truth", "matched_shower"} & set(family)
        if forbidden:
            raise ValueError(f"truth-derived family fields present for {fid}: {sorted(forbidden)}")


def self_test() -> None:
    payload = {
        "method_id": "SYNTHETIC",
        "input_manifest_sha256": "a" * 64,
        "scientific_source_sha256": "b" * 64,
        "truth_accessed": False,
        "target_information_accessed": False,
        "families": [
            {"family_id": "F1", "rank": 1, "member_ids": ["E1", "E2"], "score": 1.0},
            {"family_id": "F2", "rank": 2, "member_ids": ["E3"], "score": 0.5},
        ],
    }
    validate(payload)
    first = canonical_bytes(payload)
    second = canonical_bytes(json.loads(first))
    assert first == second
    assert len(hashlib.sha256(first).hexdigest()) == 64


if __name__ == "__main__":
    self_test()
    print("PASS_CANONICAL_PRETRUTH_OUTPUT_V1_SELF_TEST")
