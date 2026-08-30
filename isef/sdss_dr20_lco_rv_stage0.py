#!/usr/bin/env python3
"""Anonymous DR20 BOSS-LCO repeat-stable extreme-RV feasibility screen."""
from pathlib import Path
import json, urllib.request, gzip, shutil
import numpy as np
from astropy.io import fits
OUT=Path('results/sdss_dr20_lco_rv_stage0.json');OUT.parent.mkdir(parents=True,exist_ok=True)
URL='https://dr20.sdss.org/sas/dr20/spectro/astra/0.8.1/summary/mwmAllStar-0.8.1.fits.gz'
TH=[300.,400.,500.,600.,800.]
def dl(url,p):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-SDSS-DR20-LCO-RV/1.0'})
 with urllib.request.urlopen(req,timeout=300) as r,open(p,'wb') as f:
  while True:
   b=r.read(8<<20)
   if not b:break
   f.write(b)
def q(x):
 if len(x)==0:return {}
 return {str(p):float(np.quantile(x,p)) for p in [0,.5,.9,.95,.99,.999,1]}
def main():
 out={'success':False,'status':'ANONYMOUS_LCO_RV_STAGE0','identities_emitted':False,'thresholds_abs_vrad_kms':TH}
 try:
  pgz=Path('/tmp/mwmAllStar.fits.gz');pf=Path('/tmp/mwmAllStar.fits');dl(URL,pgz)
  with gzip.open(pgz,'rb') as src,open(pf,'wb') as dst:shutil.copyfileobj(src,dst,length=8<<20)
  with fits.open(pf,memmap=True) as h:
   # Official model: BOSS APO then BOSS LCO. Find explicit telescope=LCO table if HDU layout changes.
   candidates=[x for x in h[1:] if getattr(x,'data',None) is not None and hasattr(x.data,'names') and 'telescope' in x.data.names and 'v_rad' in x.data.names]
   lco=None
   hdu_meta=[]
   for x in candidates:
    tel=np.asarray(x.data['telescope']).astype(str);vals=np.unique(np.char.strip(tel))
    hdu_meta.append({'extname':x.name,'rows':int(len(x.data)),'telescope_values':[str(v) for v in vals[:20]]})
    if any('lco' in str(v).lower() for v in vals):lco=x.data
   out['hdu_structure']=hdu_meta
   if lco is None:raise RuntimeError('No BOSS-LCO table found')
   d=lco;v=np.asarray(d['v_rad'],float);ev=np.asarray(d['e_v_rad'],float);sv=np.asarray(d['std_v_rad'],float);sn=np.asarray(d['snr'],float);ng=np.asarray(d['n_good_rvs'],int);zw=np.asarray(d['zwarning_flags'],np.int64);nm=np.asarray(d['nmf_flags'],np.int64)
   base=np.isfinite(v)&np.isfinite(ev)&np.isfinite(sv)&np.isfinite(sn)&(sn>10)&(ev<30)&(ng>=2)&(sv<=30)&(zw==0)&(nm==0)
   very=base&(ev<=15)&(sv<=15)
   gv=np.asarray(d['gaia_v_rad'],float);ge=np.asarray(d['gaia_e_v_rad'],float);gok=base&np.isfinite(gv)&np.isfinite(ge)&(np.abs(v-gv)<=50)
   av=np.abs(v)
   out['lco_rows']=int(len(d));out['repeat_stable_rows']=int(base.sum());out['very_stable_rows']=int(very.sum());out['gaia_consistent_rows']=int(gok.sum())
   out['repeat_stable_counts']={str(int(t)):int(np.sum(base&(av>t))) for t in TH}
   out['very_stable_counts']={str(int(t)):int(np.sum(very&(av>t))) for t in TH}
   out['gaia_consistent_counts']={str(int(t)):int(np.sum(gok&(av>t))) for t in TH}
   out['union_independent_check_counts']={str(int(t)):int(np.sum(base&(av>t)&(very|gok))) for t in TH}
   out['quantiles_repeat_stable']={'abs_v_rad_kms':q(av[base]),'e_v_rad_kms':q(ev[base]),'std_v_rad_kms':q(sv[base]),'snr':q(sn[base]),'n_good_rvs':q(ng[base].astype(float))}
   c400=out['repeat_stable_counts']['400'];c500=out['repeat_stable_counts']['500'];cind=out['union_independent_check_counts']['400']
   out['decision']='LCO_RV_TAIL_EXISTS' if c400>=10 and c500>=2 and cind>=3 else 'LCO_RV_TAIL_TOO_SMALL';out['success']=True
 except Exception as e:out['error']=f'{type(e).__name__}: {e}';out['decision']='INFRASTRUCTURE_FAILURE_NO_SCIENTIFIC_DECISION'
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
