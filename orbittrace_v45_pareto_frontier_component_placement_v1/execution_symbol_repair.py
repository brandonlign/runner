#!/usr/bin/env python3
from __future__ import annotations

from orbittrace_v45_pareto_frontier_component_placement_v1 import train_evaluate as v46

PARENT_SIGNAL_SHA256 = 'a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07'

# Frozen v46 references v44.SIGNAL_SHA only as an immutable #1126 provenance
# identity, but frozen v44 hard-codes the same identity in its #1113 validator
# without exporting that symbol. Supply that missing name only; do not modify
# any v46 ranking, frontier, placement, evaluation, or firewall logic.
if hasattr(v46.v44, 'SIGNAL_SHA'):
    v46.require(v46.v44.SIGNAL_SHA == PARENT_SIGNAL_SHA256, 'unexpected pre-existing v44 SIGNAL_SHA')
else:
    v46.v44.SIGNAL_SHA = PARENT_SIGNAL_SHA256

if __name__ == '__main__':
    raise SystemExit(v46.main())
