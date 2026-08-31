#!/usr/bin/env python3
"""Frozen post-primary diagnostics for PUNCH C/2025 R3.

Created while the repaired authorized primary run was still executing and before
any scientific primary result was available.  This file implements only the
already-preregistered artifact-review views:

* exact primary indices 0,10,20,30,40,50,60,70,79;
* each entire mechanically extracted 512x81 strip with the already-frozen
  Gaussian ridge overlaid;
* complete 80x512 cleaned-centerline time-distance view;
* complete width, amplitude, flagged-fraction, and eligibility series;
* primary comet mosaic-position series for detector/mosaic-systematic review.

It cannot alter the primary classification, estimator, mask, axis, wavelength
band, model set, or time interval.  It does not reference the 53-epoch holdout.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits

import punch_r3_primary_analysis_frozen as p
import punch_r3_primary_analysis_locked as locked

FIXED_INDICES=(0,10,20,30,40,50,60,70,79)
OUT=p.OUT/'artifact_review'


def require_primary_authorization():
    if os.environ.get('PUNCH_R3_TARGET_OPEN_AUTHORIZED')!='YES':
        raise SystemExit('REFUSING PRIMARY DIAGNOSTIC OPEN without exact authorization')


def robust_display_z(strip):
    """Fixed display-only normalization; never used in a scientific decision."""
    a=np.asarray(strip,float)
    med=float(np.nanmedian(a))
    mad=float(np.nanmedian(np.abs(a-med)))
    scale=1.4826*mad
    if not np.isfinite(scale) or scale<=0:scale=1.0
    z=(a-med)/scale
    return z,med,scale


def render_fixed_strips(report,rows):
    raw=np.asarray(report['ridge_raw_center_px'],float)
    clean=np.asarray(report['ridge_clean_center_px'],float)
    rendered=[]
    for idx in FIXED_INDICES:
        row=rows[idx]
        path=p.curl_file(row)
        try:
            with fits.open(path,memmap=False) as h:
                if tuple(h[1].shape)!=(4096,4096):raise RuntimeError('unexpected CTM science shape')
                strip=p.extract_mechanical_strip(h[1],row)
            z,med,scale=robust_display_z(strip)
            fig,ax=plt.subplots(figsize=(12,3.5))
            ax.imshow(z,origin='lower',aspect='auto',extent=[0,p.NX-1,-(p.NY-1)/2,(p.NY-1)/2],
                      cmap='gray',vmin=-4,vmax=8,interpolation='nearest')
            x=np.arange(p.NX)
            ax.plot(x,raw[idx],linewidth=.7,label='raw frozen Gaussian ridge')
            ax.plot(x,clean[idx],linewidth=1.1,label='cleaned frozen Gaussian ridge')
            ax.set_xlim(0,p.NX-1);ax.set_ylim(-(p.NY-1)/2,(p.NY-1)/2)
            ax.set_xlabel('downstream pixel');ax.set_ylabel('cross-tail pixel')
            ax.set_title(f"Frozen primary frame {idx}: {row['timestamp_utc']}")
            ax.legend(loc='upper right',fontsize=7)
            fig.tight_layout()
            fn=OUT/f'fixed_strip_{idx:02d}.png';fig.savefig(fn,dpi=160);plt.close(fig)
            rendered.append({'index':idx,'timestamp_utc':row['timestamp_utc'],'filename':row['relative_path'],
                             'display_median_native':med,'display_robust_sigma_native':scale,'output':fn.name})
        finally:
            try:path.unlink()
            except OSError:pass
    return rendered


def render_full_sequence(report,rows):
    clean=np.asarray(report['ridge_clean_center_px'],float)
    flag=np.asarray(report['ridge_flag_mask'],bool)
    eligible=np.asarray(report['ridge_frame_eligible'],bool)
    width=report['per_frame_width_amplitude']
    t=np.arange(p.N)*p.DT_H

    fig,ax=plt.subplots(figsize=(12,5))
    im=ax.imshow(clean,origin='lower',aspect='auto',extent=[0,p.NX-1,t[0],t[-1]],
                 cmap='coolwarm',vmin=-15,vmax=15,interpolation='nearest')
    ax.set_xlabel('downstream pixel');ax.set_ylabel('hours from primary start')
    ax.set_title('Complete frozen 80x512 cleaned primary centerline')
    fig.colorbar(im,ax=ax,label='cross-tail ridge displacement [px]')
    fig.tight_layout();fig.savefig(OUT/'full_clean_centerline_time_distance.png',dpi=160);plt.close(fig)

    w=np.asarray([np.nan if x['median_sigma_width_px'] is None else x['median_sigma_width_px'] for x in width],float)
    a=np.asarray([np.nan if x['median_peak_amplitude_native_units'] is None else x['median_peak_amplitude_native_units'] for x in width],float)
    ff=np.mean(flag,axis=1)
    fig,axs=plt.subplots(4,1,figsize=(12,9),sharex=True)
    axs[0].plot(t,w);axs[0].set_ylabel('median sigma width [px]')
    axs[1].plot(t,a);axs[1].set_ylabel('median fitted amplitude [native]')
    axs[2].plot(t,ff);axs[2].axhline(.05,linestyle='--',linewidth=.8);axs[2].set_ylabel('flagged fraction')
    axs[3].step(t,eligible.astype(int),where='mid');axs[3].set_ylim(-.1,1.1);axs[3].set_ylabel('eligible');axs[3].set_xlabel('hours from primary start')
    fig.suptitle('Complete frozen primary width/amplitude/flag/eligibility series')
    fig.tight_layout();fig.savefig(OUT/'full_width_amplitude_flag_eligibility.png',dpi=160);plt.close(fig)

    mx=np.asarray([float(r['nucleus_x_0based']) for r in rows]);my=np.asarray([float(r['nucleus_y_0based']) for r in rows])
    fig,ax=plt.subplots(figsize=(7,6));ax.plot(mx,my,marker='.',markersize=3);ax.set_xlabel('mosaic x [px]');ax.set_ylabel('mosaic y [px]')
    ax.set_title('Frozen primary comet mosaic trajectory');fig.tight_layout();fig.savefig(OUT/'full_mosaic_position_series.png',dpi=160);plt.close(fig)

    return {
        'maximum_per_frame_flagged_fraction':float(np.max(ff)),
        'median_per_frame_flagged_fraction':float(np.median(ff)),
        'eligible_frame_fraction':float(np.mean(eligible)),
        'valid_centerline_fraction':float(np.isfinite(clean).mean()),
        'mosaic_x_range_px':[float(np.min(mx)),float(np.max(mx))],
        'mosaic_y_range_px':[float(np.min(my)),float(np.max(my))],
    }


def main():
    require_primary_authorization();OUT.mkdir(parents=True,exist_ok=True)
    result_path=p.OUT/'primary_result.json'
    if not result_path.exists():raise SystemExit('primary_result.json must exist from the exact locked analyzer in the same job')
    report=json.loads(result_path.read_text());rows=locked.load_local_manifest()
    prov=report.get('provenance',{})
    if prov.get('n_epochs')!=80 or prov.get('holdout_accessed') is not False:raise RuntimeError('primary provenance invariant failed')
    if [prov.get('first_timestamp'),prov.get('last_timestamp')]!=[rows[0]['timestamp_utc'],rows[-1]['timestamp_utc']]:raise RuntimeError('primary timestamp invariant failed')
    rendered=render_fixed_strips(report,rows)
    full=render_full_sequence(report,rows)
    summary={
        'status':'FROZEN_DIAGNOSTICS_GENERATED',
        'role':'artifact/alternative review only; cannot improve or alter primary classification',
        'fixed_indices':list(FIXED_INDICES),
        'n_fixed_frames':len(rendered),
        'fixed_frames':rendered,
        'full_sequence_quantitative_summary':full,
        'primary_classification_unchanged':report.get('primary_decision',{}).get('classification'),
        'primary_statistical_pass_pending_artifact_veto':report.get('primary_decision',{}).get('statistical_pass_pending_artifact_veto'),
        'display_normalization':'per fixed frame only: median subtraction / (1.4826*MAD), fixed display clip [-4,+8]; display-only, never science input',
        'holdout_accessed':False,
        'forbidden_actions':'no target-selected frame, subinterval, recentering, curvature correction, hand mask, or model/threshold change',
    }
    (OUT/'diagnostic_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,indent=2,sort_keys=True))


if __name__=='__main__':main()
