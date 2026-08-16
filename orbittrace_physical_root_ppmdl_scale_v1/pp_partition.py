#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import graph_tool
import graph_tool.all as gt
import numpy as np

PREFIX = "ORBITTRACE_PHYSICAL_ROOT_PPMDL_SCALE_V1|"
MIN_SUPPORT = 4
EXPECTED_GRAPH_TOOL_BUILD_PREFIX = "2.99dev (commit c049a734"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def component_seed(ids: list[str], denominator: int, bucket: int) -> int:
    ch = hashlib.sha256("|".join(sorted(ids)).encode("utf-8")).hexdigest()
    raw = hashlib.sha256((PREFIX + str(denominator) + "|" + str(bucket) + "|" + ch).encode("utf-8")).digest()[:4]
    return int.from_bytes(raw, "big")


def member_hash(ids: list[str]) -> str:
    return hashlib.sha256("|".join(sorted(ids)).encode("utf-8")).hexdigest()[:20]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--denominator", type=int, required=True)
    ap.add_argument("--bucket", type=int, required=True)
    a = ap.parse_args()

    version = str(graph_tool.__version__)
    req(version.startswith(EXPECTED_GRAPH_TOOL_BUILD_PREFIX), f"graph-tool release image build changed: {version}")

    p = json.loads(a.input.read_text())
    ids = [str(x) for x in p["ids"]]
    edges = [(int(x[0]), int(x[1])) for x in p["edges"]]
    n = len(ids)
    req(n >= 4 and len(set(ids)) == n, "invalid input IDs")
    req(a.denominator in (128, 1024) and a.bucket in (0, 1, 2, 3), "invalid frozen subset")
    req(all(0 <= u < v < n for u, v in edges), "edges must be canonical distinct pairs")
    req(len(edges) == len(set(edges)), "duplicate edges")

    g = gt.Graph(directed=False)
    g.add_vertex(n)
    if edges:
        g.add_edge_list(edges)
    comp_prop, hist = gt.label_components(g)
    comp = np.asarray(comp_prop.a, dtype=np.int64)
    hist = np.asarray(hist, dtype=np.int64)
    req(comp.shape == (n,) and int(hist.sum()) == n, "component partition changed")

    candidates: list[dict] = []
    component_rows: list[dict] = []
    for cid in range(len(hist)):
        global_ix = np.flatnonzero(comp == cid)
        size = int(len(global_ix))
        if size < MIN_SUPPORT:
            component_rows.append({"component": cid, "size": size, "eligible": False, "block_count": 0})
            continue

        remap = {int(v): j for j, v in enumerate(global_ix.tolist())}
        local_edges = [(remap[u], remap[v]) for u, v in edges if u in remap and v in remap]
        sg = gt.Graph(directed=False)
        sg.add_vertex(size)
        if local_edges:
            sg.add_edge_list(local_edges)
        req(int(sg.num_vertices()) == size, "subgraph vertex count changed")
        req(int(sg.num_edges()) == len(local_edges), "subgraph edge count changed")

        cids = [ids[int(v)] for v in global_ix]
        seed = component_seed(cids, a.denominator, a.bucket)
        np.random.seed(seed)
        gt.seed_rng(seed)

        state = gt.minimize_blockmodel_dl(sg, state=gt.PPBlockState)
        labels = np.asarray(state.get_blocks().a, dtype=np.int64)
        req(labels.shape == (size,), "wrong planted-partition label shape")
        unique_labels = sorted(int(x) for x in np.unique(labels))
        entropy = float(state.entropy())
        req(np.isfinite(entropy), "nonfinite planted-partition description length")

        kept = 0
        block_sizes = []
        for lab in unique_labels:
            lix = np.flatnonzero(labels == lab)
            mids = sorted(cids[int(i)] for i in lix)
            block_sizes.append(len(mids))
            if len(mids) < MIN_SUPPORT:
                continue
            kept += 1
            candidates.append({
                "family_hash": member_hash(mids),
                "member_ids": mids,
                "member_count": len(mids),
                "component": cid,
                "component_size": size,
                "component_seed": seed,
                "block_label": lab,
            })

        component_rows.append({
            "component": cid,
            "size": size,
            "eligible": True,
            "edge_count": len(local_edges),
            "seed": seed,
            "description_length": entropy,
            "inferred_block_count": len(unique_labels),
            "support4_block_count": kept,
            "block_sizes_desc": sorted(block_sizes, reverse=True),
        })

    unique: dict[tuple[str, ...], dict] = {}
    for row in candidates:
        key = tuple(row["member_ids"])
        unique.setdefault(key, row)
    rows = sorted(unique.values(), key=lambda r: (r["family_hash"], r["member_ids"]))

    out = {
        "schema": "ORBITTRACE_PHYSICAL_ROOT_PPMDL_PARTITION_V1",
        "graph_tool_version": version,
        "graph_tool_release_image_digest": "sha256:e12ed85b23e1068eec883bbffeafc7cc36ce461f88ee26e0b3ef20bfcd5508f7",
        "engineering_repair": "repair1_release_2_98_image_reports_2_99dev_c049a734",
        "denominator": a.denominator,
        "bucket": a.bucket,
        "events_total": n,
        "edge_count": len(edges),
        "physical_component_count": int(len(hist)),
        "eligible_component_count": int(np.sum(hist >= MIN_SUPPORT)),
        "candidate_count": len(rows),
        "candidates": rows,
        "components": component_rows,
        "rng_rule": "sha256_method_denominator_bucket_component_membership_uint32_be",
        "model": "graph_tool_PPBlockState_minimize_blockmodel_dl_defaults",
        "degree_corrected": True,
        "truth_access": False,
    }
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "graph_tool_version": version,
        "events_total": n,
        "edge_count": len(edges),
        "components": len(hist),
        "eligible_components": int(np.sum(hist >= MIN_SUPPORT)),
        "candidate_count": len(rows),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
