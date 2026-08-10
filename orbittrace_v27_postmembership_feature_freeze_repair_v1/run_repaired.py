#!/usr/bin/env python3
"""Transport-only v27 wrapper preventing URC-v2 module-level side effects.

The original v27 source imports URC-v2 only for its seven pure cohesion formulas. Importing the
historical full development module mutates historical runtime globals before the frozen 71-feature
identity is reconstructed. This wrapper supplies only those exact seven formulas under the same
module import name, then executes the unchanged v27 builder.
"""
from __future__ import annotations

import math
import sys
import types
from typing import Any

import numpy as np


YEARS = (2013, 2014)


def cohesion_features(
    family: dict[str, Any],
    lookup: dict[str, dict[str, Any]],
    support: Any,
    base: Any,
) -> list[float]:
    """Byte-for-semantics copy of pre-SonotaCo URC-v2 cohesion_features."""
    all_distances: list[float] = []
    per_year_q90: list[float] = []
    counts: list[int] = []
    centroids = family.get("centroids", {})
    for year in YEARS:
        ids = [str(eid) for eid in family["event_ids"] if int(str(eid)[:4]) == year]
        counts.append(len(ids))
        c = centroids.get(str(year))
        distances: list[float] = []
        if c is not None:
            for eid in ids:
                row = lookup.get(eid)
                if row is None:
                    raise RuntimeError(f"member event absent from development scan: {eid}")
                d = float(support.centroid_distance(row, c, base))
                if not math.isfinite(d):
                    raise RuntimeError(f"nonfinite member distance for {eid}")
                distances.append(d)
                all_distances.append(d)
        per_year_q90.append(float(np.quantile(distances, 0.90)) if distances else 10.0)
    cmin, cmax = min(counts), max(counts)
    balance = float(cmin / max(cmax, 1))
    return [
        float(cmin),
        float(cmax),
        balance,
        float(np.median(all_distances)) if all_distances else 10.0,
        float(np.quantile(all_distances, 0.90)) if all_distances else 10.0,
        float(max(all_distances)) if all_distances else 10.0,
        float(max(per_year_q90)),
    ]


def install_transport_stub() -> None:
    pkg_name = "orbittrace_unified_recurrent_catalogue_lab_v2"
    mod_name = pkg_name + ".run_lab"
    pkg = types.ModuleType(pkg_name)
    pkg.__path__ = []  # package marker
    mod = types.ModuleType(mod_name)
    mod.cohesion_features = cohesion_features
    pkg.run_lab = mod
    sys.modules[pkg_name] = pkg
    sys.modules[mod_name] = mod


def main() -> int:
    install_transport_stub()
    from orbittrace_v27_postmembership_feature_freeze_v1 import build_pretruth as impl
    return int(impl.main())


if __name__ == "__main__":
    raise SystemExit(main())
