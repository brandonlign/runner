#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

EXPECTED_BASELINE_GZIP_SHA256 = "6d72b0f9558b89228953dd73b3760c61df039b713f233473079ae4fac563a100"
EXPECTED_BASELINE_INNER_SHA256 = "7ff3b13bc45e19b4b886453b4d8cc3b4f18090bf8a2291e39850540fd69b5e53"
EXPECTED_CANDIDATES = 8469
EXPECTED_CANONICAL = {2022: 10, 2023: 8, 2024: 14, 2025: 34, 2026: 29}
TARGET_TOTAL = 18
MAX_RANK = 100
MIN_2022 = 4
MIN_2023 = 4
MIN_TOTAL = 8
MIN_CLEAN_F1_EXCLUSIVE = 0.5


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def canonical_rows(path: Path) -> tuple[list[tuple[str, int]], str, str | None]:
    with zipfile.ZipFile(path) as z:
        hits = [n for n in z.namelist() if Path(n).name == "april_candidate_members.csv"]
        req(len(hits) == 1, f"canonical csv count {hits}")
        text = z.read(hits[0]).decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    req(bool(rows), "empty canonical csv")
    fields = list(rows[0])
    bynorm = {norm(x): x for x in fields}
    idcol = None
    for key in ("eventid", "event", "trajectoryid", "id"):
        if key in bynorm:
            idcol = bynorm[key]
            break
    if idcol is None:
        for field in fields:
            name = norm(field)
            if "id" in name and ("event" in name or "trajectory" in name):
                idcol = field
                break
    req(idcol is not None, f"no canonical ID column: {fields}")
    yearcol = next((f for f in fields if norm(f) in ("year", "yr")), None)

    out: list[tuple[str, int]] = []
    for row in rows:
        eid = str(row[idcol]).strip()
        req(bool(eid), "empty canonical ID")
        if yearcol is not None and str(row[yearcol]).strip():
            year = int(float(row[yearcol]))
        else:
            match = re.search(r"20(22|23|24|25|26)", eid)
            req(match is not None, f"cannot derive canonical year from {eid}")
            year = int(match.group(0))
        out.append((eid, year))

    counts = Counter(year for _, year in out)
    req(dict(sorted(counts.items())) == EXPECTED_CANONICAL, f"canonical counts changed: {dict(counts)}")
    req(len({eid for eid, _ in out}) == 95, "canonical IDs not unique")
    return out, idcol, yearcol


def quality(ids: set[str], t22: set[str], t23: set[str]) -> dict[str, Any]:
    o22 = sorted(ids & t22)
    o23 = sorted(ids & t23)
    overlap = len(o22) + len(o23)
    precision = overlap / len(ids) if ids else 0.0
    recall = overlap / TARGET_TOTAL
    f1 = (2.0 * precision * recall / (precision + recall)) if precision + recall else 0.0
    return {
        "overlap_2022_ids": o22,
        "overlap_2023_ids": o23,
        "overlap_2022": len(o22),
        "overlap_2023": len(o23),
        "overlap_total": overlap,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage-a", type=Path, required=True)
    ap.add_argument("--stage-a-sha256", type=Path, required=True)
    ap.add_argument("--canonical-zip", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    recorded = a.stage_a_sha256.read_text().strip().split()[0]
    actual = sha256(a.stage_a)
    req(recorded == actual, f"Stage-A digest changed: recorded={recorded} actual={actual}")

    pre = json.loads(a.stage_a.read_text())
    req(pre["schema"] == "ORBITTRACE_M2D_FIXED4_DRIFT_HALO_V1_FINAL_TARGET_PRETRUTH", "wrong Stage-A schema")
    req(pre["scientific_role"] == "COMPLETE_ALREADY_BLIND_M2D_RANKING_WITH_FROZEN_FIXED4_SEEDED_95PCT_OAS_DRIFT_HALOS_BEFORE_TARGET_REFERENCE_ACCESS", "wrong Stage-A role")
    req(pre["baseline_pretruth_gzip_sha256"] == EXPECTED_BASELINE_GZIP_SHA256, "wrong baseline gzip")
    req(pre["baseline_pretruth_inner_sha256"] == EXPECTED_BASELINE_INNER_SHA256, "wrong baseline inner payload")
    req(pre["candidate_count"] == len(pre["halos"]) == EXPECTED_CANDIDATES, "Stage-A candidate count changed")
    req([int(r["rank"]) for r in pre["halos"]] == list(range(1, EXPECTED_CANDIDATES + 1)), "Stage-A order changed")
    req(pre["parent_rank_changed"] is False and pre["parent_membership_changed"] is False, "parent discovery changed")
    req(pre["target_reference_access"] is False, "target reference accessed before Stage-A seal")
    req(pre["target_information_used"] is False, "target information used before Stage-A seal")
    req(pre["target_coordinates_accessed"] is False, "target coordinates accessed before Stage-A seal")
    req(pre["canonical_target_ids_accessed"] is False, "canonical IDs accessed before Stage-A seal")
    req(pre["prior_target_reveal_artifact_accessed"] is False, "prior target reveal accessed before Stage-A seal")
    req(pre["target_aware_parent_selection"] is False, "target-aware parent choice used")
    req(pre["reranking_used"] is False and pre["family_merge_used"] is False, "rerank/merge used before reveal")
    req(pre["post_result_parameter_search"] is False, "post-result parameter search used")

    canon, idcol, yearcol = canonical_rows(a.canonical_zip)
    t22 = {eid for eid, year in canon if year == 2022}
    t23 = {eid for eid, year in canon if year == 2023}
    req(len(t22) == 10 and len(t23) == 8, "wrong 2022/2023 target counts")

    evaluated: list[dict[str, Any]] = []
    for frozen in pre["halos"]:
        rank = int(frozen["rank"])
        parent_ids = set(map(str, frozen["parent_event_ids"]))
        seed_ids = set(map(str, frozen["seed_event_ids"]))
        halo_ids = set(map(str, frozen["halo_event_ids"]))
        req(len(parent_ids) == int(frozen["parent_member_count"]), f"parent size changed rank {rank}")
        req(len(seed_ids) == int(frozen["seed_member_count"]), f"seed size changed rank {rank}")
        req(len(halo_ids) == int(frozen["halo_member_count"]), f"halo size changed rank {rank}")
        req(seed_ids.issubset(halo_ids) and halo_ids.issubset(parent_ids), f"membership containment changed rank {rank}")

        parent_q = quality(parent_ids, t22, t23)
        seed_q = quality(seed_ids, t22, t23)
        halo_q = quality(halo_ids, t22, t23)
        support_gate = (
            halo_q["overlap_2022"] >= MIN_2022
            and halo_q["overlap_2023"] >= MIN_2023
            and halo_q["overlap_total"] >= MIN_TOTAL
        )
        rank_gate = rank <= MAX_RANK
        clean_gate = rank_gate and support_gate and halo_q["f1"] > MIN_CLEAN_F1_EXCLUSIVE
        evaluated.append(
            {
                "rank": rank,
                "family_hash": str(frozen["family_hash"]),
                "parent_member_count": int(frozen["parent_member_count"]),
                "seed_member_count": int(frozen["seed_member_count"]),
                "halo_member_count": int(frozen["halo_member_count"]),
                "parent": parent_q,
                "seed": seed_q,
                "halo": halo_q,
                "rank_gate": rank_gate,
                "support_gate": support_gate,
                "clean_f1_gate": halo_q["f1"] > MIN_CLEAN_F1_EXCLUSIVE,
                "clean_success_gate": clean_gate,
            }
        )

    clean = [r for r in evaluated if r["clean_success_gate"]]
    partial = [r for r in evaluated if r["rank_gate"] and r["support_gate"]]
    clean.sort(key=lambda r: r["rank"])
    partial.sort(key=lambda r: r["rank"])

    if clean:
        verdict = "CLEAN_M2D_FIXED4_DRIFT_HALO_ORBITTRACE_REDISCOVERY"
        selected = clean[0]
    elif partial:
        verdict = "PARTIAL_M2D_FIXED4_DRIFT_HALO_ORBITTRACE_RECOVERY"
        selected = partial[0]
    else:
        verdict = "NO_M2D_FIXED4_DRIFT_HALO_ORBITTRACE_RECOVERY"
        selected = None

    result = {
        "verdict": verdict,
        "stage_a_sha256": actual,
        "baseline_pretruth_gzip_sha256": EXPECTED_BASELINE_GZIP_SHA256,
        "baseline_pretruth_inner_sha256": EXPECTED_BASELINE_INNER_SHA256,
        "candidate_count": EXPECTED_CANDIDATES,
        "canonical_column": idcol,
        "canonical_year_column": yearcol,
        "target_counts": {"2022": len(t22), "2023": len(t23), "total": TARGET_TOTAL},
        "success_rule": {
            "maximum_original_parent_rank": MAX_RANK,
            "minimum_exact_2022_ids": MIN_2022,
            "minimum_exact_2023_ids": MIN_2023,
            "minimum_exact_total_ids": MIN_TOTAL,
            "exact_target_f1_strictly_greater_than": MIN_CLEAN_F1_EXCLUSIVE,
        },
        "first_original_rank_with_support_gate": partial[0]["rank"] if partial else None,
        "first_original_rank_with_clean_success_gate": clean[0]["rank"] if clean else None,
        "selected_candidate": selected,
        "evaluated": evaluated,
        "reveal_operation": "exact trajectory-ID set intersection only against already-frozen parent/seed/halo memberships",
        "coordinates_used": False,
        "activity_interval_used": False,
        "orbit_matching_used": False,
        "nearest_target_matching_used": False,
        "membership_recomputed_after_reveal": False,
        "parent_switched_after_reveal": False,
        "family_merge_used": False,
        "reranking_used": False,
        "parameter_tuning_after_reveal": False,
        "second_reveal_authorized": False,
    }
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")

    lines = [
        "# M2D fixed4-seeded drift halo v1 — final blind OrbitTrace exact-ID reveal",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        f"- Stage-A frozen halo SHA-256: `{actual}`",
        f"- complete frozen candidate count: **{EXPECTED_CANDIDATES:,}**",
        f"- first original rank meeting annual/total support: **{result['first_original_rank_with_support_gate']}**",
        f"- first original rank meeting clean success: **{result['first_original_rank_with_clean_success_gate']}**",
    ]
    if selected is not None:
        h = selected["halo"]
        p = selected["parent"]
        s = selected["seed"]
        lines.extend(
            [
                f"- selected original M2D parent rank: **{selected['rank']}**",
                f"- parent / seed / halo members: **{selected['parent_member_count']} / {selected['seed_member_count']} / {selected['halo_member_count']}**",
                f"- halo exact 2022 overlap: **{h['overlap_2022']}/10**",
                f"- halo exact 2023 overlap: **{h['overlap_2023']}/8**",
                f"- halo total exact overlap: **{h['overlap_total']}/18**",
                f"- halo precision / recall / F1: **{h['precision']:.6f} / {h['recall']:.6f} / {h['f1']:.6f}**",
                f"- parent exact overlap / F1: **{p['overlap_total']}/18 / {p['f1']:.6f}**",
                f"- fixed4 seed exact overlap / F1: **{s['overlap_total']}/18 / {s['f1']:.6f}**",
            ]
        )
    lines.extend(
        [
            "",
            "All 8,469 parent/seed/model/covariance/event-score/halo mappings were sealed before the canonical target archive was opened. Reveal used exact trajectory-ID intersection only; no reranking, merging, target-aware trimming, covariance/confidence/scale change, or membership recomputation was permitted.",
        ]
    )
    (a.output.parent / "FINAL_BLIND_TARGET_REVEAL.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
