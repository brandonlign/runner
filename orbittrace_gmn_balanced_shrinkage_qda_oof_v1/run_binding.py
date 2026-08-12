#!/usr/bin/env python3
"""Engineering-only wrapper: use the authoritative parent array hash serialization."""
from __future__ import annotations

from orbittrace_gmn_balanced_shrinkage_qda_oof_v1 import run_development as impl

# The frozen implementation accidentally serialized array shapes as JSON when
# checking provenance. The authoritative parent hashes use str(tuple(shape)).
# Override only this provenance helper before any fixture or scientific code runs.
# No score, feature, label, fold, covariance, ranking, gate, or firewall logic changes.
impl.array_sha = impl.parent.array_sha

if __name__ == "__main__":
    raise SystemExit(impl.main())
