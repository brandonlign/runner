#!/usr/bin/env python3
"""Anonymous APO-only 6D calibration under the frozen DR20 protocol.
No LCO 6D outcomes or source identities are accessed/emitted.
"""
from pathlib import Path
import json, urllib.request, gzip, shutil
import numpy as np
from astropy.io import fits
import astropy.units as u
from astropy.coordinates import SkyCoord, Galactocentric, CartesianDifferential, ICRS
OUT=Path('results/sdss_dr20_apo_6d_calibration.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
URL='https://dr20.sdss.org/sas/dr20/spectro/astra/0.8.1/summary/mwmAllStar-0.8.1.fits.gz'
TH=[400.,500.,600.,700.,800.]
GC=Galactocentric(galcen_coord=ICRS(ra=266.4051*u.deg,dec=-28.936175*u.deg),galcen_distance=8.122*u.kpc,galcen_v_sun=CartesianDifferential([12.9,245.6,7.78]*u.km/u.s),z_sun=20.8*u.pc,roll=0*u.deg)
def dl(url,p):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-SDSS-DR20-APO-6D/1.0'})
 with urllib.request.urlopen(req,timeout=300) as r,open(p,'wb') as f:
  while True:
   b=r.read(8<<20)
   if not b:break
   f.write(b)
def speed(ra,dec,dist,pmra,pmde,rv):
 c=SkyCoord(ra=np.asarray(ra)*u.deg,dec=np.asarray(dec)*u.deg,distance=np.asarray(dist)*u.pc,pm_ra_cosdec=np.asarray(pmra)*u.mas/u.yr,pm_dec=np.asarray(pmde)*u.mas/u.yr,radial_velocity=np.asarray(rv)*u.km/u.s,frame='icrs')
 g=c.transform_to(GC)
 return np.sqrt(g.v_x.to_value(u.km/u.s)**2+g.v_y.to_value(u.km/u.s)**2+g.v_z.to_value(u.km/u.s)**2)
def counts(v,ths=TH):return {str(int(t)):int(np.sum(v>t)) for t in ths}
def monotonic(d):
 vals=[d[str(int(t))] for t in TH if str(int(t)) in d]
 return all(vals[i]>=vals[i+1] for i in range(len(vals)-1))
def main():
 out={'success':False,'status':'ANONYMOUS_APO_6D_CALIBRATION','identities_emitted':False,'lco_6d_accessed':False,'mc_draws_per_star':128,'thresholds_kms':TH}
 try:
  gz=Path('/tmp/mwmAllStar6d.fits.gz'); ff=Path('/tmp/mwmAllStar6d.fits');dl(URL,gz)
  with gzip.open(gz,'rb') as src,open(ff,'wb') as dst:shutil.copyfileobj(src,dst,length=8<<20)
  with fits.open(ff,memmap=True) as h:
   tables=[x.data for x in h[1:] if getattr(x,'data',None) is not None and hasattr(x.data,'names') and 'telescope' in x.data.names and 'v_rad' in x.data.names and len(x.data)>0]
   d0=max(tables,key=len); tel=np.char.lower(np.char.strip(np.asarray(d0['telescope']).astype(str))); apo_idx=np.flatnonzero(tel=='apo25m')
   out['apo_rows_structural']=int(len(apo_idx));out['lco_rows_structural_only']=int(np.sum(tel=='lco25m'))
   d=d0[apo_idx]
   v=np.asarray(d['v_rad'],float);ev=np.asarray(d['e_v_rad'],float);sv=np.asarray(d['std_v_rad'],float);sn=np.asarray(d['snr'],float);ng=np.asarray(d['n_good_rvs'],int);zw=np.asarray(d['zwarning_flags'],np.int64);nm=np.asarray(d['nmf_flags'],np.int64)
   rvok=np.isfinite(v)&np.isfinite(ev)&np.isfinite(sv)&np.isfinite(sn)&(sn>10)&(ev<30)&(ng>=2)&(sv<=30)&(zw==0)&(nm==0)
   ra=np.asarray(d['ra'],float);dec=np.asarray(d['dec'],float);pmra=np.asarray(d['pmra'],float);pmde=np.asarray(d['pmde'],float);epmra=np.asarray(d['e_pmra'],float);epmde=np.asarray(d['e_pmde'],float)
   lo=np.asarray(d['r_lo_photogeo'],float);med=np.asarray(d['r_med_photogeo'],float);hi=np.asarray(d['r_hi_photogeo'],float);na=np.asarray(d['n_associated'],int);nn=np.asarray(d['n_neighborhood'],int)
   finite=np.isfinite(ra)&np.isfinite(dec)&np.isfinite(pmra)&np.isfinite(pmde)&np.isfinite(epmra)&np.isfinite(epmde)&(epmra>0)&(epmde>0)&np.isfinite(lo)&np.isfinite(med)&np.isfinite(hi)&(lo>0)&(med>0)&(hi>0)&(lo<med)&(med<hi)
   width=np.full(len(d),np.inf);width[finite]=(hi[finite]-lo[finite])/(2*med[finite])
   pmsig=np.zeros(len(d));pmsig[finite]=np.sqrt((pmra[finite]/epmra[finite])**2+(pmde[finite]/epmde[finite])**2)
   usable=rvok&finite&(width<=0.30)&(pmsig>=5)&(na==1)
   ii=np.flatnonzero(usable);out['repeat_stable_apo_rows']=int(rvok.sum());out['sixd_usable_apo_rows']=int(len(ii));out['sixd_usable_fraction_of_rvstable']=float(len(ii)/rvok.sum()) if rvok.sum() else 0.0
   out['n_neighborhood_diagnostic']={'median':float(np.median(nn[ii])) if len(ii) else None,'fraction_zero':float(np.mean(nn[ii]==0)) if len(ii) else None,'fraction_le1':float(np.mean(nn[ii]<=1)) if len(ii) else None}
   nom=speed(ra[ii],dec[ii],med[ii],pmra[ii],pmde[ii],v[ii]) if len(ii) else np.array([])
   out['nominal_speed_counts']=counts(nom)
   # Fixed per-row deterministic MC seeds. Process in chunks but retain per-star 2.5th percentiles only.
   vlo=np.empty(len(ii),float);vmed=np.empty(len(ii),float);vhi=np.empty(len(ii),float)
   D=128;chunk=256
   for a in range(0,len(ii),chunk):
    inds=ii[a:a+chunk];n=len(inds);R=np.empty((n,D));P1=np.empty((n,D));P2=np.empty((n,D));VR=np.empty((n,D))
    for j,idx in enumerate(inds):
     rng=np.random.default_rng(20260830+int(apo_idx[idx]))
     z=rng.normal(size=D);sig=np.where(z<0,med[idx]-lo[idx],hi[idx]-med[idx]);R[j]=np.maximum(1.0,med[idx]+z*sig)
     P1[j]=rng.normal(pmra[idx],epmra[idx],D);P2[j]=rng.normal(pmde[idx],epmde[idx],D);VR[j]=rng.normal(v[idx],ev[idx],D)
    RA=np.repeat(ra[inds],D);DE=np.repeat(dec[inds],D);sp=speed(RA,DE,R.ravel(),P1.ravel(),P2.ravel(),VR.ravel()).reshape(n,D)
    vlo[a:a+n]=np.quantile(sp,.025,axis=1);vmed[a:a+n]=np.quantile(sp,.5,axis=1);vhi[a:a+n]=np.quantile(sp,.975,axis=1)
   out['mc_lower_speed_counts']=counts(vlo,TH[:-1]);out['mc_median_speed_counts']=counts(vmed);out['mc_upper_speed_counts']=counts(vhi)
   highrv=np.abs(v[ii])>400
   out['high_abs_rv400_subset']={'n':int(highrv.sum()),'nominal_speed_counts':counts(nom[highrv]),'mc_lower_speed_counts':counts(vlo[highrv],TH[:-1])}
   cond={'usable_ge_10000':len(ii)>=10000,'nominal_gt400_ge100':out['nominal_speed_counts']['400']>=100,'lower_gt400_ge10':out['mc_lower_speed_counts']['400']>=10,'nominal_monotonic':monotonic(out['nominal_speed_counts']),'lower_monotonic':all(out['mc_lower_speed_counts'][str(int(TH[i]))]>=out['mc_lower_speed_counts'][str(int(TH[i+1]))] for i in range(len(TH)-2))}
   out['calibration_conditions']=cond;out['decision']='APO_6D_PIPELINE_CALIBRATED' if all(cond.values()) else 'APO_6D_PIPELINE_NOT_CALIBRATED';out['success']=True
 except Exception as e:
  out['error']=f'{type(e).__name__}: {e}';out['decision']='INFRASTRUCTURE_FAILURE_NO_SCIENTIFIC_DECISION'
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
