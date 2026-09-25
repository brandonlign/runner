#!/usr/bin/env python3
from __future__ import annotations

import difflib
import hashlib
import py_compile
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit_p12_snm_id_transport_repair.py V2 V3")
    old_path, new_path = map(Path, sys.argv[1:])
    old = old_path.read_text(encoding="utf-8")
    new = new_path.read_text(encoding="utf-8")
    if sha256(old_path) != V2_SHA256:
        raise RuntimeError(f"matched-v2 source changed: {sha256(old_path)}")
    if sha256(new_path) != V3_SHA256:
        raise RuntimeError(f"matched-v3 source changed: {sha256(new_path)}")

    for needle in (OLD_SIG, OLD_AUDIT, OLD_CALL):
        if old.count(needle) != 1:
            raise RuntimeError(f"old repair anchor count={old.count(needle)} for {needle!r}")
    for needle in (NEW_SIG, NEW_AUDIT, NEW_CALL):
        if new.count(needle) != 1:
            raise RuntimeError(f"new repair anchor count={new.count(needle)} for {needle!r}")

    reverted = new.replace(NEW_SIG, OLD_SIG, 1).replace(NEW_AUDIT, OLD_AUDIT, 1).replace(NEW_CALL, OLD_CALL, 1)
    if reverted != old:
        raise RuntimeError("v3 differs from exact matched-v2 outside the three authorized ID-semantic substitutions")

    if "int(seed_id[:4])" in new:
        raise RuntimeError("event-ID-prefix year inference survived")
    if new.count("year = int(key[:4])") != 2:
        raise RuntimeError("legacy MONTH_KEYS year parsing was altered")
    if new.count("source_seed_years") != old.count("source_seed_years"):
        raise RuntimeError("P12 source-year audit field changed")
    if new.count("source_year") != old.count("source_year") + 3:
        # New formal argument + audit-metadata use + explicit call argument.
        raise RuntimeError("unexpected explicit source_year source delta")
    if "OrbitTrace-April" in new or "target_coordinate" in new:
        raise RuntimeError("forbidden target-specific token present")

    py_compile.compile(str(new_path), doraise=True)
    delta = list(difflib.unified_diff(old.splitlines(), new.splitlines(), fromfile="matched-v2", tofile="matched-v3", lineterm=""))
    removed = [x for x in delta if x.startswith("-") and not x.startswith("---")]
    added = [x for x in delta if x.startswith("+") and not x.startswith("+++")]
    if len(removed) != 3 or len(added) != 3:
        raise RuntimeError(f"unexpected repair diff cardinality removed={len(removed)} added={len(added)}")
    print("\n".join(delta))
    print(f"P14_P12_SNM_ID_TRANSPORT_V3_SHA256={sha256(new_path)}")
    print("PASS_P14_P12_SNM_ID_TRANSPORT_REPAIR_EXACT_SOURCE_EQUIVALENCE")
    print("NO_COMPARATOR_ARTIFACT_NO_ARCHIVE_NO_TRUTH_NO_EXTERNAL_NO_TARGET_ACCESS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
