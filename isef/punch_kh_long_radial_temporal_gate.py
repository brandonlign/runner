#!/usr/bin/env python3
"""Final 48-epoch long/radial temporal real-background gate for PUNCH R3 KH.

TARGET BLIND. Reads only rotated 512x81-equivalent sections from 48 distinct
2025-09-21 CTM v0l epochs at eight fixed control starts. No R3 pixels.
"""
from __future__ import annotations
import json,re,time
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
import numpy as np
import requests
from astropy.io import fits
from scipy.ndimage import map_coordinates

import punch_kh_real_background_controls_v2 as bg
import punch_kh_real_background_wave_gate as wg
import punch_kh_long_oriented_spatial_gate as ls

OUT=Path('results/punch_kh_long_radial_temporal_gate');OUT.mkdir(parents=True,exist_ok=True)
ROOT=bg.ROOT;FILE_RE=re.compile(r'href=["\'](PUNCH_L2_CTM_(20250921\d{6})_v0l\.fits)["\']',re.I)
NT=48;CADENCE_S=480;WAVES=ls.WAVES;PEAK=ls.PEAK;NX=ls.NX;NY=ls.NY
EPOCH_RETRIES=5
bg.NX=NX;bg.NY=NY;bg.NT=NT


def exact_run():
    r=requests.get(ROOT,timeout=(10,30));r.raise_for_status();rows=[]
    for name,stamp in FILE_RE.findall(r.text):
        sec=int(stamp[8:10])*3600+int(stamp[10:12])*60+int(stamp[12:14]);rows.append((sec,name,stamp))
    rows=sorted(set(rows))
    for i in range(len(rows)-NT+1):
        sub=rows[i:i+NT]
        if all(sub[j+1][0]-sub[j][0]==CADENCE_S for j in range(NT-1)):return sub
    raise RuntimeError('no exact 48-frame v0l run')


def remote_radial_patch(hdu,field):
    cx,cy=field['center'];u=np.asarray(field['u'],float);v=np.asarray([-u[1],u[0]])
    s=np.arange(NX,dtype=float);q=np.arange(NY,dtype=float)-(NY-1)/2;S,Q=np.meshgrid(s,q)
    xx=cx+S*u[0]+Q*v[0];yy=cy+S*u[1]+Q*v[1]
    x0=max(0,int(np.floor(xx.min()))-2);x1=min(4096,int(np.ceil(xx.max()))+3)
    y0=max(0,int(np.floor(yy.min()))-2);y1=min(4096,int(np.ceil(yy.max()))+3)
    tile=np.asarray(hdu.section[y0:y1,x0:x1],float)
    return map_coordinates(tile,[yy-y0,xx-x0],order=1,mode='nearest')


def read_epoch(name):
    """Read all eight frozen patches atomically; retry only transport/runtime I/O.

    No patch is committed to the time cube until every field for this exact epoch
    has been obtained, preventing duplicates if a range request fails mid-epoch.
    """
    last=None
    for attempt in range(1,EPOCH_RETRIES+1):
        try:
            tmp={}
            with fits.open(ROOT+name,use_fsspec=True,
                           fsspec_kwargs={'block_size':1024*1024},memmap=False) as h:
                if tuple(h[1].shape)!=(4096,4096):raise RuntimeError('unexpected CTM shape')
                for label,field in ls.FIELDS.items():
                    tmp[label]=remote_radial_patch(h[1],field)
            return tmp
        except Exception as exc:
            last=exc
            if attempt>=EPOCH_RETRIES:break
            print('  transport retry',attempt,'/',EPOCH_RETRIES,'for',name,type(exc).__name__,flush=True)
            time.sleep(5*attempt)
    raise RuntimeError(f'failed frozen epoch {name} after {EPOCH_RETRIES} transport attempts') from last


def read_cubes(run):
    cubes={k:[] for k in ls.FIELDS}
    for i,(_,name,_) in enumerate(run):
        print('EPOCH',i+1,'/',len(run),name,flush=True)
        epoch=read_epoch(name)
        for label in ls.FIELDS:cubes[label].append(epoch[label])
    return {k:np.asarray(v,float) for k,v in cubes.items()}


def standardize(cube):
    meds=np.nanmedian(cube,axis=(1,2));centered=cube-meds[:,None,None];fm=np.nanmedian(np.abs(centered),axis=(1,2));scale=float(np.nanmedian(1.4826*fm))
    if not np.isfinite(scale) or scale<=0:raise RuntimeError('bad pooled scale')
    z=centered/scale;finite=np.isfinite(z)
    if finite.mean()<.98:raise RuntimeError('insufficient finite background')
    z[~finite]=0.;return z,{'pooled_robust_sigma':scale,'finite_fraction':float(finite.mean())}


def inject(cube,wavelength,kind,seed=0):
    rng=np.random.default_rng(seed);y=np.arange(NY)-(NY-1)/2;x=np.arange(NX,dtype=float);t=np.arange(NT)*bg.DT;frames=[];truth=[]
    if kind=='random_knots':
        freq=np.fft.rfftfreq(NX,d=1.);f0=1/wavelength;env=np.exp(-.5*((freq-f0)/(0.7*f0))**2);env[0]=0;base=env*np.exp(1j*rng.uniform(0,2*np.pi,len(freq)))
    for i,ti in enumerate(t):
        if kind=='growth':
            amp=wg.BASE_AMP*np.exp(wg.TRUE_GAMMA*np.clip(ti-t[wg.ONSET],0,t[wg.SATURATION]-t[wg.ONSET]));center=amp*np.sin(2*np.pi*(x-bg.SPEED*ti)/wavelength+.3)
        elif kind=='step':
            amp=wg.BASE_AMP if i<wg.STEP_CP else wg.STEP_AFTER;center=amp*np.sin(2*np.pi*(x-bg.SPEED*ti)/wavelength+.3)
        elif kind=='random_knots':
            shifted=base*np.exp(-2j*np.pi*freq*bg.SPEED*ti);center=np.fft.irfft(shifted,n=NX);center=center/max(np.std(center),1e-12)*3+rng.normal(0,.15,NX)
        else:raise ValueError(kind)
        img=cube[i].copy();bright=PEAK*(1-.30*x/NX)
        for j,c in enumerate(center):img[:,j]+=bright[j]*np.exp(-.5*((y-c)/bg.TAIL_SIGMA)**2)
        frames.append(img);truth.append(center)
    return y,t,np.asarray(frames),np.asarray(truth)


def trial(args):
    label,cube,wave,kind,seed=args;y,t,frames,truth=inject(cube,wave,kind,seed);raw=bg.centerline(frames,y);clean,flag,elig=bg.mask_center(raw);fit=wg.infer_wave(clean,elig,t)
    good=np.isfinite(clean)&np.isfinite(truth);err=np.abs(clean[good]-truth[good]) if np.any(good) else np.asarray([np.inf])
    out={'field':label,'wavelength_true':wave,'kind':kind,'seed':seed,'fit':fit,'kh_call':wg.full_kh_call(fit),'flagged_fraction':float(np.mean(flag)),'eligible_frame_fraction':float(np.mean(elig)),'valid_fraction':float(np.mean(good)),'median_abs_error_px':float(np.median(err)),'p90_abs_error_px':float(np.quantile(err,.90))}
    if kind=='growth' and fit.get('status')=='OK':
        out.update({'wavelength_relerr':abs(fit['wavelength']-wave)/wave,'speed_relerr':abs(fit['phase_speed']-bg.SPEED)/bg.SPEED,'growth_relerr':abs(fit['growth_rate']-wg.TRUE_GAMMA)/wg.TRUE_GAMMA})
        out['positive_pass']=bool(out['kh_call'] and out['wavelength_relerr']<=wg.POS_WAVELENGTH_RELERR_MAX and out['speed_relerr']<=wg.POS_SPEED_RELERR_MAX and out['growth_relerr']<=wg.POS_GROWTH_RELERR_MAX)
    return out


def main():
    run=exact_run();raw=read_cubes(run);cubes={};stats={}
    for k,v in raw.items():cubes[k],stats[k]=standardize(v)
    tasks=[]
    for i,(label,cube) in enumerate(cubes.items()):
        for w in WAVES:tasks.append((label,cube,w,'growth',0))
        tasks.append((label,cube,40.,'step',0));tasks.append((label,cube,40.,'random_knots',7000+i))
    trials=[]
    with ProcessPoolExecutor(max_workers=4) as pool:
        fs=[pool.submit(trial,t) for t in tasks]
        for f in as_completed(fs):trials.append(f.result())
    pos=[r for r in trials if r['kind']=='growth'];null=[r for r in trials if r['kind']!='growth']
    summary={'selected_start':run[0][2],'selected_end':run[-1][2],'n_epochs':len(run),'positive_n':len(pos),'positive_pass_n':sum(r.get('positive_pass',False) for r in pos),'positive_pass_fraction':float(np.mean([r.get('positive_pass',False) for r in pos])) if pos else 0.,'null_n':len(null),'null_false_kh_n':sum(r['kh_call'] for r in null),'p90_of_trial_p90_error_px':float(np.quantile([r['p90_abs_error_px'] for r in trials],.90)),'minimum_valid_fraction':float(min(r['valid_fraction'] for r in trials)),'minimum_eligible_frame_fraction':float(min(r['eligible_frame_fraction'] for r in trials)),'by_wavelength':{str(int(w)):{'n':sum(r['kind']=='growth' and r['wavelength_true']==w for r in trials),'pass_fraction':float(np.mean([r.get('positive_pass',False) for r in pos if r['wavelength_true']==w]))} for w in WAVES}}
    center_ok=summary['p90_of_trial_p90_error_px']<=wg.CENTERLINE_P90_OF_P90_MAX and summary['minimum_valid_fraction']>=wg.CENTERLINE_MIN_VALID and summary['minimum_eligible_frame_fraction']>=wg.CENTERLINE_MIN_ELIGIBLE;wave_ok=summary['positive_pass_fraction']>=wg.POS_PASS_FRACTION_MIN and summary['null_false_kh_n']<=wg.NULL_FALSE_KH_MAX
    summary.update({'centerline_gate':'PASS' if center_ok else 'FAIL','wave_gate':'PASS' if wave_ok else 'FAIL','gate':'PASS' if center_ok and wave_ok else 'FAIL'})
    sf={k:{'center':[float(x) for x in v['center']],'u':[float(x) for x in v['u']]} for k,v in ls.FIELDS.items()}
    report={'information_barrier':'48 distinct 2025-09-21 non-R3 CTM v0l epochs only; zero R3 pixels','selection_rule':'earliest exact contiguous 48-frame v0l run at 8-minute cadence','transport_rule':f'atomic eight-field epoch reads with up to {EPOCH_RETRIES} retries; science arrays and frozen metrics unchanged','roi':[NY,NX],'fields':sf,'wavelengths':WAVES,'peak_sigma':PEAK,'selected_files':[n for _,n,_ in run],'patch_stats':stats,'trials':trials,'summary':summary}
    (OUT/'summary.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(summary,indent=2,sort_keys=True));return 0 if center_ok and wave_ok else 3
if __name__=='__main__':raise SystemExit(main())
