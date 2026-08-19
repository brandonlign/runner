#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import zipfile
from collections import Counter
from pathlib import Path

PRETRUTH_GZIP_SHA256 = "b1beb3dac03579b2ca2a0f85a2e65213e3a4826dfe0d8f038856f6b227319765"
PRETRUTH_INNER_SHA256 = "75dec41919072681a423d3c37d4565ca5ee19dccf86900b3b39ef5d30153ca0b"
CANONICAL_ZIP_SHA256 = "716b70313465d5df4bfb092a85a81680e6f618606b71e25470c63c480b6449f5"
EXPECTED_CANDIDATES = 8884
EXPECTED_ALL = {2019: 1, 2020: 4, 2021: 1, 2022: 10, 2023: 8, 2024: 14, 2025: 34, 2026: 29}
EXPECTED_CANONICAL = {2022: 10, 2023: 8, 2024: 14, 2025: 34, 2026: 29}
NESTED_BUNDLE_BASENAME = "GhostStream_Expert_Review_Bundle.zip"
CANONICAL_MEMBER_PATH = "reconstruction/exact_downstream/primary/april_candidate_members.csv"
OLD = {"rank": 84, "overlap_2022": 10, "overlap_2023": 8, "overlap_total": 18, "member_count": 1814, "precision": 18.0 / 1814.0}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_rows(path: Path) -> list[tuple[str, int]]:
    outer = path.read_bytes()
    req(sha256(outer) == CANONICAL_ZIP_SHA256, "canonical outer ZIP SHA changed")
    with zipfile.ZipFile(io.BytesIO(outer)) as oz:
        nested_hits = [n for n in oz.namelist() if Path(n).name == NESTED_BUNDLE_BASENAME]
        req(len(nested_hits) == 1, f"nested expert bundle count {nested_hits}")
        nested = oz.read(nested_hits[0])
    with zipfile.ZipFile(io.BytesIO(nested)) as nz:
        req(CANONICAL_MEMBER_PATH in nz.namelist(), "canonical member CSV missing from nested expert bundle")
        text = nz.read(CANONICAL_MEMBER_PATH).decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    req(bool(rows), "empty canonical member CSV")
    req("year" in rows[0] and "unique_trajectory_identifier" in rows[0], f"unexpected canonical columns {list(rows[0])}")
    parsed = [(str(r["unique_trajectory_identifier"]).strip(), int(r["year"])) for r in rows]
    req(all(eid for eid, _ in parsed), "empty trajectory ID")
    req(len({eid for eid, _ in parsed}) == len(parsed), "canonical historical IDs not unique")
    counts = Counter(y for _, y in parsed)
    req(dict(sorted(counts.items())) == EXPECTED_ALL, f"historical canonical counts changed: {dict(sorted(counts.items()))}")
    canonical = [(eid, y) for eid, y in parsed if y in EXPECTED_CANONICAL]
    ccounts = Counter(y for _, y in canonical)
    req(dict(sorted(ccounts.items())) == EXPECTED_CANONICAL, f"2022-2026 canonical counts changed: {dict(sorted(ccounts.items()))}")
    req(len(canonical) == 95 and len({eid for eid, _ in canonical}) == 95, "canonical 2022-2026 ID count changed")
    return canonical


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pretruth", type=Path, required=True)
    ap.add_argument("--canonical-zip", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    pre_gz = a.pretruth.read_bytes()
    req(sha256(pre_gz) == PRETRUTH_GZIP_SHA256, "sealed support-pruned replay gzip SHA changed")
    pre_raw = gzip.decompress(pre_gz)
    req(sha256(pre_raw) == PRETRUTH_INNER_SHA256, "sealed support-pruned replay inner SHA changed")
    pre = json.loads(pre_raw)
    req(pre["schema"] == "ORBITTRACE_M2D_BLIND_REDISCOVERY_V1_PRETRUTH", "wrong pretruth schema")
    req(pre["scientific_role"] == "TARGET_FREE_COMPLETE_M2D_RANKING_BEFORE_ORBITTRACE_REVEAL", "wrong pretruth scientific role")
    req(pre["verdict"] == "BLIND_M2D_SCAN_FROZEN_AWAITING_SEPARATE_REVEAL", "pretruth was not frozen")
    req(pre["replay_variant"] == "PROMOTED_SUPPORT_PRUNED_CUT_V1_POST_PROMOTION_BLIND_PROTOCOL_REPLAY", "wrong replay variant")
    req(pre["configuration"]["years"] == [2022, 2023], "wrong scan years")
    req(pre["configuration"]["target_interval_exclusion"] is None, "target interval excluded in scan")
    req(pre["configuration"]["cut_rule"] == "recurse_reportable_child_discard_immediate_subsupport_sibling_else_parent_when_both_children_subsupport", "cut rule changed")
    req(pre["shower_truth_used"] is False, "shower truth used before freeze")
    req(pre["orbittrace_target_information_access"] is False, "OrbitTrace target info used before freeze")
    req(pre["orbittrace_canonical_members_access"] is False, "canonical members used before freeze")
    req(pre["prior_orbittrace_reveal_access"] is False, "prior reveal used before freeze")
    req(pre["post_result_parameter_search"] is False and pre["post_promotion_parameter_search"] is False, "post-result search recorded")
    req(int(pre["candidate_count"]) == EXPECTED_CANDIDATES == len(pre["candidates"]), "sealed candidate count changed")
    req([int(c["rank"]) for c in pre["candidates"]] == list(range(1, EXPECTED_CANDIDATES + 1)), "sealed rank order invalid")

    canonical = canonical_rows(a.canonical_zip)
    byyear = {y: {eid for eid, yy in canonical if yy == y} for y in (2022, 2023)}
    req(len(byyear[2022]) == 10 and len(byyear[2023]) == 8, "2022/2023 target ID count changed")

    evaluated = []
    for c in pre["candidates"]:
        ids = set(map(str, c["event_ids"]))
        o22 = sorted(ids & byyear[2022])
        o23 = sorted(ids & byyear[2023])
        overlap = len(o22) + len(o23)
        evaluated.append({
            "rank": int(c["rank"]),
            "family_hash": str(c["family_hash"]),
            "member_count": int(c["member_count"]),
            "m2d": float(c["internal_2d_mass"]),
            "modal_contrast": float(c["modal_contrast"]),
            "overlap_2022": o22,
            "overlap_2023": o23,
            "overlap_total": overlap,
            "precision": overlap / len(ids) if ids else 0.0,
            "recall": overlap / 18.0,
            "gate": len(o22) >= 4 and len(o23) >= 4 and overlap >= 8,
        })

    passing = sorted((x for x in evaluated if x["gate"]), key=lambda x: x["rank"])
    best = sorted(evaluated, key=lambda x: (-x["overlap_total"], -min(len(x["overlap_2022"]), len(x["overlap_2023"])), x["rank"]))[0]
    if passing:
        first = passing[0]
        if first["rank"] <= 25:
            reveal_verdict = "FULL_M2D_BLIND_ORBITTRACE_REDISCOVERY"
            chosen = first
        elif first["rank"] <= 100:
            reveal_verdict = "PARTIAL_M2D_BLIND_ORBITTRACE_REDISCOVERY"
            chosen = first
        else:
            reveal_verdict = "NO_M2D_BLIND_ORBITTRACE_REDISCOVERY"
            chosen = best
    else:
        first = None
        reveal_verdict = "NO_M2D_BLIND_ORBITTRACE_REDISCOVERY"
        chosen = best

    new = {
        "rank": int(chosen["rank"]),
        "overlap_2022": len(chosen["overlap_2022"]),
        "overlap_2023": len(chosen["overlap_2023"]),
        "overlap_total": int(chosen["overlap_total"]),
        "member_count": int(chosen["member_count"]),
        "precision": float(chosen["precision"]),
        "recall": float(chosen["recall"]),
    }
    checks = {
        "preserves_all_18_exact_ids": new["overlap_total"] == 18 and new["overlap_2022"] == 10 and new["overlap_2023"] == 8,
        "remains_within_partial_rank_band": new["rank"] <= 100,
        "family_strictly_smaller_than_1814": new["member_count"] < 1814,
    }
    comparison_verdict = "IMPROVED_SUPPORT_PRUNED_ORBITTRACE_EXTRACTION" if all(checks.values()) else "NO_CLEAN_SUPPORT_PRUNED_ORBITTRACE_EXTRACTION_IMPROVEMENT"
    result = {
        "schema": "ORBITTRACE_M2D_SUPPORT_PRUNED_BLIND_REPLAY_V1_REVEAL_REPAIR",
        "verdict": comparison_verdict,
        "reveal_verdict": reveal_verdict,
        "scientific_scan_reexecuted": False,
        "reveal_repair_only": True,
        "pretruth_gzip_sha256": PRETRUTH_GZIP_SHA256,
        "pretruth_inner_sha256": PRETRUTH_INNER_SHA256,
        "canonical_zip_sha256": CANONICAL_ZIP_SHA256,
        "candidate_count": EXPECTED_CANDIDATES,
        "first_gate_passing_rank": None if first is None else int(first["rank"]),
        "chosen_family": chosen,
        "best_overlap_family": best,
        "baseline_pr1378": OLD,
        "checks": checks,
        "member_reduction": OLD["member_count"] - new["member_count"],
        "member_reduction_fraction": (OLD["member_count"] - new["member_count"]) / OLD["member_count"],
        "precision_multiplier": new["precision"] / OLD["precision"] if OLD["precision"] else None,
        "gate_definition": ">=4 exact canonical IDs in 2022 and >=4 in 2023 and >=8 total; FULL rank<=25, PARTIAL rank<=100",
        "reveal_operation": "exact unique_trajectory_identifier set intersection only",
        "canonical_source": f"{NESTED_BUNDLE_BASENAME}:{CANONICAL_MEMBER_PATH}; filtered to years 2022-2026 then reveal uses 2022-2023 only",
        "interpretation_boundary": "Post-promotion apples-to-apples replay of frozen PR1378 exact-ID protocol. Not a new pristine blind discovery claim; does not establish tuned-HDBSCAN-family superiority or cross-survey generalization.",
    }
    out_json = a.output / "SUPPORT_PRUNED_BLIND_REPLAY_REVEAL_REPAIR.json"
    out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    c = chosen
    lines = [
        "# Support-pruned M2D OrbitTrace replay — reveal-only repair",
        "",
        f"Verdict: **`{comparison_verdict}`**",
        f"Reveal classification: **`{reveal_verdict}`**",
        "",
        "The scientific scan/ranking was not rerun. This step repaired only the nested canonical-bundle reader and performed the same exact-ID intersection used by PR #1378.",
        "",
        f"- frozen candidate count: **{EXPECTED_CANDIDATES:,}**",
        f"- selected rank: **{c['rank']}** (PR #1378: **84**)",
        f"- exact 2022 overlap: **{len(c['overlap_2022'])}/10**",
        f"- exact 2023 overlap: **{len(c['overlap_2023'])}/8**",
        f"- total exact overlap: **{c['overlap_total']}/18**",
        f"- candidate members: **{c['member_count']:,}** (PR #1378: **1,814**)",
        f"- exact-ID precision: **{c['precision']:.6f}** (PR #1378: **{OLD['precision']:.6f}**)",
        f"- exact-ID recall: **{c['recall']:.6f}**",
        f"- member reduction: **{result['member_reduction']:,}** (**{100.0 * result['member_reduction_fraction']:.1f}%**)",
        f"- precision multiplier: **{result['precision_multiplier']:.2f}x**",
        f"- family hash: `{c['family_hash']}`",
        f"- M2D: `{c['m2d']:.17g}`",
        f"- sealed replay gzip SHA-256: `{PRETRUTH_GZIP_SHA256}`",
        f"- sealed replay inner SHA-256: `{PRETRUTH_INNER_SHA256}`",
        "",
        "Reveal operation: exact trajectory-ID intersection only. No coordinates, activity interval, orbital similarity, family merge, membership expansion, reranking, or parameter change was used.",
    ]
    (a.output / "SUPPORT_PRUNED_BLIND_REPLAY_REVEAL_REPAIR.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
