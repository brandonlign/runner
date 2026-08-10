#!/usr/bin/env python3
"""Transport-only SonotaCo schema adapter for the frozen v27 cohesion features.

The historical URC-v2 helper recovered year from the first four characters of a GMN event ID.
Canonical SonotaCo IDs are opaque (`SNT...`) and already carry the explicit canonical `year`
field. This wrapper changes only that transport lookup: it applies the exact same seven frozen
cohesion formulas after selecting annual members by `lookup[eid]['year']` instead of an ID prefix.
No distance, quantile, feature, membership, candidate, ranking, threshold, or truth rule changes.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np

from orbittrace_final_sonotaco_one_shot_v1.runtime_helpers import require
from orbittrace_v27_postmembership_feature_freeze_repair_v2 import extract_postfeatures as helper
from orbittrace_v27_postmembership_feature_freeze_repair_v5 import extract_id_bound as impl

YEARS = (2013, 2014)


def schema_compatible_cohesion_features(
    family: dict[str, Any],
    lookup: dict[str, dict[str, Any]],
    support: Any,
    base: Any,
) -> list[float]:
    """Exact URC-v2 cohesion math with canonical-row year transport."""
    all_distances: list[float] = []
    per_year_q90: list[float] = []
    counts: list[int] = []
    centroids = family.get('centroids', {})

    for year in YEARS:
        ids: list[str] = []
        for raw_eid in family['event_ids']:
            eid = str(raw_eid)
            row = lookup.get(eid)
            require(row is not None, f'member event absent from scan: {eid}')
            require('year' in row, f'canonical year missing for member: {eid}')
            if int(row['year']) == year:
                ids.append(eid)

        counts.append(len(ids))
        c = centroids.get(str(year))
        distances: list[float] = []
        if c is not None:
            for eid in ids:
                row = lookup[eid]
                d = float(support.centroid_distance(row, c, base))
                require(math.isfinite(d), f'nonfinite member distance {eid}')
                distances.append(d)
                all_distances.append(d)
        per_year_q90.append(float(np.quantile(distances, 0.90)) if distances else 10.0)

    cmin, cmax = min(counts), max(counts)
    return [
        float(cmin),
        float(cmax),
        float(cmin / max(cmax, 1)),
        float(np.median(all_distances)) if all_distances else 10.0,
        float(np.quantile(all_distances, 0.90)) if all_distances else 10.0,
        float(max(all_distances)) if all_distances else 10.0,
        float(max(per_year_q90)),
    ]


def main() -> int:
    helper.cohesion_features = schema_compatible_cohesion_features
    return int(impl.main())


if __name__ == '__main__':
    raise SystemExit(main())
