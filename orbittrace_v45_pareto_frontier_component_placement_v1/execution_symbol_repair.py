#!/usr/bin/env python3
from __future__ import annotations

from orbittrace_v45_pareto_frontier_component_placement_v1 import train_evaluate as v46

PARENT_SIGNAL_SHA256 = 'a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07'

# Frozen v46 references two parent names that frozen v44 uses transitively but
# does not export. Bind only the already-fixed immutable values/implementation:
# - SIGNAL_SHA is the exact #1098 signal identity hard-coded by frozen v44.
# - component_best_percentiles is the exact frozen-v42 helper that frozen v44
#   itself calls in build_v44_order. No ranking/frontier/evaluation logic changes.
if hasattr(v46.v44, 'SIGNAL_SHA'):
    v46.require(v46.v44.SIGNAL_SHA == PARENT_SIGNAL_SHA256, 'unexpected pre-existing v44 SIGNAL_SHA')
else:
    v46.v44.SIGNAL_SHA = PARENT_SIGNAL_SHA256

if hasattr(v46.v44, 'component_best_percentiles'):
    v46.require(
        v46.v44.component_best_percentiles is v46.v42.component_best_percentiles,
        'unexpected pre-existing v44 component_best_percentiles',
    )
else:
    v46.v44.component_best_percentiles = v46.v42.component_best_percentiles

if __name__ == '__main__':
    raise SystemExit(v46.main())
