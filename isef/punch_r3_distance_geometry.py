#!/usr/bin/env python3
"""Freeze target-blind observer-range geometry for C/2025 R3.

Uses JPL Horizons observer quantity 20 (delta, deldot) for the already frozen
primary and holdout timestamps. No PUNCH image or FITS file is opened.
"""
from __future__ import annotations

import json,time
from datetime import datetime,timedelta,timezone
from pathlib import Path

import astropy.units as u
from astropy.time import Time
from astroquery.jplhorizons import Horizons

OUT=Path('results/punch_r3_distance_geometry');OUT.mkdir(parents=True,exist_ok=True)
OBSERVER='500@399';DESIGNATION='C/2025 R3';CADENCE_MIN=8;BATCH=12;RETRIES=5
PRIMARY_START=datetime(2026,4,21,18,0,29,tzinfo=timezone.utc);PRIMARY_N=80
HOLDOUT_START=datetime(2026,4,22,4,56,29,tzinfo=timezone.utc);HOLDOUT_N=53
PIXEL_DEG=0.0225
AU_KM=float(u.au.to_value(u.km))


def epochs(start,n):return [start+timedelta(minutes=CADENCE_MIN*i) for i in range(n)]


def query(times):
    rows=[]
    for j in range(0,len(times),BATCH):
        chunk=times[j:j+BATCH];last=None
        for attempt in range(RETRIES):
            try:
                tab=Horizons(id=DESIGNATION,id_type='designation',location=OBSERVER,epochs=Time(chunk).jd.tolist()).ephemerides(quantities='20')
                break
            except Exception as exc:
                last=exc
                if attempt+1==RETRIES:raise RuntimeError('Horizons range query failed') from last
                time.sleep(2*(attempt+1))
        if len(tab)!=len(chunk):raise RuntimeError('Horizons row mismatch')
        for dt,r in zip(chunk,tab):
            delta=float(r['delta']);deldot=float(r['delta_rate']) if 'delta_rate' in r.colnames else float(r['deldot'])
            # Exact transverse plane scale corresponding to one nominal CTM pixel.
            km_per_pixel=delta*AU_KM*__import__('math').tan(__import__('math').radians(PIXEL_DEG))
            rows.append({'timestamp_utc':dt.isoformat().replace('+00:00','Z'),'delta_au':delta,'deldot_km_s':deldot,'projected_km_per_0p0225deg_pixel':km_per_pixel})
    return rows


def main():
    primary=query(epochs(PRIMARY_START,PRIMARY_N));holdout=query(epochs(HOLDOUT_START,HOLDOUT_N))
    if len(primary)!=PRIMARY_N or len(holdout)!=HOLDOUT_N:raise RuntimeError('incomplete frozen range geometry')
    allrows=primary+holdout
    report={
      'information_barrier':'JPL Horizons observer ephemeris only; no PUNCH target pixels or FITS values opened',
      'observer':OBSERVER,'designation':DESIGNATION,'horizons_quantity':'20 observer range & range-rate',
      'nominal_ctm_deg_per_pixel':PIXEL_DEG,
      'conversion_rule':'projected km per pixel = delta * AU_km * tan(0.0225 deg); report epoch-dependent scale/range rather than one image-tuned scale',
      'primary':primary,'holdout':holdout,
      'summary':{
        'delta_au_range':[min(r['delta_au'] for r in allrows),max(r['delta_au'] for r in allrows)],
        'projected_km_per_pixel_range':[min(r['projected_km_per_0p0225deg_pixel'] for r in allrows),max(r['projected_km_per_0p0225deg_pixel'] for r in allrows)],
        'deldot_km_s_range':[min(r['deldot_km_s'] for r in allrows),max(r['deldot_km_s'] for r in allrows)],
      },
      'gate':'PASS'
    }
    (OUT/'geometry.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report['summary'],indent=2,sort_keys=True));return 0

if __name__=='__main__':raise SystemExit(main())
