#!/usr/bin/env python3
"""Identify which published Fielder GC candidate anchors the published Oyashio track.

External positive-control bookkeeping only. Opens only UGC9050-Dw1 GO-16890
F814W combined DRC, reads its WCS, converts the two published stream-track
endpoints to sky coordinates, and compares them to the public Fielder GC
candidate table shipped in the Holm et al. public repository. No MATLAS field
or null-control image is queried/opened.
"""
from __future__ import annotations
import csv, io, json
from pathlib import Path
import numpy as np, requests
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
import astropy.units as u
import matlas_oyashio_blind_detector_pilot as p

OUT=Path('results/oyashio_gc_anchor_identification');OUT.mkdir(parents=True,exist_ok=True)
GC_URL='https://raw.githubusercontent.com/juliekh/extragalacticGCstream/main/data_files/Fielder_GCCs_table.csv'

def load_gc_table():
    r=requests.get(GC_URL,timeout=30);r.raise_for_status();txt=r.text.lstrip('\ufeff')
    rows=[]
    for z in csv.DictReader(io.StringIO(txt)):
        rows.append({'id':int(z['No.']),'ra_deg':float(z['RA (deg)']),'dec_deg':float(z['Dec (deg)']),
                     'f555w':float(z['F555W (mag)']),'f814w':float(z['F814W (mag)']),
                     'v_minus_i':float(z['(V-I) (mag)']),'c_4_8':float(z['c_4-8']),'d_cen_kpc':float(z['D_cen (kpc)'])})
    return rows

def science_wcs(path):
    # Use the actual FITS SCI header. p.load_sci intentionally returns only a
    # JSON-safe metadata summary, which is unsuitable for WCS construction.
    with fits.open(path,memmap=False) as h:
        idx=None
        for j,hd in enumerate(h):
            if getattr(hd,'data',None) is not None and np.ndim(hd.data)==2:
                idx=j;break
        if idx is None: raise RuntimeError(f'No 2-D science image in {path.name}')
        return WCS(h[idx].header,relax=True).celestial,idx,list(h[idx].data.shape)

def main():
    rows=p.query_products();row=next(r for r in rows if r['filename']==p.EXPECTED_COMBINED)
    path=p.download_one(row);w,sci_hdu,shape=science_wcs(path)
    raw,_=p.truth_points_dense()
    endpoints=[raw[0],raw[-1]]
    gcs=load_gc_table();gcsky=SkyCoord([x['ra_deg'] for x in gcs]*u.deg,[x['dec_deg'] for x in gcs]*u.deg)
    out=[]
    for k,(x,y) in enumerate(endpoints):
        sc=w.pixel_to_world(float(x),float(y))
        if not hasattr(sc,'ra'): sc=SkyCoord(sc[0].ra,sc[0].dec)
        sep=sc.separation(gcsky).arcsec;ii=int(np.argmin(sep));g=dict(gcs[ii]);g['separation_arcsec']=float(sep[ii])
        out.append({'endpoint_index':k,'x_px':float(x),'y_px':float(y),'ra_deg':float(sc.ra.deg),'dec_deg':float(sc.dec.deg),'nearest_gc':g})
    # The anchor is defined as the endpoint with the smaller nearest-GC separation.
    anchor=min(out,key=lambda z:z['nearest_gc']['separation_arcsec'])
    rep={'role':'external positive-control anchor identification only','matlas_target_science_values_opened':False,
         'information_barrier':'Only GO-16890 Oyashio F814W combined DRC WCS/image loaded',
         'image':{'filename':row['filename'],'science_hdu':sci_hdu,'shape':shape},
         'gc_catalog_source':GC_URL,'gc_catalog_n':len(gcs),'track_endpoints':out,'identified_anchor':anchor,
         'anchor_pass':bool(anchor['nearest_gc']['separation_arcsec']<=0.25)}
    path.unlink(missing_ok=True);(OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    print(json.dumps(rep,indent=2,sort_keys=True))
    raise SystemExit(0 if rep['anchor_pass'] else 3)
if __name__=='__main__':main()
