#!/usr/bin/env python3
"""Broad OGLE bulge eclipsing-binary positive controls for Euclid Q2 Field 1.

Fallback/expansion beyond the 242-object ultra-short-period catalog. Downloads
OGLE's published ident.dat + ecl.dat, joins by ID, and filters entirely on OGLE
position/period/depth/brightness before any Euclid pixel is read.
"""
import json,urllib.request,math
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
import euclid_routed_feasibility as b

BASE='https://ftp.astrouw.edu.pl/ogle/ogle4/OCVS/blg/ecl';OUT=Path('results/euclid_ogle_ecl_positive_controls.json')
CENTER=(267.45,-30.05);RAD=0.48

def fetch(name):
    req=urllib.request.Request(f'{BASE}/{name}',headers={'User-Agent':'isef-euclid-ogle-ecl/1.0'})
    with urllib.request.urlopen(req,timeout=180) as r:return r.read().decode('ascii',errors='replace')
def parse_ident(txt):
    d={}
    for line in txt.splitlines():
      if len(line)<48:continue
      try:
        sid=line[0:19].strip();sub=line[21:24].strip();rah=int(line[25:27]);ram=int(line[28:30]);ras=float(line[31:36]);sgn=-1 if line[37:38]=='-' else 1;dd=int(line[38:40]);dm=int(line[41:43]);ds=float(line[44:48]);ra=15*(rah+ram/60+ras/3600);de=sgn*(dd+dm/60+ds/3600);d[sid]={'id':sid,'subtype':sub,'ra':ra,'dec':de}
      except:pass
    return d
def parse_ecl(txt):
    d={}
    for line in txt.splitlines():
      if len(line)<65:continue
      try:
        sid=line[0:19].strip();imag=float(line[21:27]);vm=line[28:34].strip();period=float(line[35:47]);epoch=float(line[49:58]);depth=float(line[60:65]);sec=line[66:71].strip();d[sid]={'imag':imag,'vmag':float(vm) if vm else None,'period_days':period,'period_hours':24*period,'epoch_hjd_minus2450000':epoch,'primary_depth_mag':depth,'secondary_depth_mag':float(sec) if sec else None}
      except:pass
    return d
def ang(ra,de):
    c=math.cos(math.radians((de+CENTER[1])/2));return math.hypot((ra-CENTER[0])*c,de-CENTER[1])
def aper(im,x,y,r=2.2,ri=5,ro=8):
    x0=max(0,int(x)-9);x1=min(im.shape[1],int(x)+10);y0=max(0,int(y)-9);y1=min(im.shape[0],int(y)+10);s=im[y0:y1,x0:x1];yy,xx=np.indices(s.shape);rad=np.hypot(xx+x0-x,yy+y0-y);a=s[rad<=r];n=s[(rad>=ri)&(rad<=ro)]
    if len(a)<8 or len(n)<20:return np.nan
    return float(np.nansum(a-np.nanmedian(n)))
def fast_routes(qs,cent,sh,target):
    ra,de=target;cd=max(math.cos(math.radians(de)),0.2);routes={}
    for g,(dx,dy) in enumerate(sh):
      eq=(ra-dx/(3600*cd),de-dy/3600);dist=np.hypot((cent[:,0]-eq[0])*cd,cent[:,1]-eq[1])*3600
      found=None
      for k in np.argsort(dist)[:5]:
        q=b.getq(g,int(k))
        if b.contains(q,ra,de,b.MARGIN):found=int(k);break
      if found is None:return None
      routes[g]=found
    return routes
def measure(r,routes):
    ra=r['ra'];de=r['dec'];hs=b.epoch_headers(routes);ims=[None]*16;meta=[None]*16
    try:
      with ThreadPoolExecutor(max_workers=8) as ex:
        fs=[ex.submit(b.stamp,i,hs[i],ra,de) for i in range(16)]
        for f in as_completed(fs):i,z,m=f.result();ims[i]=z;meta[i]=m
    except Exception as e:return {**r,'valid_flux':False,'error':str(e)}
    fl=[]
    for e,q in enumerate(hs):
      x,y=b.pix(q,ra,de);fl.append(aper(ims[e],float(x)-meta[e]['x0'],float(y)-meta[e]['y0']))
    fl=np.asarray(fl,float);valid=bool(np.all(np.isfinite(fl)&(fl>0)));rec={**r,'valid_flux':valid}
    if valid:
      z=fl/np.median(fl);rec['normalized_flux']=[float(v) for v in z];rec['max_abs_excursion']=float(np.max(np.abs(z-1)));rec['peak_to_peak_fraction']=float(np.max(z)-np.min(z))
    return rec
def main():
    ident=parse_ident(fetch('ident.dat'));ecl=parse_ecl(fetch('ecl.dat'));rows=[]
    for sid,a in ident.items():
      p=ecl.get(sid)
      if not p:continue
      r={**a,**p}
      if ang(r['ra'],r['dec'])<=RAD and r['period_days']<=0.5 and r['primary_depth_mag']>=0.20 and r['imag']<=19.5:rows.append(r)
    # OGLE-only deterministic priority: deepest, shorter, brighter.
    rows.sort(key=lambda r:(-r['primary_depth_mag'],r['period_days'],r['imag']))
    qs=b.map_epoch0();cent=np.array([q.center for q in qs]);sh=b.pointing_shifts();geom=[]
    for r in rows:
      route=fast_routes(qs,cent,sh,(r['ra'],r['dec']))
      if route is not None:geom.append((r,route))
      if len(geom)>=15:break
    tested=[measure(r,route) for r,route in geom[:10]];valid=[x for x in tested if x['valid_flux']]
    out={'success':True,'note':'broad OGLE EB controls selected solely from published OGLE metadata before Euclid photometry','catalog_ident_url':f'{BASE}/ident.dat','catalog_ecl_url':f'{BASE}/ecl.dat','ident_objects':len(ident),'ecl_objects':len(ecl),'metadata_selected_in_central_field':len(rows),'geometry_controls':len(geom),'tested':tested,'valid_controls':len(valid)}
    if valid:out['diagnostic_ranking_by_euclid_excursion']=sorted([{'id':x['id'],'max_abs_excursion':x['max_abs_excursion'],'peak_to_peak_fraction':x['peak_to_peak_fraction'],'period_hours':x['period_hours'],'primary_depth_mag':x['primary_depth_mag']} for x in valid],key=lambda z:z['max_abs_excursion'],reverse=True)
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
