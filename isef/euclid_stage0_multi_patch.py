#!/usr/bin/env python3
"""Generalization test of the same-dither PSF detector on independent Q2 patches.

Uses five non-overlapping 128x128 sky patches around the development location.
For every patch it dynamically routes the four dither groups, range-reads all 16
Euclid VIS stamps, detects isolated stars, measures same-dither PSF-scale changes,
and performs point-source injections. This is still development-field work; it
exists to test whether the single-patch noise floor generalizes before any blind
field is opened.
"""
import json, math
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import euclid_routed_feasibility as b
import euclid_stage0_psf_detector as pd

OUT=Path('results/euclid_stage0_multi_patch.json')
RNG=np.random.default_rng(20260829)
CENTER=(267.5945,-30.0074)
# ~30-45 arcsec offsets, comfortably beyond a 128 px VIS stamp (~13 arcsec).
OFFSETS_ARCSEC=[(0,0),(36,0),(-36,0),(0,36),(0,-36)]
AMPS=(0.10,0.20,0.50)

def target_from_offset(dra_as,ddec_as):
    ra,de=CENTER
    return ra + dra_as/(3600*math.cos(math.radians(de))), de+ddec_as/3600

def fetch_cube(target,qs,shifts):
    routes,_=b.route_groups(qs,target,shifts)
    hs=b.epoch_headers(routes); ims=[None]*16; meta=[None]*16
    with ThreadPoolExecutor(max_workers=8) as ex:
        fs=[ex.submit(b.stamp,e,hs[e],target[0],target[1]) for e in range(16)]
        for f in as_completed(fs):
            e,z,m=f.result();ims[e]=z;meta[e]=m
    return np.stack(ims),hs,meta,routes

def origins(meta): return [(int(m['x0']),int(m['y0'])) for m in meta]

def analyze_patch(idx,target,qs,shifts):
    cube,hs,meta,routes=fetch_cube(target,qs,shifts);orig=origins(meta)
    ra,de,peak=pd.sources(cube,hs,orig); stars=[]; inj={a:[] for a in AMPS}
    for j,(r,d) in enumerate(zip(ra,de)):
        cuts={e:pd.cut(cube,hs,orig,r,d,e) for e in range(16)}
        if any(v is None for v in cuts.values()): continue
        frac=[]
        for e in range(16):
            peers=[p for p in range(e%4,16,4) if p!=e]; ref=np.nanmedian(np.stack([cuts[p] for p in peers]),axis=0)
            f,shape,corr=pd.scale_metric(cuts[e],ref); frac.append(f)
        frac=np.asarray(frac);sig,med=pd.mad_sigma(frac);z=np.abs(frac-med)/sig
        stars.append({'star':j,'ra':float(r),'dec':float(d),'peak':float(peak[j]),'max_abs_fraction':float(np.max(np.abs(frac))),'robust_sigma':float(sig),'max_robust_z':float(np.max(z))})
        for amp in AMPS:
            for _ in range(6):
                e=int(RNG.integers(0,16));peers=[p for p in range(e%4,16,4) if p!=e];ref=np.nanmedian(np.stack([cuts[p] for p in peers]),axis=0)
                yy,xx=np.indices(ref.shape);cc=(np.array(ref.shape)-1)/2;rr=np.hypot(xx-cc[1],yy-cc[0]);floor=float(np.nanmedian(ref[(rr>=5.5)&(rr<=7.5)]));tmpl=ref-floor
                f,shape,corr=pd.scale_metric(cuts[e]+amp*tmpl,ref);inj[amp].append(float(f))
    maxima=np.asarray([s['max_abs_fraction'] for s in stars],float)
    return {'patch':idx,'target':{'ra':target[0],'dec':target[1]},'routes':{str(k):int(v['k']) if isinstance(v,dict) else int(v) for k,v in routes.items()},'valid_stars':len(stars),'max_abs_fraction':pd.summary(maxima),'maxima':maxima.tolist(),'stars':sorted(stars,key=lambda x:x['max_abs_fraction'],reverse=True)[:8],'injected_recovered':{str(a):inj[a] for a in AMPS}}

def main():
    qs=b.map_epoch0();shifts=b.pointing_shifts();patches=[];fail=[]
    for i,off in enumerate(OFFSETS_ARCSEC):
        target=target_from_offset(*off)
        try: patches.append(analyze_patch(i,target,qs,shifts))
        except Exception as e: fail.append({'patch':i,'offset_arcsec':off,'error':f'{type(e).__name__}: {e}'})
    allmax=np.asarray([v for p in patches for v in p['maxima']],float)
    pooled={'stars':int(len(allmax))}
    if len(allmax):
        pooled.update({'max_abs_fraction':pd.summary(allmax),'q95':float(np.quantile(allmax,.95)),'q99':float(np.quantile(allmax,.99)),'zero_observed_fp':float(np.max(allmax))})
    injection={}
    for a in AMPS:
        vals=np.asarray([v for p in patches for v in p['injected_recovered'][str(a)]],float)
        injection[str(a)]={'trials':int(len(vals)),'recovered':pd.summary(vals)}
        if len(allmax) and len(vals):
            injection[str(a)]['recovery_gt_pooled_q99']=float(np.mean(np.abs(vals)>pooled['q99']))
            injection[str(a)]['recovery_gt_pooled_zero_fp']=float(np.mean(np.abs(vals)>pooled['zero_observed_fp']))
    out={'success':len(patches)>=4,'note':'multi-patch development-field generalization; no blind field opened','requested_patches':len(OFFSETS_ARCSEC),'successful_patches':len(patches),'failures':fail,'pooled':pooled,'injections':injection,'patches':patches}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
