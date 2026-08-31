#!/usr/bin/env python3
"""Header-only CTM WCS probe for frozen C/2025 R3 geometry.

No target science/uncertainty pixel is decoded. Three fixed v0l epochs are used
to verify that matched-Horizons nucleus coordinates and local anti-solar PAs map
sensibly through the delivered alternate celestial WCS (key A).
"""
from __future__ import annotations
import json,time
from pathlib import Path
import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.time import Time
from astropy.wcs import WCS
from astroquery.jplhorizons import Horizons

OUT=Path('results/punch_r3_wcs_geometry_probe');OUT.mkdir(parents=True,exist_ok=True)
ROOT='https://umbra.nascom.nasa.gov/punch/2/CTM/2026/'
SAMPLES=[
 ('2026-04-21T18:00:29Z','04/21/PUNCH_L2_CTM_20260421180029_v0l.fits'),
 ('2026-04-21T23:20:29Z','04/21/PUNCH_L2_CTM_20260421232029_v0l.fits'),
 ('2026-04-22T11:52:29Z','04/22/PUNCH_L2_CTM_20260422115229_v0l.fits'),
]

def eph(objid,id_type,t):
    last=None
    for k in range(5):
        try:return Horizons(id=objid,id_type=id_type,location='500@399',epochs=Time(t).jd).ephemerides(quantities='1')[0]
        except Exception as e:last=e;time.sleep(2*(k+1))
    raise last

def main():
    rows=[]
    for stamp,rel in SAMPLES:
        c=eph('C/2025 R3','designation',stamp);s=eph('10',None,stamp)
        comet=SkyCoord(float(c['RA'])*u.deg,float(c['DEC'])*u.deg,frame='icrs')
        sun=SkyCoord(float(s['RA'])*u.deg,float(s['DEC'])*u.deg,frame='icrs')
        elong=float(comet.separation(sun).deg)
        anti=float((comet.position_angle(sun).deg+180)%360)
        # A tiny 0.25-degree sky-plane step fixes the local downstream tangent.
        downstream=comet.directional_offset_by(anti*u.deg,.25*u.deg)
        url=ROOT+rel
        with fits.open(url,use_fsspec=True,fsspec_kwargs={'block_size':1024*1024},memmap=False,lazy_load_hdus=True) as h:
            hdr=h[1].header.copy()
        w=WCS(hdr,key='A')
        x,y=w.world_to_pixel(comet);xd,yd=w.world_to_pixel(downstream)
        dx=float(xd-x);dy=float(yd-y);norm=(dx*dx+dy*dy)**.5
        radius=((float(x)-2047.0)**2+(float(y)-2047.0)**2)**.5
        rows.append({'timestamp':stamp,'url':url,'elongation_deg':elong,'antisolar_pa_deg':anti,
          'nucleus_pixel_0based':[float(x),float(y)],'radius_from_crpix_approx_px':radius,
          'expected_radius_from_elongation_px':elong/.0225,
          'downstream_unit_pixel':[dx/norm,dy/norm],
          'ctypeA':[hdr.get('CTYPE1A'),hdr.get('CTYPE2A')],'crvalA':[hdr.get('CRVAL1A'),hdr.get('CRVAL2A')],
          'pcA':[hdr.get('PC1_1A'),hdr.get('PC1_2A'),hdr.get('PC2_1A'),hdr.get('PC2_2A')]})
    # Conservative sanity: mapped target must be inside image and radial mapping
    # should be within 10% of small-angle elongation / nominal sampling.
    ok=True
    for r in rows:
        x,y=r['nucleus_pixel_0based'];exp=r['expected_radius_from_elongation_px'];got=r['radius_from_crpix_approx_px']
        ok &= (0<=x<4096 and 0<=y<4096 and abs(got-exp)/exp<.10)
    report={'information_barrier':'target FITS headers + matched Horizons only; no target array pixels decoded','rows':rows,'gate':'PASS' if ok else 'FAIL'}
    (OUT/'summary.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report,indent=2,sort_keys=True));return 0 if ok else 3
if __name__=='__main__':raise SystemExit(main())
