#!/usr/bin/env python3
"""Frozen Stage-5 post-prime known-binary recoverability pilot.

Science contract:
  brandonlign/isef research/TESS_BINARY_STAGE5_RECOVERABILITY_PILOT_PROTOCOL_2026-09-01.md

This script is DEVELOPMENT ONLY. It must never be run on FINAL_VALIDATION_40.
It uses one fixed tess-asteroids raw-FFI extraction and AP photometry, then the
existing frozen Stage-0 rotation+BLS machinery. It does not apply Stage-4.
"""
from __future__ import annotations
import argparse, json, traceback
from pathlib import Path
import numpy as np
from astropy.io import fits
from tess_asteroids import MovingTPF, __version__ as tess_asteroids_version
import tess_binary_stage0_detector as s0

OUT=Path('results/tess_binary_stage5_recoverability_pilot')
OUT.mkdir(parents=True,exist_ok=True)
FINAL_HOLDOUT={1717,3658,7930,5772,6265,6177,3865,13123,9006,2478,20882,37424,4788,3220,8297,9972,1052,4370,4494,4383,2500,15430,18301,2871,1089,9940,4092,5781,3187,24106,4607,6098,9617,1526,4666,9260,46829,5872,118303,6809}


def fracerr(x,truth): return abs(float(x)-float(truth))/float(truth)


def analyze_ap(path: Path, p_orb_d: float):
    with fits.open(path,memmap=False) as h:
        d=h['LIGHTCURVE_AP'].data; names=set(d.names or [])
        t=np.asarray(d['TIME'],float); y=np.asarray(d['TESSMAG'],float)
        dy=np.asarray(d['TESSMAG_ERR'],float) if 'TESSMAG_ERR' in names else None
        q=np.asarray(d['QUALITY']) if 'QUALITY' in names else np.zeros(len(t),int)
        good=np.isfinite(t)&np.isfinite(y)&(q==0)
        if dy is not None: good &= np.isfinite(dy)&(dy>0)
        if 'AP_QUALITY' in names:
            aq=np.asarray(d['AP_QUALITY']); good &= np.isfinite(aq)&(aq==0)
        t=t[good]; y=y[good]; dy=dy[good] if dy is not None else None
    rep={'n_good':int(len(t)),'baseline_d':float(t.max()-t.min()) if len(t)>1 else 0.0,'eligible':False}
    if len(t)<s0.MIN_N or rep['baseline_d']<s0.MIN_BASELINE_D: return rep
    # Fixed Stage-0 rotational model followed by frozen BLS scan.
    rot,rm=s0.fit_rotation(t,y,dy); resid=y-rot
    b,_=s0.scan_bls(t,resid,dy)
    bp=float(b['period_d']); aliases={'half_orbit_d':p_orb_d/2.0,'orbit_d':p_orb_d}
    errs={k:fracerr(bp,v) for k,v in aliases.items()}
    rep.update({'eligible':True,'rotation':rm,'bls':b,'external_aliases':aliases,
                'fractional_errors':errs,'period_recovery':bool(min(errs.values())<=0.05),
                'best_alias':min(errs,key=errs.get),'best_alias_fractional_error':float(min(errs.values()))})
    return rep


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--number',type=int,required=True); ap.add_argument('--period-days',type=float,required=True); ap.add_argument('--sectors',required=True)
    a=ap.parse_args(); sectors=[int(x) for x in a.sectors.split(',') if x]
    if a.number in FINAL_HOLDOUT: raise RuntimeError('REFUSING TO OPEN FINAL_VALIDATION_40 IDENTITY')
    objdir=OUT/str(a.number); objdir.mkdir(parents=True,exist_ok=True)
    rows=[]
    for sector in sectors:
        row={'number':a.number,'sector':sector,'external_orbit_period_d':a.period_days,'science_role':'development'}
        secdir=objdir/f'sector_{sector}'; secdir.mkdir(parents=True,exist_ok=True)
        try:
            mt=MovingTPF.from_name(str(a.number),sector=sector)
            row.update({'camera':int(mt.camera),'ccd':int(mt.ccd),'ephemeris_rows':int(len(mt.ephem))})
            mt.make_tpf(shape=(11,11),bg_method='linear_model',ap_method='prf',save=True,outdir=str(secdir))
            mt.make_lc(method='all',save=True,outdir=str(secdir))
            lcs=list(secdir.glob('*_lc.fits'))
            if len(lcs)!=1: raise RuntimeError(f'expected one LC FITS, got {lcs}')
            row['analysis']=analyze_ap(lcs[0],a.period_days)
        except Exception as e:
            row['error']=f'{type(e).__name__}: {e}'; row['traceback']=traceback.format_exc(limit=4)
        rows.append(row); print(json.dumps(row,sort_keys=True),flush=True)
    eligible=any(r.get('analysis',{}).get('eligible',False) for r in rows)
    recovered=any(r.get('analysis',{}).get('period_recovery',False) for r in rows)
    rep={'protocol':'TESS_BINARY_STAGE5_RECOVERABILITY_PILOT_PROTOCOL_2026-09-01.md','number':a.number,
         'external_orbit_period_d':a.period_days,'frozen_sectors':sectors,'tess_asteroids_version':tess_asteroids_version,
         'final_validation_identity':False,'year8_values_opened':False,'object_has_eligible_sector':eligible,
         'object_recovered':recovered,'sectors':rows}
    (objdir/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print('OBJECT_RESULT '+json.dumps({'number':a.number,'eligible':eligible,'recovered':recovered},sort_keys=True))

if __name__=='__main__': main()
