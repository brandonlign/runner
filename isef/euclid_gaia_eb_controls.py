#!/usr/bin/env python3
"""Externally selected Gaia DR3 eclipsing-binary controls for Euclid Q2 Field 1.

Selection uses Gaia metadata only. Euclid measurements are never used to choose
which systems enter the positive-control set.
"""
import csv,io,json,urllib.parse,urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
from astropy.table import Table
import euclid_routed_feasibility as b
import euclid_exact_routing as er
OUT=Path('results/euclid_gaia_eb_controls.json');OUT.parent.mkdir(parents=True,exist_ok=True)
TAPS=['https://gea.esac.esa.int/tap-server/tap/sync','https://gaia.aip.de/tap/sync']
# Center on the already established exact-WCS-safe development footprint. This
# geometric choice predates this query and is not based on candidate Euclid flux.
CENTER=(267.58,-30.11);RADIUS=0.18

def parse(raw):
 t=raw.decode('utf-8','replace')
 if 'value="ERROR"' in t[:4000]:raise RuntimeError(t[:1500])
 if '<VOTABLE' in t[:1000]:
  q=Table.read(io.BytesIO(raw),format='votable');return [{str(n).lower():('' if np.ma.is_masked(r[n]) else str(r[n])) for n in q.colnames} for r in q]
 return [{str(k).lower():v for k,v in r.items()} for r in csv.DictReader(io.StringIO(t))]
def tap(q):
 body=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'csv','QUERY':q}).encode();errs=[]
 for u in TAPS:
  try:
   req=urllib.request.Request(u,data=body,headers={'User-Agent':'isef-euclid-eb-controls/1.1','Content-Type':'application/x-www-form-urlencoded'});raw=urllib.request.urlopen(req,timeout=30).read();return parse(raw),u
  except Exception as e:errs.append(f'{u}: {e}')
 raise RuntimeError('; '.join(errs))
def aper(im,x,y,r=2.2,ri=5,ro=8):
 x0=max(0,int(x)-9);x1=min(im.shape[1],int(x)+10);y0=max(0,int(y)-9);y1=min(im.shape[0],int(y)+10);s=im[y0:y1,x0:x1];yy,xx=np.indices(s.shape);rr=np.hypot(xx+x0-x,yy+y0-y);a=s[rr<=r];n=s[(rr>=ri)&(rr<=ro)];return float(np.nansum(a-np.nanmedian(n))) if len(a)>=8 and len(n)>=20 else np.nan
def sid(r):return r.get('sid') or r.get('datalinkid') or r.get('source_id')
def measure(r,gm):
 ra=float(r['cra']);de=float(r['cdec'])
 try:routes,diag=er.route_target(gm,(ra,de))
 except Exception as e:return {'source_id':sid(r),'ra':ra,'dec':de,'routed':False,'route_error':str(e)}
 hs=b.epoch_headers(routes);ims=[None]*16;meta=[None]*16
 with ThreadPoolExecutor(max_workers=8) as ex:
  fs=[ex.submit(er.stamp,e,hs[e],ra,de) for e in range(16)]
  for f in as_completed(fs):e,z,m=f.result();ims[e]=z;meta[e]=m
 fl=[]
 for e,q in enumerate(hs):
  x,y=b.pix(q,ra,de);fl.append(aper(ims[e],float(x)-meta[e]['x0'],float(y)-meta[e]['y0']))
 fl=np.asarray(fl,float);valid=bool(np.all(np.isfinite(fl)&(fl>0)));o={'source_id':sid(r),'ra':ra,'dec':de,'routed':True,'valid_flux':valid,'gmag':float(r['gmag']),'frequency_per_day':float(r['freq']),'period_hours':24/float(r['freq']),'primary_depth_mag':float(r['depth']),'primary_duration_phase':float(r['duration']),'global_ranking':float(r['rank']),'route_diagnostics':diag}
 if valid:
  z=fl/np.median(fl);o['normalized_flux']=z.tolist();o['max_abs_excursion']=float(np.max(np.abs(z-1)));o['peak_to_peak_fraction']=float(np.max(z)-np.min(z))
 return o
def main():
 ra,de=CENTER;q=f"""SELECT TOP 60 gs.source_id AS sid,gs.ra AS cra,gs.dec AS cdec,gs.phot_g_mean_mag AS gmag,v.frequency AS freq,v.derived_primary_ecl_depth AS depth,v.derived_primary_ecl_duration AS duration,v.global_ranking AS rank FROM gaiadr3.gaia_source AS gs JOIN gaiadr3.vari_eclipsing_binary AS v ON gs.source_id=v.source_id WHERE 1=CONTAINS(POINT('ICRS',gs.ra,gs.dec),CIRCLE('ICRS',{ra},{de},{RADIUS})) AND gs.phot_g_mean_mag<19.0 AND v.frequency>=2.0 AND v.derived_primary_ecl_depth>=0.20 AND v.derived_primary_ecl_duration>=0.03 AND v.global_ranking>=0.5 ORDER BY v.derived_primary_ecl_depth DESC"""
 try:rows,endpoint=tap(q)
 except Exception as e:rows=[];endpoint=None;err=str(e)
 if not rows:
  o={'success':False,'query':q,'endpoint':endpoint,'error':locals().get('err','zero rows')};OUT.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps(o,indent=2));return
 gm=er.map_groups();tested=[]
 for r in rows:
  z=measure(r,gm);tested.append(z)
  if sum(bool(x.get('valid_flux')) for x in tested)>=8 or len(tested)>=30:break
 good=[x for x in tested if x.get('valid_flux')];o={'success':len(good)>0,'endpoint':endpoint,'query':q,'catalog_candidates_returned':len(rows),'selection':'Gaia DR3 EB selected before Euclid measurement: G<19; frequency>=2/d; primary eclipse depth>=0.20 mag; eclipse duration phase>=0.03; global ranking>=0.5; ordered by published eclipse depth; geometric cone centered on pre-existing exact-WCS-safe development footprint','tested':tested,'valid_controls':len(good)}
 if good:o['diagnostic_ranking_by_euclid_excursion']=sorted([{'source_id':x['source_id'],'max_abs_excursion':x['max_abs_excursion'],'peak_to_peak_fraction':x['peak_to_peak_fraction'],'period_hours':x['period_hours'],'primary_depth_mag':x['primary_depth_mag'],'primary_duration_phase':x['primary_duration_phase'],'global_ranking':x['global_ranking']} for x in good],key=lambda x:x['max_abs_excursion'],reverse=True)
 OUT.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,indent=2,sort_keys=True))
if __name__=='__main__':main()
