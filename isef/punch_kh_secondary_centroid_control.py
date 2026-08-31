#!/usr/bin/env python3
"""Target-blind calibration of an independent secondary tail-center observable.

The primary observable remains the frozen robust Gaussian ridge. This script
calibrates a simpler background-subtracted transverse intensity centroid on one
fixed non-R3 PUNCH CTM snapshot across all eight final radial control fields.
It is a robustness diagnostic only and cannot replace the primary estimator.
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
from astropy.io import fits

import punch_kh_real_background_controls_v2 as bg
import punch_kh_real_background_wave_gate as wg
import punch_kh_long_oriented_spatial_gate as ls

OUT=Path('results/punch_kh_secondary_centroid_control');OUT.mkdir(parents=True,exist_ok=True)
NX=ls.NX;NY=ls.NY;NT=ls.NT
bg.NX=NX;bg.NY=NY;bg.NT=NT
WAVES=ls.WAVES


def centroid_centerline(frames,y):
    """Independent moment center after an edge-fit linear local background.

    The local window and edge bands are frozen here before target opening.
    No Gaussian profile or primary-ridge fit parameters are reused.
    """
    frames=np.asarray(frames,float); y=np.asarray(y,float)
    keep=np.abs(y)<=15
    yy=y[keep]
    edge=(np.abs(yy)>=12)
    A=np.column_stack([np.ones(edge.sum()),yy[edge]])
    pinv=np.linalg.pinv(A)
    out=np.full((frames.shape[0],frames.shape[2]),np.nan)
    for i in range(frames.shape[0]):
        f=frames[i,keep,:]
        for j in range(frames.shape[2]):
            col=f[:,j]
            good=np.isfinite(col)
            if good.sum()<24 or np.sum(good&edge)<6:continue
            eg=good&edge
            Ag=np.column_stack([np.ones(eg.sum()),yy[eg]])
            try:coef=np.linalg.lstsq(Ag,col[eg],rcond=None)[0]
            except Exception:continue
            resid=col-(coef[0]+coef[1]*yy)
            w=np.clip(resid,0,None)
            w[~good]=0
            sw=float(np.sum(w))
            if not np.isfinite(sw) or sw<=1e-12:continue
            out[i,j]=float(np.sum(w*yy)/sw)
    return out


def trial(label,z,wave):
    y,t,frames,truth=ls.inject(z,wave,'growth',0)
    raw=centroid_centerline(frames,y)
    clean,flag,elig=bg.mask_center(raw)
    fit=wg.infer_wave(clean,elig,t)
    good=np.isfinite(clean)&np.isfinite(truth)
    err=np.abs(clean[good]-truth[good]) if np.any(good) else np.asarray([np.inf])
    out={
        'field':label,'wavelength_true':wave,'fit':fit,
        'valid_fraction':float(np.mean(good)),
        'eligible_frame_fraction':float(np.mean(elig)),
        'p90_abs_error_px':float(np.quantile(err,.90)),
    }
    if fit.get('status')=='OK':
        out['wavelength_relerr']=abs(fit['wavelength']-wave)/wave
        out['speed_relerr']=abs(fit['phase_speed']-bg.SPEED)/bg.SPEED
        out['propagation_sign_correct']=bool(np.sign(fit['phase_speed'])==np.sign(bg.SPEED))
        out['phase_r2']=float(fit.get('phase_r2',np.nan))
        out['spectral_concentration']=float(fit.get('spectral_concentration',np.nan))
        out['diagnostic_recovery']=bool(out['wavelength_relerr']<=wg.POS_WAVELENGTH_RELERR_MAX and out['speed_relerr']<=wg.POS_SPEED_RELERR_MAX and out['propagation_sign_correct'])
    else:
        out['diagnostic_recovery']=False
    return out


def main():
    selected=bg.choose_files();name=selected[1][1];path=bg.download(name)
    trials=[]
    with fits.open(path,memmap=True) as h:
        data=h[1].data
        for label,field in ls.FIELDS.items():
            strip=ls.radial_source_strip(data,field);z,stats=bg.standardize(strip)
            if z is None:raise RuntimeError(f'invalid {label}: {stats}')
            for wave in WAVES:
                trials.append(trial(label,z,wave))
    ok=[r for r in trials if r.get('diagnostic_recovery')]
    valid=[r for r in trials if r['fit'].get('status')=='OK']
    summary={
        'n_trials':len(trials),
        'n_recovered':len(ok),
        'recovery_fraction':float(len(ok)/len(trials)),
        'minimum_valid_fraction':float(min(r['valid_fraction'] for r in trials)),
        'minimum_eligible_frame_fraction':float(min(r['eligible_frame_fraction'] for r in trials)),
        'p90_of_trial_p90_center_error_px':float(np.quantile([r['p90_abs_error_px'] for r in trials],.90)),
        'calibrated_wavelength_relerr_p95':float(np.quantile([r['wavelength_relerr'] for r in valid],.95)) if valid else None,
        'calibrated_speed_relerr_p95':float(np.quantile([r['speed_relerr'] for r in valid],.95)) if valid else None,
        'all_recovered_propagation_sign_correct':bool(all(r.get('propagation_sign_correct',False) for r in ok)) if ok else False,
        'by_wavelength':{str(int(w)):{'n':sum(r['wavelength_true']==w for r in trials),'recovery_fraction':float(np.mean([r['diagnostic_recovery'] for r in trials if r['wavelength_true']==w]))} for w in WAVES},
    }
    # This gate controls only whether the secondary observable is sufficiently
    # calibrated to support a robustness statement. It cannot affect the primary
    # Gaussian-ridge scientific classification.
    gate=(summary['recovery_fraction']>=.80 and summary['minimum_valid_fraction']>=.95 and summary['minimum_eligible_frame_fraction']>=.90 and summary['all_recovered_propagation_sign_correct'])
    summary['secondary_diagnostic_gate']='PASS' if gate else 'FAIL'
    report={
        'information_barrier':'one fixed 2025-09-21 non-R3 CTM file; zero R3 pixels',
        'role':'secondary robustness diagnostic only; primary Gaussian ridge remains authoritative',
        'file':name,'fields':list(ls.FIELDS),'wavelengths':WAVES,'peak_sigma':ls.PEAK,
        'centroid_rule':'within +/-15 px, least-squares linear background from |y|=12..15 px edges, nonnegative residual intensity moment; then frozen star mask',
        'trials':trials,'summary':summary,
    }
    (OUT/'summary.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,indent=2,sort_keys=True))
    return 0 if gate else 3


if __name__=='__main__':raise SystemExit(main())
