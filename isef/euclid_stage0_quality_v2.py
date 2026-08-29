#!/usr/bin/env python3
"""Second Euclid Stage-0 quality gate: cross-aperture and temporal/dither coherence.

This is a development diagnostic. It does not freeze a discovery threshold.
It tests whether large candidate-like excursions preserve point-source flux scaling
across apertures and whether they correlate with dither position or neighboring stars.
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
OUT=Path('results/euclid_stage0_quality_v2.json')
RADII=(1.8,2.2,2.8,3.2)


def main():
    base=json.loads(RES.read_text()); cube=np.load(NPZ)['stamps']
    ra=float(base['target']['ra']); dec=float(base['target']['dec'])
    routes={int(g):int(v['k']) for g,v in base['routes'].items()}; hs=b.epoch_headers(routes)
    origins=[]
    for q in hs:
        x,y=b.pix(q,ra,dec); origins.append((int(round(float(x)))-b.HALF,int(round(float(y)))-b.HALF))

    _,bg,std=sigma_clipped_stats(cube[0],sigma=3,maxiters=5)
    tab=DAOStarFinder(fwhm=1.8,threshold=max(6*std,1e-6),exclude_border=True)(cube[0]-bg)
    x=np.asarray(tab['xcentroid'],float); y=np.asarray(tab['ycentroid'],float); peak=np.asarray(tab['peak'],float)
    ids=[]
    for j in range(len(x)):
        if not(12<x[j]<b.STAMP-12 and 12<y[j]<b.STAMP-12): continue
        dd=np.hypot(x-x[j],y-y[j]); dd[j]=np.inf
        if np.min(dd)>=7: ids.append(j)
    ids=np.asarray(ids,int); ids=ids[np.argsort(peak[ids])[::-1][:80]]
    sx=x[ids]+origins[0][0]; sy=y[ids]+origins[0][1]; wr,wd=hs[0].w.pixel_to_world_values(sx,sy)

    nr=len(RADII); n=len(ids); fl=np.full((nr,n,16),np.nan); cent=np.full((n,16),np.nan)
    positions=[]
    for e,q in enumerate(hs):
        px,py=q.w.world_to_pixel_values(wr,wd); px=np.asarray(px,float)-origins[e][0]; py=np.asarray(py,float)-origins[e][1]
        if e==0: positions=np.column_stack([px,py])
        for j,(xx,yy) in enumerate(zip(px,py)):
            if 11<=xx<b.STAMP-11 and 11<=yy<b.STAMP-11:
                for ir,r in enumerate(RADII): fl[ir,j,e]=d.aperture(cube[e],xx,yy,r)
                # simple positive-weight centroid around predicted location
                yy0,xx0=np.indices(cube[e].shape); rad=np.hypot(xx0-xx,yy0-yy); ann=(rad>=5)&(rad<=8)
                bkg=float(np.nanmedian(cube[e][ann])); z=np.clip(cube[e]-bkg,0,None); core=rad<=3.2; sw=float(np.nansum(z[core]))
                if sw>0:
                    cx=float(np.nansum(xx0[core]*z[core])/sw); cy=float(np.nansum(yy0[core]*z[core])/sw); cent[j,e]=float(np.hypot(cx-xx,cy-yy))

    valid=np.all(np.isfinite(fl)&(fl>0),axis=(0,2)) & np.all(np.isfinite(cent),axis=1)
    fl=fl[:,valid,:]; cent=cent[valid]; p=peak[ids][valid]; positions=np.asarray(positions)[valid]
    n=fl.shape[1]

    corr=np.empty_like(fl)
    for ir in range(nr):
        z=fl[ir]/np.median(fl[ir],axis=1)[:,None]
        common=np.median(z,axis=0)
        corr[ir]=z/common[None,:]
    residual=corr-1.0
    ref=residual[0]
    maxepoch=np.argmax(np.abs(ref),axis=1)
    maxamp=np.max(np.abs(ref),axis=1)

    # generic per-epoch cross-aperture disagreement. True point-source scaling should
    # produce similar fractional residuals in all four apertures.
    amp_med=np.median(residual,axis=0)
    ap_mad=np.median(np.abs(residual-amp_med[None,:,:]),axis=0)
    sign_agree=np.mean(np.sign(residual)==np.sign(amp_med[None,:,:]),axis=0)

    # local-neighbor synchronicity: correlation of each star with nearest neighbors.
    dist=np.hypot(positions[:,None,0]-positions[None,:,0],positions[:,None,1]-positions[None,:,1])
    np.fill_diagonal(dist,np.inf)
    neighbor_idx=np.argsort(dist,axis=1)[:,:min(3,max(1,n-1))]
    local_med=np.zeros_like(ref)
    for j in range(n): local_med[j]=np.median(ref[neighbor_idx[j]],axis=0)

    # same-dither repeat statistic: compare event to the other three epochs with same group.
    events=[]
    for j in range(n):
        e=int(maxepoch[j]); vals=np.array([residual[ir,j,e] for ir in range(nr)],float)
        g=e%4; peers=[q for q in range(g,16,4) if q!=e]
        same=np.median(ref[j,peers]) if peers else np.nan
        cmad=float(ap_mad[j,e]); med=float(np.median(vals)); denom=max(abs(med),0.02)
        crossfrac=cmad/denom
        neighbor=float(local_med[j,e])
        # centroid change relative to this star's median centroid
        cmed=float(np.median(cent[j])); cdev=float(abs(cent[j,e]-cmed))
        events.append({
          'rank_peak':float(p[j]), 'event_epoch':e, 'dither_group':g,
          'ref_abs_excursion':float(maxamp[j]), 'aperture_residuals':{str(r):float(vals[k]) for k,r in enumerate(RADII)},
          'median_aperture_residual':med, 'aperture_mad':cmad, 'aperture_disagreement_fraction':float(crossfrac),
          'aperture_sign_agreement':float(sign_agree[j,e]), 'same_dither_other_epochs_median':float(same),
          'nearest3_local_median_residual':neighbor, 'centroid_abs_pixels':float(cent[j,e]),
          'centroid_change_from_star_median_pixels':cdev,
          'nearest_neighbor_pixels':float(np.min(dist[j]))
        })
    events.sort(key=lambda z:z['ref_abs_excursion'],reverse=True)

    # Evaluate predeclared consistency grids on >20% events. These do not use brightness.
    pathological=maxamp>0.20; grids=[]
    for frac in (0.20,0.35,0.50):
      for cdev in (0.15,0.25,0.40):
        good=np.ones(n,dtype=bool)
        for j in range(n):
            e=maxepoch[j]; med=np.median(residual[:,j,e]); disagree=np.median(np.abs(residual[:,j,e]-med))/max(abs(med),0.02)
            good[j]=(disagree<=frac and sign_agree[j,e]>=0.75 and abs(cent[j,e]-np.median(cent[j]))<=cdev)
        grids.append({'max_aperture_disagreement_fraction':frac,'max_centroid_change_pixels':cdev,
                      'stars_kept':int(good.sum()),'gt20pct_events':int(pathological.sum()),
                      'gt20pct_consistent':int(np.sum(pathological&good)),'gt20pct_inconsistent':int(np.sum(pathological&~good)),
                      'le20pct_kept':int(np.sum((~pathological)&good)),'le20pct_rejected':int(np.sum((~pathological)&~good)),
                      'max_excursion_kept':float(np.max(maxamp[good])) if np.any(good) else None})

    out={'success':True,'note':'development cross-aperture/dither/neighbor quality diagnostic; not a discovery threshold',
         'stars_valid':int(n),'radii':list(RADII),'gt20pct_events':int(pathological.sum()),
         'grids':grids,'worst_events':events[:20]}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))

if __name__=='__main__': main()
