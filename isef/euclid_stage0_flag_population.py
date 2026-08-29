#!/usr/bin/env python3
"""Population-level flag audit of large aperture excursions in Stage-0 patch.

Identifies >10% and >20% measurements using the pre-existing fixed aperture
photometry, then checks released Euclid FLG pixels at those source/epoch
positions. This quantifies how much of the raw high-excursion tail is directly
explained by pipeline artifact flags before any blind search.
"""
import json, math, urllib.request
from pathlib import Path
import numpy as np
from astropy.stats import sigma_clipped_stats
from photutils.detection import DAOStarFinder
import euclid_routed_feasibility as b
import euclid_stage0_diagnostics as d
import euclid_stage0_flag_validation as fv

RES=Path('results/euclid_routed_feasibility.json');NPZ=Path('results/euclid_routed_stamps.npz');OUT=Path('results/euclid_stage0_flag_population.json')
LAY={}

def layout(url):
    if url not in LAY:LAY[url]=fv.layout(url)
    return LAY[url]
def stamp_cached(url,k,x,y,half=2):
    lay=layout(url);nx=lay['nx'];ny=lay['ny'];bpp=abs(lay['bitpix'])//8;cx=int(round(float(x)));cy=int(round(float(y)));x0=max(0,cx-half);x1=min(nx,cx+half+1);y0=max(0,cy-half);y1=min(ny,cy+half+1);ext=lay['primary_offset']+k*lay['stride'];data0=ext+lay['header_bytes'];start=data0+y0*nx*bpp;end=data0+y1*nx*bpp-1;raw,_=fv.rr(url,start,end);rows=np.frombuffer(raw,dtype=fv.dtype_for(lay['bitpix'])).reshape(y1-y0,nx);return rows[:,x0:x1].copy()
def main():
    base=json.loads(RES.read_text());cube=np.load(NPZ)['stamps'];ra0=float(base['target']['ra']);de0=float(base['target']['dec']);routes={int(g):int(v['k']) for g,v in base['routes'].items()};hs=b.epoch_headers(routes);orig=[]
    for q in hs:
        x,y=b.pix(q,ra0,de0);orig.append((int(round(float(x)))-b.HALF,int(round(float(y)))-b.HALF))
    _,bg,std=sigma_clipped_stats(cube[0],sigma=3,maxiters=5);tab=DAOStarFinder(fwhm=1.8,threshold=max(6*std,1e-6),exclude_border=True)(cube[0]-bg);x=np.asarray(tab['xcentroid'],float);y=np.asarray(tab['ycentroid'],float);peak=np.asarray(tab['peak'],float);ids=[]
    for j in range(len(x)):
        if not(12<x[j]<b.STAMP-12 and 12<y[j]<b.STAMP-12):continue
        dd=np.hypot(x-x[j],y-y[j]);dd[j]=np.inf
        if np.min(dd)>=7:ids.append(j)
    ids=np.asarray(ids,int);ids=ids[np.argsort(peak[ids])[::-1][:80]];sx=x[ids]+orig[0][0];sy=y[ids]+orig[0][1];wr,wd=hs[0].w.pixel_to_world_values(sx,sy);fl=np.full((len(ids),16),np.nan)
    pos=[]
    for e,q in enumerate(hs):
        px,py=q.w.world_to_pixel_values(wr,wd);px=np.asarray(px)-orig[e][0];py=np.asarray(py)-orig[e][1];pos.append((px,py))
        for j,(xx,yy) in enumerate(zip(px,py)):
            if 9<=xx<b.STAMP-9 and 9<=yy<b.STAMP-9:fl[j,e]=d.aperture(cube[e],xx,yy,1.8)
    ok=np.all(np.isfinite(fl)&(fl>0),axis=1);fl=fl[ok];wr=np.asarray(wr)[ok];wd=np.asarray(wd)[ok];ids=ids[ok]
    n=fl/np.median(fl,axis=1)[:,None];common=np.median(n,axis=0);corr=n/common[None,:];events=[]
    for j in range(len(fl)):
      for e in range(16):
        exc=float(abs(corr[j,e]-1))
        if exc<=0.10:continue
        q=hs[e];ra=float(wr[j]);de=float(wd[j]);gx,gy=b.pix(q,ra,de);sci=b.FILES[e];fn=sci.replace('_sci.fits','_flg.fits');url=f'{b.BASE}/{fn}'
        try:
            z=stamp_cached(url,q.k,gx,gy,2).astype(np.int64);cv=int(z[z.shape[0]//2,z.shape[1]//2]);bits={'invalid':bool(np.any(z&1)),'hot':bool(np.any(z&2)),'cosmic':bool(np.any(z&16)),'cr_region':bool(np.any(z&512)),'saturated':bool(np.any(z&8)),'bad_column':bool(np.any(z&128))};artifact=any(bits.values())
        except Exception as ex:cv=None;bits={};artifact=None
        events.append({'star':j,'ra':ra,'dec':de,'epoch':e,'signed_residual':float(corr[j,e]-1),'abs_excursion':exc,'center_flag':cv,'artifact_flag_in_5x5':artifact,'artifact_bits':bits})
    def sm(th):
        r=[e for e in events if e['abs_excursion']>th];known=[e for e in r if e['artifact_flag_in_5x5'] is not None];return {'events':len(r),'flag_read_success':len(known),'artifact_flagged':sum(e['artifact_flag_in_5x5'] for e in known),'artifact_flagged_fraction':float(np.mean([e['artifact_flag_in_5x5'] for e in known])) if known else None,'unflagged':sum(not e['artifact_flag_in_5x5'] for e in known)}
    out={'success':True,'note':'population-level released-FLG audit for raw aperture excursions; flags are candidate-independent','stars':len(fl),'measurements':len(fl)*16,'gt10':sm(0.10),'gt20':sm(0.20),'events':sorted(events,key=lambda e:e['abs_excursion'],reverse=True)};OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
