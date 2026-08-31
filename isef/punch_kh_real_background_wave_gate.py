#!/usr/bin/env python3
"""Full wave/growth discrimination on real non-target PUNCH backgrounds.

TARGET BLIND: imports the corrected 2025-09-21 background/extraction machinery
and never accesses C/2025 R3 files.
"""
from __future__ import annotations

import json
import math
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from astropy.io import fits

import punch_kh_real_background_controls_v2 as bg

OUT=Path("results/punch_kh_real_background_wave_gate")
OUT.mkdir(parents=True,exist_ok=True)

MIN_WAVELENGTH=6.0
MAX_WAVELENGTH=80.0
PHASE_R2_MIN=.98
SPECTRAL_CONCENTRATION_MIN=.20
DBIC_MIN=10.0
POS_WAVELENGTH_RELERR_MAX=.10
POS_SPEED_RELERR_MAX=.15
POS_GROWTH_RELERR_MAX=.25
POS_PASS_FRACTION_MIN=.80
NULL_FALSE_KH_MAX=0
PEAK_POS=[5.0,8.0]
PEAK_NULL=5.0
ONSET=10
SATURATION=34
TRUE_GAMMA=.35
BASE_AMP=1.5
STEP_CP=22
STEP_AFTER=BASE_AMP*math.exp(TRUE_GAMMA*((SATURATION-ONSET)*bg.DT))


def injected_movie(real_bg,peak,kind,seed=0):
    rng=np.random.default_rng(seed)
    y=np.arange(bg.NY)-(bg.NY-1)/2
    x=np.arange(bg.NX,dtype=float)
    t=np.arange(bg.NT)*bg.DT
    frames=[];truth=[]

    if kind=="random_knots":
        freq=np.fft.rfftfreq(bg.NX,d=1.0);f0=1/bg.WAVELENGTH
        env=np.exp(-.5*((freq-f0)/(0.7*f0))**2);env[0]=0
        base=env*np.exp(1j*rng.uniform(0,2*np.pi,len(freq)))

    for i,ti in enumerate(t):
        start=int(round(bg.DRIFT*i)); real=real_bg[:,start:start+bg.NX]
        if kind=="growth":
            logamp=np.log(BASE_AMP)+TRUE_GAMMA*np.clip(ti-t[ONSET],0,t[SATURATION]-t[ONSET])
            amp=math.exp(logamp)
            center=amp*np.sin(2*np.pi*(x-bg.SPEED*ti)/bg.WAVELENGTH+.3)
        elif kind=="step":
            amp=BASE_AMP if i<STEP_CP else STEP_AFTER
            center=amp*np.sin(2*np.pi*(x-bg.SPEED*ti)/bg.WAVELENGTH+.3)
        elif kind=="random_knots":
            shifted=base*np.exp(-2j*np.pi*freq*bg.SPEED*ti)
            center=np.fft.irfft(shifted,n=bg.NX)
            center=center/max(np.std(center),1e-12)*3.0
            center+=rng.normal(0,.15,bg.NX)
        else: raise ValueError(kind)
        truth.append(center)
        img=real.copy();bright=peak*(1-.30*x/bg.NX)
        for j,c in enumerate(center):
            img[:,j]+=bright[j]*np.exp(-.5*((y-c)/bg.TAIL_SIGMA)**2)
        frames.append(img)
    return y,t,np.asarray(frames),np.asarray(truth)


def r2(y,p):
    den=np.sum((y-np.mean(y))**2)
    return float(1-np.sum((y-p)**2)/den) if den>0 else float("nan")


def bic(rss,n,k):return float(n*np.log(max(rss/n,np.finfo(float).tiny))+k*np.log(n))


def positive_fit(x,y):
    X=np.c_[np.ones(len(x)),x];coef=np.linalg.lstsq(X,y,rcond=None)[0];b,m=map(float,coef)
    if m<0:m=0.;b=float(np.mean(y))
    pred=b+m*x;return b,m,float(np.sum((y-pred)**2))


def growth_compare(t,amp,minseg=6,ming=8):
    y=np.log(np.maximum(np.asarray(amp,float),np.finfo(float).tiny));n=len(y)
    rc=float(np.sum((y-np.mean(y))**2));bc=bic(rc,n,1)
    X=np.c_[np.ones(n),t-t[0]];coef=np.linalg.lstsq(X,y,rcond=None)[0];pl=X@coef;bl=bic(float(np.sum((y-pl)**2)),n,2)
    beststep=(np.inf,-1)
    for cp in range(minseg,n-minseg+1):
        pred=np.r_[np.full(cp,np.mean(y[:cp])),np.full(n-cp,np.mean(y[cp:]))];rss=float(np.sum((y-pred)**2))
        if rss<beststep[0]:beststep=(rss,cp)
    bs=bic(beststep[0],n,3)
    best=(np.inf,-1,-1,0.)
    for i0 in range(minseg,n-1-ming+1):
        first=i0+ming;last=n-1-minseg;inds=list(range(first,last+1)) if first<=last else []
        if n-1>=first:inds.append(n-1)
        for i1 in inds:
            xx=np.clip(t-t[i0],0,t[i1]-t[i0]);_,g,rss=positive_fit(xx,y)
            if rss<best[0]:best=(rss,i0,i1,g)
    bgrowth=bic(best[0],n,4);ds=bs-bgrowth;dc=bc-bgrowth;dl=bl-bgrowth
    return {"growth_rate":best[3],"onset_index":best[1],"saturation_index":best[2],
            "delta_bic_growth_over_step":float(ds),"delta_bic_growth_over_constant":float(dc),
            "delta_bic_growth_over_linear":float(dl),
            "growth_preferred":bool(best[3]>0 and ds>=DBIC_MIN and dc>=DBIC_MIN and dl>=DBIC_MIN)}


def infer_wave(clean,eligible,t):
    # No long-gap interpolation beyond the already frozen <=2-column mask repair.
    rowgood=np.asarray(eligible,bool)&np.all(np.isfinite(clean),axis=1)
    if np.mean(rowgood)<.90:return {"status":"INSUFFICIENT_COMPLETE_FRAMES","complete_frame_fraction":float(np.mean(rowgood))}
    yy=clean[rowgood];tt=t[rowgood];s=np.arange(bg.NX,dtype=float)
    yy=yy-np.mean(yy,axis=1,keepdims=True)
    ft=np.fft.rfft(yy,axis=1);freq=np.fft.rfftfreq(bg.NX,d=1.0);wave=np.full_like(freq,np.inf);pos=freq>0;wave[pos]=1/freq[pos]
    allow=pos&(wave>=MIN_WAVELENGTH)&(wave<=MAX_WAVELENGTH);inds=np.where(allow)[0]
    power=np.mean(np.abs(ft)**2,axis=0);j=int(inds[np.argmax(power[inds])]);f=float(freq[j]);w=1/f;k=2*np.pi*f
    coeff=ft[:,j];amp=2*np.abs(coeff)/bg.NX;phase=np.unwrap(np.angle(coeff));pc=np.polyfit(tt,phase,1);pp=np.polyval(pc,tt)
    speed=float(-pc[0]/k);pr2=r2(phase,pp);conc=float(power[j]/np.sum(power[allow]));gc=growth_compare(tt,amp)
    return {"status":"OK","complete_frame_fraction":float(np.mean(rowgood)),"wavelength":float(w),"phase_speed":speed,
            "phase_r2":pr2,"spectral_concentration":conc,"mode_amplitude":amp.tolist(),**gc}


def full_kh_call(r):
    return bool(r.get("status")=="OK" and r["phase_r2"]>=PHASE_R2_MIN and r["spectral_concentration"]>=SPECTRAL_CONCENTRATION_MIN and r["growth_preferred"])


def trial(args):
    file_label,patch,bgreal,peak,kind,seed=args
    y,t,frames,truth=injected_movie(bgreal,peak,kind,seed);raw=bg.centerline(frames,y);clean,flag,elig=bg.mask_center(raw);r=infer_wave(clean,elig,t)
    out={"file":file_label,"patch":patch,"peak_sigma":peak,"kind":kind,"seed":seed,"fit":r,"kh_call":full_kh_call(r),
         "flagged_fraction":float(np.mean(flag)),"eligible_frame_fraction":float(np.mean(elig))}
    if kind=="growth" and r.get("status")=="OK":
        out.update({"wavelength_relerr":abs(r["wavelength"]-bg.WAVELENGTH)/bg.WAVELENGTH,
                    "speed_relerr":abs(r["phase_speed"]-bg.SPEED)/bg.SPEED,
                    "growth_relerr":abs(r["growth_rate"]-TRUE_GAMMA)/TRUE_GAMMA})
        out["positive_pass"]=bool(out["kh_call"] and out["wavelength_relerr"]<=POS_WAVELENGTH_RELERR_MAX and out["speed_relerr"]<=POS_SPEED_RELERR_MAX and out["growth_relerr"]<=POS_GROWTH_RELERR_MAX)
    return out


def main():
    selected=bg.choose_files();report={"information_barrier":"2025-09-21 non-R3 backgrounds only; no R3 access",
        "frozen_gate":{"wavelength_px":[MIN_WAVELENGTH,MAX_WAVELENGTH],"phase_r2_min":PHASE_R2_MIN,
            "spectral_concentration_min":SPECTRAL_CONCENTRATION_MIN,"delta_bic_min_each":DBIC_MIN,
            "positive_wavelength_relerr_max":POS_WAVELENGTH_RELERR_MAX,"positive_speed_relerr_max":POS_SPEED_RELERR_MAX,
            "positive_growth_relerr_max":POS_GROWTH_RELERR_MAX,"positive_pass_fraction_min":POS_PASS_FRACTION_MIN,"null_false_kh_max":NULL_FALSE_KH_MAX},"trials":[]}
    for file_index,(_,name) in enumerate(selected):
        path=bg.download(name)
        with fits.open(path,memmap=True) as hdul:
            data=np.asarray(hdul[1].data,float);tasks=[]
            for patch,(cx,cy) in bg.PATCH_CENTERS.items():
                strip=bg.extract_source_strip(data,cx,cy);z,stats=bg.standardize(strip)
                if z is None:continue
                for peak in PEAK_POS:tasks.append((name,patch,z,peak,"growth",0))
                tasks.append((name,patch,z,PEAK_NULL,"step",0))
                tasks.append((name,patch,z,PEAK_NULL,"random_knots",1000+file_index))
        with ProcessPoolExecutor(max_workers=4) as pool:
            fut=[pool.submit(trial,x) for x in tasks]
            for f in as_completed(fut):report["trials"].append(f.result())
        try:path.unlink()
        except OSError:pass

    pos=[r for r in report["trials"] if r["kind"]=="growth"];null=[r for r in report["trials"] if r["kind"]!="growth"]
    summary={"positive_n":len(pos),"positive_pass_n":sum(r.get("positive_pass",False) for r in pos),
        "positive_pass_fraction":float(np.mean([r.get("positive_pass",False) for r in pos])) if pos else 0,
        "null_n":len(null),"null_false_kh_n":sum(r["kh_call"] for r in null),"by_kind":{}}
    for kind in ["growth","step","random_knots"]:
        ss=[r for r in report["trials"] if r["kind"]==kind]
        summary["by_kind"][kind]={"n":len(ss),"kh_call_fraction":float(np.mean([r["kh_call"] for r in ss])) if ss else None,
            "median_phase_r2":float(np.median([r["fit"].get("phase_r2",np.nan) for r in ss])),
            "median_spectral_concentration":float(np.median([r["fit"].get("spectral_concentration",np.nan) for r in ss]))}
    gate=summary["positive_pass_fraction"]>=POS_PASS_FRACTION_MIN and summary["null_false_kh_n"]<=NULL_FALSE_KH_MAX
    summary["gate"]="PASS" if gate else "FAIL";report["summary"]=summary
    (OUT/"summary.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps(summary,indent=2,sort_keys=True));return 0 if gate else 3

if __name__=="__main__":raise SystemExit(main())
