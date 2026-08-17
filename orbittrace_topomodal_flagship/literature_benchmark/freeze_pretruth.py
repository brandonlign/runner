#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

PAIRS = ("sugar", "hdbscan", "dsh")
YEARS = (2013, 2014)


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
    for pair in PAIRS:
        ap.add_argument(f"--candidate-{pair}-dir", type=Path, required=True)
        for year in YEARS:
            ap.add_argument(f"--comparator-{pair}-{year}-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args(); a.output.mkdir(parents=True, exist_ok=True)

    candidate_dirs = {p: getattr(a, f"candidate_{p}_dir") for p in PAIRS}
    comp_dirs = {(p, y): getattr(a, f"comparator_{p}_{y}_dir") for p in PAIRS for y in YEARS}
    panels: list[dict[str, Any]] = []

    for pair in PAIRS:
        cand_dir = candidate_dirs[pair]
        cand_path = cand_dir / "candidate_primary_output.json"
        cand_manifest_path = cand_dir / "candidate_source_manifest.json"
        cand = load(cand_path)
        require(cand.get("method") == "fixed-scale TopoModal flagship", "wrong flagship method")
        require(cand.get("comparator_pair") == pair, "flagship pair mismatch")
        require(cand.get("truth_accessed") is False, "flagship truth accessed prefreeze")
        require(cand.get("target_information_access") is False, "flagship target access")
        require(isinstance(cand.get("families"), list) and cand["families"], "empty flagship families")

        for year in YEARS:
            rows_path = a.prepare_dir / f"{pair}_{year}.json"
            rows = load(rows_path)
            require(isinstance(rows, list) and rows, "empty pair rows")
            ids = sorted(str(r["id"]) for r in rows)
            require(len(ids) == len(set(ids)), "duplicate pairwise IDs")
            ids_sha = hashlib.sha256(("\n".join(ids) + "\n").encode()).hexdigest()

            comp_dir = comp_dirs[(pair, year)]
            comp_path = comp_dir / "comparator_primary_output.json"
            comp_manifest_path = comp_dir / "comparator_source_manifest.json"
            comp = load(comp_path)
            require(int(comp.get("year", -1)) == year, "comparator year mismatch")
            require(comp.get("truth_accessed") is False, "comparator truth accessed prefreeze")
            require(comp.get("target_information_access") is False, "comparator target access")
            require(isinstance(comp.get("families"), list), "invalid comparator families")
            b = int(comp.get("retained_family_count", -1))
            require(b == len(comp["families"]) and b > 0, f"empty/invalid literature family catalogue: {pair} {year}")

            panels.append({
                "pair": pair,
                "year": year,
                "pairwise_event_count": len(rows),
                "pairwise_event_ids_sha256": ids_sha,
                "pairwise_rows_json_sha256": sha(rows_path),
                "topomodal_candidate_count": int(cand["family_count"]),
                "topomodal_primary_output_sha256": sha(cand_path),
                "topomodal_source_manifest_sha256": sha(cand_manifest_path),
                "literature_family_count": b,
                "literature_primary_output_sha256": sha(comp_path),
                "literature_source_manifest_sha256": sha(comp_manifest_path),
            })

    require(len(panels) == 6, "expected six frozen panels")
    freeze = {
        "schema": "ORBITTRACE_TOPOMODAL_FLAGSHIP_MATCHED_LITERATURE_PRETRUTH_FREEZE_V1",
        "pretruth_outputs_frozen": True,
        "panels": panels,
        "truth_accessed_before_freeze": False,
        "blind_exclusion": [20.0, 55.0],
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    freeze_sha = dump(a.output / "PRETRUTH_FREEZE.json", freeze)
    print(json.dumps({"verdict": "PASS_TOPOMODAL_FLAGSHIP_LITERATURE_PRETRUTH_FREEZE", "panels": len(panels), "freeze_sha256": freeze_sha}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
