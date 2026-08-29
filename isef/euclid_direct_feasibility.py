#!/usr/bin/env python3
"""Run Stage-0 using direct WCS maps for all four Euclid dither groups.

This deliberately avoids inferring cross-quadrant routing from a global pointing
shift.  It maps all 144 SCI quadrant headers in representative epochs 0..3,
finds a fixed sky location with safe pixel margin in every group, then delegates
the 16-epoch stamp/photometry test to euclid_routed_feasibility.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import math
import numpy as np
import euclid_routed_feasibility as b

GROUP_MAPS = None
SELECTED = None


def map_group(g):
    qs = [None] * 144
    with ThreadPoolExecutor(max_workers=32) as ex:
        fs = {ex.submit(b.getq, g, k): k for k in range(144)}
        for f in as_completed(fs):
            qs[fs[f]] = f.result()
    return qs


def containing(qs, ra, dec, margin=b.MARGIN):
    hits = []
    for q in qs:
        try:
            if b.contains(q, ra, dec, margin):
                x, y = b.pix(q, ra, dec)
                edge = min(x, b.NX-x, y, b.NY-y)
                hits.append((edge, q.k))
        except Exception:
            pass
    return sorted(hits, reverse=True)


def find_common(maps):
    centers = np.array([q.center for q in maps[0]])
    med = (float(np.median(centers[:,0])), float(np.median(centers[:,1])))
    order = sorted(range(144), key=lambda k: b.dist_arcsec(maps[0][k].center, med, med[1]))
    # Search real epoch-0 detector interiors, not inferred focal-plane shifts.
    # Offsets span roughly +/-60 arcsec around each quadrant center so a target
    # can move away from gaps introduced by the ~125-354 arcsec dithers.
    offsets = [0, -20, 20, -40, 40, -60, 60]
    best = None
    for k in order:
        cra, cdec = maps[0][k].center
        cd = max(math.cos(math.radians(cdec)), 0.2)
        for dx in offsets:
            for dy in offsets:
                ra = cra + dx/(3600*cd)
                dec = cdec + dy/3600
                hs = [containing(m, ra, dec) for m in maps]
                n = sum(bool(h) for h in hs)
                if n == 4:
                    routes = {g: h[0][1] for g, h in enumerate(hs)}
                    score = min(h[0][0] for h in hs)
                    if best is None or score > best[0]:
                        best = (score, k, ra, dec, routes, med)
        # Once several central quadrants have been examined, a strong-margin
        # solution is sufficient; otherwise continue across the full mosaic.
        if best is not None and best[0] >= b.MARGIN + 100 and order.index(k) >= 15:
            break
    if best is None:
        raise RuntimeError('no sky target is safely covered in all four representative dither groups')
    return best


def patched_map_epoch0():
    return GROUP_MAPS[0]


def patched_choose_target(qs):
    score, k, ra, dec, routes, med = SELECTED
    return k, ra, dec, med


def patched_route_groups(qs, target, shifts):
    score, k0, ra, dec, routes, med = SELECTED
    diagnostics = []
    for g, k in routes.items():
        q = GROUP_MAPS[g][k]
        x, y = b.pix(q, ra, dec)
        diagnostics.append({'group': g, 'candidate_k': k, 'extname': q.name,
                            'x': float(x), 'y': float(y), 'inside': True,
                            'direct_wcs_map': True,
                            'edge_margin_pixels': float(min(x,b.NX-x,y,b.NY-y))})
    diagnostics.append({'selection_min_edge_margin_pixels': float(score)})
    return routes, diagnostics


def main():
    global GROUP_MAPS, SELECTED
    with ThreadPoolExecutor(max_workers=4) as ex:
        GROUP_MAPS = list(ex.map(map_group, range(4)))
    SELECTED = find_common(GROUP_MAPS)
    score, k, ra, dec, routes, med = SELECTED
    print('DIRECT_ROUTE', {'min_edge_margin_pixels': score, 'epoch0_k': k,
                           'ra': ra, 'dec': dec, 'routes': routes})
    b.map_epoch0 = patched_map_epoch0
    b.choose_target = patched_choose_target
    b.route_groups = patched_route_groups
    b.main()


if __name__ == '__main__':
    main()
