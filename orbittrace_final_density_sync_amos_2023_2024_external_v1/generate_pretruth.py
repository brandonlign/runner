#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability

from orbittrace_recurrent_eom_hdbscan_v1.recurrent_eom import (
    eom_labels,
    recurrent_stability,
    selected_eom_nodes,
)
from orbittrace_density_synchronous_recurrent_eom_v1.density_synchronous_eom import (
    density_synchronous_stability,
)
from orbittrace_recurrent_eom_hdbscan_v1.run_development import (
    MIN_CLUSTER_SIZE,
    MIN_SAMPLES,
    candidates_from_labels,
    canonical_partition,
    geo_matrix,
    member_hash,
)

YEARS = (2023, 2024)
BLIND = (20.0, 55.0)
CANONICAL_KEYS = {"id", "year", "sol", "sun_lon", "ecl_lat", "vg", "iau", "complex_key"}
SELECTED_FINAL_METHOD = "density_synchronous_recurrent_eom_hdbscan_v1_pr1263"
SCIENTIFIC_ROLE = "PRISTINE_FINAL_EXTERNAL_AMOS_2023_2024_TEST_ONLY"

RECURRENT_KERNEL_BLOB = "30ac3fa3bc47910370df528fcf3ae8ecb6277b47"
RECURRENT_RUNNER_BLOB = "fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c"
DENSITY_SYNC_KERNEL_BLOB = "587a304f451e41b9503272f1783a6c6ebb295000"
DENSITY_SYNC_RUNNER_BLOB = "157813ca331165180a6d20aa71bfc78d5984396f"
AMOS_ADAPTER_TRANSFORM_BLOB = "612ad23af6e11ac2155282258e3d1429fbe00d67"
AMOS_ADAPTER_BLOB = "9a0fb05f94d6a28cd95f97d864e76400056273b0"
AMOS_BLIND_RECEIPT_BLOB = "9fed803aa09f03f779610eaff5304251bbf21020"
FINAL_PROTOCOL_BLOB = "1ddb4bae33a1ae8a6224cbc4abcba5dda70cf993"


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ndarray_sha(a: np.ndarray) -> str:
    x = np.ascontiguousarray(a)
    h = hashlib.sha256()
    h.update(json.dumps(x.dtype.descr if x.dtype.names else x.dtype.str, sort_keys=True, separators=(",", ":")).encode())
    h.update(json.dumps(list(x.shape), separators=(",", ":")).encode())
    h.update(x.tobytes(order="C"))
    return h.hexdigest()


def mapping_sha(mapping: dict[Any, Any]) -> str:
    payload = {str(k): v for k, v in sorted(mapping.items(), key=lambda kv: int(kv[0]))}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def order_sha(candidates: list[dict[str, Any]]) -> str:
    return hashlib.sha256("\n".join(str(x["family_id"]) for x in candidates).encode()).hexdigest()


def membership_sha(candidates: list[dict[str, Any]]) -> str:
    rows = ["|".join(map(str, row["event_ids"])) for row in candidates]
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()


def load_canonical(path: Path, year: int) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(raw, list) and raw, f"empty/non-list canonical input for {year}")
    out: list[dict[str, Any]] = []
    ids: list[str] = []
    seen: set[str] = set()
    for row in raw:
        require(isinstance(row, dict) and set(row) == CANONICAL_KEYS, f"unexpected canonical schema for {year}")
        eid = str(row["id"])
        require(eid and eid not in seen, f"blank/duplicate ID in {year}: {eid!r}")
        seen.add(eid)
        require(int(row["year"]) == year, f"wrong canonical year for {eid}")
        require(int(row["iau"]) == 0 and str(row["complex_key"]) == "HIDDEN", f"truth-bearing canonical state exposed for {eid}")
        sol = float(row["sol"])
        lon = float(row["sun_lon"])
        lat = float(row["ecl_lat"])
        vg = float(row["vg"])
        require(all(math.isfinite(v) for v in (sol, lon, lat, vg)), f"nonfinite canonical geometry for {eid}")
        require(0.0 <= sol < 360.0 and -180.0 <= lon < 180.0 and -90.0 <= lat <= 90.0 and vg > 0.0, f"invalid canonical geometry for {eid}")
        require(not (BLIND[0] <= sol <= BLIND[1]), f"protected AMOS event reached final method: {eid}")
        ids.append(eid)
        out.append({"id": eid, "year": year, "sol": sol, "lon": lon, "lat": lat, "vg": vg})
    require(ids == sorted(ids), f"canonical adapter output for {year} is not deterministic ID order")
    return out


def sync_candidates_from_labels(
    labels: np.ndarray,
    selected_nodes: tuple[int, ...],
    events: list[dict[str, Any]],
    ordinary: dict[float, float],
    synchronous: dict[float, float],
) -> list[dict[str, Any]]:
    positive_labels = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    require(positive_labels == list(range(len(selected_nodes))), "density-sync compact labels no longer map contiguously to selected nodes")
    out: list[dict[str, Any]] = []
    for lab, node in enumerate(selected_nodes):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(str(events[int(i)]["id"]) for i in idx))
        require(len(members) >= MIN_CLUSTER_SIZE, f"density-sync selected cluster below frozen minimum: node={node}")
        out.append({
            "family_id": member_hash("DSEOM1", members),
            "node_id": int(node),
            "event_ids": list(members),
            "member_count": len(members),
            "synchronous_stability": float(synchronous[float(node)]),
            "ordinary_stability": float(ordinary[float(node)]),
        })
    out.sort(key=lambda f: (
        -f["synchronous_stability"],
        -f["ordinary_stability"],
        -f["member_count"],
        f["family_id"],
    ))
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--canonical-2023", type=Path, required=True)
    p.add_argument("--canonical-2024", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    by_year = {
        2023: load_canonical(a.canonical_2023, 2023),
        2024: load_canonical(a.canonical_2024, 2024),
    }
    events = by_year[2023] + by_year[2024]
    ids = [str(e["id"]) for e in events]
    require(len(ids) == len(set(ids)), "event ID reused across AMOS years")
    require(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected interval survived canonical load")

    X = geo_matrix(events)
    years = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    require(tuple(sorted(int(y) for y in np.unique(years))) == YEARS, "exact AMOS year pair changed")

    model = hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(X)
    tree = model.condensed_tree_._raw_tree
    tree_digest_before = ndarray_sha(tree)
    ordinary = compute_stability(tree)

    ordinary_labels = eom_labels(tree, ordinary)
    require(canonical_partition(model.labels_) == canonical_partition(ordinary_labels), "custom ordinary extraction diverged from vanilla HDBSCAN")
    ordinary_nodes = selected_eom_nodes(tree, ordinary)
    require(len(ordinary_nodes) == len(set(int(x) for x in ordinary_labels if int(x) >= 0)), "ordinary selected-node/label mismatch")
    ordinary_candidates = candidates_from_labels(ordinary_labels, ordinary_nodes, events, ordinary, None, False)

    recurrent, recurrent_annual = recurrent_stability(tree, years)
    require(ndarray_sha(tree) == tree_digest_before, "recurrent-EOM mutated shared condensed tree")
    recurrent_labels = eom_labels(tree, recurrent)
    recurrent_nodes = selected_eom_nodes(tree, recurrent)
    require(len(recurrent_nodes) == len(set(int(x) for x in recurrent_labels if int(x) >= 0)), "recurrent selected-node/label mismatch")
    recurrent_candidates = candidates_from_labels(recurrent_labels, recurrent_nodes, events, ordinary, recurrent, True)

    synchronous, sync_parent_annual, sync_reconstructed_annual = density_synchronous_stability(tree, years)
    require(ndarray_sha(tree) == tree_digest_before, "density-synchronous kernel mutated shared condensed tree")
    require(recurrent_annual == sync_parent_annual, "density-synchronous parent annual EOM differs from exact recurrent-EOM")
    require(set(recurrent_annual) == set(sync_reconstructed_annual), "density-synchronous annual reconstruction node universe changed")
    reconstruction_max_abs_error = 0.0
    for node in recurrent_annual:
        expected = np.asarray(recurrent_annual[node], dtype=float)
        got = np.asarray(sync_reconstructed_annual[node], dtype=float)
        require(bool(np.allclose(got, expected, rtol=1e-12, atol=1e-12)), f"density-synchronous annual reconstruction mismatch at node {node}")
        reconstruction_max_abs_error = max(reconstruction_max_abs_error, float(np.max(np.abs(got - expected))))
    sync_labels = eom_labels(tree, synchronous)
    sync_nodes = selected_eom_nodes(tree, synchronous)
    require(len(sync_nodes) == len(set(int(x) for x in sync_labels if int(x) >= 0)), "density-sync selected-node/label mismatch")
    sync_candidates = sync_candidates_from_labels(sync_labels, sync_nodes, events, ordinary, synchronous)

    ordinary_order = order_sha(ordinary_candidates)
    recurrent_order = order_sha(recurrent_candidates)
    sync_order = order_sha(sync_candidates)
    mechanism = {
        "ordinary_vs_recurrent": bool(ordinary_nodes != recurrent_nodes or ordinary_order != recurrent_order),
        "recurrent_vs_density_sync": bool(recurrent_nodes != sync_nodes or recurrent_order != sync_order),
        "ordinary_vs_density_sync": bool(ordinary_nodes != sync_nodes or ordinary_order != sync_order),
    }

    payload = {
        "scientific_role": SCIENTIFIC_ROLE,
        "phase": "PRETRUTH_FROZEN",
        "selected_final_method": SELECTED_FINAL_METHOD,
        "years": list(YEARS),
        "blind_exclusion": list(BLIND),
        "events_total": len(events),
        "events_by_year": {str(y): len(by_year[y]) for y in YEARS},
        "event_ids_by_year": {str(y): [str(e["id"]) for e in by_year[y]] for y in YEARS},
        "canonical_input_sha256": {"2023": file_sha(a.canonical_2023), "2024": file_sha(a.canonical_2024)},
        "geo6_sha256": ndarray_sha(X),
        "condensed_tree_sha256": tree_digest_before,
        "condensed_tree_rows": int(len(tree)),
        "ordinary_stability_sha256": mapping_sha(ordinary),
        "recurrent_annual_eom_sha256": mapping_sha(recurrent_annual),
        "recurrent_quality_sha256": mapping_sha(recurrent),
        "density_sync_parent_annual_sha256": mapping_sha(sync_parent_annual),
        "density_sync_reconstructed_annual_sha256": mapping_sha(sync_reconstructed_annual),
        "density_sync_annual_reconstruction_max_abs_error": reconstruction_max_abs_error,
        "density_sync_quality_sha256": mapping_sha(synchronous),
        "recurrent_annual_eom": {str(k): list(v) for k, v in sorted(recurrent_annual.items())},
        "density_sync_reconstructed_annual_eom": {str(k): list(v) for k, v in sorted(sync_reconstructed_annual.items())},
        "ordinary_selected_nodes": list(ordinary_nodes),
        "recurrent_selected_nodes": list(recurrent_nodes),
        "density_sync_selected_nodes": list(sync_nodes),
        "ordinary_candidates": ordinary_candidates,
        "recurrent_candidates": recurrent_candidates,
        "density_sync_candidates": sync_candidates,
        "ordinary_order_sha256": ordinary_order,
        "recurrent_order_sha256": recurrent_order,
        "density_sync_order_sha256": sync_order,
        "ordinary_membership_sha256": membership_sha(ordinary_candidates),
        "recurrent_membership_sha256": membership_sha(recurrent_candidates),
        "density_sync_membership_sha256": membership_sha(sync_candidates),
        "mechanism_active": mechanism,
        "frozen_hdbscan": {
            "representation": "GEO6",
            "min_cluster_size": MIN_CLUSTER_SIZE,
            "min_samples": MIN_SAMPLES,
            "metric": "euclidean",
            "cluster_selection_method": "eom",
            "cluster_selection_epsilon": 0.0,
            "allow_single_cluster": False,
            "prediction_data": False,
        },
        "source_pins": {
            "recurrent_eom_git_blob": RECURRENT_KERNEL_BLOB,
            "recurrent_development_runner_git_blob": RECURRENT_RUNNER_BLOB,
            "density_sync_git_blob": DENSITY_SYNC_KERNEL_BLOB,
            "density_sync_development_runner_git_blob": DENSITY_SYNC_RUNNER_BLOB,
            "amos_adapter_transform_git_blob": AMOS_ADAPTER_TRANSFORM_BLOB,
            "amos_adapter_git_blob": AMOS_ADAPTER_BLOB,
            "amos_blind_receipt_git_blob": AMOS_BLIND_RECEIPT_BLOB,
            "final_protocol_git_blob": FINAL_PROTOCOL_BLOB,
        },
        "labels_accessed": False,
        "amos_shower_associations_accessed": False,
        "amos_orbit_elements_accessed": False,
        "sonotaco_access": False,
        "asfn_access": False,
        "efn_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "orbittrace_target_access": False,
        "amos_post_result_parameter_search": False,
    }
    out = a.output / "FINAL_DENSITY_SYNC_AMOS_2023_2024_PRETRUTH.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    digest = file_sha(out)
    (a.output / "PRETRUTH_SHA256.txt").write_text(digest + "\n", encoding="ascii")
    print(json.dumps({
        "verdict": "PASS_FINAL_DENSITY_SYNC_AMOS_PRETRUTH_FREEZE",
        "pretruth_sha256": digest,
        "events": payload["events_by_year"],
        "ordinary_candidates": len(ordinary_candidates),
        "recurrent_candidates": len(recurrent_candidates),
        "density_sync_candidates": len(sync_candidates),
        "mechanism_active": mechanism,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
