#!/usr/bin/env python3
"""Engineering-only binding wrapper for frozen equal-block Fisher science."""
from __future__ import annotations

from orbittrace_gmn_equal_block_fisher_oof_v1 import exact_parent_reconstruction as exact
from orbittrace_gmn_equal_block_fisher_oof_v1 import run_development as impl

# Replace only the parent-provenance helper. The frozen block scores, combination,
# diversity, fusion, performance gates, and firewall remain exactly unchanged.
impl.fisher_parent.oof_parent_and_fisher = exact.oof_parent_and_fisher_exact

if __name__ == "__main__":
    raise SystemExit(impl.main())
