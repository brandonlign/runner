#!/usr/bin/env python3
"""Pre-flux TESS 3I timing/quality/injection gate under frozen protocol.

Reads TIME, formal FLUX_ERR_CORR, quality/background/centroid diagnostics and
background-star overlap only. Deliberately never accesses FLUX or FLUX_CORR.
"""
import json, urllib.request
from pathlib import Path
import numpy as np
from astropy.io import fits

REC='https://zenodo.org/api/records/19376249'
OUT=Path('results/tess3i_preflux_sampling_gate.json'); OUT.parent.mkdir(exist_ok=True)
P0_H=7.136; P0=P0_H/24.; GAP=.10; MINSPAN=1.25*P0; NINJ=1000
AMPS=[.01,.02,.05,.10]; RNG=np.random.default_rng(317136)

def medmad(x):
 x=np.asarray(x,float); x=x[np.isfinite(x)]
 if not len(x): return np.nan,np.nan
 m=float(np.median(x)); return m,float(1.4826*np.median(np.abs(x-m)))

def fit_bic(y,e,t,seg,evol=False,signal=True):
 cols=[]; use=np.unique(seg)
 for s in use:
  z=(seg==s).astype(float); c=float(np.median(t[seg==s])); cols += [z,z*(t-c)]
 if signal:
  w=2*np.pi/P0
  if evol:
   for s in use:
    z=(seg==s).astype(float); cols += [z*np.sin(w*t),z*np.cos(w*t)]
  else: cols += [np.sin(w*t),np.cos(w*t)]
 X=np.column_stack(cols); sw=1/np.maximum(e,1e-12); Xw=X*sw[:,None]; yw=y*sw
 b=np.linalg.lstsq(Xw,yw,rcond=None)[0]; r=(y-X@b)/e; chi=float(r@r); k=X.shape[1]; n=len(y)
 return chi+k*np.log(n)

def segment_times(t):
 order=np.argsort(t); ts=t[order]; ids=np.zeros(len(ts),int); s=0
 for i in range(1,len(ts)):
  if ts[i]-ts[i-1] > GAP: s+=1
  ids[i]=s
 back=np.empty_like(ids); back[order]=ids
 return back

def main():
 o={'status':'FROZEN_PREFLUX_SAMPLING_GATE','protocol_commit':'161c881dc8cbe10aaafa96216d1712b877ff3c39','flux_accessed':False,'flux_corr_accessed':False,'success':False}
 try:
  with urllib.request.urlopen(urllib.request.Request(REC,headers={'User-Agent':'ISEF-TESS3I-Preflux/1.0'}),timeout=120) as r: meta=json.load(r)
  fs=[f for f in meta.get('files',[]) if f.get('key','').startswith('hlsp_tess-3i_tess_ffi_') and f.get('key','').endswith('_lc.fits')]
  if len(fs)!=1: raise RuntimeError(f'expected one 200s LC, found {len(fs)}')
  f=fs[0]; url=f.get('links',{}).get('content') or f.get('links',{}).get('self'); p=Path('/tmp')/f['key']
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ISEF-TESS3I-Preflux/1.0'}),timeout=180) as r, open(p,'wb') as w:
   while True:
    b=r.read(1<<20)
    if not b: break
    w.write(b)
  results={}
  with fits.open(p,memmap=True) as h:
   extra=h['EXTRAS'].data
   et=np.asarray(extra['TIME'],float); nstar=np.asarray(extra['NPIX_BKGSTAR_CORE'],float)
   for ap in ['LIGHTCURVE_AP0','LIGHTCURVE_AP1']:
    d=h[ap].data
    # IMPORTANT: no FLUX/FLUX_CORR field is touched anywhere.
    t=np.asarray(d['TIME'],float); er=np.asarray(d['FLUX_ERR_CORR'],float); q=np.asarray(d['QUALITY'],int); aq=np.asarray(d['AP_QUALITY'],int)
    bmad=np.asarray(d['BKG_MAD'],float); bstd=np.asarray(d['BKG_STD'],float); c1=np.asarray(d['MOM_CENTR1'],float); c2=np.asarray(d['MOM_CENTR2'],float)
    if len(et)!=len(t) or np.nanmax(np.abs(et-t))>1e-7: raise RuntimeError('EXTRAS time alignment failed')
    base=np.isfinite(t)&np.isfinite(er)&(er>0)&np.isfinite(bmad)&np.isfinite(bstd)&np.isfinite(c1)&np.isfinite(c2)&(q==0)&(aq==0)&(nstar==0)
    mb,sd=medmad(bmad[base]); bgok=bmad <= mb+5*sd if np.isfinite(sd) else np.ones(len(t),bool)
    mc1=float(np.median(c1[base])); mc2=float(np.median(c2[base])); disp=np.hypot(c1-mc1,c2-mc2); md,ds=medmad(disp[base]); cok=disp <= md+5*ds if np.isfinite(ds) else np.ones(len(t),bool)
    clean=base&bgok&cok; tt=t[clean]; ee=er[clean]
    seg=segment_times(tt); seginfo=[]; evo_ids=[]
    for s in np.unique(seg):
     x=tt[seg==s]; span=float(x.max()-x.min()) if len(x) else 0
     elig=bool(span>=MINSPAN and len(x)>=25)
     if elig: evo_ids.append(int(s))
     seginfo.append({'id':int(s),'n':int(len(x)),'start_btjd':float(x.min()),'stop_btjd':float(x.max()),'span_hours':span*24,'evolution_eligible':elig})
    evo_mask=np.isin(seg,evo_ids); te=tt[evo_mask]; se=seg[evo_mask]; eformal=ee[evo_mask]
    mag=float(h[ap].header['TESSMAG']); fref=10**((20.44-mag)/2.5); efull=ee/fref; efe=eformal/fref
    det_thresh=10.0 if ap=='LIGHTCURVE_AP0' else 6.0
    detrec={}
    for amp in AMPS:
     hit=0
     for j in range(NINJ):
      ph=RNG.uniform(0,2*np.pi); y=amp*np.sin(2*np.pi*tt/P0+ph)+RNG.normal(0,efull)
      b0=fit_bic(y,efull,tt,seg,signal=False); b1=fit_bic(y,efull,tt,seg,evol=False,signal=True)
      if b0-b1>=det_thresh: hit+=1
     detrec[str(amp)]=hit/NINJ
    evohit=0
    if len(evo_ids)>=2:
     lens={s:np.sum(se==s) for s in np.unique(se)}; pair=sorted(lens,key=lambda s:(-lens[s],s))[:2]; pair=sorted(pair,key=lambda s:np.median(te[se==s]))
     cut=float(np.mean([np.median(te[se==pair[0]]),np.median(te[se==pair[1]])]))
     for j in range(NINJ):
      ph=RNG.uniform(0,2*np.pi); shift=np.where(te>cut,0.20*2*np.pi,0.0); y=.05*np.sin(2*np.pi*te/P0+ph+shift)+RNG.normal(0,efe)
      h0=fit_bic(y,efe,te,se,evol=False,signal=True); h1=fit_bic(y,efe,te,se,evol=True,signal=True)
      if h0-h1>=10: evohit+=1
    results[ap]={'rows_total':int(len(t)),'rows_clean':int(clean.sum()),'clean_fraction':float(clean.mean()),'background_mad_median':mb,'background_mad_robust_sigma':sd,'centroid_disp_median':md,'centroid_disp_robust_sigma':ds,'segments':seginfo,'evolution_eligible_segment_count':len(evo_ids),'header_tessmag':mag,'header_implied_flux_e_s':fref,'median_fractional_formal_error':float(np.median(efull)),'detection_delta_bic_threshold':det_thresh,'detection_recovery':detrec,'phase_shift_0p20_recovery':evohit/NINJ if len(evo_ids)>=2 else None}
  ap0=results['LIGHTCURVE_AP0']; ap1=results['LIGHTCURVE_AP1']
  o['apertures']=results
  o['gate_ap0_detection_5pct']=bool(ap0['detection_recovery']['0.05']>=.90)
  o['gate_ap1_detection_5pct']=bool(ap1['detection_recovery']['0.05']>=.80)
  o['gate_ap0_evolution_0p20']=bool(ap0['phase_shift_0p20_recovery'] is not None and ap0['phase_shift_0p20_recovery']>=.80)
  o['gate_passed']=bool(o['gate_ap0_detection_5pct'] and o['gate_ap1_detection_5pct'] and o['gate_ap0_evolution_0p20'])
  o['decision']='PREFLUX_GATE_PASSED_FLUX_OPENING_PERMITTED' if o['gate_passed'] else 'PREFLUX_GATE_FAILED_KEEP_FLUX_SEALED'
  o['success']=True
 except Exception as e:
  o['error']=type(e).__name__+': '+str(e); o['decision']='INFRASTRUCTURE_FAILURE_NO_SCIENCE_DECISION'
 OUT.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n'); print(json.dumps(o,indent=2,sort_keys=True))
if __name__=='__main__': main()
