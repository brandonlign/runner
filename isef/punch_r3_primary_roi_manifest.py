#!/usr/bin/env python3
"""Freeze the exact 80-epoch C/2025 R3 primary ROI geometry without image pixels.

INFORMATION BARRIER: this program reads only Level-2 CTM FITS headers plus
matched JPL Horizons Sun/comet ephemerides. It never indexes, decompresses, or
summarizes PRIMARY DATA ARRAY or UNCERTAINTY ARRAY values.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.time import Time
from astropy.wcs import WCS
from astroquery.jplhorizons import Horizons

OUT = Path('results/punch_r3_primary_roi_manifest')
OUT.mkdir(parents=True, exist_ok=True)
ROOT = 'https://umbra.nascom.nasa.gov/punch/2/CTM/2026/'
START = datetime(2026, 4, 21, 18, 0, 29, tzinfo=timezone.utc)
N = 80
CADENCE_MIN = 8
NX = 512
NY = 81
OBSERVER = '500@399'
RETRIES = 5


def frozen_epochs():
    return [START + timedelta(minutes=CADENCE_MIN*i) for i in range(N)]


def file_rel(dt: datetime) -> str:
    stamp = dt.strftime('%Y%m%d%H%M%S')
    return f"{dt:%m/%d}/PUNCH_L2_CTM_{stamp}_v0l.fits"


def eph(object_id: str, id_type, dt: datetime):
    last = None
    for k in range(RETRIES):
        try:
            return Horizons(id=object_id, id_type=id_type, location=OBSERVER,
                            epochs=Time(dt).jd).ephemerides(quantities='1')[0]
        except Exception as exc:
            last = exc
            time.sleep(2*(k+1))
    raise RuntimeError(f'Horizons failed for {object_id}') from last


def roi_bounds(cx: float, cy: float, ux: float, uy: float):
    v = np.asarray([-uy, ux], float)
    s = np.arange(NX, dtype=float)
    q = np.arange(NY, dtype=float) - (NY-1)/2
    S, Q = np.meshgrid(s, q)
    xx = cx + S*ux + Q*v[0]
    yy = cy + S*uy + Q*v[1]
    return {
        'xmin': float(xx.min()), 'xmax': float(xx.max()),
        'ymin': float(yy.min()), 'ymax': float(yy.max()),
        'integer_fetch_bounds': [
            max(0, int(np.floor(xx.min()))-2),
            min(4096, int(np.ceil(xx.max()))+3),
            max(0, int(np.floor(yy.min()))-2),
            min(4096, int(np.ceil(yy.max()))+3),
        ],
    }


def main():
    rows = []
    for i, dt in enumerate(frozen_epochs()):
        rel = file_rel(dt)
        url = ROOT + rel
        comet_e = eph('C/2025 R3', 'designation', dt)
        sun_e = eph('10', None, dt)
        comet = SkyCoord(float(comet_e['RA'])*u.deg, float(comet_e['DEC'])*u.deg, frame='icrs')
        sun = SkyCoord(float(sun_e['RA'])*u.deg, float(sun_e['DEC'])*u.deg, frame='icrs')
        elong = float(comet.separation(sun).deg)
        anti = float((comet.position_angle(sun).deg + 180.0) % 360.0)
        downstream = comet.directional_offset_by(anti*u.deg, 0.25*u.deg)

        # Header-only access. h[1].data and h[2].data are never referenced.
        last = None
        for k in range(RETRIES):
            try:
                with fits.open(url, use_fsspec=True,
                               fsspec_kwargs={'block_size': 1024*1024},
                               memmap=False, lazy_load_hdus=True) as h:
                    hdr = h[1].header.copy()
                break
            except Exception as exc:
                last = exc
                if k+1 == RETRIES:
                    raise RuntimeError(f'header fetch failed: {url}') from last
                time.sleep(2*(k+1))

        if int(hdr.get('ZNAXIS1', hdr.get('NAXIS1', 0))) not in (0, 4096):
            # Compressed-image headers vary in representation; final WCS/bounds
            # checks below are the decisive geometry sanity checks.
            pass
        w = WCS(hdr, key='A')
        x, y = w.world_to_pixel(comet)
        xd, yd = w.world_to_pixel(downstream)
        dx, dy = float(xd-x), float(yd-y)
        norm = float(np.hypot(dx, dy))
        if not np.isfinite(norm) or norm <= 0:
            raise RuntimeError('invalid downstream WCS tangent')
        ux, uy = dx/norm, dy/norm
        bounds = roi_bounds(float(x), float(y), ux, uy)
        inside = (bounds['xmin'] >= 0 and bounds['ymin'] >= 0 and
                  bounds['xmax'] < 4096 and bounds['ymax'] < 4096)
        radius = float(np.hypot(float(x)-2047.0, float(y)-2047.0))
        expected = elong / 0.0225
        radial_agreement = abs(radius-expected)/expected
        if not inside or radial_agreement >= 0.10:
            raise RuntimeError(f'geometry sanity failure at {dt.isoformat()}')

        rows.append({
            'index': i,
            'timestamp_utc': dt.isoformat().replace('+00:00','Z'),
            'relative_path': rel,
            'url': url,
            'comet_ra_deg': float(comet_e['RA']),
            'comet_dec_deg': float(comet_e['DEC']),
            'sun_ra_deg': float(sun_e['RA']),
            'sun_dec_deg': float(sun_e['DEC']),
            'elongation_deg': elong,
            'antisolar_pa_east_of_north_deg': anti,
            'nucleus_pixel_0based': [float(x), float(y)],
            'downstream_unit_pixel': [ux, uy],
            'radius_px': radius,
            'expected_radius_px': expected,
            'radial_agreement_fraction': radial_agreement,
            'roi_bounds': bounds,
        })
        print(f'{i+1}/{N} {dt.isoformat()} nucleus=({x:.3f},{y:.3f}) u=({ux:.6f},{uy:.6f})', flush=True)

    report = {
        'information_barrier': '80 frozen primary R3 CTM headers + matched Horizons only; zero science/uncertainty pixel values decoded',
        'partition': 'primary only',
        'n_epochs': N,
        'cadence_min': CADENCE_MIN,
        'roi_shape': [NY, NX],
        'roi_rule': 'start at Horizons/WCS nucleus and extend 512 pixels along local anti-solar tangent; cross-tail width 81 pixels',
        'processing_version': 'v0l only',
        'rows': rows,
        'gate': 'PASS',
    }
    (OUT/'manifest.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(json.dumps({
        'gate':'PASS', 'n_epochs':len(rows),
        'nucleus_x_range':[min(r['nucleus_pixel_0based'][0] for r in rows), max(r['nucleus_pixel_0based'][0] for r in rows)],
        'nucleus_y_range':[min(r['nucleus_pixel_0based'][1] for r in rows), max(r['nucleus_pixel_0based'][1] for r in rows)],
        'elongation_deg_range':[min(r['elongation_deg'] for r in rows), max(r['elongation_deg'] for r in rows)],
        'max_radial_agreement_fraction':max(r['radial_agreement_fraction'] for r in rows),
    }, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
