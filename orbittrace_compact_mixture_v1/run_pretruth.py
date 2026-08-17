#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import scipy
import sklearn

from compact_mixture_v1 import (
    COVARIANCE_TYPE,
    H_LOGV,
    H_RAD,
    H_SOL,
    INIT_PARAMS,
    MAX_ITER,
    MIN_SUPPORT,
    N_COMPONENTS,
    N_INIT,
    RANDOM_STATE,
    REG_COVAR,
    TOL,
    fit_ranked,
)

YEARS = (2013, 2014)
BLIND = (20.0, 55.0)
EXPECTED_RUNTIME = {"numpy": "2.3.5", "scipy": "1.17.0", "sklearn": "1.8.0"}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, obj: Any) -> str:
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows-2013", type=Path, required=True)
    ap.add_argument("--rows-2014", type=Path, required=True)
    ap.add_argument("--scientific-source", type=Path, required=True)
    ap.add_argument("--protocol", type=Path, required=True)
    ap.add_argument("--audit", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    runtime = {"numpy": np.__version__, "scipy": scipy.__version__, "sklearn": sklearn.__version__}
    require(runtime == EXPECTED_RUNTIME, f"runtime drift: {runtime}")

    rows_by_year: dict[int, list[dict[str, Any]]] = {}
    allowed_detector_fields = {"id", "sol", "sun_lon", "ecl_lat", "vg"}
    for year, path in ((2013, a.rows_2013), (2014, a.rows_2014)):
        rows = json.loads(path.read_text())
        require(isinstance(rows, list) and rows, f"empty rows {year}")
        require(len({str(r["id"]) for r in rows}) == len(rows), f"duplicate IDs {year}")
        require(all(int(r["year"]) == year for r in rows), f"wrong year row {year}")
        require(all(not (BLIND[0] <= float(r["sol"]) <= BLIND[1]) for r in rows), "protected row entered v1")
        require(all("shower" not in r and "truth" not in r for r in rows), "explicit truth field entered v1")
        view = [{k: r[k] for k in allowed_detector_fields} for r in rows]
        rows_by_year[year] = view

    pooled = rows_by_year[2013] + rows_by_year[2014]
    require(len({str(r["id"]) for r in pooled}) == len(pooled), "pooled ID collision")

    ranked, fit_summary = fit_ranked(pooled)
    require([int(f["rank"]) for f in ranked] == list(range(1, len(ranked) + 1)), "rank discontinuity")

    out = {
        "schema": "ORBITTRACE_COMPACT_MIXTURE_V1_PRETRUTH",
        "method": "OrbitTrace Compact Mixture v1",
        "scientific_role": "EXPOSED_POST_SELECTION_SONOTACO_2013_2014_DEVELOPMENT",
        "years": list(YEARS),
        "annual_event_counts": {str(y): len(rows_by_year[y]) for y in YEARS},
        "pooled_event_count": len(pooled),
        "family_count": len(ranked),
        "families": ranked,
        "fit_summary": fit_summary,
        "configuration": {
            "n_components": N_COMPONENTS,
            "covariance_type": COVARIANCE_TYPE,
            "reg_covar": REG_COVAR,
            "tol": TOL,
            "max_iter": MAX_ITER,
            "n_init": N_INIT,
            "init_params": INIT_PARAMS,
            "random_state": RANDOM_STATE,
            "min_support": MIN_SUPPORT,
            "h_sol": H_SOL,
            "h_rad": H_RAD,
            "h_logv": H_LOGV,
            "membership": "hard_MAP",
            "ranking": "weight_over_sqrt_diag_covariance_determinant",
        },
        "runtime": runtime,
        "scientific_source_sha256": sha(a.scientific_source),
        "protocol_sha256": sha(a.protocol),
        "label_free_complexity_audit_sha256": sha(a.audit),
        "blind_exclusion": list(BLIND),
        "detector_input_fields": sorted(allowed_detector_fields),
        "truth_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    primary_sha = dump(a.output / "candidate_primary_output.json", out)
    manifest = {
        "method": out["method"],
        "candidate_output_sha256": primary_sha,
        "scientific_source_sha256": out["scientific_source_sha256"],
        "protocol_sha256": out["protocol_sha256"],
        "label_free_complexity_audit_sha256": out["label_free_complexity_audit_sha256"],
        "configuration": out["configuration"],
        "runtime": runtime,
        "truth_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
    }
    manifest_sha = dump(a.output / "candidate_source_manifest.json", manifest)
    print(json.dumps({
        "verdict": "PASS_COMPACT_MIXTURE_V1_PRETRUTH_GENERATION",
        "events": len(pooled), "families": len(ranked), "n_iter": fit_summary["n_iter"],
        "bic": fit_summary["bic"], "primary_sha256": primary_sha, "manifest_sha256": manifest_sha,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
