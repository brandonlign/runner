#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ORIGINAL_GIT_BLOB = "fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c"

REPLACEMENTS = (
    ("YEARS = (2022, 2023)", "YEARS = (2020, 2021)"),
    (
        'support.CORPUS = "orbittrace-recurrent-eom-hdbscan-v1-development-2022-2023-target-excluded"',
        'support.CORPUS = "orbittrace-recurrent-eom-hdbscan-v1-gmn-2020-2021-retrospective-target-excluded"',
    ),
    (
        'req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden), "label outside pooled accessible event IDs")',
        'req(all(any(eid in ids_by_year[y] for y in YEARS) for eid in hidden), "label outside pooled accessible event IDs")',
    ),
    (
        'verdict = "PASS_RECURRENT_EOM_HDBSCAN_V1_GMN_DEVELOPMENT" if passed else "FAIL_RECURRENT_EOM_HDBSCAN_V1_GMN_DEVELOPMENT"',
        'verdict = "PASS_RECURRENT_EOM_HDBSCAN_V1_GMN_2020_2021_RETROSPECTIVE_TRANSFER" if passed else "FAIL_RECURRENT_EOM_HDBSCAN_V1_GMN_2020_2021_RETROSPECTIVE_TRANSFER"',
    ),
    (
        '"scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",',
        '"scientific_role": "TARGET_EXCLUDED_GMN_2020_2021_RETROSPECTIVE_TRANSFER_ONLY",',
    ),
    (
        '"dms_scientific_access": False,\n    }\n    (a.output / "RECURRENT_EOM_HDBSCAN_V1_GMN_DEVELOPMENT.json")',
        '"dms_scientific_access": False,\n        "post_result_parameter_search": False,\n    }\n    (a.output / "RECURRENT_EOM_HDBSCAN_V1_GMN_DEVELOPMENT.json")',
    ),
)


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()

    raw = a.source.read_bytes()
    if git_blob_sha(raw) != ORIGINAL_GIT_BLOB:
        raise RuntimeError("binding recurrent-EOM development source blob changed")
    text = raw.decode("utf-8")
    for old, new in REPLACEMENTS:
        count = text.count(old)
        if count != 1:
            raise RuntimeError(f"expected exactly one transport replacement, found {count}: {old[:100]}")
        text = text.replace(old, new, 1)

    # Fail closed against accidental year remnants in executable logic/provenance.
    forbidden = (
        "ids_by_year[2022]",
        "ids_by_year[2023]",
        "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "PASS_RECURRENT_EOM_HDBSCAN_V1_GMN_DEVELOPMENT",
        "FAIL_RECURRENT_EOM_HDBSCAN_V1_GMN_DEVELOPMENT",
    )
    for token in forbidden:
        if token in text:
            raise RuntimeError(f"stale binding-year token survived transport: {token}")

    out = text.encode("utf-8")
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_bytes(out)
    print("original_git_blob", git_blob_sha(raw))
    print("transfer_git_blob", git_blob_sha(out))
    print("transfer_sha256", hashlib.sha256(out).hexdigest())
    print("scientific_method_changes", False)
    print("calendar_transport", "2022,2023 -> 2020,2021")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
