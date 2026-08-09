#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

DEV_SHA256 = "78e93b5af19a441bc58b00428d2b356218b33f7a4a891a640dd59cb5d4599c32"
MATCHED_V3_SHA256 = "55a1efed550498d51b859ffec555797ba8473d7d8b5f20ad6831c5f15b43b415"

OLD_REQUIRE = '            require(len(negative_events) >= MIN_DIRECTION_NEGATIVES, f"P2 input-ineligible: <{MIN_DIRECTION_NEGATIVES} negatives for {family_id} {source_year}->{target_year}")\n'
NEW_SUPPORT = '''            if len(negative_events) < MIN_DIRECTION_NEGATIVES:\n                direction_audits.append({\n                    "family_id": family_id,\n                    "source_year": source_year,\n                    "target_year": target_year,\n                    "source_seed_count": len(source_ids),\n                    "p12_source_fit_year": int(source_year),\n                    "p12_target_evaluation_year": int(target_year),\n                    "positive_count": len(rows_by_year[target_year]),\n                    "negative_count": len(negative_events),\n                    "target_centroid_sol": float(target_center["sol"]),\n                    "p15_characterization_status": "CHARACTERIZATION_UNAVAILABLE_INSUFFICIENT_NEGATIVES",\n                    "p15_required_negative_count": int(MIN_DIRECTION_NEGATIVES),\n                    "p15_nonseed_proposals_contributed": 0,\n                    **obs_audit,\n                })\n                continue\n'''

HALO_ANCHOR = '    halo_checkpoint = {\n'
HALO_LEDGER = '''    p15_unavailable_directions = sorted(\n        [\n            {\n                "family_id": str(a["family_id"]),\n                "source_year": int(a["source_year"]),\n                "target_year": int(a["target_year"]),\n                "negative_count": int(a["negative_count"]),\n                "required_negative_count": int(a["p15_required_negative_count"]),\n                "status": str(a["p15_characterization_status"]),\n            }\n            for a in direction_audits\n            if a.get("p15_characterization_status") == "CHARACTERIZATION_UNAVAILABLE_INSUFFICIENT_NEGATIVES"\n        ],\n        key=lambda a: (a["family_id"], a["source_year"], a["target_year"]),\n    )\n    p15_unavailable_directions_sha256 = hashlib.sha256(\n        json.dumps(p15_unavailable_directions, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()\n    ).hexdigest()\n\n    halo_checkpoint = {\n'''

CHECKPOINT_ANCHOR = '        "parameter_search": False,\n        "core_families": families,\n'
CHECKPOINT_FIELDS = '''        "parameter_search": False,\n        "p15_secondary_halo_support_safe": True,\n        "p15_required_negative_count": int(MIN_DIRECTION_NEGATIVES),\n        "p15_unavailable_directions": p15_unavailable_directions,\n        "p15_unavailable_directions_sha256": p15_unavailable_directions_sha256,\n        "core_families": families,\n'''


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"P15 anchor {label} count={count}")
    return text.replace(old, new, 1)


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_p15_support_safe_halo_patch.py INPUT OUTPUT")
    source, output = map(Path, sys.argv[1:])
    raw = source.read_bytes()
    source_sha = digest(raw)
    if source_sha not in {DEV_SHA256, MATCHED_V3_SHA256}:
        raise RuntimeError(f"P15 source not exact frozen development/matched-v3 source: {source_sha}")
    text = raw.decode("utf-8")
    if text.count("MIN_DIRECTION_NEGATIVES = 128") != 1:
        raise RuntimeError("P15 immutable MIN_DIRECTION_NEGATIVES=128 changed")
    if "CHARACTERIZATION_UNAVAILABLE_INSUFFICIENT_NEGATIVES" in text:
        raise RuntimeError("P15 support-safe rule already present")
    patched = replace_once(text, OLD_REQUIRE, NEW_SUPPORT, "negative-support fail-closed rule")

    if source_sha == MATCHED_V3_SHA256:
        if "import hashlib" not in patched or "import json" not in patched:
            raise RuntimeError("matched P15 source lacks required existing hashlib/json imports")
        patched = replace_once(patched, HALO_ANCHOR, HALO_LEDGER, "matched availability ledger")
        patched = replace_once(patched, CHECKPOINT_ANCHOR, CHECKPOINT_FIELDS, "matched checkpoint ledger fields")
    else:
        if HALO_ANCHOR in patched:
            raise RuntimeError("development P12 unexpectedly contains matched halo checkpoint")

    if patched.count("MIN_DIRECTION_NEGATIVES = 128") != 1:
        raise RuntimeError("P15 changed negative-support threshold")
    if "try:" in NEW_SUPPORT or "except" in NEW_SUPPORT:
        raise RuntimeError("P15 may not introduce general exception handling")
    for token in ("OrbitTrace-April", "target_coordinate"):
        if token in patched:
            raise RuntimeError(f"forbidden target token present: {token}")
    output.write_text(patched, encoding="utf-8")
    print(f"P15_INPUT_SHA256={source_sha}")
    print(f"P15_OUTPUT_SHA256={digest(patched.encode('utf-8'))}")
    print("P15_SCOPE=secondary halo availability only; immutable 128 minimum; unavailable direction contributes zero proposals; primary core/rank untouched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
