#!/usr/bin/env python3
"""Find and test Gaia DR3 short-timescale positive controls in Euclid Q2 Field 1.

The Gaia label is used only to choose positive-control coordinates, never to tune
Euclid event thresholds. Candidates are required to be bright, high-amplitude,
and have Gaia frequency corresponding to periods short enough that a ~2 h Euclid
sequence has a reasonable chance of showing measurable variation.
"""
import csv, io, json, math, urllib.parse, urllib.request
from pathlib import Path
import numpy as np
import euclid_routed_feasibility as b

OUT=Path('results/euclid_gaia_positive_controls.json')
TAP='https://gea.esac.esa.int/tap-server/tap/sync'
CENTER=(267.5945,-30.0074); RADIUS=0.45

def tap(adql):
    body=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'csv','QUERY':adql}).encode()
    req=urllib.request.Request(TAP,data=body,headers={'User-Agent':'isef-euclid-positive-controls/1.0','Content-Type':'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req,timeout=90) as r: txt=r.read().decode('utf-8',errors='replace')
    if '<VOTABLE' in txt[:500] or '<INFO name="QUERY_STATUS" value="ERROR"' in txt: raise RuntimeError(txt[:2000])
    return list(csv.DictReader(io.StringIO(txt)))

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
        norm=flux/np.median(flux);rec['euclid_normalized_flux']=[float(x) for x in norm];rec['euclid_peak_to_peak_fraction']=float(np.max(norm)-np.min(norm));rec['euclid_max_abs_excursion']=float(np.max(np.abs(norm-1)));rec['euclid_group_medians']=[float(np.median(norm[g::4])) for g in range(4)]
    return rec

def main():
    ra,de=CENTER
    adql=f"""SELECT TOP 80 gs.source_id,gs.ra,gs.dec,gs.phot_g_mean_mag,v.amplitude_estimate,v.frequency
FROM gaiadr3.gaia_source AS gs JOIN gaiadr3.vari_short_timescale AS v USING (source_id)
WHERE 1=CONTAINS(POINT('ICRS',gs.ra,gs.dec),CIRCLE('ICRS',{ra},{de},{RADIUS}))
AND gs.phot_g_mean_mag < 19.0 AND v.amplitude_estimate >= 0.10 AND v.frequency IS NOT NULL AND v.frequency >= 4.0
ORDER BY v.amplitude_estimate DESC"""
    rows=tap(adql);qs=b.map_epoch0();shifts=b.pointing_shifts();tested=[]
    # Prefer high amplitude and bright controls. Stop after 8 routed objects to bound I/O.
    rows=sorted(rows,key=lambda r:(-float(r['amplitude_estimate']),float(r['phot_g_mean_mag'])))
    for row in rows:
        rec=measure_candidate(row,qs,shifts);tested.append(rec)
        if sum(1 for x in tested if x.get('routed'))>=8:break
    good=[x for x in tested if x.get('valid_flux')]
    out={'success':True,'note':'Gaia labels select coordinates only; Euclid light curves are measured blindly with fixed aperture method','query':adql,'gaia_candidates_returned':len(rows),'tested':tested,'valid_controls':len(good)}
    if good:
        out['max_euclid_excursion_controls']=sorted([{'source_id':x['source_id'],'max_abs_excursion':x['euclid_max_abs_excursion'],'peak_to_peak':x['euclid_peak_to_peak_fraction'],'gaia_amplitude_mag':x['gaia_amplitude_mag'],'gaia_frequency_per_day':x['gaia_frequency_per_day']} for x in good],key=lambda z:z['max_abs_excursion'],reverse=True)
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
