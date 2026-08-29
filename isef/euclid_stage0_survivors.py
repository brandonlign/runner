#!/usr/bin/env python3
"""Inspect large Stage-0 photometric excursions that survive candidate-independent morphology cuts."""
import json
from pathlib import Path
import numpy as np
from astropy.stats import sigma_clipped_stats
from photutils.detection import DAOStarFinder
import euclid_routed_feasibility as b
import euclid_stage0_quality as q

RES=Path('results/euclid_routed_feasibility.json');NPZ=Path('results/euclid_routed_stamps.npz');OUT=Path('results/euclid_stage0_survivors.json')

def ms(x,f=1e-6):
 m=np.nanmedian(x);s=max(float(1.4826*np.nanmedian(np.abs(x-m))),f);return m,s

def main():
 base=json.loads(RES.read_text());cube=np.load(NPZ)['stamps'];ra0=float(base['target']['ra']);dec0=float(base['target']['dec']);routes={int(g):int(v['k']) for g,v in base['routes'].items()};hs=b.epoch_headers(routes)
 origins=[]
 for z in hs:
  x,y=b.pix(z,ra0,dec0);origins.append((int(round(float(x)))-b.HALF,int(round(float(y)))-b.HALF))
 _,bg,std=sigma_clipped_stats(cube[0],sigma=3,maxiters=5);tab=DAOStarFinder(fwhm=1.8,threshold=max(6*std,1e-6),exclude_border=True)(cube[0]-bg)
 x=np.asarray(tab['xcentroid'],float);y=np.asarray(tab['ycentroid'],float);peak=np.asarray(tab['peak'],float);ids=[];nn=[]
 for j in range(len(x)):
  if not(12<x[j]<b.STAMP-12 and 12<y[j]<b.STAMP-12):continue
  dd=np.hypot(x-x[j],y-y[j]);dd[j]=np.inf
  if np.min(dd)>=7:ids.append(j);nn.append(float(np.min(dd)))
 ids=np.asarray(ids,int);ord=np.argsort(peak[ids])[::-1][:80];ids=ids[ord];nn=np.asarray(nn)[ord]
 sx=x[ids]+origins[0][0];sy=y[ids]+origins[0][1];wr,wd=hs[0].w.pixel_to_world_values(sx,sy);n=len(ids)
 fs=np.full((n,16),np.nan);fl=np.full((n,16),np.nan);rat=np.full((n,16),np.nan);cen=np.full((n,16),np.nan);noi=np.full((n,16),np.nan)
 for e,z in enumerate(hs):
  px,py=z.w.world_to_pixel_values(wr,wd);px=np.asarray(px,float)-origins[e][0];py=np.asarray(py,float)-origins[e][1]
  for j,(xx,yy) in enumerate(zip(px,py)):
   if 11<=xx<b.STAMP-11 and 11<=yy<b.STAMP-11:fs[j,e],fl[j,e],rat[j,e],cen[j,e],noi[j,e]=q.aperture_and_shape(cube[e],xx,yy)
 ok=np.all(np.isfinite(fs)&np.isfinite(fl)&np.isfinite(rat)&np.isfinite(cen)&(fs>0)&(fl>0),axis=1)
 fs=fs[ok];fl=fl[ok];rat=rat[ok];cen=cen[ok];noi=noi[ok];wr=np.asarray(wr)[ok];wd=np.asarray(wd)[ok];pk=peak[ids][ok];nn=nn[ok]
 nrm=fs/np.median(fs,axis=1)[:,None];common=np.median(nrm,axis=0);corr=nrm/common[None,:];large=fl/np.median(fl,axis=1)[:,None];large/=np.median(large,axis=0)[None,:]
 rows=[]
 for j in range(len(fs)):
  mr,sr=ms(rat[j],.002);mc,sc=ms(cen[j],.03);mn,sn=ms(noi[j],1e-6)
  rz=np.abs(rat[j]-mr)/sr;cz=np.abs(cen[j]-mc)/sc;nz=np.abs(noi[j]-mn)/sn;bad=(rz>4)|(cz>4)|(nz>8)
  exc=float(np.max(np.abs(corr[j]-1)));e=int(np.argmax(np.abs(corr[j]-1)))
  if exc>0.20 and not np.any(bad):
   rows.append({'ra':float(wr[j]),'dec':float(wd[j]),'rank_peak':float(pk[j]),'nearest_detected_neighbor_px':float(nn[j]),'max_excursion':exc,'event_epoch':e,'event_sign':'brightening' if corr[j,e]>1 else 'dimming','small_aperture_corrected':[float(v) for v in corr[j]],'large_aperture_corrected':[float(v) for v in large[j]],'small_large_ratio':[float(v) for v in rat[j]],'centroid_offset_px':[float(v) for v in cen[j]],'background_noise':[float(v) for v in noi[j]],'ratio_z':[float(v) for v in rz],'centroid_z':[float(v) for v in cz],'noise_z':[float(v) for v in nz],'small_large_event_agreement':float(abs((corr[j,e]-1)-(large[j,e]-1)))})
 rows.sort(key=lambda r:r['max_excursion'],reverse=True)
 out={'success':True,'strict_quality_rule':'all epochs ratio_z<=4, centroid_z<=4, noise_z<=8; rule does not use excursion amplitude','survivors':rows}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
