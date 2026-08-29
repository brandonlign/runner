#!/usr/bin/env python3
"""Refit/validate OGLE ephemerides for the four prospectively selected Euclid v2 EB controls.

No Euclid science flux is read. Candidate IDs were frozen by the metadata-only
run 33273558474. For each target, OGLE I-band photometry is downloaded from
OGLE-II/III/IV when available. A narrow frequency grid around the published
catalog period is fit on early-time photometry using a periodic Fourier model;
the chosen ephemeris is then evaluated prospectively on the latest 25% OGLE
photometry. Only ephemerides with good late-OGLE phase prediction and tight
2025 propagation qualify for a future Euclid control test.
"""
import io,json,math,urllib.request
from pathlib import Path
import numpy as np
from astropy.time import Time
from astropy.coordinates import SkyCoord,EarthLocation
import astropy.units as u
import euclid_routed_feasibility as b

BASE='https://ftp.astrouw.edu.pl/ogle/ogle4/OCVS/blg/ecl'
OUT=Path('results/euclid_v2_ogle_eb_refit.json');OUT.parent.mkdir(parents=True,exist_ok=True)
TARGETS={
'OGLE-BLG-ECL-125275':{'ra':267.4830833333333,'dec':-30.092,'P0':0.2766925,'T0':7000.24,'depth':0.777},
'OGLE-BLG-ECL-121416':{'ra':267.359375,'dec':-30.082833333333333,'P0':0.247765,'T0':7000.15,'depth':0.644},
'OGLE-BLG-ECL-128512':{'ra':267.58141666666666,'dec':-30.114055555555556,'P0':0.3735955,'T0':7000.0931,'depth':0.621},
'OGLE-BLG-ECL-120480':{'ra':267.32925,'dec':-29.78927777777778,'P0':0.2585159,'T0':7000.2555,'depth':0.344},
}

def get(url):
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'isef-euclid-v2-eb-refit/1.0'})
  with urllib.request.urlopen(req,timeout=90) as r:return r.read().decode('ascii','replace')
 except Exception:return None
def load(sid):
 rows=[];sources=[]
 for era in ('phot_ogle2','phot_ogle3','phot_ogle4'):
  txt=get(f'{BASE}/{era}/I/{sid}.dat')
  if not txt:continue
  n=0
  for l in txt.splitlines():
   try:
    a=l.split();t=float(a[0]);m=float(a[1]);e=float(a[2]);
    if np.isfinite(t+m+e) and 0<e<0.3:rows.append((t,m,e,era));n+=1
   except:pass
  sources.append({'era':era,'rows':n})
 return rows,sources
def design(t,P,K=8):
 ph=2*np.pi*t/P;cols=[np.ones(len(t))]
 for k in range(1,K+1):cols.extend([np.cos(k*ph),np.sin(k*ph)])
 return np.column_stack(cols)
def fit_chi(t,m,e,P,K=8):
 X=design(t,P,K);w=1/np.clip(e,.005,.3);A=X*w[:,None];y=m*w
 try:c=np.linalg.lstsq(A,y,rcond=None)[0];res=(m-X@c)/np.clip(e,.005,.3);return float(np.mean(res*res)),c
 except:return 1e99,None
def model(t,P,c):return design(np.asarray(t),P,(len(c)-1)//2)@c
def grid_fit(t,m,e,P0):
 # Catalog period has 7 decimals. Search ±4e-5 d, wide enough to correct accumulated phase drift but not hunt arbitrary aliases.
 coarse=np.linspace(P0-4e-5,P0+4e-5,801);sc=np.array([fit_chi(t,m,e,p)[0] for p in coarse]);p=coarse[int(np.argmin(sc))]
 fine=np.linspace(p-2e-7,p+2e-7,401);sf=np.array([fit_chi(t,m,e,x)[0] for x in fine]);i=int(np.argmin(sf));p=float(fine[i]);chi,c=fit_chi(t,m,e,p)
 # Empirical period uncertainty via profile width: increase mean normalized chi2 by 1/N (equiv total chi2 +1).
 target=chi+1/len(t);mask=sf<=target
 sig=float((fine[mask].max()-fine[mask].min())/2) if np.any(mask) and np.sum(mask)>1 else 2e-7
 return p,sig,chi,c
def phase_offset_from_template(t,m,e,P,c):
 # Find shift minimizing weighted residual to fixed training template, on a fine phase grid.
 shifts=np.linspace(-.15,.15,1201);vals=[]
 for s in shifts:
  pred=model(t-s*P,P,c);vals.append(np.average((m-pred)**2,weights=1/np.clip(e,.005,.3)**2))
 j=int(np.argmin(vals));return float(shifts[j]),float(vals[j])
def times():
 o=[]
 for ep in range(16):
  h=b.getq(ep,0).raw;iso=h.get('DATE-OBS') or h.get('DATEOBS');tt=Time(str(iso),format='isot',scale='utc') if iso else Time(float(h.get('MJD-OBS',h.get('MJDOBS'))),format='mjd',scale='utc');tt+=.5*float(h.get('EXPTIME',400))*u.s;o.append((ep,float(tt.jd)))
 return o
def hjd(jd,ra,de):
 t=Time(jd,format='jd',scale='utc',location=EarthLocation.from_geocentric(0,0,0,u.m));return float((t+t.light_travel_time(SkyCoord(ra*u.deg,de*u.deg),kind='heliocentric')).jd-2450000)
def pdist(x):return abs((x+.5)%1-.5)
def main():
 ets=times();out=[]
 for sid,r in TARGETS.items():
  rows,src=load(sid);rec={**r,'id':sid,'photometry_sources':src,'n_photometry':len(rows)}
  if len(rows)<100:rec['qualified']=False;rec['failure']='insufficient_photometry';out.append(rec);continue
  a=np.array([(x[0],x[1],x[2]) for x in rows],float);a=a[np.argsort(a[:,0])];cut=np.quantile(a[:,0],.75);tr=a[a[:,0]<=cut];ho=a[a[:,0]>cut]
  P,Psig,chi,c=grid_fit(tr[:,0],tr[:,1],tr[:,2],r['P0']);shift,holdmse=phase_offset_from_template(ho[:,0],ho[:,1],ho[:,2],P,c)
  # Estimate expected peak-to-peak I amplitude from fitted periodic template.
  g=np.linspace(0,P,2000);pred=model(g,P,c);amp=float(np.nanmax(pred)-np.nanmin(pred))
  baseline=float(np.max(a[:,0])-np.min(a[:,0]));dt2025=max(hjd(j,r['ra'],r['dec']) for _,j in ets)-np.mean(tr[:,0]);phase_sigma_2025=float(abs(dt2025)*Psig/(P*P))
  # Late holdout must require <0.04 cycle phase shift; propagated 2-sigma phase uncertainty <0.04.
  qual=bool(abs(shift)<=.04 and 2*phase_sigma_2025<=.04 and amp>=.15)
  phases=[{'epoch':ep,'phase':float(((hjd(j,r['ra'],r['dec'])-r['T0'])/P)%1)} for ep,j in ets]
  rec.update({'train_n':len(tr),'holdout_n':len(ho),'train_end_hjd_minus2450000':float(cut),'fit_period_days':P,'period_profile_sigma_days':Psig,'period_delta_seconds':float((P-r['P0'])*86400),'train_mean_norm_chi2':chi,'late_holdout_best_phase_shift_cycles':shift,'late_holdout_template_mse':holdmse,'fitted_peak_to_peak_mag':amp,'photometry_baseline_days':baseline,'forecast_phase_sigma_2025_1s':phase_sigma_2025,'forecast_phase_95_approx':2*phase_sigma_2025,'euclid_phases_relative_catalog_T0_refined_P':phases,'qualified':qual})
  out.append(rec)
 good=[x for x in out if x.get('qualified')]
 final={'success':True,'frozen_candidate_ids':list(TARGETS),'qualified_controls':len(good),'decision':'EB_CONTROL_EPHEMERIS_VALIDATED' if good else 'EB_CONTROL_EPHEMERIS_FAILED','qualification_rule':'late OGLE holdout phase shift <=0.04 cycles; approximate 2025 95% propagated phase uncertainty <=0.04 cycles; fitted OGLE amplitude >=0.15 mag','targets':out,'note':'No Euclid science flux values were read. Candidate IDs came from metadata-only run 33273558474.'};OUT.write_text(json.dumps(final,indent=2,sort_keys=True)+'\n');print(json.dumps(final,indent=2,sort_keys=True))
if __name__=='__main__':main()
