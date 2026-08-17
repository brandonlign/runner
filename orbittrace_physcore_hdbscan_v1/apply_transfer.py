#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

FROZEN_PHYSCORE_GIT_BLOB_SHA1 = "410a5ebe1ffdcf88f1530a2eb61f6342ca3639dd"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha1(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()


def dump(path: Path, value: Any) -> str:
    raw = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def load_frozen(path: Path) -> Any:
    require(git_blob_sha1(path) == FROZEN_PHYSCORE_GIT_BLOB_SHA1, "frozen PhysCore source identity changed")
    spec = importlib.util.spec_from_file_location("frozen_physcore_hdbscan_v1", path)
    require(spec is not None and spec.loader is not None, "cannot import frozen PhysCore")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", choices=("sugar", "hdbscan", "dsh"), required=True)
    ap.add_argument("--year", type=int, choices=(2013, 2014), required=True)
    ap.add_argument("--rows", type=Path, required=True)
    ap.add_argument("--hdbscan-dir", type=Path, required=True)
    ap.add_argument("--frozen-source", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    frozen = load_frozen(a.frozen_source)
    frozen_source_sha256 = sha(a.frozen_source)
    rows = json.loads(a.rows.read_text())
    require(isinstance(rows, list) and rows, "empty rows")
    require(all(not (frozen.BLIND[0] <= float(r["sol"]) <= frozen.BLIND[1]) for r in rows), "protected row present")
    require(all("shower" not in r and "truth" not in r for r in rows), "truth field present")
    by = {str(r["id"]): r for r in rows}
    require(len(by) == len(rows), "duplicate row IDs")

    hp = a.hdbscan_dir / "comparator_primary_output.json"
    hm = a.hdbscan_dir / "comparator_source_manifest.json"
    parent = json.loads(hp.read_text())
    families = parent["families"]
    require(int(parent["retained_family_count"]) == len(families) and families, "invalid HDBSCAN parent")

    out: list[dict[str, Any]] = []
    audits: list[dict[str, Any]] = []
    for rank, family in enumerate(families, 1):
        parent_ids = [str(x) for x in family["member_ids"]]
        require(len(parent_ids) == len(set(parent_ids)) and set(parent_ids) <= set(by), "bad parent membership")
        parent_rows = [by[x] for x in parent_ids]
        active = frozen.physcore(parent_rows)
        refined_ids = sorted(parent_ids[i] for i in active)
        fallback = len(refined_ids) < frozen.MIN_SUPPORT_INCLUDING_SELF
        ids = sorted(parent_ids) if fallback else refined_ids
        require(len(ids) >= frozen.MIN_SUPPORT_INCLUDING_SELF and set(ids) <= set(parent_ids), "invalid refined membership")
        out.append({
            "family_id": f"PCH{a.year}_{rank:03d}",
            "rank": rank,
            "parent_family_id": str(family["family_id"]),
            "event_ids": ids,
            "member_count": len(ids),
            "parent_member_count": len(parent_ids),
            "fallback_to_parent": fallback,
        })
        audits.append({
            "parent_family_id": str(family["family_id"]),
            "parent_member_count": len(parent_ids),
            "refined_member_count": len(ids),
            "retained_fraction": len(ids) / len(parent_ids),
            "fallback_to_parent": fallback,
        })

    require(any(x["refined_member_count"] < x["parent_member_count"] for x in audits), "no strict refinement")
    payload = {
        "schema": "ORBITTRACE_PHYSCORE_HDBSCAN_V1_MATCHED_TRANSFER_PRETRUTH",
        "method": "PhysCore-HDBSCAN v1",
        "pair": a.pair,
        "year": a.year,
        "family_count": len(out),
        "families": out,
        "audit": audits,
        "configuration": {
            "h_sol": frozen.H_SOL,
            "h_rad": frozen.H_RAD,
            "h_logv": frozen.H_LOGV,
            "radius": frozen.RADIUS,
            "min_support_including_self": frozen.MIN_SUPPORT_INCLUDING_SELF,
            "peeling": "maximal_3_core",
            "split_components": False,
            "fallback": "parent_if_core_lt_4",
        },
        "frozen_physcore_source_git_blob_sha1": FROZEN_PHYSCORE_GIT_BLOB_SHA1,
        "frozen_physcore_source_sha256": frozen_source_sha256,
        "row_json_sha256": sha(a.rows),
        "hdbscan_primary_output_sha256": sha(hp),
        "hdbscan_source_manifest_sha256": sha(hm),
        "truth_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    primary_sha = dump(a.output / "physcore_primary_output.json", payload)
    manifest = {
        "schema": "ORBITTRACE_PHYSCORE_HDBSCAN_V1_MATCHED_TRANSFER_MANIFEST",
        "pair": a.pair,
        "year": a.year,
        "candidate_output_sha256": primary_sha,
        "row_json_sha256": sha(a.rows),
        "hdbscan_primary_output_sha256": sha(hp),
        "hdbscan_source_manifest_sha256": sha(hm),
        "frozen_physcore_source_git_blob_sha1": FROZEN_PHYSCORE_GIT_BLOB_SHA1,
        "frozen_physcore_source_sha256": frozen_source_sha256,
        "truth_accessed": False,
        "target_information_access": False,
        "post_result_parameter_search": False,
    }
    manifest_sha = dump(a.output / "physcore_source_manifest.json", manifest)
    print(json.dumps({
        "pair": a.pair,
        "year": a.year,
        "parent_families": len(families),
        "strict_refinements": sum(x["refined_member_count"] < x["parent_member_count"] for x in audits),
        "frozen_source_sha256": frozen_source_sha256,
        "candidate_sha256": primary_sha,
        "manifest_sha256": manifest_sha,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
