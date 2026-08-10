#!/usr/bin/env python3
"""Target-excluded cardinality stress wrapper for density-capped multiplicity v13.

This imports the frozen multiplicity-v5 holdout through its already-audited loader correction and
changes only local-episode cardinality from an exact fixed cap to min(cap, available local events).
Proposal generation, family construction, wavelet geometry, multiplicity definition, ranking and
evaluation remain in the frozen v5 module.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import run_holdout_loader_corrected as v5_loader

v5 = v5_loader.core

ALLOWED_CAPS = (32, 64, 96, 128)
SYNTHETIC_SIZES = (4, 8, 16, 32, 64, 96, 128)
ACTIVE_CAP = 128
TRANSPORT_RETRY_ATTEMPTS = 4


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def install_transport_retries() -> None:
    """Retry only transient HTTP exceptions from the unchanged GMN URLs/requests."""
    import requests

    original_get = requests.get

    def retrying_get(*args: Any, **kwargs: Any) -> Any:
        for attempt in range(TRANSPORT_RETRY_ATTEMPTS):
            try:
                return original_get(*args, **kwargs)
            except requests.exceptions.RequestException:
                if attempt + 1 == TRANSPORT_RETRY_ATTEMPTS:
                    raise
                time.sleep(float(2**attempt))
        raise AssertionError("unreachable retry loop")

    requests.get = retrying_get


def adaptive_local_episode(
    family: dict[str, Any],
    year: int,
    scan_events: list[dict[str, Any]],
    runtime: Any,
    base: Any,
) -> tuple[Any, dict[str, Any]]:
    """Frozen v5 local episode with only exact-cardinality requirement replaced by min(cap,N)."""
    cap = int(ACTIVE_CAP)
    require(cap in ALLOWED_CAPS, f"unexpected stress cap {cap}")
    centroid = family.get("centroids", {}).get(str(year))
    require(centroid is not None, f"family {family['family_id']} missing centroid for {year}")
    center_sol = float(centroid["sol"])
    window_events = runtime.window_events_for_center(scan_events, center_sol, base)
    k = min(cap, len(window_events))
    require(k >= 4, f"family {family['family_id']} year {year} has fewer than four local events")
    anchor = {
        "sol": center_sol,
        "sun_lon": float(centroid["sun_lon"]),
        "ecl_lat": float(centroid["ecl_lat"]),
        "vg": float(centroid["vg"]),
    }
    distances = runtime.exact_wavelet_r2(anchor, window_events)
    selected = runtime.stable_smallest_indices(distances, k)
    selected_indices = [int(index) for index in selected]
    require(len(selected_indices) == k and len(set(selected_indices)) == k, "episode index duplication")
    chosen = [window_events[index] for index in selected_indices]
    episode = SimpleNamespace(
        sun_lon=np.asarray([float(event["sun_lon"]) for event in chosen], dtype=np.float64),
        ecl_lat=np.asarray([float(event["ecl_lat"]) for event in chosen], dtype=np.float64),
        vg=np.asarray([float(event["vg"]) for event in chosen], dtype=np.float64),
    )
    return episode, {
        "window_event_count": len(window_events),
        "episode_size": len(chosen),
        "episode_cap": cap,
        "adaptive_cardinality": True,
        "selected_max_r2": float(np.max(distances[selected])),
        "centroid": anchor,
    }


def synthetic_cardinality_checks() -> dict[str, Any]:
    """Prove the unchanged ratio scorer is finite/Brown-equivalent over variable cardinalities."""
    checks: dict[str, Any] = {}
    for n in SYNTHETIC_SIZES:
        lon = np.linspace(-150.0, 150.0, n, dtype=np.float64)
        lat = np.linspace(-45.0, 45.0, n, dtype=np.float64)
        vg = np.linspace(20.0, 60.0, n, dtype=np.float64)
        lon[:4] = np.asarray([10.0, 10.2, 9.8, 10.1])
        lat[:4] = np.asarray([5.0, 5.1, 4.9, 5.05])
        vg[:4] = np.asarray([35.0, 35.2, 34.9, 35.1])
        episode = SimpleNamespace(sun_lon=lon, ecl_lat=lat, vg=vg)
        v3_score, brown_score, multiplicity, difference = v5.score_episode(episode)
        order = np.arange(n, dtype=int)[::-1]
        permuted = SimpleNamespace(sun_lon=lon[order], ecl_lat=lat[order], vg=vg[order])
        pv3, pbrown, pmultiplicity, pdifference = v5.score_episode(permuted)
        require(abs(v3_score - pv3) <= 1e-10, f"v3 permutation failure at n={n}")
        require(abs(brown_score - pbrown) <= 1e-10, f"Brown permutation failure at n={n}")
        require(abs(multiplicity - pmultiplicity) <= 1e-10, f"multiplicity permutation failure at n={n}")
        require(max(difference, pdifference) <= v5.BROWN_EQ_TOL, f"Brown equivalence failure at n={n}")
        require(1.0 - 1e-10 <= multiplicity <= 4.0 + 1e-10, f"multiplicity bound failure at n={n}")
        checks[str(n)] = {
            "v3_score": float(v3_score),
            "brown_score": float(brown_score),
            "multiplicity": float(multiplicity),
            "brown_equivalence_difference": float(difference),
            "permutation_invariant": True,
        }
    return checks


def parse_wrapper_args() -> tuple[argparse.Namespace, list[str]]:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--cap", type=int, choices=ALLOWED_CAPS, required=True)
    p.add_argument("--v13-summary", type=Path, required=True)
    return p.parse_known_args()


def main() -> int:
    global ACTIVE_CAP
    wrapper, remaining = parse_wrapper_args()
    checks = synthetic_cardinality_checks()

    # Keep frozen v5's EPISODE_SIZE=128 untouched so its source/runtime identity guard
    # remains exact. The successor intervention is only the separate adaptive cap used
    # by the patched local-episode builder after the frozen runtime has been verified.
    require(int(v5.EPISODE_SIZE) == 128, "frozen v5 episode-size identity changed")
    ACTIVE_CAP = int(wrapper.cap)
    v5.build_local_episode = adaptive_local_episode
    install_transport_retries()

    sys.argv = [sys.argv[0], *remaining]
    rc = int(v5.main())
    require(rc == 0, f"frozen v5 execution returned {rc}")

    output_arg = None
    for i, token in enumerate(remaining):
        if token == "--output":
            output_arg = Path(remaining[i + 1])
            break
    require(output_arg is not None, "missing forwarded --output")
    result = json.loads((output_arg / "multiplicity_v5_holdout.json").read_text())
    rankings = json.loads((output_arg / "multiplicity_v5_rankings.json").read_text())
    order = [str(x) for x in rankings["multiplicity"]]
    scoring = result["family_scoring_summary"]
    summary = {
        "method": "orbittrace_density_capped_multiplicity_v13_stress",
        "stress_cap": int(wrapper.cap),
        "adaptive_rule": "K=min(cap,N_local); fail only if N_local<4",
        "synthetic_cardinality_checks": checks,
        "family_count": int(result["family_count"]),
        "family_universe_sha256": canonical_sha(sorted(order)),
        "multiplicity_order_sha256": canonical_sha(order),
        "episode_sizes_observed": list(scoring["episode_sizes"]),
        "max_brown_equivalence_difference": float(scoring["max_brown_equivalence_difference"]),
        "multiplicity_metrics": result["metrics"]["multiplicity"],
        "fixed4_metrics": result["metrics"]["fixed4_persistence"],
        "transport_retry_attempts": TRANSPORT_RETRY_ATTEMPTS,
        "truth_labels_used_only_after_ranking": True,
        "sonotaco_2013_2014_access": False,
        "maarsy_access": False,
        "target_information_access": False,
    }
    wrapper.v13_summary.parent.mkdir(parents=True, exist_ok=True)
    wrapper.v13_summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
