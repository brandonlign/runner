#!/usr/bin/env python3
"""Wave/null gate on 48 distinct real non-R3 PUNCH CTM epochs.

TARGET BLIND: only 2025-09-21 Level-2 CTM v0l controls are opened. The control
sequence is chosen mechanically as the earliest exact 48-frame contiguous
8-minute run. Fixed E/W/N/S field locations are used without appearance-based
selection. Each movie frame comes from a different real CTM epoch.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import requests
from astropy.io import fits

import punch_kh_real_background_controls_v2 as bg
import punch_kh_real_background_wave_gate as wg

ROOT=bg.ROOT
OUT=Path("results/punch_kh_temporal_background_wave_gate")
OUT.mkdir(parents=True,exist_ok=True)
FILE_RE=re.compile(r'href=["\'](PUNCH_L2_CTM_(20250921\d{6})_v0l\.fits)["\']',re.I)
NT=48
CADENCE_S=480
PEAK_POS=[5.0,8.0]
PEAK_NULL=5.0


def list_exact_run():
    r=requests.get(ROOT,timeout=(10,30));r.raise_for_status()
    rows=[]
    for name,stamp in FILE_RE.findall(r.text):
        hh=int(stamp[8:10]);mm=int(stamp[10:12]);ss=int(stamp[12:14])
        sec=hh*3600+mm*60+ss
        rows.append((sec,name,stamp))
    rows=sorted(set(rows))
    for i in range(0,len(rows)-NT+1):
        sub=rows[i:i+NT]
        if all(sub[j+1][0]-sub[j][0]==CADENCE_S for j in range(NT-1)):
            return sub
    raise RuntimeError("no exact contiguous 48-epoch v0l run on frozen date")


def read_cutouts(run):
    # Fixed preregistered locations, same 81x192 field used by the estimator.
    cubes={k:[] for k in bg.PATCH_CENTERS}
    for idx,(_,name,stamp) in enumerate(run):
        url=ROOT+name
        print("CUTOUT",idx+1,"/",len(run),name,flush=True)
        with fits.open(url,use_fsspec=True,fsspec_kwargs={"block_size":1024*1024},memmap=False) as hdul:
            if tuple(hdul[1].shape)!=(4096,4096):
                raise RuntimeError(f"unexpected CTM shape {hdul[1].shape}")
            for label,(cx,cy) in bg.PATCH_CENTERS.items():
                x0=int(round(cx-bg.NX/2));x1=x0+bg.NX
                y0=int(round(cy-bg.NY/2));y1=y0+bg.NY
                arr=np.asarray(hdul[1].section[y0:y1,x0:x1],float)
                if arr.shape!=(bg.NY,bg.NX):raise RuntimeError("cutout shape mismatch")
                cubes[label].append(arr)
    return {k:np.asarray(v,float) for k,v in cubes.items()}


def standardize_temporal(cube):
    # Remove only a per-epoch DC level; use one pooled robust scale for the
    # entire 48-epoch field so epoch-to-epoch structured variation is retained.
    meds=np.nanmedian(cube,axis=(1,2))
    centered=cube-meds[:,None,None]
    frame_mad=np.nanmedian(np.abs(centered),axis=(1,2))
    pooled=float(np.nanmedian(1.4826*frame_mad))
    if not np.isfinite(pooled) or pooled<=0:raise RuntimeError("invalid pooled background scale")
    z=centered/pooled
    finite=np.isfinite(z)
    if finite.mean()<.98:raise RuntimeError("temporal control cube insufficiently finite")
    z[~finite]=0.0
    return z,{"pooled_robust_sigma":pooled,"finite_fraction":float(finite.mean())}


def injected_temporal(cube,peak,kind,seed=0):
    # Reuse the already frozen synthetic mode definitions from wg, substituting
    # the distinct real background frame at each cadence epoch.
    rng=np.random.default_rng(seed)
    y=np.arange(bg.NY)-(bg.NY-1)/2
    x=np.arange(bg.NX,dtype=float)
    t=np.arange(NT)*bg.DT
    frames=[];truth=[]
    if kind=="random_knots":
        freq=np.fft.rfftfreq(bg.NX,d=1.0);f0=1/bg.WAVELENGTH
        env=np.exp(-.5*((freq-f0)/(0.7*f0))**2);env[0]=0
        base=env*np.exp(1j*rng.uniform(0,2*np.pi,len(freq)))
    for i,ti in enumerate(t):
        if kind=="growth":
            logamp=np.log(wg.BASE_AMP)+wg.TRUE_GAMMA*np.clip(ti-t[wg.ONSET],0,t[wg.SATURATION]-t[wg.ONSET])
            amp=np.exp(logamp);center=amp*np.sin(2*np.pi*(x-bg.SPEED*ti)/bg.WAVELENGTH+.3)
        elif kind=="step":
            amp=wg.BASE_AMP if i<wg.STEP_CP else wg.STEP_AFTER
            center=amp*np.sin(2*np.pi*(x-bg.SPEED*ti)/bg.WAVELENGTH+.3)
        elif kind=="random_knots":
            shifted=base*np.exp(-2j*np.pi*freq*bg.SPEED*ti)
            center=np.fft.irfft(shifted,n=bg.NX)
            center=center/max(np.std(center),1e-12)*3.0
            center+=rng.normal(0,.15,bg.NX)
        else:raise ValueError(kind)
        img=cube[i].copy();bright=peak*(1-.30*x/bg.NX)
        for j,c in enumerate(center):
            img[:,j]+=bright[j]*np.exp(-.5*((y-c)/bg.TAIL_SIGMA)**2)
        frames.append(img);truth.append(center)
    return y,t,np.asarray(frames),np.asarray(truth)


def trial(args):
    patch,cube,peak,kind,seed=args
    y,t,frames,truth=injected_temporal(cube,peak,kind,seed)
    raw=bg.centerline(frames,y);clean,flag,elig=bg.mask_center(raw)
    fit=wg.infer_wave(clean,elig,t)
    out={"patch":patch,"peak_sigma":peak,"kind":kind,"seed":seed,"fit":fit,
         "kh_call":wg.full_kh_call(fit),"flagged_fraction":float(np.mean(flag)),
         "eligible_frame_fraction":float(np.mean(elig))}
    good=np.isfinite(clean)&np.isfinite(truth)
    if np.any(good):
        err=np.abs(clean[good]-truth[good]);out.update({"median_abs_error_px":float(np.median(err)),
            "p90_abs_error_px":float(np.quantile(err,.90)),"valid_fraction":float(np.mean(good))})
    if kind=="growth" and fit.get("status")=="OK":
        out.update({"wavelength_relerr":abs(fit["wavelength"]-bg.WAVELENGTH)/bg.WAVELENGTH,
                    "speed_relerr":abs(fit["phase_speed"]-bg.SPEED)/bg.SPEED,
                    "growth_relerr":abs(fit["growth_rate"]-wg.TRUE_GAMMA)/wg.TRUE_GAMMA})
        out["positive_pass"]=bool(out["kh_call"] and out["wavelength_relerr"]<=wg.POS_WAVELENGTH_RELERR_MAX and
                                  out["speed_relerr"]<=wg.POS_SPEED_RELERR_MAX and out["growth_relerr"]<=wg.POS_GROWTH_RELERR_MAX)
    return out


def main():
    run=list_exact_run();cubes=read_cutouts(run)
    zcubes={};stats={}
    for patch,cube in cubes.items():zcubes[patch],stats[patch]=standardize_temporal(cube)
    tasks=[]
    for pi,(patch,cube) in enumerate(zcubes.items()):
        for peak in PEAK_POS:tasks.append((patch,cube,peak,"growth",0))
        tasks.append((patch,cube,PEAK_NULL,"step",0))
        tasks.append((patch,cube,PEAK_NULL,"random_knots",2000+pi))
    trials=[]
    with ProcessPoolExecutor(max_workers=4) as pool:
        futs=[pool.submit(trial,x) for x in tasks]
        for f in as_completed(futs):trials.append(f.result())
    pos=[r for r in trials if r["kind"]=="growth"];null=[r for r in trials if r["kind"]!="growth"]
    summary={"selected_start":run[0][2],"selected_end":run[-1][2],"n_epochs":len(run),
      "positive_n":len(pos),"positive_pass_n":sum(r.get("positive_pass",False) for r in pos),
      "positive_pass_fraction":float(np.mean([r.get("positive_pass",False) for r in pos])) if pos else 0.0,
      "null_n":len(null),"null_false_kh_n":sum(r["kh_call"] for r in null),
      "p90_of_trial_p90_error_px":float(np.quantile([r.get("p90_abs_error_px",np.inf) for r in trials],.90)),
      "minimum_valid_fraction":float(min(r.get("valid_fraction",0.0) for r in trials)),
      "minimum_eligible_frame_fraction":float(min(r["eligible_frame_fraction"] for r in trials))}
    gate=summary["positive_pass_fraction"]>=wg.POS_PASS_FRACTION_MIN and summary["null_false_kh_n"]<=wg.NULL_FALSE_KH_MAX
    summary["gate"]="PASS" if gate else "FAIL"
    report={"information_barrier":"48 distinct 2025-09-21 non-R3 L2 CTM v0l epochs only; zero R3 access",
      "selection_rule":"earliest exact contiguous 48-frame v0l run at 8-minute cadence",
      "selected_files":[name for _,name,_ in run],"patch_stats":stats,"trials":trials,"summary":summary}
    (OUT/"summary.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,indent=2,sort_keys=True));return 0 if gate else 3

if __name__=="__main__":raise SystemExit(main())
