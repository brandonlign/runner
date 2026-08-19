#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

CANONICAL_ZIP_SHA256 = "716b70313465d5df4bfb092a85a81680e6f618606b71e25470c63c480b6449f5"
NESTED_BUNDLE_BASENAME = "GhostStream_Expert_Review_Bundle.zip"
CANONICAL_MEMBER_PATH = "reconstruction/exact_downstream/primary/april_candidate_members.csv"
EXPECTED_ALL = {2019: 1, 2020: 4, 2021: 1, 2022: 10, 2023: 8, 2024: 14, 2025: 34, 2026: 29}
EXPECTED_PARENT = {"rank": 82, "member_count": 1708, "family_hash": "936d785f4c50b5dae659"}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(x: bytes) -> str:
    return hashlib.sha256(x).hexdigest()


def canonical(path: Path) -> dict[int, set[str]]:
    outer = path.read_bytes()
    req(sha(outer) == CANONICAL_ZIP_SHA256, "canonical outer ZIP changed")
    with zipfile.ZipFile(io.BytesIO(outer)) as oz:
        hits = [n for n in oz.namelist() if Path(n).name == NESTED_BUNDLE_BASENAME]
        req(len(hits) == 1, "nested expert bundle changed")
        nested = oz.read(hits[0])
    with zipfile.ZipFile(io.BytesIO(nested)) as nz:
        req(CANONICAL_MEMBER_PATH in nz.namelist(), "canonical member CSV missing")
        text = nz.read(CANONICAL_MEMBER_PATH).decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    parsed = [(str(r["unique_trajectory_identifier"]).strip(), int(r["year"])) for r in rows]
    req(len({eid for eid, _ in parsed}) == len(parsed), "canonical IDs not unique")
    req(dict(sorted(Counter(y for _, y in parsed).items())) == EXPECTED_ALL, "canonical historical counts changed")
    return {y: {eid for eid, yy in parsed if yy == y} for y in (2022, 2023)}


def metric(row: dict[str, Any], truth: dict[int, set[str]]) -> dict[str, Any]:
    ids = set(map(str, row["event_ids"]))
    o22 = sorted(ids & truth[2022]); o23 = sorted(ids & truth[2023])
    n = len(ids); hit = len(o22) + len(o23)
    return {
        "family_hash": str(row["family_hash"]),
        "member_count": n,
        "overlap_2022": o22,
        "overlap_2023": o23,
        "overlap_total": hit,
        "precision": hit / n if n else 0.0,
        "recall": hit / 18.0,
        "f1": (2.0 * hit / n * hit / 18.0 / (hit / n + hit / 18.0)) if hit and n else 0.0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pretruth", type=Path, required=True)
    ap.add_argument("--expected-pretruth-sha", required=True)
    ap.add_argument("--canonical-zip", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args(); a.output.mkdir(parents=True, exist_ok=True)

    raw = a.pretruth.read_bytes()
    req(sha(raw) == a.expected_pretruth_sha, "sealed NCA characterization pretruth changed")
    pre = json.loads(raw)
    req(pre.get("schema") == "ORBITTRACE_NCA_ORBITTRACE_CHARACTERIZATION_V1_PRETRUTH", "wrong pretruth schema")
    req(pre.get("canonical_target_ids_accessed") is False and pre.get("target_overlap_used_for_construction") is False, "pretruth target firewall changed")
    req(pre.get("post_result_parameter_search") is False and pre.get("configuration", {}).get("new_tuned_parameters") == [], "pretruth search/tuning changed")
    p = pre["parent"]
    req(int(p["rank"]) == EXPECTED_PARENT["rank"] and int(p["member_count"]) == EXPECTED_PARENT["member_count"] and str(p["family_hash"]) == EXPECTED_PARENT["family_hash"], "parent identity changed")
    req(pre["nca_branches"] and str(pre["nca_branches"][0]["family_hash"]) == str(pre["primary_branch_family_hash"]), "primary branch identity invalid")

    truth = canonical(a.canonical_zip)
    req(len(truth[2022]) == 10 and len(truth[2023]) == 8, "2022/2023 canonical counts changed")
    parent_metric = metric(p, truth)
    req(parent_metric["overlap_total"] == 18 and len(parent_metric["overlap_2022"]) == 10 and len(parent_metric["overlap_2023"]) == 8, "known parent replay overlap changed")

    seeds = []
    for i, row in enumerate(pre["bwm_seeds"], 1):
        m = metric(row, truth); m["seed_rank_within_parent"] = i; seeds.append(m)
    branches = []
    branch_sets: list[set[str]] = []
    for row in pre["nca_branches"]:
        m = metric(row, truth)
        m["branch_rank_within_parent"] = int(row["branch_rank_within_parent"])
        m["seed_family_hash"] = str(row["cmr_seed_family_hash"])
        m["internal_2d_mass"] = float(row["internal_2d_mass"])
        branches.append(m); branch_sets.append(set(map(str, row["event_ids"])))
    primary = branches[0]
    union_ids = set().union(*branch_sets) if branch_sets else set()
    union_row = {"family_hash": "ALL_FROZEN_NCA_BRANCH_UNION", "event_ids": sorted(union_ids)}
    union_metric = metric(union_row, truth)
    oracle = sorted(branches, key=lambda x: (-int(x["overlap_total"]), -float(x["precision"]), int(x["branch_rank_within_parent"])))[0]

    concentration = {
        "primary_precision_multiplier_vs_parent": primary["precision"] / parent_metric["precision"] if parent_metric["precision"] else None,
        "primary_member_reduction": parent_metric["member_count"] - primary["member_count"],
        "primary_member_reduction_fraction": (parent_metric["member_count"] - primary["member_count"]) / parent_metric["member_count"],
        "primary_preserves_all_18": primary["overlap_total"] == 18,
        "all_branches_union_preserves_all_18": union_metric["overlap_total"] == 18,
        "any_single_frozen_branch_preserves_all_18": any(x["overlap_total"] == 18 for x in branches),
    }
    result = {
        "schema": "ORBITTRACE_NCA_ORBITTRACE_CHARACTERIZATION_V1_REVEAL",
        "scientific_role": "POST_REVEAL_DESCRIPTIVE_NCA_TARGET_CONCENTRATION_ONLY",
        "pretruth_sha256": a.expected_pretruth_sha,
        "canonical_zip_sha256": CANONICAL_ZIP_SHA256,
        "parent": parent_metric,
        "bwm_seeds": seeds,
        "nca_branches": branches,
        "deterministic_primary_branch": primary,
        "all_frozen_branches_union": union_metric,
        "oracle_best_branch_post_reveal_descriptive_only": oracle,
        "concentration": concentration,
        "method_changed_after_reveal": False,
        "branch_selected_after_reveal_for_method": False,
        "interpretation_boundary": "Reveal-only exact-ID characterization of branches sealed before canonical access. The oracle row is descriptive only. This result cannot promote a child branch, repair failed ECT/EMCU benchmark gates, create a new blind rediscovery claim, or establish cross-survey generalization.",
    }
    outj = a.output / "NCA_ORBITTRACE_CHARACTERIZATION_V1_REVEAL.json"
    outj.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    lines = [
        "# NCA OrbitTrace characterization v1 — reveal-only result", "",
        f"- unchanged parent: {parent_metric['overlap_total']}/18 exact IDs in {parent_metric['member_count']:,} members (precision {parent_metric['precision']:.6f})",
        f"- deterministic primary NCA branch: {primary['overlap_total']}/18 in {primary['member_count']:,} members (precision {primary['precision']:.6f}, recall {primary['recall']:.6f})",
        f"- all frozen NCA branches union: {union_metric['overlap_total']}/18 in {union_metric['member_count']:,} members (precision {union_metric['precision']:.6f})",
        f"- frozen branch count: {len(branches)}; BWM seed count: {len(seeds)}",
        f"- post-reveal oracle branch (descriptive only): rank {oracle['branch_rank_within_parent']}, {oracle['overlap_total']}/18 in {oracle['member_count']:,} members (precision {oracle['precision']:.6f})",
        "", "No branch was changed, reranked by target overlap, or promoted after reveal. This is characterization only.",
    ]
    (a.output / "NCA_ORBITTRACE_CHARACTERIZATION_V1_REVEAL.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
