#!/usr/bin/env python3
"""Check whether the existing raw-FFI tess-asteroids extraction of 6764 preserves its known binary signal.

6764 is already-consumed development data. This is infrastructure validation,
not a new confirmatory test and not a detector threshold-selection run. The
script reads the saved extraction artifact from run 33450624985 and tests both
aperture and PSF TESS-magnitude products with the existing fixed BLS grid.
No Year-8 or fresh post-prime object is opened.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
from astropy.io import fits
from astropy.timeseries import LombScargle
import tess_binary_stage0_detector as s0

KNOWN_ORBIT_H=30.41
KNOWN_EVENT_SPACING_H=KNOWN_ORBIT_H/2.0
KNOWN_ROT_H=4.739
OUT=Path('results/tess_binary_6764_raw_recovery'); OUT.mkdir(parents=True,exist_ok=True)


def robust_ls_period_h(t,y,dy,pmin_h=2.0,pmax_h=50.0):
    base=float(t.max()-t.min()); fmin=24/pmax_h; fmax=24/pmin_h; df=1/(5*base)
    freq=np.arange(fmin,fmax+0.5*df,df)
    ls=LombScargle(t,y-np.median(y),dy,fit_mean=True,center_data=True)
    p=np.asarray(ls.power(freq),float); j=int(np.nanargmax(p))
    return float(24/freq[j]),float(p[j])


def match_frac(x,truth): return abs(float(x)-float(truth))/float(truth)


def analyze_table(path,extname):
    with fits.open(path,memmap=False) as h:
        d=h[extname].data
        names=set(d.names or [])
        t=np.asarray(d['TIME'],float); y=np.asarray(d['TESSMAG'],float)
        dy=np.asarray(d['TESSMAG_ERR'],float) if 'TESSMAG_ERR' in names else None
        q=np.asarray(d['QUALITY']) if 'QUALITY' in names else np.zeros(len(t),int)
        good=np.isfinite(t)&np.isfinite(y)&(q==0)
        if dy is not None: good &= np.isfinite(dy)&(dy>0)
        if extname=='LIGHTCURVE_AP' and 'AP_QUALITY' in names:
            aq=np.asarray(d['AP_QUALITY']); good &= np.isfinite(aq)&(aq==0)
        t=t[good]; y=y[good]; dy=dy[good] if dy is not None else None
    rep={'extname':extname,'n_good':int(len(t)),'baseline_d':float(t.max()-t.min()) if len(t)>1 else 0.0}
    if len(t)<s0.MIN_N or rep['baseline_d']<s0.MIN_BASELINE_D:
        rep['eligible']=False; return rep
    rep['eligible']=True
    b,_=s0.scan_bls(t,y-np.median(y),dy)
    ls_h,ls_power=robust_ls_period_h(t,y,dy)
    event_h=float(b['period_d']*24)
    rep.update({'bls':b,'bls_period_h':event_h,'ls_peak_period_h':ls_h,'ls_peak_power':ls_power,
        'event_spacing_fractional_error':match_frac(event_h,KNOWN_EVENT_SPACING_H),
        'orbit_fractional_error_if_2p':match_frac(2*event_h,KNOWN_ORBIT_H),
        'rotation_fractional_error_direct':match_frac(ls_h,KNOWN_ROT_H),
        'rotation_fractional_error_half_alias':match_frac(2*ls_h,KNOWN_ROT_H),
        'rotation_fractional_error_double_alias':match_frac(0.5*ls_h,KNOWN_ROT_H),
        'event_spacing_within_10pct':bool(match_frac(event_h,KNOWN_EVENT_SPACING_H)<=0.10),
        'orbit_2p_within_10pct':bool(match_frac(2*event_h,KNOWN_ORBIT_H)<=0.10),
        'rotation_or_simple_alias_within_10pct':bool(min(match_frac(ls_h,KNOWN_ROT_H),match_frac(2*ls_h,KNOWN_ROT_H),match_frac(0.5*ls_h,KNOWN_ROT_H))<=0.10)})
    return rep


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('artifact_root'); a=ap.parse_args()
    root=Path(a.artifact_root); files=list(root.rglob('*_lc.fits'))
    if len(files)!=1: raise RuntimeError(f'expected one extracted LC FITS; found {files}')
    path=files[0]
    tables=[analyze_table(path,'LIGHTCURVE_AP'),analyze_table(path,'LIGHTCURVE_PSF')]
    usable=[z for z in tables if z.get('eligible')]
    recovery=bool(any(z.get('event_spacing_within_10pct') or z.get('orbit_2p_within_10pct') for z in usable))
    rep={'role':'raw-FFI extraction infrastructure recovery on already-consumed 6764 only',
         'source_artifact_run':33450624985,'source_artifact_id':9779845288,'known_orbit_h':KNOWN_ORBIT_H,
         'known_event_spacing_h':KNOWN_EVENT_SPACING_H,'known_rotation_h':KNOWN_ROT_H,'year8_values_opened':False,
         'fresh_postprime_values_opened':False,'tables':tables,'raw_extraction_preserves_known_event_period_within_10pct':recovery}
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps(rep,indent=2,sort_keys=True,allow_nan=False))
    raise SystemExit(0 if recovery else 8)

if __name__=='__main__': main()
