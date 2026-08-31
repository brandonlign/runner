#!/usr/bin/env python3
"""Freeze the exact 53-epoch C/2025 R3 late-holdout ROI geometry without image pixels.

Created while the repaired 80-epoch primary run was still executing and before
its scientific result was available.  The late-holdout timestamps are copied
from the pre-target protocol.  This program reads only Level-2 CTM FITS headers
plus matched JPL Horizons Sun/comet ephemerides.  It never indexes, decompresses,
or summarizes PRIMARY DATA ARRAY or UNCERTAINTY ARRAY values.

This freezes geometry only.  It does not authorize opening holdout science
pixels and cannot depend on the primary outcome.
"""
from __future__ import annotations

import csv
import hashlib
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

OUT=Path('results/punch_r3_holdout_roi_manifest')
OUT.mkdir(parents=True,exist_ok=True)
ROOT='https://umbra.nascom.nasa.gov/punch/2/CTM/2026/'
START=datetime(2026,4,22,4,56,29,tzinfo=timezone.utc)
N=53
CADENCE_MIN=8
EXPECTED_LAST=datetime(2026,4,22,11,52,29,tzinfo=timezone.utc)
NX=512
NY=81
OBSERVER='500@399'
RETRIES=5
CSV_FIELDS=('index','timestamp_utc','relative_path','nucleus_x_0based','nucleus_y_0based',
            'downstream_ux','downstream_uy','elongation_deg','antisolar_pa_deg')


def frozen_epochs():
    epochs=[START+timedelta(minutes=CADENCE_MIN*i) for i in range(N)]
    if epochs[-1]!=EXPECTED_LAST:raise RuntimeError('frozen late-holdout partition arithmetic changed')
    return epochs


def file_rel(dt):
    return f"{dt:%m/%d}/PUNCH_L2_CTM_{dt:%Y%m%d%H%M%S}_v0l.fits"


def eph(object_id,id_type,dt):
    last=None
    for k in range(RETRIES):
        try:
            return Horizons(id=object_id,id_type=id_type,location=OBSERVER,
                            epochs=Time(dt).jd).ephemerides(quantities='1')[0]
        except Exception as exc:
            last=exc;time.sleep(2*(k+1))
    raise RuntimeError(f'Horizons failed for {object_id}') from last


def roi_bounds(cx,cy,ux,uy):
    v=np.asarray([-uy,ux],float);s=np.arange(NX,dtype=float);q=np.arange(NY,dtype=float)-(NY-1)/2
    S,Q=np.meshgrid(s,q);xx=cx+S*ux+Q*v[0];yy=cy+S*uy+Q*v[1]
    return {'xmin':float(xx.min()),'xmax':float(xx.max()),'ymin':float(yy.min()),'ymax':float(yy.max())}


def main():
    rows=[];detail=[]
    for i,dt in enumerate(frozen_epochs()):
        rel=file_rel(dt);url=ROOT+rel
        comet_e=eph('C/2025 R3','designation',dt);sun_e=eph('10',None,dt)
        comet=SkyCoord(float(comet_e['RA'])*u.deg,float(comet_e['DEC'])*u.deg,frame='icrs')
        sun=SkyCoord(float(sun_e['RA'])*u.deg,float(sun_e['DEC'])*u.deg,frame='icrs')
        elong=float(comet.separation(sun).deg)
        anti=float((comet.position_angle(sun).deg+180.0)%360.0)
        downstream=comet.directional_offset_by(anti*u.deg,0.25*u.deg)

        # Header only: h[1].data and h[2].data are never referenced.
        last=None
        for k in range(RETRIES):
            try:
                with fits.open(url,use_fsspec=True,fsspec_kwargs={'block_size':1024*1024},
                               memmap=False,lazy_load_hdus=True) as h:
                    hdr=h[1].header.copy()
                break
            except Exception as exc:
                last=exc
                if k+1==RETRIES:raise RuntimeError(f'header fetch failed: {url}') from last
                time.sleep(2*(k+1))

        w=WCS(hdr,key='A');x,y=w.world_to_pixel(comet);xd,yd=w.world_to_pixel(downstream)
        dx,dy=float(xd-x),float(yd-y);norm=float(np.hypot(dx,dy))
        if not np.isfinite(norm) or norm<=0:raise RuntimeError('invalid downstream WCS tangent')
        ux,uy=dx/norm,dy/norm;bounds=roi_bounds(float(x),float(y),ux,uy)
        inside=(bounds['xmin']>=0 and bounds['ymin']>=0 and bounds['xmax']<4096 and bounds['ymax']<4096)
        radius=float(np.hypot(float(x)-2047.0,float(y)-2047.0));expected=elong/0.0225
        radial_agreement=abs(radius-expected)/expected
        if not inside or radial_agreement>=.10:raise RuntimeError(f'geometry sanity failure at {dt.isoformat()}')

        csvrow={
            'index':i,'timestamp_utc':dt.isoformat().replace('+00:00','Z'),'relative_path':rel,
            'nucleus_x_0based':float(x),'nucleus_y_0based':float(y),'downstream_ux':ux,'downstream_uy':uy,
            'elongation_deg':elong,'antisolar_pa_deg':anti,
        }
        rows.append(csvrow)
        detail.append({**csvrow,'comet_ra_deg':float(comet_e['RA']),'comet_dec_deg':float(comet_e['DEC']),
                       'sun_ra_deg':float(sun_e['RA']),'sun_dec_deg':float(sun_e['DEC']),
                       'radius_px':radius,'expected_radius_px':expected,
                       'radial_agreement_fraction':radial_agreement,'roi_bounds':bounds})
        print(f'{i+1}/{N} {dt.isoformat()} nucleus=({x:.3f},{y:.3f}) u=({ux:.6f},{uy:.6f})',flush=True)

    csvpath=OUT/'holdout_manifest.csv'
    with csvpath.open('w',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=CSV_FIELDS);wr.writeheader();wr.writerows(rows)
    digest=hashlib.sha256(csvpath.read_bytes()).hexdigest()
    report={
        'information_barrier':'53 frozen late-holdout R3 CTM headers + matched Horizons only; zero science/uncertainty pixel values decoded',
        'partition':'late-evolution holdout only','n_epochs':N,'cadence_min':CADENCE_MIN,
        'first_timestamp':rows[0]['timestamp_utc'],'last_timestamp':rows[-1]['timestamp_utc'],
        'roi_shape':[NY,NX],
        'roi_rule':'identical to primary: start at Horizons/WCS nucleus and extend 512 pixels along local anti-solar tangent; cross-tail width 81 pixels',
        'processing_version':'v0l only','manifest_sha256':digest,'rows':detail,'gate':'PASS',
        'holdout_science_pixels_opened':False,
    }
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'gate':'PASS','n_epochs':N,'first':rows[0]['timestamp_utc'],'last':rows[-1]['timestamp_utc'],
                      'manifest_sha256':digest,
                      'nucleus_x_range':[min(r['nucleus_x_0based'] for r in rows),max(r['nucleus_x_0based'] for r in rows)],
                      'nucleus_y_range':[min(r['nucleus_y_0based'] for r in rows),max(r['nucleus_y_0based'] for r in rows)],
                      'elongation_deg_range':[min(r['elongation_deg'] for r in rows),max(r['elongation_deg'] for r in rows)],
                      'max_radial_agreement_fraction':max(r['radial_agreement_fraction'] for r in detail),
                      'holdout_science_pixels_opened':False},indent=2))


if __name__=='__main__':main()
