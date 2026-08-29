#!/usr/bin/env python3
"""Geometry-correct wrapper for the cross-quadrant Euclid Stage-0 test.

Selects a target only if the exposure-0 focal-plane WCS, translated by the four
empirically measured dither vectors, predicts that the target falls well inside
a SCI quadrant at every pointing. The base module then validates those routes
against the actual headers for all 16 exposures and performs the pixel test.
"""
import math
import numpy as np
import euclid_routed_feasibility as m


def robust_choose_target(qs):
    shifts=m.pointing_shifts()
    centers=np.array([q.center for q in qs],float)
    med=(float(np.median(centers[:,0])),float(np.median(centers[:,1])))
    cd=math.cos(math.radians(med[1]))

    def predicted_route(ra,de,g):
        sx,sy=shifts[g]
        eq=(ra-sx/(cd*3600.0),de-sy/3600.0)
        nearest=sorted(range(len(qs)),key=lambda k:m.dist_arcsec(qs[k].center,eq,de))[:12]
        for k in nearest:
            if m.contains(qs[k],eq,m.MARGIN+24):
                return k
        return None

    # Start from central quadrant interiors, then widen through the focal plane.
    order=sorted(range(len(qs)),key=lambda k:m.dist_arcsec(qs[k].center,med,med[1]))
    # Test the exact quadrant center plus modest interior offsets. This avoids
    # accidentally selecting a point that a later dither moves onto a gap.
    offsets=[(0,0),(250,0),(-250,0),(0,250),(0,-250),(300,300),(-300,300),(300,-300),(-300,-300)]
    for k in order:
        q=qs[k]
        for dx,dy in offsets:
            ra,de=q.w.pixel_to_world_values(m.NX/2+dx,m.NY/2+dy)
            ra=float(ra);de=float(de)
            routes=[predicted_route(ra,de,g) for g in range(4)]
            if all(x is not None for x in routes):
                print('PREDICTED_TARGET',{'source_k':k,'ra':ra,'dec':de,'routes':routes},flush=True)
                return int(routes[0]),ra,de,med
    raise RuntimeError('no all-four-pointing silicon target found in focal-plane search')

m.choose_target=robust_choose_target
m.main()
