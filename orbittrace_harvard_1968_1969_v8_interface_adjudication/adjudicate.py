#!/usr/bin/env python3
"""Pre-data adjudication of Harvard 1968/1969 against the frozen v8 input contract."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

EXPECTED_FIXED4_SHA256 = "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62"
EXPECTED_FIELDS = {
    "ORBIT_NUMBER",
    "OBSERVATION_TIME",
    "SEMIMAJOR_AXIS",
    "ECCENTRICITY",
    "PERIHELION_DISTANCE",
    "APHELION_DISTANCE",
    "INCLINATION",
    "AOP",
    "LAN",
    "LOP",
    "LMA",
    "VINF",
    "RADIANT_RA",
    "RADIANT_DEC",
}
ORBITAL_FIELDS = {
    "SEMIMAJOR_AXIS",
    "ECCENTRICITY",
    "PERIHELION_DISTANCE",
    "APHELION_DISTANCE",
    "INCLINATION",
    "AOP",
    "LAN",
    "LOP",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def find_fixed4_source(root: Path) -> Path:
    matches = list(root.rglob("run_fixed4_support_wrapper_development.py"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one fixed4 source file, found {len(matches)}")
    return matches[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--structure-json", required=True, type=Path)
    ap.add_argument("--fixed4-artifact", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    structure = json.loads(args.structure_json.read_text())
    assert structure["verdict"] == "PASS_HARVARD_1968_1969_STRUCTURE_AUDIT"
    assert structure["target_table_member_opened"] is False
    assert structure["scientific_event_values_inspected"] is False
    assert structure["orbittrace_target_information_access"] is False

    fixed4_dir = args.output / "fixed4_source"
    fixed4_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(args.fixed4_artifact) as zf:
        zf.extractall(fixed4_dir)
    fixed4 = find_fixed4_source(fixed4_dir)
    fixed4_sha = sha256(fixed4)
    assert fixed4_sha == EXPECTED_FIXED4_SHA256, fixed4_sha
    src = fixed4.read_text(errors="replace")

    source_gates = {
        "geocentric_ecliptic_longitude_contract": '"lam": pick(cols, [("lamgeo", "deg"), ("geocentric", "ecliptic", "longitude")])' in src,
        "geocentric_ecliptic_latitude_contract": '"bet": pick(cols, [("betgeo", "deg"), ("geocentric", "ecliptic", "latitude")])' in src,
        "geocentric_velocity_contract": '"vg": pick(cols, [("vgeo", "km", "s"), ("geocentric", "velocity")])' in src,
        "feature_matrix_uses_ecliptic_lon": "e.ecl_lon" in src,
        "feature_matrix_uses_ecliptic_lat": "e.ecl_lat" in src,
        "feature_matrix_uses_vg_over_40": "e.vg / 40.0" in src,
        "family_link_radius_1_5": bool(re.search(r"^FAMILY_LINK_RADIUS\s*=\s*1\.5\s*$", src, re.M)),
    }
    assert all(source_gates.values()), source_gates

    fields = structure["schema_fields"]
    by_name = {f.get("name"): f for f in fields if f.get("name")}
    assert set(by_name) == EXPECTED_FIELDS, set(by_name)

    ra_desc = by_name["RADIANT_RA"].get("description", "")
    dec_desc = by_name["RADIANT_DEC"].get("description", "")
    vinf_desc = by_name["VINF"].get("description", "")
    label_gates = {
        "ra_is_observed_radiant_b1950": "observed radiant" in ra_desc.lower() and "b1950" in ra_desc.lower(),
        "dec_is_observed_radiant_b1950": "observed radiant" in dec_desc.lower() and "b1950" in dec_desc.lower(),
        "vinf_is_top_of_atmosphere": "top of the atmosphere" in vinf_desc.lower(),
    }
    assert all(label_gates.values()), label_gates

    non_orbital = EXPECTED_FIELDS - ORBITAL_FIELDS
    # The official non-orbital interface contains time, IDs, one angular elongation,
    # VINF, and observed RA/DEC, but no site/position/height or native geocentric fields.
    native_geocentric_fields = {
        name for name in non_orbital
        if re.search(r"(^|_)(VG|V_G|GEOCENTRIC|LAMG|BETG)($|_)", name, re.I)
    }
    event_state_fields = {
        name for name in non_orbital
        if re.search(r"SITE|STATION|LATITUDE|LONGITUDE|HEIGHT|ALTITUDE|POSITION|RANGE|ZENITH", name, re.I)
    }

    compatibility = bool(native_geocentric_fields or event_state_fields)
    # Even if an unrelated token matched, the exact required state must be source-proven.
    # With the frozen 14-field schema it is not.
    exact_recovery_available = False
    verdict = "PASS_HARVARD_1968_1969_V8_INTERFACE_COMPATIBILITY" if exact_recovery_available else "FAIL_HARVARD_1968_1969_V8_INTERFACE_COMPATIBILITY"

    result = {
        "verdict": verdict,
        "fixed4_source_sha256": fixed4_sha,
        "fixed4_source_gates": source_gates,
        "harvard_label_gates": label_gates,
        "harvard_field_names": sorted(EXPECTED_FIELDS),
        "harvard_orbital_fields_reserved_post_ranking": sorted(ORBITAL_FIELDS),
        "native_geocentric_nonorbital_fields": sorted(native_geocentric_fields),
        "event_site_position_height_fields": sorted(event_state_fields),
        "schema_has_any_candidate_state_token": compatibility,
        "exact_nonorbital_geocentric_recovery_available": exact_recovery_available,
        "failure_reason": (
            "Frozen v8 requires geocentric ecliptic radiant longitude/latitude and geocentric velocity in its discovery metric. "
            "The official Harvard non-orbital interface provides only B1950 observed radiant and VINF at the top of the atmosphere, plus observation time/ID/LMA, with no event-specific site/meteor-position/height state. "
            "Recovering exact geocentric discovery coordinates would therefore require orbital-element inversion or an assumed/learned apparent-to-geocentric correction, neither of which is permitted for an external validation of the frozen v8 method."
        ),
        "harvard_event_table_opened": False,
        "harvard_event_values_inspected": False,
        "orbital_elements_used_for_discovery": False,
        "approximate_transform_introduced": False,
        "v8_modified": False,
        "orbittrace_target_information_access": False,
        "claim_boundary": (
            "Pre-event-data interface compatibility only. This FAIL does not measure v8 performance. Harvard 1968-1969 remains scientifically fresh but cannot supply the exact frozen v8 discovery coordinates without prohibited adaptation."
        ),
    }
    (args.output / "harvard_1968_1969_v8_interface_adjudication.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))

    # Remove extracted source tree so artifact contains adjudication result/provenance only.
    for path in sorted(fixed4_dir.rglob("*"), reverse=True):
        if path.is_file() or path.is_symlink():
            path.unlink()
        elif path.is_dir():
            path.rmdir()
    fixed4_dir.rmdir()

    # FAIL is the expected scientific adjudication outcome, not an infrastructure failure.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
