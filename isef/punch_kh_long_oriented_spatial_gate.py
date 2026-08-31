#!/usr/bin/env python3
"""Final long/oriented spatial real-background gate for PUNCH R3 KH.

TARGET BLIND. Uses three frozen 2025-09-21 CTM files, eight target-radius fields,
a 512x81 strip at the frozen target-like orientation, and a 5-sigma positive
wavelength grid 24/40/64/80 px. No R3 pixels are opened.
"""
from __future__ import annotations
import json, math
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import numpy as np
from astropy.io import fits
from scipy.ndimage import map_coordinates

import punch_kh_real_background_controls_v2 as bg
import punch_kh_real_background_wave_gate as wg

OUT=Path('results/punch_kh_long_oriented_spatial_gate');OUT.mkdir(parents=True,exist_ok=True)
NX=512; NY=81; NT=48; DT=bg.DT; DRIFT=bg.DRIFT
ORIENT=np.asarray([0.8035,0.5953],float);ORIENT/=np.linalg.norm(ORIENT)
CROSS=np.asarray([-ORIENT[1],ORIENT[0]])
RADII=[550,650];C0=2048
FIELDS={f'r{r}_{lab}':(C0+dx*r,C0+dy*r) for r in RADII for lab,(dx,dy) in {'E':(1,0),'W':(-1,0),'N':(0,1),'S':(0,-1)}.items()}
WAVES=[24.0,40.0,64.0,80.0]
PEAK=5.0
MAX_SHIFT=int(math.ceil(DRIFT*(NT-1)));SOURCE_NX=NX+MAX_SHIFT+4

# Make imported inference/extractor use the final 512-pixel coordinate.
bg.NX=NX; bg.NY=NY; bg.NT=NT; bg.MAX_SHIFT=MAX_SHIFT; bg.SOURCE_NX=SOURCE_NX


def oriented_source_strip(data,cx,cy):
    # Long coordinate spans a centered drift trajectory; cross coordinate is 81 px.
    ss=np.arange(SOURCE_NX,dtype=float)-(SOURCE_NX-1)/2
    yy=np.arange(NY,dtype=float)-(NY-1)/2
    S,Y=np.meshgrid(ss,yy)
    xx=cx + S*ORIENT[0] + Y*CROSS[0]
    ypix=cy + S*ORIENT[1] + Y*CROSS[1]
    if xx.min()<1 or ypix.min()<1 or xx.max()>data.shape[1]-2 or ypix.max()>data.shape[0]-2:
        raise RuntimeError('oriented control strip outside mosaic')
    return map_coordinates(np.asarray(data,float),[ypix,xx],order=1,mode='nearest')


def inject(real_bg,wavelength,kind,seed=0):
    rng=np.random.default_rng(seed); y=np.arange(NY)-(NY-1)/2; x=np.arange(NX,dtype=float);t=np.arange(NT)*DT
    frames=[];truth=[]
    if kind=='random_knots':
        freq=np.fft.rfftfreq(NX,d=1.0);f0=1/wavelength;env=np.exp(-.5*((freq-f0)/(0.7*f0))**2);env[0]=0
        base=env*np.exp(1j*rng.uniform(0,2*np.pi,len(freq)))
    for i,ti in enumerate(t):
        start=int(round(DRIFT*i));real=real_bg[:,start:start+NX]
        if kind=='growth':
            amp=wg.BASE_AMP*math.exp(wg.TRUE_GAMMA*np.clip(ti-t[wg.ONSET],0,t[wg.SATURATION]-t[wg.ONSET]))
            center=amp*np.sin(2*np.pi*(x-bg.SPEED*ti)/wavelength+.3)
        elif kind=='step':
            amp=wg.BASE_AMP if i<wg.STEP_CP else wg.STEP_AFTER
            center=amp*np.sin(2*np.pi*(x-bg.SPEED*ti)/wavelength+.3)
        elif kind=='random_knots':
            shifted=base*np.exp(-2j*np.pi*freq*bg.SPEED*ti);center=np.fft.irfft(shifted,n=NX)
            center=center/max(np.std(center),1e-12)*3.0+rng.normal(0,.15,NX)
        else:raise ValueError(kind)
        img=real.copy();bright=PEAK*(1-.30*x/NX)
        for j,c in enumerate(center):img[:,j]+=bright[j]*np.exp(-.5*((y-c)/bg.TAIL_SIGMA)**2)
        frames.append(img);truth.append(center)
    return y,t,np.asarray(frames),np.asarray(truth)


def trial(args):
    file_label,field,z,wave,kind,seed=args
    y,t,frames,truth=inject(z,wave,kind,seed);raw=bg.centerline(frames,y);clean,flag,elig=bg.mask_center(raw);fit=wg.infer_wave(clean,elig,t)
    good=np.isfinite(clean)&np.isfinite(truth);err=np.abs(clean[good]-truth[good]) if np.any(good) else np.asarray([np.inf])
    out={'file':file_label,'field':field,'wavelength_true':wave,'kind':kind,'seed':seed,'fit':fit,'kh_call':wg.full_kh_call(fit),
         'flagged_fraction':float(np.mean(flag)),'eligible_frame_fraction':float(np.mean(elig)),'valid_fraction':float(np.mean(good)),
         'median_abs_error_px':float(np.median(err)),'p90_abs_error_px':float(np.quantile(err,.90))}
    if kind=='growth' and fit.get('status')=='OK':
        out.update({'wavelength_relerr':abs(fit['wavelength']-wave)/wave,'speed_relerr':abs(fit['phase_speed']-bg.SPEED)/bg.SPEED,
                    'growth_relerr':abs(fit['growth_rate']-wg.TRUE_GAMMA)/wg.TRUE_GAMMA})
        out['positive_pass']=bool(out['kh_call'] and out['wavelength_relerr']<=wg.POS_WAVELENGTH_RELERR_MAX and out['speed_relerr']<=wg.POS_SPEED_RELERR_MAX and out['growth_relerr']<=wg.POS_GROWTH_RELERR_MAX)
    return out


def main():
    selected=bg.choose_files();trials=[]
    for fi,(_,name) in enumerate(selected):
        path=bg.download(name);tasks=[]
        with fits.open(path,memmap=True) as h:
            data=h[1].data
            for field,(cx,cy) in FIELDS.items():
                strip=oriented_source_strip(data,cx,cy);z,stats=bg.standardize(strip)
                if z is None:raise RuntimeError(f'invalid field {field}: {stats}')
                for wave in WAVES:tasks.append((name,field,z,wave,'growth',0))
                tasks.append((name,field,z,40.0,'step',0));tasks.append((name,field,z,40.0,'random_knots',5000+fi))
        with ProcessPoolExecutor(max_workers=4) as pool:
            fut=[pool.submit(trial,t) for t in tasks]
            for f in as_completed(fut):trials.append(f.result())
        try:path.unlink()
        except OSError:pass
    pos=[r for r in trials if r['kind']=='growth'];null=[r for r in trials if r['kind']!='growth']
    summary={'positive_n':len(pos),'positive_pass_n':sum(r.get('positive_pass',False) for r in pos),
      'positive_pass_fraction':float(np.mean([r.get('positive_pass',False) for r in pos])) if pos else 0.,
      'null_n':len(null),'null_false_kh_n':sum(r['kh_call'] for r in null),
      'p90_of_trial_p90_error_px':float(np.quantile([r['p90_abs_error_px'] for r in trials],.90)),
      'minimum_valid_fraction':float(min(r['valid_fraction'] for r in trials)),
      'minimum_eligible_frame_fraction':float(min(r['eligible_frame_fraction'] for r in trials)),
      'by_wavelength':{str(int(w)):{'n':sum(r['kind']=='growth' and r['wavelength_true']==w for r in trials),
        'pass_fraction':float(np.mean([r.get('positive_pass',False) for r in pos if r['wavelength_true']==w]))} for w in WAVES}}
    center_ok=summary['p90_of_trial_p90_error_px']<=wg.CENTERLINE_P90_OF_P90_MAX and summary['minimum_valid_fraction']>=wg.CENTERLINE_MIN_VALID and summary['minimum_eligible_frame_fraction']>=wg.CENTERLINE_MIN_ELIGIBLE
    wave_ok=summary['positive_pass_fraction']>=wg.POS_PASS_FRACTION_MIN and summary['null_false_kh_n']<=wg.NULL_FALSE_KH_MAX
    summary.update({'centerline_gate':'PASS' if center_ok else 'FAIL','wave_gate':'PASS' if wave_ok else 'FAIL','gate':'PASS' if center_ok and wave_ok else 'FAIL'})
    report={'information_barrier':'three 2025-09-21 non-R3 CTM files only; zero R3 pixels','roi':[NY,NX],'orientation_unit':ORIENT.tolist(),'fields':FIELDS,'wavelengths':WAVES,'peak_sigma':PEAK,'trials':trials,'summary':summary}
    (OUT/'summary.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(summary,indent=2,sort_keys=True));return 0 if center_ok and wave_ok else 3
if __name__=='__main__':raise SystemExit(main())
