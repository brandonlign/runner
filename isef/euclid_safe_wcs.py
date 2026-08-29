#!/usr/bin/env python3
"""Normalize Astropy scalar WCS outputs for arbitrary Euclid sky targets."""
import numpy as np

def apply(module):
    raw=module.pix
    if getattr(raw,'_euclid_scalarized',False):return
    def scalar(q,ra,de):
        x,y=raw(q,ra,de);return float(np.asarray(x)),float(np.asarray(y))
    scalar._euclid_scalarized=True
    module.pix=scalar
