#!/usr/bin/env python3
"""Gaia DR3 short-timescale positive controls for Euclid Q2 Field 1.

External TAP lookup is non-critical and fails fast. Gaia labels select coordinates
only; they do not tune Euclid thresholds. Both CSV and standards-compliant
VOTable TAP responses are accepted, and Euclid positions use exact WCS routing.
"""
import csv, io, json, urllib.parse, urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
from astropy.table import Table
import euclid_routed_feasibility as b
import euclid_exact_routing as er

OUT=Path('results/euclid_gaia_positive_controls.json')
TAPS=['https://gea.esac.esa.int/tap-server/tap/sync','https://gaia.aip.de/tap/sync']
CENTER=(267.5945,-30.0074);RADIUS=0.20

def parse_response(raw):
    txt=raw.decode('utf-8',errors='replace')
    if 'value="ERROR"' in txt[:4000]:raise RuntimeError(txt[:1500])
    if '<VOTABLE' in txt[:1000]:
        t=Table.read(io.BytesIO(raw),format='votable');rows=[]
        for rr in t:
            d={}
            for n in t.colnames:
                v=rr[n];d[n]='' if np.ma.is_masked(v) else str(v)
            rows.append(d)
        return rows
    return list(csv.DictReader(io.StringIO(txt)))

def tap(adql):
    errs=[];body=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'csv','QUERY':adql}).encode()
    for url in TAPS:
        try:
            req=urllib.request.Request(url,data=body,headers={'User-Agent':'isef-euclid-positive-controls/1.3','Content-Type':'application/x-www-form-urlencoded'})
            with urllib.request.urlopen(req,timeout=15) as r:raw=r.read()
            return parse_response(raw),url
        except Exception as e:errs.append(f'{url}: {type(e).__name__}: {e}')
    raise RuntimeError('; '.join(errs))

def aperture(im,x,y,r=2.2,ri=5,ro=8):
    x0=max(0,int(x)-9);x1=min(im.shape[1],int(x)+10);y0=max(0,int(y)-9);y1=min(im.shape[0],int(y)+10);s=im[y0:y1,x0:x1];yy,xx=np.indices(s.shape);rad=np.hypot(xx+x0-x,yy+y0-y);a=s[rad<=r];n=s[(rad>=ri)&(rad<=ro)]
    if len(a)<8 or len(n)<20:return np.nan
    return float(np.nansum(a-np.nanmedian(n)))

def measure_candidate(row,groupmaps):
    ra=float(row['ra']);de=float(row['dec'])
    try:routes,diag=er.route_target(groupmaps,(ra,de))
    except Exception as e:return {'source_id':row['source_id'],'ra':ra,'dec':de,'routed':False,'route_error':str(e)}
    hs=b.epoch_headers(routes);ims=[None]*16;meta=[None]*16
    with ThreadPoolExecutor(max_workers=8) as ex:
        fs=[ex.submit(er.stamp,i,hs[i],ra,de) for i in range(16)]
        for f in as_completed(fs):i,z,m=f.result();ims[i]=z;meta[i]=m
    cube=np.stack(ims);flux=[]
    for e,q in enumerate(hs):
        x,y=b.pix(q,ra,de);lx=float(np.asarray(x))-meta[e]['x0'];ly=float(np.asarray(y))-meta[e]['y0'];flux.append(aperture(cube[e],lx,ly))
    flux=np.asarray(flux,float);valid=np.all(np.isfinite(flux)&(flux>0));rec={'source_id':row['source_id'],'ra':ra,'dec':de,'routed':True,'route_diagnostics':diag,'valid_flux':bool(valid),'phot_g_mean_mag':float(row['phot_g_mean_mag']) if row['phot_g_mean_mag'] else None,'gaia_amplitude_mag':float(row['amplitude_estimate']) if row['amplitude_estimate'] else None,'gaia_frequency_per_day':float(row['frequency']) if row['frequency'] else None}
    if valid:
        norm=flux/np.median(flux);rec['euclid_normalized_flux']=[float(x) for x in norm];rec['euclid_peak_to_peak_fraction']=float(np.max(norm)-np.min(norm));rec['euclid_max_abs_excursion']=float(np.max(np.abs(norm-1)))
    return rec

def main():
    ra,de=CENTER
    # vari_short_timescale already carries source_id, coordinates and G magnitude;
    # querying it directly avoids TAP-dependent JOIN/USING syntax failures.
    adql=f"""SELECT TOP 30 source_id,ra,dec,phot_g_mean_mag,amplitude_estimate,frequency
FROM gaiadr3.vari_short_timescale
WHERE 1=CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',{ra},{de},{RADIUS}))
AND phot_g_mean_mag < 19.0 AND amplitude_estimate >= 0.10 AND frequency >= 4.0
ORDER BY amplitude_estimate DESC"""
    try:rows,endpoint=tap(adql)
    except Exception as e:
        out={'success':False,'noncritical':True,'error':f'{type(e).__name__}: {e}','query':adql};OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2));return
    rows=sorted(rows,key=lambda r:(-float(r['amplitude_estimate']),float(r['phot_g_mean_mag'])));groupmaps=er.map_groups();tested=[]
    for row in rows:
        rec=measure_candidate(row,groupmaps);tested.append(rec)
        if sum(1 for x in tested if x.get('routed'))>=5:break
    good=[x for x in tested if x.get('valid_flux')]
    out={'success':len(good)>0,'endpoint':endpoint,'note':'Gaia labels select coordinates only; fixed Euclid photometry and exact WCS routing','query':adql,'gaia_candidates_returned':len(rows),'tested':tested,'valid_controls':len(good)}
    if good:out['control_excursions']=[{'source_id':x['source_id'],'gaia_amplitude_mag':x['gaia_amplitude_mag'],'gaia_frequency_per_day':x['gaia_frequency_per_day'],'euclid_max_abs_excursion':x['euclid_max_abs_excursion'],'euclid_peak_to_peak_fraction':x['euclid_peak_to_peak_fraction']} for x in good]
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
