#!/usr/bin/env python3
"""Pre-result collision-corrected locked Oyashio ranking: >=1 kpc only.

This wrapper implements the literature-driven correction recorded in
research/MATLAS_COLLISION_AUDIT_NUCLEAR_TAILS_2026-08-31.md before the first
all-anchor ranking result was known. It removes only the 0.5-kpc exploratory
length because published MATLAS nuclear cluster-merger tails reach comparable
sub-kpc scales. Every anchor, score, width, orientation, curvature, mask,
truth gate and defensive validity behavior is otherwise identical.
"""
import numpy as np
import oyashio_anchored_path_ranking_locked as locked

p=locked.p
p.LENGTHS_PC=np.array([1000.,2000.,4000.])

if __name__=='__main__':
    p.main()
