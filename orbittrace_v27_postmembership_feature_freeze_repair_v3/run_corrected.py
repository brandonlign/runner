#!/usr/bin/env python3
"""Provenance-only correction for v27 split-process feature freeze.

Clean split-process run 31423471568 executed the untouched v22 builder for both routes and
proved the previously hard-coded 71-feature hashes were stale. Centroid and expanded-membership
identities remained exact. This wrapper changes only those two observed pretruth identity pins;
the 16 frozen post-membership feature definitions and all scientific code are unchanged.
"""
from __future__ import annotations

from orbittrace_v27_postmembership_feature_freeze_repair_v2 import extract_postfeatures as impl

impl.EXPECTED['sugar']['base_feature_sha256'] = '717032336c93862666cd071979170980832dd4aefb5f5eaf10228b36aee3426b'
impl.EXPECTED['hdbscan']['base_feature_sha256'] = 'b9bab759b2a0f24526b63be42488c8d4d957817c7384915021cd81ee4b3d3e75'

if __name__ == '__main__':
    raise SystemExit(impl.main())
