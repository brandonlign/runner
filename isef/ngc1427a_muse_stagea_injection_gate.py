#!/usr/bin/env python3
"""Frozen Stage-A injection/recovery + off-line null gate for NGC1427A.

This program follows isef research freezes a468846f..., 411c8f..., 813c599a...
and infrastructure correction 16e222b3.... It may read target pixels internally
only to evaluate synthetic injections and aggregate off-line nulls. It never
emits coordinates, fluxes, S/N, counts, or spectra of non-injected sources in
the real [O III] window.
"""
import json, math, urllib.parse, urllib.request, time
from pathlib import Path
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from scipy.ndimage import convolve, maximum_filter

DP='ADP.2026-06-24T16:04:14.194'; ID='ivo://eso.org/ID?'+DP
SODA='https://dataportal.eso.org/dataPortal/soda/sync'
OUT=Path('results/ngc1427a_muse_stagea_injection_gate.json');OUT.parent.mkdir(exist_ok=True)
C=299792.458; VSYS=2036.; BETA=VSYS/C; DOP=math.sqrt((1+BETA)/(1-BETA))
LAM=5006.843*DOP
MAGS=[25.5,26.,26.5,27.,27.5,28.,28.5,29.]
FWHM_A=2.6; FWHM_ARC=0.8; PIX_ARC=0.2; SIGPIX=(FWHM_ARC/2.354820045)/PIX_ARC
RAD=8/3600
w=WCS(naxis=2); w.wcs.crpix=[367.59362211212,305.46016102962];w.wcs.crval=[55.045646972206,-35.618826927816];w.wcs.ctype=['RA---TAN','DEC--TAN'];w.wcs.cd=np.array([[-5.5555555555556e-05,0],[0,5.5555555555556e-05]])
XY=[(.20*735,.20*610),(.50*735,.20*610),(.80*735,.20*610),(.20*735,.50*610),(.50*735,.50*610),(.80*735,.50*610),(.20*735,.80*610),(.50*735,.80*610),(.80*735,.80*610)]
CENTERS=w.all_pix2world(np.array(XY),0)

def psf_kernel():
 r=int(math.ceil(4*SIGPIX)); y,x=np.mgrid[-r:r+1,-r:r+1];p=np.exp(-(x*x+y*y)/(2*SIGPIX**2));p/=p.sum();return p
P=psf_kernel(); PR=P.shape[0]//2; P2=P*P

def download_tile(i,ra,dec):
 lo=(LAM-120)*1e-10;hi=(LAM+120)*1e-10
 params={'ID':ID,'CIRCLE':f'{ra:.10f} {dec:.10f} {RAD}','BAND':f'{lo:.12e} {hi:.12e}'}
 url=SODA+'?'+urllib.parse.urlencode(params); last=None
 for a in range(4):
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'ISEF-NGC1427A-StageA/1.1'})
   with urllib.request.urlopen(req,timeout=300) as r: raw=r.read(20_000_000)
   if len(raw)>=20_000_000: raise RuntimeError('cutout unexpectedly >=20MB')
   p=Path(f'/tmp/ngc1427a_stagea_tile{i}.fits');p.write_bytes(raw);return p,len(raw),params
  except Exception as e:last=e;time.sleep(2**a)
 raise last

def wave_from(h,n):
 crval=float(h['CRVAL3']);crpix=float(h['CRPIX3']);step=float(h.get('CD3_3',h.get('CDELT3')))
 pix=np.arange(n)+1.;return crval+(pix-crpix)*step

def spec_map(data,var,wave,center):
 line=np.abs(wave-center)<=12.5
 side=((wave>=center-40)&(wave<=center-25))|((wave>=center+25)&(wave<=center+40))
 if line.sum()<5 or side.sum()<8: raise RuntimeError('spectral cutout/window mismatch')
 vv=var[side]; yy=data[side]; good=np.isfinite(vv)&(vv>0)&np.isfinite(yy)
 wt=np.where(good,1/vv,0.); sw=wt.sum(axis=0)
 c=np.divide((np.where(good,yy,0)*wt).sum(axis=0),sw,out=np.full(sw.shape,np.nan),where=sw>0)
 vc=np.divide(1.,sw,out=np.full(sw.shape,np.inf),where=sw>0)
 wl=wave[line]; q=np.exp(-.5*((wl-center)/(FWHM_A/2.354820045))**2);q=q/(q.sum()*np.median(np.diff(wl)))
 yl=data[line]-c[None,:,:]; vl=var[line]; gl=np.isfinite(yl)&np.isfinite(vl)&(vl>0)
 inv=np.where(gl,1/vl,0.); qq=q[:,None,None]
 den=(qq*qq*inv).sum(axis=0); num=(qq*np.where(gl,yl,0)*inv).sum(axis=0)
 amp=np.divide(num,den,out=np.full(den.shape,np.nan),where=den>0)
 coeff=np.divide((qq*inv).sum(axis=0),den,out=np.zeros(den.shape),where=den>0)
 cterm=np.zeros(vc.shape,float); ok=np.isfinite(vc)&np.isfinite(coeff)
 np.multiply(vc,coeff*coeff,out=cterm,where=ok)
 cterm[(~np.isfinite(vc))&(np.abs(coeff)>0)]=np.inf
 va=np.divide(1.,den,out=np.full(den.shape,np.inf),where=den>0)+cterm
 return amp,va

def spatial_snr(img,var):
 good=np.isfinite(img)&np.isfinite(var)&(var>0)
 iv=np.where(good,1/var,0.); y=np.where(good,img,0.)
 num=convolve(y*iv,P,mode='constant',cval=0.);den=convolve(iv,P2,mode='constant',cval=0.)
 return np.divide(num,np.sqrt(den),out=np.full(img.shape,np.nan),where=den>0),den

def local_peak_mask(snr):
 finite=np.isfinite(snr); z=np.where(finite,snr,-np.inf);mx=maximum_filter(z,size=3,mode='constant',cval=-np.inf)
 return finite&(z>=5.)&(z==mx)

def positions(seed,valid,n=25):
 # Infrastructure correction 16e222b3...: positions are individual, independent
 # injected-source trials, never simultaneous. Uniform without replacement.
 rng=np.random.default_rng(seed); ys,xs=np.where(valid)
 if len(xs)<n: raise RuntimeError(f'only {len(xs)} valid injection pixels')
 take=rng.choice(len(xs),size=n,replace=False)
 return [(int(xs[j]),int(ys[j])) for j in take]

def add_one(base,pos,amp):
 z=base.copy();r=PR;x,y=pos;z[y-r:y+r+1,x-r:x+r+1]+=amp*P;return z

def wilson(k,n,z=1.0):
 if n==0:return [None,None]
 p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d;return [c-h,c+h]

def main():
 o={'status':'FROZEN_STAGEA_INJECTION_GATE','success':False,'decision':'NO_DECISION','stagea_freeze':'a468846f91e726139bf84e3f14b7138558748db6','sideband_clarification':'411c8f242b677df730d32286f11a397806c0229e','null_clarification':'813c599ad1443bd18f6a007c4f2216b8e0ddc323','injection_execution_correction':'16e222b3fae86c1587824311ba86e7ddff65526d','real_candidate_outputs_emitted':False,'real_oiii_peak_count_emitted':False,'planned_oiii_A':LAM,'tile_results':[],'injection_domain':'spectrally compressed line-flux map; exact linear response to frozen 2.6-A spectral template before spatial matched filtering; each source trial injected separately'}
 try:
  null_total=0;usable_area_arc2=0.;mosaic_area=736*611*PIX_ARC**2
  for ti,(ra,dec) in enumerate(CENTERS):
   p,nbytes,params=download_tile(ti,ra,dec)
   try:
    with fits.open(p,memmap=False) as h:
     data=np.asarray(h['DATA'].data,dtype=np.float64);var=np.asarray(h['STAT'].data,dtype=np.float64);hdr=h['DATA'].header;shdr=h['STAT'].header
   finally:p.unlink(missing_ok=True)
   wave=wave_from(hdr,data.shape[0])
   if '10**(-20)' not in str(hdr.get('BUNIT','')): raise RuntimeError('unexpected DATA units')
   if '10**(-40)' not in str(shdr.get('BUNIT','')): raise RuntimeError('STAT is not squared DATA units')
   base,basev=spec_map(data,var,wave,LAM)
   valid=np.isfinite(base)&np.isfinite(basev)&(basev>0)
   support=convolve(valid.astype(float),np.ones(P.shape),mode='constant',cval=0)==P.size
   usable=int(support.sum()); usable_area_arc2+=usable*PIX_ARC**2
   recover={}; yygrid,xxgrid=np.ogrid[:base.shape[0],:base.shape[1]];rad=FWHM_ARC/PIX_ARC
   for mi,m in enumerate(MAGS):
    hit=0;tot=0;A=10**(-0.4*(m+13.74))/1e-20
    for rep in range(4):
     seed=14270000+1000*ti+10*mi+rep
     for x,y in positions(seed,support,25):
      inj=add_one(base,(x,y),A);snr,_=spatial_snr(inj,basev);pk=local_peak_mask(snr)
      near=pk&((xxgrid-x)**2+(yygrid-y)**2<=rad**2);hit+=int(np.any(near));tot+=1
    recover[str(m)]={'recovered':hit,'injected':tot,'fraction':hit/tot,'wilson_68':wilson(hit,tot)}
   null_counts=[]
   for nc in [LAM-75,LAM+75]:
    im,iv=spec_map(data,var,wave,nc);snr,_=spatial_snr(im,iv);pk=local_peak_mask(snr)&support;cnt=int(pk.sum());null_counts.append(cnt);null_total+=cnt
   o['tile_results'].append({'tile_index':ti,'cutout_bytes':nbytes,'shape':list(data.shape),'usable_pixels':usable,'usable_area_arcsec2':usable*PIX_ARC**2,'recovery':recover,'offline_null_peak_counts':null_counts})
  sample_false=null_total*.5; density=sample_false/usable_area_arc2 if usable_area_arc2>0 else float('inf');full_false=density*mosaic_area
  o['aggregate_offline_null_peaks']=null_total;o['sampled_expected_false_scaled']=sample_false;o['usable_sampled_area_arcsec2']=usable_area_arc2;o['full_mosaic_area_arcsec2']=mosaic_area;o['conservative_full_mosaic_expected_false']=full_false
  n27=sum(t['recovery']['27.0']['fraction']>=.90 for t in o['tile_results']);n275=sum(t['recovery']['27.5']['fraction']>=.50 for t in o['tile_results'])
  o['tiles_passing_27_recovery']=n27;o['tiles_passing_27p5_recovery']=n275
  o['gate_recovery_27']=n27>=5;o['gate_recovery_27p5']=n275>=5;o['gate_false_positive_full_mosaic']=full_false<=1.0;o['gate_spatial_coverage']=sum(t['usable_pixels']>0 for t in o['tile_results'])>=5
  o['gate_passed']=bool(o['gate_recovery_27'] and o['gate_recovery_27p5'] and o['gate_false_positive_full_mosaic'] and o['gate_spatial_coverage'])
  o['decision']='STAGEA_PASSED' if o['gate_passed'] else 'STAGEA_FAILED_DO_NOT_OPEN_REAL_CANDIDATES';o['success']=True
 except Exception as e:
  o['error']=type(e).__name__+': '+str(e);o['decision']='INFRASTRUCTURE_FAILURE_NO_SCIENTIFIC_DECISION'
 OUT.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,indent=2,sort_keys=True))
if __name__=='__main__':main()
