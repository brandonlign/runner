#!/usr/bin/env python3
"""Stage-3 mutual-event detector development on the already-open 6764 positive only.

Stage-2 correctly separated the event harmonic (~15.20 h) from the rotational
alias (~2.37 h), but its single box forced alternating primary/secondary events
to share one depth. Stage-3 evaluates the raw-BLS event period P and 2P.  The
2P hypothesis contains two independent eclipse boxes separated by P, matching
the physical primary/secondary mutual-event geometry while retaining a compact
model.  No frozen null-control or Year-8 light curve may be opened here.
"""
from __future__ import annotations
import json, math, hashlib
from pathlib import Path
import numpy as np, requests
from astropy.timeseries import LombScargle
import tess_binary_stage0_detector as s0

OUT=Path('results/tess_binary_stage3_development');OUT.mkdir(parents=True,exist_ok=True)
URL='https://archive.konkoly.hu/pub/tssys/dr1/lightcurves_spectra/6764.lc'
PUBLISHED_ROT_H=4.739
PUBLISHED_ORBIT_H=30.41
EVENT_MASK_PAD=1.5
ROT_HARMONICS=4
EVENT_SMOOTH_HARMONICS=4
MIN_DEPTH_SNR=6.0
MIN_EVENTS=3
MIN_DBIC_ROT_ONLY=20.0
MIN_DBIC_SMOOTH=10.0


def fourier_design(t,period_d,tref,harmonics,linear=False):
    x=np.asarray(t,float)-float(tref);cols=[np.ones(len(x))]
    if linear:cols.append(x)
    w=2*np.pi/period_d
    for h in range(1,harmonics+1):cols += [np.sin(h*w*x),np.cos(h*w*x)]
    return np.column_stack(cols)


def fit(X,y,dy):
    w=1/np.asarray(dy,float);b=np.linalg.lstsq(X*w[:,None],y*w,rcond=None)[0];m=X@b
    return b,float(np.sum(((y-m)/dy)**2))


def bic(rss,n,k):return float(n*np.log(max(rss/n,1e-300))+k*np.log(n))


def phase(t,t0,P):return ((t-t0+0.5*P)%P)-0.5*P


def base_event_mask(t,b,pad=EVENT_MASK_PAD):return np.abs(phase(t,b['transit_time'],b['period_d']))<=pad*b['duration_d']/2


def estimate_rotation(t,y,dy):
    base=float(t.max()-t.min());fmin=24/s0.ROT_P_MAX_H;fmax=24/s0.ROT_P_MIN_H;df=1/(s0.ROT_OVERSAMPLE*base)
    freq=np.arange(fmin,fmax+0.5*df,df);ls=LombScargle(t,y-np.median(y),dy,fit_mean=True,center_data=True)
    power=np.asarray(ls.power(freq),float);j=int(np.nanargmax(power));return float(1/freq[j]),float(power[j])


def compare_hypothesis(t,y,dy,b,rot_p,mult):
    Pe=b['period_d'];Porb=mult*Pe;t0=b['transit_time'];dur=b['duration_d'];tref=float(np.median(t))
    Xr=fourier_design(t,rot_p,tref,ROT_HARMONICS,linear=True)
    if mult==1:
        boxes=[(np.abs(phase(t,t0,Porb))<=dur/2).astype(float)]
    elif mult==2:
        boxes=[(np.abs(phase(t,t0,Porb))<=dur/2).astype(float),
               (np.abs(phase(t,t0+Pe,Porb))<=dur/2).astype(float)]
    else:raise ValueError(mult)
    Xb=np.column_stack([Xr,*boxes])
    Xe=fourier_design(t,Porb,tref,EVENT_SMOOTH_HARMONICS,linear=False)[:,1:]
    Xs=np.column_stack([Xr,Xe])
    br,rr=fit(Xr,y,dy);bb,rb=fit(Xb,y,dy);bs,rs=fit(Xs,y,dy);n=len(t)
    BicR=bic(rr,n,Xr.shape[1]);BicB=bic(rb,n,Xb.shape[1]);BicS=bic(rs,n,Xs.shape[1])
    return {'orbit_multiplier':mult,'physical_period_d':float(Porb),'physical_period_h':float(Porb*24),
            'box_depths_faintness':[float(x) for x in bb[-len(boxes):]],
            'bic_rotation_only':BicR,'bic_binary_boxes':BicB,'bic_rotation_plus_smooth':BicS,
            'delta_bic_rotation_only_minus_binary':BicR-BicB,
            'delta_bic_smooth_minus_binary':BicS-BicB,
            'binary_added_parameter_n':len(boxes),'smooth_added_parameter_n':int(Xe.shape[1])}


def observed_event_count(t,b):
    P=b['period_d'];dur=b['duration_d'];t0=b['transit_time'];k0=math.floor((t.min()-t0)/P)-1;k1=math.ceil((t.max()-t0)/P)+1
    return int(sum(int((np.abs(t-(t0+k*P))<=dur/2).sum())>=2 for k in range(k0,k1+1)))


def sanitize(x):
    if isinstance(x,dict):return {k:sanitize(v) for k,v in x.items()}
    if isinstance(x,list):return [sanitize(v) for v in x]
    if isinstance(x,(np.bool_,bool)):return bool(x)
    if isinstance(x,np.integer):return int(x)
    if isinstance(x,(np.floating,float)):
        v=float(x);return v if math.isfinite(v) else None
    return x


def main():
    r=requests.get(URL,timeout=120,headers={'User-Agent':'ISEF-stage3-dev-positive-only/1.0'});r.raise_for_status();raw=OUT/'6764.lc';raw.write_bytes(r.content)
    a=np.loadtxt(raw);t,y,dy=s0.clean_input(a[:,1],a[:,4],a[:,5],a[:,9].astype(int))
    b,_=s0.scan_bls(t,y-np.median(y),dy);masked=base_event_mask(t,b);rot_p,rot_power=estimate_rotation(t[~masked],y[~masked],dy[~masked])
    hyps=[compare_hypothesis(t,y,dy,b,rot_p,m) for m in (1,2)]
    chosen=min(hyps,key=lambda z:z['bic_binary_boxes'])
    event_n=observed_event_count(t,b)
    hard={'depth_snr':b['depth_snr']>=MIN_DEPTH_SNR,'event_n':event_n>=MIN_EVENTS,
          'all_box_depths_positive':all(x>0 for x in chosen['box_depths_faintness']),
          'dbic_rotation_only':chosen['delta_bic_rotation_only_minus_binary']>=MIN_DBIC_ROT_ONLY,
          'dbic_smooth':chosen['delta_bic_smooth_minus_binary']>=MIN_DBIC_SMOOTH}
    detector_pass=bool(all(hard.values()))
    orbit_match=bool(abs(chosen['physical_period_h']-PUBLISHED_ORBIT_H)/PUBLISHED_ORBIT_H<=0.05)
    rot_h=float(rot_p*24);rot_match=bool(any(abs(f*rot_h-PUBLISHED_ROT_H)/PUBLISHED_ROT_H<=0.05 for f in (0.5,1,2)))
    dev_pass=bool(detector_pass and orbit_match and rot_match)
    rep=sanitize({'role':'Stage-3 development on already-open 6764 positive only; no null/discovery values opened','target':'(6764) Kirillavrov',
      'source_url':URL,'raw_sha256':hashlib.sha256(r.content).hexdigest(),
      'architecture':'raw BLS event search -> event mask -> out-of-event rotation -> compare compact P/2P binary-box hypotheses against rotation-only and smooth alternatives',
      'thresholds':{'event_mask_pad':EVENT_MASK_PAD,'min_depth_snr':MIN_DEPTH_SNR,'min_events':MIN_EVENTS,'min_dbic_rotation_only':MIN_DBIC_ROT_ONLY,'min_dbic_smooth':MIN_DBIC_SMOOTH,'rotation_harmonics':ROT_HARMONICS,'event_smooth_harmonics':EVENT_SMOOTH_HARMONICS},
      'bls':b,'event_n':event_n,'rotation_period_h_alias':rot_h,'rotation_ls_power':rot_power,'published_rotation_h':PUBLISHED_ROT_H,'rotation_alias_match_within_5pct':rot_match,
      'hypotheses':hyps,'chosen_hypothesis':chosen,'published_orbit_h':PUBLISHED_ORBIT_H,'chosen_orbit_match_within_5pct':orbit_match,
      'hard_conditions':hard,'stage3_detector_pass':detector_pass,'development_positive_pass':dev_pass,'null_control_values_opened':False,'year8_values_opened':False})
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({k:rep[k] for k in ('bls','rotation_period_h_alias','rotation_alias_match_within_5pct','hypotheses','chosen_hypothesis','chosen_orbit_match_within_5pct','hard_conditions','stage3_detector_pass','development_positive_pass')},indent=2,allow_nan=False))
    raise SystemExit(0 if dev_pass else 6)

if __name__=='__main__':main()
