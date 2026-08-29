#!/usr/bin/env python3
"""Force the strongest measured Gaia DR3 rapid-variable control through the Euclid Stage-0B photometric gate.

The external catalogue coordinate is intentionally used as a forced-photometry
positive control; it is not used to tune morphology or variability thresholds.
"""
import json
from pathlib import Path
import numpy as np
import euclid_exact_routing as er
import euclid_stage0_multi_patch as mp
import euclid_stage0_psf_detector as pd
import euclid_stage0_psf_flag_gate as fg
OUT=Path('results/euclid_gaia_control_fullgate.json');OUT.parent.mkdir(parents=True,exist_ok=True)
TARGET={'source_id':'4056413404956022528','ra':267.5813953658793,'dec':-30.11408905040285,'gaia_amplitude_mag':0.609702,'gaia_frequency_per_day':5.353459999063657}
DEV_Q95=0.10999505618160727;MULTIPATCH_Q95=0.14011415120359302
MORPH={'control_quantile':0.95,'shape_residual_max':0.7433354680523049,'shape_correlation_min':0.6246851398220109}

def save(x):OUT.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n');print(json.dumps(x,indent=2,sort_keys=True))
def main():
    gm=er.map_groups();target=(TARGET['ra'],TARGET['dec'])
    try:routes,diag=er.route_target(gm,target)
    except Exception as e:return save({'success':False,'target':TARGET,'error':f'route: {type(e).__name__}: {e}'})
    spec={'offset_arcsec':(0,0),'target':target,'routes':routes,'route_diagnostics':diag}
    try:
        # Local ensemble supplies the same candidate-independent epoch common mode.
        res=mp.analyze_patch(0,spec,MORPH);cube,hs,meta=mp.fetch_cube(spec);orig=[(int(m['x0']),int(m['y0'])) for m in meta]
    except Exception as e:return save({'success':False,'target':TARGET,'error':f'analyze: {type(e).__name__}: {e}'})
    cuts={e:pd.cut(cube,hs,orig,TARGET['ra'],TARGET['dec'],e) for e in range(16)}
    if any(v is None for v in cuts.values()):return save({'success':False,'target':TARGET,'error':'forced target cutout missing in one or more epochs'})
    rows=[]
    for e in range(16):
        peers=[p for p in range(e%4,16,4) if p!=e];ref=np.nanmedian(np.stack([cuts[p] for p in peers]),axis=0);f,s,c=pd.scale_metric(cuts[e],ref);morph=pd.morph_ok(s,c,MORPH);artifact=False;flag_checked=False;flag_error=None
        if morph and abs(f)>fg.CHECK_FLOOR:
            flag_checked=True
            try:artifact=bool(fg.flag_artifact(hs[e],e,TARGET['ra'],TARGET['dec'])[0])
            except Exception as ex:artifact=True;flag_error=f'{type(ex).__name__}: {ex}'
        accepted=bool(morph and not artifact);corrected=fg.common_correct(f,res['epoch_common_mode_fraction'][e]);rows.append({'epoch':e,'fraction':float(f),'corrected_fraction':float(corrected),'shape_residual':float(s),'shape_correlation':float(c),'morphology_ok':bool(morph),'flag_checked':flag_checked,'artifact_flag':artifact,'flag_error':flag_error,'accepted':accepted})
    good=[r for r in rows if r['accepted']];vals=np.asarray([r['corrected_fraction'] for r in good],float);imax=int(np.argmax(np.abs(vals))) if len(vals) else None;mx=float(np.max(np.abs(vals))) if len(vals) else None;me=int(good[imax]['epoch']) if len(vals) else None
    recovered=bool(len(good)>=pd.MIN_ACCEPTED and mx is not None and mx>=MULTIPATCH_Q95)
    save({'success':True,'target':TARGET,'control_mode':'external-coordinate forced photometry; coordinate selected from Gaia before Euclid full-gate measurement','frozen_morphology_limits':MORPH,'accepted_epochs':len(good),'max_abs_corrected_fraction':mx,'max_epoch':me,'passes_original_dev_q95':bool(mx is not None and mx>=DEV_Q95),'passes_broad_multipatch_q95':bool(mx is not None and mx>=MULTIPATCH_Q95),'positive_control_recovered':recovered,'measurements':rows,'local_patch_summary':{'valid_stars':res['valid_stars'],'flag_reads':res['flag_reads'],'flagged_high_measurements':res['flagged_high_measurements'],'max_abs_fraction':res['max_abs_fraction']},'interpretation':'Recovery requires >=12 accepted epochs and an absolute common-mode-corrected same-dither PSF excursion above the pre-existing five-patch q95 threshold. The Gaia coordinate is a positive-control seed only; thresholds and morphology limits are unchanged.'})
if __name__=='__main__':main()
