#!/usr/bin/env python3
"""Injection recovery through the full development morphology+FLAG discovery gate.

Synthetic unresolved brightenings and dimmings are inserted into real Euclid
cutouts, measured with the same-dither PSF scale estimator, then subjected to the
same candidate-independent morphology and released-FLG requirements used for the
source-level null. The detection threshold is read from the already-computed
joint null; it is not retuned from injections.
"""
import json
from pathlib import Path
import numpy as np
import euclid_stage0_psf_detector as pd
import euclid_stage0_psf_flag_gate as fg

NULL=Path('results/euclid_stage0_psf_flag_gate.json');OUT=Path('results/euclid_stage0_joint_injection.json')
RNG=np.random.default_rng(20260829);AMPS=(0.10,0.15,0.20,0.30,0.50);REPS=12

def summary(a):return pd.summary(np.asarray(a,float))

def main():
    null=json.loads(NULL.read_text());thresholds=null['thresholds'];base,cube,hs,orig=pd.setup();lim=pd.morphology_limits();ra,de,peak=pd.sources(cube,hs,orig);flagcache={};rows=[];eligible=0
    for j,(r,d) in enumerate(zip(ra,de)):
        cuts={e:pd.cut(cube,hs,orig,r,d,e) for e in range(16)}
        if any(v is None for v in cuts.values()):continue
        refs={};baseline_ok=[]
        for e in range(16):
            peers=[p for p in range(e%4,16,4) if p!=e];ref=np.nanmedian(np.stack([cuts[p] for p in peers]),axis=0);refs[e]=ref;f,s,c=pd.scale_metric(cuts[e],ref);baseline_ok.append(pd.morph_ok(s,c,lim))
        if sum(baseline_ok)<pd.MIN_ACCEPTED:continue
        eligible+=1
        for amp in AMPS:
            for sign,label in ((1,'brightening'),(-1,'dimming')):
                for rep in range(REPS):
                    e=int(RNG.integers(0,16));ref=refs[e];yy,xx=np.indices(ref.shape);cc=(np.array(ref.shape)-1)/2;rr=np.hypot(xx-cc[1],yy-cc[0]);floor=float(np.nanmedian(ref[(rr>=5.5)&(rr<=7.5)]));tmpl=ref-floor;event=cuts[e]+sign*amp*tmpl;f,s,c=pd.scale_metric(event,ref);morph=pd.morph_ok(s,c,lim)
                    key=(j,e);artifact=None;flag_error=None
                    if morph:
                        if key not in flagcache:
                            try:flagcache[key]=fg.flag_artifact(hs[e],e,float(r),float(d))[0]
                            except Exception as ex:flagcache[key]=True;flag_error=f'{type(ex).__name__}: {ex}'
                        artifact=flagcache[key]
                    accepted=bool(morph and artifact is False);absf=abs(float(f));rows.append({'star':j,'epoch':e,'amplitude':amp,'sign':label,'recovered_fraction':float(f),'abs_error':float(abs(f-sign*amp)),'morphology_ok':morph,'artifact_flag':artifact,'accepted':accepted,'detect_q95':bool(accepted and absf>thresholds['q95']),'detect_q99':bool(accepted and absf>thresholds['q99']),'detect_zero_fp':bool(accepted and absf>thresholds['zero_observed_fp']),'flag_error':flag_error})
    outamp={}
    for amp in AMPS:
        outamp[str(amp)]={}
        for label in ('brightening','dimming'):
            z=[x for x in rows if x['amplitude']==amp and x['sign']==label];a=[x for x in z if x['accepted']]
            outamp[str(amp)][label]={'trials':len(z),'gate_accepted':len(a),'gate_acceptance':float(len(a)/len(z)) if z else 0,'recovered_fraction':summary([x['recovered_fraction'] for x in a]),'abs_error':summary([x['abs_error'] for x in a]),'recovery_q95':float(np.mean([x['detect_q95'] for x in z])) if z else 0,'recovery_q99':float(np.mean([x['detect_q99'] for x in z])) if z else 0,'recovery_zero_observed_fp':float(np.mean([x['detect_zero_fp'] for x in z])) if z else 0}
    out={'success':True,'note':'development full-gate injections; thresholds imported unchanged from joint morphology+FLAG null','thresholds':thresholds,'eligible_sources':eligible,'unique_flag_reads':len(flagcache),'amplitudes':outamp}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
