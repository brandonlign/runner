#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def greedy_antichain(rows: list[dict[str, Any]], parent: list[int | None], children: list[list[int]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    del parent, children
    sets = [set(map(str, r["event_ids"])) for r in rows]
    order = sorted(range(len(rows)), key=lambda i: (-float(rows[i]["internal_2d_mass"]), str(rows[i]["family_hash"])))
    accepted: list[int] = []
    rejected_overlap = 0
    rejected_broad_ancestor = 0
    rejected_narrow_descendant = 0
    rejected_examples: list[dict[str, Any]] = []

    for i in order:
        s = sets[i]
        overlaps = [j for j in accepted if not s.isdisjoint(sets[j])]
        if not overlaps:
            accepted.append(i)
            continue
        # TopoModal hierarchy membership is laminar: any overlap must be containment.
        for j in overlaps:
            a = sets[j]
            req(s.issubset(a) or a.issubset(s), "non-laminar hierarchy overlap")
        rejected_overlap += 1
        if any(sets[j].issubset(s) and sets[j] != s for j in overlaps):
            rejected_broad_ancestor += 1
        if any(s.issubset(sets[j]) and sets[j] != s for j in overlaps):
            rejected_narrow_descendant += 1
        if len(rejected_examples) < 20:
            rejected_examples.append({
                "rejected_family_hash": str(rows[i]["family_hash"]),
                "rejected_members": int(rows[i]["member_count"]),
                "rejected_m2d": float(rows[i]["internal_2d_mass"]),
                "accepted_overlap": [{
                    "family_hash": str(rows[j]["family_hash"]),
                    "members": int(rows[j]["member_count"]),
                    "m2d": float(rows[j]["internal_2d_mass"]),
                } for j in overlaps[:4]],
            })

    out = [dict(rows[i]) for i in accepted]
    out.sort(key=lambda r: (-float(r["internal_2d_mass"]), str(r["family_hash"])))
    for rank, row in enumerate(out, 1):
        row["rank"] = rank
    out_sets = [set(map(str, r["event_ids"])) for r in out]
    req(all(a.isdisjoint(b) for i, a in enumerate(out_sets) for b in out_sets[i + 1 :]), "accepted antichain overlaps")
    return out, {
        "reportable_node_count": len(rows),
        "selected_candidate_count": len(out),
        # Compatibility key consumed by the frozen label-free parent driver only.
        "evidence_split_count": rejected_overlap,
        "overlap_rejection_count": rejected_overlap,
        "rejected_broad_ancestor_count": rejected_broad_ancestor,
        "rejected_narrow_descendant_count": rejected_narrow_descendant,
        "rejected_examples": rejected_examples,
        "pairwise_disjoint": True,
        "packing_rule": "M2D_desc_then_family_hash; accept_iff_disjoint_from_all_higher_ranked_accepted_nodes",
    }


def main() -> int:
    args = list(sys.argv[1:])
    req("--recursive-builder" in args, "missing --recursive-builder")
    pos = args.index("--recursive-builder")
    req(pos + 1 < len(args), "missing recursive builder value")
    recursive_path = Path(args[pos + 1])
    del args[pos:pos + 2]
    req("--output" in args, "missing --output")
    op = args.index("--output")
    req(op + 1 < len(args), "missing output value")
    output_path = Path(args[op + 1])

    rec = load(recursive_path, "greedy_antichain_frozen_label_free_driver")
    rec.evidence_cut = greedy_antichain
    old = sys.argv
    try:
        sys.argv = [old[0], *args]
        rc = int(rec.main() or 0)
    finally:
        sys.argv = old
    req(rc == 0 and output_path.is_file(), "parent label-free driver failed")

    payload = json.loads(output_path.read_text())
    req(payload.get("shower_truth_used") is False, "truth entered pretruth")
    req(payload.get("target_information_access") is False and payload.get("target_region_events_accessed") is False, "target firewall")
    req(payload.get("orbittrace_reveal_access") is False and payload.get("sonotaco_scientific_access") is False, "external/reveal firewall")
    req(payload.get("post_result_parameter_search") is False, "post-result search")
    total_rejected = int(payload.pop("total_evidence_split_count"))
    payload["schema"] = "ORBITTRACE_M2D_GREEDY_ANTICHAIN_V1_PRETRUTH"
    payload["scientific_role"] = "TARGET_EXCLUDED_GMN_GREEDY_M2D_ANTICHAIN_FROZEN_BEFORE_TRUTH"
    payload["configuration"] = {
        "radius": 1.0,
        "minimum_support": 4,
        "packing_rule": "score_all_reportable_hierarchy_nodes_by_exact_M2D_desc_then_family_hash; greedily_accept_iff_disjoint_from_higher_ranked_accepts",
        "ranking": ["internal_2d_mass_desc", "family_hash_asc"],
        "new_tuned_parameters": [],
    }
    payload["total_overlap_rejection_count"] = total_rejected
    payload["total_rejected_broad_ancestor_count"] = sum(int(s["cut_summary"].get("rejected_broad_ancestor_count", 0)) for s in payload["subsets"])
    payload["total_rejected_narrow_descendant_count"] = sum(int(s["cut_summary"].get("rejected_narrow_descendant_count", 0)) for s in payload["subsets"])
    output_path.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": "GREEDY_M2D_ANTICHAIN_PRETRUTH_SEALED",
        "overlap_rejections": payload["total_overlap_rejection_count"],
        "rejected_broad_ancestors": payload["total_rejected_broad_ancestor_count"],
        "rejected_narrow_descendants": payload["total_rejected_narrow_descendant_count"],
        "global_size_summary": payload["global_size_summary"],
    }, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
