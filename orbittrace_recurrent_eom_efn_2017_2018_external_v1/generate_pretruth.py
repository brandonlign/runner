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

from orbittrace_recurrent_eom_hdbscan_v1.recurrent_eom import eom_labels, recurrent_stability, selected_eom_nodes

YEARS = (2017, 2018)
BLIND = (20.0, 55.0)
EXPECTED_COUNTS = {2017: 338, 2018: 444}
GEOMETRY_SHA256 = {
    2017: "7583ae47b78401b52dfd9fe2fa1863580b987c69b3d6c8142445f6f3795e82b2",
    2018: "01491fcecbd6e407a8c7424239210e2f233a22e527c9b74d694d0d2f936f9008",
}
METHOD_BLOB = "30ac3fa3bc47910370df528fcf3ae8ecb6277b47"
PROMOTED_RUNNER_BLOB = "fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c"
PROTOCOL_BLOB = "4bc7870d566dd1cd6056add53b4e19155f98814d"
STAGE2_FREEZE_BLOB = "463d31b738c3c133be000c36ee88e025d1565c5a"
MIN_CLUSTER_SIZE = 10
MIN_SAMPLES = 10
SPEED_SCALE = 72.0


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def stable_json_bytes(obj: Any) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def load_geometry(path: Path, year: int) -> list[dict[str, Any]]:
    require(sha_file(path) == GEOMETRY_SHA256[year], f"binding EFN {year} geometry SHA changed")
    rows = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(rows, list) and len(rows) == EXPECTED_COUNTS[year], f"wrong EFN {year} geometry count")
    expected_keys = {"id", "year", "sol", "sun_lon", "ecl_lat", "vg", "iau", "complex_key"}
    ids: list[str] = []
    out: list[dict[str, Any]] = []
    for row in rows:
        require(isinstance(row, dict) and set(row) == expected_keys, f"EFN {year} geometry schema changed")
        eid = str(row["id"])
        require(eid and int(row["year"]) == year, f"EFN geometry ID/year mismatch: {eid}")
        require(int(row["iau"]) == 0 and str(row["complex_key"]) == "HIDDEN", f"truth-bearing state entered geometry for {eid}")
        sol = float(row["sol"])
        lon = float(row["sun_lon"])
        lat = float(row["ecl_lat"])
        vg = float(row["vg"])
        require(all(math.isfinite(x) for x in (sol, lon, lat, vg)), f"nonfinite EFN geometry for {eid}")
        require(0.0 <= sol < 360.0 and not (BLIND[0] <= sol <= BLIND[1]), f"protected/noncanonical EFN sol for {eid}")
        require(-90.0 <= lat <= 90.0 and vg > 0.0, f"invalid EFN native geometry for {eid}")
        ids.append(eid)
        out.append({"id": eid, "year": year, "sol": sol, "sun_lon": lon, "ecl_lat": lat, "vg": vg})
    require(ids == sorted(ids) and len(ids) == len(set(ids)), f"EFN {year} geometry ID order/uniqueness changed")
    return out


def geo6(events: list[dict[str, Any]]) -> np.ndarray:
    sol = np.radians(np.asarray([e["sol"] for e in events], dtype=float))
    lon = np.radians(np.asarray([e["sun_lon"] for e in events], dtype=float))
    lat = np.radians(np.asarray([e["ecl_lat"] for e in events], dtype=float))
    vg = np.asarray([e["vg"] for e in events], dtype=float)
    X = np.column_stack((
        np.cos(sol),
        np.sin(sol),
        np.sin(lon) * np.cos(lat),
        np.cos(lon) * np.cos(lat),
        np.sin(lat),
        vg / SPEED_SCALE,
    ))
    require(X.shape == (sum(EXPECTED_COUNTS.values()), 6) and np.all(np.isfinite(X)), "invalid EFN GEO6 matrix")
    return X


def canonical_partition(labels: np.ndarray, event_ids: list[str]) -> tuple[tuple[str, ...], ...]:
    groups: list[tuple[str, ...]] = []
    for lab in sorted(int(x) for x in np.unique(labels) if int(x) >= 0):
        members = tuple(sorted(event_ids[int(i)] for i in np.flatnonzero(labels == lab)))
        groups.append(members)
    return tuple(sorted(groups))


def partition_sha(labels: np.ndarray, event_ids: list[str]) -> str:
    payload = [list(group) for group in canonical_partition(labels, event_ids)]
    return sha_bytes(stable_json_bytes(payload))


def member_hash(prefix: str, members: tuple[str, ...]) -> str:
    return hashlib.sha256((prefix + "|" + "|".join(members)).encode("utf-8")).hexdigest()[:20]


def candidates_from_labels(
    labels: np.ndarray,
    selected_nodes: tuple[int, ...],
    events: list[dict[str, Any]],
    ordinary: dict[float, float],
    recurrent: dict[float, float] | None,
    successor: bool,
) -> list[dict[str, Any]]:
    positive_labels = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    require(positive_labels == list(range(len(selected_nodes))), "compact HDBSCAN labels no longer map contiguously to selected nodes")
    out: list[dict[str, Any]] = []
    for lab, node in enumerate(selected_nodes):
        idx = np.flatnonzero(labels == lab)
        members = tuple(sorted(str(events[int(i)]["id"]) for i in idx))
        require(len(members) >= MIN_CLUSTER_SIZE, f"selected cluster below frozen minimum: node={node}")
        row: dict[str, Any] = {
            "family_id": member_hash("REOM1" if successor else "HDBEOM", members),
            "node_id": int(node),
            "event_ids": list(members),
            "member_count": len(members),
            "ordinary_stability": float(ordinary[float(node)]),
        }
        if successor:
            require(recurrent is not None, "missing recurrent stability")
            row["recurrent_stability"] = float(recurrent[float(node)])
        out.append(row)
    if successor:
        out.sort(key=lambda f: (-f["recurrent_stability"], -f["ordinary_stability"], -f["member_count"], f["family_id"]))
    else:
        out.sort(key=lambda f: (-f["ordinary_stability"], -f["member_count"], f["family_id"]))
    return out


def tree_records(tree: np.ndarray) -> list[dict[str, Any]]:
    return [
        {
            "parent": int(row["parent"]),
            "child": int(row["child"]),
            "lambda_val": float(row["lambda_val"]),
            "child_size": int(row["child_size"]),
        }
        for row in tree
    ]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--geometry-2017", type=Path, required=True)
    p.add_argument("--geometry-2018", type=Path, required=True)
    p.add_argument("--stage2-result", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()

    stage2 = json.loads(a.stage2_result.read_text(encoding="utf-8"))
    require(stage2["verdict"] == "PASS_RECURRENT_EOM_EFN_STAGE2_RETAINED_NATIVE_GEOMETRY", "binding Stage-2 result did not pass")
    require(stage2["scientific_role"] == "PRISTINE_EXTERNAL_EFN_2017_2018_STAGE2_RETAINED_GEOMETRY_ONLY", "wrong Stage-2 scientific role")
    require(stage2["catalogue"] == "J/A+A/667/A157" and stage2["years"] == [2017, 2018], "wrong Stage-2 catalogue/years")
    require(stage2["rows_by_year"] == {"2017": 338, "2018": 444}, "Stage-2 retained counts changed")
    require(stage2["canonical_geometry_sha256"] == {str(y): GEOMETRY_SHA256[y] for y in YEARS}, "Stage-2 geometry manifest changed")
    require(stage2["labels_accessed"] is False and stage2["shower_column_returned"] is False and stage2["orbit_fields_returned"] is False, "truth-bearing Stage-2 state")
    require(stage2["target_region_physical_values_accessed"] is False and stage2["target_information_access"] is False, "Stage-2 firewall changed")

    rows17 = load_geometry(a.geometry_2017, 2017)
    rows18 = load_geometry(a.geometry_2018, 2018)
    events = rows17 + rows18
    event_ids = [e["id"] for e in events]
    require(len(event_ids) == 782 and len(set(event_ids)) == 782, "pooled EFN event identity changed")
    years = np.asarray([e["year"] for e in events], dtype=np.int64)
    require(tuple(sorted(int(y) for y in np.unique(years))) == YEARS, "pooled EFN year domain changed")

    X = geo6(events)
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
    ordinary = compute_stability(tree)
    parent_labels = eom_labels(tree, ordinary)
    require(canonical_partition(model.labels_, event_ids) == canonical_partition(parent_labels, event_ids), "custom parent extraction diverged from vanilla HDBSCAN")
    parent_nodes = selected_eom_nodes(tree, ordinary)
    require(len(parent_nodes) == len(set(int(x) for x in parent_labels if int(x) >= 0)), "parent selected-node/label count mismatch")

    recurrent, annual = recurrent_stability(tree, years)
    successor_labels = eom_labels(tree, recurrent)
    successor_nodes = selected_eom_nodes(tree, recurrent)
    require(len(successor_nodes) == len(set(int(x) for x in successor_labels if int(x) >= 0)), "successor selected-node/label count mismatch")

    parent_candidates = candidates_from_labels(parent_labels, parent_nodes, events, ordinary, None, False)
    successor_candidates = candidates_from_labels(successor_labels, successor_nodes, events, ordinary, recurrent, True)

    tree_rows = tree_records(tree)
    tree_identity = {
        "numpy_dtype_descr": [[str(name), str(dtype)] for name, dtype in tree.dtype.descr],
        "shape": list(tree.shape),
        "raw_tree_bytes_sha256": sha_bytes(tree.tobytes(order="C")),
        "records_sha256": sha_bytes(stable_json_bytes(tree_rows)),
        "records": tree_rows,
    }
    event_order = [{"id": e["id"], "year": int(e["year"])} for e in events]
    event_order_sha = sha_bytes(stable_json_bytes(event_order))
    year_vector_sha = sha_bytes(years.astype("<i8", copy=False).tobytes(order="C"))
    geo6_sha = sha_bytes(np.asarray(X, dtype="<f8").tobytes(order="C"))

    ordinary_rows = [
        {"node_id": int(float(k)), "stability": float(v)}
        for k, v in sorted(ordinary.items(), key=lambda kv: float(kv[0]))
    ]
    recurrent_rows = [
        {"node_id": int(float(k)), "recurrent_stability": float(v)}
        for k, v in sorted(recurrent.items(), key=lambda kv: float(kv[0]))
    ]
    annual_rows = [
        {"node_id": int(node), "annual_normalized_stability": {"2017": float(vals[0]), "2018": float(vals[1])}}
        for node, vals in sorted(annual.items())
    ]

    payload = {
        "verdict": "PASS_RECURRENT_EOM_EFN_PRETRUTH_CANDIDATE_FREEZE",
        "scientific_role": "PRISTINE_EXTERNAL_EFN_2017_2018_VALIDATION_ONLY",
        "phase": "PRETRUTH_CANDIDATE_FREEZE_ONLY",
        "catalogue": "J/A+A/667/A157",
        "catalogue_rows_expected": 824,
        "years": [2017, 2018],
        "blind_exclusion": [20.0, 55.0],
        "retained_rows_by_year": {"2017": 338, "2018": 444},
        "canonical_geometry_sha256": {str(y): GEOMETRY_SHA256[y] for y in YEARS},
        "stage2_result_sha256": sha_file(a.stage2_result),
        "source_pins": {
            "recurrent_eom_git_blob": METHOD_BLOB,
            "promoted_runner_git_blob": PROMOTED_RUNNER_BLOB,
            "pretruth_protocol_git_blob": PROTOCOL_BLOB,
            "stage2_binding_freeze_git_blob": STAGE2_FREEZE_BLOB,
        },
        "runtime": {
            "python": "3.11",
            "numpy": "2.1.3",
            "scipy": "1.14.1",
            "scikit_learn": "1.7.1",
            "hdbscan": "0.8.43",
        },
        "configuration": {
            "representation": "GEO6=(cos(sol),sin(sol),sin(sun_lon)*cos(ecl_lat),cos(sun_lon)*cos(ecl_lat),sin(ecl_lat),vg/72)",
            "min_cluster_size": MIN_CLUSTER_SIZE,
            "min_samples": MIN_SAMPLES,
            "metric": "euclidean",
            "cluster_selection_method": "eom",
            "cluster_selection_epsilon": 0.0,
            "allow_single_cluster": False,
            "prediction_data": False,
            "speed_scale": SPEED_SCALE,
        },
        "pooled_event_count": len(events),
        "pooled_event_order_sha256": event_order_sha,
        "pooled_event_order": event_order,
        "year_vector_little_endian_int64_sha256": year_vector_sha,
        "geo6_little_endian_float64_sha256": geo6_sha,
        "condensed_tree": tree_identity,
        "ordinary_stability": ordinary_rows,
        "annual_recurrent_stability": annual_rows,
        "recurrent_stability": recurrent_rows,
        "vanilla_model_partition_sha256": partition_sha(np.asarray(model.labels_, dtype=np.int64), event_ids),
        "vanilla_custom_partition_sha256": partition_sha(parent_labels, event_ids),
        "recurrent_partition_sha256": partition_sha(successor_labels, event_ids),
        "vanilla_selected_nodes": [int(x) for x in parent_nodes],
        "recurrent_selected_nodes": [int(x) for x in successor_nodes],
        "mechanism_active": parent_nodes != successor_nodes,
        "vanilla_candidates": parent_candidates,
        "recurrent_candidates": successor_candidates,
        "vanilla_candidate_count": len(parent_candidates),
        "recurrent_candidate_count": len(successor_candidates),
        "vanilla_ordering": ["ordinary_stability_desc", "member_count_desc", "family_id_asc"],
        "recurrent_ordering": ["recurrent_stability_desc", "ordinary_stability_desc", "member_count_desc", "family_id_asc"],
        "truth_interface_available": False,
        "shower_column_accessed": False,
        "object_column_accessed": False,
        "orbit_fields_accessed": False,
        "quality_filter_used": False,
        "survey_calibration_used": False,
        "post_result_parameter_search": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "target_region_physical_values_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "orbittrace_target_access": False,
    }
    require(payload["vanilla_model_partition_sha256"] == payload["vanilla_custom_partition_sha256"], "vanilla identity hash mismatch")
    require(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected EFN event reached pretruth payload")

    a.output.mkdir(parents=True, exist_ok=True)
    out = a.output / "EFN_RECURRENT_EOM_PRETRUTH.json"
    out.write_bytes(stable_json_bytes(payload))
    result = {
        "verdict": payload["verdict"],
        "pretruth_sha256": sha_file(out),
        "pooled_event_count": payload["pooled_event_count"],
        "vanilla_candidate_count": payload["vanilla_candidate_count"],
        "recurrent_candidate_count": payload["recurrent_candidate_count"],
        "mechanism_active": payload["mechanism_active"],
        "vanilla_selected_node_count": len(parent_nodes),
        "recurrent_selected_node_count": len(successor_nodes),
        "condensed_tree_rows": len(tree_rows),
        "condensed_tree_raw_sha256": tree_identity["raw_tree_bytes_sha256"],
        "geo6_sha256": geo6_sha,
        "shower_column_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    (a.output / "EFN_RECURRENT_EOM_PRETRUTH_MANIFEST.json").write_bytes(stable_json_bytes(result))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
