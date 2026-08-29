#!/usr/bin/env python3
"""Euclid Q2 Stage-0 photometric feasibility with cross-quadrant routing.

The VIS science MEF has a fixed layout verified from the released file size:
primary header 17280 bytes followed by 144 identical SCI extensions. Each SCI
extension has an 8640-byte header and 2048x2066 float32 data padded to FITS
blocks, giving a 16,934,400-byte extension stride.

We map all 144 quadrant WCS headers for exposure 0 concurrently, choose a
central sky target, infer the physical quadrant needed for each of the four
pointing groups from their measured global shifts, validate the routed quadrant
against representative/all epochs, then range-read a compact stamp from each of
all 16 exposures. Bright-star differential aperture photometry supplies a first
repeatability floor. This is a Stage-0 feasibility diagnostic, not the final
crowded-field/PSF method.
"""
from __future__ import annotations
import json, math, re, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from astropy.wcs import WCS
from photutils.detection import DAOStarFinder

BASE='https://irsa.ipac.caltech.edu/data/Euclid/q2/data'
FILES=[
'EUC_VIS_SWL-DET-067070-00-1__20250621T020155.487037Z_sci.fits','EUC_VIS_SWL-DET-067070-01-1__20250621T020156.049078Z_sci.fits','EUC_VIS_SWL-DET-067070-02-1__20250621T020157.327960Z_sci.fits','EUC_VIS_SWL-DET-067070-03-1__20250621T020200.784839Z_sci.fits','EUC_VIS_SWL-DET-067070-04-1__20250621T020159.310075Z_sci.fits','EUC_VIS_SWL-DET-067070-05-1__20250621T020148.061975Z_sci.fits','EUC_VIS_SWL-DET-067070-06-1__20250621T020208.198375Z_sci.fits','EUC_VIS_SWL-DET-067070-07-1__20250621T020158.860635Z_sci.fits','EUC_VIS_SWL-DET-067070-08-1__20250621T020202.737416Z_sci.fits','EUC_VIS_SWL-DET-067070-09-1__20250621T020203.034854Z_sci.fits','EUC_VIS_SWL-DET-067070-10-1__20250621T020153.520357Z_sci.fits','EUC_VIS_SWL-DET-067070-11-1__20250621T020206.950527Z_sci.fits','EUC_VIS_SWL-DET-067070-12-1__20250621T020154.990859Z_sci.fits','EUC_VIS_SWL-DET-067070-13-1__20250621T020149.508409Z_sci.fits','EUC_VIS_SWL-DET-067070-14-1__20250621T020202.468375Z_sci.fits','EUC_VIS_SWL-DET-067070-15-1__20250621T020200.444396Z_sci.fits']
URLS=[f'{BASE}/{f}' for f in FILES]
OUT=Path('results/euclid_routed_feasibility.json');NPZ=Path('results/euclid_routed_stamps.npz')
BLOCK=2880;PRIMARY=17280;HDR=8640;NX=2048;NY=2066;BPP=4;DATA=NX*NY*BPP;PAD_DATA=math.ceil(DATA/BLOCK)*BLOCK;STRIDE=HDR+PAD_DATA
STAMP=128;HALF=STAMP//2;MARGIN=HALF+12
assert PRIMARY+144*STRIDE==2438570880

def rr(url,a,b,timeout=45):
    n=b-a+1;req=urllib.request.Request(url,headers={'Range':f'bytes={a}-{b}','User-Agent':'isef-euclid-routed/1.0'})
    with urllib.request.urlopen(req,timeout=timeout) as r:data=r.read(n+1);h=dict(r.headers.items());s=r.status
    if s!=206 or len(data)!=n:raise RuntimeError(f'range failure HTTP={s} got={len(data)} want={n}')
    return data,h

def val(raw):
    raw=raw.strip();q=False;cut=len(raw)
    for i,ch in enumerate(raw):
        if ch=="'":q=not q
        elif ch=='/' and not q:cut=i;break
    s=raw[:cut].strip()
    if not s:return None
    if s.startswith("'"):
        m=re.match(r"'((?:''|[^'])*)'",s);return m.group(1).replace("''","'").strip() if m else s.strip("'").strip()
    if s=='T':return True
    if s=='F':return False
    try:return float(s.replace('D','E')) if any(c in s for c in '.EDed') else int(s)
    except:return s

def parse(buf):
    d={};cards=[];ended=False
    for i in range(0,len(buf),80):
        c=buf[i:i+80].decode('ascii',errors='replace');cards.append(c);k=c[:8].strip()
        if k=='END':ended=True;break
        if len(c)>=10 and c[8:10]=='= ':d[k]=val(c[10:])
    if not ended:raise RuntimeError('no END in fixed header')
    return d,cards

def offset(k):return PRIMARY+k*STRIDE
@dataclass
class Q:
    k:int;name:str;raw:dict;cards:list
    @property
    def w(self):return WCS(fits.Header.fromstring(''.join(self.cards),sep=''),relax=True)
    @property
    def center(self):
        r,d=self.w.pixel_to_world_values(NX/2,NY/2);return float(r),float(d)

def getq(epoch,k):
    b,_=rr(URLS[epoch],offset(k),offset(k)+HDR-1);h,c=parse(b)
    if int(h.get('NAXIS1',0))!=NX or int(h.get('NAXIS2',0))!=NY or int(h.get('BITPIX',0))!=-32:raise RuntimeError(f'unexpected SCI geometry epoch={epoch} k={k} {h.get("EXTNAME")}')
    return Q(k,str(h.get('EXTNAME','')),h,c)

def map_epoch0():
    qs=[None]*144
    with ThreadPoolExecutor(max_workers=32) as ex:
        fs={ex.submit(getq,0,k):k for k in range(144)}
        for f in as_completed(fs):qs[fs[f]]=f.result()
    return qs

def dist_arcsec(a,b,dec):
    return math.hypot((a[0]-b[0])*math.cos(math.radians(dec))*3600,(a[1]-b[1])*3600)

def pix(q,ra,de):return q.w.world_to_pixel_values(ra,de)
def contains(q,ra,de,margin=MARGIN):
    x,y=pix(q,ra,de);return np.isfinite(x) and np.isfinite(y) and margin<=x<NX-margin and margin<=y<NY-margin

def choose_target(qs):
    centers=np.array([q.center for q in qs]);med=(float(np.median(centers[:,0])),float(np.median(centers[:,1])))
    # Prefer a quadrant center near the focal-plane median but not one of the few closest if that center lies beside a detector gap.
    order=sorted(range(144),key=lambda k:dist_arcsec(qs[k].center,med,med[1]))
    for k in order[:20]:
        ra,de=qs[k].center
        # Target is exactly at a quadrant center, maximizing margin in epoch 0.
        if contains(qs[k],ra,de,MARGIN+100):return k,ra,de,med
    k=order[0];ra,de=qs[k].center;return k,ra,de,med

def pointing_shifts():
    # Same physical quadrant k=0 is enough to measure the global dither shift.
    reps=[getq(g,0) for g in range(4)];r0,d0=reps[0].center;cd=math.cos(math.radians(d0));out=[]
    for q in reps:
        r,d=q.center;out.append(((r-r0)*cd*3600,(d-d0)*3600))
    return out

def route_groups(qs,target,shifts):
    ra,de=target;cd=math.cos(math.radians(de));routes={};diagnostics=[]
    for g,(sx,sy) in enumerate(shifts):
        # If a physical quadrant moves by (+sx,+sy), the exposure-0 footprint that maps onto our fixed sky target is target-shift.
        eq=(ra-sx/(cd*3600),de-sy/3600)
        nearest=sorted(range(144),key=lambda k:dist_arcsec(qs[k].center,eq,de))[:8]
        chosen=None
        for k in nearest:
            q=getq(g,k)
            x,y=pix(q,ra,de)
            diagnostics.append({'group':g,'candidate_k':k,'extname':q.name,'x':float(x),'y':float(y),'inside':bool(contains(q,ra,de))})
            if contains(q,ra,de):chosen=k;break
        if chosen is None:raise RuntimeError(f'no routed quadrant for group {g}; nearest={nearest}')
        routes[g]=chosen
    return routes,diagnostics

def epoch_headers(routes):
    hs=[None]*16
    with ThreadPoolExecutor(max_workers=16) as ex:
        fs={ex.submit(getq,i,routes[i%4]):i for i in range(16)}
        for f in as_completed(fs):hs[fs[f]]=f.result()
    return hs

def stamp(epoch,q,ra,de):
    x,y=pix(q,ra,de);cx=int(round(x));cy=int(round(y));x0=cx-HALF;y0=cy-HALF
    if x0<0 or y0<0 or x0+STAMP>NX or y0+STAMP>NY:raise RuntimeError(f'stamp outside routed quadrant epoch={epoch} {q.name} x={x} y={y}')
    data0=offset(q.k)+HDR;start=data0+y0*NX*BPP;end=data0+(y0+STAMP)*NX*BPP-1;raw,_=rr(URLS[epoch],start,end,90)
    rows=np.frombuffer(raw,dtype='>f4').reshape(STAMP,NX);z=rows[:,x0:x0+STAMP].astype(np.float32)
    return epoch,z,{'x0':x0,'y0':y0,'x':float(x),'y':float(y),'extname':q.name,'k':q.k}
def aperture(im,x,y,r=2.5,ri=5,ro=8):
    x0=max(0,int(x)-9);x1=min(STAMP,int(x)+10);y0=max(0,int(y)-9);y1=min(STAMP,int(y)+10);s=im[y0:y1,x0:x1];yy,xx=np.indices(s.shape);rad=np.hypot(xx+x0-x,yy+y0-y);a=s[rad<=r];n=s[(rad>=ri)&(rad<=ro)]
    if len(a)<8 or len(n)<20:return np.nan
    return float(np.nansum(a-np.nanmedian(n)))
def rscatter(v):
    m=np.nanmedian(v);return float(1.4826*np.nanmedian(np.abs(v-m))/abs(m)) if np.isfinite(m) and m!=0 else np.nan

def main():
    t=time.time();res={'success':False,'method':'cross-quadrant routed 16-epoch Stage-0','stamp_pixels':STAMP,'file_layout':{'primary':PRIMARY,'header':HDR,'stride':STRIDE,'quadrants':144}}
    try:
        _,hh=rr(URLS[0],0,1023);res['http']={'content_range':hh.get('Content-Range')};qs=map_epoch0();res['epoch0_extnames']=[q.name for q in qs]
        k0,ra,de,med=choose_target(qs);res['target']={'epoch0_k':k0,'epoch0_extname':qs[k0].name,'ra':ra,'dec':de,'focal_median_ra':med[0],'focal_median_dec':med[1]}
        shifts=pointing_shifts();res['pointing_shifts_arcsec']=[{'dra':float(x),'ddec':float(y),'r':float(math.hypot(x,y))} for x,y in shifts]
        routes,route_diag=route_groups(qs,(ra,de),shifts);res['routes']={str(g):{'k':int(k),'epoch0_extname':qs[k].name} for g,k in routes.items()};res['route_diagnostics']=route_diag
        hs=epoch_headers(routes);valid=[]
        for i,q in enumerate(hs):
            x,y=pix(q,ra,de);valid.append({'epoch':i,'group':i%4,'k':q.k,'extname':q.name,'x':float(x),'y':float(y),'inside':bool(contains(q,ra,de))})
        res['epoch_routing']=valid
        if not all(v['inside'] for v in valid):raise RuntimeError('routed quadrant fails margin in one or more repeated epochs')
        ims=[None]*16;meta=[None]*16
        with ThreadPoolExecutor(max_workers=8) as ex:
            fs=[ex.submit(stamp,i,hs[i],ra,de) for i in range(16)]
            for f in as_completed(fs):i,z,m=f.result();ims[i]=z;meta[i]=m
        cube=np.stack(ims);NPZ.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(NPZ,stamps=cube,ra=ra,dec=de);res['stamp_shape']=list(cube.shape)
        _,bg,std=sigma_clipped_stats(cube[0],sigma=3,maxiters=5);tab=DAOStarFinder(fwhm=1.8,threshold=max(6*std,1e-6),exclude_border=True)(cube[0]-bg)
        if tab is None or len(tab)<5:raise RuntimeError(f'too few bright detections: {0 if tab is None else len(tab)}')
        x=np.asarray(tab['xcentroid'],float);y=np.asarray(tab['ycentroid'],float);peak=np.asarray(tab['peak'],float);ids=[]
        for j in range(len(x)):
            if not(12<x[j]<STAMP-12 and 12<y[j]<STAMP-12):continue
            d=np.hypot(x-x[j],y-y[j]);d[j]=np.inf
            if np.min(d)>=7:ids.append(j)
        ids=np.asarray(ids,int)
        if len(ids)<3:raise RuntimeError(f'too few isolated stars: {len(ids)}')
        ids=ids[np.argsort(peak[ids])[::-1][:80]];sx=x[ids]+meta[0]['x0'];sy=y[ids]+meta[0]['y0'];wr,wd=hs[0].w.pixel_to_world_values(sx,sy);fl=np.full((len(ids),16),np.nan)
        for e,q in enumerate(hs):
            px,py=q.w.world_to_pixel_values(wr,wd);px-=meta[e]['x0'];py-=meta[e]['y0']
            for j,(xx,yy) in enumerate(zip(px,py)):
                if 9<=xx<STAMP-9 and 9<=yy<STAMP-9:fl[j,e]=aperture(cube[e],xx,yy)
        ok=np.all(np.isfinite(fl)&(fl>0),axis=1);fl=fl[ok]
        if len(fl)<3:raise RuntimeError(f'only {len(fl)} isolated stars valid in all 16 epochs')
        norm=fl/np.median(fl,axis=1)[:,None];common=np.median(norm,axis=0);corr=norm/common[None,:];raw=np.array([rscatter(v) for v in norm]);sc=np.array([rscatter(v) for v in corr])
        res['photometry']={'detected_epoch0':int(len(tab)),'isolated_selected':int(len(ids)),'valid_all_epochs':int(len(fl)),'raw_fractional_scatter_median':float(np.median(raw)),'corrected_fractional_scatter_median':float(np.median(sc)),'corrected_p25':float(np.percentile(sc,25)),'corrected_p75':float(np.percentile(sc,75)),'best10_median':float(np.median(np.sort(sc)[:min(10,len(sc))])),'common_mode':[float(v) for v in common],'same_pointing_group_medians':[float(np.median(corr[:,g::4])) for g in range(4)]}
        res['success']=True
    except Exception as e:res['error']=f'{type(e).__name__}: {e}';raise
    finally:
        res['elapsed_seconds']=round(time.time()-t,2);OUT.parent.mkdir(parents=True,exist_ok=True);txt=json.dumps(res,indent=2,sort_keys=True);OUT.write_text(txt+'\n');print(txt,flush=True)
if __name__=='__main__':main()
