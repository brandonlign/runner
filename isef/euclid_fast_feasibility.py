#!/usr/bin/env python3
"""Fast Euclid Q2 Stage-0 feasibility test.

Uses bounded HTTP Range reads only. It scans the first Field-1 exposure once,
ranks detector quadrants near the nominal field center, checks candidate quadrants
across all 16 dithers concurrently, then range-reads a 256x256 common sky stamp
from every epoch and measures bright-star repeatability.

This is a feasibility diagnostic, not the final crowded-field photometry method.
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

BASE="https://irsa.ipac.caltech.edu/data/Euclid/q2/data"
FILES=[
"EUC_VIS_SWL-DET-067070-00-1__20250621T020155.487037Z_sci.fits",
"EUC_VIS_SWL-DET-067070-01-1__20250621T020156.049078Z_sci.fits",
"EUC_VIS_SWL-DET-067070-02-1__20250621T020157.327960Z_sci.fits",
"EUC_VIS_SWL-DET-067070-03-1__20250621T020200.784839Z_sci.fits",
"EUC_VIS_SWL-DET-067070-04-1__20250621T020159.310075Z_sci.fits",
"EUC_VIS_SWL-DET-067070-05-1__20250621T020148.061975Z_sci.fits",
"EUC_VIS_SWL-DET-067070-06-1__20250621T020208.198375Z_sci.fits",
"EUC_VIS_SWL-DET-067070-07-1__20250621T020158.860635Z_sci.fits",
"EUC_VIS_SWL-DET-067070-08-1__20250621T020202.737416Z_sci.fits",
"EUC_VIS_SWL-DET-067070-09-1__20250621T020203.034854Z_sci.fits",
"EUC_VIS_SWL-DET-067070-10-1__20250621T020153.520357Z_sci.fits",
"EUC_VIS_SWL-DET-067070-11-1__20250621T020206.950527Z_sci.fits",
"EUC_VIS_SWL-DET-067070-12-1__20250621T020154.990859Z_sci.fits",
"EUC_VIS_SWL-DET-067070-13-1__20250621T020149.508409Z_sci.fits",
"EUC_VIS_SWL-DET-067070-14-1__20250621T020202.468375Z_sci.fits",
"EUC_VIS_SWL-DET-067070-15-1__20250621T020200.444396Z_sci.fits",
]
URLS=[f"{BASE}/{f}" for f in FILES]
OUT=Path("results/euclid_fast_feasibility.json")
NPZ=Path("results/euclid_fast_stamps.npz")
BLOCK=2880; CARD=80; MAX_HEADER=32*BLOCK
FIELD_RA=267.425; FIELD_DEC=-30.019
STAMP=256; HALF=STAMP//2; MARGIN=HALF+12


def bounded_range(url,start,end,timeout=45):
    want=end-start+1
    req=urllib.request.Request(url,headers={"Range":f"bytes={start}-{end}","User-Agent":"isef-euclid-fast/1.0"})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        data=r.read(want+1); headers=dict(r.headers.items()); status=r.status
    if status!=206: raise RuntimeError(f"HTTP {status} ignored Range for {url}")
    if len(data)!=want: raise RuntimeError(f"range length {len(data)} != {want} for {url}")
    return data,headers,status


def value(raw):
    raw=raw.strip(); quote=False; cut=len(raw)
    for i,ch in enumerate(raw):
        if ch=="'": quote=not quote
        elif ch=="/" and not quote: cut=i; break
    s=raw[:cut].strip()
    if not s:return None
    if s.startswith("'"):
        m=re.match(r"'((?:''|[^'])*)'",s); return m.group(1).replace("''", "'").strip() if m else s.strip("'").strip()
    if s=="T":return True
    if s=="F":return False
    try:return float(s.replace("D","E")) if any(c in s for c in ".EDed") else int(s)
    except ValueError:return s


def parse_header(buf):
    d={}; cards=[]
    for off in range(0,len(buf),CARD):
        c=buf[off:off+CARD].decode("ascii",errors="replace"); cards.append(c)
        k=c[:8].strip()
        if k=="END": return d,cards,math.ceil((off+CARD)/BLOCK)*BLOCK
        if len(c)>=10 and c[8:10]=="= ": d[k]=value(c[10:])
    raise RuntimeError("FITS END card not found in bounded header")


def read_header(url,offset):
    b,_,_=bounded_range(url,offset,offset+MAX_HEADER-1)
    return parse_header(b)


def data_bytes(h):
    n=int(h.get("NAXIS",0) or 0)
    pix=0 if n==0 else math.prod(int(h.get(f"NAXIS{i}",0) or 0) for i in range(1,n+1))
    return (pix*abs(int(h.get("BITPIX",8) or 8))//8 + int(h.get("PCOUNT",0) or 0))*int(h.get("GCOUNT",1) or 1)


def astro_header(cards): return fits.Header.fromstring("".join(cards),sep="")

@dataclass
class Hdu:
    idx:int; offset:int; header_bytes:int; data_offset:int; data_bytes:int; extname:str; nx:int; ny:int; bitpix:int; cards:list; hdr:dict
    @property
    def wcs(self): return WCS(astro_header(self.cards),relax=True)


def scan_first(url):
    out=[]; off=0
    for idx in range(220):
        h,c,hb=read_header(url,off); db=data_bytes(h); pad=math.ceil(db/BLOCK)*BLOCK if db else 0
        if int(h.get("NAXIS",0) or 0)==2 and int(h.get("NAXIS1",0) or 0)>100 and int(h.get("NAXIS2",0) or 0)>100:
            out.append(Hdu(idx,off,hb,off+hb,db,str(h.get("EXTNAME","")),int(h["NAXIS1"]),int(h["NAXIS2"]),int(h["BITPIX"]),c,h))
        off2=off+hb+pad
        if off2<=off:break
        off=off2
        if len(out)>=144:break
    return out


def read_at_template(url,tpl):
    h,c,hb=read_header(url,tpl.offset)
    if int(h.get("NAXIS",0) or 0)!=2 or str(h.get("EXTNAME",""))!=tpl.extname:
        raise RuntimeError(f"layout mismatch expected {tpl.extname} got {h.get('EXTNAME')}")
    return Hdu(tpl.idx,tpl.offset,hb,tpl.offset+hb,data_bytes(h),str(h.get("EXTNAME","")),int(h["NAXIS1"]),int(h["NAXIS2"]),int(h["BITPIX"]),c,h)


def all_epochs_for(tpl):
    hs=[None]*16; hs[0]=tpl
    with ThreadPoolExecutor(max_workers=8) as ex:
        fs={ex.submit(read_at_template,URLS[i],tpl):i for i in range(1,16)}
        for f in as_completed(fs): hs[fs[f]]=f.result()
    return hs


def inside(h,ra,dec):
    x,y=h.wcs.world_to_pixel_values(ra,dec)
    return np.isfinite(x) and np.isfinite(y) and MARGIN<=x<h.nx-MARGIN and MARGIN<=y<h.ny-MARGIN


def pick_patch(first):
    ranked=[]
    for h in first:
        try:
            ra,dec=h.wcs.pixel_to_world_values(h.nx/2,h.ny/2)
            d=((ra-FIELD_RA)*math.cos(math.radians(FIELD_DEC)))**2+(dec-FIELD_DEC)**2
            ranked.append((d,h))
        except Exception:pass
    ranked.sort(key=lambda z:z[0])
    diag=[]
    for _,tpl in ranked[:8]:
        t=time.time()
        try: hs=all_epochs_for(tpl)
        except Exception as e:
            diag.append({"extname":tpl.extname,"error":str(e),"seconds":round(time.time()-t,2)}); continue
        centers=[h.wcs.pixel_to_world_values(h.nx/2,h.ny/2) for h in hs]
        cra=float(np.mean([p[0] for p in centers])); cdec=float(np.mean([p[1] for p in centers]))
        # Search a modest grid around the mean center. The 16 observations repeat four dither positions.
        best=(0,cra,cdec)
        for dra in np.linspace(-0.04,0.04,33):
            for dd in np.linspace(-0.04,0.04,33):
                ra=cra+dra/max(math.cos(math.radians(cdec)),0.2); dec=cdec+dd
                n=sum(inside(h,ra,dec) for h in hs)
                if n>best[0]:best=(n,ra,dec)
                if n==16:
                    diag.append({"extname":tpl.extname,"coverage":16,"seconds":round(time.time()-t,2)})
                    return hs,ra,dec,diag
        diag.append({"extname":tpl.extname,"coverage":int(best[0]),"seconds":round(time.time()-t,2)})
    raise RuntimeError(f"no common patch: {diag}")


def dtype(bitpix):return {8:">u1",16:">i2",32:">i4",64:">i8",-32:">f4",-64:">f8"}[bitpix]


def read_stamp(i,h,ra,dec):
    x,y=h.wcs.world_to_pixel_values(ra,dec); cx=int(round(x)); cy=int(round(y))
    x0=cx-HALF; x1=cx+HALF; y0=cy-HALF; y1=cy+HALF; bpp=abs(h.bitpix)//8
    start=h.data_offset+y0*h.nx*bpp; end=h.data_offset+y1*h.nx*bpp-1
    raw,_,_=bounded_range(URLS[i],start,end,timeout=90)
    arr=np.frombuffer(raw,dtype=dtype(h.bitpix)).reshape(y1-y0,h.nx)[:,x0:x1].astype(np.float32)
    arr=arr*float(h.hdr.get("BSCALE",1) or 1)+float(h.hdr.get("BZERO",0) or 0)
    return i,arr,{"x0":x0,"y0":y0,"cx":cx,"cy":cy}


def aperture(im,x,y,r=3.0,rin=6.0,rout=9.0):
    xi0=max(0,int(x)-10); xi1=min(im.shape[1],int(x)+11); yi0=max(0,int(y)-10); yi1=min(im.shape[0],int(y)+11)
    sub=im[yi0:yi1,xi0:xi1]
    yy,xx=np.indices(sub.shape); rr=np.hypot((xx+xi0)-x,(yy+yi0)-y)
    ap=sub[rr<=r]; an=sub[(rr>=rin)&(rr<=rout)]
    if ap.size<10 or an.size<20:return np.nan
    bg=np.nanmedian(an); return float(np.nansum(ap-bg))


def rscatter(v):
    med=np.nanmedian(v)
    return float(1.4826*np.nanmedian(np.abs(v-med))/abs(med)) if np.isfinite(med) and med!=0 else np.nan


def main():
    t0=time.time(); result={"success":False,"method":"fast concurrent bounded-range Stage-0"}
    try:
        b,h,s=bounded_range(URLS[0],0,1023); result["range"]={"status":s,"content_range":h.get("Content-Range"),"bytes":len(b)}
        first=scan_first(URLS[0]); result["image_hdus_first_epoch"]=len(first)
        hs,ra,dec,diag=pick_patch(first); result["patch"]={"ra":ra,"dec":dec,"extname":hs[0].extname,"diagnostics":diag}
        stamps=[None]*16; metas=[None]*16
        with ThreadPoolExecutor(max_workers=6) as ex:
            fs=[ex.submit(read_stamp,i,hs[i],ra,dec) for i in range(16)]
            for f in as_completed(fs):
                i,a,m=f.result(); stamps[i]=a; metas[i]=m
        cube=np.stack(stamps); NPZ.parent.mkdir(parents=True,exist_ok=True); np.savez_compressed(NPZ,stamps=cube,ra=ra,dec=dec)
        result["stamp_shape"]=list(cube.shape)

        _,med,std=sigma_clipped_stats(cube[0],sigma=3,maxiters=5)
        tab=DAOStarFinder(fwhm=1.8,threshold=max(8*std,1e-6),exclude_border=True)(cube[0]-med)
        if tab is None or len(tab)<8: raise RuntimeError(f"too few detections: {0 if tab is None else len(tab)}")
        x=np.asarray(tab["xcentroid"],float); y=np.asarray(tab["ycentroid"],float); peak=np.asarray(tab["peak"],float)
        good=[]
        for i in range(len(x)):
            if not (15<x[i]<STAMP-15 and 15<y[i]<STAMP-15):continue
            d=np.hypot(x-x[i],y-y[i]); d[i]=np.inf
            if np.nanmin(d)>=10:good.append(i)
        good=np.array(good,dtype=int)
        if len(good)<5: raise RuntimeError(f"too few isolated stars: {len(good)}")
        good=good[np.argsort(peak[good])[::-1][:150]]
        sx=x[good]+metas[0]["x0"]; sy=y[good]+metas[0]["y0"]
        wr,wd=hs[0].wcs.pixel_to_world_values(sx,sy)
        flux=np.full((len(good),16),np.nan)
        for e in range(16):
            px,py=hs[e].wcs.world_to_pixel_values(wr,wd); px-=metas[e]["x0"]; py-=metas[e]["y0"]
            for j,(xx,yy) in enumerate(zip(px,py)):
                if 10<=xx<STAMP-10 and 10<=yy<STAMP-10: flux[j,e]=aperture(cube[e],xx,yy)
        ok=np.all(np.isfinite(flux)&(flux>0),axis=1); flux=flux[ok]; wr=np.asarray(wr)[ok]; wd=np.asarray(wd)[ok]
        if len(flux)<4: raise RuntimeError(f"only {len(flux)} valid all-epoch stars")
        medstar=np.median(flux,axis=1); norm=flux/medstar[:,None]
        common=np.median(norm,axis=0); corrected=norm/common[None,:]
        raw=np.array([rscatter(v) for v in norm]); scat=np.array([rscatter(v) for v in corrected])
        # Same nominal dither position repeats every four exposures; measure residual offsets by modulo-4 group.
        group_medians=[]
        for g in range(4): group_medians.append(float(np.median(corrected[:,g::4])))
        result["photometry"]={
            "detected":int(len(tab)),"isolated":int(len(good)),"valid_all_epochs":int(len(flux)),
            "raw_scatter_median":float(np.nanmedian(raw)),"corrected_scatter_median":float(np.nanmedian(scat)),
            "corrected_scatter_p25":float(np.nanpercentile(scat,25)),"corrected_scatter_p75":float(np.nanpercentile(scat,75)),
            "best10_median":float(np.nanmedian(np.sort(scat)[:min(10,len(scat))])),
            "common_mode":common.tolist(),"mod4_group_medians":group_medians,
        }
        result["sample"]=[{"ra":float(r),"dec":float(d),"scatter":float(s)} for r,d,s in zip(wr[:20],wd[:20],scat[:20])]
        result["success"]=True
    except Exception as e:
        result["error"]=f"{type(e).__name__}: {e}"; raise
    finally:
        result["elapsed_seconds"]=round(time.time()-t0,2); OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__": main()
