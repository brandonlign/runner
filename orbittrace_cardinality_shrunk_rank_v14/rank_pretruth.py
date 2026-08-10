#!/usr/bin/env python3
"""Freeze v14 cardinality-shrunk rankings from label-free v13 stress artifacts."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

CAPS = (32, 64, 96, 128)
REFERENCE_EPISODE_SIZE = 128.0
EXPECTED_FAMILY_COUNT = 92
TOL = 1e-12


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def load_gzip_json(path: Path) -> Any:
    with gzip.open(path, "rt") as handle:
        return json.load(handle)


def rank_one(cap_dir: Path, cap: int) -> dict[str, Any]:
    rankings = load_json(cap_dir / "multiplicity_v5_rankings.json")
    scores = load_gzip_json(cap_dir / "multiplicity_v5_family_scores.json.gz")
    summary = load_json(cap_dir / "v13_summary.json")

    require(int(summary["stress_cap"]) == cap, f"stress-cap identity mismatch for {cap}")
    require(summary["sonotaco_2013_2014_access"] is False, "SonotaCo access in v14 rank input")
    require(summary["maarsy_access"] is False, "MAARSY access in v14 rank input")
    require(summary["target_information_access"] is False, "target access in v14 rank input")

    multiplicity = [str(x) for x in rankings["multiplicity"]]
    fixed4 = [str(x) for x in rankings["fixed4_persistence"]]
    require(len(multiplicity) == EXPECTED_FAMILY_COUNT, f"unexpected family count at cap {cap}")
    require(len(fixed4) == EXPECTED_FAMILY_COUNT, f"unexpected fixed4 family count at cap {cap}")
    require(set(multiplicity) == set(fixed4), f"ranking universe mismatch at cap {cap}")

    score_by_id = {str(row["family_id"]): row for row in scores}
    require(set(score_by_id) == set(multiplicity), f"score universe mismatch at cap {cap}")
    r_m = {fid: rank for rank, fid in enumerate(multiplicity)}
    r_f = {fid: rank for rank, fid in enumerate(fixed4)}

    rows: list[dict[str, Any]] = []
    for fid in multiplicity:
        per_year = score_by_id[fid]["per_year"]
        sizes = [int(row["episode_size"]) for _, row in sorted(per_year.items())]
        require(len(sizes) == 2 and min(sizes) >= 4, f"invalid episode sizes for {fid} at cap {cap}: {sizes}")
        q = min(1.0, max(0.0, min(sizes) / REFERENCE_EPISODE_SIZE))
        rm = int(r_m[fid]); rf = int(r_f[fid])
        fused = q * rm + (1.0 - q) * rf
        require(-TOL <= q <= 1.0 + TOL, f"q out of range for {fid}")
        require(min(rm, rf) - TOL <= fused <= max(rm, rf) + TOL, f"fused rank escaped endpoint interval for {fid}")
        if abs(q - 1.0) <= TOL:
            require(abs(fused - rm) <= TOL, f"q=1 endpoint identity failed for {fid}")
        rows.append({
            "family_id": fid,
            "multiplicity_rank_zero_based": rm,
            "fixed4_rank_zero_based": rf,
            "min_episode_size": min(sizes),
            "episode_sizes": sizes,
            "q": q,
            "v14_fused_rank_score": fused,
        })

    ordered_rows = sorted(
        rows,
        key=lambda row: (
            float(row["v14_fused_rank_score"]),
            int(row["multiplicity_rank_zero_based"]),
            int(row["fixed4_rank_zero_based"]),
            str(row["family_id"]),
        ),
    )
    order = [str(row["family_id"]) for row in ordered_rows]
    if cap == 128:
        require(order == multiplicity, "cap128 v14 order failed exact multiplicity identity")

    return {
        "cap": cap,
        "method": "cardinality_shrunk_rank_v14",
        "rule": "R14=q*r_M+(1-q)*r_F; q=min(year episode size)/128",
        "family_count": len(order),
        "family_universe_sha256": canonical_sha(sorted(order)),
        "input_multiplicity_order_sha256": canonical_sha(multiplicity),
        "input_fixed4_order_sha256": canonical_sha(fixed4),
        "v14_order_sha256": canonical_sha(order),
        "order": order,
        "rows": ordered_rows,
        "labels_read": False,
        "sonotaco_2013_2014_access": False,
        "maarsy_access": False,
        "target_information_access": False,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()


def main() -> int:
    a = parse_args(); a.output.mkdir(parents=True, exist_ok=True)
    results = {cap: rank_one(a.input_root / f"cap{cap}", cap) for cap in CAPS}
    universes = {result["family_universe_sha256"] for result in results.values()}
    require(len(universes) == 1, "family universe differs across v14 caps")
    for cap, result in results.items():
        path = a.output / f"v14_order_cap{cap}.json"
        path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    audit = {
        "verdict": "PASS_V14_PRETRUTH_RANK_FREEZE",
        "caps": list(CAPS),
        "family_count": EXPECTED_FAMILY_COUNT,
        "family_universe_sha256": next(iter(universes)),
        "cap128_exact_multiplicity_identity": results[128]["order"] == [
            row["family_id"] for row in sorted(results[128]["rows"], key=lambda r: r["multiplicity_rank_zero_based"])
        ],
        "all_rankings_frozen_before_labels": True,
        "sonotaco_2013_2014_access": False,
        "maarsy_access": False,
        "target_information_access": False,
    }
    require(audit["cap128_exact_multiplicity_identity"], "cap128 audit identity failed")
    (a.output / "v14_pretruth_audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
