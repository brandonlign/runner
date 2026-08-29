#!/usr/bin/env python3
"""Blinded old-era 5XMM vs 4XMM-DR14 slim cohort probe.

HEASARC TAP caps synchronous results at 100,000 rows. This revision deterministically
partitions the full sky into 24 RA bins, rejects any capped bin, and concatenates
all bins before analysis. No source names/IDs/coordinates are emitted.
"""
from pathlib import Path
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.table import Table,vstack
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u

EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_slim_v1.0.fits.gz'
P4=Path('/tmp/4XMM_DR14cat_slim_v1.0.fits.gz')
OUT=Path('results/xmm_dr15_reprocessing_tap.json');OUT.parent.mkdir(parents=True,exist_ok=True)
CUTOFF=60309.99999
BASE=f'sum_flag < 3 AND extent = 0 AND end_time <= {CUTOFF} AND ep_det_ml >= 15'
COLS='ra,dec,pn_hr1,pn_hr2,pn_hr3,pn_hr4,classx_outlier,approx_source_var,gaia_match_prob,wise_match_prob,n_obs,n_contrib,ep_det_ml'
EXPECTED_PARENT=370948

def save(x):OUT.write_text(json.dumps(x,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps(x,indent=2,sort_keys=True,default=str))
def tap(adql):
    b=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':adql}).encode()
    req=urllib.request.Request(EP,data=b,headers={'User-Agent':'ISEF-XMM-reprocessing-TAP/1.1','Content-Type':'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req,timeout=180) as r:raw=r.read()
    txt=raw.decode('utf-8','replace')
    if 'QUERY_STATUS' in txt[:8000] and 'value="ERROR"' in txt[:8000]:raise RuntimeError(txt[:4000])
    return Table.read(io.BytesIO(raw),format='votable')
def all5():
    tabs=[];diag=[]
    width=15.0
    for k in range(24):
        lo=k*width;hi=(k+1)*width
        t=tap(f'SELECT TOP 100000 {COLS} FROM xmmssc WHERE {BASE} AND ra >= {lo} AND ra < {hi}')
        n=len(t);diag.append({'ra_min':lo,'ra_max':hi,'rows':n})
        if n>=100000:raise RuntimeError(f'RA bin {lo}-{hi} hit TAP cap; increase partitioning')
        tabs.append(t)
    t=vstack(tabs,metadata_conflicts='silent')
    return t,diag
def dl4():
    reqh=urllib.request.Request(U4,method='HEAD',headers={'User-Agent':'ISEF-XMM-reprocessing-TAP/1.1'})
    with urllib.request.urlopen(reqh,timeout=30) as r:total=int(r.headers['Content-Length'])
    if P4.exists() and P4.stat().st_size==total:return
    req=urllib.request.Request(U4,headers={'User-Agent':'ISEF-XMM-reprocessing-TAP/1.1'})
    with urllib.request.urlopen(req,timeout=180) as r,P4.open('wb') as f:
      while True:
        b=r.read(8*1024*1024)
        if not b:break
        f.write(b)
    if P4.stat().st_size!=total:raise RuntimeError(f'4XMM slim incomplete {P4.stat().st_size}/{total}')
def pick(names,*opts):
    m={x.upper():x for x in names}
    for x in opts:
        if x.upper() in m:return m[x.upper()]
    return None
def arr(t,n):return np.asarray(t[n],dtype=float)
def summarize(a):
    a=np.asarray(a,dtype=float);a=a[np.isfinite(a)]
    if not len(a):return None
    return {'n':int(len(a)),'median':float(np.median(a)),'q05':float(np.quantile(a,.05)),'q25':float(np.quantile(a,.25)),'q75':float(np.quantile(a,.75)),'q95':float(np.quantile(a,.95)),'min':float(np.min(a)),'max':float(np.max(a))}
def main():
  try:
    t5,bins=all5()
    if len(t5)!=EXPECTED_PARENT:
        return save({'success':False,'stage':'pagination_completeness','rows':int(len(t5)),'expected':EXPECTED_PARENT,'ra_bins':bins,'note':'Refusing scientific comparison until full parent is reproduced.'})
    dl4()
    with fits.open(P4,memmap=True) as h:
      tabs=[z for z in h if isinstance(z,(fits.BinTableHDU,fits.TableHDU)) and z.data is not None];d=max(tabs,key=lambda z:len(z.data)).data;n=list(d.names)
      r4=pick(n,'SC_RA','RA');q4=pick(n,'SC_DEC','DEC')
      if not r4 or not q4:return save({'success':False,'stage':'4xmm_semantics','columns':n})
      ra4=np.asarray(d[r4],float);de4=np.asarray(d[q4],float);ok=np.isfinite(ra4)&np.isfinite(de4);ra4=ra4[ok];de4=de4[ok]
      ra5=arr(t5,'ra');de5=arr(t5,'dec');ok5=np.isfinite(ra5)&np.isfinite(de5);idx=np.where(ok5)[0]
      _,sep,_=SkyCoord(ra5[idx]*u.deg,de5[idx]*u.deg).match_to_catalog_sky(SkyCoord(ra4*u.deg,de4*u.deg));sec=sep.arcsec
      radii=(2,3,5,7,10,15,20,30);counts={str(r):int(np.sum(sec>r)) for r in radii}
      orphan=idx[sec>10];present=idx[sec<=3]
      out={'success':True,'decision':'OLD_ERA_4XMM_ABSENT_COHORT_EXISTS' if len(orphan)>=100 else 'COHORT_SMALL','base':BASE,'five_parent_rows':int(len(t5)),'parent_complete':True,'ra_bins':bins,'four_slim_rows':int(len(d)),'four_valid_positions':int(len(ra4)),'unmatched_counts_by_radius_arcsec':counts,'conservative_unmatched_10arcsec':int(len(orphan)),'comparison_present_within_3arcsec':int(len(present)),'note':'No identities/coordinates emitted. END_TIME is only an old-era proxy; exact contributing ObsIDs remain mandatory before reprocessing-only claim.'}
      for c in ('pn_hr1','pn_hr2','pn_hr3','pn_hr4','classx_outlier','approx_source_var','n_obs','n_contrib','ep_det_ml'):
        z=arr(t5,c);out[f'cohort_{c}']=summarize(z[orphan]);out[f'present_{c}']=summarize(z[present])
      for c in ('gaia_match_prob','wise_match_prob'):
        z=arr(t5,c);out[f'cohort_{c}_finite_fraction']=float(np.isfinite(z[orphan]).mean()) if len(orphan) else None;out[f'present_{c}_finite_fraction']=float(np.isfinite(z[present]).mean()) if len(present) else None
      hr3=arr(t5,'pn_hr3');ol=arr(t5,'classx_outlier');var=arr(t5,'approx_source_var');g=arr(t5,'gaia_match_prob');w=arr(t5,'wise_match_prob')
      def frac(ix,mask):return {'n':int(np.sum(mask[ix])),'denom':int(len(ix)),'fraction':float(np.mean(mask[ix])) if len(ix) else None}
      tests={'very_soft_hr3':np.isfinite(hr3)&(hr3<-0.78),'classx_ge5':np.isfinite(ol)&(ol>=5),'classx_ge8':np.isfinite(ol)&(ol>=8),'var_ge30':np.isfinite(var)&(var>=30),'var_ge100':np.isfinite(var)&(var>=100),'no_gaia_no_wise':~np.isfinite(g)&~np.isfinite(w),'soft_no_gaia_no_wise':np.isfinite(hr3)&(hr3<-0.78)&~np.isfinite(g)&~np.isfinite(w)}
      out['fixed_enrichment']={k:{'cohort':frac(orphan,m),'present':frac(present,m)} for k,m in tests.items()}
      save(out)
  except Exception as e:save({'success':False,'stage':'analysis','error':f'{type(e).__name__}: {e}'})
if __name__=='__main__':main()
