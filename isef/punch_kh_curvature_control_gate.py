#!/usr/bin/env python3
"""Control-only validation of the frozen common quadratic curvature baseline.

TARGET BLIND. Uses one fixed 2025-09-21 CTM epoch and target-azimuth fields at
r=550/650. Tests downstream quadratic bends of 0/10/20 px with growing waves at
24/40/64/80 px, plus curved step/random nulls.
"""
from __future__ import annotations
import json,math
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
import numpy as np
from astropy.io import fits
from scipy.optimize import least_squares

import punch_kh_real_background_controls_v2 as bg
import punch_kh_real_background_wave_gate as wg
import punch_kh_long_oriented_spatial_gate as ls

OUT=Path('results/punch_kh_curvature_control_gate');OUT.mkdir(parents=True,exist_ok=True)
NX=ls.NX;NY=ls.NY;NT=ls.NT;bg.NX=NX;bg.NY=NY;bg.NT=NT
FIELDS={k:v for k,v in ls.FIELDS.items() if k in ('r550_a0','r650_a0')}
CURVES=[0.,10.,20.];WAVES=ls.WAVES;PEAK=ls.PEAK


def fitcol_general(y,flux,center0,halfwidth):
    keep=np.abs(y-center0)<=halfwidth;yy=y[keep];ff=np.asarray(flux[keep],float);good=np.isfinite(ff);yy=yy[good];ff=ff[good]
    if len(ff)<12:return np.nan
    edge=np.r_[ff[:4],ff[-4:]];b0=float(np.median(edge));amp0=max(float(np.max(ff)-b0),.05);scale=max(float(np.std(ff)),1.)
    p0=np.array([b0,0.,amp0,center0,3.]);lo=np.array([b0-20*scale,-5*scale,0.,center0-halfwidth,1.]);hi=np.array([b0+20*scale,5*scale,max(100*scale,amp0*2),center0+halfwidth,8.])
    def model(p):
        b,m,a,c,s=p;return b+m*yy+a*np.exp(-.5*((yy-c)/s)**2)
    try:
        f=least_squares(lambda p:ff-model(p),p0,bounds=(lo,hi),loss='soft_l1',f_scale=.5,max_nfev=400);return float(f.x[3]) if f.success else np.nan
    except Exception:return np.nan


def derive_baseline(frames,y):
    med=np.nanmedian(frames,axis=0);coarse=np.asarray([fitcol_general(y,med[:,j],0.,35.) for j in range(NX)])
    clean,flag,elig=bg.mask_center(coarse[None,:]);c=clean[0];x=np.linspace(-1,1,NX);keep=np.isfinite(c)
    if keep.mean()<.80:raise RuntimeError('insufficient coarse baseline columns')
    for _ in range(6):
        coef=np.polyfit(x[keep],c[keep],2);pred=np.polyval(coef,x);res=c-pred;mad=1.4826*np.nanmedian(np.abs(res[keep]-np.nanmedian(res[keep])));mad=max(float(mad),.25);new=keep&(np.abs(res)<=3*mad)
        if np.array_equal(new,keep):break
        keep=new
        if keep.mean()<.80:raise RuntimeError('curvature clipping below 80 percent')
    return np.polyval(np.polyfit(x[keep],c[keep],2),x),float(keep.mean())


def extract_relative(frames,y,baseline):
    raw=np.full((NT,NX),np.nan)
    for i,img in enumerate(frames):
        for j in range(NX):raw[i,j]=fitcol_general(y,img[:,j],float(baseline[j]),15.)-baseline[j]
    return bg.mask_center(raw)


def inject(real_bg,wave,curve_amp,kind,seed=0):
    rng=np.random.default_rng(seed);y=np.arange(NY)-(NY-1)/2;x=np.arange(NX,dtype=float);t=np.arange(NT)*bg.DT;q=x/(NX-1);basecurve=curve_amp*q*q;frames=[];truthrel=[]
    if kind=='random_knots':
        freq=np.fft.rfftfreq(NX,d=1.);f0=1/wave;env=np.exp(-.5*((freq-f0)/(0.7*f0))**2);env[0]=0;base=env*np.exp(1j*rng.uniform(0,2*np.pi,len(freq)))
    for i,ti in enumerate(t):
        start=int(round(bg.DRIFT*i));real=real_bg[:,start:start+NX]
        if kind=='growth':
            amp=wg.BASE_AMP*np.exp(wg.TRUE_GAMMA*np.clip(ti-t[wg.ONSET],0,t[wg.SATURATION]-t[wg.ONSET]));rel=amp*np.sin(2*np.pi*(x-bg.SPEED*ti)/wave+.3)
        elif kind=='step':
            amp=wg.BASE_AMP if i<wg.STEP_CP else wg.STEP_AFTER;rel=amp*np.sin(2*np.pi*(x-bg.SPEED*ti)/wave+.3)
        elif kind=='random_knots':
            shifted=base*np.exp(-2j*np.pi*freq*bg.SPEED*ti);rel=np.fft.irfft(shifted,n=NX);rel=rel/max(np.std(rel),1e-12)*3+rng.normal(0,.15,NX)
        else:raise ValueError(kind)
        center=basecurve+rel;img=real.copy();bright=PEAK*(1-.30*x/NX)
        for j,c in enumerate(center):img[:,j]+=bright[j]*np.exp(-.5*((y-c)/bg.TAIL_SIGMA)**2)
        frames.append(img);truthrel.append(rel)
    return y,t,np.asarray(frames),np.asarray(truthrel),basecurve


def trial(args):
    label,z,wave,curve,kind,seed=args;y,t,frames,truth,base=inject(z,wave,curve,kind,seed);baseline,base_valid=derive_baseline(frames,y);clean,flag,elig=extract_relative(frames,y,baseline);fit=wg.infer_wave(clean,elig,t)
    good=np.isfinite(clean)&np.isfinite(truth);err=np.abs(clean[good]-truth[good]) if np.any(good) else np.asarray([np.inf])
    out={'field':label,'wavelength_true':wave,'curve_end_px':curve,'kind':kind,'fit':fit,'kh_call':wg.full_kh_call(fit),'baseline_column_fraction':base_valid,'baseline_rmse_px':float(np.sqrt(np.mean((baseline-base)**2))),'valid_fraction':float(np.mean(good)),'eligible_frame_fraction':float(np.mean(elig)),'p90_abs_error_px':float(np.quantile(err,.90))}
    if kind=='growth' and fit.get('status')=='OK':
        out.update({'wavelength_relerr':abs(fit['wavelength']-wave)/wave,'speed_relerr':abs(fit['phase_speed']-bg.SPEED)/bg.SPEED,'growth_relerr':abs(fit['growth_rate']-wg.TRUE_GAMMA)/wg.TRUE_GAMMA})
        out['positive_pass']=bool(out['kh_call'] and out['wavelength_relerr']<=wg.POS_WAVELENGTH_RELERR_MAX and out['speed_relerr']<=wg.POS_SPEED_RELERR_MAX and out['growth_relerr']<=wg.POS_GROWTH_RELERR_MAX)
    return out


def main():
    # fixed middle control file nearest 08:00
    selected=bg.choose_files();name=selected[1][1];path=bg.download(name);tasks=[]
    with fits.open(path,memmap=True) as h:
        data=h[1].data
        for label,field in FIELDS.items():
            strip=ls.radial_source_strip(data,field);z,stats=bg.standardize(strip)
            if z is None:raise RuntimeError(f'invalid {label}: {stats}')
            for c in CURVES:
                for w in WAVES:tasks.append((label,z,w,c,'growth',0))
                tasks.append((label,z,40.,c,'step',0));tasks.append((label,z,40.,c,'random_knots',9000+int(c)))
    trials=[]
    with ProcessPoolExecutor(max_workers=4) as pool:
        fs=[pool.submit(trial,t) for t in tasks]
        for f in as_completed(fs):trials.append(f.result())
    pos=[r for r in trials if r['kind']=='growth'];null=[r for r in trials if r['kind']!='growth']
    summary={'positive_n':len(pos),'positive_pass_n':sum(r.get('positive_pass',False) for r in pos),'positive_pass_fraction':float(np.mean([r.get('positive_pass',False) for r in pos])),'null_n':len(null),'null_false_kh_n':sum(r['kh_call'] for r in null),'p90_of_trial_p90_error_px':float(np.quantile([r['p90_abs_error_px'] for r in trials],.90)),'minimum_valid_fraction':float(min(r['valid_fraction'] for r in trials)),'minimum_eligible_frame_fraction':float(min(r['eligible_frame_fraction'] for r in trials)),'maximum_baseline_rmse_px':float(max(r['baseline_rmse_px'] for r in trials)),'by_curve':{str(int(c)):{'pass_fraction':float(np.mean([r.get('positive_pass',False) for r in pos if r['curve_end_px']==c]))} for c in CURVES}}
    center_ok=summary['p90_of_trial_p90_error_px']<=wg.CENTERLINE_P90_OF_P90_MAX and summary['minimum_valid_fraction']>=wg.CENTERLINE_MIN_VALID and summary['minimum_eligible_frame_fraction']>=wg.CENTERLINE_MIN_ELIGIBLE;wave_ok=summary['positive_pass_fraction']>=wg.POS_PASS_FRACTION_MIN and summary['null_false_kh_n']<=wg.NULL_FALSE_KH_MAX
    summary.update({'centerline_gate':'PASS' if center_ok else 'FAIL','wave_gate':'PASS' if wave_ok else 'FAIL','gate':'PASS' if center_ok and wave_ok else 'FAIL'})
    report={'information_barrier':'one 2025-09-21 non-R3 CTM file only; zero R3 pixels','file':name,'fields':list(FIELDS),'curves_px':CURVES,'wavelengths':WAVES,'peak_sigma':PEAK,'trials':trials,'summary':summary}
    (OUT/'summary.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(summary,indent=2,sort_keys=True));return 0 if center_ok and wave_ok else 3
if __name__=='__main__':raise SystemExit(main())
