#!/usr/bin/env python3
import json, math, urllib.request, io
from pathlib import Path
import numpy as np
from astropy.io import fits

FIELD='112053'
FILES=[
 ('60334','spec-112053-60334-63050396111356292.fits'),
 ('60660','spec-112053-60660-63050396111356292.fits'),
 ('60665','spec-112053-60665-63050396111356292.fits'),
]
BASE='https://dr20.sdss.org/sas/dr20/spectro/boss/redux/v6_2_1/spectra/daily'
C=299792.458
# Avoid Balmer lines because VOS 461 is a strong emission-line Herbig star.
# Photospheric/stellar absorption diagnostics plausible in an A0 spectrum.
LINES={
 'CaII_K':3933.663,
 'MgII_4481':4481.126,
 'HeI_4026':4026.191,
 'HeI_4471':4471.480,
}
OUT=Path('results/sdss_dr20_postsurvivor_spectrum_feature_audit.json'); OUT.parent.mkdir(exist_ok=True)

def download(url):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-DR20-SpectrumAudit/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r:return r.read()

def extract(raw):
 with fits.open(io.BytesIO(raw),memmap=False) as h:
  meta=[{'i':i,'name':x.name,'shape':None if x.data is None else getattr(x.data,'shape',None),'cols':None if not hasattr(x.data,'names') else list(x.data.names)} for i,x in enumerate(h)]
  tab=None
  for x in h[1:]:
   if x.data is not None and hasattr(x.data,'names') and x.data.names and 'loglam' in [n.lower() for n in x.data.names] and 'flux' in [n.lower() for n in x.data.names]:
    tab=x.data; break
  if tab is None: raise RuntimeError('no flux/loglam table')
  cmap={n.lower():n for n in tab.names}; wave=10**np.asarray(tab[cmap['loglam']],float); flux=np.asarray(tab[cmap['flux']],float)
  ivar=np.asarray(tab[cmap['ivar']],float) if 'ivar' in cmap else np.ones_like(flux)
 return wave,flux,ivar,meta

def feature(w,f,iv,rest,rv=-471.7881):
 expected=rest*(1+rv/C)
 # local linear continuum from outer portions of +/-18 A window, then minimum in +/-4 A about predicted and +/-10 A about rest
 m=(w>rest-18)&(w<rest+18)&np.isfinite(f)&(iv>0)
 if m.sum()<20:return {'expected_A':expected,'usable':False}
 ww=w[m]; ff=f[m]; vv=iv[m]
 outer=(np.abs(ww-rest)>11)
 if outer.sum()<6: outer=np.ones_like(ww,dtype=bool)
 p=np.polyfit(ww[outer],ff[outer],1,w=np.sqrt(np.maximum(vv[outer],1e-12)))
 nf=ff/np.polyval(p,ww)
 def minnear(center,half):
  q=np.abs(ww-center)<=half
  if q.sum()<3:return None
  j=np.flatnonzero(q)[np.argmin(nf[q])]
  lam=float(ww[j]); return {'lambda_A':lam,'norm_flux':float(nf[j]),'velocity_kms':float((lam/rest-1)*C),'offset_from_expected_A':float(lam-expected)}
 pred=minnear(expected,4.0); broad=minnear(rest,10.0)
 return {'expected_A':float(expected),'predicted_window_min':pred,'broad_window_min':broad,'usable':True}

o={'status':'BOSS_VISIT_SPECTRUM_FEATURE_AUDIT','expected_summary_rv_kms':-471.7881,'features':{},'visits':[]}
try:
 for mjd,fn in FILES:
  url=f'{BASE}/{FIELD}/{fn}'; raw=download(url); w,f,iv,meta=extract(raw)
  rec={'mjd':int(mjd),'file':fn,'url':url,'bytes':len(raw),'wave_min_A':float(np.nanmin(w)),'wave_max_A':float(np.nanmax(w)),'hdu':meta,'lines':{}}
  for name,rest in LINES.items(): rec['lines'][name]=feature(w,f,iv,rest)
  o['visits'].append(rec)
 # aggregate velocities for predicted minima, but do not treat a blind local minimum as proof unless multiple named lines agree.
 for name in LINES:
  vals=[]
  for r in o['visits']:
   z=r['lines'][name].get('predicted_window_min') if r['lines'][name].get('usable') else None
   if z and z['norm_flux']<0.98: vals.append(z['velocity_kms'])
  o['features'][name]={'n_absorption_like_visits':len(vals),'median_velocity_kms':None if not vals else float(np.median(vals)),'velocities_kms':vals}
 o['success']=True
except Exception as e:
 o['success']=False;o['error']=type(e).__name__+': '+str(e)
OUT.write_text(json.dumps(o,indent=2,default=str)+'\n'); print(json.dumps(o,indent=2,default=str))
