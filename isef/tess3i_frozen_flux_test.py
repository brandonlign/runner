#!/usr/bin/env python3
"""Execute the preregistered TESS Sector 1751 3I/ATLAS flux test.

This is the first authorized script to read FLUX_CORR. It follows
research/TESS3I_COHERENCE_PROTOCOL_V0.md (commit 161c881d...).
"""
import json, math, urllib.request
from pathlib import Path
import numpy as np
from astropy.io import fits

REC='https://zenodo.org/api/records/19376249'
OUT=Path('results/tess3i_frozen_flux_test.json'); OUT.parent.mkdir(exist_ok=True)
P0_H=7.136; P1_H=7.20; GAP=.10; MINSPAN=1.25*(P0_H/24.); BOOT=2000
RNG=np.random.default_rng(3171362026)

def medmad(x):
 x=np.asarray(x,float); z=x[np.isfinite(x)]
 if not len(z): return np.nan,np.nan
 m=float(np.median(z)); return m,float(1.4826*np.median(np.abs(z-m)))

def wrapcyc(x): return float((x+0.5)%1.0-0.5)

def segment_times(t):
 order=np.argsort(t); ts=t[order]; ids=np.zeros(len(ts),int); s=0
 for i in range(1,len(ts)):
  if ts[i]-ts[i-1] > GAP: s+=1
  ids[i]=s
 back=np.empty_like(ids); back[order]=ids
 return back

def model_matrix(t,seg,period_h,mode,evo_ids=None):
 p=period_h/24.; w=2*np.pi/p; cols=[]; names=[]; use=np.unique(seg)
 for s in use:
  z=(seg==s).astype(float); c=float(np.median(t[seg==s])); cols += [z,z*(t-c)]; names += [f'i_{s}',f'slope_{s}']
 if mode=='none': pass
 elif mode=='coherent': cols += [np.sin(w*t),np.cos(w*t)]; names += ['sin_common','cos_common']
 elif mode=='evolving':
  # Common sinusoid applies to short fragments. Eligible segments add deltas,
  # yielding their own A_s/B_s while preserving the frozen common term elsewhere.
  cols += [np.sin(w*t),np.cos(w*t)]; names += ['sin_common','cos_common']
  for s in (evo_ids or []):
   z=(seg==s).astype(float); cols += [z*np.sin(w*t),z*np.cos(w*t)]; names += [f'sin_delta_{s}',f'cos_delta_{s}']
 else: raise ValueError(mode)
 return np.column_stack(cols),names

def fit(y,e,t,seg,period_h,mode,evo_ids=None):
 X,names=model_matrix(t,seg,period_h,mode,evo_ids); sw=1/np.maximum(e,1e-12); Xw=X*sw[:,None]; yw=y*sw
 b=np.linalg.lstsq(Xw,yw,rcond=None)[0]; pred=X@b; r=(y-pred)/e; chi=float(r@r); k=len(b); n=len(y); bic=chi+k*np.log(n)
 return {'bic':bic,'chi2':chi,'k':k,'beta':b,'pred':pred,'resid':y-pred,'names':names,'X':X}

def coeff(fitres,name): return float(fitres['beta'][fitres['names'].index(name)])

def segment_phase_amp(fr,evo_ids):
 a=coeff(fr,'sin_common'); b=coeff(fr,'cos_common'); out={}
 for s in evo_ids:
  aa=a+coeff(fr,f'sin_delta_{s}'); bb=b+coeff(fr,f'cos_delta_{s}'); out[int(s)]={'amplitude':float(np.hypot(aa,bb)),'phase_cycles':float((np.arctan2(bb,aa)/(2*np.pi))%1.0)}
 return out

def block_resample_standardized(t,seg,stdres,block_hours=2.0):
 out=np.empty(len(stdres),float)
 for s in np.unique(seg):
  idx=np.flatnonzero(seg==s); order=idx[np.argsort(t[idx])]; n=len(order)
  if n<=1: out[order]=stdres[order]; continue
  dt=np.median(np.diff(t[order]))*24.; L=max(1,int(round(block_hours/max(dt,1e-6)))); vals=stdres[order]; take=[]
  while len(take)<n:
   start=int(RNG.integers(0,max(1,n-L+1))); take.extend(vals[start:min(n,start+L)].tolist())
  out[order]=np.asarray(take[:n])
 return out

def diagnostic_bic(t,y,quality_mask,period_h=P0_H):
 m=quality_mask&np.isfinite(t)&np.isfinite(y)
 tt=t[m]; yy=y[m]
 if len(tt)<25: return None
 med,rs=medmad(yy)
 if not np.isfinite(rs) or rs<=0: return {'n':int(len(tt)),'delta_bic_detection':None,'reason':'constant_or_invalid'}
 yy=(yy-med)/rs; ee=np.ones(len(yy)); sg=segment_times(tt)
 a=fit(yy,ee,tt,sg,period_h,'none'); b=fit(yy,ee,tt,sg,period_h,'coherent')
 return {'n':int(len(tt)),'delta_bic_detection':float(a['bic']-b['bic'])}

def clean_ap(d,extra):
 t=np.asarray(d['TIME'],float); y=np.asarray(d['FLUX_CORR'],float); er=np.asarray(d['FLUX_ERR_CORR'],float); q=np.asarray(d['QUALITY'],int); aq=np.asarray(d['AP_QUALITY'],int)
 bmad=np.asarray(d['BKG_MAD'],float); bstd=np.asarray(d['BKG_STD'],float); c1=np.asarray(d['MOM_CENTR1'],float); c2=np.asarray(d['MOM_CENTR2'],float); nstar=np.asarray(extra['NPIX_BKGSTAR_CORE'],float)
 base=np.isfinite(t)&np.isfinite(y)&np.isfinite(er)&(er>0)&np.isfinite(bmad)&np.isfinite(bstd)&np.isfinite(c1)&np.isfinite(c2)&(q==0)&(aq==0)&(nstar==0)
 mb,sd=medmad(bmad[base]); bgok=bmad<=mb+5*sd if np.isfinite(sd) else np.ones(len(t),bool)
 mc1=float(np.median(c1[base])); mc2=float(np.median(c2[base])); disp=np.hypot(c1-mc1,c2-mc2); md,ds=medmad(disp[base]); cok=disp<=md+5*ds if np.isfinite(ds) else np.ones(len(t),bool)
 clean=base&bgok&cok
 return {'tall':t,'yall':y,'eall':er,'q':q,'aq':aq,'bmad':bmad,'bstd':bstd,'disp':disp,'nstar':nstar,'mask':clean,'t':t[clean],'y':y[clean],'e':er[clean]}

def analyze_ap(c,period_h,boot=False):
 t,y,e=c['t'],c['y'],c['e']; seg=segment_times(t); evo=[]; seginfo=[]
 for s in np.unique(seg):
  x=t[seg==s]; span=float(x.max()-x.min()); elig=span>=MINSPAN and len(x)>=25
  if elig: evo.append(int(s))
  seginfo.append({'id':int(s),'n':int(len(x)),'span_hours':span*24,'evolution_eligible':bool(elig),'start_btjd':float(x.min()),'stop_btjd':float(x.max())})
 fnone=fit(y,e,t,seg,period_h,'none'); f0=fit(y,e,t,seg,period_h,'coherent'); f1=fit(y,e,t,seg,period_h,'evolving',evo)
 det=float(fnone['bic']-f0['bic']); db=float(f0['bic']-f1['bic']); phases=segment_phase_amp(f1,evo)
 out={'n':int(len(t)),'segments':seginfo,'evolution_eligible_ids':evo,'delta_bic_detection':det,'delta_bic_evolution':db,'coherent_amplitude':float(np.hypot(coeff(f0,'sin_common'),coeff(f0,'cos_common'))),'coherent_phase_cycles':float((np.arctan2(coeff(f0,'cos_common'),coeff(f0,'sin_common'))/(2*np.pi))%1.0),'evolving_segment_fits':phases}
 if len(evo)>=2:
  es=sorted(evo,key=lambda s:np.median(t[seg==s])); dphi=wrapcyc(phases[es[-1]]['phase_cycles']-phases[es[0]]['phase_cycles']); out['phase_difference_late_minus_early_cycles']=dphi; out['phase_difference_hours']=dphi*period_h
  if boot:
   stdres=f1['resid']/e; draws=[]
   for _ in range(BOOT):
    zr=block_resample_standardized(t,seg,stdres,2.0); yb=f1['pred']+zr*e; fb=fit(yb,e,t,seg,period_h,'evolving',evo); ph=segment_phase_amp(fb,evo); draws.append(wrapcyc(ph[es[-1]]['phase_cycles']-ph[es[0]]['phase_cycles']))
   arr=np.asarray(draws); # unwrap around observed phase difference
   arr=dphi+((arr-dphi+0.5)%1.0-0.5)
   out['phase_difference_bootstrap_99pct_cycles']=[float(np.quantile(arr,.005)),float(np.quantile(arr,.995))]; out['bootstrap_draws']=BOOT; out['phase_difference_99pct_excludes_zero']=bool(np.quantile(arr,.005)>0 or np.quantile(arr,.995)<0)
 return out

def main():
 o={'status':'FROZEN_TESS3I_FLUX_TEST','protocol_commit':'161c881dc8cbe10aaafa96216d1712b877ff3c39','preflux_gate_commit':'e6fe661cda6589a2b94a057b8034970b39338858','flux_opened':True,'success':False}
 try:
  with urllib.request.urlopen(urllib.request.Request(REC,headers={'User-Agent':'ISEF-TESS3I-FrozenFlux/1.0'}),timeout=120) as r: meta=json.load(r)
  fs=[f for f in meta.get('files',[]) if f.get('key','').startswith('hlsp_tess-3i_tess_ffi_') and f.get('key','').endswith('_lc.fits')]
  if len(fs)!=1: raise RuntimeError(f'expected one 200s LC, found {len(fs)}')
  f=fs[0]; url=f.get('links',{}).get('content') or f.get('links',{}).get('self'); p=Path('/tmp')/f['key']
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ISEF-TESS3I-FrozenFlux/1.0'}),timeout=180) as r, open(p,'wb') as w:
   while True:
    b=r.read(1<<20)
    if not b: break
    w.write(b)
  with fits.open(p,memmap=True) as h:
   extra=h['EXTRAS'].data; c0=clean_ap(h['LIGHTCURVE_AP0'].data,extra); c1=clean_ap(h['LIGHTCURVE_AP1'].data,extra)
   a0=analyze_ap(c0,P0_H,boot=True); a1=analyze_ap(c1,P0_H,boot=True)
   # Fixed P1 sensitivity; no bootstrap needed for the prespecified secondary period.
   p1a0=analyze_ap(c0,P1_H,boot=False); p1a1=analyze_ap(c1,P1_H,boot=False)
   # Instrumental diagnostic P0 tests. Use quality/AP-quality base but deliberately do not impose the NPIX_BKGSTAR cut on that diagnostic itself.
   d0=h['LIGHTCURVE_AP0'].data; tall=np.asarray(d0['TIME'],float); q0=(np.asarray(d0['QUALITY'],int)==0)&(np.asarray(d0['AP_QUALITY'],int)==0)
   diagnostics={
    'BKG_MAD':diagnostic_bic(tall,np.asarray(d0['BKG_MAD'],float),q0),
    'BKG_STD':diagnostic_bic(tall,np.asarray(d0['BKG_STD'],float),q0),
    'CENTROID_DISPLACEMENT':diagnostic_bic(tall,c0['disp'],q0),
    'NPIX_BKGSTAR_CORE':diagnostic_bic(tall,np.asarray(extra['NPIX_BKGSTAR_CORE'],float),q0),
   }
  det0=a0['delta_bic_detection']>=10; det1=a1['delta_bic_detection']>=6
  evolution=False; phase_consistent=False
  if det0 and det1 and a0['delta_bic_evolution']>=10 and a1['delta_bic_evolution']>=6 and 'phase_difference_late_minus_early_cycles' in a0 and 'phase_difference_late_minus_early_cycles' in a1:
   x=a0['phase_difference_late_minus_early_cycles']; y=a1['phase_difference_late_minus_early_cycles']; phase_consistent=bool((x>0 and y>0) or (x<0 and y<0)); evolution=phase_consistent
  o['primary_P0_hours']=P0_H; o['AP0_small_core']=a0; o['AP1_large_core']=a1; o['P1_7p20h_sensitivity']={'AP0':p1a0,'AP1':p1a1}; o['instrumental_diagnostics_P0']=diagnostics
  o['gate_P0_detected_AP0']=bool(det0); o['gate_P0_detected_AP1']=bool(det1); o['P0_detection_gate_passed']=bool(det0 and det1); o['phase_direction_consistent_AP0_AP1']=phase_consistent; o['strong_evolution_evidence']=evolution
  if not (det0 and det1): o['decision']='TESS_DOES_NOT_ROBUSTLY_DETECT_EXTERNAL_7P136H_MODULATION'
  elif evolution: o['decision']='P0_DETECTED_STRONG_EVOLUTION_EVIDENCE'
  else: o['decision']='P0_DETECTED_COHERENT_OR_INCONCLUSIVE_EVOLUTION'
  o['success']=True
 except Exception as e:
  o['error']=type(e).__name__+': '+str(e); o['decision']='INFRASTRUCTURE_FAILURE_NO_SCIENTIFIC_DECISION'
 OUT.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n'); print(json.dumps(o,indent=2,sort_keys=True))
if __name__=='__main__': main()
