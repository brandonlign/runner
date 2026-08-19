#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
from gudhi.clustering.tomato import Tomato
from scipy.spatial import cKDTree

PROMOTED_SUPPORT_BLOB = "3712a36033088f1bd486cefdc8dc474c194fc85c"
PROMOTION_RESULT_SHA256 = "cbc7a0ac6bad3ad93dbd91419718c9b2388eeb71d65016e9f7fcd2d275d00503"
CUT_RULE = "recurse_reportable_child_discard_immediate_subsupport_sibling_else_parent_when_both_children_subsupport"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def support_pruned_cut_linear(
    old: Any,
    structural: Any,
    events: list[dict[str, Any]],
    *,
    keep_neighbors: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[list[int]] | None, np.ndarray, np.ndarray, np.ndarray]:
    """Memory-linear implementation of the already-promoted support-pruned cut.

    Scientific rule is exactly support_pruned_cut.py v1. Internal-node memberships are
    represented by subtree sizes plus a leaf-owner traversal so the full pooled
    2022+2023 replay does not materialize a frozenset at every hierarchy node.
    """
    ordered = sorted(events, key=lambda e: str(e["id"]))
    ids = [str(e["id"]) for e in ordered]
    Z = structural.physical_embedding(ordered)
    raw = cKDTree(Z).query_ball_point(Z, r=float(old.RADIUS), p=2.0, eps=0.0, return_sorted=True)
    neighbors = [list(map(int, row)) for row in raw]
    req(len(neighbors) == len(ids), "radius graph row count")
    adjacency = [set(row) for row in neighbors]
    for i, row in enumerate(neighbors):
        req(bool(row) and row.count(i) == 1, f"self membership failure at {i}")
        req(row[0] >= 0 and row[-1] < len(ids), f"radius index out of range {i}")
    req(all(i in adjacency[j] for i, row in enumerate(neighbors) for j in row), "radius graph asymmetric")

    degrees = np.asarray([len(row) for row in neighbors], dtype=np.int64)
    rho = degrees.astype(float) / float(len(ids))
    req(np.all(rho > 0.0) and np.all(np.isfinite(rho)), "invalid radius density")

    model = Tomato(graph_type="manual", density_type="manual")
    model.fit(neighbors, weights=rho)
    leaf_labels = np.asarray(model.leaf_labels_, dtype=np.int64)
    L = int(model.n_leaves_)
    req(leaf_labels.shape == (len(ids),) and L >= 1, "bad ToMATo leaves")
    req(int(leaf_labels.min()) >= 0 and int(leaf_labels.max()) + 1 == L, "noncontiguous ToMATo leaves")
    children = np.asarray(model.children_, dtype=np.int64).reshape((-1, 2))
    roots_expected = len(np.asarray(model.max_weight_per_cc_, dtype=float))
    req(L - len(children) == roots_expected, "leaf/merge/root arithmetic")

    diagram = np.asarray(model.diagram_, dtype=float)
    ds = old.diagram_sorted(diagram)
    P = np.sort(np.asarray(diagram[:, 0] - diagram[:, 1], dtype=float)) if diagram.size else np.empty(0, dtype=float)
    req(len(P) == len(children) == len(ds) and np.all(P >= -1e-15), "bad finite persistence")
    P = np.maximum(P, 0.0)

    N = L + len(children)
    parent = np.full(N, -1, dtype=np.int64)
    subtree_size = np.zeros(N, dtype=np.int64)
    subtree_size[:L] = np.bincount(leaf_labels, minlength=L)
    req(np.all(subtree_size[:L] > 0), "empty ToMATo leaf")
    active_peak = np.full(N, np.nan, dtype=float)
    active_key: list[str | None] = [None] * N
    merge_level = np.full(N, np.nan, dtype=float)

    for i, (lab, eid) in enumerate(zip(leaf_labels.tolist(), ids)):
        value = float(rho[i])
        previous = active_peak[lab]
        key = active_key[lab]
        if not np.isfinite(previous) or value > previous or (value == previous and (key is None or eid < key)):
            active_peak[lab] = value
            active_key[lab] = eid

    reconstructed: list[list[float]] = []
    dying: set[int] = set()
    for off, pair in enumerate(children):
        node = L + off
        a, b = int(pair[0]), int(pair[1])
        req(0 <= a < node and 0 <= b < node and a != b, "bad ToMATo child")
        req(parent[a] == -1 and parent[b] == -1, "hierarchy node has multiple parents")
        parent[a] = node
        parent[b] = node
        subtree_size[node] = subtree_size[a] + subtree_size[b]
        pa, pb = float(active_peak[a]), float(active_peak[b])
        ka, kb = str(active_key[a]), str(active_key[b])
        if pa > pb or (pa == pb and ka < kb):
            winner, loser = a, b
        else:
            winner, loser = b, a
        active_peak[node] = float(active_peak[winner])
        active_key[node] = str(active_key[winner])
        req(loser not in dying, "mode died twice")
        dying.add(loser)
        death = float(active_peak[loser]) - float(P[off])
        merge_level[node] = death
        reconstructed.append([float(active_peak[loser]), death])

    roots = np.flatnonzero(parent == -1)
    req(len(roots) == roots_expected, "root count mismatch")
    req(int(subtree_size[roots].sum()) == len(ids), "roots do not partition events")
    rec = old.diagram_sorted(np.asarray(reconstructed, dtype=float))
    req(rec.shape == ds.shape and np.allclose(rec, ds, rtol=0.0, atol=1e-12), "ToMATo diagram reconstruction mismatch")

    selected_nodes: list[int] = []
    discarded_nodes: list[int] = []
    stack = [int(x) for x in roots[::-1]]
    while stack:
        node = stack.pop()
        if node < L:
            if int(subtree_size[node]) >= int(old.MIN_SUPPORT):
                selected_nodes.append(node)
            else:
                discarded_nodes.append(node)
            continue
        a, b = map(int, children[node - L])
        sa, sb = int(subtree_size[a]), int(subtree_size[b])
        if sa >= int(old.MIN_SUPPORT) and sb >= int(old.MIN_SUPPORT):
            stack.append(b)
            stack.append(a)
        elif sa >= int(old.MIN_SUPPORT) and sb < int(old.MIN_SUPPORT):
            discarded_nodes.append(b)
            stack.append(a)
        elif sb >= int(old.MIN_SUPPORT) and sa < int(old.MIN_SUPPORT):
            discarded_nodes.append(a)
            stack.append(b)
        elif int(subtree_size[node]) >= int(old.MIN_SUPPORT):
            selected_nodes.append(node)
        else:
            discarded_nodes.append(node)

    req(len(selected_nodes) == len(set(selected_nodes)), "duplicate selected node")
    req(len(discarded_nodes) == len(set(discarded_nodes)), "duplicate discarded node")
    req(all(int(subtree_size[n]) >= int(old.MIN_SUPPORT) for n in selected_nodes), "sub-support selected")
    req(all(int(subtree_size[n]) < int(old.MIN_SUPPORT) for n in discarded_nodes), "reportable node discarded")

    selected_set = set(selected_nodes)
    leaf_owner = np.full(L, -1, dtype=np.int64)
    stack2: list[tuple[int, int]] = [(int(r), -1) for r in roots[::-1]]
    while stack2:
        node, owner = stack2.pop()
        if node in selected_set:
            owner = node
        if node < L:
            leaf_owner[node] = owner
        else:
            a, b = map(int, children[node - L])
            stack2.append((b, owner))
            stack2.append((a, owner))

    ids_by_node: dict[int, list[str]] = {node: [] for node in selected_nodes}
    for eid, lab in zip(ids, leaf_labels.tolist()):
        owner = int(leaf_owner[int(lab)])
        if owner >= 0:
            ids_by_node[owner].append(eid)
    for node in selected_nodes:
        req(len(ids_by_node[node]) == int(subtree_size[node]) >= int(old.MIN_SUPPORT), "selected membership size mismatch")

    discarded_event_count = int(sum(int(subtree_size[n]) for n in discarded_nodes))
    covered_event_count = int(sum(len(v) for v in ids_by_node.values()))
    req(covered_event_count + discarded_event_count == len(ids), "selected+noise do not partition universe")

    rows: list[dict[str, Any]] = []
    for node in selected_nodes:
        mem = ids_by_node[node]
        p = int(parent[node])
        outside = 0.0 if p == -1 else float(merge_level[p])
        req(np.isfinite(outside), f"missing outside merge {node}")
        contrast = float(active_peak[node]) - outside
        req(contrast >= -1e-12 and np.isfinite(contrast), f"bad modal contrast {node}")
        contrast = max(contrast, 0.0)
        members = frozenset(mem)
        rows.append({
            "family_id": old.family_id("TSPC1", mem),
            "family_hash": structural.member_hash(members),
            "event_ids": mem,
            "member_count": len(mem),
            "node": int(node),
            "is_root": bool(p == -1),
            "active_mode_peak": float(active_peak[node]),
            "active_mode_key": str(active_key[node]),
            "outside_merge_level": outside,
            "modal_contrast": contrast,
        })
    rows.sort(key=lambda r: (-float(r["modal_contrast"]), str(r["family_hash"])))
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank

    summary = {
        "candidate_count": len(rows),
        "root_count": len(roots),
        "leaf_count": L,
        "internal_node_count": len(children),
        "covered_event_count": covered_event_count,
        "discarded_subsupport_node_count": len(discarded_nodes),
        "discarded_subsupport_event_count": discarded_event_count,
        "coverage_fraction": float(covered_event_count / len(ids)) if ids else 0.0,
        "median_radius_degree": float(np.median(degrees)),
        "p90_radius_degree": float(np.quantile(degrees, 0.9)),
        "max_radius_degree": int(degrees.max()),
        "pairwise_disjoint_by_construction": True,
        "selected_plus_noise_partition": True,
        "diagram_reconstruction_max_abs_error": float(np.max(np.abs(rec - ds))) if rec.size else 0.0,
        "cut_rule": CUT_RULE,
    }
    return rows, summary, neighbors if keep_neighbors else None, leaf_labels, leaf_owner, degrees


def equivalence_audit(old: Any, structural: Any, support: Any) -> dict[str, Any]:
    events = old.synthetic_events()
    exact, exact_summary = support.support_pruned_cut(structural, events)
    optimized, opt_summary, _neighbors, _labels, _owners, _degrees = support_pruned_cut_linear(old, structural, events, keep_neighbors=False)
    req(len(exact) == len(optimized), "support-pruned candidate count differs on synthetic audit")
    exact_by_members = {tuple(r["event_ids"]): r for r in exact}
    opt_by_members = {tuple(r["event_ids"]): r for r in optimized}
    req(set(exact_by_members) == set(opt_by_members), "support-pruned synthetic memberships differ")
    fields = ("family_id", "family_hash", "member_count", "node", "is_root", "active_mode_key")
    float_fields = ("active_mode_peak", "outside_merge_level", "modal_contrast")
    for members in exact_by_members:
        a, b = exact_by_members[members], opt_by_members[members]
        for field in fields:
            req(a[field] == b[field], f"support-pruned synthetic mismatch field={field}")
        for field in float_fields:
            req(abs(float(a[field]) - float(b[field])) <= 1e-15, f"support-pruned synthetic float mismatch field={field}")
    req(int(exact_summary["discarded_subsupport_event_count"]) == int(opt_summary["discarded_subsupport_event_count"]), "discarded-event audit mismatch")
    return {
        "verdict": "PASS_EXACT_SYNTHETIC_SUPPORT_PRUNED_CUT_EQUIVALENCE",
        "event_count": len(events),
        "candidate_count": len(exact),
        "discarded_subsupport_event_count": int(opt_summary["discarded_subsupport_event_count"]),
        "optimized_summary": opt_summary,
    }


def main() -> int:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--old-scan", type=Path, required=True)
    known, remaining = ap.parse_known_args()
    old = load(known.old_scan, "orbittrace_m2d_blind_1378_frozen")

    # Freeze the only scientific substitution: promoted support-pruned cut v1.
    old.SUPPORT_BLOB = PROMOTED_SUPPORT_BLOB
    old.support_resolved_cut_linear = lambda structural, events, keep_neighbors: support_pruned_cut_linear(old, structural, events, keep_neighbors=keep_neighbors)
    old.equivalence_audit = lambda structural, support: equivalence_audit(old, structural, support)

    sys.argv = [str(known.old_scan)] + remaining
    rc = int(old.main())
    req(rc == 0, f"frozen #1378 scan returned {rc}")

    out_arg = None
    for i, token in enumerate(remaining):
        if token == "--output" and i + 1 < len(remaining):
            out_arg = Path(remaining[i + 1])
            break
    req(out_arg is not None, "missing output argument")
    ranked_path = out_arg / "orbittrace_m2d_blind_ranked_pretruth.json.gz"
    payload = json.loads(gzip.decompress(ranked_path.read_bytes()))
    req(payload["shower_truth_used"] is False, "truth entered scan")
    req(payload["orbittrace_target_information_access"] is False, "target information entered scan")
    req(payload["orbittrace_canonical_members_access"] is False, "canonical IDs entered scan")
    req(payload["prior_orbittrace_reveal_access"] is False, "prior reveal entered scan")
    payload["replay_variant"] = "PROMOTED_SUPPORT_PRUNED_CUT_V1_POST_PROMOTION_BLIND_PROTOCOL_REPLAY"
    payload["configuration"]["cut_rule"] = CUT_RULE
    payload["promotion_evidence_result_sha256"] = PROMOTION_RESULT_SHA256
    payload["method_changed_after_promotion"] = False
    payload["post_promotion_parameter_search"] = False
    inner = json.dumps(payload, separators=(",", ":"), sort_keys=True, allow_nan=False).encode("utf-8")
    ranked_path.write_bytes(gzip.compress(inner, compresslevel=9, mtime=0))
    (out_arg / "support_pruned_replay_metadata.json").write_text(json.dumps({
        "replay_variant": payload["replay_variant"],
        "cut_rule": CUT_RULE,
        "promotion_evidence_result_sha256": PROMOTION_RESULT_SHA256,
        "candidate_count": payload["candidate_count"],
        "event_count": payload["event_count"],
        "covered_event_count": payload["support_summary"]["covered_event_count"],
        "discarded_subsupport_event_count": payload["support_summary"]["discarded_subsupport_event_count"],
        "pretruth_inner_sha256": old.sha256_bytes(inner),
        "pretruth_gzip_sha256": old.sha256_path(ranked_path),
        "target_information_access": False,
        "canonical_members_access": False,
    }, indent=2, sort_keys=True) + "\n")
    print("SUPPORT_PRUNED_REPLAY_PRETRUTH_SEALED", old.sha256_path(ranked_path), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
