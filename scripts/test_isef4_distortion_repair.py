#!/usr/bin/env python3
"""Offline invariants: NAIF-backed derived LROC NAC distortion shape only."""
from __future__ import annotations
import copy
import importlib.util
from pathlib import Path

source = Path(__file__).resolve().with_name("isef4_isis_camera_triage.py")
spec = importlib.util.spec_from_file_location("nac_triage", source)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def support(value, naif=0.013):
    return {
        "name_model": "USGS_ASTRO_LINE_SCANNER_SENSOR_MODEL",
        "naif_keywords": {"INS-85600_OD_K": naif},
        "optical_distortion": {"lrolrocnac": {"coefficients": value}},
    }

for value in (0.013, None, [0.013]):
    isd = support(value)
    source_copy = copy.deepcopy(isd["naif_keywords"])
    res = mod.normalize_lroc_nac_distortion(isd)
    assert isd["optical_distortion"]["lrolrocnac"]["coefficients"] == [0.013]
    assert isd["naif_keywords"] == source_copy
    assert res["verified_source_key"] == "INS-85600_OD_K"
    assert res["status"] == ("already_vector" if isinstance(value, list)
                             else "repaired_derived_isd_only")

for value, naif in ((0.015, 0.013), ([0.013, 0.013], 0.013),
                    ("0.013", 0.013), (float("nan"), 0.013),
                    (None, None), (True, 0.013), (None, [1., 2.])):
    isd = support(value, naif)
    old = copy.deepcopy(isd)
    try:
        mod.normalize_lroc_nac_distortion(isd)
    except ValueError:
        assert isd == old or (value != value)  # NaN is not equal to itself
    else:
        raise AssertionError(f"invalid distortion accepted: {value!r}/{naif!r}")

for mutate in (
    lambda x: x.update(name_model="OTHER"),
    lambda x: x.update(optical_distortion={"radial": {"coefficients": 0.013}}),
    lambda x: x.update(naif_keywords={}),
):
    isd = support(0.013)
    mutate(isd)
    try:
        mod.normalize_lroc_nac_distortion(isd)
    except ValueError:
        pass
    else:
        raise AssertionError("wrong source or model accepted")

print("LROC NAC distortion shape invariant: PASS")
