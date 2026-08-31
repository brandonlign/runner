#!/usr/bin/env python3
"""Geometry-first metadata screen for TESS Cycle-8 asteroid visibility.

No TESS pixels or light-curve values are opened. JPL SBDB osculating elements
are propagated with a two-body approximation to each sector midpoint, then
`tesswcs` is used only to identify objects geometrically inside the cameras.
Exact tess-ephem confirmation is a later metadata-only stage.
"""
from __future__ import annotations
import json,math,hashlib
from pathlib import Path
import numpy as np,requests
from astropy.coordinates import get_body_barycentric_posvel,SkyCoord
from astropy.time import Time
import astropy.units as u
from tesswcs import locate, pointings

OUT=Path('results/tess_binary_year8_geometry_screen');OUT.mkdir(parents=True,exist_ok=True)
SECTORS=(97,98)
H_MAX=14.5
I_MIN_DEG=8.0
COND_MAX=3
EPS=np.deg2rad(23.439291111)


def sbdb_pool():
    cdata=json.dumps({'AND':[f'H|LE|{H_MAX}',f'i|GE|{I_MIN_DEG}',f'condition_code|LE|{COND_MAX}']},separators=(',',':'))
    fields='spkid,pdes,full_name,H,condition_code,epoch,e,a,i,om,w,ma,n,equinox,rot_per,diameter,class'
    params={'fields':fields,'sb-class':'MBA','sb-ns':'n','sb-kind':'a','sb-sat':'false','sb-cdata':cdata,'full-prec':'true'}
    r=requests.get('https://ssd-api.jpl.nasa.gov/sbdb_query.api',params=params,timeout=180);r.raise_for_status();j=r.json()
    cols=j['fields'];rows=[]
    for x in j.get('data',[]):
        z=dict(zip(cols,x))
        try:
            for k in ('epoch','e','a','i','om','w','ma','n','H'):z[k]=float(z[k])
        except Exception:continue
        if z.get('equinox') not in (None,'J2000'):
            continue
        z['hash']=hashlib.sha256(str(z['pdes']).encode()).hexdigest();rows.append(z)
    rows.sort(key=lambda z:(z['hash'],str(z['pdes'])))
    return rows,r.url


def earth_helio_ecliptic_au(jd):
    t=Time(jd,format='jd',scale='tdb');pe,_=get_body_barycentric_posvel('earth',t);ps,_=get_body_barycentric_posvel('sun',t)
    v=(pe.xyz-ps.xyz).to_value(u.au)
    x,y,z=v
    return np.array([x, np.cos(EPS)*y+np.sin(EPS)*z, -np.sin(EPS)*y+np.cos(EPS)*z])


def solve_kepler(M,e):
    E=np.asarray(M,float).copy()
    for _ in range(12):
        d=(E-e*np.sin(E)-M)/(1-e*np.cos(E));E-=d
    return E


def propagate(rows,jd):
    epoch=np.array([z['epoch'] for z in rows]);e=np.array([z['e'] for z in rows]);a=np.array([z['a'] for z in rows])
    inc=np.deg2rad([z['i'] for z in rows]);Om=np.deg2rad([z['om'] for z in rows]);w=np.deg2rad([z['w'] for z in rows])
    M=np.deg2rad((np.array([z['ma'] for z in rows])+np.array([z['n'] for z in rows])*(jd-epoch))%360.0)
    E=solve_kepler(M,e);xo=a*(np.cos(E)-e);yo=a*np.sqrt(np.maximum(0,1-e*e))*np.sin(E)
    cw,sw=np.cos(w),np.sin(w);cO,sO=np.cos(Om),np.sin(Om);ci,si=np.cos(inc),np.sin(inc)
    # Rz(Omega) Rx(i) Rz(omega) applied to orbital-plane vector.
    x=(cO*cw-sO*sw*ci)*xo+(-cO*sw-sO*cw*ci)*yo
    y=(sO*cw+cO*sw*ci)*xo+(-sO*sw+cO*cw*ci)*yo
    z=(sw*si)*xo+(cw*si)*yo
    earth=earth_helio_ecliptic_au(jd)[:,None];g=np.vstack([x,y,z])-earth
    # ecliptic -> ICRS-equatorial J2000 axes
    xq=g[0];yq=np.cos(EPS)*g[1]-np.sin(EPS)*g[2];zq=np.sin(EPS)*g[1]+np.cos(EPS)*g[2]
    rr=np.sqrt(xq*xq+yq*yq+zq*zq);ra=np.rad2deg(np.arctan2(yq,xq))%360;dec=np.rad2deg(np.arcsin(zq/rr))
    return ra,dec,rr


def sector_mid(s):
    q=pointings[pointings['Sector']==s]
    if len(q)!=1:raise RuntimeError(f'sector {s} not uniquely in tesswcs pointings')
    start=float(q['Start'][0]);end=float(q['End'][0]);return start,end,0.5*(start+end)


def main():
    rows,url=sbdb_pool();per=[];union=set()
    for s in SECTORS:
        start,end,mid=sector_mid(s);ra,dec,dist=propagate(rows,mid);crd=SkyCoord(ra=ra*u.deg,dec=dec*u.deg,frame='icrs')
        loc=locate.get_pixel_locations(crd,sector=s).to_pandas()
        idx=sorted({int(x) for x in np.asarray(loc['Target Index'])}) if len(loc) else []
        candidates=[]
        for i in idx:
            z=rows[i];union.add(i);candidates.append({'pool_index':i,'pdes':str(z['pdes']),'full_name':z['full_name'],'H':z['H'],'hash':z['hash'],
                'approx_ra_deg':float(ra[i]),'approx_dec_deg':float(dec[i]),'approx_geocentric_au':float(dist[i])})
        per.append({'sector':s,'start_jd':start,'end_jd':end,'mid_jd':mid,'approx_fov_candidate_n':len(candidates),'candidates':candidates})
        print('sector',s,'candidates',len(candidates),flush=True)
    union_rows=[rows[i] for i in sorted(union,key=lambda i:(rows[i]['hash'],str(rows[i]['pdes'])))]
    rep={'role':'metadata/geometry-only Cycle-8 FOV screen','tess_pixel_values_opened':False,'tess_lightcurve_values_opened':False,
         'approximation':'JPL SBDB osculating two-body propagation to sector midpoint; Earth heliocentric vector from Astropy; tesswcs camera geometry',
         'jpl_query_url':url,'pool_n':len(rows),'sectors':per,'union_candidate_n':len(union_rows),
         'union_candidates':[{'pdes':str(z['pdes']),'full_name':z['full_name'],'H':z['H'],'hash':z['hash']} for z in union_rows]}
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    (OUT/'candidate_ids.txt').write_text(''.join(str(z['pdes'])+'\n' for z in union_rows))
    print(json.dumps({'pool_n':len(rows),'per_sector':{str(q['sector']):q['approx_fov_candidate_n'] for q in per},'union_candidate_n':len(union_rows),'first20':[z['pdes'] for z in union_rows[:20]]},indent=2))

if __name__=='__main__':main()
