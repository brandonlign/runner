#!/usr/bin/env python3
"""Frozen HPSC1 native-VIRUS lambda4363 gate using exact FITS byte ranges.
Scientific method is identical to HETDEX_XMPG_SPECTRUM_CONTROL_FREEZE.md.
Only transport changes: download HPSC1 source index + required spectrum rows.
Never accesses HPSC2.
"""
from pathlib import Path
import io,json,math,urllib.request
import numpy as np
from astropy.table import Table
from astropy.coordinates import SkyCoord
import astropy.units as u
from scipy.special import ndtr,ndtri
OUT=Path('results/hetdex_xmpg_virus_range_gate.json');OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='https://zenodo.org/records/7448504/files/'
INDEX=BASE+'hetdex_sc1_v3.2.ecsv?download=1'
SPECURL=BASE+'hetdex_sc1_spec_v3.2.fits?download=1'
CONTROLS=[('O3ELG2',8.2826,-0.1793),('O3ELG4a',9.8204,-0.0121),('O3ELG9',203.8739,51.0155),('O3ELG11',176.0732,51.1047),('O3ELG15',212.7970,51.2664)]
TARGET=4363.21;PSEUDO=[4323.21,4343.21,4383.21,4403.21];OFFSETS=np.arange(-3.,3.01,1.);SIGMA=2.5
# Frozen HPSC1 v3.2 FITS layout from public documentation:
NROW=232650;NPIX=1036;INFO_ROWLEN=190;BLOCK=2880

def pad(n):return ((n+BLOCK-1)//BLOCK)*BLOCK
PRIMARY=BLOCK;INFO_HEADER=3*BLOCK;INFO_DATA=pad(INFO_ROWLEN*NROW)
SPEC_HEADER_START=PRIMARY+INFO_HEADER+INFO_DATA
SPEC_DATA_START=SPEC_HEADER_START+BLOCK
PLANE_BYTES=pad(NROW*NPIX*4)
SPECERR_HEADER_START=SPEC_DATA_START+PLANE_BYTES
SPECERR_DATA_START=SPECERR_HEADER_START+BLOCK
# SPEC_OBS, SPEC_OBS_ERR, APCOR follow, each float32 plane + one-block header.
WAVE_HEADER_START=SPECERR_DATA_START+PLANE_BYTES + (BLOCK+PLANE_BYTES)*3
WAVE_DATA_START=WAVE_HEADER_START+BLOCK

def get_range(url,start,n,timeout=120):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-HETDEX-XMPG-range/1.0','Range':f'bytes={start}-{start+n-1}'})
 with urllib.request.urlopen(req,timeout=timeout) as r:
  b=r.read(n);cr=r.headers.get('Content-Range');status=r.status
 if len(b)!=n:raise RuntimeError(f'range length {len(b)} != {n} at {start}; status={status} content-range={cr}')
 return b,cr

def header_cards(b):
 s=b.decode('ascii','replace');d={}
 for i in range(0,len(s),80):
  card=s[i:i+80];key=card[:8].strip()
  if key=='END':break
  if '=' in card[:12]:d[key]=card[10:30].strip().strip("'")
 return d

def corrected_sigma(snr):
 p=max(1e-300,1-float(ndtr(snr)));pc=min(1.,7*p);return float(ndtri(max(1e-12,1-pc)))
def one_obs(wave,flux,err,z,rest,off):
 cen=rest*(1+z)+off;finite=np.isfinite(wave)&np.isfinite(flux)&np.isfinite(err)&(err>0)
 if finite.sum()==0 or cen<wave[finite].min()+30 or cen>wave[finite].max()-30:return None
 dx=wave-cen;side=finite&(np.abs(dx)>=8)&(np.abs(dx)<=24);core=finite&(np.abs(dx)<=8)
 if side.sum()<10 or core.sum()<5:return None
 X=np.column_stack([np.ones(side.sum()),wave[side]-cen]);ww=err[side]**-2
 try:cov=np.linalg.inv(X.T@(ww[:,None]*X));beta=cov@(X.T@(ww*flux[side]))
 except np.linalg.LinAlgError:return None
 y=flux[core]-(beta[0]+beta[1]*(wave[core]-cen));e=err[core];t=np.exp(-.5*((wave[core]-cen)/SIGMA)**2);wt=e**-2;den=np.sum(wt*t*t)
 if not np.isfinite(den) or den<=0:return None
 amp=float(np.sum(wt*t*y)/den);ae=float(den**-.5);fac=math.sqrt(2*math.pi)*SIGMA
 return {'flux':amp*fac,'flux_err':ae*fac,'snr':amp/ae}
def combine(rows,wave,rest):
 vals=[]
 for off in OFFSETS:
  ms=[]
  for row in rows:
   m=one_obs(wave,row['spec'],row['err'],row['z'],rest,float(off))
   if m:ms.append(m)
  if not ms:continue
  w=np.array([m['flux_err']**-2 for m in ms]);f=np.array([m['flux'] for m in ms]);fc=float(np.sum(w*f)/w.sum());ec=float(w.sum()**-.5)
  vals.append({'offset_A':float(off),'combined_flux':fc,'combined_flux_err':ec,'snr':fc/ec,'valid_observations':len(ms)})
 if not vals:return {'technically_testable':False}
 best=max(vals,key=lambda x:x['snr']);cs=corrected_sigma(best['snr'])
 return {'technically_testable':True,'best':best,'corrected_sigma':cs,'recovered':bool(cs>=3 and best['combined_flux']>0),'all_offsets':vals}
def main():
 out={'success':False,'status':'FROZEN_HPSC1_CONTROL_GATE_RANGE_TRANSPORT','hpsc2_opened':False,'controls':[],'layout':{'spec_data_start':SPEC_DATA_START,'specerr_data_start':SPECERR_DATA_START,'wave_data_start':WAVE_DATA_START},'freeze':{'target_rest_A':TARGET,'pseudo_rest_A':PSEUDO,'offsets_A':OFFSETS.tolist(),'sigma_A':SIGMA,'threshold_corrected_sigma':3.0}}
 try:
  # Sanity-check computed FITS extension offsets before reading science rows.
  hs,_=get_range(SPECURL,SPEC_HEADER_START,BLOCK);he,_=get_range(SPECURL,SPECERR_HEADER_START,BLOCK);hw,_=get_range(SPECURL,WAVE_HEADER_START,BLOCK)
  out['header_sanity']={'spec':header_cards(hs),'spec_err':header_cards(he),'wavelength':header_cards(hw)}
  if out['header_sanity']['spec'].get('EXTNAME','').strip()!='SPEC' or out['header_sanity']['spec_err'].get('EXTNAME','').strip()!='SPEC_ERR' or out['header_sanity']['wavelength'].get('EXTNAME','').strip()!='WAVELENGTH':raise RuntimeError('computed FITS offsets failed EXTNAME sanity')
  wb,_=get_range(SPECURL,WAVE_DATA_START,NPIX*8);wave=np.frombuffer(wb,dtype='>f8').astype(float)
  # 62 MB index table only; row order is documented to match spectral arrays.
  req=urllib.request.Request(INDEX,headers={'User-Agent':'ISEF-HETDEX-XMPG-range/1.0'})
  with urllib.request.urlopen(req,timeout=180) as r:index_bytes=r.read()
  tab=Table.read(io.BytesIO(index_bytes),format='ascii.ecsv');ra=np.asarray(tab['RA'],float);dec=np.asarray(tab['DEC'],float);z=np.asarray(tab['z_hetdex'],float);coords=SkyCoord(ra*u.deg,dec*u.deg)
  bytes_read=len(index_bytes)+3*BLOCK+NPIX*8
  for label,cra,cdec in CONTROLS:
   sep=coords.separation(SkyCoord(cra*u.deg,cdec*u.deg)).arcsec;idxs=np.where(sep<=3)[0];rows=[]
   for i in idxs:
    if not np.isfinite(z[i]):continue
    sb,_=get_range(SPECURL,SPEC_DATA_START+int(i)*NPIX*4,NPIX*4);eb,_=get_range(SPECURL,SPECERR_DATA_START+int(i)*NPIX*4,NPIX*4);bytes_read+=2*NPIX*4
    rows.append({'z':float(z[i]),'spec':np.frombuffer(sb,dtype='>f4').astype(float),'err':np.frombuffer(eb,dtype='>f4').astype(float)})
   out['controls'].append({'label':label,'matched_source_observations':len(rows),'nearest_sep_arcsec':float(np.min(sep)),'lambda4363':combine(rows,wave,TARGET),'pseudo_lines':{str(p):combine(rows,wave,p) for p in PSEUDO}})
  test=[r for r in out['controls'] if r['lambda4363'].get('technically_testable')];rec=[r for r in test if r['lambda4363'].get('recovered')];ps=[p for r in out['controls'] for p in r['pseudo_lines'].values() if p.get('technically_testable')];pr=[p for p in ps if p.get('recovered')];counts=[]
  for r in out['controls']:
   q=[p for p in r['pseudo_lines'].values() if p.get('technically_testable')]
   if q:counts.append(sum(p.get('recovered',False) for p in q))
  cond={'at_least_4_testable':len(test)>=4,'control_recovery_ge_075':len(test)>=4 and len(rec)/len(test)>=.75,'pseudo_median_le_05':bool(counts and np.median(counts)<=.5),'pseudo_fraction_le_025':bool(ps and len(pr)/len(ps)<=.25)}
  out.update({'transport_bytes_read_approx':bytes_read,'technically_testable_controls':len(test),'recovered_controls':len(rec),'recovery_fraction':len(rec)/len(test) if test else None,'valid_pseudo_tests':len(ps),'pseudo_recoveries':len(pr),'pseudo_recovery_fraction':len(pr)/len(ps) if ps else None,'median_pseudo_recoveries_per_control':float(np.median(counts)) if counts else None,'gate_conditions':cond,'decision':'VIRUS_SPECTRUM_GATE_PASSED' if all(cond.values()) else 'VIRUS_SPECTRUM_GATE_FAILED','success':True})
 except Exception as e:out['error']=f'{type(e).__name__}: {e}';out['decision']='INFRASTRUCTURE_FAILURE_NO_SCIENTIFIC_DECISION'
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
