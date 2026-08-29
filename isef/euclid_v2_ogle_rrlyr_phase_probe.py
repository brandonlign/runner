#!/usr/bin/env python3
"""Prospective Euclid Q2 v2 controls from OGLE RR Lyrae.

No Euclid science flux is read. Selection uses only OGLE position, period and
period uncertainty, epoch of maximum, amplitude/magnitude, Euclid timestamps,
and exact all-16-exposure WCS coverage. Survivors require OGLE time-series
validation before any Euclid photometry is inspected.
"""
import json,math,urllib.request
from pathlib import Path
import numpy as np
from astropy.time import Time
from astropy.coordinates import SkyCoord,EarthLocation
import astropy.units as u
import euclid_routed_feasibility as b
import euclid_exact_routing as er
BASE='https://ftp.astrouw.edu.pl/ogle/ogle4/OCVS/blg/rrlyr'
OUT=Path('results/euclid_v2_ogle_rrlyr_phase_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
CENTER=(267.5945,-30.0074);RAD=.70;EPOCH_QUANT_HALF=.5e-5

def fetch(n):
 req=urllib.request.Request(f'{BASE}/{n}',headers={'User-Agent':'isef-euclid-v2-rrlyr/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r:return r.read().decode('ascii',errors='replace')
def ident(txt):
 d={}
 for l in txt.splitlines():
  if len(l)<51:continue
  try:
   sid=l[:20].strip();h=int(l[28:30]);m=int(l[31:33]);s=float(l[34:39]);sg=-1 if l[40:41]=='-' else 1;dd=int(l[41:43]);dm=int(l[44:46]);ds=float(l[47:51]);d[sid]={'id':sid,'subtype':l[22:26].strip(),'ra':15*(h+m/60+s/3600),'dec':sg*(dd+dm/60+ds/3600)}
  except:pass
 return d
def pars(txt):
 d={}
 for l in txt.splitlines():
  if len(l)<78:continue
  try:
   sid=l[:20].strip();I=float(l[22:28]);V=l[29:35].strip();P=float(l[37:47]);Pe=float(l[48:58]);ep=float(l[60:70]);amp=float(l[72:77]);d[sid]={'imag':I,'vmag':float(V) if V else None,'period_days':P,'period_error_days':Pe,'epoch_max_hjd_minus2450000':ep,'amplitude_mag':amp}
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
def phase(r,ts):
 P=r['period_days'];Pe=r['period_error_days'];ep=2450000+r['epoch_max_hjd_minus2450000'];q=[];ms=0
 for e,jd,_ in ts:
  h=hjd(jd,r['ra'],r['dec']);cy=(h-ep)/P;ph=cy%1;sig=math.hypot(EPOCH_QUANT_HALF/P,abs(h-ep)*Pe/(P*P));ms=max(ms,sig);q.append({'epoch':e,'phase':ph,'phase_sigma_from_catalog_period_1s_plus_epoch_quant':sig})
 if ms>.06:return None
 vals=np.array([.5*r['amplitude_mag']*math.cos(2*math.pi*x['phase']) for x in q]);span=float(vals.max()-vals.min())
 if span<.12:return None
 return {**r,'max_forecast_phase_sigma':ms,'predicted_fundamental_mag_span':span,'phases':q}
def main():
 I=ident(fetch('ident.dat'));P={};P.update(pars(fetch('RRab.dat')));P.update(pars(fetch('RRc.dat')));ts=times();pre=[];metadata=0
 for sid,a in I.items():
  if sid not in P:continue
  r={**a,**P[sid]}
  if sep(r)>RAD or r['imag']>19.5 or r['amplitude_mag']<.20 or r['period_error_days']<=0:continue
  metadata+=1;q=phase(r,ts)
  if q:pre.append(q)
 pre.sort(key=lambda x:(x['max_forecast_phase_sigma'],-x['predicted_fundamental_mag_span'],-x['amplitude_mag'],x['imag']))
 gm=er.map_groups();good=[];bad=0
 # Route highest-value prospective controls first, but selection order has no Euclid flux information.
 for r in pre:
  try:
   rt,diag=er.route_target(gm,(r['ra'],r['dec']));good.append({**r,'routes':{str(k):int(v) for k,v in rt.items()},'route_diagnostics':diag})
   if len(good)>=25:break
  except:bad+=1
 out={'success':True,'decision':'RRLYR_EPHEMERIS_VALIDATION_WORTHWHILE' if good else 'RRLYR_PHASE_CONTROL_NOT_FEASIBLE','metadata_candidates':metadata,'phase_precise_candidates_before_routing':len(pre),'exact_routed_phase_controls_to_validate':len(good),'routing_rejections_examined':bad,'best_candidates':good,'euclid_times':[{'epoch':e,'jd_utc_mid':j,'utc_mid_isot':i} for e,j,i in ts],'selection_note':'No Euclid science flux read; sinusoidal span is a conservative target-ranking proxy, not the final expected RR Lyrae template. OGLE time-series validation is required before Euclid control testing.'};OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
