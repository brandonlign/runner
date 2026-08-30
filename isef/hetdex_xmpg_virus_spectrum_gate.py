#!/usr/bin/env python3
"""Frozen HPSC1 native-VIRUS lambda4363 positive-control gate.
Reads only five externally specified pre-2020 controls from HPSC1 spectra.
Never accesses HPSC2. Scientific parameters are fixed; HPSC1 mirror is transport-only.
"""
from pathlib import Path
import json, math, os
import numpy as np
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
from scipy.special import ndtr, ndtri
OUT=Path(os.environ.get('HETDEX_GATE_OUT','results/hetdex_xmpg_virus_spectrum_gate.json'));OUT.parent.mkdir(parents=True,exist_ok=True)
URL=os.environ.get('HETDEX_HPSC1_SPEC_URL','https://web.corral.tacc.utexas.edu/hetdex/HETDEX/catalogs/hetdex_source_catalog_1/hetdex_sc1_spec_v3.2.fits')
CONTROLS=[('O3ELG2',8.2826,-0.1793),('O3ELG4a',9.8204,-0.0121),('O3ELG9',203.8739,51.0155),('O3ELG11',176.0732,51.1047),('O3ELG15',212.7970,51.2664)]
TARGET=4363.21;PSEUDO=[4323.21,4343.21,4383.21,4403.21];OFFSETS=np.arange(-3.0,3.01,1.0);SIGMA=2.5

def corrected_sigma(snr):
 p=max(1e-300,1.0-float(ndtr(snr)));pc=min(1.0,7.0*p)
 return float(ndtri(max(1e-12,1.0-pc)))
def one_obs(wave,flux,err,z,rest,offset):
 cen=rest*(1.0+z)+offset;finite=np.isfinite(wave)&np.isfinite(flux)&np.isfinite(err)&(err>0)
 if finite.sum()==0 or not np.isfinite(cen) or cen<wave[finite].min()+30 or cen>wave[finite].max()-30:return None
 dx=wave-cen;side=finite&(np.abs(dx)>=8)&(np.abs(dx)<=24);core=finite&(np.abs(dx)<=8)
 if side.sum()<10 or core.sum()<5:return None
 X=np.column_stack([np.ones(side.sum()),wave[side]-cen]);ww=1.0/err[side]**2
 try: cov=np.linalg.inv(X.T@(ww[:,None]*X));beta=cov@(X.T@(ww*flux[side]))
 except np.linalg.LinAlgError:return None
 y=flux[core]-(beta[0]+beta[1]*(wave[core]-cen));e=err[core];t=np.exp(-0.5*((wave[core]-cen)/SIGMA)**2);wt=1.0/e**2;den=np.sum(wt*t*t)
 if not np.isfinite(den) or den<=0:return None
 amp=float(np.sum(wt*t*y)/den);ae=float(den**-0.5);fac=math.sqrt(2*math.pi)*SIGMA
 return {'flux':amp*fac,'flux_err':ae*fac,'snr':amp/ae,'center':cen}
def combine_for_rest(rows,wave,spec,specerr,rest):
 by=[]
 for off in OFFSETS:
  ms=[]
  for idx,z in rows:
   m=one_obs(wave,np.asarray(spec[idx],float),np.asarray(specerr[idx],float),z,rest,float(off))
   if m is not None:ms.append(m)
  if not ms:continue
  w=np.array([1/m['flux_err']**2 for m in ms]);f=np.array([m['flux'] for m in ms]);fc=float(np.sum(w*f)/np.sum(w));ec=float(np.sum(w)**-0.5)
  by.append({'offset_A':float(off),'combined_flux':fc,'combined_flux_err':ec,'snr':fc/ec,'valid_observations':len(ms)})
 if not by:return {'technically_testable':False}
 best=max(by,key=lambda x:x['snr']);cs=corrected_sigma(best['snr'])
 return {'technically_testable':True,'best':best,'corrected_sigma':cs,'recovered':bool(cs>=3.0 and best['combined_flux']>0),'all_offsets':by}
def main():
 out={'success':False,'status':'FROZEN_HPSC1_CONTROL_GATE','hpsc2_opened':False,'transport_url':URL,'controls':[],'freeze':{'target_rest_A':TARGET,'pseudo_rest_A':PSEUDO,'centroid_offsets_A':OFFSETS.tolist(),'gaussian_sigma_A':SIGMA,'corrected_sigma_threshold':3.0}}
 try:
  with fits.open(URL,use_fsspec=True,fsspec_kwargs={'block_size':4*1024*1024,'cache_type':'readahead'},memmap=False,lazy_load_hdus=True) as h:
   info=h['INFO'].data;ra=np.asarray(info['RA'],float);dec=np.asarray(info['DEC'],float);z=np.asarray(info['z_hetdex'],float);coords=SkyCoord(ra*u.deg,dec*u.deg);wave=np.asarray(h['WAVELENGTH'].data,float);spec=h['SPEC'].data;specerr=h['SPEC_ERR'].data
   for label,cra,cdec in CONTROLS:
    sep=coords.separation(SkyCoord(cra*u.deg,cdec*u.deg)).arcsec;idxs=np.where(sep<=3.0)[0];rows=[(int(i),float(z[i])) for i in idxs if np.isfinite(z[i])]
    rec={'label':label,'matched_source_observations':len(rows),'nearest_sep_arcsec':float(np.min(sep)),'lambda4363':combine_for_rest(rows,wave,spec,specerr,TARGET),'pseudo_lines':{str(r):combine_for_rest(rows,wave,spec,specerr,r) for r in PSEUDO}};out['controls'].append(rec)
  test=[r for r in out['controls'] if r['lambda4363']['technically_testable']];rec=[r for r in test if r['lambda4363']['recovered']];ps=[p for r in out['controls'] for p in r['pseudo_lines'].values() if p.get('technically_testable')];pr=[p for p in ps if p.get('recovered')];counts=[]
  for r in out['controls']:
   q=[p for p in r['pseudo_lines'].values() if p.get('technically_testable')]
   if q:counts.append(sum(p.get('recovered',False) for p in q))
  out.update({'technically_testable_controls':len(test),'recovered_controls':len(rec),'recovery_fraction':len(rec)/len(test) if test else None,'valid_pseudo_tests':len(ps),'pseudo_recoveries':len(pr),'pseudo_recovery_fraction':len(pr)/len(ps) if ps else None,'median_pseudo_recoveries_per_control':float(np.median(counts)) if counts else None})
  cond={'at_least_4_testable':len(test)>=4,'control_recovery_ge_075':len(test)>=4 and len(rec)/len(test)>=0.75,'pseudo_median_le_05':bool(counts and np.median(counts)<=0.5),'pseudo_fraction_le_025':bool(ps and len(pr)/len(ps)<=0.25)};out['gate_conditions']=cond;out['decision']='VIRUS_SPECTRUM_GATE_PASSED' if all(cond.values()) else 'VIRUS_SPECTRUM_GATE_FAILED';out['success']=True
 except Exception as e:out['error']=f'{type(e).__name__}: {e}';out['decision']='INFRASTRUCTURE_FAILURE_NO_SCIENTIFIC_DECISION'
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
