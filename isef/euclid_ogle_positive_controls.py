#!/usr/bin/env python3
"""OGLE ultra-short-period eclipsing-binary positive controls in Euclid Q2 Field 1.

Uses the published OGLE fixed-width list of 242 P<0.22 d Galactic-bulge
binaries. Selection uses only OGLE coordinates/period/depth plus Euclid focal
plane geometry. Euclid photometry is then measured with the existing fixed
aperture method. Development positive-control test only.
"""
import json,urllib.request,math
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
import euclid_routed_feasibility as b

URL='https://ftp.astrouw.edu.pl/ogle/ogle4/OCVS/blg/short_period_ecl/list.dat';OUT=Path('results/euclid_ogle_positive_controls.json')

def get():
    req=urllib.request.Request(URL,headers={'User-Agent':'isef-euclid-ogle-controls/1.0'})
    with urllib.request.urlopen(req,timeout=60) as r:txt=r.read().decode('ascii',errors='replace')
    rows=[]
    for line in txt.splitlines():
        if len(line)<104:continue
        try:
            sid=line[0:19].strip();rah=int(line[39:41]);ram=int(line[42:44]);ras=float(line[45:50]);sgn=-1 if line[51:52]=='-' else 1;dd=int(line[52:54]);dm=int(line[55:57]);ds=float(line[58:62]);sub=line[63:66].strip();imag=float(line[68:74]);period=float(line[82:92]);depth=float(line[93:98]);ra=15*(rah+ram/60+ras/3600);de=sgn*(dd+dm/60+ds/3600)
            rows.append({'id':sid,'ra':ra,'dec':de,'subtype':sub,'imag':imag,'period_days':period,'period_hours':24*period,'primary_depth_mag':depth})
        except:pass
    return rows

def aper(im,x,y,r=2.2,ri=5,ro=8):
    x0=max(0,int(x)-9);x1=min(im.shape[1],int(x)+10);y0=max(0,int(y)-9);y1=min(im.shape[0],int(y)+10);s=im[y0:y1,x0:x1];yy,xx=np.indices(s.shape);rad=np.hypot(xx+x0-x,yy+y0-y);a=s[rad<=r];n=s[(rad>=ri)&(rad<=ro)]
    if len(a)<8 or len(n)<20:return np.nan
    return float(np.nansum(a-np.nanmedian(n)))
def fast_routes(qs,cent,sh,target):
    ra,de=target;cd=max(math.cos(math.radians(de)),0.2);routes={}
    for g,(dx,dy) in enumerate(sh):
        eq=(ra-dx/(3600*cd),de-dy/3600);dist=np.hypot((cent[:,0]-eq[0])*cd,cent[:,1]-eq[1])*3600;order=np.argsort(dist)[:5];found=None
        for k in order:
            q=b.getq(g,int(k))
            if b.contains(q,ra,de,b.MARGIN):found=int(k);break
        if found is None:return None
        routes[g]=found
    return routes
def measure(row,routes):
    ra=row['ra'];de=row['dec'];hs=b.epoch_headers(routes);ims=[None]*16;meta=[None]*16
    try:
      with ThreadPoolExecutor(max_workers=8) as ex:
        fs=[ex.submit(b.stamp,i,hs[i],ra,de) for i in range(16)]
        for f in as_completed(fs):i,z,m=f.result();ims[i]=z;meta[i]=m
    except Exception as e:return {**row,'valid_flux':False,'error':str(e),'routes':routes}
    fl=[]
    for e,q in enumerate(hs):
        x,y=b.pix(q,ra,de);fl.append(aper(ims[e],float(x)-meta[e]['x0'],float(y)-meta[e]['y0']))
    fl=np.asarray(fl,float);valid=bool(np.all(np.isfinite(fl)&(fl>0)));rec={**row,'valid_flux':valid,'routes':routes}
    if valid:
        z=fl/np.median(fl);rec['normalized_flux']=[float(v) for v in z];rec['max_abs_excursion']=float(np.max(np.abs(z-1)));rec['peak_to_peak_fraction']=float(np.max(z)-np.min(z))
    return rec
def main():
    allrows=get();qs=b.map_epoch0();cent=np.array([q.center for q in qs]);sh=b.pointing_shifts();geom=[]
    # Geometry and OGLE-only ranking are frozen before Euclid pixels are read.
    for r in allrows:
        routes=fast_routes(qs,cent,sh,(r['ra'],r['dec']))
        if routes is not None:geom.append((r,routes))
    geom.sort(key=lambda x:(-x[0]['primary_depth_mag'],x[0]['period_days'],x[0]['imag']))
    tested=[]
    for r,routes in geom[:12]:tested.append(measure(r,routes))
    valid=[x for x in tested if x['valid_flux']]
    out={'success':True,'note':'OGLE ultra-short-period controls selected using published coordinates/period/depth and geometry before Euclid photometry','catalog_url':URL,'catalog_objects':len(allrows),'geometry_controls':len(geom),'tested':tested,'valid_controls':len(valid)}
    if valid:out['diagnostic_ranking_by_euclid_excursion']=sorted([{'id':x['id'],'max_abs_excursion':x['max_abs_excursion'],'peak_to_peak_fraction':x['peak_to_peak_fraction'],'period_hours':x['period_hours'],'primary_depth_mag':x['primary_depth_mag']} for x in valid],key=lambda z:z['max_abs_excursion'],reverse=True)
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
