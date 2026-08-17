#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from orbittrace_final_sonotaco_normalizer_v1 import normalizer

YEARS = (2013, 2014)
BLIND = (20.0, 55.0)


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def dump(path: Path, obj: Any) -> str:
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prepare-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "schema": "ORBITTRACE_TOPOMODAL_FLAGSHIP_DSH_ROWS_V1",
        "years": list(YEARS),
        "blind_exclusion": list(BLIND),
        "normalizer_git_blob": "0264546418d0b50fa53514a6ba170f7c3e33d4d3",
        "panels": {},
        "truth_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }

    for year in YEARS:
        src = a.prepare_dir / f"base_{year}.json"
        rows = json.loads(src.read_text())
        require(isinstance(rows, list) and rows, f"empty base rows {year}")
        require(len({str(r["id"]) for r in rows}) == len(rows), f"duplicate IDs {year}")
        require(all(not (BLIND[0] <= float(r["sol"]) <= BLIND[1]) for r in rows), "protected row present")
        require(all("shower" not in r and "truth" not in r for r in rows), "truth-bearing field in pretruth rows")
        out_rows = [r for r in rows if normalizer.orbit_pairwise_eligible(r)]
        require(out_rows, f"empty D_SH row universe {year}")
        require(all(all(r.get(k) is not None for k in ("q", "e", "peri", "node", "inc")) for r in out_rows), "D_SH orbit missing")
        out = a.output / f"dsh_{year}.json"
        sha = dump(out, out_rows)
        ids = sorted(str(r["id"]) for r in out_rows)
        ids_sha = hashlib.sha256(("\n".join(ids) + "\n").encode()).hexdigest()
        manifest["panels"][str(year)] = {
            "event_count": len(out_rows),
            "event_ids_sha256": ids_sha,
            "rows_json_sha256": sha,
        }

    dump(a.output / "dsh_row_manifest.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
