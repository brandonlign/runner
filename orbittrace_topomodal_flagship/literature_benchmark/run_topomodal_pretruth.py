#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

EXPECTED_SOURCE_BLOB = "752df8212ce601227f6e9170b0fe994ba06b515d"
YEARS = (2013, 2014)
BLIND = (20.0, 55.0)
ALLOWED = {"sugar", "hdbscan", "dsh"}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, obj: Any) -> str:
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def load_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("frozen_topomodal_flagship", path)
    require(spec is not None and spec.loader is not None, "cannot import flagship source")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--comparator", required=True, choices=sorted(ALLOWED))
    ap.add_argument("--rows-2013", type=Path, required=True)
    ap.add_argument("--rows-2014", type=Path, required=True)
    ap.add_argument("--flagship-source", type=Path, required=True)
    ap.add_argument("--source-git-blob", required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    require(a.source_git_blob == EXPECTED_SOURCE_BLOB, "flagship source blob changed")
    mod = load_module(a.flagship_source)
    require(float(mod.RADIUS) == 1.0 and int(mod.MIN_SUPPORT) == 4, "flagship graph/support changed")
    require(abs(float(mod.H_LOGV) - __import__("math").log(1.1)) < 1e-15, "flagship speed scale changed")

    rows_by_year: dict[int, list[dict[str, Any]]] = {}
    for year, path in ((2013, a.rows_2013), (2014, a.rows_2014)):
        rows = json.loads(path.read_text())
        require(isinstance(rows, list) and rows, f"empty rows {year}")
        require(len({str(r["id"]) for r in rows}) == len(rows), f"duplicate IDs {year}")
        require(all(int(r["year"]) == year for r in rows), f"wrong year row {year}")
        require(all(not (BLIND[0] <= float(r["sol"]) <= BLIND[1]) for r in rows), "protected row entered flagship")
        require(all("shower" not in r and "truth" not in r for r in rows), "truth field entered flagship")
        rows_by_year[year] = rows

    pooled_raw = rows_by_year[2013] + rows_by_year[2014]
    require(len({str(r["id"]) for r in pooled_raw}) == len(pooled_raw), "pooled ID collision")
    adapted = [
        {
            "id": str(r["id"]),
            "sol": float(r["sol"]),
            "lon": float(r["sun_lon"]),
            "lat": float(r["ecl_lat"]),
            "vg": float(r["vg"]),
        }
        for r in pooled_raw
    ]

    ranked, summary = mod.topomodal_ranked(adapted)
    require(ranked, "flagship returned no candidates")
    require([int(x["rank"]) for x in ranked] == list(range(1, len(ranked) + 1)), "rank discontinuity")
    allowed_ids = {str(r["id"]) for r in pooled_raw}
    families: list[dict[str, Any]] = []
    for r in ranked:
        ids = [str(x) for x in r["event_ids"]]
        require(ids and len(ids) == len(set(ids)), "invalid flagship membership")
        require(set(ids).issubset(allowed_ids), "flagship membership outside pairwise universe")
        families.append({
            "family_id": str(r["family_id"]),
            "rank": int(r["rank"]),
            "event_ids": ids,
            "member_count": int(r["member_count"]),
            "is_root": bool(r["is_root"]),
            "creation_prominence": float(r["creation_prominence"]),
            "prominence_span": None if r["prominence_span"] is None else float(r["prominence_span"]),
            "peak_density": float(r["peak_density"]),
            "mean_density": float(r["mean_density"]),
        })

    out = {
        "schema": "ORBITTRACE_TOPOMODAL_FLAGSHIP_LITERATURE_PRETRUTH_V1",
        "method": "fixed-scale TopoModal flagship",
        "comparator_pair": a.comparator,
        "years": list(YEARS),
        "annual_event_counts": {str(y): len(rows_by_year[y]) for y in YEARS},
        "pooled_event_count": len(pooled_raw),
        "family_count": len(families),
        "families": families,
        "structural_summary": {k: v for k, v in summary.items() if k != "candidate_rows"},
        "flagship_source_git_blob": EXPECTED_SOURCE_BLOB,
        "flagship_source_sha256": sha(a.flagship_source),
        "blind_exclusion": list(BLIND),
        "truth_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    output_sha = dump(a.output / "candidate_primary_output.json", out)
    manifest = {
        "method": out["method"],
        "comparator_pair": a.comparator,
        "flagship_source_git_blob": EXPECTED_SOURCE_BLOB,
        "flagship_source_sha256": sha(a.flagship_source),
        "candidate_output_sha256": output_sha,
        "configuration": {
            "radius": 1.0,
            "min_support": 4,
            "h_sol": float(mod.H_SOL),
            "h_rad": float(mod.H_RAD),
            "h_logv": float(mod.H_LOGV),
        },
        "truth_accessed": False,
        "target_information_access": False,
    }
    dump(a.output / "candidate_source_manifest.json", manifest)
    print(json.dumps({"comparator": a.comparator, "events": len(pooled_raw), "families": len(families), "output_sha256": output_sha}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
