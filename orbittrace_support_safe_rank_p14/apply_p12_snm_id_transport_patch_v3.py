#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

EXACT_P12_SHA256 = "78e93b5af19a441bc58b00428d2b356218b33f7a4a891a640dd59cb5d4599c32"
P12_MATCHED_V2_SHA256 = "f511a012693b7db05495985e32793177c9844196bf82e6f7fe868070ffed34ae"
P12_MATCHED_V3_SHA256 = "55a1efed550498d51b859ffec555797ba8473d7d8b5f20ad6831c5f15b43b415"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"P14 P12 SNM ID transport anchor {label} count={n}")
    return text.replace(old, new, 1)


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_p12_snm_id_transport_patch_v3.py EXACT_P12 OUTPUT")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    if sha256(source) != EXACT_P12_SHA256:
        raise RuntimeError(f"exact P12 source SHA changed: {sha256(source)}")

    here = Path(__file__).resolve().parent.parent / "orbittrace_core_halo_p13_literature"
    v2 = here / "apply_p12_matched_transport_patch_v2.py"
    with tempfile.TemporaryDirectory() as td:
        intermediate = Path(td) / "p12_panel_v2.py"
        subprocess.run([sys.executable, str(v2), str(source), str(intermediate)], check=True)
        if sha256(intermediate) != P12_MATCHED_V2_SHA256:
            raise RuntimeError(f"existing exact matched-v2 source changed: {sha256(intermediate)}")
        text = intermediate.read_text(encoding="utf-8")

    old_sig = '''def source_observation_model(
    rows: list[dict[str, Any]], base: types.ModuleType
) -> tuple[dict[str, float], dict[str, np.ndarray], dict[str, Any]]:
'''
    new_sig = '''def source_observation_model(
    rows: list[dict[str, Any]], base: types.ModuleType, source_year: int
) -> tuple[dict[str, float], dict[str, np.ndarray], dict[str, Any]]:
'''
    text = once(text, old_sig, new_sig, "source_observation_model explicit source-year argument")
    text = once(
        text,
        '    seed_years = sorted(set(int(seed_id[:4]) for seed_id in seed_ids))\n',
        '    seed_years = [int(source_year)]\n',
        "audit-only source_seed_years derivation",
    )
    text = once(
        text,
        '            center, observation_model, obs_audit = source_observation_model(rows_by_year[source_year], base)\n',
        '            center, observation_model, obs_audit = source_observation_model(rows_by_year[source_year], base, source_year)\n',
        "matched call passes existing explicit source year",
    )

    if "int(seed_id[:4])" in text:
        raise RuntimeError("event-ID-prefix source-year inference survived")
    if text.count("year = int(key[:4])") != 2:
        raise RuntimeError("MONTH_KEYS year parsing changed unexpectedly")
    if "OrbitTrace-April" in text or "target_coordinate" in text:
        raise RuntimeError("forbidden target-specific token introduced")

    output.write_text(text, encoding="utf-8")
    result = sha256(output)
    if result != P12_MATCHED_V3_SHA256:
        raise RuntimeError(f"P14 P12 SNM ID transport output SHA changed: {result}")
    print(f"P14_P12_SNM_ID_TRANSPORT_INPUT_SHA256={P12_MATCHED_V2_SHA256}")
    print(f"P14_P12_SNM_ID_TRANSPORT_OUTPUT_SHA256={result}")
    print("P14_P12_SNM_ID_TRANSPORT_SCOPE=audit-only source_seed_years derives from existing explicit source_year; P12 numerical science/membership/gates unchanged; no data/truth/target access")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
