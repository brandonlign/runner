#!/usr/bin/env python3
"""Run and aggregate the frozen Stage-4 external validation.

Scientific freeze: brandonlign/isef research/TESS_BINARY_STAGE4_FREEZE_2026-08-31.md
This wrapper may not alter the detector, manifests, or validation thresholds.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np, requests
from scipy.stats import fisher_exact
import tess_binary_stage4_frozen as s4

ROOT_URL='https://archive.konkoly.hu/pub/tssys/dr1/lightcurves_spectra'
POS_FILE=Path(__file__).with_name('tess_binary_stage4_validation_positives.txt')
CTRL_FILE=Path(__file__).with_name('tess_binary_stage4_validation_controls.txt')
OUT=Path('results/tess_binary_stage4_validation')
POS_SHARDS=5
CTRL_SHARDS=10
MIN_POS_ELIGIBLE=45
MIN_CTRL_ELIGIBLE=185
MIN_POS_HARD=3
MAX_CTRL_HARD_FRAC=0.020
MAX_FISHER_P=0.010
MIN_ODDS_RATIO=3.0


def sanitize(x):
    if isinstance(x,dict): return {k:sanitize(v) for k,v in x.items()}
    if isinstance(x,list): return [sanitize(v) for v in x]
    if isinstance(x,(np.bool_,bool)): return bool(x)
    if isinstance(x,np.integer): return int(x)
    if isinstance(x,(np.floating,float)):
        v=float(x); return v if math.isfinite(v) else None
    return x


def load_manifest(role):
    p=POS_FILE if role=='positive' else CTRL_FILE
    nums=[int(x) for x in p.read_text().split()]
    want=50 if role=='positive' else 200
    if len(nums)!=want or len(set(nums))!=want: raise RuntimeError(f'{role} manifest cardinality mismatch')
    return nums


def run_one(number):
    url=f'{ROOT_URL}/{number}.lc'
    try:
        r=requests.get(url,timeout=120,headers={'User-Agent':'ISEF-frozen-stage4-validation/1.0'}); r.raise_for_status()
        raw=r.content; a=np.loadtxt(raw.splitlines())
        if a.ndim!=2 or a.shape[1]<10: raise RuntimeError(f'unexpected TSSYS shape {a.shape}')
        d=s4.detect(a[:,1],a[:,4],a[:,5],a[:,9].astype(int))
        return sanitize({'number':int(number),'fetch_ok':True,'source_url':url,'source_sha256':hashlib.sha256(raw).hexdigest(),'detector':d})
    except Exception as e:
        return {'number':int(number),'fetch_ok':False,'error':f'{type(e).__name__}: {e}'[:1000]}


def shard(role,index):
    nums=load_manifest(role); nsh=POS_SHARDS if role=='positive' else CTRL_SHARDS
    if not 0<=index<nsh: raise RuntimeError('invalid shard index')
    chosen=[n for i,n in enumerate(nums) if i%nsh==index]
    rows=[]
    for j,n in enumerate(chosen,1):
        z=run_one(n); rows.append(z); d=z.get('detector',{})
        print(role,index,j,len(chosen),n,z.get('fetch_ok'),d.get('eligible'),d.get('hard_pass'),flush=True)
    p=OUT/f'{role}-shard-{index}'; p.mkdir(parents=True,exist_ok=True)
    rep={'role':role,'shard_index':index,'shard_n':nsh,'manifest_n':len(nums),'object_n':len(chosen),'numbers':chosen,
         'rows':rows,'year8_values_opened':False,'post_validation_tuning_permitted':False}
    (p/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True,allow_nan=False)+'\n')


def find_shard_reports(root,role,nsh):
    root=Path(root); out=[]
    for i in range(nsh):
        matches=list(root.rglob(f'{role}-shard-{i}/report.json'))
        if not matches:
            # Artifact contents may have report.json directly under artifact-name directory.
            matches=[p for p in root.rglob('report.json') if f'stage4-{role}-{i}' in str(p.parent) or f'{role}-{i}' in str(p.parent)]
        if len(matches)!=1: raise RuntimeError(f'expected one report for {role} shard {i}; got {matches}')
        out.append(json.loads(matches[0].read_text()))
    return out


def summarize(rows):
    fetch=[z for z in rows if z.get('fetch_ok')]
    elig=[z for z in fetch if z.get('detector',{}).get('eligible')]
    hard=[z for z in elig if z.get('detector',{}).get('hard_pass')]
    return {'manifest_n':len(rows),'fetch_ok_n':len(fetch),'eligible_n':len(elig),'hard_pass_n':len(hard),
            'hard_pass_fraction_of_eligible':len(hard)/len(elig) if elig else 1.0,
            'hard_pass_numbers':[int(z['number']) for z in hard],
            'ineligible_numbers':[int(z['number']) for z in fetch if not z.get('detector',{}).get('eligible')],
            'fetch_fail_numbers':[int(z['number']) for z in rows if not z.get('fetch_ok')]}


def aggregate(root):
    posreps=find_shard_reports(root,'positive',POS_SHARDS); ctrlreps=find_shard_reports(root,'control',CTRL_SHARDS)
    pos=[z for r in posreps for z in r['rows']]; ctrl=[z for r in ctrlreps for z in r['rows']]
    pmanifest=load_manifest('positive'); cmanifest=load_manifest('control')
    if [z['number'] for z in sorted(pos,key=lambda z:pmanifest.index(z['number']))] != pmanifest: raise RuntimeError('positive aggregate membership mismatch')
    if [z['number'] for z in sorted(ctrl,key=lambda z:cmanifest.index(z['number']))] != cmanifest: raise RuntimeError('control aggregate membership mismatch')
    ps=summarize(pos); cs=summarize(ctrl)
    a=ps['hard_pass_n']; b=ps['eligible_n']-a; c=cs['hard_pass_n']; d=cs['eligible_n']-c
    odds,pv=fisher_exact([[a,b],[c,d]],alternative='greater') if ps['eligible_n'] and cs['eligible_n'] else (0.0,1.0)
    odds=float(odds); pv=float(pv)
    checks={'positive_eligible_at_least_45':ps['eligible_n']>=MIN_POS_ELIGIBLE,
            'control_eligible_at_least_185':cs['eligible_n']>=MIN_CTRL_ELIGIBLE,
            'positive_hard_pass_at_least_3':a>=MIN_POS_HARD,
            'control_hard_pass_fraction_at_most_0p02':cs['hard_pass_fraction_of_eligible']<=MAX_CTRL_HARD_FRAC,
            'fisher_one_sided_p_at_most_0p01':pv<=MAX_FISHER_P,
            'odds_ratio_at_least_3':bool(math.isinf(odds) or odds>=MIN_ODDS_RATIO)}
    passed=bool(all(checks.values()))
    rep=sanitize({'role':'frozen Stage-4 external-validation decision','scientific_freeze':'brandonlign/isef:research/TESS_BINARY_STAGE4_FREEZE_2026-08-31.md',
      'positive_summary':ps,'control_summary':cs,'contingency_table':[[a,b],[c,d]],'fisher_alternative':'greater',
      'fisher_odds_ratio':odds,'fisher_p':pv,'checks':checks,'overall_validation_pass':passed,
      'year8_values_opened':False,'post_validation_tuning_permitted':False,'positive_rows':pos,'control_rows':ctrl})
    OUT.mkdir(parents=True,exist_ok=True); (OUT/'final.json').write_text(json.dumps(rep,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({k:rep[k] for k in ('positive_summary','control_summary','contingency_table','fisher_odds_ratio','fisher_p','checks','overall_validation_pass')},indent=2,allow_nan=False))
    raise SystemExit(0 if passed else 30)


def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='mode',required=True)
    q=sp.add_parser('shard'); q.add_argument('role',choices=['positive','control']); q.add_argument('index',type=int)
    a=sp.add_parser('aggregate'); a.add_argument('root')
    args=ap.parse_args()
    if args.mode=='shard': shard(args.role,args.index)
    else: aggregate(args.root)

if __name__=='__main__': main()
