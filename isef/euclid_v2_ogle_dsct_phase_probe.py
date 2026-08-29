#!/usr/bin/env python3
"""Prospective Euclid Q2 v2 positive-control feasibility using OGLE delta Scuti stars.

NO Euclid science flux is read. Targets are selected solely from the published
OGLE bulge delta-Scuti catalog (position, I magnitude, amplitude, period,
period uncertainty, epoch and Fourier shape) plus Euclid FITS timestamps and
exact WCS coverage. The catalog ephemeris is propagated to the 2025 Euclid
sequence. Survivors must then have their OGLE time series refit/validated before
any Euclid flux is inspected.
"""
import json,math,urllib.request
from pathlib import Path
from astropy.time import Time
from astropy.coordinates import SkyCoord,EarthLocation
import astropy.units as u
import numpy as np
import euclid_routed_feasibility as b
import euclid_exact_routing as er
BASE='https://ftp.astrouw.edu.pl/ogle/ogle4/OCVS/blg/dsct'
OUT=Path('results/euclid_v2_ogle_dsct_phase_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
CENTER=(267.45,-30.05);RAD=.65
EPOCH_QUANT_HALF=.5e-5 # HJD F10.5

def fetch(n):
 req=urllib.request.Request(f'{BASE}/{n}',headers={'User-Agent':'isef-euclid-v2-dsct/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r:return r.read().decode('ascii',errors='replace')
def ident(txt):
 d={}
 for l in txt.splitlines():
  if len(l)<56:continue
  try:
   sid=l[:19].strip();h=int(l[33:35]);m=int(l[36:38]);s=float(l[39:44]);sg=-1 if l[45:46]=='-' else 1;dd=int(l[46:48]);dm=int(l[49:51]);ds=float(l[52:56]);d[sid]={'id':sid,'mode':l[21:31].strip(),'ra':15*(h+m/60+s/3600),'dec':sg*(dd+dm/60+ds/3600)}
  except:pass
 return d
def params(txt):
 d={}
 for l in txt.splitlines():
  if len(l)<104:continue
  try:
   sid=l[:19].strip();I=float(l[21:27]);V=l[28:34].strip();P=float(l[36:46]);Pe=float(l[47:57]);ep=float(l[59:69]);amp=float(l[71:76]);r21=float(l[78:83]);phi21=float(l[84:89]);r31=float(l[91:96]);phi31=float(l[97:102]);d[sid]={'imag':I,'vmag':float(V) if V else None,'period_days':P,'period_error_days':Pe,'epoch_max_hjd_minus2450000':ep,'amplitude_mag':amp,'r21':r21,'phi21':phi21,'r31':r31,'phi31':phi31}
  except:pass
 return d
def sep(r):return math.hypot((r['ra']-CENTER[0])*math.cos(math.radians((r['dec']+CENTER[1])/2)),r['dec']-CENTER[1])
def times():
 o=[]
 for e in range(16):
  h=b.getq(e,0).raw;iso=h.get('DATE-OBS') or h.get('DATEOBS');t=Time(str(iso),format='isot',scale='utc') if iso else Time(float(h.get('MJD-OBS',h.get('MJDOBS'))),format='mjd',scale='utc');t+=.5*float(h.get('EXPTIME',400))*u.s;o.append((e,float(t.jd),t.utc.isot))
 return o
def hjd(jd,ra,de):
 t=Time(jd,format='jd',scale='utc',location=EarthLocation.from_geocentric(0,0,0,u.m));return float((t+t.light_travel_time(SkyCoord(ra*u.deg,de*u.deg),kind='heliocentric')).jd)
def pd(x):return abs((x+.5)%1-.5)
def phase_info(r,ts):
 P=r['period_days'];Pe=r['period_error_days'];ep=2450000+r['epoch_max_hjd_minus2450000'];q=[];maxsig=0
 for e,jd,_ in ts:
  h=hjd(jd,r['ra'],r['dec']);cy=(h-ep)/P;ph=cy%1;sig=math.hypot(EPOCH_QUANT_HALF/P,abs(h-ep)*Pe/(P*P));maxsig=max(maxsig,sig);q.append({'epoch':e,'phase':ph,'phase_sigma_from_catalog_period_1s_plus_epoch_quant':sig})
 # Require forecast phase precision tight enough that 16 phases remain informative.
 if maxsig>.08:return None
 # Conservative signal proxy independent of Euclid: sinusoidal fundamental with listed peak-to-peak amplitude.
 vals=np.array([.5*r['amplitude_mag']*math.cos(2*math.pi*x['phase']) for x in q]);span=float(vals.max()-vals.min())
 if span<.12:return None
 return {**r,'max_forecast_phase_sigma':maxsig,'predicted_fundamental_mag_span':span,'phases':q}
def main():
 I=ident(fetch('ident.dat'));P=params(fetch('dsct.dat'));ts=times();pre=[];metadata=0
 for sid,a in I.items():
  if sid not in P:continue
  r={**a,**P[sid]}
  if sep(r)>RAD or r['imag']>19.5 or r['amplitude_mag']<.15 or r['period_days']>.25 or r['period_days']<.02 or r['period_error_days']<=0:continue
  metadata+=1;q=phase_info(r,ts)
  if q:pre.append(q)
 pre.sort(key=lambda x:(x['max_forecast_phase_sigma'],-x['predicted_fundamental_mag_span'],-x['amplitude_mag'],x['imag']))
 gm=er.map_groups();good=[];bad=0
 for r in pre:
  try:
   rt,diag=er.route_target(gm,(r['ra'],r['dec']));good.append({**r,'routes':{str(k):int(v) for k,v in rt.items()},'route_diagnostics':diag})
  except:bad+=1
 out={'success':True,'decision':'DSCT_EPHEMERIS_REFIT_WORTHWHILE' if good else 'DSCT_PHASE_CONTROL_NOT_FEASIBLE','metadata_candidates':metadata,'phase_precise_candidates_before_routing':len(pre),'exact_routed_phase_controls_to_refit':len(good),'routing_rejections':bad,'best_candidates':good[:25],'euclid_times':[{'epoch':e,'jd_utc_mid':j,'utc_mid_isot':i} for e,j,i in ts],'selection_note':'No Euclid science flux read. The sinusoidal span is only a conservative preselection proxy; OGLE time-series refit/holdout validation is required before the Euclid control test.'};OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
