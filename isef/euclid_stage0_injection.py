#!/usr/bin/env python3
"""Pilot light-curve injection/recovery on the real Stage-0 Euclid stamps.

This is a development sensitivity test, not the final image-level completeness
experiment and not a survey discovery threshold.
"""
import json
from pathlib import Path
import numpy as np
from astropy.stats import sigma_clipped_stats
from photutils.detection import DAOStarFinder
import euclid_routed_feasibility as b
import euclid_stage0_diagnostics as d

RES=Path('results/euclid_routed_feasibility.json');NPZ=Path('results/euclid_routed_stamps.npz');OUT=Path('results/euclid_stage0_injection.json')

def build_flux(radius=1.8):
    base=json.loads(RES.read_text());cube=np.load(NPZ)['stamps'];ra=float(base['target']['ra']);dec=float(base['target']['dec']);routes={int(g):int(v['k']) for g,v in base['routes'].items()};hs=b.epoch_headers(routes)
    origins=[]
    for q in hs:
        x,y=b.pix(q,ra,dec);origins.append((int(round(float(x)))-b.HALF,int(round(float(y)))-b.HALF))
    _,bg,std=sigma_clipped_stats(cube[0],sigma=3,maxiters=5);tab=DAOStarFinder(fwhm=1.8,threshold=max(6*std,1e-6),exclude_border=True)(cube[0]-bg)
    x=np.asarray(tab['xcentroid'],float);y=np.asarray(tab['ycentroid'],float);peak=np.asarray(tab['peak'],float);ids=[]
    for j in range(len(x)):
        if not(12<x[j]<b.STAMP-12 and 12<y[j]<b.STAMP-12):continue
        dd=np.hypot(x-x[j],y-y[j]);dd[j]=np.inf
        if np.min(dd)>=7:ids.append(j)
    ids=np.asarray(ids,int);ids=ids[np.argsort(peak[ids])[::-1][:80]];sx=x[ids]+origins[0][0];sy=y[ids]+origins[0][1];wr,wd=hs[0].w.pixel_to_world_values(sx,sy)
    fl=np.full((len(ids),16),np.nan)
    for e,q in enumerate(hs):
        px,py=q.w.world_to_pixel_values(wr,wd);px=np.asarray(px)-origins[e][0];py=np.asarray(py)-origins[e][1]
        for j,(xx,yy) in enumerate(zip(px,py)):
            if 11<=xx<b.STAMP-11 and 11<=yy<b.STAMP-11:fl[j,e]=d.aperture(cube[e],xx,yy,radius)
    ok=np.all(np.isfinite(fl)&(fl>0),axis=1);return fl[ok],peak[ids][ok]

def normalize(fl):
    n=fl/np.median(fl,axis=1)[:,None];common=np.median(n,axis=0);return n/common[None,:]

def robust_sigma(v):
    m=np.median(v);s=1.4826*np.median(np.abs(v-m));return max(float(s),0.003)

def stat(v):
    s=robust_sigma(v);return float(np.max(np.abs(v-np.median(v)))/s)

def main():
    rng=np.random.default_rng(20260829);out={'success':True,'note':'development light-curve injection on real measured residuals; not final image-level completeness or survey FDR','radii':{}}
    for radius in (1.8,3.2):
        fl,peak=build_flux(radius);corr=normalize(fl);null=np.array([stat(v) for v in corr]);threshold=float(np.quantile(null,0.95,method='higher'));false_positive=float(np.mean(null>=threshold));rows=[]
        for kind,sign in [('flare',1),('eclipse',-1)]:
          for duration in (1,2,3):
            for amp in (0.03,0.05,0.08,0.10,0.15,0.20,0.30):
                hit=0;trials=0
                for i,v in enumerate(corr):
                    for rep in range(30):
                        start=int(rng.integers(0,17-duration));z=v.copy();z[start:start+duration]*=(1+sign*amp);hit+=stat(z)>=threshold;trials+=1
                rows.append({'kind':kind,'duration_epochs':duration,'amplitude':amp,'recovery':hit/trials,'trials':trials})
        out['radii'][str(radius)]={'stars':int(len(corr)),'null_threshold_95pct_max_abs_mad':threshold,'empirical_star_false_positive_fraction':false_positive,'median_fractional_scatter':float(np.median([d.rscatter(v) for v in corr])),'injections':rows}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))

if __name__=='__main__':main()
