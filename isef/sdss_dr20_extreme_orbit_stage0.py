#!/usr/bin/env python3
"""Anonymous SDSS DR20 GravPot16 extreme-apocenter Stage 0.
Emits aggregate counts/quantiles only; never source IDs or row indices.
"""
from pathlib import Path
import json, urllib.request
import numpy as np
from astropy.io import fits
OUT=Path('results/sdss_dr20_extreme_orbit_stage0.json');OUT.parent.mkdir(parents=True,exist_ok=True)
URL='https://data.sdss.org/sas/dr20/vac/mwm/orbits/GravPot16-1.0.0.fits'
TH=[30.,50.,100.,200.]
def download(url,p):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-SDSS-DR20-extreme-orbit/1.0'})
 with urllib.request.urlopen(req,timeout=300) as r,open(p,'wb') as f:
  while True:
   b=r.read(8<<20)
   if not b:break
   f.write(b)
def q(x):
 if len(x)==0:return {}
 return {str(p):float(np.quantile(x,p)) for p in [0,.5,.9,.95,.99,.999,1]}
def main():
 out={'success':False,'status':'ANONYMOUS_STAGE0','identities_emitted':False,'thresholds_kpc':TH}
 try:
  p=Path('/tmp/GravPot16-1.0.0.fits');download(URL,p)
  with fits.open(p,memmap=True) as h:
   d=max([x for x in h if getattr(x,'data',None) is not None and hasattr(x.data,'names')],key=lambda x:len(x.data)).data
   apo=np.asarray(d['apo_ps41'],float);err=np.asarray(d['Error_apo_ps41'],float);ruwe=np.asarray(d['RUWE'],float)
   good=np.isfinite(apo)&np.isfinite(err)&np.isfinite(ruwe)&(apo>0)&(err>0)&(ruwe<1.4)
   alo=apo-2*err;frac=err/apo
   out['total_rows']=int(len(d));out['quality_screened_rows']=int(good.sum());out['quality_fraction']=float(good.mean())
   out['counts_apo_lo2_gt_kpc']={str(int(t)):int(np.sum(good&(alo>t))) for t in TH}
   out['quantiles']={'apo_ps41_kpc':q(apo[good]),'apo_lo2_kpc':q(alo[good]),'ruwe':q(ruwe[good]),'apo_fractional_error':q(frac[good])}
   c100=out['counts_apo_lo2_gt_kpc']['100'];c200=out['counts_apo_lo2_gt_kpc']['200']
   out['decision']='TAIL_EXISTS' if c100>=20 and c200>=3 else 'TAIL_TOO_SMALL';out['success']=True
 except Exception as e:out['error']=f'{type(e).__name__}: {e}';out['decision']='INFRASTRUCTURE_FAILURE_NO_SCIENTIFIC_DECISION'
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
