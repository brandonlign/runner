#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

import numpy as np
from scipy.spatial import cKDTree

DOCKER_IMAGE = "tiagopeixoto/graph-tool@sha256:e12ed85b23e1068eec883bbffeafc7cc36ce461f88ee26e0b3ef20bfcd5508f7"
EXPECTED_GRAPH_TOOL_BUILD_PREFIX = "2.99dev (commit c049a734"
METHOD = "ORBITTRACE_PHYSICAL_ROOT_PPMDL_SCALE_V1"
MIN_SUPPORT = 4


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def infer_subset(base: Any, ids: list[str]) -> tuple[int, int]:
    h = np.asarray([base.event_hash_u64(x) for x in ids], dtype=np.uint64)
    m1024 = np.unique(h % np.uint64(1024))
    if len(m1024) == 1 and int(m1024[0]) in (0, 1, 2, 3):
        return 1024, int(m1024[0])
    m128 = np.unique(h % np.uint64(128))
    req(len(m128) == 1 and int(m128[0]) in (0, 1, 2, 3), "cannot infer frozen subset identity")
    return 128, int(m128[0])


def canonical_edges(neighbors: list[list[int]]) -> list[list[int]]:
    edges: list[list[int]] = []
    seen: set[tuple[int, int]] = set()
    for i, row in enumerate(neighbors):
        for j in row:
            if j == i:
                continue
            u, v = (i, int(j)) if i < int(j) else (int(j), i)
            if (u, v) not in seen:
                seen.add((u, v))
                edges.append([u, v])
    edges.sort()
    return edges


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-runner", type=Path, required=True)
    ap.add_argument("--partition-script", type=Path, required=True)
    ap.add_argument("--parent-runner", type=Path, required=True)
    ap.add_argument("--quality-source", type=Path, required=True)
    ap.add_argument("--support-source-parts", type=Path, required=True)
    ap.add_argument("--candidate-payload", type=Path, required=True)
    ap.add_argument("--baseline-payload", type=Path, required=True)
    ap.add_argument("--scorer-parts", type=Path, required=True)
    ap.add_argument("--v8-result-json", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    aux = a.output / "ppmdl_partitions"
    aux.mkdir(parents=True, exist_ok=True)

    base = load_module(a.base_runner, "ppmdl_frozen_topomodal_base")
    req(getattr(base, "MIN_SUPPORT") == MIN_SUPPORT, "#1284 support changed")
    req(float(getattr(base, "RADIUS")) == 1.0, "#1284 physical radius changed")

    repo_root = Path.cwd().resolve()
    partition_script = a.partition_script.resolve()
    req(partition_script.is_file(), "partition script missing")
    req(str(partition_script).startswith(str(repo_root) + os.sep), "partition script must be inside repository")
    script_rel = partition_script.relative_to(repo_root).as_posix()

    def ppmdl_candidates(events: list[dict[str, Any]]):
        ordered = sorted(events, key=lambda e: str(e["id"]))
        ids = [str(e["id"]) for e in ordered]
        denominator, bucket = infer_subset(base, ids)
        Z = base.physical_embedding(ordered)
        tree = cKDTree(Z)
        raw_neighbors = tree.query_ball_point(Z, r=1.0, p=2.0, eps=0.0, return_sorted=True)
        neighbors = [list(map(int, row)) for row in raw_neighbors]
        req(len(neighbors) == len(ids), "radius graph row count changed")
        adjacency = [set(row) for row in neighbors]
        req(all(i in adjacency[i] for i in range(len(ids))), "self missing from radius neighborhoods")
        req(all(i in adjacency[j] for i, row in enumerate(neighbors) for j in row), "radius graph not symmetric")
        edges = canonical_edges(neighbors)
        payload = {
            "schema": "ORBITTRACE_PHYSICAL_ROOT_GRAPH_V1",
            "ids": ids,
            "edges": edges,
            "denominator": denominator,
            "bucket": bucket,
            "physical_embedding": "exact_1284_5deg_4deg_10pct",
            "radius": 1.0,
            "truth_access": False,
        }
        raw = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        graph_sha = sha256_bytes(raw)

        with tempfile.TemporaryDirectory(prefix=f"orbittrace-ppmdl-{denominator}-{bucket}-") as td:
            tdp = Path(td)
            inp = tdp / "input.json"
            out = tdp / "output.json"
            inp.write_bytes(raw)
            cmd = [
                "docker", "run", "--rm",
                "-e", "OMP_NUM_THREADS=1",
                "-e", "OPENBLAS_NUM_THREADS=1",
                "-v", f"{repo_root}:/repo:ro",
                "-v", f"{tdp}:/work",
                DOCKER_IMAGE,
                "python3", f"/repo/{script_rel}",
                "--input", "/work/input.json",
                "--output", "/work/output.json",
                "--denominator", str(denominator),
                "--bucket", str(bucket),
            ]
            print(f"[ppmdl] d={denominator} b={bucket} n={len(ids)} edges={len(edges)}", flush=True)
            cp = subprocess.run(cmd, check=False, text=True, capture_output=True)
            if cp.stdout:
                print(cp.stdout, end="", flush=True)
            if cp.stderr:
                print(cp.stderr, end="", file=sys.stderr, flush=True)
            req(cp.returncode == 0, f"graph-tool partition failed d={denominator} b={bucket} rc={cp.returncode}")
            req(out.is_file(), "partition output missing")
            part_raw = out.read_bytes()
            part = json.loads(part_raw)
            req(part["schema"] == "ORBITTRACE_PHYSICAL_ROOT_PPMDL_PARTITION_V1", "wrong partition schema")
            req(str(part["graph_tool_version"]).startswith(EXPECTED_GRAPH_TOOL_BUILD_PREFIX), "graph-tool release image build changed")
            req(part["graph_tool_release_image_digest"] == "sha256:e12ed85b23e1068eec883bbffeafc7cc36ce461f88ee26e0b3ef20bfcd5508f7", "graph-tool image digest changed")
            req(part["engineering_repair"] == "repair1_release_2_98_image_reports_2_99dev_c049a734", "repair identity changed")
            req(int(part["events_total"]) == len(ids), "partition event count changed")
            req(int(part["edge_count"]) == len(edges), "partition edge count changed")
            req(bool(part["truth_access"]) is False, "partition accessed truth")
            req(int(part["denominator"]) == denominator and int(part["bucket"]) == bucket, "partition subset changed")
            (aux / f"partition_d{denominator}_b{bucket}.json").write_bytes(part_raw)

        candidates: list[frozenset[str]] = []
        rows = []
        seen: set[tuple[str, ...]] = set()
        idset = set(ids)
        for r in part["candidates"]:
            mids = tuple(sorted(str(x) for x in r["member_ids"]))
            req(len(mids) >= MIN_SUPPORT and len(set(mids)) == len(mids), "invalid support-4 partition candidate")
            req(set(mids).issubset(idset), "partition emitted foreign event")
            if mids in seen:
                continue
            seen.add(mids)
            members = frozenset(mids)
            candidates.append(members)
            rows.append({"family_hash": base.member_hash(members), "member_count": len(members)})
        counts = sorted((len(c) for c in candidates), reverse=True)
        summary = {
            "candidate_count": len(candidates),
            "physical_component_count": int(part["physical_component_count"]),
            "eligible_component_count": int(part["eligible_component_count"]),
            "inferred_block_count_total": int(sum(int(x.get("inferred_block_count", 0)) for x in part["components"])),
            "graph_edge_count": len(edges),
            "graph_sha256": graph_sha,
            "graph_tool_version": str(part["graph_tool_version"]),
            "graph_tool_release_image_digest": part["graph_tool_release_image_digest"],
            "engineering_repair": part["engineering_repair"],
            "model": str(part["model"]),
            "largest_candidate_count": int(counts[0]) if counts else 0,
            "largest_candidate_fraction": float(counts[0] / len(ids)) if counts else 0.0,
            "candidate_rows": sorted(rows, key=lambda r: (-r["member_count"], r["family_hash"])),
        }
        return candidates, summary

    base.topomodal_candidates = ppmdl_candidates

    old_argv = sys.argv[:]
    sys.argv = [
        str(a.base_runner),
        "--parent-runner", str(a.parent_runner),
        "--quality-source", str(a.quality_source),
        "--support-source-parts", str(a.support_source_parts),
        "--candidate-payload", str(a.candidate_payload),
        "--baseline-payload", str(a.baseline_payload),
        "--scorer-parts", str(a.scorer_parts),
        "--v8-result-json", str(a.v8_result_json),
        "--output", str(a.output),
    ]
    try:
        rc = int(base.main())
    finally:
        sys.argv = old_argv
    req(rc == 0, "frozen #1284 diagnostic harness failed")

    legacy = a.output / "TOPOMODAL_HIERARCHY_SCALE_V1.json"
    req(legacy.is_file(), "base diagnostic output missing")
    d = json.loads(legacy.read_text())
    req(d["scientific_role"] == "ZERO_LABEL_STRUCTURAL_DIAGNOSTIC_ONLY", "base scientific role changed")
    req(d["shower_truth_used"] is False and d["target_information_access"] is False, "firewall changed")

    for row in d["fits"]:
        row["ppmdl"] = row.pop("topomodal")
    for pair in d["nested_pairs"]:
        pair["ppmdl"] = pair.pop("topomodal")
        pair["ppmdl_strict_win"] = pair.pop("topomodal_strict_win")
    s = d["summary"]
    s["ppmdl_pooled_fine_to_coarse_mean_best_jaccard"] = s.pop("topomodal_pooled_fine_to_coarse_mean_best_jaccard")
    s["ppmdl_median_bucket_fine_to_coarse_mean_best_jaccard"] = s.pop("topomodal_median_bucket_fine_to_coarse_mean_best_jaccard")
    s["ppmdl_bucket_wins"] = s.pop("topomodal_bucket_wins")
    gate = s["gate"]
    gate["ppmdl_nonempty_all_eight"] = gate.pop("topomodal_nonempty_all_eight")
    passed = all(bool(x) for x in gate.values())

    d["schema"] = METHOD
    d["interpretation"] = (
        "SUPPORTS_PHYSICAL_ROOT_PPMDL_CROSS_SCALE_COHERENCE"
        if passed else "REFUTES_PHYSICAL_ROOT_PPMDL_CROSS_SCALE_COHERENCE"
    )
    d["configuration"] = {
        "physical_embedding": "exact_1284_5deg_solar_4deg_radiant_10pct_logspeed",
        "graph": "exact_simple_undirected_radius_1_physical_graph",
        "outer_boundary": "exact_physical_connected_components",
        "model": "graph_tool_release_2_98_image_digest_PPBlockState_minimize_blockmodel_dl_defaults",
        "graph_tool_release_image_digest": "sha256:e12ed85b23e1068eec883bbffeafc7cc36ce461f88ee26e0b3ef20bfcd5508f7",
        "graph_tool_reported_build_prefix": EXPECTED_GRAPH_TOOL_BUILD_PREFIX,
        "engineering_repair": "repair1_release_2_98_image_reports_2_99dev_c049a734",
        "degree_corrected": True,
        "community_count": "Bayesian_description_length_selected",
        "min_candidate_support": MIN_SUPPORT,
        "rng": "one_sha256_derived_seed_per_physical_component_no_restarts",
        "coarse_denominator": 128,
        "fine_denominator": 1024,
        "buckets": [0, 1, 2, 3],
    }
    d["literature_role"] = "Bayesian_assortative_planted_partition_graph_inference"
    d["method_parameter_selection_from_result"] = False
    out = a.output / "PHYSICAL_ROOT_PPMDL_SCALE_V1.json"
    out.write_text(json.dumps(d, indent=2, sort_keys=True, allow_nan=False) + "\n")
    legacy.unlink()
    print(json.dumps({"interpretation": d["interpretation"], "summary": d["summary"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
