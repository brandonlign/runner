#!/usr/bin/env python3
"""Gaia DR3 eclipsing-binary positive controls for Euclid Q2 Field 1.

Selection is defined entirely from Gaia metadata before Euclid fluxes are read:
bright systems with short periods and deep/wide modeled primary eclipses. The
Euclid measurements are then extracted with the pre-existing fixed aperture
method. This is a feasibility positive-control test, not a discovery search.
"""
import csv,io,json,urllib.parse,urllib.request
from pathlib import Path
import numpy as np
import euclid_routed_feasibility as b
from concurrent.futures import ThreadPoolExecutor,as_completed

OUT=Path('results/euclid_gaia_positive_controls_v2.json')
TAP='https://gea.esac.esa.int/tap-server/tap/sync'; CENTER=(267.45,-30.05);RADIUS=0.30

def tap(q):
    body=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'csv','QUERY':q}).encode();req=urllib.request.Request(TAP,data=body,headers={'User-Agent':'isef-euclid-positive-v2/1.1','Content-Type':'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req,timeout=120) as r:txt=r.read().decode('utf-8',errors='replace')
    if '<VOTABLE' in txt[:500] or 'QUERY_STATUS" value="ERROR' in txt:raise RuntimeError(txt[:3000])
    return list(csv.DictReader(io.StringIO(txt)))
def aper(im,x,y,r=2.2,ri=5,ro=8):
    x0=max(0,int(x)-9);x1=min(im.shape[1],int(x)+10);y0=max(0,int(y)-9);y1=min(im.shape[0],int(y)+10);s=im[y0:y1,x0:x1];yy,xx=np.indices(s.shape);rad=np.hypot(xx+x0-x,yy+y0-y);a=s[rad<=r];n=s[(rad>=ri)&(rad<=ro)]
    if len(a)<8 or len(n)<20:return np.nan
    return float(np.nansum(a-np.nanmedian(n)))
def measure(row,qs,shifts):
    ra=float(row['ra']);de=float(row['dec'])
    try:routes,_=b.route_groups(qs,(ra,de),shifts);hs=b.epoch_headers(routes)
    except Exception as e:return {'source_id':row['source_id'],'ra':ra,'dec':de,'routed':False,'routing_error':str(e)}
    ims=[None]*16;meta=[None]*16
    try:
      with ThreadPoolExecutor(max_workers=8) as ex:
        fs=[ex.submit(b.stamp,i,hs[i],ra,de) for i in range(16)]
        for f in as_completed(fs):i,z,m=f.result();ims[i]=z;meta[i]=m
    except Exception as e:return {'source_id':row['source_id'],'ra':ra,'dec':de,'routed':True,'valid_flux':False,'stamp_error':str(e)}
    fl=[]
    for e,q in enumerate(hs):
        x,y=b.pix(q,ra,de);fl.append(aper(ims[e],float(x)-meta[e]['x0'],float(y)-meta[e]['y0']))
    fl=np.asarray(fl,float);valid=bool(np.all(np.isfinite(fl)&(fl>0)))
    rec={'source_id':row['source_id'],'ra':ra,'dec':de,'routed':True,'valid_flux':valid,'gmag':float(row['phot_g_mean_mag']),'frequency_per_day':float(row['frequency']),'period_hours':24/float(row['frequency']),'primary_depth_mag':float(row['derived_primary_ecl_depth']),'primary_duration_phase':float(row['derived_primary_ecl_duration']),'global_ranking':float(row['global_ranking'])}
    if valid:
        z=fl/np.median(fl);rec['euclid_normalized_flux']=[float(v) for v in z];rec['euclid_peak_to_peak_fraction']=float(np.max(z)-np.min(z));rec['euclid_max_abs_excursion']=float(np.max(np.abs(z-1)))
        rec['expected_primary_eclipse_duration_minutes']=float(row['derived_primary_ecl_duration'])*24*60/float(row['frequency'])
    return rec
def main():
    ra,de=CENTER
    q=f"""SELECT TOP 50 gs.source_id,gs.ra,gs.dec,gs.phot_g_mean_mag,e.frequency,e.global_ranking,e.derived_primary_ecl_depth,e.derived_primary_ecl_duration
FROM gaiadr3.vari_eclipsing_binary AS e JOIN gaiadr3.gaia_source AS gs ON e.source_id=gs.source_id
WHERE e.frequency >= 2.0 AND e.derived_primary_ecl_depth >= 0.20
AND e.derived_primary_ecl_duration >= 0.03 AND e.global_ranking >= 0.5
AND gs.phot_g_mean_mag < 18.8
AND 1=CONTAINS(POINT('ICRS',gs.ra,gs.dec),CIRCLE('ICRS',{ra},{de},{RADIUS}))
ORDER BY e.derived_primary_ecl_depth DESC"""
    rows=tap(q);qs=b.map_epoch0();shifts=b.pointing_shifts();tested=[]
    rows=sorted(rows,key=lambda r:(-float(r['derived_primary_ecl_depth']),-float(r['frequency']),float(r['phot_g_mean_mag'])))
    for row in rows:
        x=measure(row,qs,shifts);tested.append(x)
        if sum(bool(v.get('valid_flux')) for v in tested)>=8 or len(tested)>=30:break
    good=[v for v in tested if v.get('valid_flux')]
    out={'success':True,'note':'Gaia DR3 EB selection fixed before Euclid measurements; narrowed TAP cone after server timeout, not based on Euclid outcomes','query':q,'gaia_candidates_returned':len(rows),'tested_count':len(tested),'routed_count':sum(bool(v.get('routed')) for v in tested),'valid_controls':len(good),'tested':tested}
    if good:out['ranked_by_euclid_excursion_for_diagnostic_only']=sorted([{'source_id':v['source_id'],'euclid_max_abs_excursion':v['euclid_max_abs_excursion'],'peak_to_peak':v['euclid_peak_to_peak_fraction'],'period_hours':v['period_hours'],'primary_depth_mag':v['primary_depth_mag'],'expected_primary_eclipse_duration_minutes':v['expected_primary_eclipse_duration_minutes']} for v in good],key=lambda x:x['euclid_max_abs_excursion'],reverse=True)
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
