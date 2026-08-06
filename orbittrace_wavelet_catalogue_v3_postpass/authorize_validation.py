#!/usr/bin/env python3
"""Authorize held-out validation only after an immutable development PASS.

This script reads one completed development result JSON. It does not load any
meteor catalogue, OrbitTrace reference, or held-out observation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

FROZEN_SOURCE_COMMIT = "f930664025250c9861683bef5bdeb0c6d19a4231"
EXPECTED_VERDICT = "PASS_WAVELET_CATALOGUE_V3_DEVELOPMENT"
EXPECTED_RESCUE_QUEUE = "fixed4 p <= 1/129; never inserted into wavelet ranking"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("result_json", type=Path)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    raw = args.result_json.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if args.expected_sha256 and digest != args.expected_sha256:
        raise SystemExit(f"development result digest mismatch: {digest}")

    result = json.loads(raw)
    if result.get("verdict") != EXPECTED_VERDICT:
        raise SystemExit(f"development did not pass: {result.get('verdict')}")

    configuration = result.get("configuration", {})
    required_configuration = {
        "years": [2022, 2023],
        "blind_exclusion": [20.0, 55.0],
        "rescue_alpha": 1.0 / 129.0,
        "rescue_queue": EXPECTED_RESCUE_QUEUE,
    }
    for key, expected in required_configuration.items():
        if configuration.get(key) != expected:
            raise SystemExit(
                f"frozen configuration mismatch: {key}={configuration.get(key)!r}"
            )

    gates = result.get("gates")
    if not isinstance(gates, dict) or not gates:
        raise SystemExit("development gates are absent")
    failed = sorted(key for key, value in gates.items() if value is not True)
    if failed:
        raise SystemExit(f"development gates did not all pass: {failed}")

    authorization = {
        "verdict": "AUTHORIZE_TARGET_EXCLUDED_2024_2025_VALIDATION",
        "frozen_source_commit": FROZEN_SOURCE_COMMIT,
        "development_result_sha256": digest,
        "development_years": [2022, 2023],
        "validation_years": [2024, 2025],
        "blind_exclusion": [20.0, 55.0],
        "held_out_catalogues_loaded_by_this_gate": False,
        "orbittrace_reference_loaded_by_this_gate": False,
        "tuning_after_validation_allowed": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(authorization, indent=2) + "\n")
    print(json.dumps(authorization, indent=2))


if __name__ == "__main__":
    main()
