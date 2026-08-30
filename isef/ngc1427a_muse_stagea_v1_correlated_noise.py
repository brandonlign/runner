#!/usr/bin/env python3
"""Prospective Stage-A v1 on untouched NGC1427A tiles.

Implements research freeze f1d464cde039a2483695b46c9c0627744d34fe89.
The v0 failure remains failed. V1 changes only the map-level noise model to the
literature-justified empirical 3-sigma-clipped effective RMS used in published
MUSE work. It emits no real [O III] candidate information.
"""
import json, math, urllib.parse, urllib.request, time
from pathlib import Path
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from scipy.ndimage import convolve, maximum_filter

FREEZE='f1d464cde039a2483695b46c9c0627744d34fe89'
DP='ADP.2026-06-24T16:04:14.194'; ID='ivo://eso.org/ID?'+DP
SODA='https://dataportal.eso.org/dataPortal/soda/sync'
OUT=Path('results/ngc1427a_muse_stagea_v1_correlated_noise.json'); OUT.parent.mkdir(exist_ok=True)
C=299792.458; VSYS=2036.; DOP=math.sqrt((1+VSYS/C)/(1-VSYS/C)); LAM=5006.843*DOP
MAGS=[25.5,26.,26.5,27.,27.5,28.,28.5,29.]
FWHM_A=2.6; FWHM_ARC=.8; PIX_ARC=.2; SIGPIX=(FWHM_ARC/2.354820045)/PIX_ARC; RAD=6/3600
w=WCS(naxis=2); w.wcs.crpix=[367.59362211212,305.46016102962]; w.wcs.crval=[55.045646972206,-35.618826927816]; w.wcs.ctype=['RA---TAN','DEC--TAN']; w.wcs.cd=np.array([[-5.5555555555556e-05,0],[0,5.5555555555556e-05]])
GRID=[.08,.35,.65,.92]; XY=[(x*735,y*610) for y in GRID for x in GRID]; CENTERS=w.all_pix2world(np.array(XY),0)

def psf():
 r=int(math.ceil(4*SIGPIX)); y,x=np.mgrid[-r:r+1,-r:r+1]; p=np.exp(-(x*x+y*y)/(2*SIGPIX**2)); p/=p.sum(); return p
P=psf(); P2SUM=float(np.sum(P*P)); PR=P.shape[0]//2

def get_tile(i,ra,dec):
 lo=(LAM-120)*1e-10; hi=(LAM+120)*1e-10; q={'ID':ID,'CIRCLE':f'{ra:.10f} {dec:.10f} {RAD}','BAND':f'{lo:.12e} {hi:.12e}'}; url=SODA+'?'+urllib.parse.urlencode(q); last=None
 for a in range(5):
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'ISEF-NGC1427A-StageA-v1/1.0'})
   with urllib.request.urlopen(req,timeout=300) as r: raw=r.read(20_000_000)
   if len(raw)>=20_000_000: raise RuntimeError('cutout unexpectedly >=20 MB')
   p=Path(f'/tmp/ngc1427a_v1_{i}.fits'); p.write_bytes(raw); return p,len(raw)
  except Exception as e: last=e; time.sleep(2**a)
 raise last

def wave(h,n):
 step=float(h.get('CD3_3',h.get('CDELT3'))); return float(h['CRVAL3'])+(np.arange(n)+1-float(h['CRPIX3']))*step

def line_map(data,var,wl,center):
 line=np.abs(wl-center)<=12.5; side=((wl>=center-40)&(wl<=center-25))|((wl>=center+25)&(wl<=center+40))
 if line.sum()<5 or side.sum()<8: raise RuntimeError('window outside SODA cube')
 vv=var[side]; yy=data[side]; g=np.isfinite(vv)&(vv>0)&np.isfinite(yy); wt=np.where(g,1/vv,0.); sw=wt.sum(0)
 cont=np.divide((np.where(g,yy,0)*wt).sum(0),sw,out=np.full(sw.shape,np.nan),where=sw>0)
 vc=np.divide(1.,sw,out=np.full(sw.shape,np.inf),where=sw>0)
 x=wl[line]; q=np.exp(-.5*((x-center)/(FWHM_A/2.354820045))**2); q=q/(q.sum()*np.median(np.diff(x)))
 yl=data[line]-cont[None]; vl=var[line]; gg=np.isfinite(yl)&np.isfinite(vl)&(vl>0); iv=np.where(gg,1/vl,0.); qq=q[:,None,None]
 den=(qq*qq*iv).sum(0); num=(qq*np.where(gg,yl,0)*iv).sum(0); amp=np.divide(num,den,out=np.full(den.shape,np.nan),where=den>0)
 coeff=np.divide((qq*iv).sum(0),den,out=np.zeros(den.shape),where=den>0); cterm=np.zeros(vc.shape); ok=np.isfinite(vc)&np.isfinite(coeff); np.multiply(vc,coeff*coeff,out=cterm,where=ok); cterm[(~np.isfinite(vc))&(np.abs(coeff)>0)]=np.inf
 va=np.divide(1.,den,out=np.full(den.shape,np.inf),where=den>0)+cterm
 return amp,va

def filtered(img): return convolve(np.where(np.isfinite(img),img,0.),P,mode='constant',cval=0.)/P2SUM

def filtered_diag_var(var):
 good=np.isfinite(var)&(var>0); x=np.where(good,var,0.); return convolve(x,P*P,mode='constant',cval=0.)/(P2SUM*P2SUM)

def robust_noise(a,mask):
 x=np.asarray(a[mask],float); x=x[np.isfinite(x)]
 if len(x)<100: raise RuntimeError('too few valid pixels for empirical noise')
 med=float(np.median(x)); sig=float(1.4826*np.median(np.abs(x-med)))
 for _ in range(10):
  if not np.isfinite(sig) or sig<=0: raise RuntimeError('invalid empirical sigma')
  y=x[np.abs(x-med)<=3*sig]
  nmed=float(np.median(y)); nsig=float(1.4826*np.median(np.abs(y-nmed)))
  if len(y)==len(x) and abs(nmed-med)<=1e-6*sig and abs(nsig-sig)<=1e-6*sig: med,sig=nmed,nsig; break
  x=y; med,sig=nmed,nsig
 return med,sig

def snr_emp(img,var,support):
 f=filtered(img); med,sig=robust_noise(f,support); s=(f-med)/sig
 dv=filtered_diag_var(var); pred=np.sqrt(dv[support]); pred=pred[np.isfinite(pred)&(pred>0)]; pr=float(np.median(pred)) if len(pred) else None
 ratio=float(sig/pr) if pr and pr>0 else None
 pos=float(np.mean(s[support]>=5)); neg=float(np.mean(s[support]<=-5)); return s,{'median':med,'sigma_eff':sig,'diag_pred_rms_median':pr,'sigma_ratio_to_diag':ratio,'positive_tail_ge5_fraction':pos,'negative_tail_leminus5_fraction':neg,'tail_symmetric':bool(abs(pos-neg)<=.001 or (np.sum(s[support]>=5)<3 and np.sum(s[support]<=-5)<3))}

def peaks(s,support):
 z=np.where(np.isfinite(s),s,-np.inf); mx=maximum_filter(z,size=3,mode='constant',cval=-np.inf); return support&(z>=5)&(z==mx)

def positions(seed,valid,n=25):
 rng=np.random.default_rng(seed); ys,xs=np.where(valid)
 if len(xs)<n: raise RuntimeError('too few injection pixels')
 jj=rng.choice(len(xs),n,replace=False); return [(int(xs[j]),int(ys[j])) for j in jj]

def inject(base,x,y,A):
 z=base.copy(); r=PR; z[y-r:y+r+1,x-r:x+r+1]+=A*P; return z

def wilson(k,n,z=1.):
 p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d; return [c-h,c+h]

def main():
 o={'status':'STAGEA_V1_CORRELATED_NOISE','freeze':FREEZE,'success':False,'decision':'NO_DECISION','real_candidate_outputs_emitted':False,'real_oiii_peak_count_emitted':False,'planned_oiii_A':LAM,'tiles':[]}
 try:
  total_area=0.; null_total=0; sigmas=[]; pathological=False
  for ti,(ra,dec) in enumerate(CENTERS):
   p,nbytes=get_tile(ti,ra,dec)
   try:
    with fits.open(p,memmap=False) as h: data=np.asarray(h['DATA'].data,float); var=np.asarray(h['STAT'].data,float); hdr=h['DATA'].header; sh=h['STAT'].header
   finally: p.unlink(missing_ok=True)
   if '10**(-40)' not in str(sh.get('BUNIT','')): raise RuntimeError('STAT units not variance')
   wl=wave(hdr,data.shape[0]); base,bv=line_map(data,var,wl,LAM); valid=np.isfinite(base)&np.isfinite(bv)&(bv>0); support=convolve(valid.astype(float),np.ones(P.shape),mode='constant',cval=0)==P.size
   area=float(support.sum()*PIX_ARC**2); total_area+=area
   # Internal target map used only to define empirical noise for injection detection; no real target peaks/counts are emitted.
   _, target_noise=snr_emp(base,bv,support); sigmas.append(target_noise['sigma_eff'])
   rec={}; yy,xx=np.ogrid[:base.shape[0],:base.shape[1]]; rr=(FWHM_ARC/PIX_ARC)**2
   for mi,m in enumerate(MAGS):
    A=10**(-.4*(m+13.74))/1e-20; hit=tot=0
    for rep in range(4):
     for x,y in positions(27142000+1000*ti+10*mi+rep,support,25):
      sm,_=snr_emp(inject(base,x,y,A),bv,support); pk=peaks(sm,support); hit+=int(np.any(pk&((xx-x)**2+(yy-y)**2<=rr))); tot+=1
    rec[str(m)]={'recovered':hit,'injected':tot,'fraction':hit/tot,'wilson_68':wilson(hit,tot)}
   nc=[]; ndiag=[]
   for c0 in [LAM-75,LAM+75]:
    im,iv=line_map(data,var,wl,c0); sm,diag=snr_emp(im,iv,support); cnt=int(peaks(sm,support).sum()); null_total+=cnt; nc.append(cnt); ndiag.append(diag); pathological |= not diag['tail_symmetric']
   o['tiles'].append({'tile_index':ti,'cutout_bytes':nbytes,'shape':list(data.shape),'usable_area_arcsec2':area,'recovery':rec,'offline_null_peak_counts':nc,'offline_null_noise_diagnostics':ndiag,'target_noise_aggregate_only':target_noise})
  sample_false=.5*null_total; mosaic=736*611*PIX_ARC**2; full_false=sample_false/total_area*mosaic
  a27=sum(t['usable_area_arcsec2'] for t in o['tiles'] if t['recovery']['27.0']['fraction']>=.90); a275=sum(t['usable_area_arcsec2'] for t in o['tiles'] if t['recovery']['27.5']['fraction']>=.50)
  medsig=float(np.median(sigmas)); sigma_regime_ok=all(.5*medsig<=x<=10*medsig for x in sigmas)
  o.update({'aggregate_offline_null_peaks':null_total,'sampled_expected_false_scaled':sample_false,'usable_sampled_area_arcsec2':total_area,'conservative_full_mosaic_expected_false':full_false,'area_fraction_passing_27':a27/total_area,'area_fraction_passing_27p5':a275/total_area,'gate_recovery_27':a27/total_area>=.5,'gate_recovery_27p5':a275/total_area>=.5,'gate_false_positive_full_mosaic':full_false<=1.,'gate_noise_tail_sanity':not pathological,'gate_sigma_regime_sanity':sigma_regime_ok})
  o['gate_passed']=bool(o['gate_recovery_27'] and o['gate_recovery_27p5'] and o['gate_false_positive_full_mosaic'] and o['gate_noise_tail_sanity'] and o['gate_sigma_regime_sanity'])
  o['decision']='STAGEA_V1_PASSED' if o['gate_passed'] else 'STAGEA_V1_FAILED_KILL_DIRECTION'; o['success']=True
 except Exception as e: o['error']=type(e).__name__+': '+str(e); o['decision']='INFRASTRUCTURE_FAILURE_NO_SCIENTIFIC_DECISION'
 OUT.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n'); print(json.dumps(o,indent=2,sort_keys=True))
if __name__=='__main__': main()
