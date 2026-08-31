#!/usr/bin/env python3
"""Run the frozen Stage-3 detector on the preregistered historical validation panel.

The detector itself is imported unchanged from tess_binary_stage3_frozen.py.
This wrapper contains only the pre-frozen validation truth/gates and deterministic
sharding.  Running it opens validation light-curve values and therefore must
occur only after the science-repo Stage-3 freeze commit.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np, requests
from tess_binary_stage3_frozen import detect

ROOT='https://archive.konkoly.hu/pub/tssys/dr1/lightcurves_spectra'
CONTROL_FILE=Path(__file__).with_name('tess_binary_stage3_null_controls.txt')
OUT=Path('results/tess_binary_stage3_validation')
POSITIVE_NUMBER=1803
POSITIVE_ORBIT_H=28.46
POSITIVE_ROT_H=2.7329
TOL_FRAC=0.05
SHARDS=8


def sanitize(x):
    if isinstance(x,dict):return {k:sanitize(v) for k,v in x.items()}
    if isinstance(x,list):return [sanitize(v) for v in x]
    if isinstance(x,(np.bool_,bool)):return bool(x)
    if isinstance(x,np.integer):return int(x)
    if isinstance(x,(np.floating,float)):
        v=float(x);return v if math.isfinite(v) else None
    return x


def fetch_lc(number):
    url=f'{ROOT}/{int(number)}.lc'
    r=requests.get(url,timeout=120,headers={'User-Agent':'ISEF-frozen-stage3-validation/1.0'})
    r.raise_for_status()
    a=np.loadtxt(r.content.splitlines())
    if a.ndim!=2 or a.shape[1]<10:raise RuntimeError(f'unexpected TSSYS shape for {number}: {a.shape}')
    return url,r.content,a


def run_one(number):
    try:
        url,raw,a=fetch_lc(number)
        d=detect(a[:,1],a[:,4],a[:,5],a[:,9].astype(int))
        return sanitize({'number':int(number),'fetch_ok':True,'source_url':url,'source_sha256':hashlib.sha256(raw).hexdigest(),'detector':d})
    except Exception as e:
        return {'number':int(number),'fetch_ok':False,'error':f'{type(e).__name__}: {e}'[:1000]}


def positive():
    OUT.mkdir(parents=True,exist_ok=True)
    z=run_one(POSITIVE_NUMBER);d=z.get('detector',{});c=d.get('chosen_hypothesis',{})
    physical_h=c.get('physical_period_h');rot_h=d.get('rotation_period_h_alias')
    period_match=bool(physical_h is not None and abs(float(physical_h)-POSITIVE_ORBIT_H)/POSITIVE_ORBIT_H<=TOL_FRAC)
    rotation_alias_match=bool(rot_h is not None and any(abs(f*float(rot_h)-POSITIVE_ROT_H)/POSITIVE_ROT_H<=TOL_FRAC for f in (0.5,1.0,2.0)))
    checks={'fetch_ok':bool(z.get('fetch_ok')),'eligible':bool(d.get('eligible')),'hard_pass':bool(d.get('hard_pass')),
            'physical_period_within_5pct':period_match,'rotation_or_simple_alias_within_5pct':rotation_alias_match}
    rep={'role':'untouched external validation positive','target':'(1803) Zwicky','published_orbit_h':POSITIVE_ORBIT_H,
         'published_primary_rotation_h':POSITIVE_ROT_H,'tolerance_fraction':TOL_FRAC,'checks':checks,'positive_validation_pass':bool(all(checks.values())),
         'result':z,'year8_values_opened':False}
    p=OUT/'positive';p.mkdir(parents=True,exist_ok=True);(p/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'checks':checks,'chosen_hypothesis':c,'rotation_period_h_alias':rot_h,'positive_validation_pass':rep['positive_validation_pass']},indent=2))
    raise SystemExit(0 if rep['positive_validation_pass'] else 10)


def null_shard(index):
    controls=[int(x) for x in CONTROL_FILE.read_text().split()]
    if len(controls)!=128 or len(set(controls))!=128:raise RuntimeError('frozen control manifest is not 128 unique numbers')
    chosen=[n for i,n in enumerate(controls) if i%SHARDS==index]
    results=[]
    for j,n in enumerate(chosen,1):
        z=run_one(n);results.append(z)
        d=z.get('detector',{})
        print(index,j,len(chosen),n,z.get('fetch_ok'),d.get('eligible'),d.get('hard_pass'),flush=True)
    rep={'role':'frozen historical no-known-binary specificity shard','shard_index':index,'shards':SHARDS,'manifest_n':len(controls),
         'object_n':len(chosen),'numbers':chosen,'results':results,'year8_values_opened':False}
    p=OUT/f'null-shard-{index}';p.mkdir(parents=True,exist_ok=True);(p/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True,allow_nan=False)+'\n')


def aggregate():
    results=[]
    for i in range(SHARDS):
        p=OUT/f'null-shard-{i}'/'report.json'
        if not p.exists():raise RuntimeError(f'missing shard report {i}')
        results.extend(json.loads(p.read_text())['results'])
    controls=[int(x) for x in CONTROL_FILE.read_text().split()]
    by={int(z['number']):z for z in results}
    if len(by)!=128 or set(by)!=set(controls):raise RuntimeError(f'aggregate mismatch: {len(by)} unique')
    fetch_ok=[z for z in results if z.get('fetch_ok')]
    eligible=[z for z in fetch_ok if z.get('detector',{}).get('eligible')]
    hard=[z for z in eligible if z.get('detector',{}).get('hard_pass')]
    frac=len(hard)/len(eligible) if eligible else 1.0
    specificity_checks={'eligible_n_at_least_115':len(eligible)>=115,'hard_pass_fraction_at_most_0p02':frac<=0.02}
    rep={'role':'frozen historical specificity aggregate','manifest_n':128,'fetch_ok_n':len(fetch_ok),'eligible_n':len(eligible),'hard_pass_n':len(hard),
         'hard_pass_fraction_of_eligible':frac,'specificity_checks':specificity_checks,'specificity_pass':bool(all(specificity_checks.values())),
         'hard_pass_numbers':[int(z['number']) for z in hard],'results':results,'year8_values_opened':False}
    (OUT/'null-aggregate.json').write_text(json.dumps(rep,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({k:rep[k] for k in ('manifest_n','fetch_ok_n','eligible_n','hard_pass_n','hard_pass_fraction_of_eligible','specificity_checks','specificity_pass','hard_pass_numbers')},indent=2))
    raise SystemExit(0 if rep['specificity_pass'] else 11)


def final_gate():
    pos=json.loads((OUT/'positive'/'report.json').read_text());nul=json.loads((OUT/'null-aggregate.json').read_text())
    overall=bool(pos['positive_validation_pass'] and nul['specificity_pass'])
    rep={'role':'frozen Stage-3 historical validation decision','positive_validation_pass':pos['positive_validation_pass'],'specificity_pass':nul['specificity_pass'],
         'overall_validation_pass':overall,'positive_summary':{'checks':pos['checks'],'chosen_hypothesis':pos['result'].get('detector',{}).get('chosen_hypothesis'),
         'rotation_period_h_alias':pos['result'].get('detector',{}).get('rotation_period_h_alias')},
         'null_summary':{k:nul[k] for k in ('manifest_n','fetch_ok_n','eligible_n','hard_pass_n','hard_pass_fraction_of_eligible','specificity_checks','hard_pass_numbers')},
         'year8_values_opened':False,'post_validation_tuning_permitted':False}
    (OUT/'final.json').write_text(json.dumps(rep,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps(rep,indent=2,sort_keys=True,allow_nan=False))
    raise SystemExit(0 if overall else 12)


def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='mode',required=True)
    sp.add_parser('positive');q=sp.add_parser('null-shard');q.add_argument('index',type=int);sp.add_parser('aggregate');sp.add_parser('final')
    a=ap.parse_args()
    if a.mode=='positive':positive()
    elif a.mode=='null-shard':
        if not 0<=a.index<SHARDS:raise SystemExit('bad shard')
        null_shard(a.index)
    elif a.mode=='aggregate':aggregate()
    else:final_gate()

if __name__=='__main__':main()
