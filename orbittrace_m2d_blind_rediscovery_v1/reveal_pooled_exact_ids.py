#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

EXPECTED_CANONICAL = {2022: 10, 2023: 8, 2024: 14, 2025: 34, 2026: 29}
EXPECTED_INNER_SHA256 = "7ff3b13bc45e19b4b886453b4d8cc3b4f18090bf8a2291e39850540fd69b5e53"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


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
        for f in fields:
            n = norm(f)
            if "id" in n and ("event" in n or "trajectory" in n):
                idcol = f
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
            m = re.search(r"20(22|23|24|25|26)", eid)
            req(m is not None, f"cannot derive year {eid}")
            year = int(m.group(0))
        out.append((eid, year))
    counts = Counter(y for _, y in out)
    req(dict(sorted(counts.items())) == EXPECTED_CANONICAL, f"canonical counts {dict(counts)}")
    req(len({eid for eid, _ in out}) == 95, "canonical IDs not unique")
    return out, idcol, yearcol


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pretruth", type=Path, required=True)
    ap.add_argument("--canonical-zip", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    pre_gz = a.pretruth.read_bytes()
    pre_raw = gzip.decompress(pre_gz)
    inner_sha = hashlib.sha256(pre_raw).hexdigest()
    req(inner_sha == EXPECTED_INNER_SHA256, f"pretruth inner SHA changed: {inner_sha}")
    pre = json.loads(pre_raw)
    req(pre["schema"] == "ORBITTRACE_M2D_BLIND_REDISCOVERY_V1_PRETRUTH", "wrong pretruth schema")
    req(pre["scientific_role"] == "TARGET_FREE_COMPLETE_M2D_RANKING_BEFORE_ORBITTRACE_REVEAL", "wrong scientific role")
    req(pre["configuration"]["years"] == [2022, 2023], "wrong pooled years")
    req(pre["configuration"]["target_interval_exclusion"] is None, "target interval was excluded")
    req(pre["shower_truth_used"] is False, "pretruth used shower truth")
    req(pre["orbittrace_target_information_access"] is False, "pretruth used OrbitTrace target information")
    req(pre["orbittrace_canonical_members_access"] is False, "pretruth used canonical members")
    req(pre["prior_orbittrace_reveal_access"] is False, "pretruth used prior reveal")
    req(pre["post_result_parameter_search"] is False, "pretruth used post-result search")
    req(pre["candidate_count"] == len(pre["candidates"]) == 8469, "candidate count changed")
    req([int(c["rank"]) for c in pre["candidates"]] == list(range(1, 8470)), "ranking discontinuity")

    canon, idcol, yearcol = canonical_rows(a.canonical_zip)
    byyear = {y: {eid for eid, yy in canon if yy == y} for y in (2022, 2023)}
    req(len(byyear[2022]) == 10 and len(byyear[2023]) == 8, "wrong 2022/2023 canonical counts")

    evaluated = []
    for c in pre["candidates"]:
        ids = set(map(str, c["event_ids"]))
        o22 = sorted(ids & byyear[2022])
        o23 = sorted(ids & byyear[2023])
        total = len(o22) + len(o23)
        evaluated.append({
            "rank": int(c["rank"]),
            "family_hash": str(c["family_hash"]),
            "member_count": int(c["member_count"]),
            "m2d": float(c["internal_2d_mass"]),
            "modal_contrast": float(c["modal_contrast"]),
            "overlap_2022": o22,
            "overlap_2023": o23,
            "overlap_total": total,
            "precision": total / len(ids) if ids else 0.0,
            "recall": total / 18.0,
            "gate": len(o22) >= 4 and len(o23) >= 4 and total >= 8,
        })

    passing = sorted((x for x in evaluated if x["gate"]), key=lambda x: x["rank"])
    best = sorted(
        evaluated,
        key=lambda x: (-x["overlap_total"], -min(len(x["overlap_2022"]), len(x["overlap_2023"])), x["rank"]),
    )[0]
    if passing and passing[0]["rank"] <= 25:
        verdict = "FULL_M2D_BLIND_ORBITTRACE_REDISCOVERY"
        chosen = passing[0]
    elif passing and passing[0]["rank"] <= 100:
        verdict = "PARTIAL_M2D_BLIND_ORBITTRACE_REDISCOVERY"
        chosen = passing[0]
    else:
        verdict = "NO_M2D_BLIND_ORBITTRACE_REDISCOVERY"
        chosen = best

    result = {
        "verdict": verdict,
        "pretruth_inner_sha256": inner_sha,
        "pretruth_gzip_sha256": hashlib.sha256(pre_gz).hexdigest(),
        "candidate_count": int(pre["candidate_count"]),
        "canonical_column": idcol,
        "canonical_year_column": yearcol,
        "first_gate_passing_rank": passing[0]["rank"] if passing else None,
        "chosen_family": chosen,
        "best_overlap_family": best,
        "gate_definition": ">=4 exact canonical IDs in 2022 and >=4 in 2023 and >=8 total; FULL rank<=25, PARTIAL rank<=100",
        "reveal_operation": "exact event-ID set intersection only",
        "coordinates_used": False,
        "activity_interval_used": False,
        "orbit_matching_used": False,
        "member_expansion_used": False,
        "reranking_used": False,
    }
    (a.output / "M2D_POOLED_BLIND_REVEAL.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    c = chosen
    lines = [
        "# M2D pooled blind OrbitTrace exact-ID reveal",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        f"- frozen pretruth inner SHA-256: `{inner_sha}`",
        f"- candidate count: **{pre['candidate_count']:,}**",
        f"- selected rank: **{c['rank']}**",
        f"- exact 2022 overlap: **{len(c['overlap_2022'])}/10**",
        f"- exact 2023 overlap: **{len(c['overlap_2023'])}/8**",
        f"- total exact overlap: **{c['overlap_total']}/18**",
        f"- candidate members: **{c['member_count']}**",
        f"- precision vs canonical 2022–2023 IDs: **{c['precision']:.3f}**",
        f"- recall vs canonical 2022–2023 IDs: **{c['recall']:.3f}**",
        "",
        "Reveal used exact event-ID intersection only; no coordinates, activity interval, orbit matching, member expansion, merging, or reranking was allowed after the pooled M2D catalogue was frozen.",
    ]
    (a.output / "M2D_POOLED_BLIND_REVEAL.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
