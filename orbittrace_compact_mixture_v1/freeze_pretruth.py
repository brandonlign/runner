#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

YEARS = (2013, 2014)
EXPECTED_METHOD = "OrbitTrace Compact Mixture v1"
EXPECTED_LITERATURE = "catalogue HDBSCAN"


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def dump(path: Path, obj: Any) -> str:
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prepare-dir", type=Path, required=True)
    ap.add_argument("--candidate-dir", type=Path, required=True)
    ap.add_argument("--hdbscan-2013-dir", type=Path, required=True)
    ap.add_argument("--hdbscan-2014-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    candidate_path = a.candidate_dir / "candidate_primary_output.json"
    candidate_manifest_path = a.candidate_dir / "candidate_source_manifest.json"
    candidate = load(candidate_path)
    candidate_manifest = load(candidate_manifest_path)

    require(candidate.get("method") == EXPECTED_METHOD, "wrong candidate method")
    require(candidate.get("truth_accessed") is False, "candidate truth accessed before freeze")
    require(candidate.get("target_information_access") is False, "candidate target information accessed")
    require(candidate.get("target_region_events_accessed") is False, "candidate target-region event access")
    require(candidate.get("post_result_parameter_search") is False, "candidate post-result search")
    require(candidate_manifest.get("truth_accessed") is False, "candidate manifest truth access")
    require(candidate_manifest.get("target_information_access") is False, "candidate manifest target access")
    fams = candidate.get("families")
    require(isinstance(fams, list) and fams, "empty candidate family list")
    require(int(candidate.get("family_count", -1)) == len(fams), "candidate family count mismatch")
    require([int(f["rank"]) for f in fams] == list(range(1, len(fams) + 1)), "candidate rank order invalid")

    hdb_dirs = {2013: a.hdbscan_2013_dir, 2014: a.hdbscan_2014_dir}
    panels: list[dict[str, Any]] = []
    for year in YEARS:
        rows_path = a.prepare_dir / f"hdbscan_{year}.json"
        rows = load(rows_path)
        require(isinstance(rows, list) and rows, f"empty rows {year}")
        row_ids = [str(r["id"]) for r in rows]
        require(len(row_ids) == len(set(row_ids)), f"duplicate row IDs {year}")
        ids_sha = hashlib.sha256(("\n".join(sorted(row_ids)) + "\n").encode()).hexdigest()

        hdir = hdb_dirs[year]
        hpath = hdir / "comparator_primary_output.json"
        hmanifest_path = hdir / "comparator_source_manifest.json"
        hsummary_path = hdir / "comparator_pretruth_summary.json"
        h = load(hpath)
        hm = load(hmanifest_path)
        hs = load(hsummary_path)

        require(h.get("method") == EXPECTED_LITERATURE, f"wrong HDBSCAN method {year}")
        require(int(h.get("year", -1)) == year, f"wrong HDBSCAN year {year}")
        require(h.get("truth_accessed") is False, f"HDBSCAN truth accessed {year}")
        require(hm.get("target_information_access") is False, f"HDBSCAN target access {year}")
        require(hm.get("truth_labels_accepted") is False, f"HDBSCAN accepted truth {year}")
        require(hs.get("truth_accessed") is False, f"HDBSCAN summary truth access {year}")
        hfams = h.get("families")
        require(isinstance(hfams, list) and hfams, f"empty HDBSCAN families {year}")
        b = int(h.get("retained_family_count", -1))
        require(b == len(hfams) and b > 0, f"bad HDBSCAN family count {year}")
        require(hs.get("primary_output_sha256") == sha(hpath), f"HDBSCAN primary hash mismatch {year}")
        require(hs.get("source_manifest_sha256") == sha(hmanifest_path), f"HDBSCAN manifest hash mismatch {year}")

        panels.append({
            "year": year,
            "event_count": len(rows),
            "event_ids_sha256": ids_sha,
            "rows_json_sha256": sha(rows_path),
            "candidate_primary_output_sha256": sha(candidate_path),
            "candidate_source_manifest_sha256": sha(candidate_manifest_path),
            "candidate_family_count": len(fams),
            "hdbscan_primary_output_sha256": sha(hpath),
            "hdbscan_source_manifest_sha256": sha(hmanifest_path),
            "hdbscan_pretruth_summary_sha256": sha(hsummary_path),
            "hdbscan_family_budget": b,
        })

    require(len(panels) == 2, "expected two frozen panels")
    freeze = {
        "schema": "ORBITTRACE_COMPACT_MIXTURE_V1_HDBSCAN_PRETRUTH_FREEZE",
        "method": EXPECTED_METHOD,
        "literature_comparator": EXPECTED_LITERATURE,
        "pretruth_outputs_frozen": True,
        "panels": panels,
        "blind_exclusion": [20.0, 55.0],
        "truth_accessed_before_freeze": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    freeze_sha = dump(a.output / "PRETRUTH_FREEZE.json", freeze)
    print(json.dumps({
        "verdict": "PASS_COMPACT_MIXTURE_V1_HDBSCAN_PRETRUTH_FREEZE",
        "panel_count": len(panels), "candidate_family_count": len(fams), "freeze_sha256": freeze_sha,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
