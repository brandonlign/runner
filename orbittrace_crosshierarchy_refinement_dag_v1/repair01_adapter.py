#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import sys

FROZEN_RUNNER_GIT_BLOB = "4a45d8ab4b2237ddcbc4e1d0bf0f8a01dba15bf0"
RAW_SUPPORT_CUT_PRELABEL_SHA256 = "4529eadd9ff93aae057f0a6fd5e0dd923f2300b7c6e01b74a0b7638e22da6de6"
OLD_PARETO_PRELABEL_SHA256 = "5752ef8b36a5d317455e649723c26692fe2636262dc6d74befbe2ffb95945310"


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def replace_once(src: str, old: str, new: str, label: str) -> str:
    count = src.count(old)
    if count != 1:
        raise RuntimeError(f"repair01 source mismatch for {label}: expected 1 occurrence, got {count}")
    return src.replace(old, new, 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-runner", type=Path, required=True)
    ap.add_argument("--patched-runner", type=Path, required=True)
    ap.add_argument("remainder", nargs=argparse.REMAINDER)
    a = ap.parse_args()

    raw = a.source_runner.read_bytes()
    actual_blob = git_blob_sha(raw)
    if actual_blob != FROZEN_RUNNER_GIT_BLOB:
        raise RuntimeError(f"frozen runner blob changed: {actual_blob}")
    src = raw.decode("utf-8")

    # Technical Repair 01: provenance/rebind interface only. Every replacement is
    # exact-count audited against the frozen pre-result runner. No DAG, metric,
    # hierarchy, panel, gate, firewall, or interpretation code is edited here.
    src = replace_once(
        src,
        f'PARETO_PRELABEL_SHA256 = "{OLD_PARETO_PRELABEL_SHA256}"',
        f'PARETO_PRELABEL_SHA256 = "{RAW_SUPPORT_CUT_PRELABEL_SHA256}"',
        "immutable parent prelabel sha",
    )
    src = replace_once(
        src,
        'req(sha256_file(a.pareto_prelabel) == PARETO_PRELABEL_SHA256, "sealed Pareto prelabel changed")',
        'req(sha256_file(a.pareto_prelabel) == PARETO_PRELABEL_SHA256, "sealed raw support-cut prelabel changed")',
        "parent prelabel hash message",
    )
    src = replace_once(
        src,
        'req(not bool(sealed.get("shower_truth_used", False)), "sealed Pareto prelabel unexpectedly used truth")',
        'req(not bool(sealed.get("shower_truth_used", False)), "sealed raw support-cut prelabel unexpectedly used truth")',
        "parent prelabel firewall message",
    )
    src = replace_once(
        src,
        'sealed_topo = list(old["source_overlap_consensus_candidates"])',
        'sealed_topo = list(old["successor_candidates"])',
        "raw topomodal membership field",
    )
    src = replace_once(
        src,
        'same_count = int(old["event_count"]) == len(ids)',
        'same_count = int(old["events_total"]) == len(ids)',
        "raw panel count field",
    )
    src = replace_once(
        src,
        'old_universe = set(str(z) for y in YEARS for z in old["annual_event_ids"][str(y)])\n                same_universe = old_universe == set(ids)',
        'same_universe = str(old["event_universe_sha256"]) == universe_hash(ids)',
        "raw panel universe field",
    )

    # Assert the frozen scientific contract remains present after the adapter.
    required_unchanged = (
        'DENOMINATORS = (64, 128, 1024)',
        'BUCKETS = (0, 1, 2, 3)',
        'SALT = "ORBITTRACE_SCALE_STRESS_V1|"',
        'edge_members.setdefault((i, j), set()).add(eid)',
        'joint = topo_union.intersection(recurrent_union)',
        '"pooled_mean_atoms_gt_recurrent": means["atoms"] > means["recurrent"]',
        '"pooled_mean_atoms_gt_topomodal": means["atoms"] > means["topomodal"]',
        '"median_atoms_gt_recurrent": medians["atoms"] > medians["recurrent"]',
        '"median_atoms_gt_topomodal": medians["atoms"] > medians["topomodal"]',
        '"atoms_strictly_beat_both_at_least_5_of_8": strict_both >= 5',
        '"shower_truth_used": False',
        '"target_information_access": False',
        '"target_region_events_accessed": False',
        '"external_scientific_access": False',
        '"post_result_parameter_search": False',
    )
    for token in required_unchanged:
        if token not in src:
            raise RuntimeError(f"repair01 scientific-contract token missing: {token}")

    a.patched_runner.parent.mkdir(parents=True, exist_ok=True)
    a.patched_runner.write_text(src)
    patched_sha = hashlib.sha256(src.encode()).hexdigest()
    print(f"repair01_frozen_runner_git_blob={actual_blob}", flush=True)
    print(f"repair01_patched_runner_sha256={patched_sha}", flush=True)
    print(f"repair01_parent_prelabel_sha256={RAW_SUPPORT_CUT_PRELABEL_SHA256}", flush=True)

    remainder = list(a.remainder)
    if remainder and remainder[0] == "--":
        remainder = remainder[1:]
    if not remainder:
        raise RuntimeError("repair01 missing frozen runner arguments")

    os.execv(sys.executable, [sys.executable, str(a.patched_runner), *remainder])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
