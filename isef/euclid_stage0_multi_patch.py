#!/usr/bin/env python3
"""Full-gate generalization across widely separated safe Q2 development patches.

Candidate patch centers are proposed on a coarse grid around the Stage-0 region,
but a patch is used only after exact all-quadrant WCS routing proves that the same
sky position has a safe 128-pixel stamp in all four dither groups. Selected patch
centers must be >=120 arcsec apart. Within every selected patch we apply the same
candidate-independent morphology gate, released Euclid FLG screen, and per-epoch
ensemble PSF common-mode correction as the single-patch joint null. No blind field
is opened here.
"""
import json, math
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import numpy as np
import euclid_routed_feasibility as b
import euclid_exact_routing as er
import euclid_stage0_psf_detector as pd
import euclid_stage0_psf_flag_gate as fg

OUT=Path('results/euclid_stage0_multi_patch.json')
CENTER=(267.5945,-30.0074); MIN_SEP_AS=120.0; TARGET_PATCHES=5
# Search widely before giving up; routing is WCS-only and cheap compared with image I/O.
CANDIDATE_OFFSETS=[
 (0,0),(180,0),(-180,0),(0,180),(0,-180),(360,0),(-360,0),(0,360),(0,-360),
 (180,180),(180,-180),(-180,180),(-180,-180),(360,180),(360,-180),(-360,180),(-360,-180),
 (540,0),(-540,0),(0,540),(0,-540),(540,180),(540,-180),(-540,180),(-540,-180),
 (360,360),(360,-360),(-360,360),(-360,-360),(720,0),(-720,0),(0,720),(0,-720)
]

def target_from_offset(dra_as,ddec_as):
    ra,de=CENTER;return ra+dra_as/(3600*math.cos(math.radians(de))),de+ddec_as/3600

def sep_as(a,b):
    return math.hypot((a[0]-b[0])*math.cos(math.radians((a[1]+b[1])/2))*3600,(a[1]-b[1])*3600)

def select_safe(groupmaps):
    chosen=[];rejected=[]
    for off in CANDIDATE_OFFSETS:
        target=target_from_offset(*off)
        if any(sep_as(target,c['target'])<MIN_SEP_AS for c in chosen):continue
        try:
            routes,diag=er.route_target(groupmaps,target)
            chosen.append({'offset_arcsec':off,'target':target,'routes':routes,'route_diagnostics':diag})
            if len(chosen)>=TARGET_PATCHES:break
        except Exception as e:rejected.append({'offset_arcsec':off,'error':f'{type(e).__name__}: {e}'})
    return chosen,rejected

def fetch_cube(spec):
    target=spec['target'];routes=spec['routes'];hs=b.epoch_headers(routes);ims=[None]*16;meta=[None]*16
    with ThreadPoolExecutor(max_workers=8) as ex:
        fs=[ex.submit(er.stamp,e,hs[e],target[0],target[1]) for e in range(16)]
        for fut in as_completed(fs):e,z,m=fut.result();ims[e]=z;meta[e]=m
    return np.stack(ims),hs,meta

def analyze_patch(idx,spec,lim):
    cube,hs,meta=fetch_cube(spec);orig=[(int(m['x0']),int(m['y0'])) for m in meta];ra,de,peak=pd.sources(cube,hs,orig)
    src=[];checks=[]
    for j,(r,d) in enumerate(zip(ra,de)):
        cuts={e:pd.cut(cube,hs,orig,r,d,e) for e in range(16)}
        if any(v is None for v in cuts.values()):continue
        mm=[]
        for e in range(16):
            peers=[p for p in range(e%4,16,4) if p!=e];ref=np.nanmedian(np.stack([cuts[p] for p in peers]),axis=0);f,s,c=pd.scale_metric(cuts[e],ref);morph=pd.morph_ok(s,c,lim)
            row={'star':j,'ra':float(r),'dec':float(d),'epoch':e,'fraction':float(f),'morphology_ok':morph,'artifact_flag':False,'flag_checked':False,'shape_residual':float(s),'shape_correlation':float(c)};mm.append(row)
            if morph and abs(f)>fg.CHECK_FLOOR:checks.append(row)
        src.append({'star':j,'ra':float(r),'dec':float(d),'peak':float(peak[j]),'measurements':mm})
    with ThreadPoolExecutor(max_workers=32) as ex:
        fs={ex.submit(fg.flag_artifact,hs[r['epoch']],r['epoch'],r['ra'],r['dec']):r for r in checks}
        for fut in as_completed(fs):
            r=fs[fut];r['flag_checked']=True
            try:r['artifact_flag']=bool(fut.result()[0])
            except Exception as e:r['artifact_flag']=True;r['flag_error']=f'{type(e).__name__}: {e}'
    for s in src:
        for r in s['measurements']:r['accepted_precommon']=bool(r['morphology_ok'] and not r['artifact_flag'])
    common=[];common_n=[]
    for e in range(16):
        vals=[r['fraction'] for s in src for r in s['measurements'] if r['epoch']==e and r['accepted_precommon']]
        common.append(float(np.median(vals)) if vals else 0.0);common_n.append(len(vals))
    stars=[]
    for s in src:
        good=[]
        for r in s['measurements']:
            r['corrected_fraction']=fg.common_correct(r['fraction'],common[r['epoch']]);r['accepted']=r['accepted_precommon']
            if r['accepted']:good.append(r)
        if len(good)<pd.MIN_ACCEPTED:continue
        vals=np.asarray([r['corrected_fraction'] for r in good]);imax=int(np.argmax(np.abs(vals)));sig,med=pd.mad_sigma(vals)
        stars.append({'star':s['star'],'ra':s['ra'],'dec':s['dec'],'peak':s['peak'],'accepted_epochs':len(good),'max_abs_fraction':float(np.max(np.abs(vals))),'max_epoch':int(good[imax]['epoch']),'signed_max_fraction':float(vals[imax]),'robust_sigma':sig,'median_fraction':med})
    maxima=np.asarray([s['max_abs_fraction'] for s in stars],float)
    return {'patch':idx,'offset_arcsec':list(spec['offset_arcsec']),'target':{'ra':spec['target'][0],'dec':spec['target'][1]},'routes':{str(k):int(v) for k,v in spec['routes'].items()},'route_diagnostics':spec['route_diagnostics'],'candidate_stars':len(ra),'valid_stars':len(stars),'flag_reads':len(checks),'flagged_high_measurements':sum(bool(r['artifact_flag']) for r in checks),'epoch_common_mode_fraction':common,'epoch_common_mode_n':common_n,'max_abs_fraction':pd.summary(maxima),'maxima':maxima.tolist(),'top_sources':sorted(stars,key=lambda x:x['max_abs_fraction'],reverse=True)[:10]}

def main():
    lim=pd.morphology_limits();groupmaps=er.map_groups();selected,rejected=select_safe(groupmaps);patches=[];fail=[]
    for i,spec in enumerate(selected):
        try:patches.append(analyze_patch(i,spec,lim))
        except Exception as e:fail.append({'patch':i,'offset_arcsec':list(spec['offset_arcsec']),'error':f'{type(e).__name__}: {e}'})
    allmax=np.asarray([v for p in patches for v in p['maxima']],float);pooled={'stars':int(len(allmax))}
    if len(allmax):pooled.update({'max_abs_fraction':pd.summary(allmax),'q90':float(np.quantile(allmax,.90)),'q95':float(np.quantile(allmax,.95)),'q99':float(np.quantile(allmax,.99)),'zero_observed_fp':float(np.max(allmax))})
    out={'success':len(patches)>=4 and len(allmax)>=100,'note':'safe-center exact-WCS multi-patch full morphology+FLAG+common-mode development generalization; no blind field opened','morphology_limits':lim,'min_patch_separation_arcsec':MIN_SEP_AS,'selected_centers':[{'offset_arcsec':list(x['offset_arcsec']),'target':{'ra':x['target'][0],'dec':x['target'][1]}} for x in selected],'routing_rejections':rejected,'requested_patches':TARGET_PATCHES,'successful_patches':len(patches),'analysis_failures':fail,'pooled':pooled,'patches':patches}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
