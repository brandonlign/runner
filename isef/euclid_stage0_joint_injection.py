#!/usr/bin/env python3
"""Injection recovery through the full morphology+FLAG+common-mode gate.

Thresholds and epoch common modes are imported unchanged from the real-data joint
null. Synthetic unresolved brightenings/dimmings are measured with the same-dither
PSF estimator. FLAG status is an image property, so all unique selected star/epoch
locations are fetched concurrently before recovery is scored.
"""
import json
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import numpy as np
import euclid_stage0_psf_detector as pd
import euclid_stage0_psf_flag_gate as fg

NULL=Path('results/euclid_stage0_psf_flag_gate.json');OUT=Path('results/euclid_stage0_joint_injection.json')
RNG=np.random.default_rng(20260829);AMPS=(0.10,0.15,0.20,0.30,0.50);REPS=12

def summary(a):return pd.summary(np.asarray(a,float))

def main():
    null=json.loads(NULL.read_text());thresholds=null['thresholds'];common=np.asarray(null['epoch_common_mode_fraction'],float);base,cube,hs,orig=pd.setup();lim=pd.morphology_limits();ra,de,peak=pd.sources(cube,hs,orig);rows=[];eligible=0;locations={}
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
                    e=int(RNG.integers(0,16));ref=refs[e];yy,xx=np.indices(ref.shape);cc=(np.array(ref.shape)-1)/2;rr=np.hypot(xx-cc[1],yy-cc[0]);floor=float(np.nanmedian(ref[(rr>=5.5)&(rr<=7.5)]));tmpl=ref-floor;event=cuts[e]+sign*amp*tmpl;f,s,c=pd.scale_metric(event,ref);morph=pd.morph_ok(s,c,lim);key=(j,e)
                    if morph:locations[key]=(hs[e],e,float(r),float(d))
                    corrected=fg.common_correct(f,common[e]);rows.append({'star':j,'epoch':e,'amplitude':amp,'sign':label,'recovered_fraction_raw':float(f),'recovered_fraction':corrected,'abs_error':float(abs(corrected-sign*amp)),'morphology_ok':morph,'location_key':key})
    flagcache={}
    with ThreadPoolExecutor(max_workers=32) as ex:
        fs={ex.submit(fg.flag_artifact,*args):key for key,args in locations.items()}
        for fut in as_completed(fs):
            key=fs[fut]
            try:flagcache[key]=bool(fut.result()[0])
            except Exception:flagcache[key]=True
    for r in rows:
        artifact=flagcache.get(tuple(r['location_key'])) if r['morphology_ok'] else None;r['artifact_flag']=artifact;r['accepted']=bool(r['morphology_ok'] and artifact is False);a=abs(r['recovered_fraction']);r['detect_q95']=bool(r['accepted'] and a>thresholds['q95']);r['detect_q99']=bool(r['accepted'] and a>thresholds['q99']);r['detect_zero_fp']=bool(r['accepted'] and a>thresholds['zero_observed_fp']);del r['location_key']
    outamp={}
    for amp in AMPS:
        outamp[str(amp)]={}
        for label in ('brightening','dimming'):
            z=[x for x in rows if x['amplitude']==amp and x['sign']==label];a=[x for x in z if x['accepted']]
            outamp[str(amp)][label]={'trials':len(z),'gate_accepted':len(a),'gate_acceptance':float(len(a)/len(z)) if z else 0,'recovered_fraction':summary([x['recovered_fraction'] for x in a]),'abs_error':summary([x['abs_error'] for x in a]),'recovery_q95':float(np.mean([x['detect_q95'] for x in z])) if z else 0,'recovery_q99':float(np.mean([x['detect_q99'] for x in z])) if z else 0,'recovery_zero_observed_fp':float(np.mean([x['detect_zero_fp'] for x in z])) if z else 0}
    out={'success':True,'note':'development full-gate injections; thresholds/common modes imported unchanged from real morphology+FLAG null','thresholds':thresholds,'epoch_common_mode_fraction':common.tolist(),'eligible_sources':eligible,'unique_flag_reads':len(flagcache),'amplitudes':outamp}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
