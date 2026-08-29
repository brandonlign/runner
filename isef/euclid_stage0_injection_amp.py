#!/usr/bin/env python3
"""Rerun the Stage-0 injection pilot with a stable fractional-amplitude statistic."""
import numpy as np
import euclid_stage0_injection as p


def amplitude_stat(v):
    v=np.asarray(v,float);m=np.median(v)
    return float(np.max(np.abs(v/m-1.0)))

p.stat=amplitude_stat
p.main()
