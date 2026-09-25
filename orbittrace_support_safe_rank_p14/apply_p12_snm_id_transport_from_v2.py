#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

V2_SHA256 = "f511a012693b7db05495985e32793177c9844196bf82e6f7fe868070ffed34ae"
V3_SHA256 = "55a1efed550498d51b859ffec555797ba8473d7d8b5f20ad6831c5f15b43b415"

OLD_SIG = '''def source_observation_model(
    rows: list[dict[str, Any]], base: types.ModuleType
) -> tuple[dict[str, float], dict[str, np.ndarray], dict[str, Any]]:
'''
NEW_SIG = '''def source_observation_model(
    rows: list[dict[str, Any]], base: types.ModuleType, source_year: int
) -> tuple[dict[str, float], dict[str, np.ndarray], dict[str, Any]]:
'''
OLD_AUDIT = '    seed_years = sorted(set(int(seed_id[:4]) for seed_id in seed_ids))\n'
NEW_AUDIT = '    seed_years = [int(source_year)]\n'
OLD_CALL = '            center, observation_model, obs_audit = source_observation_model(rows_by_year[source_year], base)\n'
NEW_CALL = '            center, observation_model, obs_audit = source_observation_model(rows_by_year[source_year], base, source_year)\n'


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"P14 matched-v3 anchor {label} count={n}")
    return text.replace(old, new, 1)


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_p12_snm_id_transport_from_v2.py MATCHED_V2 OUTPUT")
    source, output = map(Path, sys.argv[1:])
    raw = source.read_bytes()
    if digest(raw) != V2_SHA256:
        raise RuntimeError(f"matched-v2 source changed: {digest(raw)}")
    text = raw.decode("utf-8")
    text = once(text, OLD_SIG, NEW_SIG, "explicit source-year argument")
    text = once(text, OLD_AUDIT, NEW_AUDIT, "audit-only source year")
    text = once(text, OLD_CALL, NEW_CALL, "explicit source-year call")
    result = digest(text.encode("utf-8"))
    if result != V3_SHA256:
        raise RuntimeError(f"matched-v3 output changed: {result}")
    if "int(seed_id[:4])" in text:
        raise RuntimeError("event-ID-prefix year inference survived")
    if text.count("year = int(key[:4])") != 2:
        raise RuntimeError("MONTH_KEYS parsing changed")
    if "OrbitTrace-April" in text or "target_coordinate" in text:
        raise RuntimeError("forbidden target-specific token introduced")
    output.write_text(text, encoding="utf-8")
    print(f"P14_MATCHED_V3_TRANSPORT_SHA256={result}")
    print("PASS_P14_MATCHED_V3_AUDIT_ONLY_SNM_ID_TRANSPORT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
