#!/usr/bin/env python3
"""Outcome-independent dimensionless summaries for the frozen PUNCH R3 primary.

Created before repaired primary workflow 33410414475 returned a scientific
result.  This script only derives quantities already permitted by the frozen
physics-interpretation protocol from primary_result.json.  It defines no new
pass/fail threshold and cannot alter the frozen primary classification.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

ROOT=Path('results/punch_r3_primary_analysis')
IN=ROOT/'primary_result.json'
OUT=ROOT/'dimensionless_primary.json'
GAUSS_FWHM_PER_SIGMA=2.0*math.sqrt(2.0*math.log(2.0))


def finite_summary(a):
    x=np.asarray(a,float);x=x[np.isfinite(x)]
    if len(x)==0:return {'n':0,'median':None,'p16':None,'p84':None}
    return {'n':int(len(x)),'median':float(np.median(x)),
            'p16':float(np.quantile(x,.16)),'p84':float(np.quantile(x,.84))}


def main():
    if not IN.exists():raise SystemExit('primary_result.json is required')
    d=json.loads(IN.read_text());fit=d.get('primary_fit',{});decision=d.get('primary_decision',{})
    widths=np.asarray([np.nan if r.get('median_sigma_width_px') is None else r['median_sigma_width_px']
                       for r in d.get('per_frame_width_amplitude',[])],float)
    clean=np.asarray(d.get('ridge_clean_center_px',[]),float)
    elig=np.asarray(d.get('ridge_frame_eligible',[]),bool)
    if clean.shape!=(80,512) or elig.shape!=(80,) or widths.shape!=(80,):
        raise RuntimeError('frozen primary array/width dimensions changed')
    rowgood=elig & np.all(np.isfinite(clean),axis=1)
    selected_widths=widths[rowgood]
    fwhm=selected_widths*GAUSS_FWHM_PER_SIGMA

    status=fit.get('status');wave=float(fit['wavelength']) if status=='OK' else float('nan')
    speed=float(fit['phase_speed']) if status=='OK' else float('nan')
    gamma=float(fit['growth_rate']) if status=='OK' else float('nan')
    amp=np.asarray(fit.get('mode_amplitude',[]),float) if status=='OK' else np.asarray([],float)
    if status=='OK' and len(amp)!=int(np.sum(rowgood)):
        raise RuntimeError('mode-amplitude/frame alignment invariant failed')

    ratio_amp_sigma=amp/selected_widths if len(amp) else np.asarray([],float)
    ratio_amp_fwhm=amp/fwhm if len(amp) else np.asarray([],float)
    med_sigma=float(np.nanmedian(selected_widths)) if np.any(np.isfinite(selected_widths)) else float('nan')
    med_fwhm=med_sigma*GAUSS_FWHM_PER_SIGMA if np.isfinite(med_sigma) else float('nan')

    positive_gamma=bool(np.isfinite(gamma) and gamma>0)
    nonzero_speed=bool(np.isfinite(speed) and abs(speed)>np.finfo(float).tiny)
    mode_ok=bool(np.isfinite(wave) and wave>0)
    growth_advection=(gamma*wave/(2*math.pi*abs(speed))) if positive_gamma and nonzero_speed and mode_ok else None
    efold_h=(1.0/gamma) if positive_gamma else None
    advect_px_efold=(abs(speed)/gamma) if positive_gamma and nonzero_speed else None

    out={
        'role':'derived reporting quantities only; no new thresholds and no classification change',
        'primary_classification_unchanged':decision.get('classification'),
        'primary_statistical_pass_pending_artifact_veto':decision.get('statistical_pass_pending_artifact_veto'),
        'complete_eligible_frame_count':int(np.sum(rowgood)),
        'tail_gaussian_sigma_width_px':finite_summary(selected_widths),
        'tail_gaussian_fwhm_width_px':finite_summary(fwhm),
        'mode_amplitude_px':finite_summary(amp),
        'mode_amplitude_over_gaussian_sigma_width':finite_summary(ratio_amp_sigma),
        'mode_amplitude_over_gaussian_fwhm_width':finite_summary(ratio_amp_fwhm),
        'selected_wavelength_px':float(wave) if np.isfinite(wave) else None,
        'phase_pattern_speed_px_per_hour':float(speed) if np.isfinite(speed) else None,
        'growth_rate_per_hour':float(gamma) if np.isfinite(gamma) else None,
        'growth_efolding_time_hours':efold_h,
        'wavelength_over_median_gaussian_sigma_width':float(wave/med_sigma) if mode_ok and np.isfinite(med_sigma) and med_sigma>0 else None,
        'wavelength_over_median_gaussian_fwhm_width':float(wave/med_fwhm) if mode_ok and np.isfinite(med_fwhm) and med_fwhm>0 else None,
        'growth_advection_gamma_lambda_over_2pi_abs_vphase':float(growth_advection) if growth_advection is not None else None,
        'projected_advective_distance_per_efold_px':float(advect_px_efold) if advect_px_efold is not None else None,
        'projected_advective_wavelengths_per_efold':float(advect_px_efold/wave) if advect_px_efold is not None and mode_ok else None,
        'definitions':{
            'width':'per-frame median fitted Gaussian sigma from frozen primary ridge; FWHM is exact Gaussian conversion 2*sqrt(2 ln 2)*sigma',
            'growth_advection':'gamma*lambda/(2*pi*abs(v_phase)); dimensionless magnitude, with v_phase retained separately as signed projected pattern speed',
            'amplitude':'Fourier mode transverse ridge-displacement amplitude returned by the frozen estimator, in pixels; not brightness amplitude',
        },
        'holdout_accessed':False,
    }
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))


if __name__=='__main__':main()
