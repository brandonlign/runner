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

EXPECTED_ALL = {2019: 1, 2020: 4, 2021: 1, 2022: 10, 2023: 8, 2024: 14, 2025: 34, 2026: 29}
EXPECTED_CANONICAL = {2022: 10, 2023: 8, 2024: 14, 2025: 34, 2026: 29}
PRETRUTH_GZIP_SHA256 = "6d72b0f9558b89228953dd73b3760c61df039b713f233473079ae4fac563a100"
PRETRUTH_INNER_SHA256 = "7ff3b13bc45e19b4b886453b4d8cc3b4f18090bf8a2291e39850540fd69b5e53"
CANONICAL_ZIP_SHA256 = "716b70313465d5df4bfb092a85a81680e6f618606b71e25470c63c480b6449f5"
NESTED_BUNDLE_BASENAME = "GhostStream_Expert_Review_Bundle.zip"
CANONICAL_MEMBER_PATH = "reconstruction/exact_downstream/primary/april_candidate_members.csv"


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
    req(sha256(pre_gz) == PRETRUTH_GZIP_SHA256, "frozen pretruth gzip SHA changed")
    pre_raw = gzip.decompress(pre_gz)
    req(sha256(pre_raw) == PRETRUTH_INNER_SHA256, "frozen pretruth inner SHA changed")
    pre = json.loads(pre_raw)
    req(pre["schema"] == "ORBITTRACE_M2D_BLIND_REDISCOVERY_V1_PRETRUTH", "wrong pretruth schema")
    req(pre["scientific_role"] == "TARGET_FREE_COMPLETE_M2D_RANKING_BEFORE_ORBITTRACE_REVEAL", "wrong pretruth scientific role")
    req(pre["verdict"] == "BLIND_M2D_SCAN_FROZEN_AWAITING_SEPARATE_REVEAL", "pretruth was not frozen")
    req(pre["configuration"]["years"] == [2022, 2023], "wrong scan years")
    req(pre["configuration"]["target_interval_exclusion"] is None, "target interval excluded in scan")
    req(pre["shower_truth_used"] is False, "shower truth used before freeze")
    req(pre["orbittrace_target_information_access"] is False, "OrbitTrace target info used before freeze")
    req(pre["orbittrace_canonical_members_access"] is False, "canonical members used before freeze")
    req(pre["prior_orbittrace_reveal_access"] is False, "prior reveal used before freeze")
    req(pre["post_result_parameter_search"] is False, "post-result parameter search recorded")
    req(int(pre["candidate_count"]) == 8469 == len(pre["candidates"]), "frozen candidate count changed")
    req([int(c["rank"]) for c in pre["candidates"]] == list(range(1, 8470)), "frozen rank order invalid")

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
    req(bool(passing), "no gate-passing family")
    best = sorted(evaluated, key=lambda x: (-x["overlap_total"], -min(len(x["overlap_2022"]), len(x["overlap_2023"])), x["rank"]))[0]
    first = passing[0]
    if first["rank"] <= 25:
        verdict = "FULL_M2D_BLIND_ORBITTRACE_REDISCOVERY"
        chosen = first
    elif first["rank"] <= 100:
        verdict = "PARTIAL_M2D_BLIND_ORBITTRACE_REDISCOVERY"
        chosen = first
    else:
        verdict = "NO_M2D_BLIND_ORBITTRACE_REDISCOVERY"
        chosen = best

    result = {
        "schema": "ORBITTRACE_M2D_BLIND_REDISCOVERY_V1_REVEAL_REPAIR",
        "verdict": verdict,
        "scientific_scan_reexecuted": False,
        "reveal_repair_only": True,
        "pretruth_gzip_sha256": PRETRUTH_GZIP_SHA256,
        "pretruth_inner_sha256": PRETRUTH_INNER_SHA256,
        "canonical_zip_sha256": CANONICAL_ZIP_SHA256,
        "candidate_count": 8469,
        "first_gate_passing_rank": first["rank"],
        "chosen_family": chosen,
        "best_overlap_family": best,
        "gate_definition": ">=4 exact canonical IDs in 2022 and >=4 in 2023 and >=8 total; FULL rank<=25, PARTIAL rank<=100",
        "reveal_operation": "exact unique_trajectory_identifier set intersection only",
        "canonical_source": f"{NESTED_BUNDLE_BASENAME}:{CANONICAL_MEMBER_PATH}; filtered to years 2022-2026 then reveal uses 2022-2023 only",
    }
    out_json = a.output / "M2D_BLIND_REVEAL_REPAIR.json"
    out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    c = chosen
    lines = [
        "# M2D blind OrbitTrace exact-ID reveal — technical repair",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        "The M2D scan/ranking was not rerun. This reveal consumed the already-frozen pooled pretruth payload and repaired only the nested canonical-bundle reader.",
        "",
        f"- frozen candidate count: **8,469**",
        f"- selected rank: **{c['rank']}**",
        f"- exact 2022 overlap: **{len(c['overlap_2022'])}/10**",
        f"- exact 2023 overlap: **{len(c['overlap_2023'])}/8**",
        f"- total exact overlap: **{c['overlap_total']}/18**",
        f"- candidate members: **{c['member_count']}**",
        f"- precision: **{c['precision']:.6f}**",
        f"- recall: **{c['recall']:.6f}**",
        f"- family hash: `{c['family_hash']}`",
        f"- M2D: `{c['m2d']:.17g}`",
        f"- frozen pretruth gzip SHA-256: `{PRETRUTH_GZIP_SHA256}`",
        f"- frozen pretruth inner SHA-256: `{PRETRUTH_INNER_SHA256}`",
        "",
        "Reveal operation: exact trajectory-ID intersection only. No coordinates, activity interval, orbital similarity, family merge, membership expansion, or reranking was used.",
    ]
    (a.output / "M2D_BLIND_REVEAL_REPAIR.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
