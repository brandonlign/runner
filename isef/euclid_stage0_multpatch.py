#!/usr/bin/env python3
"""Geometry-selected multi-patch replication of Euclid Q2 Stage-0 photometry.

Patches are selected solely from focal-plane geometry and spatial separation,
without examining their flux behavior. This tests whether the single-patch
precision result generalizes across Field 1.
"""
import json, math
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
from astropy.stats import sigma_clipped_stats
from photutils.detection import DAOStarFinder
import euclid_routed_feasibility as b

OUT=Path('results/euclid_stage0_multpatch.json'); NPATCH=4; MINSEP=550.0

def sep(a,bp):return b.dist_arcsec(a,bp,(a[1]+bp[1])/2)

def choose(qs,shifts):
    # Candidate locations are epoch-0 quadrant centers only; no image data enter selection.
    centers=[q.center for q in qs]; med=(float(np.median([x[0] for x in centers])),float(np.median([x[1] for x in centers])))
    order=sorted(range(len(qs)),key=lambda k:b.dist_arcsec(qs[k].center,med,med[1]))
    selected=[]
    # Spread sampling through deterministic rank stride rather than photometric quality.
    proposal=order[::3]+[k for k in order if k not in order[::3]]
    for k in proposal:
        target=qs[k].center
        if any(sep(target,x['target'])<MINSEP for x in selected):continue
        try:routes,diag=b.route_groups(qs,target,shifts)
        except:continue
        hs=b.epoch_headers(routes);inside=[];margins=[]
        for q in hs:
            x,y=b.pix(q,*target);inside.append(bool(b.contains(q,*target)));margins.append(float(min(x,y,b.NX-x,b.NY-y)))
        if not all(inside) or min(margins)<b.MARGIN+20:continue
        selected.append({'target':target,'epoch0_k':k,'routes':routes,'min_margin_pixels':min(margins)})
        if len(selected)>=NPATCH:break
    return selected

def aperture(im,x,y,r=1.8,ri=5,ro=8):
    x0=max(0,int(x)-9);x1=min(im.shape[1],int(x)+10);y0=max(0,int(y)-9);y1=min(im.shape[0],int(y)+10);s=im[y0:y1,x0:x1];yy,xx=np.indices(s.shape);rad=np.hypot(xx+x0-x,yy+y0-y);a=s[rad<=r];n=s[(rad>=ri)&(rad<=ro)]
    if len(a)<8 or len(n)<20:return np.nan
    return float(np.nansum(a-np.nanmedian(n)))
def rscatter(v):
    m=np.nanmedian(v);return float(1.4826*np.nanmedian(np.abs(v-m))/abs(m)) if np.isfinite(m) and m!=0 else np.nan

def run_patch(p):
    ra,de=p['target'];routes=p['routes'];hs=b.epoch_headers(routes);ims=[None]*16;meta=[None]*16
    with ThreadPoolExecutor(max_workers=8) as ex:
        fs=[ex.submit(b.stamp,i,hs[i],ra,de) for i in range(16)]
        for f in as_completed(fs):i,z,m=f.result();ims[i]=z;meta[i]=m
    cube=np.stack(ims);_,bg,std=sigma_clipped_stats(cube[0],sigma=3,maxiters=5);tab=DAOStarFinder(fwhm=1.8,threshold=max(6*std,1e-6),exclude_border=True)(cube[0]-bg)
    if tab is None:return {'ra':ra,'dec':de,'error':'no detections'}
    x=np.asarray(tab['xcentroid'],float);y=np.asarray(tab['ycentroid'],float);peak=np.asarray(tab['peak'],float);ids=[]
    for j in range(len(x)):
        if not(12<x[j]<b.STAMP-12 and 12<y[j]<b.STAMP-12):continue
        dd=np.hypot(x-x[j],y-y[j]);dd[j]=np.inf
        if np.min(dd)>=7:ids.append(j)
    ids=np.asarray(ids,int)
    if len(ids)==0:return {'ra':ra,'dec':de,'detected':int(len(tab)),'error':'no isolated sources'}
    ids=ids[np.argsort(peak[ids])[::-1][:80]];sx=x[ids]+meta[0]['x0'];sy=y[ids]+meta[0]['y0'];wr,wd=hs[0].w.pixel_to_world_values(sx,sy);fl=np.full((len(ids),16),np.nan)
    for e,q in enumerate(hs):
        px,py=q.w.world_to_pixel_values(wr,wd);px=np.asarray(px)-meta[e]['x0'];py=np.asarray(py)-meta[e]['y0']
        for j,(xx,yy) in enumerate(zip(px,py)):
            if 9<=xx<b.STAMP-9 and 9<=yy<b.STAMP-9:fl[j,e]=aperture(cube[e],xx,yy)
    ok=np.all(np.isfinite(fl)&(fl>0),axis=1);fl=fl[ok]
    if len(fl)==0:return {'ra':ra,'dec':de,'detected':int(len(tab)),'isolated':int(len(ids)),'error':'no all-epoch valid sources'}
    norm=fl/np.median(fl,axis=1)[:,None];common=np.median(norm,axis=0);corr=norm/common[None,:];sc=np.array([rscatter(v) for v in corr]);mx=np.max(np.abs(corr-1),axis=1)
    return {'ra':float(ra),'dec':float(de),'epoch0_k':int(p['epoch0_k']),'routes':{str(g):int(k) for g,k in routes.items()},'min_margin_pixels':float(p['min_margin_pixels']),'detected':int(len(tab)),'isolated':int(len(ids)),'valid_all_epochs':int(len(fl)),'median_fractional_scatter':float(np.median(sc)),'p25_scatter':float(np.percentile(sc,25)),'p75_scatter':float(np.percentile(sc,75)),'best10_median_scatter':float(np.median(np.sort(sc)[:min(10,len(sc))])),'gt10pct_excursions':int(np.sum(mx>0.10)),'gt20pct_excursions':int(np.sum(mx>0.20)),'max_excursion':float(np.max(mx))}

def main():
    qs=b.map_epoch0();shifts=b.pointing_shifts();sel=choose(qs,shifts);rows=[]
    for p in sel:rows.append(run_patch(p))
    good=[r for r in rows if 'median_fractional_scatter' in r]
    out={'success':len(good)==len(sel) and len(sel)==NPATCH,'note':'geometry-selected Field-1 replication; patch choice used no photometric outcomes','selection':{'requested_patches':NPATCH,'minimum_separation_arcsec':MINSEP,'selected':len(sel)},'patches':rows}
    if good:out['aggregate']={'patches_good':len(good),'median_of_patch_median_scatter':float(np.median([r['median_fractional_scatter'] for r in good])),'range_patch_median_scatter':[float(min(r['median_fractional_scatter'] for r in good)),float(max(r['median_fractional_scatter'] for r in good))],'total_valid_stars':int(sum(r['valid_all_epochs'] for r in good)),'total_gt20pct_excursions':int(sum(r['gt20pct_excursions'] for r in good))}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
