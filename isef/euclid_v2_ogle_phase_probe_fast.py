#!/usr/bin/env python3
"""Fast metadata-only Euclid v2 OGLE phase-control feasibility probe.

Phase-predict from OGLE metadata before exact-WCS routing. No Euclid science flux
is read. Survivors require an OGLE time-series ephemeris refit before any Euclid
photometric test.
"""
import json, math, urllib.request
from pathlib import Path
from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation
import astropy.units as u
import euclid_routed_feasibility as b
import euclid_exact_routing as er
BASE='https://ftp.astrouw.edu.pl/ogle/ogle4/OCVS/blg/ecl'
OUT=Path('results/euclid_v2_ogle_phase_probe_fast.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
CENTER=(267.45,-30.05); RAD=0.60; DP=0.5e-7; DE=0.5e-4

def fetch(n):
 req=urllib.request.Request(f'{BASE}/{n}',headers={'User-Agent':'isef-euclid-v2-ogle-phase-fast/1.0'})
 with urllib.request.urlopen(req,timeout=240) as r:return r.read().decode('ascii',errors='replace')
def ids(txt):
 d={}
 for l in txt.splitlines():
  if len(l)<48:continue
  try:
   s=l[:19].strip();h=int(l[25:27]);m=int(l[28:30]);z=float(l[31:36]);sg=-1 if l[37:38]=='-' else 1;dd=int(l[38:40]);dm=int(l[41:43]);ds=float(l[44:48]);d[s]={'id':s,'subtype':l[21:24].strip(),'ra':15*(h+m/60+z/3600),'dec':sg*(dd+dm/60+ds/3600)}
  except:pass
 return d
def pars(txt):
 d={}
 for l in txt.splitlines():
  if len(l)<65:continue
  try:
   s=l[:19].strip();d[s]={'imag':float(l[21:27]),'period_days':float(l[35:47]),'epoch_hjd_minus2450000':float(l[49:58]),'primary_depth_mag':float(l[60:65])}
  except:pass
 return d
def sep(r):return math.hypot((r['ra']-CENTER[0])*math.cos(math.radians((r['dec']+CENTER[1])/2)),r['dec']-CENTER[1])
def times():
 o=[]
 for e in range(16):
  h=b.getq(e,0).raw;iso=h.get('DATE-OBS') or h.get('DATEOBS');t=Time(str(iso),format='isot',scale='utc') if iso else Time(float(h.get('MJD-OBS',h.get('MJDOBS'))),format='mjd',scale='utc');t+=0.5*float(h.get('EXPTIME',400))*u.s;o.append((e,float(t.jd),t.utc.isot))
 return o
def hjd(jd,ra,de):
 t=Time(jd,format='jd',scale='utc',location=EarthLocation.from_geocentric(0,0,0,u.m));return float((t+t.light_travel_time(SkyCoord(ra*u.deg,de*u.deg),kind='heliocentric')).jd)
def pd(x):return abs((x+0.5)%1-.5)
def phase(r,ts):
 P=r['period_days'];ep=2450000+r['epoch_hjd_minus2450000'];a=[];near=[];far=[];mq=0
 for e,jd,_ in ts:
  h=hjd(jd,r['ra'],r['dec']);cy=(h-ep)/P;ph=cy%1;q=(DE+abs(cy)*DP)/P;dist=pd(ph);mq=max(mq,q)
  if dist+q<=.055:near.append(e)
  if dist-q>=.18:far.append(e)
  a.append({'epoch':e,'phase':ph,'distance_primary':dist,'catalog_quantization_phase_bound':q})
 return ({**r,'near_primary_epochs':near,'far_primary_epochs':far,'max_catalog_quantization_phase_bound':mq,'phases':a} if near and len(far)>=3 else None)
def main():
 I=ids(fetch('ident.dat'));E=pars(fetch('ecl.dat'));ts=times();pre=[];mn=0
 for s,r0 in I.items():
  if s not in E:continue
  r={**r0,**E[s]}
  if sep(r)>.60 or not(.12<=r['period_days']<=.5) or r['primary_depth_mag']<.20 or r['imag']>19.5:continue
  mn+=1;q=phase(r,ts)
  if q:pre.append(q)
 pre.sort(key=lambda x:(-x['primary_depth_mag'],x['max_catalog_quantization_phase_bound'],x['imag'],x['period_days']))
 gm=er.map_groups();good=[];bad=0
 for r in pre:
  try:
   rt,d=er.route_target(gm,(r['ra'],r['dec']));good.append({**r,'routes':{str(k):int(v) for k,v in rt.items()},'route_diagnostics':d})
  except:bad+=1
 out={'success':True,'decision':'OGLE_EPHEMERIS_REFIT_WORTHWHILE' if good else 'OGLE_PHASE_CONTROL_NOT_FEASIBLE','ident_objects':len(I),'ecl_objects':len(E),'metadata_candidates':mn,'phase_candidates_before_routing':len(pre),'exact_routed_phase_candidates':len(good),'routing_rejections':bad,'best_candidates':good[:20],'euclid_times':[{'epoch':e,'jd_utc_mid':j,'utc_mid_isot':i} for e,j,i in ts],'note':'No Euclid science flux read; catalog numeric precision is not physical ephemeris uncertainty. Refit OGLE time series before using any survivor as a control.'};OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
