#!/usr/bin/env python3
"""Minimal Euclid Q2 16-epoch Stage-0 test using only the first few SCI quadrants.

The Q2 _sci FITS product contains 144 SCI quadrant extensions of identical pixel
format. For a feasibility test we do not need to scan the focal plane. We read
the primary header, then test the first four quadrant extensions, each across
all 16 Field-1 dithers concurrently, looking for a common 192x192-pixel sky
region. This avoids hundreds of sequential remote header requests.
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
'EUC_VIS_SWL-DET-067070-00-1__20250621T020155.487037Z_sci.fits',
'EUC_VIS_SWL-DET-067070-01-1__20250621T020156.049078Z_sci.fits',
'EUC_VIS_SWL-DET-067070-02-1__20250621T020157.327960Z_sci.fits',
'EUC_VIS_SWL-DET-067070-03-1__20250621T020200.784839Z_sci.fits',
'EUC_VIS_SWL-DET-067070-04-1__20250621T020159.310075Z_sci.fits',
'EUC_VIS_SWL-DET-067070-05-1__20250621T020148.061975Z_sci.fits',
'EUC_VIS_SWL-DET-067070-06-1__20250621T020208.198375Z_sci.fits',
'EUC_VIS_SWL-DET-067070-07-1__20250621T020158.860635Z_sci.fits',
'EUC_VIS_SWL-DET-067070-08-1__20250621T020202.737416Z_sci.fits',
'EUC_VIS_SWL-DET-067070-09-1__20250621T020203.034854Z_sci.fits',
'EUC_VIS_SWL-DET-067070-10-1__20250621T020153.520357Z_sci.fits',
'EUC_VIS_SWL-DET-067070-11-1__20250621T020206.950527Z_sci.fits',
'EUC_VIS_SWL-DET-067070-12-1__20250621T020154.990859Z_sci.fits',
'EUC_VIS_SWL-DET-067070-13-1__20250621T020149.508409Z_sci.fits',
'EUC_VIS_SWL-DET-067070-14-1__20250621T020202.468375Z_sci.fits',
'EUC_VIS_SWL-DET-067070-15-1__20250621T020200.444396Z_sci.fits']
URLS=[f'{BASE}/{f}' for f in FILES]
OUT=Path('results/euclid_ultrafast_feasibility.json'); NPZ=Path('results/euclid_ultrafast_stamps.npz')
BLOCK=2880; CARD=80; HMAX=32*BLOCK; STAMP=192; HALF=STAMP//2; MARGIN=HALF+12

def rr(url,a,b,timeout=45):
    n=b-a+1; req=urllib.request.Request(url,headers={'Range':f'bytes={a}-{b}','User-Agent':'isef-euclid-ultrafast/1.0'})
    with urllib.request.urlopen(req,timeout=timeout) as r: data=r.read(n+1); h=dict(r.headers.items()); s=r.status
    if s!=206 or len(data)!=n: raise RuntimeError(f'range failure status={s} bytes={len(data)} wanted={n}')
    return data,h

def pval(raw):
    raw=raw.strip(); q=False; cut=len(raw)
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

def header(url,off):
    b,_=rr(url,off,off+HMAX-1); d={}; cards=[]
    for i in range(0,len(b),CARD):
        c=b[i:i+CARD].decode('ascii',errors='replace');cards.append(c);k=c[:8].strip()
        if k=='END':return d,cards,math.ceil((i+CARD)/BLOCK)*BLOCK
        if len(c)>=10 and c[8:10]=='= ':d[k]=pval(c[10:])
    raise RuntimeError('no END in header')

def dbytes(h):
    n=int(h.get('NAXIS',0) or 0); pix=0 if n==0 else math.prod(int(h.get(f'NAXIS{i}',0) or 0) for i in range(1,n+1))
    return (pix*abs(int(h.get('BITPIX',8) or 8))//8+int(h.get('PCOUNT',0) or 0))*int(h.get('GCOUNT',1) or 1)

def ah(cards):return fits.Header.fromstring(''.join(cards),sep='')
@dataclass
class H:
    off:int; hb:int; data:int; db:int; name:str; nx:int; ny:int; bp:int; cards:list; raw:dict
    @property
    def w(self):return WCS(ah(self.cards),relax=True)

def make(url,off):
    h,c,hb=header(url,off);return H(off,hb,off+hb,dbytes(h),str(h.get('EXTNAME','')),int(h.get('NAXIS1',0) or 0),int(h.get('NAXIS2',0) or 0),int(h.get('BITPIX',0) or 0),c,h)

def first_offsets():
    p,_,phb=header(URLS[0],0);off=phb;out=[]
    for _ in range(4):
        h=make(URLS[0],off)
        if h.nx<100 or h.ny<100:raise RuntimeError(f'non-image extension {h.name}')
        out.append(h);off=h.data+math.ceil(h.db/BLOCK)*BLOCK
    return out

def epoch_headers(tpl):
    hs=[None]*16;hs[0]=tpl
    with ThreadPoolExecutor(max_workers=12) as ex:
        fs={ex.submit(make,URLS[i],tpl.off):i for i in range(1,16)}
        for f in as_completed(fs):
            i=fs[f];hs[i]=f.result()
    if any(h.name!=tpl.name for h in hs):raise RuntimeError('extension layout differs across epochs')
    return hs

def inside(h,ra,dec):
    x,y=h.w.world_to_pixel_values(ra,dec);return np.isfinite(x) and np.isfinite(y) and MARGIN<=x<h.nx-MARGIN and MARGIN<=y<h.ny-MARGIN

def common(hs):
    cs=[h.w.pixel_to_world_values(h.nx/2,h.ny/2) for h in hs];ra0=float(np.mean([x[0] for x in cs]));de0=float(np.mean([x[1] for x in cs]))
    best=(0,ra0,de0)
    for dra in np.linspace(-0.06,0.06,41):
      for dde in np.linspace(-0.06,0.06,41):
        ra=ra0+dra/max(math.cos(math.radians(de0)),.2);de=de0+dde;n=sum(inside(h,ra,de) for h in hs)
        if n>best[0]:best=(n,ra,de)
        if n==16:return ra,de,16
    return best[1],best[2],best[0]

def dt(bp):return {8:'>u1',16:'>i2',32:'>i4',64:'>i8',-32:'>f4',-64:'>f8'}[bp]
def stamp(i,h,ra,de):
    x,y=h.w.world_to_pixel_values(ra,de);cx=int(round(x));cy=int(round(y));x0=cx-HALF;y0=cy-HALF;bpp=abs(h.bp)//8
    a=h.data+y0*h.nx*bpp;b=h.data+(y0+STAMP)*h.nx*bpp-1;raw,_=rr(URLS[i],a,b,90)
    z=np.frombuffer(raw,dtype=dt(h.bp)).reshape(STAMP,h.nx)[:,x0:x0+STAMP].astype(np.float32)
    z=z*float(h.raw.get('BSCALE',1) or 1)+float(h.raw.get('BZERO',0) or 0)
    return i,z,{'x0':x0,'y0':y0}
def ap(im,x,y,r=3,ri=6,ro=9):
    x0=max(0,int(x)-10);x1=min(STAMP,int(x)+11);y0=max(0,int(y)-10);y1=min(STAMP,int(y)+11);s=im[y0:y1,x0:x1];yy,xx=np.indices(s.shape);rad=np.hypot(xx+x0-x,yy+y0-y);a=s[rad<=r];n=s[(rad>=ri)&(rad<=ro)]
    if len(a)<10 or len(n)<20:return np.nan
    return float(np.nansum(a-np.nanmedian(n)))
def rs(v):
    m=np.nanmedian(v);return float(1.4826*np.nanmedian(np.abs(v-m))/abs(m)) if np.isfinite(m) and m!=0 else np.nan

def main():
    t=time.time();res={'success':False,'method':'minimal first-four-quadrant concurrent range test'}
    try:
        b,h=rr(URLS[0],0,1023);res['http']={'bytes':len(b),'content_range':h.get('Content-Range')}
        candidates=first_offsets();diag=[];chosen=None
        for tpl in candidates:
            hs=epoch_headers(tpl);ra,de,n=common(hs);diag.append({'extname':tpl.name,'coverage':n})
            if n==16:chosen=(hs,ra,de);break
        res['quadrant_diagnostics']=diag
        if chosen is None:raise RuntimeError('none of first four quadrants has a common 192px region')
        hs,ra,de=chosen;res['patch']={'extname':hs[0].name,'ra':ra,'dec':de}
        ims=[None]*16;meta=[None]*16
        with ThreadPoolExecutor(max_workers=8) as ex:
            fs=[ex.submit(stamp,i,hs[i],ra,de) for i in range(16)]
            for f in as_completed(fs):i,z,m=f.result();ims[i]=z;meta[i]=m
        cube=np.stack(ims);NPZ.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(NPZ,stamps=cube,ra=ra,dec=de)
        _,med,std=sigma_clipped_stats(cube[0],sigma=3,maxiters=5);tab=DAOStarFinder(fwhm=1.8,threshold=max(7*std,1e-6),exclude_border=True)(cube[0]-med)
        if tab is None or len(tab)<6:raise RuntimeError(f'too few detections {0 if tab is None else len(tab)}')
        x=np.array(tab['xcentroid'],float);y=np.array(tab['ycentroid'],float);peak=np.array(tab['peak'],float);ids=[]
        for i in range(len(x)):
            if not(14<x[i]<STAMP-14 and 14<y[i]<STAMP-14):continue
            d=np.hypot(x-x[i],y-y[i]);d[i]=np.inf
            if np.min(d)>=9:ids.append(i)
        ids=np.array(ids,int)
        if len(ids)<4:raise RuntimeError(f'too few isolated stars {len(ids)}')
        ids=ids[np.argsort(peak[ids])[::-1][:100]];sx=x[ids]+meta[0]['x0'];sy=y[ids]+meta[0]['y0'];wr,wd=hs[0].w.pixel_to_world_values(sx,sy);fl=np.full((len(ids),16),np.nan)
        for e in range(16):
            px,py=hs[e].w.world_to_pixel_values(wr,wd);px-=meta[e]['x0'];py-=meta[e]['y0']
            for j,(xx,yy) in enumerate(zip(px,py)):
                if 10<=xx<STAMP-10 and 10<=yy<STAMP-10:fl[j,e]=ap(cube[e],xx,yy)
        ok=np.all(np.isfinite(fl)&(fl>0),axis=1);fl=fl[ok];wr=np.asarray(wr)[ok];wd=np.asarray(wd)[ok]
        if len(fl)<3:raise RuntimeError(f'only {len(fl)} valid stars')
        n=fl/np.median(fl,axis=1)[:,None];cm=np.median(n,axis=0);c=n/cm[None,:];sc=np.array([rs(v) for v in c]);raw=np.array([rs(v) for v in n])
        res['photometry']={'detected':int(len(tab)),'isolated_selected':int(len(ids)),'valid_all_epochs':int(len(fl)),'raw_scatter_median':float(np.median(raw)),'corrected_scatter_median':float(np.median(sc)),'p25':float(np.percentile(sc,25)),'p75':float(np.percentile(sc,75)),'best10_median':float(np.median(np.sort(sc)[:min(10,len(sc))])),'common_mode':cm.tolist(),'mod4_epoch_medians':[float(np.median(c[:,g::4])) for g in range(4)]}
        res['success']=True
    except Exception as e:res['error']=f'{type(e).__name__}: {e}';raise
    finally:res['elapsed_seconds']=round(time.time()-t,2);OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(res,indent=2,sort_keys=True)+'\n');print(json.dumps(res,indent=2,sort_keys=True))
if __name__=='__main__':main()
