#!/usr/bin/env python3
"""Find independent TESS sectors for asteroid 12523 without opening TESS science.

Stage A propagates current JPL osculating elements with a two-body approximation
at five fixed times per TESS sector and uses tesswcs camera geometry. Stage B
runs exact tess-ephem/Horizons only for approximate candidate sectors.
No TESS pixel or light-curve value is accessed.
"""
from __future__ import annotations
import json,math
from pathlib import Path
import numpy as np,requests
import astropy.units as u
from astropy.coordinates import SkyCoord,get_body_barycentric_posvel
from astropy.time import Time
from tesswcs import locate,pointings
from tess_ephem import ephem

OUT=Path('results/tess_binary_12523_sector_inventory');OUT.mkdir(parents=True,exist_ok=True)
TARGET='12523';EPS=np.deg2rad(23.439291111)
SECTORS=range(1,108)
FRACTIONS=np.array([0.05,0.25,0.50,0.75,0.95])


def sbdb_elements():
    r=requests.get('https://ssd-api.jpl.nasa.gov/sbdb.api',params={'sstr':TARGET,'full-prec':'true'},timeout=120);r.raise_for_status();j=r.json()
    els={z['name']:float(z['value']) for z in j['orbit']['elements'] if z.get('value') is not None}
    need=['e','a','i','om','w','ma'];
    if any(k not in els for k in need):raise RuntimeError(f'missing elements {els.keys()}')
    epoch=float(j['orbit']['epoch'])
    # Gaussian gravitational constant, rad/day; infer mean motion from a.
    n_deg=0.9856076686/(els['a']**1.5)
    return {'epoch':epoch,**{k:els[k] for k in need},'n':n_deg},j


def earth_helio_ecliptic(jd):
    t=Time(jd,format='jd',scale='tdb');pe,_=get_body_barycentric_posvel('earth',t);ps,_=get_body_barycentric_posvel('sun',t)
    v=(pe.xyz-ps.xyz).to_value(u.au);x,y,z=v
    return np.vstack([x,np.cos(EPS)*y+np.sin(EPS)*z,-np.sin(EPS)*y+np.cos(EPS)*z])


def solve_kepler(M,e):
    E=np.asarray(M,float).copy()
    for _ in range(12):E-=(E-e*np.sin(E)-M)/(1-e*np.cos(E))
    return E


def propagate(el,jd):
    jd=np.asarray(jd,float);e=el['e'];a=el['a'];inc=np.deg2rad(el['i']);Om=np.deg2rad(el['om']);w=np.deg2rad(el['w'])
    M=np.deg2rad((el['ma']+el['n']*(jd-el['epoch']))%360.0);E=solve_kepler(M,e)
    xo=a*(np.cos(E)-e);yo=a*np.sqrt(1-e*e)*np.sin(E)
    cO,sO=np.cos(Om),np.sin(Om);cw,sw=np.cos(w),np.sin(w);ci,si=np.cos(inc),np.sin(inc)
    x=(cO*cw-sO*sw*ci)*xo+(-cO*sw-sO*cw*ci)*yo
    y=(sO*cw+cO*sw*ci)*xo+(-sO*sw+cO*cw*ci)*yo
    z=(sw*si)*xo+(cw*si)*yo
    g=np.vstack([x,y,z])-earth_helio_ecliptic(jd)
    xq=g[0];yq=np.cos(EPS)*g[1]-np.sin(EPS)*g[2];zq=np.sin(EPS)*g[1]+np.cos(EPS)*g[2]
    rr=np.sqrt(xq*xq+yq*yq+zq*zq);ra=np.rad2deg(np.arctan2(yq,xq))%360;dec=np.rad2deg(np.arcsin(zq/rr))
    return ra,dec,rr


def sector_row(s):
    q=pointings[pointings['Sector']==s]
    if len(q)!=1:return None
    return float(q['Start'][0]),float(q['End'][0])


def approx_candidates(el):
    out=[]
    for s in SECTORS:
        se=sector_row(s)
        if se is None:continue
        start,end=se;times=start+(end-start)*FRACTIONS;ra,dec,dist=propagate(el,times)
        coords=SkyCoord(ra=ra*u.deg,dec=dec*u.deg,frame='icrs')
        loc=locate.get_pixel_locations(coords,sector=s).to_pandas()
        # With one coordinate per sample, Target Index is sample index.
        inds=sorted({int(x) for x in np.asarray(loc['Target Index'])}) if len(loc) else []
        if inds:
            out.append({'sector':s,'start_jd':start,'end_jd':end,'approx_visible_sample_indices':inds,
                        'approx_samples':[{'fraction':float(FRACTIONS[i]),'jd':float(times[i]),'ra_deg':float(ra[i]),'dec_deg':float(dec[i]),'geocentric_au':float(dist[i])} for i in inds]})
    return out


def exact_candidates(approx):
    out=[]
    for q in approx:
        s=q['sector']
        try:
            d=ephem(TARGET,sector=s,time_step=0.5,interpolation_step='6H')
            if d is None or len(d)==0:
                z={'sector':s,'rows':0,'visible':False}
            else:
                vv=np.asarray(d['vmag'],float) if 'vmag' in d.columns else np.full(len(d),np.nan)
                tt=np.asarray(d.index,float)
                cams=sorted({f'{int(a)}/{int(b)}' for a,b in zip(d['camera'],d['ccd'])})
                z={'sector':s,'rows':int(len(d)),'visible':True,'span_d':float(tt.max()-tt.min()) if len(tt)>1 else 0.0,
                   'time_min':float(tt.min()),'time_max':float(tt.max()),'camera_ccd':cams,
                   'vmag_median':float(np.nanmedian(vv)) if np.isfinite(vv).any() else None,
                   'vmag_min':float(np.nanmin(vv)) if np.isfinite(vv).any() else None,
                   'vmag_max':float(np.nanmax(vv)) if np.isfinite(vv).any() else None}
        except Exception as e:
            z={'sector':s,'rows':0,'visible':False,'error':f'{type(e).__name__}: {e}'[:1000]}
        out.append(z);print('sector',s,z,flush=True)
    return out


def main():
    el,jpl=sbdb_elements();approx=approx_candidates(el);exact=exact_candidates(approx)
    usable=[z for z in exact if z.get('visible') and z.get('rows',0)>=10 and z.get('span_d',0)>=5]
    rep={'role':'metadata-only independent-sector inventory for post-null candidate 12523','target':'(12523) 1998 HH100',
         'tess_pixel_values_opened':False,'tess_lightcurve_values_opened':False,'approx_method':'two-body JPL osculating propagation, five fixed samples/sector, tesswcs geometry',
         'jpl_elements':el,'approx_candidate_n':len(approx),'approx_candidates':approx,'exact_tess_ephem':exact,'usable_exact_sectors':usable,
         'jpl_object':jpl.get('object')}
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'approx_candidate_sectors':[z['sector'] for z in approx],'exact_visible':[z for z in exact if z.get('visible')],'usable':usable},indent=2))

if __name__=='__main__':main()
