#!/usr/bin/env python3
import json, urllib.request, io
from pathlib import Path
import numpy as np
from astropy.io import fits
FIELD='112053';GROUP='112XXX';CID='63050396111356292';MJDS=['60334','60660','60665']
BASE='https://data.sdss.org/sas/dr20/spectro/boss/redux/v6_2_1/spectra/daily/full';C=299792.458
LINES={'Halpha':6562.79,'Hbeta':4861.35,'Hgamma':4340.472,'Hdelta':4101.734}
OUT=Path('results/sdss_dr20_postsurvivor_emission_velocity_audit.json');OUT.parent.mkdir(exist_ok=True)
def get(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ISEF-DR20-EmissionAudit/1.0'}),timeout=180) as r:return r.read()
def calc(w,f,iv,rest):
 m=(w>rest-35)&(w<rest+35)&np.isfinite(f)&(iv>0)
 ww=w[m];ff=f[m];vv=iv[m]
 side=(np.abs(ww-rest)>22)
 if side.sum()<8:return {'usable':False}
 p=np.polyfit(ww[side],ff[side],1,w=np.sqrt(np.maximum(vv[side],1e-9))); cont=np.polyval(p,ww);nf=ff/cont
 # strongest emission peak and flux-weighted centroid above continuum within +/- 18 A
 q=np.abs(ww-rest)<=18; qi=np.flatnonzero(q); j=qi[np.argmax(nf[q])]
 peak_lam=float(ww[j]); peak_v=float((peak_lam/rest-1)*C)
 excess=np.maximum(nf[q]-1,0); centroid=float(np.sum(ww[q]*excess)/np.sum(excess)) if np.sum(excess)>0 else None
 centroid_v=None if centroid is None else float((centroid/rest-1)*C)
 # also find absorption minimum for reverse-P-Cygni context
 k=qi[np.argmin(nf[q])]; min_lam=float(ww[k]);min_v=float((min_lam/rest-1)*C)
 return {'usable':True,'peak_lambda_A':peak_lam,'peak_velocity_kms':peak_v,'peak_norm_flux':float(nf[j]),'emission_excess_centroid_A':centroid,'centroid_velocity_kms':centroid_v,'min_lambda_A':min_lam,'min_velocity_kms':min_v,'min_norm_flux':float(nf[k])}
o={'status':'POSTSURVIVOR_BALMER_EMISSION_VELOCITY_AUDIT','visits':[]}
try:
 for mjd in MJDS:
  fn=f'spec-{FIELD}-{mjd}-{CID}.fits';url=f'{BASE}/{GROUP}/{FIELD}/{mjd}/{fn}';raw=get(url)
  with fits.open(io.BytesIO(raw),memmap=False) as h:
   t=h['COADD'].data;w=10**np.asarray(t['LOGLAM'],float);f=np.asarray(t['FLUX'],float);iv=np.asarray(t['IVAR'],float)
   zline=[]
   if 'ZLINE' in h:
    for r in h['ZLINE'].data:
     name=r['LINENAME'].decode(errors='replace').strip() if isinstance(r['LINENAME'],bytes) else str(r['LINENAME']).strip()
     if any(x.lower() in name.lower() for x in ['h_alpha','halpha','h_beta','hbeta','h_gamma','hgamma','h_delta','hdelta']):
      zline.append({'name':name,'linewave':float(r['LINEWAVE']),'linez':float(r['LINEZ']),'linez_err':float(r['LINEZ_ERR']),'velocity_kms':float(r['LINEZ']*C),'area':float(r['LINEAREA']),'ew':float(r['LINEEW'])})
   o['visits'].append({'mjd':int(mjd),'lines':{n:calc(w,f,iv,r) for n,r in LINES.items()},'pipeline_zline_balmer':zline})
 o['success']=True
except Exception as e:o['success']=False;o['error']=type(e).__name__+': '+str(e)
OUT.write_text(json.dumps(o,indent=2,default=str)+'\n');print(json.dumps(o,indent=2,default=str))
