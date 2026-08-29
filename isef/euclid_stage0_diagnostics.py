#!/usr/bin/env python3
"""Diagnose the Stage-0 Euclid repeatability floor by dither group/aperture."""
import json, math
from pathlib import Path
import numpy as np
from astropy.stats import sigma_clipped_stats
from photutils.detection import DAOStarFinder
import euclid_routed_feasibility as b

RES=Path('results/euclid_routed_feasibility.json'); NPZ=Path('results/euclid_routed_stamps.npz'); OUT=Path('results/euclid_stage0_diagnostics.json')

def rscatter(v):
    v=np.asarray(v,float);m=np.nanmedian(v)
    return float(1.4826*np.nanmedian(np.abs(v-m))/abs(m)) if np.isfinite(m) and m!=0 else np.nan

def aperture(im,x,y,r,ri=None,ro=None):
    ri=ri or r+2.5;ro=ro or r+5.5
    x0=max(0,int(x)-11);x1=min(im.shape[1],int(x)+12);y0=max(0,int(y)-11);y1=min(im.shape[0],int(y)+12)
    s=im[y0:y1,x0:x1];yy,xx=np.indices(s.shape);rr=np.hypot(xx+x0-x,yy+y0-y)
    a=s[rr<=r];ann=s[(rr>=ri)&(rr<=ro)]
    return float(np.nansum(a-np.nanmedian(ann))) if len(a)>=8 and len(ann)>=20 else np.nan

def main():
    base=json.loads(RES.read_text());cube=np.load(NPZ)['stamps'];ra=float(base['target']['ra']);dec=float(base['target']['dec'])
    routes={int(g):int(v['k']) for g,v in base['routes'].items()};hs=b.epoch_headers(routes)
    # Reconstruct each stamp origin exactly as Stage-0 did.
    origins=[]
    for q in hs:
        x,y=b.pix(q,ra,dec);x=float(x);y=float(y);origins.append((int(round(x))-b.HALF,int(round(y))-b.HALF))
    _,bg,std=sigma_clipped_stats(cube[0],sigma=3,maxiters=5);tab=DAOStarFinder(fwhm=1.8,threshold=max(6*std,1e-6),exclude_border=True)(cube[0]-bg)
    x=np.asarray(tab['xcentroid'],float);y=np.asarray(tab['ycentroid'],float);peak=np.asarray(tab['peak'],float);ids=[]
    for j in range(len(x)):
        if not(12<x[j]<b.STAMP-12 and 12<y[j]<b.STAMP-12):continue
        d=np.hypot(x-x[j],y-y[j]);d[j]=np.inf
        if np.min(d)>=7:ids.append(j)
    ids=np.asarray(ids,int);ids=ids[np.argsort(peak[ids])[::-1][:80]]
    sx=x[ids]+origins[0][0];sy=y[ids]+origins[0][1];wr,wd=hs[0].w.pixel_to_world_values(sx,sy)
    positions=[]
    for e,q in enumerate(hs):
        px,py=q.w.world_to_pixel_values(wr,wd);positions.append((np.asarray(px)-origins[e][0],np.asarray(py)-origins[e][1]))
    out={'success':True,'target':{'ra':ra,'dec':dec},'detected':int(len(tab)),'isolated':int(len(ids)),'apertures':{}}
    for rad in (1.8,2.2,2.5,2.8,3.2,3.6,4.0):
        fl=np.full((len(ids),16),np.nan)
        for e in range(16):
            px,py=positions[e]
            for j,(xx,yy) in enumerate(zip(px,py)):
                if 11<=xx<b.STAMP-11 and 11<=yy<b.STAMP-11:fl[j,e]=aperture(cube[e],xx,yy,rad)
        ok=np.all(np.isfinite(fl)&(fl>0),axis=1);f=fl[ok]
        if len(f)<3:continue
        norm=f/np.median(f,axis=1)[:,None];common=np.median(norm,axis=0);corr=norm/common[None,:]
        total=np.array([rscatter(v) for v in corr])
        within=[];between=[]
        for v in corr:
            gs=[v[g::4] for g in range(4)];within.append(np.nanmedian([rscatter(z) for z in gs]));between.append(rscatter([np.nanmedian(z) for z in gs]))
        within=np.asarray(within);between=np.asarray(between)
        out['apertures'][str(rad)]={'valid':int(len(f)),'total_scatter_median':float(np.nanmedian(total)),'best10_total_median':float(np.nanmedian(np.sort(total)[:min(10,len(total))])),'within_same_dither_scatter_median':float(np.nanmedian(within)),'between_dither_group_scatter_median':float(np.nanmedian(between)),'between_to_within_ratio':float(np.nanmedian(between)/np.nanmedian(within)),'common_mode_range':float(np.max(common)-np.min(common))}
    best=min(out['apertures'],key=lambda k:out['apertures'][k]['total_scatter_median']);out['best_aperture_radius']=float(best);out['best']=out['apertures'][best]
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))

if __name__=='__main__':main()
