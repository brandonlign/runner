#!/usr/bin/env python3
"""Diagnose catastrophic Stage-0 photometry outliers using candidate-independent image-shape metrics.

The quality features intentionally do not use a source's astrophysical flux-excursion
score. They measure whether the pixel morphology is inconsistent with the same star's
normal PSF: small/large aperture ratio, centroid displacement, and local-background
roughness. This is a development kill test, not a frozen discovery cut.
"""
import json
from pathlib import Path
import numpy as np
from astropy.stats import sigma_clipped_stats
from photutils.detection import DAOStarFinder
import euclid_routed_feasibility as b
import euclid_stage0_diagnostics as d

RES=Path('results/euclid_routed_feasibility.json')
NPZ=Path('results/euclid_routed_stamps.npz')
OUT=Path('results/euclid_stage0_quality.json')


def mad_sigma(x, floor=1e-6):
    x=np.asarray(x,float);m=np.nanmedian(x);s=1.4826*np.nanmedian(np.abs(x-m))
    return float(max(s,floor)),float(m)


def aperture_and_shape(im,x,y,rsmall=1.8,rlarge=3.2):
    # Evaluate a compact 19x19 patch around the WCS-predicted position.
    x0=max(0,int(np.floor(x))-9);x1=min(im.shape[1],int(np.floor(x))+10)
    y0=max(0,int(np.floor(y))-9);y1=min(im.shape[0],int(np.floor(y))+10)
    s=np.asarray(im[y0:y1,x0:x1],float)
    yy,xx=np.indices(s.shape);xx=xx+x0;yy=yy+y0;rad=np.hypot(xx-x,yy-y)
    ann=(rad>=5)&(rad<=8);bg=float(np.nanmedian(s[ann]));noise=float(1.4826*np.nanmedian(np.abs(s[ann]-bg)))
    z=s-bg
    fs=float(np.nansum(z[rad<=rsmall]));fl=float(np.nansum(z[rad<=rlarge]))
    # Positive-weight centroid is a morphology diagnostic only, not photometry.
    core=rad<=3.2;w=np.clip(z[core],0,None);sw=float(np.nansum(w))
    if sw>0:
        cx=float(np.nansum(xx[core]*w)/sw);cy=float(np.nansum(yy[core]*w)/sw);co=float(np.hypot(cx-x,cy-y))
    else:co=float('nan')
    ratio=float(fs/fl) if np.isfinite(fl) and fl!=0 else float('nan')
    return fs,fl,ratio,co,noise


def main():
    base=json.loads(RES.read_text());cube=np.load(NPZ)['stamps'];ra=float(base['target']['ra']);dec=float(base['target']['dec'])
    routes={int(g):int(v['k']) for g,v in base['routes'].items()};hs=b.epoch_headers(routes)
    origins=[]
    for q in hs:
        x,y=b.pix(q,ra,dec);origins.append((int(round(float(x)))-b.HALF,int(round(float(y)))-b.HALF))
    _,bg,std=sigma_clipped_stats(cube[0],sigma=3,maxiters=5)
    tab=DAOStarFinder(fwhm=1.8,threshold=max(6*std,1e-6),exclude_border=True)(cube[0]-bg)
    x=np.asarray(tab['xcentroid'],float);y=np.asarray(tab['ycentroid'],float);peak=np.asarray(tab['peak'],float);ids=[]
    for j in range(len(x)):
        if not(12<x[j]<b.STAMP-12 and 12<y[j]<b.STAMP-12):continue
        dd=np.hypot(x-x[j],y-y[j]);dd[j]=np.inf
        if np.min(dd)>=7:ids.append(j)
    ids=np.asarray(ids,int);ids=ids[np.argsort(peak[ids])[::-1][:80]]
    sx=x[ids]+origins[0][0];sy=y[ids]+origins[0][1];wr,wd=hs[0].w.pixel_to_world_values(sx,sy)
    n=len(ids);fs=np.full((n,16),np.nan);fl=np.full((n,16),np.nan);ratio=np.full((n,16),np.nan);cent=np.full((n,16),np.nan);noise=np.full((n,16),np.nan)
    for e,q in enumerate(hs):
        px,py=q.w.world_to_pixel_values(wr,wd);px=np.asarray(px,float)-origins[e][0];py=np.asarray(py,float)-origins[e][1]
        for j,(xx,yy) in enumerate(zip(px,py)):
            if 11<=xx<b.STAMP-11 and 11<=yy<b.STAMP-11:
                fs[j,e],fl[j,e],ratio[j,e],cent[j,e],noise[j,e]=aperture_and_shape(cube[e],xx,yy)
    valid=np.all(np.isfinite(fs)&np.isfinite(fl)&np.isfinite(ratio)&np.isfinite(cent)&(fs>0)&(fl>0),axis=1)
    fs=fs[valid];fl=fl[valid];ratio=ratio[valid];cent=cent[valid];noise=noise[valid];p=peak[ids][valid]
    # Common-mode corrected small-aperture light curves are used only to evaluate whether the independent quality mask suppresses bad photometry.
    norm=fs/np.median(fs,axis=1)[:,None];common=np.median(norm,axis=0);corr=norm/common[None,:]
    excursion=np.max(np.abs(corr-1),axis=1)
    # Independent morphology scores: deviations are standardized per star across epochs.
    rz=np.zeros_like(ratio);cz=np.zeros_like(cent);nz=np.zeros_like(noise)
    for j in range(len(fs)):
        sr,mr=mad_sigma(ratio[j],0.002);sc,mc=mad_sigma(cent[j],0.03);sn,mn=mad_sigma(noise[j],1e-6)
        rz[j]=np.abs(ratio[j]-mr)/sr;cz[j]=np.abs(cent[j]-mc)/sc;nz[j]=np.abs(noise[j]-mn)/sn
    # Predeclared development rules based on morphology only. Evaluate a small grid rather than cherry-picking one cut.
    grids=[]
    pathological=excursion>0.20
    for zr in (4,6,8):
      for zc in (4,6,8):
        bad=(rz>zr)|(cz>zc)|(nz>8)
        star_bad=np.any(bad,axis=1)
        kept=~star_bad
        grids.append({'ratio_z':zr,'centroid_z':zc,'noise_z':8,
                      'stars':int(len(fs)),'stars_rejected':int(star_bad.sum()),
                      'pathological_gt20pct':int(pathological.sum()),
                      'pathological_rejected':int(np.sum(pathological&star_bad)),
                      'pathological_surviving':int(np.sum(pathological&kept)),
                      'clean_le20pct_rejected':int(np.sum((~pathological)&star_bad)),
                      'median_excursion_kept':float(np.median(excursion[kept])) if np.any(kept) else None,
                      'max_excursion_kept':float(np.max(excursion[kept])) if np.any(kept) else None})
    # Epoch-level association: does the largest photometric excursion coincide with an independently bad morphology epoch?
    assoc=[]
    for j in range(len(fs)):
        e=int(np.argmax(np.abs(corr[j]-1)));assoc.append({'rank_peak':float(p[j]),'max_excursion':float(excursion[j]),'epoch':e,
          'ratio_z_at_event':float(rz[j,e]),'centroid_z_at_event':float(cz[j,e]),'noise_z_at_event':float(nz[j,e]),
          'max_shape_z_at_event':float(max(rz[j,e],cz[j,e],nz[j,e]))})
    assoc.sort(key=lambda q:q['max_excursion'],reverse=True)
    out={'success':True,'note':'development candidate-independent morphology quality gate; no final discovery cuts frozen',
         'stars_valid':int(len(fs)),'pathological_gt20pct':int(pathological.sum()),
         'excursion_quantiles':{str(q):float(np.quantile(excursion,q)) for q in (0.5,0.75,0.9,0.95,1.0)},
         'grid':grids,'worst_events':assoc[:15]}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))

if __name__=='__main__':main()
