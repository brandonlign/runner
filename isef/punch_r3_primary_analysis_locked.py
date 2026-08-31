#!/usr/bin/env python3
"""Authoritative lock wrapper for the frozen PUNCH R3 primary analyzer.

This wrapper fixes only pre-target provenance/decision semantics discovered by
no-pixel preflight. It does not change extraction, Gaussian fitting, masking,
mode inference, growth models, thresholds, or any target measurement.

It remains protected by the underlying explicit target-open authorization
interlock. No workflow authorizing target access exists unless/ until the two
final real-background gates pass scientifically.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import numpy as np

import punch_r3_primary_analysis_frozen as p

LOCAL_MANIFEST = Path(__file__).with_name('punch_r3_primary_roi_manifest.csv')
MANIFEST_SHA256 = '0a9ad1e8e47ce8c1cbb2e1d578ed1ab318dc6f90e07b972697e92761b309541b'


def load_local_manifest():
    raw=LOCAL_MANIFEST.read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=MANIFEST_SHA256:
        raise RuntimeError(f'frozen local manifest hash mismatch: {digest}')
    rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
    if len(rows)!=p.N:raise RuntimeError(f'frozen manifest expected {p.N} rows, got {len(rows)}')
    if rows[0]['timestamp_utc']!='2026-04-21T18:00:29Z' or rows[-1]['timestamp_utc']!='2026-04-22T04:32:29Z':
        raise RuntimeError('frozen primary partition timestamps changed')
    for i,row in enumerate(rows):
        if int(row['index'])!=i or not row['relative_path'].endswith('_v0l.fits'):
            raise RuntimeError('manifest index/version invariant failed')
        for k in ('nucleus_x_0based','nucleus_y_0based','downstream_ux','downstream_uy','elongation_deg','antisolar_pa_deg'):
            row[k]=float(row[k])
    return rows


def corrected_target_decision(fit,clean,eligible):
    valid=float(np.isfinite(clean).mean())
    eligible_fraction=float(np.mean(eligible))
    status=fit.get('status')
    wave=float(fit.get('wavelength',np.nan)) if status=='OK' else float('nan')
    in_confirmatory=bool(np.isfinite(wave) and p.CONFIRM_MIN_WAVE<=wave<=p.CONFIRM_MAX_WAVE)
    four_periods=bool(np.isfinite(wave) and p.NX/wave>=4.0)
    statistical_pass=bool(
        status=='OK' and in_confirmatory and four_periods and
        fit.get('phase_r2',-np.inf)>=p.PHASE_R2_MIN and
        fit.get('spectral_concentration',-np.inf)>=p.SPECTRAL_CONCENTRATION_MIN and
        fit.get('growth_rate',0)>0 and
        fit.get('delta_bic_growth_over_step',-np.inf)>=p.DBIC_MIN and
        fit.get('delta_bic_growth_over_constant',-np.inf)>=p.DBIC_MIN and
        fit.get('delta_bic_growth_over_linear',-np.inf)>=p.DBIC_MIN and
        valid>=p.MIN_VALID and eligible_fraction>=p.MIN_ELIGIBLE
    )
    # Out-of-band is always exploratory, regardless of amplitude behavior.
    if status=='OK' and not in_confirmatory:
        classification='SELECTED_MODE_OUTSIDE_CONFIRMATORY_24_80_PX_BAND'
    elif statistical_pass:
        classification='STATISTICAL_KH_LIKE_COHERENT_GROWTH_PASS_PENDING_ARTIFACT_VETO'
    elif status=='OK' and fit.get('phase_r2',-np.inf)>=p.PHASE_R2_MIN and fit.get('spectral_concentration',-np.inf)>=p.SPECTRAL_CONCENTRATION_MIN:
        classification='COHERENT_MODE_WITHOUT_PREREGISTERED_FINITE_GROWTH_SUPPORT'
    elif status=='OK' and fit.get('growth_preferred',False):
        classification='AMPLITUDE_EVOLUTION_WITHOUT_CONFIRMATORY_COHERENT_MODE_SUPPORT'
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


def postprocess_secondary():
    path=p.OUT/'primary_result.json'
    if not path.exists():return
    d=json.loads(path.read_text())
    sec=d.get('secondary_centroid',{})
    decision=d.get('primary_decision',{})
    if 'strengthened_phase_speed_consistency' in sec:
        sec['strengthened_phase_speed_consistency']=bool(
            sec['strengthened_phase_speed_consistency'] and
            decision.get('selected_mode_in_confirmatory_band',False)
        )
        sec['strengthening_requires_primary_confirmatory_band']=True
    d['provenance']['authoritative_entrypoint']='isef/punch_r3_primary_analysis_locked.py'
    d['provenance']['manifest_source']='local hash-locked runner copy; identical science-repo provenance copy'
    path.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')


def main():
    p.load_manifest=load_local_manifest
    p.target_decision=corrected_target_decision
    p.MANIFEST_URL='local:isef/punch_r3_primary_roi_manifest.csv'
    p.MANIFEST_SHA256=MANIFEST_SHA256
    rc=p.main()
    if rc==0:postprocess_secondary()
    return rc


if __name__=='__main__':raise SystemExit(main())
