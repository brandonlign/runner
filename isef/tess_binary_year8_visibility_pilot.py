#!/usr/bin/env python3
"""Metadata-only visibility pilot for a prospective Year-8 TESS asteroid sample.

Queries JPL SBDB metadata for bright, numbered, no-known-satellite main-belt
asteroids, then deterministically hashes to a 128-object feasibility subset and
uses tess-ephem for Sectors 97/98 visibility. No TESS pixel or light-curve value
is requested/opened. The subset is for yield/runtime estimation only and is not
the eventual discovery sample.
"""
from __future__ import annotations
import hashlib, json, urllib.parse
from pathlib import Path
import numpy as np, pandas as pd, requests
from tess_ephem import ephem

OUT=Path('results/tess_binary_year8_visibility_pilot');OUT.mkdir(parents=True,exist_ok=True)
SECTORS=(97,98)
PILOT_N=128
H_MAX=14.5
I_MIN_DEG=8.0
COND_MAX=3
VMAG_MEDIAN_MAX=18.0
MIN_EPHEM_DAYS=5


def sbdb_pool():
    cdata=json.dumps({'AND':[f'H|LE|{H_MAX}',f'i|GE|{I_MIN_DEG}',f'condition_code|LE|{COND_MAX}']},separators=(',',':'))
    params={'fields':'spkid,pdes,full_name,H,i,condition_code,rot_per,diameter,class','sb-class':'MBA','sb-ns':'n','sb-kind':'a','sb-sat':'false','sb-cdata':cdata,'full-prec':'true'}
    r=requests.get('https://ssd-api.jpl.nasa.gov/sbdb_query.api',params=params,timeout=120);r.raise_for_status();j=r.json()
    if 'data' not in j:raise RuntimeError(j)
    cols=j['fields'];rows=[dict(zip(cols,x)) for x in j['data']]
    for z in rows:
        z['hash']=hashlib.sha256(str(z['pdes']).encode()).hexdigest()
    rows.sort(key=lambda z:(z['hash'],str(z['pdes'])))
    return rows, r.url


def finite_num(x):
    try:
        v=float(x);return v if np.isfinite(v) else None
    except Exception:return None


def main():
    pool,url=sbdb_pool();pilot=pool[:PILOT_N];results=[]
    for n,z in enumerate(pilot,1):
        q={'spkid':z['spkid'],'pdes':z['pdes'],'full_name':z['full_name'],'H':finite_num(z['H']),'i_deg':finite_num(z['i']),
           'condition_code':finite_num(z['condition_code']),'rot_per_h':finite_num(z['rot_per']),'diameter_km':finite_num(z['diameter']),'hash':z['hash'],'sectors':{}}
        for s in SECTORS:
            try:
                d=ephem(str(z['pdes']),sector=s,time_step=2.0)
                if d is None or len(d)==0:
                    q['sectors'][str(s)]={'visible':False,'rows':0};continue
                vv=np.asarray(d['vmag'],float) if 'vmag' in d.columns else np.full(len(d),np.nan)
                cams=sorted({f"{int(a)}/{int(b)}" for a,b in zip(d['camera'],d['ccd'])})
                med=float(np.nanmedian(vv)) if np.isfinite(vv).any() else None
                q['sectors'][str(s)]={'visible':True,'rows':int(len(d)),'camera_ccd':cams,'vmag_median':med,
                                      'vmag_min':float(np.nanmin(vv)) if np.isfinite(vv).any() else None,
                                      'vmag_max':float(np.nanmax(vv)) if np.isfinite(vv).any() else None,
                                      'time_min':float(np.min(np.asarray(d.index,float))),'time_max':float(np.max(np.asarray(d.index,float)))}
            except Exception as e:
                q['sectors'][str(s)]={'visible':False,'rows':0,'error':f'{type(e).__name__}: {e}'[:500]}
        results.append(q);print(n,z['pdes'],q['sectors'],flush=True)
    qualifying=[]
    for q in results:
        for s,v in q['sectors'].items():
            if v.get('visible') and v.get('rows',0)>=MIN_EPHEM_DAYS and v.get('vmag_median') is not None and v['vmag_median']<=VMAG_MEDIAN_MAX:
                qualifying.append({'pdes':q['pdes'],'full_name':q['full_name'],'sector':int(s),'vmag_median':v['vmag_median'],'ephem_rows':v['rows'],'camera_ccd':v.get('camera_ccd',[])})
    rep={'role':'metadata-only Year-8 visibility/yield pilot; not final discovery sample','tess_pixel_values_opened':False,'tess_lightcurve_values_opened':False,
         'jpl_pool_query_url':url,'pool_n':len(pool),'pilot_n':len(pilot),'selection':{'class':'MBA','numbered':True,'known_satellite':False,'H_max':H_MAX,'inclination_min_deg':I_MIN_DEG,'condition_code_max':COND_MAX,'deterministic_order':'SHA256(pdes)','subset_n':PILOT_N},
         'visibility':{'sectors':list(SECTORS),'tess_ephem_time_step_days':2.0,'qualifying_vmag_median_max':VMAG_MEDIAN_MAX,'min_ephem_rows':MIN_EPHEM_DAYS,'qualifying_object_sector_n':len(qualifying)},
         'qualifying':qualifying,'pilot_results':results}
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    pd.DataFrame(qualifying).to_csv(OUT/'qualifying.csv',index=False)
    print(json.dumps({'pool_n':len(pool),'pilot_n':len(pilot),'qualifying_object_sector_n':len(qualifying),'qualifying':qualifying},indent=2))

if __name__=='__main__':main()
