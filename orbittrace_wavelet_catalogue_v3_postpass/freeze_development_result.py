#!/usr/bin/env python3
"""Freeze an authorized development PASS before held-out validation.

The script only hashes and validates two JSON records. It never imports or
opens meteor catalogues, target references, or validation observations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

FROZEN_SOURCE_COMMIT = "f930664025250c9861683bef5bdeb0c6d19a4231"
AUTHORIZATION_VERDICT = "AUTHORIZE_TARGET_EXCLUDED_2024_2025_VALIDATION"
FREEZE_VERDICT = "FREEZE_WAVELET_CATALOGUE_V3_DEVELOPMENT_PASS"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("result_json", type=Path)
    parser.add_argument("authorization_json", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result_digest = sha256(args.result_json)
    authorization_raw = args.authorization_json.read_bytes()
    authorization_digest = hashlib.sha256(authorization_raw).hexdigest()
    authorization = json.loads(authorization_raw)

    required = {
        "verdict": AUTHORIZATION_VERDICT,
        "frozen_source_commit": FROZEN_SOURCE_COMMIT,
        "development_result_sha256": result_digest,
        "development_years": [2022, 2023],
        "validation_years": [2024, 2025],
        "blind_exclusion": [20.0, 55.0],
        "held_out_catalogues_loaded_by_this_gate": False,
        "orbittrace_reference_loaded_by_this_gate": False,
        "tuning_after_validation_allowed": False,
    }
    for key, expected in required.items():
        if authorization.get(key) != expected:
            raise SystemExit(
                f"authorization mismatch: {key}={authorization.get(key)!r}"
            )

    manifest = {
        "verdict": FREEZE_VERDICT,
        "frozen_source_commit": FROZEN_SOURCE_COMMIT,
        "development_result_sha256": result_digest,
        "authorization_sha256": authorization_digest,
        "development_years": [2022, 2023],
        "next_authorized_phase": "target-excluded-2024-2025-validation",
        "blind_exclusion": [20.0, 55.0],
        "held_out_catalogues_loaded_by_this_freeze": False,
        "orbittrace_reference_loaded_by_this_freeze": False,
        "scientific_tuning_authorized": False,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
