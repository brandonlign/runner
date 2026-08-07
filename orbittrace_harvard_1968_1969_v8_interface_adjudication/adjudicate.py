#!/usr/bin/env python3
"""Pre-data adjudication of Harvard 1968/1969 against the frozen v8 input contract.

Source-check correction: wrapper proves the geocentric input mapping/family radius;
the paired immutable blind-catalogue source proves the feature-matrix transform/scales.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

EXPECTED_WRAPPER_SHA256 = "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62"
EXPECTED_BLIND_SHA256 = "48434df612f790924e6efce45b6b8d4de1401880f398994bc58eef2fce0987e5"
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


def find_one(root: Path, basename: str) -> Path:
    matches = list(root.rglob(basename))
    if len(matches) != 1:
        raise RuntimeError(f"expected one {basename}, found {len(matches)}")
    return matches[0]


def field_text(field: dict) -> str:
    return " ".join(str(v) for v in field.values()).lower()


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

    wrapper = find_one(fixed4_dir, "run_fixed4_support_wrapper_development.py")
    blind = find_one(fixed4_dir, "run_fixed4_blind_catalogue.py")
    wrapper_sha = sha256(wrapper)
    blind_sha = sha256(blind)
    assert wrapper_sha == EXPECTED_WRAPPER_SHA256, wrapper_sha
    assert blind_sha == EXPECTED_BLIND_SHA256, blind_sha
    wrapper_src = wrapper.read_text(errors="replace")
    blind_src = blind.read_text(errors="replace")

    source_gates = {
        "geocentric_ecliptic_longitude_contract": '"lam": pick(cols, [("lamgeo", "deg"), ("geocentric", "ecliptic", "longitude")])' in wrapper_src,
        "geocentric_ecliptic_latitude_contract": '"bet": pick(cols, [("betgeo", "deg"), ("geocentric", "ecliptic", "latitude")])' in wrapper_src,
        "geocentric_velocity_contract": '"vg": pick(cols, [("vgeo", "km", "s"), ("geocentric", "velocity")])' in wrapper_src,
        "sun_centered_longitude_from_lam_minus_sol": 'sun_lon = base.wrap180(selected["lam"].to_numpy(float) - selected["sol"].to_numpy(float))' in blind_src,
        "feature_matrix_uses_sun_lon": 'float(e["sun_lon"]) for e in events' in blind_src,
        "feature_matrix_uses_ecliptic_lat": 'float(e["ecl_lat"]) for e in events' in blind_src,
        "angular_scale_2deg": 'sphere_scale = (180.0 / math.pi) / 2.0' in blind_src,
        "vg_scale_2kms": 'float(e["vg"]) for e in events], dtype=np.float64) / 2.0' in blind_src,
        "sol_scale_4deg": 'float(base.wrap180(float(e["sol"]) - center_sol)) for e in events], dtype=np.float64) / 4.0' in blind_src,
        "family_link_radius_1_5": bool(re.search(r"^FAMILY_LINK_RADIUS\s*=\s*1\.5\s*$", wrapper_src, re.M)),
    }
    assert all(source_gates.values()), source_gates

    fields = structure["schema_fields"]
    by_name = {f.get("name"): f for f in fields if f.get("name")}
    assert set(by_name) == EXPECTED_FIELDS, set(by_name)

    ra_desc = by_name["RADIANT_RA"].get("description", "")
    dec_desc = by_name["RADIANT_DEC"].get("description", "")
    vinf_desc = by_name["VINF"].get("description", "")
    lma_desc = by_name["LMA"].get("description", "")
    label_gates = {
        "ra_is_observed_radiant_b1950": "observed radiant" in ra_desc.lower() and "b1950" in ra_desc.lower(),
        "dec_is_observed_radiant_b1950": "observed" in dec_desc.lower() and "radiant" in dec_desc.lower() and "b1950" in dec_desc.lower(),
        "vinf_is_top_of_atmosphere": "top of the atmosphere" in vinf_desc.lower(),
        "lma_is_lambda_minus_apex": "lambda minus the apex" in lma_desc.lower(),
    }
    assert all(label_gates.values()), label_gates

    non_orbital_names = EXPECTED_FIELDS - ORBITAL_FIELDS
    non_orbital_fields = [by_name[name] for name in sorted(non_orbital_names)]
    native_geocentric_fields = [
        f["name"] for f in non_orbital_fields
        if "geocentric" in field_text(f)
    ]
    event_site_position_height_fields = [
        f["name"] for f in non_orbital_fields
        if any(token in field_text(f) for token in (
            "observatory", "observer location", "station latitude", "station longitude",
            "geographic latitude", "geographic longitude", "meteor height", "meteor position",
            "trajectory position", "local zenith", "range to meteor",
        ))
    ]

    exact_recovery_available = bool(native_geocentric_fields) or bool(event_site_position_height_fields)
    # A generic time, observed radiant, VINF, or lambda-minus-apex quantity is not the
    # event-specific observer/meteor state required for an exact apparent->geocentric radiant reduction.
    verdict = (
        "PASS_HARVARD_1968_1969_V8_INTERFACE_COMPATIBILITY"
        if exact_recovery_available
        else "FAIL_HARVARD_1968_1969_V8_INTERFACE_COMPATIBILITY"
    )

    result = {
        "verdict": verdict,
        "wrapper_source_sha256": wrapper_sha,
        "blind_catalogue_source_sha256": blind_sha,
        "fixed4_source_gates": source_gates,
        "harvard_label_gates": label_gates,
        "harvard_field_names": sorted(EXPECTED_FIELDS),
        "harvard_orbital_fields_reserved_post_ranking": sorted(ORBITAL_FIELDS),
        "native_geocentric_nonorbital_fields": native_geocentric_fields,
        "event_site_position_height_fields": event_site_position_height_fields,
        "exact_nonorbital_geocentric_recovery_available": exact_recovery_available,
        "failure_reason": None if exact_recovery_available else (
            "Frozen v8 ingests geocentric ecliptic longitude/latitude and geocentric velocity, then uses sun-centered longitude = wrap180(lambda_g - solar_longitude), latitude, and Vg in its frozen discovery geometry. "
            "The official Harvard non-orbital interface provides B1950 observed radiant, VINF at the top of the atmosphere, LMA=lambda-minus-apex, observation time, and orbit number, but no native geocentric field or event-specific site/meteor-position/height state. "
            "Exact geocentric discovery coordinates therefore cannot be recovered from the non-orbital interface alone. Doing so would require orbital-element inversion or an assumed/learned apparent-to-geocentric correction, both prohibited for a frozen-v8 external validation."
        ),
        "prior_checker_failure_run_preserved": 31226997818,
        "harvard_event_table_opened": False,
        "harvard_event_values_inspected": False,
        "orbital_elements_used_for_discovery": False,
        "approximate_transform_introduced": False,
        "v8_modified": False,
        "orbittrace_target_information_access": False,
        "claim_boundary": (
            "Pre-event-data interface compatibility only. A FAIL does not measure v8 performance. Harvard 1968-1969 remains scientifically fresh but cannot supply the exact frozen v8 discovery coordinates without prohibited adaptation."
        ),
    }
    (args.output / "harvard_1968_1969_v8_interface_adjudication.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))

    for path in sorted(fixed4_dir.rglob("*"), reverse=True):
        if path.is_file() or path.is_symlink():
            path.unlink()
        elif path.is_dir():
            path.rmdir()
    fixed4_dir.rmdir()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
