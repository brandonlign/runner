#!/usr/bin/env python3
"""Metadata-only inventory of fresh known-satellite asteroids in TESS Sectors 14-96.

Purpose: determine whether a genuinely independent post-prime validation reservoir
exists after Stage-4 failed on TSSYS DR1 (Sectors 1-13). No TESS pixels or light-
curve values are opened. JPL SBDB supplies known-satellite metadata and osculating
orbits; tesswcs supplies only camera geometry. All asteroid numbers whose TSSYS
light curves were opened in Stage-3/4 are excluded from the fresh-object count.
"""
from __future__ import annotations
import hashlib, json, math
from pathlib import Path
import numpy as np, requests
from astropy.coordinates import get_body_barycentric_posvel, SkyCoord
from astropy.time import Time
import astropy.units as u
from tesswcs import locate, pointings

OUT=Path('results/tess_binary_postprime_known_geometry_inventory'); OUT.mkdir(parents=True,exist_ok=True)
SECTORS=tuple(range(14,97))
H_MAX=16.5
COND_MAX=5
EPS=np.deg2rad(23.439291111)
SAMPLE_FRACS=(0.15,0.50,0.85)
STAGE3_CONTROLS=Path(__file__).with_name('tess_binary_stage3_null_controls.txt')
STAGE4_POS=Path(__file__).with_name('tess_binary_stage4_validation_positives.txt')
STAGE4_CTRL=Path(__file__).with_name('tess_binary_stage4_validation_controls.txt')
DEV_POS={6764,1803}


def consumed_numbers():
    out=set(DEV_POS)
    for p in (STAGE3_CONTROLS,STAGE4_POS,STAGE4_CTRL): out |= {int(x) for x in p.read_text().split()}
    return out


def sbdb_known_satellite_pool():
    cdata=json.dumps({'AND':[f'H|LE|{H_MAX}',f'condition_code|LE|{COND_MAX}']},separators=(',',':'))
    fields='spkid,pdes,full_name,H,condition_code,epoch,e,a,i,om,w,ma,n,equinox,rot_per,diameter,class'
    params={'fields':fields,'sb-class':'MBA','sb-ns':'n','sb-kind':'a','sb-sat':'true','sb-cdata':cdata,'full-prec':'true'}
    r=requests.get('https://ssd-api.jpl.nasa.gov/sbdb_query.api',params=params,timeout=180); r.raise_for_status(); j=r.json()
    cols=j.get('fields',[]); rows=[]
    for x in j.get('data',[]):
        z=dict(zip(cols,x))
        try:
            for k in ('epoch','e','a','i','om','w','ma','n','H'): z[k]=float(z[k])
            z['number']=int(str(z['pdes']).strip())
        except Exception: continue
        if z.get('equinox') not in (None,'J2000'): continue
        z['hash']=hashlib.sha256(str(z['number']).encode()).hexdigest(); rows.append(z)
    rows.sort(key=lambda z:(z['hash'],z['number']))
    return rows,r.url


def earth_helio_ecliptic_au(jd):
    t=Time(jd,format='jd',scale='tdb'); pe,_=get_body_barycentric_posvel('earth',t); ps,_=get_body_barycentric_posvel('sun',t)
    x,y,z=(pe.xyz-ps.xyz).to_value(u.au)
    return np.array([x,np.cos(EPS)*y+np.sin(EPS)*z,-np.sin(EPS)*y+np.cos(EPS)*z])


def solve_kepler(M,e):
    E=np.asarray(M,float).copy()
    for _ in range(15): E -= (E-e*np.sin(E)-M)/(1-e*np.cos(E))
    return E


def propagate(rows,jd):
    epoch=np.array([z['epoch'] for z in rows]); e=np.array([z['e'] for z in rows]); a=np.array([z['a'] for z in rows])
    inc=np.deg2rad([z['i'] for z in rows]); Om=np.deg2rad([z['om'] for z in rows]); w=np.deg2rad([z['w'] for z in rows])
    M=np.deg2rad((np.array([z['ma'] for z in rows])+np.array([z['n'] for z in rows])*(jd-epoch))%360.0)
    E=solve_kepler(M,e); xo=a*(np.cos(E)-e); yo=a*np.sqrt(np.maximum(0,1-e*e))*np.sin(E)
    cw,sw=np.cos(w),np.sin(w); cO,sO=np.cos(Om),np.sin(Om); ci,si=np.cos(inc),np.sin(inc)
    x=(cO*cw-sO*sw*ci)*xo+(-cO*sw-sO*cw*ci)*yo
    y=(sO*cw+cO*sw*ci)*xo+(-sO*sw+cO*cw*ci)*yo
    z=(sw*si)*xo+(cw*si)*yo
    g=np.vstack([x,y,z])-earth_helio_ecliptic_au(jd)[:,None]
    xq=g[0]; yq=np.cos(EPS)*g[1]-np.sin(EPS)*g[2]; zq=np.sin(EPS)*g[1]+np.cos(EPS)*g[2]
    rr=np.sqrt(xq*xq+yq*yq+zq*zq); ra=np.rad2deg(np.arctan2(yq,xq))%360; dec=np.rad2deg(np.arcsin(zq/rr))
    return ra,dec,rr


def sector_bounds(s):
    q=pointings[pointings['Sector']==s]
    if len(q)!=1: raise RuntimeError(f'sector {s} absent/nonunique in tesswcs pointings')
    return float(q['Start'][0]),float(q['End'][0])


def main():
    rows,url=sbdb_known_satellite_pool(); consumed=consumed_numbers(); hits={i:set() for i in range(len(rows))}; sector_counts={}
    for s in SECTORS:
        start,end=sector_bounds(s); found=set()
        for f in SAMPLE_FRACS:
            jd=start+f*(end-start); ra,dec,_=propagate(rows,jd); crd=SkyCoord(ra=ra*u.deg,dec=dec*u.deg,frame='icrs')
            loc=locate.get_pixel_locations(crd,sector=s).to_pandas()
            if len(loc): found |= {int(x) for x in np.asarray(loc['Target Index'])}
        sector_counts[str(s)]=len(found)
        for i in found: hits[i].add(s)
        print('sector',s,'known-satellite candidates',len(found),flush=True)
    visible=[]
    for i,z in enumerate(rows):
        if not hits[i]: continue
        visible.append({'number':z['number'],'pdes':str(z['pdes']),'full_name':z.get('full_name'),'H':z['H'],
                        'condition_code':z.get('condition_code'),'rot_per_h':z.get('rot_per'),'diameter_km':z.get('diameter'),
                        'sectors':sorted(hits[i]),'consumed_tssys_values':z['number'] in consumed,'hash':z['hash']})
    fresh=[z for z in visible if not z['consumed_tssys_values']]
    fresh.sort(key=lambda z:(z['H'],-len(z['sectors']),z['number']))
    rep={'role':'metadata/geometry-only post-prime known-satellite inventory; no TESS pixels/light curves opened',
         'tess_pixel_values_opened':False,'tess_lightcurve_values_opened':False,
         'sectors':[min(SECTORS),max(SECTORS)],'sector_sample_fractions':list(SAMPLE_FRACS),'H_max':H_MAX,'condition_code_max':COND_MAX,
         'jpl_query_url':url,'known_satellite_pool_n':len(rows),'consumed_number_n':len(consumed),'visible_known_satellite_n':len(visible),
         'fresh_object_n':len(fresh),'fresh_object_sector_n':int(sum(len(z['sectors']) for z in fresh)),
         'sector_candidate_counts':sector_counts,'fresh':[z for z in fresh],'all_visible':visible}
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    (OUT/'fresh_numbers.txt').write_text(''.join(f"{z['number']}\n" for z in fresh))
    print(json.dumps({'known_satellite_pool_n':len(rows),'visible_known_satellite_n':len(visible),'fresh_object_n':len(fresh),
                      'fresh_object_sector_n':rep['fresh_object_sector_n'],'fresh_top50':fresh[:50]},indent=2))

if __name__=='__main__': main()
