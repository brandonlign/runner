#!/usr/bin/env python3
"""Generalization test of morphology-gated same-dither PSF variability.

Five development patches separated by 3 arcmin are routed with exact per-group
all-quadrant WCS containment and range-read across all 16 Q2 exposures. No blind
field is opened here.
"""
import json, math
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import euclid_routed_feasibility as b
import euclid_exact_routing as er
import euclid_stage0_psf_detector as pd

OUT=Path('results/euclid_stage0_multi_patch.json');RNG=np.random.default_rng(20260829)
CENTER=(267.5945,-30.0074);OFFSETS_ARCSEC=[(0,0),(180,0),(-180,0),(0,180),(0,-180)];AMPS=(0.10,0.20,0.50)

def target_from_offset(dra_as,ddec_as):
    ra,de=CENTER;return ra+dra_as/(3600*math.cos(math.radians(de))),de+ddec_as/3600

def fetch_cube(target,groupmaps):
    routes,route_diag=er.route_target(groupmaps,target);hs=b.epoch_headers(routes);ims=[None]*16;meta=[None]*16
    with ThreadPoolExecutor(max_workers=8) as ex:
        fs=[ex.submit(er.stamp,e,hs[e],target[0],target[1]) for e in range(16)]
        for f in as_completed(fs):e,z,m=f.result();ims[e]=z;meta[e]=m
    return np.stack(ims),hs,meta,routes,route_diag

def analyze_patch(idx,target,groupmaps,lim):
    cube,hs,meta,routes,route_diag=fetch_cube(target,groupmaps);orig=[(int(m['x0']),int(m['y0'])) for m in meta];ra,de,peak=pd.sources(cube,hs,orig);stars=[];inj={a:[] for a in AMPS};meas=acc=0
    for j,(r,d) in enumerate(zip(ra,de)):
        cuts={e:pd.cut(cube,hs,orig,r,d,e) for e in range(16)}
        if any(v is None for v in cuts.values()):continue
        frac=[];ok=[]
        for e in range(16):
            peers=[p for p in range(e%4,16,4) if p!=e];ref=np.nanmedian(np.stack([cuts[p] for p in peers]),axis=0);f,s,c=pd.scale_metric(cuts[e],ref);good=pd.morph_ok(s,c,lim);frac.append(f);ok.append(good);meas+=1;acc+=int(good)
        frac=np.asarray(frac);ok=np.asarray(ok,bool)
        if np.sum(ok)<pd.MIN_ACCEPTED:continue
        clean=frac[ok];sig,med=pd.mad_sigma(clean);z=np.abs(clean-med)/sig
        stars.append({'star':j,'ra':float(r),'dec':float(d),'peak':float(peak[j]),'accepted_epochs':int(np.sum(ok)),'max_abs_fraction':float(np.max(np.abs(clean))),'robust_sigma':float(sig),'max_robust_z':float(np.max(z))})
        for amp in AMPS:
            for _ in range(6):
                e=int(RNG.integers(0,16));peers=[p for p in range(e%4,16,4) if p!=e];ref=np.nanmedian(np.stack([cuts[p] for p in peers]),axis=0);yy,xx=np.indices(ref.shape);cc=(np.array(ref.shape)-1)/2;rr=np.hypot(xx-cc[1],yy-cc[0]);floor=float(np.nanmedian(ref[(rr>=5.5)&(rr<=7.5)]));tmpl=ref-floor;f,s,c=pd.scale_metric(cuts[e]+amp*tmpl,ref)
                if pd.morph_ok(s,c,lim):inj[amp].append(float(f))
    maxima=np.asarray([s['max_abs_fraction'] for s in stars],float)
    return {'patch':idx,'target':{'ra':target[0],'dec':target[1]},'routes':{str(k):int(v) for k,v in routes.items()},'route_diagnostics':route_diag,'candidate_stars':len(ra),'valid_stars':len(stars),'measurement_morphology_acceptance':float(acc/meas) if meas else 0,'max_abs_fraction':pd.summary(maxima),'maxima':maxima.tolist(),'stars':sorted(stars,key=lambda x:x['max_abs_fraction'],reverse=True)[:8],'injected_recovered':{str(a):inj[a] for a in AMPS}}

def main():
    lim=pd.morphology_limits();groupmaps=er.map_groups();patches=[];fail=[]
    for i,off in enumerate(OFFSETS_ARCSEC):
        try:patches.append(analyze_patch(i,target_from_offset(*off),groupmaps,lim))
        except Exception as e:fail.append({'patch':i,'offset_arcsec':off,'error':f'{type(e).__name__}: {e}'})
    allmax=np.asarray([v for p in patches for v in p['maxima']],float);pooled={'stars':int(len(allmax))}
    if len(allmax):pooled.update({'max_abs_fraction':pd.summary(allmax),'q95':float(np.quantile(allmax,.95)),'q99':float(np.quantile(allmax,.99)),'zero_observed_fp':float(np.max(allmax))})
    injection={}
    for a in AMPS:
        vals=np.asarray([v for p in patches for v in p['injected_recovered'][str(a)]],float);injection[str(a)]={'morphology_accepted_trials':int(len(vals)),'recovered':pd.summary(vals)}
        if len(allmax) and len(vals):injection[str(a)].update({'recovery_gt_pooled_q95':float(np.mean(np.abs(vals)>pooled['q95'])),'recovery_gt_pooled_q99':float(np.mean(np.abs(vals)>pooled['q99'])),'recovery_gt_pooled_zero_fp':float(np.mean(np.abs(vals)>pooled['zero_observed_fp']))})
    out={'success':len(patches)>=4 and len(allmax)>=50,'note':'3-arcmin exact-WCS multi-patch morphology-gated development generalization; no blind field opened','morphology_limits':lim,'offsets_arcsec':OFFSETS_ARCSEC,'requested_patches':5,'successful_patches':len(patches),'failures':fail,'pooled':pooled,'injections':injection,'patches':patches}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
