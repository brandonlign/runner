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

from recurrent_eom import eom_labels, recurrent_stability, selected_eom_nodes
from orbittrace_recurrent_eom_hdbscan_v1.run_development import (
    MIN_CLUSTER_SIZE,
    MIN_SAMPLES,
    candidates_from_labels,
    canonical_partition,
    geo_matrix,
)

YEARS = (2023, 2024)
BLIND = (20.0, 55.0)
EXPECTED_KEYS = {"id", "year", "sol", "sun_lon", "ecl_lat", "vg", "iau", "complex_key"}
METHOD_BLOB = "30ac3fa3bc47910370df528fcf3ae8ecb6277b47"
DEVELOPMENT_RUNNER_BLOB = "fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c"
ADAPTER_TRANSFORM_BLOB = "612ad23af6e11ac2155282258e3d1429fbe00d67"
ADAPTER_BLOB = "9a0fb05f94d6a28cd95f97d864e76400056273b0"
PROTOCOL_BLOB = "6cc45ef9e0b7b7cf1bf71f22361b64d537977f4f"


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


def order_sha(candidates: list[dict[str, Any]]) -> str:
    return hashlib.sha256("\n".join(str(x["family_id"]) for x in candidates).encode()).hexdigest()


def load_canonical(path: Path, year: int) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(raw, list) and raw, f"empty/non-list canonical input for {year}")
    out: list[dict[str, Any]] = []
    ids: list[str] = []
    for row in raw:
        require(isinstance(row, dict) and set(row) == EXPECTED_KEYS, f"unexpected canonical schema for {year}")
        eid = str(row["id"])
        require(eid and eid not in ids, f"blank/duplicate ID in {year}: {eid!r}")
        require(int(row["year"]) == year, f"wrong canonical year for {eid}")
        require(int(row["iau"]) == 0 and str(row["complex_key"]) == "HIDDEN", f"label state exposed before pretruth for {eid}")
        sol = float(row["sol"])
        lon = float(row["sun_lon"])
        lat = float(row["ecl_lat"])
        vg = float(row["vg"])
        require(all(math.isfinite(v) for v in (sol, lon, lat, vg)), f"nonfinite canonical geometry for {eid}")
        require(0.0 <= sol < 360.0 and -180.0 <= lon < 180.0 and -90.0 <= lat <= 90.0 and vg > 0.0, f"invalid canonical geometry for {eid}")
        require(not (BLIND[0] <= sol <= BLIND[1]), f"protected AMOS event reached recurrent-EOM: {eid}")
        ids.append(eid)
        out.append({"id": eid, "year": year, "sol": sol, "lon": lon, "lat": lat, "vg": vg})
    require(ids == sorted(ids), f"canonical adapter output for {year} is not deterministic ID order")
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

    parent_model = hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(X)
    tree = parent_model.condensed_tree_._raw_tree
    ordinary = compute_stability(tree)
    parent_labels = eom_labels(tree, ordinary)
    require(canonical_partition(parent_model.labels_) == canonical_partition(parent_labels), "custom parent extraction diverged from vanilla HDBSCAN")
    parent_nodes = selected_eom_nodes(tree, ordinary)
    require(len(parent_nodes) == len(set(int(x) for x in parent_labels if int(x) >= 0)), "parent selected-node/label mismatch")

    recurrent, annual_stability = recurrent_stability(tree, years)
    successor_labels = eom_labels(tree, recurrent)
    successor_nodes = selected_eom_nodes(tree, recurrent)
    require(len(successor_nodes) == len(set(int(x) for x in successor_labels if int(x) >= 0)), "successor selected-node/label mismatch")

    parent_candidates = candidates_from_labels(parent_labels, parent_nodes, events, ordinary, None, False)
    successor_candidates = candidates_from_labels(successor_labels, successor_nodes, events, ordinary, recurrent, True)

    payload = {
        "scientific_role": "PRISTINE_EXTERNAL_AMOS_2023_2024_VALIDATION_PRETRUTH",
        "years": list(YEARS),
        "blind_exclusion": list(BLIND),
        "events_total": len(events),
        "events_by_year": {str(y): len(by_year[y]) for y in YEARS},
        "event_ids_by_year": {str(y): [str(e["id"]) for e in by_year[y]] for y in YEARS},
        "canonical_input_sha256": {"2023": file_sha(a.canonical_2023), "2024": file_sha(a.canonical_2024)},
        "geo6_sha256": ndarray_sha(X),
        "condensed_tree_sha256": ndarray_sha(tree),
        "condensed_tree_rows": int(len(tree)),
        "parent_selected_nodes": list(parent_nodes),
        "successor_selected_nodes": list(successor_nodes),
        "mechanism_active": bool(parent_nodes != successor_nodes),
        "parent_candidates": parent_candidates,
        "successor_candidates": successor_candidates,
        "parent_order_sha256": order_sha(parent_candidates),
        "successor_order_sha256": order_sha(successor_candidates),
        "annual_recurrent_stability": {str(k): list(v) for k, v in sorted(annual_stability.items())},
        "frozen_hdbscan": {
            "representation": "GEO6",
            "min_cluster_size": MIN_CLUSTER_SIZE,
            "min_samples": MIN_SAMPLES,
            "metric": "euclidean",
            "cluster_selection_method": "eom",
            "cluster_selection_epsilon": 0.0,
            "allow_single_cluster": False,
        },
        "source_pins": {
            "recurrent_eom_git_blob": METHOD_BLOB,
            "development_runner_git_blob": DEVELOPMENT_RUNNER_BLOB,
            "adapter_transform_git_blob": ADAPTER_TRANSFORM_BLOB,
            "adapter_git_blob": ADAPTER_BLOB,
            "protocol_git_blob": PROTOCOL_BLOB,
        },
        "labels_accessed": False,
        "amos_shower_associations_accessed": False,
        "amos_orbit_elements_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "orbittrace_target_access": False,
    }
    out = a.output / "RECURRENT_EOM_AMOS_2023_2024_PRETRUTH.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    digest = file_sha(out)
    (a.output / "PRETRUTH_SHA256.txt").write_text(digest + "\n", encoding="ascii")
    print(json.dumps({"verdict": "PASS_RECURRENT_EOM_AMOS_PRETRUTH_FREEZE", "pretruth_sha256": digest, "events": payload["events_by_year"], "parent_candidates": len(parent_candidates), "successor_candidates": len(successor_candidates), "mechanism_active": payload["mechanism_active"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
