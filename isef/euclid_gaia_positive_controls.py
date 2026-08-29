#!/usr/bin/env python3
"""Find and test Gaia DR3 short-timescale positive controls in Euclid Q2 Field 1.

This is a non-critical external positive-control lookup. It must fail fast rather
than block the Euclid image experiment if the Gaia TAP service is slow or down.
Gaia labels choose coordinates only; they never tune Euclid thresholds.
"""
import csv, io, json, urllib.parse, urllib.request
from pathlib import Path
import numpy as np
import euclid_routed_feasibility as b

OUT=Path('results/euclid_gaia_positive_controls.json')
TAPS=[
 'https://gea.esac.esa.int/tap-server/tap/sync',
 'https://gaia.aip.de/tap/sync',
]
CENTER=(267.5945,-30.0074); RADIUS=0.20

def tap(adql):
    errs=[]
    body=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'csv','QUERY':adql}).encode()
    for url in TAPS:
        try:
            req=urllib.request.Request(url,data=body,headers={'User-Agent':'isef-euclid-positive-controls/1.1','Content-Type':'application/x-www-form-urlencoded'})
            with urllib.request.urlopen(req,timeout=15) as r: txt=r.read().decode('utf-8',errors='replace')
            if '<VOTABLE' in txt[:500] or '<INFO name="QUERY_STATUS" value="ERROR"' in txt: raise RuntimeError(txt[:1000])
            return list(csv.DictReader(io.StringIO(txt))),url
        except Exception as e: errs.append(f'{url}: {type(e).__name__}: {e}')
    raise RuntimeError('; '.join(errs))

def aperture(im,x,y,r=2.2,ri=5,ro=8):
    x0=max(0,int(x)-9);x1=min(im.shape[1],int(x)+10);y0=max(0,int(y)-9);y1=min(im.shape[0],int(y)+10);s=im[y0:y1,x0:x1];yy,xx=np.indices(s.shape);rad=np.hypot(xx+x0-x,yy+y0-y);a=s[rad<=r];n=s[(rad>=ri)&(rad<=ro)]
    if len(a)<8 or len(n)<20:return np.nan
    return float(np.nansum(a-np.nanmedian(n)))

def route(qs,target,shifts):
    try:return b.route_groups(qs,target,shifts)[0]
    except:return None

def measure_candidate(row,qs,shifts):
    ra=float(row['ra']);de=float(row['dec']);routes=route(qs,(ra,de),shifts)
    if routes is None:return {'source_id':row['source_id'],'ra':ra,'dec':de,'routed':False}
    hs=b.epoch_headers(routes);ims=[None]*16;meta=[None]*16
    from concurrent.futures import ThreadPoolExecutor,as_completed
    with ThreadPoolExecutor(max_workers=8) as ex:
        fs=[ex.submit(b.stamp,i,hs[i],ra,de) for i in range(16)]
        for f in as_completed(fs):i,z,m=f.result();ims[i]=z;meta[i]=m
    cube=np.stack(ims);flux=[]
    for e,q in enumerate(hs):
        x,y=b.pix(q,ra,de);lx=float(x)-meta[e]['x0'];ly=float(y)-meta[e]['y0'];flux.append(aperture(cube[e],lx,ly))
    flux=np.asarray(flux,float);valid=np.all(np.isfinite(flux)&(flux>0))
    rec={'source_id':row['source_id'],'ra':ra,'dec':de,'routed':True,'valid_flux':bool(valid),'phot_g_mean_mag':float(row['phot_g_mean_mag']) if row['phot_g_mean_mag'] else None,'gaia_amplitude_mag':float(row['amplitude_estimate']) if row['amplitude_estimate'] else None,'gaia_frequency_per_day':float(row['frequency']) if row['frequency'] else None}
    if valid:
        norm=flux/np.median(flux);rec['euclid_normalized_flux']=[float(x) for x in norm];rec['euclid_peak_to_peak_fraction']=float(np.max(norm)-np.min(norm));rec['euclid_max_abs_excursion']=float(np.max(np.abs(norm-1)))
    return rec

def main():
    ra,de=CENTER
    adql=f"""SELECT TOP 30 gs.source_id,gs.ra,gs.dec,gs.phot_g_mean_mag,v.amplitude_estimate,v.frequency
FROM gaiadr3.gaia_source AS gs JOIN gaiadr3.vari_short_timescale AS v USING (source_id)
WHERE 1=CONTAINS(POINT('ICRS',gs.ra,gs.dec),CIRCLE('ICRS',{ra},{de},{RADIUS}))
AND gs.phot_g_mean_mag < 19.0 AND v.amplitude_estimate >= 0.10 AND v.frequency >= 4.0
ORDER BY v.amplitude_estimate DESC"""
    try: rows,endpoint=tap(adql)
    except Exception as e:
        out={'success':False,'noncritical':True,'error':f'{type(e).__name__}: {e}','query':adql}
        OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2));return
    qs=b.map_epoch0();shifts=b.pointing_shifts();tested=[]
    rows=sorted(rows,key=lambda r:(-float(r['amplitude_estimate']),float(r['phot_g_mean_mag'])))
    for row in rows:
        rec=measure_candidate(row,qs,shifts);tested.append(rec)
        if sum(1 for x in tested if x.get('routed'))>=5:break
    good=[x for x in tested if x.get('valid_flux')]
    out={'success':True,'endpoint':endpoint,'note':'Gaia labels select coordinates only; fixed Euclid photometry','query':adql,'gaia_candidates_returned':len(rows),'tested':tested,'valid_controls':len(good)}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
