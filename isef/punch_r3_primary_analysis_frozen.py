#!/usr/bin/env python3
"""Frozen primary analysis for the PUNCH C/2025 R3 KH-like mode test.

IMPORTANT: committing/importing this file does NOT open target pixels. main()
refuses to run unless PUNCH_R3_TARGET_OPEN_AUTHORIZED=YES is explicitly set by
a later workflow after the preregistered spatial + temporal real-background
gates have both passed scientifically.

Primary only: 80 v0l epochs, 2026-04-21 18:00:29 through 2026-04-22
04:32:29 UTC. The 53-epoch late holdout is not referenced anywhere here.

Geometry is loaded from the immutable science-repo manifest pinned at commit
57f3f8f610535288870c9fd4b03aadca9ef0d645. The optional quadratic curvature
baseline failed control and is forbidden; extraction is around the raw
mechanical Horizons/WCS anti-solar axis.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import requests
from astropy.io import fits
from scipy.ndimage import map_coordinates
from scipy.optimize import least_squares

import punch_kh_real_background_controls_v2 as bg
import punch_kh_real_background_wave_gate as wg

OUT = Path('results/punch_r3_primary_analysis')
CACHE = OUT / 'cache'
ROOT = 'https://umbra.nascom.nasa.gov/punch/2/CTM/2026/'
MANIFEST_URL = ('https://raw.githubusercontent.com/brandonlign/isef/'
                '57f3f8f610535288870c9fd4b03aadca9ef0d645/'
                'research/PUNCH_R3_PRIMARY_ROI_MANIFEST.csv')
MANIFEST_SHA256 = '0a9ad1e8e47ce8c1cbb2e1d578ed1ab318dc6f90e07b972697e92761b309541b'
N = 80
NX = 512
NY = 81
DT_H = 8.0 / 60.0
CONFIRM_MIN_WAVE = 24.0
CONFIRM_MAX_WAVE = 80.0
NOMINAL_DEG_PER_PX = 0.0225

# Exact preregistered control thresholds. Injection relative-error thresholds
# are deliberately NOT target criteria because target truth is unknown.
PHASE_R2_MIN = 0.98
SPECTRAL_CONCENTRATION_MIN = 0.20
DBIC_MIN = 10.0
MIN_VALID = 0.98
MIN_ELIGIBLE = 0.90

bg.NX = NX
bg.NY = NY
bg.NT = N


def require_authorization() -> None:
    if os.environ.get('PUNCH_R3_TARGET_OPEN_AUTHORIZED') != 'YES':
        raise SystemExit(
            'REFUSING TARGET OPEN: set PUNCH_R3_TARGET_OPEN_AUTHORIZED=YES only '
            'after final frozen spatial and temporal gates pass scientifically.'
        )


def load_manifest():
    r = requests.get(MANIFEST_URL, timeout=(10, 30))
    r.raise_for_status()
    raw = r.content
    digest = hashlib.sha256(raw).hexdigest()
    if digest != MANIFEST_SHA256:
        raise RuntimeError(f'frozen manifest hash mismatch: {digest}')
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
    if len(rows) != N:
        raise RuntimeError(f'frozen manifest expected {N} rows, got {len(rows)}')
    expected_first = '2026-04-21T18:00:29Z'
    expected_last = '2026-04-22T04:32:29Z'
    if rows[0]['timestamp_utc'] != expected_first or rows[-1]['timestamp_utc'] != expected_last:
        raise RuntimeError('frozen primary partition timestamps changed')
    for i, row in enumerate(rows):
        if int(row['index']) != i or not row['relative_path'].endswith('_v0l.fits'):
            raise RuntimeError('manifest index/version invariant failed')
        for k in ('nucleus_x_0based','nucleus_y_0based','downstream_ux','downstream_uy',
                  'elongation_deg','antisolar_pa_deg'):
            row[k] = float(row[k])
    return rows


def curl_file(row):
    CACHE.mkdir(parents=True, exist_ok=True)
    rel = row['relative_path']
    name = Path(rel).name
    dest = CACHE / name
    url = ROOT + rel
    cmd = [
        'curl','--fail','--location','--show-error',
        '--retry','12','--retry-delay','5','--retry-max-time','900',
        '--retry-all-errors','--connect-timeout','30',
        '--speed-time','120','--speed-limit','1024',
        '--continue-at','-','--output',str(dest),url,
    ]
    subprocess.run(cmd, check=True)
    if not dest.exists() or dest.stat().st_size < 2880:
        raise RuntimeError(f'invalid target download: {name}')
    return dest


def extract_mechanical_strip(hdu, row):
    cx = row['nucleus_x_0based']; cy = row['nucleus_y_0based']
    u = np.asarray([row['downstream_ux'], row['downstream_uy']], float)
    if not np.isclose(np.linalg.norm(u), 1.0, atol=1e-8):
        raise RuntimeError('non-unit frozen downstream vector')
    v = np.asarray([-u[1], u[0]])
    s = np.arange(NX, dtype=float)
    q = np.arange(NY, dtype=float) - (NY-1)/2
    S,Q = np.meshgrid(s,q)
    xx = cx + S*u[0] + Q*v[0]
    yy = cy + S*u[1] + Q*v[1]
    x0=max(0,int(np.floor(xx.min()))-2);x1=min(4096,int(np.ceil(xx.max()))+3)
    y0=max(0,int(np.floor(yy.min()))-2);y1=min(4096,int(np.ceil(yy.max()))+3)
    if x0 <= 0 or y0 <= 0 or x1 >= 4096 or y1 >= 4096:
        raise RuntimeError('frozen target ROI unexpectedly touches mosaic boundary')
    tile = np.asarray(hdu.section[y0:y1,x0:x1], float)
    strip = map_coordinates(tile,[yy-y0,xx-x0],order=1,mode='nearest')
    if strip.shape != (NY,NX):
        raise RuntimeError('unexpected target strip shape')
    return strip


def read_primary_cube(rows):
    strips=[]
    file_meta=[]
    for i,row in enumerate(rows):
        print('PRIMARY',i+1,'/',N,row['timestamp_utc'],flush=True)
        path=curl_file(row)
        try:
            with fits.open(path,memmap=False) as h:
                if tuple(h[1].shape)!=(4096,4096):
                    raise RuntimeError('unexpected CTM science shape')
                # PRIMARY DATA ARRAY only. The uncertainty HDU is intentionally
                # not opened/used in this first preregistered primary analysis.
                strip=extract_mechanical_strip(h[1],row)
                hdr=h[1].header
                file_meta.append({
                    'filename':path.name,
                    'date_obs':str(hdr.get('DATE-OBS','')),
                    'bunit':str(hdr.get('BUNIT','')),
                    'finite_fraction':float(np.isfinite(strip).mean()),
                })
            strips.append(strip)
        finally:
            try:path.unlink()
            except OSError:pass
    return np.asarray(strips,float),file_meta


def standardize_cube(cube):
    """Same temporal-control normalization: per-frame median, pooled robust sigma."""
    meds=np.nanmedian(cube,axis=(1,2))
    centered=cube-meds[:,None,None]
    fm=np.nanmedian(np.abs(centered),axis=(1,2))
    scale=float(np.nanmedian(1.4826*fm))
    finite=np.isfinite(centered)
    if not np.isfinite(scale) or scale<=0:
        raise RuntimeError('invalid target pooled robust scale')
    if float(finite.mean()) < MIN_VALID:
        raise RuntimeError('target raw finite fraction below frozen minimum')
    z=centered/scale
    z[~finite]=0.0
    return z,meds,scale,float(finite.mean())


def fitcol_detailed(y,flux):
    """Exact primary Gaussian-ridge center fit, with diagnostics retained.

    Center result matches the control fitter algebra/bounds/loss; additional
    returned parameters do not change the optimization.
    """
    keep=np.abs(y)<=15
    yy=y[keep]; ff=np.asarray(flux[keep],float)
    good=np.isfinite(ff); yy=yy[good]; ff=ff[good]
    if len(ff)<12:return None
    edge=np.r_[ff[:4],ff[-4:]]
    b0=float(np.median(edge)); amp0=max(float(np.max(ff)-b0),.05)
    scale=max(float(np.std(ff)),1.0)
    p0=np.array([b0,0.,amp0,0.,3.])
    lo=np.array([b0-20*scale,-5*scale,0.,-15.,1.])
    hi=np.array([b0+20*scale,5*scale,max(100*scale,amp0*2),15.,8.])
    def model(p):
        b,m,a,c,s=p
        return b+m*yy+a*np.exp(-.5*((yy-c)/s)**2)
    try:
        f=least_squares(lambda p:ff-model(p),p0,bounds=(lo,hi),loss='soft_l1',f_scale=.5,max_nfev=400)
    except Exception:
        return None
    if not f.success:return None
    b,m,a,c,s=map(float,f.x)
    resid=ff-model(f.x)
    return {
        'background_intercept_z':b,
        'background_slope_z_per_px':m,
        'amplitude_z':a,
        'center_px':c,
        'sigma_width_px':s,
        'residual_rms_z':float(np.sqrt(np.mean(resid**2))),
        'cost':float(f.cost),
        'nfev':int(f.nfev),
    }


def fit_frame(args):
    i,img=args
    y=np.arange(NY,dtype=float)-(NY-1)/2
    rows=[]
    centers=np.full(NX,np.nan)
    for j in range(NX):
        r=fitcol_detailed(y,img[:,j])
        if r is not None:
            centers[j]=r['center_px']
            r['downstream_pixel']=j
        rows.append(r)
    return i,centers,rows


def primary_ridge(z):
    raw=np.full((N,NX),np.nan)
    details=[None]*N
    with ProcessPoolExecutor(max_workers=4) as pool:
        fut=[pool.submit(fit_frame,(i,z[i])) for i in range(N)]
        for f in as_completed(fut):
            i,c,d=f.result();raw[i]=c;details[i]=d
            print('RIDGE',i+1,'/',N,flush=True)
    clean,flag,eligible=bg.mask_center(raw)
    return raw,clean,flag,eligible,details


def centroid_centerline(z):
    """Frozen independent centroid diagnostic from passed non-target calibration."""
    y=np.arange(NY,dtype=float)-(NY-1)/2
    keep=np.abs(y)<=15; yy=y[keep]; edge=np.abs(yy)>=12
    out=np.full((N,NX),np.nan)
    for i in range(N):
        f=z[i,keep,:]
        for j in range(NX):
            col=f[:,j]; good=np.isfinite(col); eg=good&edge
            if good.sum()<24 or eg.sum()<6:continue
            A=np.column_stack([np.ones(eg.sum()),yy[eg]])
            try:coef=np.linalg.lstsq(A,col[eg],rcond=None)[0]
            except Exception:continue
            resid=col-(coef[0]+coef[1]*yy)
            w=np.clip(resid,0,None);w[~good]=0
            sw=float(np.sum(w))
            if np.isfinite(sw) and sw>1e-12:
                out[i,j]=float(np.sum(w*yy)/sw)
    return bg.mask_center(out)


def mode_fit(clean,eligible):
    # IMPORTANT: use the identical control estimator/search (6-80 px). The
    # target addendum does NOT retune the estimator. Instead, a selected mode
    # below 24 px is explicitly non-confirmatory/exploratory.
    t=np.arange(N,dtype=float)*DT_H
    return wg.infer_wave(clean,eligible,t)


def summarize_width(details,scale):
    per_frame=[]
    for frame in details:
        widths=[r['sigma_width_px'] for r in frame if r is not None and np.isfinite(r['sigma_width_px'])]
        amps=[r['amplitude_z']*scale for r in frame if r is not None and np.isfinite(r['amplitude_z'])]
        per_frame.append({
            'median_sigma_width_px':float(np.median(widths)) if widths else None,
            'p16_sigma_width_px':float(np.quantile(widths,.16)) if widths else None,
            'p84_sigma_width_px':float(np.quantile(widths,.84)) if widths else None,
            'median_peak_amplitude_native_units':float(np.median(amps)) if amps else None,
            'n_successful_columns':len(widths),
        })
    return per_frame


def target_decision(fit,clean,eligible):
    valid=float(np.isfinite(clean).mean())
    eligible_fraction=float(np.mean(eligible))
    status=fit.get('status')
    wave=float(fit.get('wavelength',np.nan)) if status=='OK' else float('nan')
    in_confirmatory=bool(np.isfinite(wave) and CONFIRM_MIN_WAVE<=wave<=CONFIRM_MAX_WAVE)
    four_periods=bool(np.isfinite(wave) and NX/wave>=4.0)
    statistical_pass=bool(
        status=='OK' and in_confirmatory and four_periods and
        fit.get('phase_r2',-np.inf)>=PHASE_R2_MIN and
        fit.get('spectral_concentration',-np.inf)>=SPECTRAL_CONCENTRATION_MIN and
        fit.get('growth_rate',0)>0 and
        fit.get('delta_bic_growth_over_step',-np.inf)>=DBIC_MIN and
        fit.get('delta_bic_growth_over_constant',-np.inf)>=DBIC_MIN and
        fit.get('delta_bic_growth_over_linear',-np.inf)>=DBIC_MIN and
        valid>=MIN_VALID and eligible_fraction>=MIN_ELIGIBLE
    )
    if statistical_pass:
        classification='STATISTICAL_KH_LIKE_COHERENT_GROWTH_PASS_PENDING_ARTIFACT_VETO'
    elif status=='OK' and fit.get('phase_r2',-np.inf)>=PHASE_R2_MIN and fit.get('spectral_concentration',-np.inf)>=SPECTRAL_CONCENTRATION_MIN and in_confirmatory:
        classification='COHERENT_MODE_WITHOUT_PREREGISTERED_FINITE_GROWTH_SUPPORT'
    elif status=='OK' and fit.get('growth_preferred',False):
        classification='AMPLITUDE_EVOLUTION_WITHOUT_CONFIRMATORY_COHERENT_MODE_SUPPORT'
    elif status=='OK' and not in_confirmatory:
        classification='SELECTED_MODE_OUTSIDE_CONFIRMATORY_24_80_PX_BAND'
    else:
        classification='NO_CONFIRMATORY_PRIMARY_MODE'
    return {
        'classification':classification,
        'statistical_pass_pending_artifact_veto':statistical_pass,
        'selected_mode_in_confirmatory_band':in_confirmatory,
        'four_period_support':four_periods,
        'valid_centerline_fraction':valid,
        'eligible_frame_fraction':eligible_fraction,
    }


def json_safe(v):
    if isinstance(v,np.ndarray):return v.tolist()
    if isinstance(v,(np.floating,)):return float(v)
    if isinstance(v,(np.integer,)):return int(v)
    if isinstance(v,(np.bool_,)):return bool(v)
    raise TypeError(type(v).__name__)


def main():
    require_authorization()
    OUT.mkdir(parents=True,exist_ok=True)
    rows=load_manifest()
    cube,file_meta=read_primary_cube(rows)
    z,frame_medians,pooled_scale,raw_finite=standardize_cube(cube)
    # Drop the raw image cube before fitting/reporting; target output retains
    # quantitative observables/diagnostics, not a hidden image-selection cache.
    del cube

    raw,clean,flag,eligible,details=primary_ridge(z)
    fit=mode_fit(clean,eligible)
    decision=target_decision(fit,clean,eligible)

    c_raw,c_clean,c_flag,c_eligible=centroid_centerline(z)
    c_fit=mode_fit(c_clean,c_eligible)
    secondary={
        'fit':c_fit,
        'valid_fraction':float(np.isfinite(c_clean).mean()),
        'eligible_frame_fraction':float(np.mean(c_eligible)),
        'calibrated_consistency_available':False,
    }
    if fit.get('status')=='OK' and c_fit.get('status')=='OK':
        wr=abs(c_fit['wavelength']-fit['wavelength'])/fit['wavelength']
        denom=max(abs(fit['phase_speed']),np.finfo(float).tiny)
        sr=abs(c_fit['phase_speed']-fit['phase_speed'])/denom
        sign=bool(np.sign(c_fit['phase_speed'])==np.sign(fit['phase_speed']))
        secondary.update({
            'wavelength_relative_difference':float(wr),
            'speed_relative_difference':float(sr),
            'same_propagation_sign':sign,
            'calibrated_consistency_available':True,
            'strengthened_phase_speed_consistency':bool(wr<=.10 and sr<=.15 and sign),
        })

    width=summarize_width(details,pooled_scale)
    wave_px=float(fit.get('wavelength',np.nan)) if fit.get('status')=='OK' else None
    speed_px_h=float(fit.get('phase_speed',np.nan)) if fit.get('status')=='OK' else None
    empirical_units={
        'wavelength_px':wave_px,
        'wavelength_deg_nominal':float(wave_px*NOMINAL_DEG_PER_PX) if wave_px is not None else None,
        'phase_speed_px_per_hour':speed_px_h,
        'phase_speed_deg_per_hour_nominal':float(speed_px_h*NOMINAL_DEG_PER_PX) if speed_px_h is not None else None,
        'growth_rate_per_hour':float(fit.get('growth_rate')) if fit.get('status')=='OK' else None,
    }

    report={
        'provenance':{
            'information_barrier_status':'PRIMARY OPENED BY EXPLICIT AUTHORIZATION; HOLDOUT REMAINS SEALED',
            'manifest_url':MANIFEST_URL,
            'manifest_sha256':MANIFEST_SHA256,
            'n_epochs':N,
            'first_timestamp':rows[0]['timestamp_utc'],
            'last_timestamp':rows[-1]['timestamp_utc'],
            'processing_version':'v0l only',
            'roi_shape':[NY,NX],
            'axis_rule':'raw frozen Horizons/WCS anti-solar axis; failed curvature baseline NOT used',
            'uncertainty_hdu_used':False,
            'holdout_accessed':False,
        },
        'normalization':{
            'rule':'per-frame ROI median subtraction + pooled median of 1.4826*frame MAD, matching final temporal control',
            'frame_medians_native_units':frame_medians.tolist(),
            'pooled_robust_sigma_native_units':pooled_scale,
            'raw_finite_fraction':raw_finite,
        },
        'primary_fit':fit,
        'primary_decision':decision,
        'empirical_units':empirical_units,
        'secondary_centroid':secondary,
        'per_frame_width_amplitude':width,
        'ridge_raw_center_px':raw.tolist(),
        'ridge_clean_center_px':clean.tolist(),
        'ridge_flag_mask':flag.tolist(),
        'ridge_frame_eligible':eligible.tolist(),
        'secondary_raw_center_px':c_raw.tolist(),
        'secondary_clean_center_px':c_clean.tolist(),
        'secondary_flag_mask':c_flag.tolist(),
        'secondary_frame_eligible':c_eligible.tolist(),
        'gaussian_fit_details':details,
        'file_metadata':file_meta,
        'interpretation_guardrail':'Statistical pass is not unique proof of KH and remains pending preregistered artifact/alternative veto review. No magnetic-field inference is authorized by this output.',
    }
    (OUT/'primary_result.json').write_text(json.dumps(report,indent=2,sort_keys=True,default=json_safe)+'\n')
    # Concise stdout avoids encouraging visual cherry-picking of the full arrays.
    print(json.dumps({
        'primary_decision':decision,
        'primary_fit':{k:fit.get(k) for k in ('status','wavelength','phase_speed','phase_r2','spectral_concentration','growth_rate','onset_index','saturation_index','delta_bic_growth_over_step','delta_bic_growth_over_constant','delta_bic_growth_over_linear','growth_preferred')},
        'secondary_consistency':{k:secondary.get(k) for k in ('calibrated_consistency_available','wavelength_relative_difference','speed_relative_difference','same_propagation_sign','strengthened_phase_speed_consistency')},
        'holdout_accessed':False,
    },indent=2,sort_keys=True))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
