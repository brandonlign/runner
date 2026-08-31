#!/usr/bin/env python3
"""Corrected real-PUNCH-background injection gate for the PUNCH KH project.

TARGET BLIND: only 2025-09-21 Level-2 CTM controls are opened. No R3 file is
accessed. Unlike v1, every synthetic movie frame samples real PUNCH pixels:
a wider source strip is extracted and a 192-pixel window walks through it, so
background drift never introduces zero-filled synthetic sky.
"""
from __future__ import annotations

import json
import math
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import requests
from astropy.io import fits
from scipy.ndimage import median_filter
from scipy.optimize import least_squares

OUT = Path("results/punch_kh_real_background_controls_v2")
OUT.mkdir(parents=True, exist_ok=True)
ROOT = "https://umbra.nascom.nasa.gov/punch/2/CTM/2025/09/21/"
TARGET_HOURS = [0, 8, 16]
PATCH_RADIUS_PX = 850
PATCH_CENTERS = {
    "E": (2048 + PATCH_RADIUS_PX, 2048),
    "W": (2048 - PATCH_RADIUS_PX, 2048),
    "N": (2048, 2048 + PATCH_RADIUS_PX),
    "S": (2048, 2048 - PATCH_RADIUS_PX),
}
NX, NY = 192, 81
NT = 48
DT = 8/60
WAVELENGTH = 24.0
SPEED = 8.0
GROWTH = 0.35
A0 = 1.5
TAIL_SIGMA = 3.0
DRIFT = 2.3
MAX_SHIFT = int(math.ceil(DRIFT*(NT-1)))
SOURCE_NX = NX + MAX_SHIFT + 4
PEAKS = [3.0, 5.0, 8.0]

LOCAL_WIDTH = 5
OUTLIER_PX = 3.0
MAX_INTERP_RUN = 2
MAX_FLAG_FRAC = 0.05

FILE_RE = re.compile(r'href=["\'](PUNCH_L2_CTM_(20250921\d{6})_v0l\.fits)["\']', re.I)


def choose_files():
    r=requests.get(ROOT,timeout=(10,30)); r.raise_for_status()
    rows=[]
    for name,stamp in FILE_RE.findall(r.text):
        sec=int(stamp[8:10])*3600+int(stamp[10:12])*60+int(stamp[12:14])
        rows.append((sec,name))
    if not rows: raise RuntimeError("No v0l L2 CTM files found on frozen control date")
    picked=[min(rows,key=lambda z:abs(z[0]-h*3600)) for h in TARGET_HOURS]
    if len({n for _,n in picked})!=3: raise RuntimeError(f"duplicate controls: {picked}")
    return picked


def download(name):
    p=OUT/name
    if not p.exists():
        with requests.get(ROOT+name,stream=True,timeout=(10,120)) as r:
            r.raise_for_status()
            with p.open("wb") as f:
                for chunk in r.iter_content(1024*1024):
                    if chunk: f.write(chunk)
    return p


def extract_source_strip(data,cx,cy):
    # Center the full drift trajectory around the preregistered radius point.
    x0=int(round(cx-NX/2-MAX_SHIFT/2)); x1=x0+SOURCE_NX
    y0=int(round(cy-NY/2)); y1=y0+NY
    if x0<0 or y0<0 or x1>data.shape[1] or y1>data.shape[0]:
        raise RuntimeError("control source strip outside mosaic")
    return np.asarray(data[y0:y1,x0:x1],float)


def standardize(p):
    finite=np.isfinite(p)
    if finite.mean()<.95: return None,{"finite_fraction":float(finite.mean())}
    med=float(np.nanmedian(p)); mad=float(np.nanmedian(np.abs(p-med)))
    sig=max(1.4826*mad,float(np.nanstd(p))*.1,1e-30)
    z=(p-med)/sig; z[~finite]=0
    return z,{"finite_fraction":float(finite.mean()),"median":med,"robust_sigma":sig}


def movie(bg,peak):
    y=np.arange(NY)-(NY-1)/2; x=np.arange(NX,dtype=float); t=np.arange(NT)*DT
    frames=[]; truths=[]
    for i,ti in enumerate(t):
        start=int(round(DRIFT*i))
        real=bg[:,start:start+NX]
        if real.shape!=(NY,NX): raise RuntimeError("drift window shape failure")
        amp=A0*np.exp(GROWTH*ti)
        center=amp*np.sin(2*np.pi*(x-SPEED*ti)/WAVELENGTH+.3)
        img=real.copy(); bright=peak*(1-.30*x/NX)
        for j,c in enumerate(center):
            img[:,j]+=bright[j]*np.exp(-.5*((y-c)/TAIL_SIGMA)**2)
        frames.append(img);truths.append(center)
    return y,np.asarray(frames),np.asarray(truths)


def fitcol(y,flux):
    keep=np.abs(y)<=15; yy=y[keep];ff=np.asarray(flux[keep],float)
    good=np.isfinite(ff);yy=yy[good];ff=ff[good]
    if len(ff)<12:return np.nan
    edge=np.r_[ff[:4],ff[-4:]];b0=float(np.median(edge));amp0=max(float(np.max(ff)-b0),.05)
    scale=max(float(np.std(ff)),1.0)
    p0=np.array([b0,0,amp0,0,3.0])
    lo=np.array([b0-20*scale,-5*scale,0,-15,1.0]);hi=np.array([b0+20*scale,5*scale,max(100*scale,amp0*2),15,8.0])
    def model(p):
        b,m,a,c,s=p;return b+m*yy+a*np.exp(-.5*((yy-c)/s)**2)
    try:
        f=least_squares(lambda p:ff-model(p),p0,bounds=(lo,hi),loss="soft_l1",f_scale=.5,max_nfev=400)
        return float(f.x[3]) if f.success else np.nan
    except Exception:return np.nan


def centerline(frames,y):
    out=np.full((frames.shape[0],frames.shape[2]),np.nan)
    for i,img in enumerate(frames):
        for j in range(img.shape[1]):out[i,j]=fitcol(y,img[:,j])
    return out


def true_runs(m):
    p=np.r_[False,np.asarray(m,bool),False];e=np.flatnonzero(p[1:]!=p[:-1]);return list(zip(e[::2],e[1::2]))


def mask_center(raw):
    ref=raw.copy();xx=np.arange(raw.shape[1])
    for row in ref:
        g=np.isfinite(row)
        if g.sum()>=2:row[~g]=np.interp(xx[~g],xx[g],row[g])
    loc=median_filter(ref,size=(1,LOCAL_WIDTH),mode="nearest")
    flag=np.isfinite(raw)&np.isfinite(loc)&(np.abs(raw-loc)>OUTLIER_PX)
    clean=raw.copy();clean[flag]=np.nan
    elig=np.ones(raw.shape[0],bool)
    for i in range(raw.shape[0]):
        denom=max(1,np.isfinite(raw[i]).sum());elig[i]=flag[i].sum()/denom<=MAX_FLAG_FRAC
        for a,b in true_runs(flag[i]):
            if b-a>MAX_INTERP_RUN:continue
            l,r=a-1,b
            if l>=0 and r<raw.shape[1] and np.isfinite(clean[i,l]) and np.isfinite(clean[i,r]):
                clean[i,a:b]=np.interp(np.arange(a,b),[l,r],[clean[i,l],clean[i,r]])
    return clean,flag,elig


def run_trial(args):
    file_label,patch_label,bg,peak,bgstats=args
    y,frames,truth=movie(bg,peak)
    raw=centerline(frames,y);clean,flag,elig=mask_center(raw)
    good=np.isfinite(clean)&np.isfinite(truth);err=np.abs(clean[good]-truth[good])
    return {"file":file_label,"patch":patch_label,"peak_sigma":peak,"status":"OK",**bgstats,
            "median_abs_error_px":float(np.median(err)),"p90_abs_error_px":float(np.quantile(err,.90)),
            "p99_abs_error_px":float(np.quantile(err,.99)),"max_abs_error_px":float(np.max(err)),
            "valid_fraction":float(np.mean(good)),"flagged_fraction":float(np.mean(flag)),
            "eligible_frame_fraction":float(np.mean(elig))}


def main():
    selected=choose_files(); report={"information_barrier":"2025-09-21 L2 controls only; zero R3 access",
        "correction_from_v1":"wide real source strips; every drifted frame uses real PUNCH pixels; no zero-filled sky",
        "selected_files":[n for _,n in selected],"patch_centers":PATCH_CENTERS,"trials":[]}
    for _,name in selected:
        path=download(name)
        with fits.open(path,memmap=True) as hdul:
            data=np.asarray(hdul[1].data,float)
            if tuple(data.shape)!=tuple(hdul[2].data.shape):raise RuntimeError("science/uncertainty shape mismatch")
            tasks=[]
            for label,(cx,cy) in PATCH_CENTERS.items():
                strip=extract_source_strip(data,cx,cy);bg,stats=standardize(strip)
                if bg is None:
                    report["trials"].append({"file":name,"patch":label,"status":"PATCH_INVALID",**stats});continue
                for peak in PEAKS:tasks.append((name,label,bg,peak,stats))
        with ProcessPoolExecutor(max_workers=4) as pool:
            futs=[pool.submit(run_trial,x) for x in tasks]
            for fut in as_completed(futs):report["trials"].append(fut.result())
        try:path.unlink()
        except OSError:pass

    good=[r for r in report["trials"] if r.get("status")=="OK"]
    s={"n_trials":len(good),"n_invalid_patches":sum(r.get("status")!="OK" for r in report["trials"])}
    if good:
        s.update({"p90_of_trial_p90_error_px":float(np.quantile([r["p90_abs_error_px"] for r in good],.90)),
            "worst_trial_p90_error_px":float(max(r["p90_abs_error_px"] for r in good)),
            "minimum_valid_fraction":float(min(r["valid_fraction"] for r in good)),
            "maximum_flagged_fraction":float(max(r["flagged_fraction"] for r in good)),
            "minimum_eligible_frame_fraction":float(min(r["eligible_frame_fraction"] for r in good)),"by_peak_sigma":{}})
        for peak in PEAKS:
            sub=[r for r in good if r["peak_sigma"]==peak]
            s["by_peak_sigma"][str(peak)]={"n":len(sub),"median_p90_error_px":float(np.median([r["p90_abs_error_px"] for r in sub])),
                "p90_trial_p90_error_px":float(np.quantile([r["p90_abs_error_px"] for r in sub],.90)),
                "min_valid_fraction":float(min(r["valid_fraction"] for r in sub)),
                "min_eligible_frame_fraction":float(min(r["eligible_frame_fraction"] for r in sub))}
    report["summary"]=s
    gate=bool(good) and s["p90_of_trial_p90_error_px"]<=1.5 and s["minimum_valid_fraction"]>=.98 and s["minimum_eligible_frame_fraction"]>=.90
    report["centerline_real_background_gate"]="PASS" if gate else "FAIL"
    (OUT/"summary.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(s,indent=2,sort_keys=True));print("GATE",report["centerline_real_background_gate"])
    return 0 if gate else 3

if __name__=="__main__":raise SystemExit(main())
