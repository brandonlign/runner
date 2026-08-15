#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from orbittrace_recurrent_eom_hdbscan_v1.run_development import annual_gate, metrics

YEARS = (2023, 2024)
BLIND = (20.0, 55.0)
LABEL_HEADER = ["event_id", "shower_association"]
SELECTED_FINAL_METHOD = "density_synchronous_recurrent_eom_hdbscan_v1_pr1263"
SCIENTIFIC_ROLE = "PRISTINE_FINAL_EXTERNAL_AMOS_2023_2024_TEST_ONLY"
PRIMARY_PASS = "PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_AMOS_2023_2024_FINAL_EXTERNAL_VALIDATION"
PRIMARY_FAIL = "FAIL_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_AMOS_2023_2024_FINAL_EXTERNAL_VALIDATION"
INCREMENT_PASS = "PASS_DENSITY_SYNCHRONY_INCREMENT_OVER_RECURRENT_EOM_AMOS"
INCREMENT_NO = "NO_DEMONSTRATED_DENSITY_SYNCHRONY_INCREMENT_OVER_RECURRENT_EOM_AMOS"
MIN_CLUSTER_SIZE = 10

EXPECTED_HDBSCAN = {
    "representation": "GEO6",
    "min_cluster_size": 10,
    "min_samples": 10,
    "metric": "euclidean",
    "cluster_selection_method": "eom",
    "cluster_selection_epsilon": 0.0,
    "allow_single_cluster": False,
    "prediction_data": False,
}

EXPECTED_SOURCE_PINS = {
    "recurrent_eom_git_blob": "30ac3fa3bc47910370df528fcf3ae8ecb6277b47",
    "recurrent_development_runner_git_blob": "fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c",
    "density_sync_git_blob": "587a304f451e41b9503272f1783a6c6ebb295000",
    "density_sync_development_runner_git_blob": "157813ca331165180a6d20aa71bfc78d5984396f",
    "amos_adapter_transform_git_blob": "612ad23af6e11ac2155282258e3d1429fbe00d67",
    "amos_adapter_git_blob": "9a0fb05f94d6a28cd95f97d864e76400056273b0",
    "amos_blind_receipt_git_blob": "9fed803aa09f03f779610eaff5304251bbf21020",
    "final_protocol_git_blob": "1ddb4bae33a1ae8a6224cbc4abcba5dda70cf993",
}

EXPECTED_PRETRUTH_KEYS = {
    "scientific_role",
    "phase",
    "selected_final_method",
    "years",
    "blind_exclusion",
    "events_total",
    "events_by_year",
    "event_ids_by_year",
    "canonical_input_sha256",
    "geo6_sha256",
    "condensed_tree_sha256",
    "condensed_tree_rows",
    "ordinary_stability_sha256",
    "recurrent_annual_eom_sha256",
    "recurrent_quality_sha256",
    "density_sync_parent_annual_sha256",
    "density_sync_reconstructed_annual_sha256",
    "density_sync_annual_reconstruction_max_abs_error",
    "density_sync_quality_sha256",
    "recurrent_annual_eom",
    "density_sync_reconstructed_annual_eom",
    "ordinary_selected_nodes",
    "recurrent_selected_nodes",
    "density_sync_selected_nodes",
    "ordinary_candidates",
    "recurrent_candidates",
    "density_sync_candidates",
    "ordinary_order_sha256",
    "recurrent_order_sha256",
    "density_sync_order_sha256",
    "ordinary_membership_sha256",
    "recurrent_membership_sha256",
    "density_sync_membership_sha256",
    "mechanism_active",
    "frozen_hdbscan",
    "source_pins",
    "labels_accessed",
    "amos_shower_associations_accessed",
    "amos_orbit_elements_accessed",
    "sonotaco_access",
    "asfn_access",
    "efn_access",
    "target_information_access",
    "target_region_events_accessed",
    "maarsy_scientific_access",
    "dms_scientific_access",
    "orbittrace_target_access",
    "amos_post_result_parameter_search",
}

CANDIDATE_SCHEMAS = {
    "ordinary": {
        "family_id", "node_id", "event_ids", "member_count", "ordinary_stability"
    },
    "recurrent": {
        "family_id", "node_id", "event_ids", "member_count", "ordinary_stability", "recurrent_stability"
    },
    "density_sync": {
        "family_id", "node_id", "event_ids", "member_count", "ordinary_stability", "synchronous_stability"
    },
}

FAMILY_PREFIX = {
    "ordinary": "HDBEOM",
    "recurrent": "REOM1",
    "density_sync": "DSEOM1",
}

NO_ASSOCIATION_ALIASES = {
    "NONE",
    "NULL",
    "NA",
    "N/A",
    "UNKNOWN",
    "UNASSIGNED",
    "NO_SHOWER",
    "NO SHOWER",
    "0",
    "-",
}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def member_hash(prefix: str, members: list[str]) -> str:
    return hashlib.sha256((prefix + "|" + "|".join(members)).encode()).hexdigest()[:20]


def order_sha(candidates: list[dict[str, Any]]) -> str:
    return hashlib.sha256("\n".join(str(x["family_id"]) for x in candidates).encode()).hexdigest()


def membership_sha(candidates: list[dict[str, Any]]) -> str:
    rows = ["|".join(map(str, row["event_ids"])) for row in candidates]
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()


def mapping_sha(mapping: dict[Any, Any]) -> str:
    payload = {str(k): v for k, v in sorted(mapping.items(), key=lambda kv: int(kv[0]))}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def require_sha256_text(value: Any, name: str) -> str:
    text = str(value)
    require(len(text) == 64 and all(c in "0123456789abcdef" for c in text), f"invalid SHA-256 field {name}")
    return text


def expected_sort_key(name: str, row: dict[str, Any]) -> tuple[Any, ...]:
    if name == "ordinary":
        return (
            -float(row["ordinary_stability"]),
            -int(row["member_count"]),
            str(row["family_id"]),
        )
    if name == "recurrent":
        return (
            -float(row["recurrent_stability"]),
            -float(row["ordinary_stability"]),
            -int(row["member_count"]),
            str(row["family_id"]),
        )
    if name == "density_sync":
        return (
            -float(row["synchronous_stability"]),
            -float(row["ordinary_stability"]),
            -int(row["member_count"]),
            str(row["family_id"]),
        )
    raise RuntimeError(f"unknown candidate method {name}")


def validate_candidate_order(
    name: str,
    candidates_raw: Any,
    selected_nodes_raw: Any,
    expected_order_sha: Any,
    expected_membership_sha: Any,
    pooled_ids: set[str],
) -> list[dict[str, Any]]:
    require(isinstance(candidates_raw, list), f"{name} candidate payload is not a list")
    require(isinstance(selected_nodes_raw, list), f"{name} selected-node list missing/non-list")
    selected_nodes = [int(x) for x in selected_nodes_raw]
    require(len(selected_nodes) == len(set(selected_nodes)), f"{name} selected-node list contains duplicates")
    require(len(selected_nodes) == len(candidates_raw), f"{name} selected-node/candidate count mismatch")

    out: list[dict[str, Any]] = []
    family_ids: set[str] = set()
    candidate_nodes: set[int] = set()
    assigned_events: set[str] = set()
    schema = CANDIDATE_SCHEMAS[name]
    prefix = FAMILY_PREFIX[name]

    for i, raw in enumerate(candidates_raw):
        require(isinstance(raw, dict), f"{name} candidate {i} is not an object")
        require(set(raw) == schema, f"{name} candidate {i} has unexpected schema")
        family_id = str(raw["family_id"])
        require(family_id and family_id not in family_ids, f"{name} duplicate/blank family ID: {family_id!r}")
        family_ids.add(family_id)

        node = int(raw["node_id"])
        require(node not in candidate_nodes, f"{name} duplicate candidate node {node}")
        candidate_nodes.add(node)

        ids = [str(x) for x in raw["event_ids"]]
        require(ids and ids == sorted(ids), f"{name} candidate {family_id} member IDs not deterministic sorted order")
        require(len(ids) == len(set(ids)), f"{name} candidate {family_id} contains duplicate event IDs")
        require(int(raw["member_count"]) == len(ids), f"{name} candidate {family_id} member_count mismatch")
        require(len(ids) >= MIN_CLUSTER_SIZE, f"{name} candidate {family_id} below frozen minimum cluster size")
        require(family_id == member_hash(prefix, ids), f"{name} candidate deterministic family ID mismatch")

        unknown = set(ids) - pooled_ids
        require(not unknown, f"{name} candidate {family_id} contains non-retained event IDs: {sorted(unknown)[:3]}")
        overlap = assigned_events.intersection(ids)
        require(not overlap, f"{name} flat candidate memberships overlap: {sorted(overlap)[:3]}")
        assigned_events.update(ids)

        for score_key in schema.intersection({"ordinary_stability", "recurrent_stability", "synchronous_stability"}):
            require(math.isfinite(float(raw[score_key])), f"{name} candidate {family_id} non-finite {score_key}")
        out.append(dict(raw))

    require(candidate_nodes == set(selected_nodes), f"{name} candidate node universe differs from selected-node tuple")
    expected_order = require_sha256_text(expected_order_sha, f"{name}_order_sha256")
    expected_membership = require_sha256_text(expected_membership_sha, f"{name}_membership_sha256")
    require(order_sha(out) == expected_order, f"{name} candidate order hash mismatch")
    require(membership_sha(out) == expected_membership, f"{name} candidate membership hash mismatch")

    expected_sorted = sorted(out, key=lambda row: expected_sort_key(name, row))
    require(
        [str(x["family_id"]) for x in out] == [str(x["family_id"]) for x in expected_sorted],
        f"{name} candidate order inconsistent with frozen score/tie sort",
    )
    return out


def validate_pretruth(pre: dict[str, Any]) -> tuple[dict[int, list[str]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    require(isinstance(pre, dict) and set(pre) == EXPECTED_PRETRUTH_KEYS, "unexpected top-level pretruth schema")
    require(pre["scientific_role"] == SCIENTIFIC_ROLE and pre["phase"] == "PRETRUTH_FROZEN", "wrong pretruth role/phase")
    require(pre["selected_final_method"] == SELECTED_FINAL_METHOD, "selected final method changed")
    require(pre["years"] == [2023, 2024] and pre["blind_exclusion"] == [20.0, 55.0], "year/blind freeze changed")
    require(pre["frozen_hdbscan"] == EXPECTED_HDBSCAN, "frozen HDBSCAN declaration changed")
    require(pre["source_pins"] == EXPECTED_SOURCE_PINS, "pretruth scientific/transport source pins changed")
    require(pre["labels_accessed"] is False and pre["amos_shower_associations_accessed"] is False, "pretruth payload is truth-bearing")
    require(pre["amos_orbit_elements_accessed"] is False, "pretruth payload opened orbit elements")
    for k in ("sonotaco_access", "asfn_access", "efn_access", "target_information_access", "target_region_events_accessed", "maarsy_scientific_access", "dms_scientific_access", "orbittrace_target_access", "amos_post_result_parameter_search"):
        require(pre[k] is False, f"firewall flag violated in pretruth: {k}")

    require(isinstance(pre["events_by_year"], dict) and set(pre["events_by_year"]) == {"2023", "2024"}, "events_by_year schema changed")
    require(isinstance(pre["event_ids_by_year"], dict) and set(pre["event_ids_by_year"]) == {"2023", "2024"}, "event_ids_by_year schema changed")
    require(isinstance(pre["canonical_input_sha256"], dict) and set(pre["canonical_input_sha256"]) == {"2023", "2024"}, "canonical input hash schema changed")
    for year in ("2023", "2024"):
        require_sha256_text(pre["canonical_input_sha256"][year], f"canonical_input_sha256[{year}]")

    ids_by_year: dict[int, list[str]] = {}
    pooled_ids: set[str] = set()
    for y in YEARS:
        ids = [str(x) for x in pre["event_ids_by_year"][str(y)]]
        require(ids and ids == sorted(ids), f"retained event IDs for {y} are empty or not deterministic sorted order")
        require(len(ids) == len(set(ids)), f"duplicate retained event ID within {y}")
        require(int(pre["events_by_year"][str(y)]) == len(ids), f"events_by_year count mismatch for {y}")
        overlap = pooled_ids.intersection(ids)
        require(not overlap, f"event ID reused across AMOS years: {sorted(overlap)[:3]}")
        pooled_ids.update(ids)
        ids_by_year[y] = ids
    require(int(pre["events_total"]) == len(pooled_ids), "events_total does not match retained-ID universe")
    require(int(pre["condensed_tree_rows"]) >= 0, "invalid condensed-tree row count")

    for k in ("geo6_sha256", "condensed_tree_sha256", "ordinary_stability_sha256", "recurrent_annual_eom_sha256", "recurrent_quality_sha256", "density_sync_parent_annual_sha256", "density_sync_reconstructed_annual_sha256", "density_sync_quality_sha256"):
        require_sha256_text(pre[k], k)
    require(pre["recurrent_annual_eom_sha256"] == pre["density_sync_parent_annual_sha256"], "density-sync parent annual hash differs from recurrent annual hash")

    recurrent_annual = pre["recurrent_annual_eom"]
    reconstructed = pre["density_sync_reconstructed_annual_eom"]
    require(isinstance(recurrent_annual, dict) and isinstance(reconstructed, dict), "annual EOM maps missing/non-object")
    require(set(recurrent_annual) == set(reconstructed), "annual EOM node universes differ")
    require(mapping_sha(recurrent_annual) == pre["recurrent_annual_eom_sha256"], "stored recurrent annual EOM hash mismatch")
    require(mapping_sha(reconstructed) == pre["density_sync_reconstructed_annual_sha256"], "stored reconstructed annual EOM hash mismatch")
    reconstruction_max = 0.0
    for node in recurrent_annual:
        expected = [float(x) for x in recurrent_annual[node]]
        got = [float(x) for x in reconstructed[node]]
        require(len(expected) == len(got) == 2, f"annual EOM pair shape changed at node {node}")
        for aa, bb in zip(expected, got):
            require(math.isfinite(aa) and math.isfinite(bb), f"non-finite annual EOM at node {node}")
            require(math.isclose(aa, bb, rel_tol=1e-12, abs_tol=1e-12), f"annual EOM reconstruction mismatch at node {node}")
            reconstruction_max = max(reconstruction_max, abs(aa - bb))
    require(reconstruction_max <= 1e-12, "annual EOM reconstruction exceeds frozen tolerance")
    require(math.isfinite(float(pre["density_sync_annual_reconstruction_max_abs_error"])), "stored reconstruction maximum is non-finite")
    require(math.isclose(float(pre["density_sync_annual_reconstruction_max_abs_error"]), reconstruction_max, rel_tol=1e-12, abs_tol=1e-15), "stored reconstruction maximum mismatch")

    ordinary_candidates = validate_candidate_order(
        "ordinary",
        pre["ordinary_candidates"],
        pre["ordinary_selected_nodes"],
        pre["ordinary_order_sha256"],
        pre["ordinary_membership_sha256"],
        pooled_ids,
    )
    recurrent_candidates = validate_candidate_order(
        "recurrent",
        pre["recurrent_candidates"],
        pre["recurrent_selected_nodes"],
        pre["recurrent_order_sha256"],
        pre["recurrent_membership_sha256"],
        pooled_ids,
    )
    sync_candidates = validate_candidate_order(
        "density_sync",
        pre["density_sync_candidates"],
        pre["density_sync_selected_nodes"],
        pre["density_sync_order_sha256"],
        pre["density_sync_membership_sha256"],
        pooled_ids,
    )

    mechanism_expected = {
        "ordinary_vs_recurrent": bool(pre["ordinary_selected_nodes"] != pre["recurrent_selected_nodes"] or pre["ordinary_order_sha256"] != pre["recurrent_order_sha256"]),
        "recurrent_vs_density_sync": bool(pre["recurrent_selected_nodes"] != pre["density_sync_selected_nodes"] or pre["recurrent_order_sha256"] != pre["density_sync_order_sha256"]),
        "ordinary_vs_density_sync": bool(pre["ordinary_selected_nodes"] != pre["density_sync_selected_nodes"] or pre["ordinary_order_sha256"] != pre["density_sync_order_sha256"]),
    }
    require(isinstance(pre["mechanism_active"], dict) and set(pre["mechanism_active"]) == set(mechanism_expected), "mechanism-active schema changed")
    require(pre["mechanism_active"] == mechanism_expected, "stored mechanism-active flags do not match selected nodes/orders")

    return ids_by_year, ordinary_candidates, recurrent_candidates, sync_candidates


def validate_association_label(label: str, eid: str) -> str:
    require(label, f"blank shower association for retained AMOS event {eid}; use explicit SPORADIC")
    upper = label.upper()
    if upper == "SPORADIC":
        require(label == "SPORADIC", f"noncanonical SPORADIC sentinel for retained AMOS event {eid}")
        return label
    require(upper not in NO_ASSOCIATION_ALIASES, f"ambiguous no-association sentinel for retained AMOS event {eid}: {label!r}; use explicit SPORADIC")
    return label


def load_labels(path: Path, expected_ids: list[str], year: int) -> dict[str, str]:
    expected = set(map(str, expected_ids))
    out: dict[str, str] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        require(r.fieldnames == LABEL_HEADER, f"wrong AMOS label header for {year}")
        for row in r:
            eid = str(row["event_id"]).strip()
            raw_label = str(row["shower_association"])
            label = raw_label.strip()
            require(raw_label == label, f"association label contains surrounding whitespace for retained AMOS event {eid}")
            require(eid and eid in expected and eid not in out, f"invalid/duplicate AMOS label ID for {year}: {eid!r}")
            out[eid] = validate_association_label(label, eid)
    require(set(out) == expected, f"AMOS label map for {year} must cover every retained ID exactly")
    return out


def public_metrics(m: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in m.items() if k != "first_rank_by_label"}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--pretruth", type=Path, required=True)
    p.add_argument("--pretruth-sha256", type=str, required=True)
    p.add_argument("--labels-2023", type=Path, required=True)
    p.add_argument("--labels-2024", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    actual_pretruth_sha = sha(a.pretruth)
    require(actual_pretruth_sha == a.pretruth_sha256.strip().lower(), "pretruth payload hash changed before label evaluation")
    pre = json.loads(a.pretruth.read_text(encoding="utf-8"))

    # All pretruth structural/source/hierarchy/order invariants are verified before
    # either label file is opened. This is a fail-closed trust-boundary check only;
    # it does not recompute geometry, hierarchy, candidates, ranks, or scientific metrics.
    ids_by_year, ordinary_candidates, recurrent_candidates, sync_candidates = validate_pretruth(pre)

    labels_by_year = {
        2023: load_labels(a.labels_2023, ids_by_year[2023], 2023),
        2024: load_labels(a.labels_2024, ids_by_year[2024], 2024),
    }
    hidden: dict[str, str] = {}
    for y in YEARS:
        require(set(hidden).isdisjoint(labels_by_year[y]), "event ID reused across AMOS label years")
        hidden.update(labels_by_year[y])

    ordinary_metrics = {str(y): metrics(ordinary_candidates, hidden, set(ids_by_year[y])) for y in YEARS}
    recurrent_metrics = {str(y): metrics(recurrent_candidates, hidden, set(ids_by_year[y])) for y in YEARS}
    sync_metrics = {str(y): metrics(sync_candidates, hidden, set(ids_by_year[y])) for y in YEARS}

    ordinary_gates = {str(y): annual_gate(ordinary_metrics[str(y)], sync_metrics[str(y)]) for y in YEARS}
    recurrent_gates = {str(y): annual_gate(recurrent_metrics[str(y)], sync_metrics[str(y)]) for y in YEARS}
    strict_vs_ordinary_100 = any(int(sync_metrics[str(y)]["recovered_at_100"]) > int(ordinary_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    strict_vs_recurrent_100 = any(int(sync_metrics[str(y)]["recovered_at_100"]) > int(recurrent_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    active_vs_ordinary = bool(pre["mechanism_active"]["ordinary_vs_density_sync"])
    active_vs_recurrent = bool(pre["mechanism_active"]["recurrent_vs_density_sync"])

    primary_pass = bool(
        strict_vs_ordinary_100
        and active_vs_ordinary
        and all(all(g.values()) for g in ordinary_gates.values())
        and all(all(g.values()) for g in recurrent_gates.values())
    )
    primary_verdict = PRIMARY_PASS if primary_pass else PRIMARY_FAIL

    incremental_pass = bool(
        strict_vs_recurrent_100
        and active_vs_recurrent
        and all(all(g.values()) for g in recurrent_gates.values())
    )
    incremental_verdict = INCREMENT_PASS if incremental_pass else INCREMENT_NO

    result: dict[str, Any] = {
        "verdict": primary_verdict,
        "incremental_density_synchrony_verdict": incremental_verdict,
        "scientific_role": SCIENTIFIC_ROLE,
        "phase": "POSTFREEZE_LABEL_EVALUATION",
        "selected_final_method": SELECTED_FINAL_METHOD,
        "pretruth_sha256": actual_pretruth_sha,
        "pretruth_internal_integrity_verified_before_labels": True,
        "years": [2023, 2024],
        "events_by_year": dict(pre["events_by_year"]),
        "label_file_sha256": {"2023": sha(a.labels_2023), "2024": sha(a.labels_2024)},
        "candidate_counts": {
            "ordinary": len(ordinary_candidates),
            "recurrent": len(recurrent_candidates),
            "density_sync": len(sync_candidates),
        },
        "mechanism_active": dict(pre["mechanism_active"]),
        "strict_recovered_at_100_improvement_vs_ordinary_some_year": strict_vs_ordinary_100,
        "strict_recovered_at_100_improvement_vs_recurrent_some_year": strict_vs_recurrent_100,
        "ordinary_metrics": ordinary_metrics,
        "recurrent_metrics": recurrent_metrics,
        "density_sync_metrics": sync_metrics,
        "density_sync_vs_ordinary_annual_gates": ordinary_gates,
        "density_sync_vs_recurrent_annual_gates": recurrent_gates,
        "frozen_hdbscan": dict(pre["frozen_hdbscan"]),
        "source_pins": dict(pre["source_pins"]),
        "blind_exclusion": list(BLIND),
        "candidate_generation_recomputed_after_labels": False,
        "ranking_changed_after_labels": False,
        "final_method_switched_after_labels": False,
        "quality_filter_used": False,
        "survey_calibration_used": False,
        "amos_post_result_parameter_search": False,
        "replacement_external_panel_authorized": False,
        "sonotaco_access": False,
        "asfn_access": False,
        "efn_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "orbittrace_target_access": False,
    }
    out = a.output / "FINAL_DENSITY_SYNC_AMOS_2023_2024_EXTERNAL_RESULT.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": primary_verdict,
        "incremental": incremental_verdict,
        "ordinary": {y: public_metrics(ordinary_metrics[y]) for y in ordinary_metrics},
        "recurrent": {y: public_metrics(recurrent_metrics[y]) for y in recurrent_metrics},
        "density_sync": {y: public_metrics(sync_metrics[y]) for y in sync_metrics},
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
