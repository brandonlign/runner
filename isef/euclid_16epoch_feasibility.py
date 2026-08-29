#!/usr/bin/env python3
"""Euclid Q2 Stage-0: small-patch 16-epoch repeatability feasibility test.

This deliberately avoids full FITS downloads. It uses HTTP Range requests to:
1) map one detector quadrant across all 16 Field-1 dithers,
2) choose a sky patch covered with margin in every epoch,
3) read only a 512x512-ish target-centered stamp from each exposure,
4) detect bright isolated stars in epoch 0,
5) perform simple fixed-sky aperture photometry in all epochs,
6) remove an exposure common mode and report robust repeatability.

This is a feasibility diagnostic, NOT the final crowded-field photometry pipeline.
Aperture photometry is intentionally conservative and only tests whether the
images can support a useful time-domain signal floor at all.
"""
from __future__ import annotations

import json, math, re, time, urllib.request
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from astropy.wcs import WCS
from photutils.detection import DAOStarFinder

BASE = "https://irsa.ipac.caltech.edu/data/Euclid/q2/data"
FILES = [
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
URLS=[f"{BASE}/{x}" for x in FILES]
OUT=Path("results/euclid_16epoch_feasibility.json")
NPZ=Path("results/euclid_16epoch_stamps.npz")
BLOCK=2880; CARD=80
FIELD_RA=267.425; FIELD_DEC=-30.019
STAMP=512; MARGIN=STAMP//2 + 16


def http_range(url,start,end,timeout=90):
    req=urllib.request.Request(url,headers={"Range":f"bytes={start}-{end}","User-Agent":"isef-euclid-feasibility/1.0"})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        return r.read(),dict(r.headers.items()),r.status


def val(raw):
    raw=raw.strip(); q=False; cut=len(raw)
    for i,ch in enumerate(raw):
        if ch=="'": q=not q
        elif ch=="/" and not q: cut=i; break
    s=raw[:cut].strip()
    if not s:return None
    if s.startswith("'"):
        m=re.match(r"'((?:''|[^'])*)'",s); return (m.group(1).replace("''", "'").strip() if m else s.strip("'").strip())
    if s=="T":return True
    if s=="F":return False
    try:
        return float(s.replace("D","E")) if any(c in s for c in ".EDed") else int(s)
    except ValueError:return s


def parse_header(buf):
    cards=[]; d={}
    for off in range(0,len(buf),CARD):
        c=buf[off:off+CARD].decode("ascii",errors="replace"); cards.append(c)
        k=c[:8].strip()
        if k=="END": return d,cards,off+CARD
        if c[8:10]=="= ": d[k]=val(c[10:])
    raise RuntimeError("no END")


def read_header(url,offset):
    blocks=1
    while blocks<=32:
        b,_,s=http_range(url,offset,offset+blocks*BLOCK-1)
        if s not in (200,206):raise RuntimeError(f"header HTTP {s}")
        try:
            d,cards,used=parse_header(b); return d,cards,math.ceil(used/BLOCK)*BLOCK
        except RuntimeError:blocks*=2
    raise RuntimeError("header too large")


def dbytes(h):
    n=int(h.get("NAXIS",0) or 0); pix=0 if n==0 else math.prod(int(h.get(f"NAXIS{i}",0) or 0) for i in range(1,n+1))
    return (pix*abs(int(h.get("BITPIX",8) or 8))//8 + int(h.get("PCOUNT",0) or 0))*int(h.get("GCOUNT",1) or 1)


def as_header(cards):
    # Keep exact cards so WCS parsing sees all SIP/PV terms if present.
    text="".join(cards)
    return fits.Header.fromstring(text,sep="")

@dataclass
class HduInfo:
    offset:int; header_bytes:int; data_offset:int; data_bytes:int; extname:str; nx:int; ny:int; bitpix:int; cards:list; hdr:dict
    @property
    def wcs(self): return WCS(as_header(self.cards),relax=True)


def scan_first(url):
    out=[]; off=0
    for idx in range(400):
        h,c,hb=read_header(url,off); db=dbytes(h); pad=math.ceil(db/BLOCK)*BLOCK if db else 0
        if int(h.get("NAXIS",0) or 0)==2 and int(h.get("NAXIS1",0) or 0)>100 and int(h.get("NAXIS2",0) or 0)>100:
            out.append(HduInfo(off,hb,off+hb,db,str(h.get("EXTNAME","")),int(h["NAXIS1"]),int(h["NAXIS2"]),int(h["BITPIX"]),c,h))
        nxt=off+hb+pad
        if nxt<=off:break
        off=nxt
        # science file should have ~144 image HDUs; no need to trust a fixed count
        if len(out)>=144:break
    return out


def read_same_hdu(url,template):
    h,c,hb=read_header(url,template.offset)
    if str(h.get("EXTNAME",""))!=template.extname or int(h.get("NAXIS",0) or 0)!=2:
        raise RuntimeError(f"layout changed at {url}: expected {template.extname}, got {h.get('EXTNAME')}")
    return HduInfo(template.offset,hb,template.offset+hb,dbytes(h),str(h.get("EXTNAME","")),int(h["NAXIS1"]),int(h["NAXIS2"]),int(h["BITPIX"]),c,h)


def inside(hdu,ra,dec,margin=MARGIN):
    x,y=hdu.wcs.world_to_pixel_values(ra,dec)
    return np.isfinite(x) and np.isfinite(y) and margin<=x<hdu.nx-margin and margin<=y<hdu.ny-margin


def choose_common_patch(first_hdus):
    # Rank quadrants near nominal field center; test at most 24 to bound requests.
    ranked=[]
    for h in first_hdus:
        try:
            ra,dec=h.wcs.pixel_to_world_values(h.nx/2,h.ny/2)
            dist=((ra-FIELD_RA)*math.cos(math.radians(FIELD_DEC)))**2+(dec-FIELD_DEC)**2
            ranked.append((dist,h,ra,dec))
        except Exception:pass
    ranked.sort(key=lambda z:z[0])
    diagnostics=[]
    for _,tpl,ra0,dec0 in ranked[:24]:
        hs=[tpl]
        try:
            for u in URLS[1:]: hs.append(read_same_hdu(u,tpl))
        except Exception as e:
            diagnostics.append({"extname":tpl.extname,"error":str(e)}); continue
        # Search sky around mean of detector centers. Grid is small because dither offsets are small.
        centers=[]
        for h in hs:
            centers.append(h.wcs.pixel_to_world_values(h.nx/2,h.ny/2))
        cra=float(np.mean([x[0] for x in centers])); cdec=float(np.mean([x[1] for x in centers]))
        # 41x41 grid over +-0.025 deg (~90 arcsec), enough to find intersection if healthy.
        best=None
        for dra in np.linspace(-0.025,0.025,41):
            for dd in np.linspace(-0.025,0.025,41):
                ra=cra+dra/max(math.cos(math.radians(cdec)),0.2); dec=cdec+dd
                ok=sum(inside(h,ra,dec) for h in hs)
                if best is None or ok>best[0]: best=(ok,ra,dec)
                if ok==16:
                    diagnostics.append({"extname":tpl.extname,"coverage":16})
                    return hs,ra,dec,diagnostics
        diagnostics.append({"extname":tpl.extname,"coverage":int(best[0])})
    raise RuntimeError(f"no common 16-epoch patch; diagnostics={diagnostics}")


def dtype(bitpix):return {8:">u1",16:">i2",32:">i4",64:">i8",-32:">f4",-64:">f8"}[bitpix]


def stamp(url,h,ra,dec):
    x,y=h.wcs.world_to_pixel_values(ra,dec); cx=int(round(x)); cy=int(round(y)); half=STAMP//2
    x0=cx-half; x1=cx+half; y0=cy-half; y1=cy+half
    bpp=abs(h.bitpix)//8
    start=h.data_offset+y0*h.nx*bpp; end=h.data_offset+y1*h.nx*bpp-1
    raw,_,s=http_range(url,start,end,timeout=120); exp=(y1-y0)*h.nx*bpp
    if s!=206 or len(raw)!=exp:raise RuntimeError(f"stamp range mismatch HTTP={s} got={len(raw)} expected={exp}")
    rows=np.frombuffer(raw,dtype=dtype(h.bitpix)).reshape(y1-y0,h.nx)
    a=rows[:,x0:x1].astype(np.float32)
    a=a*float(h.hdr.get("BSCALE",1) or 1)+float(h.hdr.get("BZERO",0) or 0)
    return a,{"cx":cx,"cy":cy,"x0":x0,"y0":y0,"world_x":float(x),"world_y":float(y)}


def aperture_flux(img,x,y,r=3.0,rin=6.0,rout=9.0):
    yy,xx=np.indices(img.shape); rr=np.hypot(xx-x,yy-y)
    ap=img[rr<=r]; an=img[(rr>=rin)&(rr<=rout)]
    if ap.size<10 or an.size<20:return np.nan
    bg=np.nanmedian(an); return float(np.nansum(ap-bg))


def robust_frac_scatter(v):
    v=np.asarray(v,float); med=np.nanmedian(v)
    if not np.isfinite(med) or med==0:return np.nan
    return float(1.4826*np.nanmedian(np.abs(v-med))/abs(med))


def main():
    t0=time.time(); result={"success":False,"stage":"16-epoch bright-isolated-star repeatability","files":FILES}
    try:
        # Explicit range check.
        p,hdr,s=http_range(URLS[0],0,1023)
        result["http"]={"status":s,"bytes":len(p),"content_range":hdr.get("Content-Range"),"accept_ranges":hdr.get("Accept-Ranges")}
        if s!=206:raise RuntimeError(f"IRSA did not honor range request: {s}")

        first=scan_first(URLS[0]); result["first_exposure_image_hdus"]=len(first)
        hs,ra,dec,diag=choose_common_patch(first)
        result["patch"]={"ra":ra,"dec":dec,"extname":hs[0].extname,"selection_diagnostics":diag}

        stamps=[]; metas=[]
        for u,h in zip(URLS,hs):
            a,m=stamp(u,h,ra,dec); stamps.append(a); metas.append(m)
        cube=np.stack(stamps); NPZ.parent.mkdir(parents=True,exist_ok=True); np.savez_compressed(NPZ,stamps=cube,ra=ra,dec=dec)
        result["stamp_shape"]=list(cube.shape)

        # Detect only high-S/N objects for the first repeatability floor.
        mean,med,std=sigma_clipped_stats(cube[0],sigma=3.0,maxiters=5)
        finder=DAOStarFinder(fwhm=1.8,threshold=max(10.0*std,1e-6),exclude_border=True)
        tab=finder(cube[0]-med)
        if tab is None or len(tab)<10:raise RuntimeError(f"too few bright stars detected: {0 if tab is None else len(tab)}")
        x0=np.asarray(tab["xcentroid"],float); y0=np.asarray(tab["ycentroid"],float); peak=np.asarray(tab["peak"],float)
        # Keep stars away from borders and nearest neighbors; crowding comes later.
        keep=np.ones(len(x0),bool)
        for i in range(len(x0)):
            if x0[i]<20 or y0[i]<20 or x0[i]>STAMP-20 or y0[i]>STAMP-20:keep[i]=False;continue
            d=np.hypot(x0-x0[i],y0-y0[i]); d[i]=np.inf
            if np.nanmin(d)<12:keep[i]=False
        ids=np.where(keep)[0]
        # Cap at 300 brightest to bound CPU/noise.
        ids=ids[np.argsort(peak[ids])[::-1][:300]]
        if len(ids)<8:raise RuntimeError(f"too few isolated stars after cuts: {len(ids)}")

        # Sky coordinates anchored in epoch 0, then transformed independently per epoch.
        # Pixel positions in stamp -> full detector pixel -> world.
        sx=x0[ids]+metas[0]["x0"]; sy=y0[ids]+metas[0]["y0"]
        wr,wd=hs[0].wcs.pixel_to_world_values(sx,sy)
        flux=np.full((len(ids),16),np.nan,float)
        for e,(im,h,m) in enumerate(zip(cube,hs,metas)):
            fx,fy=h.wcs.world_to_pixel_values(wr,wd); fx=fx-m["x0"]; fy=fy-m["y0"]
            for j,(xx,yy) in enumerate(zip(fx,fy)):
                if 10<=xx<STAMP-10 and 10<=yy<STAMP-10:
                    flux[j,e]=aperture_flux(im,xx,yy)

        # Drop nonpositive/bad measurements and stars missing epochs.
        goodstar=np.all(np.isfinite(flux)&(flux>0),axis=1)
        flux=flux[goodstar]; wr=np.asarray(wr)[goodstar]; wd=np.asarray(wd)[goodstar]
        if len(flux)<5:raise RuntimeError(f"only {len(flux)} stars have valid positive flux in all epochs")

        # Exposure common-mode correction from median normalized bright-star ensemble.
        star_med=np.median(flux,axis=1); norm=flux/star_med[:,None]
        common=np.median(norm,axis=0); corr=flux/common[None,:]
        scat=np.array([robust_frac_scatter(v) for v in corr])
        rawsc=np.array([robust_frac_scatter(v) for v in flux])
        result["photometry"]={
            "detected":int(len(tab)),"isolated_selected":int(len(ids)),"valid_all_epochs":int(len(flux)),
            "common_mode":common.tolist(),
            "raw_fractional_scatter_median":float(np.nanmedian(rawsc)),
            "corrected_fractional_scatter_median":float(np.nanmedian(scat)),
            "corrected_fractional_scatter_p25":float(np.nanpercentile(scat,25)),
            "corrected_fractional_scatter_p75":float(np.nanpercentile(scat,75)),
            "corrected_fractional_scatter_best10_median":float(np.nanmedian(np.sort(scat)[:min(10,len(scat))])),
            "note":"Simple aperture photometry on bright isolated stars; diagnostic floor only, not final crowded-field method."
        }
        result["bright_star_sample"]=[{"ra":float(r),"dec":float(d),"scatter":float(s)} for r,d,s in zip(wr[:25],wd[:25],scat[:25])]
        result["success"]=True
    except Exception as e:
        result["error"]=f"{type(e).__name__}: {e}"; raise
    finally:
        result["elapsed_seconds"]=round(time.time()-t0,2); OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":main()
