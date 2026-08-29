#!/usr/bin/env python3
"""Use a wide geometric proposal radius; exact WCS still decides acceptance."""
import math
import numpy as np
import euclid_shiftselect_feasibility as s


def approx_hit(ra,dec):
    cd=max(math.cos(math.radians(dec)),0.2)
    d=np.hypot((s.CENTERS[:,0]-ra)*cd,s.CENTERS[:,1]-dec)*3600
    order=np.argsort(d)[:4]
    # Quadrant half-diagonal is ~145 arcsec; use 140 only to propose routes.
    # This does NOT accept a target: s.search validates every proposal using
    # the exact per-epoch WCS and the configured detector-edge margin.
    for k in order:
        arc=float(d[k])
        if arc<140:
            return (1500-arc/0.1,int(k))
    return None

s.approx_hit=approx_hit
s.main()
