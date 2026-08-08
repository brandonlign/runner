#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import tarfile
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import requests

YEARS = (2016, 2017)
N_EXPECTED = 107
TOP_K = 100
MIN_Q = 30
AU_M = 149_597_870_700.0
CONTENT_URL = "https://zenodo.org/api/records/15553437/files/silseth_thesis_data.tar.gz/content"
EXPECTED_FILE_SIZE = 21_485_785_089
GEOMETRY_RESULT_SHA256 = "12705afe1d499f8c0a5acbbae37d7119e4c369015b1cd1cfc18f2c3b63086351"
GEOMETRY_RANKING_FILE_SHA256 = "fe8905d4c681a62f0b3f3b574465793d157f378d5c8321910f8d0bc6875e7279"
GEOMETRY_CANONICAL_RANKING_SHA256 = "a23696dc09896696d8b3c210181b9f0f93446dde73329f1ac5c53a4cf288c05b"
DSH_THRESHOLD = 0.05
MIN_YEAR_ORBIT_MEMBERS = 4
MIN_ORBITAL_PRECISION = 0.50
NEXT_YEAR_PREFIX = "data/2018/"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_sha256(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_module(path: Path, name: str) -> Any:
    require(path.is_file(), f"missing frozen source: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"could not load module spec: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_event_id(event_id: str) -> tuple[int, str, int]:
    parts = event_id.split("|", 3)
    require(len(parts) == 4 and parts[0] == "MAARSY", f"invalid MAARSY event id: {event_id}")
    year = int(parts[1])
    member = parts[2]
    row_index = int(parts[3])
    require(year in YEARS, f"MAARSY event outside frozen years: {event_id}")
    require(member.startswith(f"data/{year}/") and member.endswith("/kep_collect.h5"), f"unexpected MAARSY member: {event_id}")
    require(row_index >= 0, f"negative MAARSY row index: {event_id}")
    return year, member, row_index


def read_needed_native_orbits(
    needed_ids: set[str],
    output: Path,
) -> tuple[dict[str, dict[str, float]], dict[str, Any]]:
    wanted_by_member: dict[str, dict[int, str]] = {}
    for eid in sorted(needed_ids):
        _year, member, row = parse_event_id(eid)
        row_map = wanted_by_member.setdefault(member, {})
        require(row not in row_map, f"duplicate needed row identity for {member}:{row}")
        row_map[row] = eid

    seen_members: set[str] = set()
    orbits: dict[str, dict[str, float]] = {}
    invalid_rows: list[str] = []
    member_audits: list[dict[str, Any]] = []
    stopped_at_2018: str | None = None
    tmp = output / "_orbit_tmp"
    tmp.mkdir(exist_ok=True)

    with requests.get(
        CONTENT_URL,
        timeout=(60, 600),
        stream=True,
        headers={"User-Agent": "OrbitTrace-v8-MAARSY-orbital-validation/1.0", "Accept-Encoding": "identity"},
    ) as response:
        response.raise_for_status()
        total = response.headers.get("Content-Length")
        if total is not None:
            require(int(total) == EXPECTED_FILE_SIZE, f"MAARSY content length changed: {total}")
        response.raw.decode_content = False
        with tarfile.open(fileobj=response.raw, mode="r|gz") as tf:
            for member in tf:
                name = member.name.lstrip("./")
                if name.startswith(NEXT_YEAR_PREFIX):
                    stopped_at_2018 = name
                    break
                row_map = wanted_by_member.get(name)
                if row_map is None:
                    continue
                require(member.isfile(), f"needed MAARSY member is not regular file: {name}")
                require(name not in seen_members, f"duplicate needed archive member: {name}")
                seen_members.add(name)
                extracted = tf.extractfile(member)
                require(extracted is not None, f"could not open needed MAARSY member: {name}")
                local = tmp / f"needed-{len(seen_members):03d}.h5"
                written = 0
                with local.open("wb") as out:
                    while True:
                        chunk = extracted.read(1024 * 1024)
                        if not chunk:
                            break
                        out.write(chunk)
                        written += len(chunk)
                require(written == int(member.size), f"needed member byte count changed: {name}")

                rows = sorted(row_map)
                with h5py.File(local, "r") as h:
                    require("kepler" in h and isinstance(h["kepler"], h5py.Dataset), f"missing kepler dataset: {name}")
                    ds = h["kepler"]
                    require(ds.ndim == 2 and ds.shape[1] == 6, f"kepler shape changed in {name}: {ds.shape}")
                    require(ds.dtype.kind in "fi", f"kepler dtype changed in {name}: {ds.dtype}")
                    require(rows and rows[-1] < ds.shape[0], f"needed row outside kepler dataset in {name}")
                    # FIRST ORBIT VALUES: only immutable family-event rows are read.
                    values = np.asarray(ds[np.asarray(rows, dtype=np.int64), :], dtype=np.float64)

                require(values.shape == (len(rows), 6), f"kepler read shape mismatch in {name}")
                valid_count = 0
                for idx, row in enumerate(rows):
                    eid = row_map[row]
                    k = values[idx]
                    a_m, e, inc_deg, omega_deg, node_deg, _nu_deg = [float(x) for x in k]
                    a_au = a_m / AU_M
                    q_au = abs(a_au * (1.0 - e))
                    valid = bool(
                        np.all(np.isfinite(k))
                        and math.isfinite(a_au)
                        and math.isfinite(q_au)
                        and q_au > 0.0
                        and e >= 0.0
                        and 0.0 <= inc_deg <= 180.0
                        and math.isfinite(omega_deg)
                        and math.isfinite(node_deg)
                    )
                    if not valid:
                        invalid_rows.append(eid)
                        continue
                    orbits[eid] = {
                        "q": float(q_au),
                        "e": float(e),
                        "i": float(inc_deg),
                        "arg": float(omega_deg % 360.0),
                        "node": float(node_deg % 360.0),
                    }
                    valid_count += 1
                member_audits.append(
                    {
                        "member": name,
                        "member_size": int(member.size),
                        "needed_rows": len(rows),
                        "valid_orbit_rows": valid_count,
                        "invalid_orbit_rows": len(rows) - valid_count,
                        "kepler_shape": [int(x) for x in ds.shape],
                        "kepler_dtype": str(ds.dtype),
                    }
                )
                local.unlink()

    require(stopped_at_2018 is not None, "archive stream never reached first 2018 header")
    missing_members = sorted(set(wanted_by_member) - seen_members)
    require(not missing_members, f"needed MAARSY members missing before 2018: {missing_members[:10]}")
    missing_ids = sorted(needed_ids - set(orbits) - set(invalid_rows))
    require(not missing_ids, f"needed MAARSY event IDs neither valid nor explicitly invalid: {missing_ids[:10]}")
    try:
        tmp.rmdir()
    except OSError:
        pass

    return orbits, {
        "needed_family_events": len(needed_ids),
        "needed_archive_members": len(wanted_by_member),
        "seen_needed_archive_members": len(seen_members),
        "valid_orbital_events": len(orbits),
        "invalid_or_missing_orbital_events": len(needed_ids) - len(orbits),
        "explicit_invalid_orbital_event_ids": invalid_rows,
        "member_audits": member_audits,
        "stopped_at_first_2018_member_header": stopped_at_2018,
        "native_kepler_mapping": ["a_m", "e", "i_deg", "omega_deg", "Omega_deg", "nu_deg"],
        "au_m": AU_M,
        "q_definition": "abs((a_m/AU_M)*(1-e))",
        "kepler_std_opened": False,
        "geometry_fields_opened_this_stage": False,
        "orbital_elements_interpreted_only_after_rank_freeze": True,
        "target_information_access": False,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--geometry-result", required=True, type=Path)
    p.add_argument("--geometry-ranking", required=True, type=Path)
    p.add_argument("--external-evaluator", required=True, type=Path)
    p.add_argument("--dsh-comparator", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    require(sha256_file(args.geometry_result) == GEOMETRY_RESULT_SHA256, "geometry result SHA-256 changed")
    require(sha256_file(args.geometry_ranking) == GEOMETRY_RANKING_FILE_SHA256, "geometry ranking file SHA-256 changed")
    geometry = json.loads(args.geometry_result.read_text())
    ranked = json.loads(args.geometry_ranking.read_text())
    require(geometry["verdict"] == "PASS_V8_MAARSY_EXTERNAL_N_POWER_GATE", "geometry N-power gate no longer passed")
    require(geometry["family_count"] == N_EXPECTED, "geometry family count changed")
    require(geometry["configuration"]["years"] == list(YEARS), "geometry years changed")
    require(geometry["N_power_gate_passed"] is True, "geometry N power flag changed")
    require(geometry["Q_power_gate_evaluated"] is False, "geometry stage unexpectedly evaluated Q")
    require(geometry["orbit_access"] is False and geometry["target_information_access"] is False, "geometry prerequisite crossed orbit/target boundary")
    require(all(geometry["integrity_gates"].values()), "geometry integrity gate no longer all-pass")
    require(geometry["ranking_sha256_before_any_orbit_access"] == GEOMETRY_CANONICAL_RANKING_SHA256, "geometry canonical ranking hash changed")
    require(canonical_sha256(ranked) == GEOMETRY_CANONICAL_RANKING_SHA256, "recomputed geometry canonical ranking hash changed")
    require(ranked["family_count"] == N_EXPECTED and ranked["years"] == list(YEARS), "ranked geometry universe changed")
    require(ranked["orbit_access"] is False and ranked["target_information_access"] is False, "ranked geometry payload crossed firewall")

    families = ranked["families"]
    rankings = ranked["rankings"]
    require(len(families) == N_EXPECTED, "family payload count changed")
    family_ids = {str(f["family_id"]) for f in families}
    require(len(family_ids) == N_EXPECTED, "family IDs not unique")
    for name in ("multiplicity", "brown", "v3", "label_free_persistence"):
        order = [str(x) for x in rankings[name]]
        require(len(order) == N_EXPECTED and set(order) == family_ids, f"{name} ranking universe changed")

    evaluator = load_module(args.external_evaluator, "frozen_saamer_external_evaluator")
    dsh = load_module(args.dsh_comparator, "frozen_orbittrace_dsh")
    require(abs(float(evaluator.DSH_THRESHOLD) - DSH_THRESHOLD) < 1e-15, "external D_SH threshold changed")
    require(int(evaluator.MIN_YEAR_ORBIT_MEMBERS) == MIN_YEAR_ORBIT_MEMBERS, "external min year orbit members changed")
    require(abs(float(evaluator.MIN_ORBITAL_PRECISION) - MIN_ORBITAL_PRECISION) < 1e-15, "external orbital precision changed")
    require(int(evaluator.TOP_K) == TOP_K, "external top-k changed")
    require(int(evaluator.MIN_FAMILIES) == 100 and int(evaluator.MIN_ORBITALLY_CORROBORATED) == MIN_Q, "external power floors changed")
    require(abs(float(dsh.RUD2014_DSH_THRESHOLD) - DSH_THRESHOLD) < 1e-15, "frozen D_SH comparator threshold changed")

    # Dataset-specific identity parser only; corroboration/evaluation algorithms remain byte-frozen.
    evaluator.YEARS = YEARS
    evaluator.parse_event_id = parse_event_id

    needed_ids = {str(eid) for family in families for eid in family["event_ids"]}
    require(needed_ids, "empty immutable family-event universe")

    # FIRST MAARSY ORBIT-VALUE ACCESS occurs here, after family/ranking/source rules are immutable.
    orbits, orbit_audit = read_needed_native_orbits(needed_ids, args.output)
    corroboration, orbital_summary = evaluator.orbital_corroboration(families, orbits, dsh)
    metrics = {name: evaluator.evaluate_ranking([str(x) for x in order], corroboration) for name, order in rankings.items()}

    n = len(families)
    q = int(orbital_summary["orbitally_corroborated_families"])
    require(n == N_EXPECTED, "N changed after orbit access")
    m = int(metrics["multiplicity"]["top_k_orbitally_corroborated"])
    b = int(metrics["brown"]["top_k_orbitally_corroborated"])
    persistence = int(metrics["label_free_persistence"]["top_k_orbitally_corroborated"])
    required_vs_persistence = int(math.ceil(0.90 * persistence))

    integrity_gates = {
        "immutable_geometry_artifact_and_ranking_hashes": True,
        "geometry_N_power_gate_passed_with_107_families": n == N_EXPECTED,
        "all_geometry_integrity_gates_preserved": all(geometry["integrity_gates"].values()),
        "rankings_frozen_before_orbit_access": orbit_audit["orbital_elements_interpreted_only_after_rank_freeze"] is True,
        "only_immutable_family_event_orbits_read": orbit_audit["needed_family_events"] == len(needed_ids),
        "all_needed_archive_members_found_before_2018": orbit_audit["needed_archive_members"] == orbit_audit["seen_needed_archive_members"],
        "native_DASST_pyorb_mapping_used_without_remapping": orbit_audit["native_kepler_mapping"] == ["a_m", "e", "i_deg", "omega_deg", "Omega_deg", "nu_deg"] and orbit_audit["au_m"] == AU_M,
        "kepler_std_unopened": orbit_audit["kepler_std_opened"] is False,
        "geometry_fields_unopened_in_orbit_stage": orbit_audit["geometry_fields_opened_this_stage"] is False,
        "frozen_DSH_threshold_005": abs(float(dsh.RUD2014_DSH_THRESHOLD) - DSH_THRESHOLD) < 1e-15,
        "frozen_orbital_component_rule": int(evaluator.MIN_YEAR_ORBIT_MEMBERS) == 4 and abs(float(evaluator.MIN_ORBITAL_PRECISION) - 0.50) < 1e-15,
        "no_target_information_access": orbit_audit["target_information_access"] is False,
    }

    q_power = q >= MIN_Q
    scientific_gates = {
        "multiplicity_top100_beats_brown_by_at_least_one": m >= b + 1,
        "multiplicity_top100_at_least_90pct_persistence": m >= required_vs_persistence,
        "multiplicity_top100_hypergeometric_enrichment_p_le_005": float(metrics["multiplicity"]["hypergeometric_enrichment_p"]) <= 0.05,
    }

    if not all(integrity_gates.values()):
        verdict = "FAIL_V8_MAARSY_EXTERNAL_ORBITAL_INTEGRITY"
    elif not q_power:
        verdict = "INCONCLUSIVE_V8_MAARSY_EXTERNAL_POWER_Q"
    elif all(scientific_gates.values()):
        verdict = "PASS_V8_MAARSY_EXTERNAL_VALIDATION"
    else:
        verdict = "FAIL_V8_MAARSY_EXTERNAL_VALIDATION"

    result = {
        "schema": "orbittrace-v8-maarsy-2016-2017-external-validation-v1",
        "verdict": verdict,
        "configuration": {
            "years": list(YEARS),
            "immutable_geometry_family_count_N": N_EXPECTED,
            "geometry_ranking_sha256": GEOMETRY_CANONICAL_RANKING_SHA256,
            "D_SH_threshold": DSH_THRESHOLD,
            "minimum_year_orbit_members": MIN_YEAR_ORBIT_MEMBERS,
            "minimum_orbital_corroboration_precision": MIN_ORBITAL_PRECISION,
            "N_power_floor": 100,
            "Q_power_floor": MIN_Q,
            "top_k": TOP_K,
            "native_kepler_order": ["a_m", "e", "i_deg", "omega_deg", "Omega_deg", "nu_deg"],
            "AU_m": AU_M,
            "q_AU": "abs((a_m/AU_m)*(1-e))",
            "no_orbits_in_candidate_or_ranking": True,
            "no_target_information": True,
        },
        "geometry_prerequisite": {
            "verdict": geometry["verdict"],
            "N": n,
            "ranking_sha256": geometry["ranking_sha256_before_any_orbit_access"],
        },
        "orbit_read_audit": orbit_audit,
        "orbital_summary": orbital_summary,
        "metrics": metrics,
        "required_multiplicity_vs_persistence": required_vs_persistence,
        "integrity_gates": integrity_gates,
        "power_gates": {
            "at_least_100_recurrent_families": n >= 100,
            "at_least_30_orbitally_corroborated_families": q_power,
        },
        "scientific_gates": scientific_gates,
        "v8_method_changed": False,
        "external_power_floors_lowered": False,
        "successor_detector_authorized": False,
        "orbittrace_target_information_access": False,
        "final_gmn_stage_a_authorized_by_this_runner": False,
        "claim_boundary": (
            "Post-ranking orbital validation of the immutable N=107 MAARSY 2016/2017 v8 family universe. "
            "Only native kepler rows for already-ranked family events were read. The frozen SAAMER external orbital evaluator and D_SH comparator were reused with only the event-ID parser/year tuple adapted. "
            "No OrbitTrace target information or final GMN Stage A/Stage B data was accessed."
        ),
    }
    (args.output / "v8_maarsy_2016_2017_external_validation.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (args.output / "maarsy_orbital_corroboration.json.gz").write_bytes(gzip.compress(json.dumps(corroboration, separators=(",", ":")).encode("utf-8")))
    (args.output / "V8_MAARSY_2016_2017_EXTERNAL_VALIDATION.md").write_text(
        "# OrbitTrace v8 MAARSY 2016/2017 external validation\n\n"
        f"**Verdict:** `{verdict}`\n\n"
        f"- recurrent families: **N={n}**\n"
        f"- orbitally corroborated families: **Q={q}**\n"
        f"- multiplicity top-{min(TOP_K,n)} corroborated: **{m}**; enrichment p: **{metrics['multiplicity']['hypergeometric_enrichment_p']:.6g}**\n"
        f"- Brown top-{min(TOP_K,n)} corroborated: **{b}**\n"
        f"- persistence top-{min(TOP_K,n)} corroborated: **{persistence}**\n"
        f"- required multiplicity count vs persistence: **{required_vs_persistence}**\n\n"
        "All family discovery and ranking was immutable before orbit access. No OrbitTrace target information was accessed.\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
