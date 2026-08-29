#!/usr/bin/env python3
"""Use a wide geometric proposal radius; exact WCS still decides acceptance."""
import math
import numpy as np
import euclid_shiftselect_feasibility as s


def approx_hit(ra,dec):
    cd=max(math.cos(math.radians(dec)),0.2)
    d=np.hypot((s.CENTERS[:,0]-ra)*cd,s.CENTERS[:,1]-dec)*3600
    order=np.argsort(d)[:4]
    for k in order:
        arc=float(d[k])
        if arc<140:return (1500-arc/0.1,int(k))
    return None

# Astropy 7 may return zero-dimensional ndarrays for scalar WCS inputs.  The
# base probe legitimately uses vector WCS later, so normalize only scalar
# results at the shared pix() boundary.
_orig_pix=s.b.pix
def scalar_pix(q,ra,dec):
    x,y=_orig_pix(q,ra,dec)
    if np.ndim(x)==0 and np.ndim(y)==0:return float(x),float(y)
    return x,y

s.approx_hit=approx_hit
s.b.pix=scalar_pix
s.main()
