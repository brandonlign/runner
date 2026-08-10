#!/usr/bin/env python3
"""Generate one missing v15 multiplicity-cap ranking without consulting hidden labels."""
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

ALLOWED_CAPS = (16, 24, 48, 72)
ACTIVE_CAP = 16
TRANSPORT_RETRY_ATTEMPTS = 4


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def install_transport_retries() -> None:
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
    cap = int(ACTIVE_CAP)
    require(cap in ALLOWED_CAPS, f"unexpected v15 nested cap {cap}")
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


def no_label_evaluate_order(_hidden_labels: dict[str, str], _families: list[dict[str, Any]], _order: list[str]) -> dict[str, Any]:
    """Prevent any hidden-label value from being consulted in the pretruth generator."""
    return {
        "eligible_labels": 0,
        "qualified_matches": 0,
        "recovered_at_100": 0,
        "recovered_at_500": 0,
        "mrr": 0.0,
        "median_rank": None,
        "macro_f1": 0.0,
        "top100_dominant_precision": 0.0,
        "per_label": [],
    }


def parse_wrapper_args() -> tuple[argparse.Namespace, list[str]]:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--cap", type=int, choices=ALLOWED_CAPS, required=True)
    p.add_argument("--v15-summary", type=Path, required=True)
    return p.parse_known_args()


def main() -> int:
    global ACTIVE_CAP
    wrapper, remaining = parse_wrapper_args()
    require(int(v5.EPISODE_SIZE) == 128, "frozen v5 episode-size identity changed")
    ACTIVE_CAP = int(wrapper.cap)

    # Both interventions are installed before the first catalogue call in frozen v5.main:
    # (1) adaptive episode cardinality for this preregistered nested cap;
    # (2) a no-label evaluation stub, ensuring hidden shower labels are never consulted.
    v5.build_local_episode = adaptive_local_episode
    v5.evaluate_order = no_label_evaluate_order
    install_transport_retries()

    sys.argv = [sys.argv[0], *remaining]
    rc = int(v5.main())
    require(rc == 0, f"frozen v5 execution returned {rc}")

    output_arg = None
    for index, token in enumerate(remaining):
        if token == "--output":
            output_arg = Path(remaining[index + 1])
            break
    require(output_arg is not None, "missing forwarded --output")
    result = json.loads((output_arg / "multiplicity_v5_holdout.json").read_text())
    rankings = json.loads((output_arg / "multiplicity_v5_rankings.json").read_text())
    order = [str(x) for x in rankings["multiplicity"]]
    scoring = result["family_scoring_summary"]
    require(result["metrics"]["multiplicity"]["eligible_labels"] == 0, "label evaluator was not stubbed")
    require(result["metrics"]["multiplicity"]["qualified_matches"] == 0, "label evaluator was not stubbed")
    require(scoring["episode_sizes"] == [int(wrapper.cap)], f"nested cap {wrapper.cap} did not use exact episode cardinality")

    summary = {
        "method": "orbittrace_multiscale_consensus_v15_pretruth_cap",
        "stress_cap": int(wrapper.cap),
        "family_count": int(result["family_count"]),
        "family_universe_sha256": canonical_sha(sorted(order)),
        "multiplicity_order_sha256": canonical_sha(order),
        "episode_sizes_observed": list(scoring["episode_sizes"]),
        "max_brown_equivalence_difference": float(scoring["max_brown_equivalence_difference"]),
        "hidden_label_values_consulted": False,
        "postranking_label_evaluator_stubbed_before_catalogue_access": True,
        "transport_retry_attempts": TRANSPORT_RETRY_ATTEMPTS,
        "sonotaco_2013_2014_access": False,
        "maarsy_access": False,
        "target_information_access": False,
    }
    wrapper.v15_summary.parent.mkdir(parents=True, exist_ok=True)
    wrapper.v15_summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
