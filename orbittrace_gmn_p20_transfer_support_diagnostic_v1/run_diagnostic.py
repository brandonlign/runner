#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

YEARS=(2022,2023)
MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13))
BLIND=(20.0,55.0)
EXPECTED=(226,1075,3203,4504)
EXPECTED_ACTIVE_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
EXPECTED_P19_RESULT_SHA='6f1ad0626b8a8bda03f18e7f3435f0651af8bebf65cfd1d970a6b61a8ba52319'
EXPECTED_P19_PRELABEL_SHA='276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8'
EXPECTED_P20_RESULT_SHA='9ec53f29281b11002a9e22b1086d12e054392e466ea74fe82ead0187289ba303'
EXPECTED_P20_PRELABEL_SHA='8ca358ae0f3ac96b188de9eac7bcfd6f870470873a2b7ee73b7ae76497c12734'


def req(x:bool,msg:str)->None:
    if not x: raise RuntimeError(msg)

def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()

def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path)
    req(spec is not None and spec.loader is not None,f'cannot import {path}')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def fold(group:str)->int:
    return int(hashlib.sha256(group.encode()).hexdigest()[:8],16)%5

def digest_strings(xs:list[str])->str:
    return hashlib.sha256('\n'.join(sorted(xs)).encode()).hexdigest()

def stats(rows:list[dict[str,Any]])->dict[str,Any]:
    vals=np.asarray([float(r['target']) for r in rows],dtype=float)
    pos=[r for r in rows if bool(r['positive'])]
    hi=[r for r in rows if float(r['target'])>0.5]
    hi_groups=sorted({str(r['best_label']) for r in hi if r['best_label'] is not None})
    fold_counts=Counter(fold('SHOWER/'+g) for g in hi_groups)
    return {
        'families':len(rows),
        'positive_families':len(pos),
        'positive_recurrent_groups':len({str(r['best_label']) for r in pos if r['best_label'] is not None}),
        'target_gt_0_5_families':len(hi),
        'target_gt_0_5_recurrent_groups':len(hi_groups),
        'target_gt_0_5_group_fold_occupancy':{str(i):int(fold_counts.get(i,0)) for i in range(5)},
        'target_mean':float(np.mean(vals)) if len(vals) else 0.0,
        'target_median':float(np.median(vals)) if len(vals) else 0.0,
        'target_q90':float(np.quantile(vals,0.90)) if len(vals) else 0.0,
        'target_q95':float(np.quantile(vals,0.95)) if len(vals) else 0.0,
        'target_q99':float(np.quantile(vals,0.99)) if len(vals) else 0.0,
        'target_max':float(np.max(vals)) if len(vals) else 0.0,
        'high_quality_family_ids_sha256':digest_strings([str(r['family_id']) for r in hi]),
        'high_quality_recurrent_groups_sha256':digest_strings(hi_groups),
    }


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--active-ranker-source',type=Path,required=True)
    p.add_argument('--support-source-parts',type=Path,required=True)
    p.add_argument('--candidate-payload',type=Path,required=True)
    p.add_argument('--baseline-payload',type=Path,required=True)
    p.add_argument('--scorer-parts',type=Path,required=True)
    p.add_argument('--v8-result-json',type=Path,required=True)
    p.add_argument('--p19-result-json',type=Path,required=True)
    p.add_argument('--p19-prelabel-json',type=Path,required=True)
    p.add_argument('--p20-result-json',type=Path,required=True)
    p.add_argument('--p20-prelabel-json',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)

    req(sha(a.active_ranker_source)==EXPECTED_ACTIVE_SHA,'#839 source changed')
    req(sha(a.p19_result_json)==EXPECTED_P19_RESULT_SHA,'P19 result changed')
    req(sha(a.p19_prelabel_json)==EXPECTED_P19_PRELABEL_SHA,'P19 prelabel changed')
    req(sha(a.p20_result_json)==EXPECTED_P20_RESULT_SHA,'P20 result changed')
    req(sha(a.p20_prelabel_json)==EXPECTED_P20_PRELABEL_SHA,'P20 prelabel changed')

    ranker=load_module(a.active_ranker_source,'frozen_839_p20_support_diag')
    p19=json.loads(a.p19_prelabel_json.read_text()); p20=json.loads(a.p20_prelabel_json.read_text())
    hard=p19['hard_families']; s19=p19['soft_families']; s20=p20['soft_families']; fams=hard+s19+s20
    req((len(hard),len(s19),len(s20),len(fams))==EXPECTED,'candidate universe changed')
    ids=[str(f['family_id']) for f in fams]; req(len(set(ids))==len(ids),'family IDs collide')
    source={str(f['family_id']):'hard' for f in hard}; source.update({str(f['family_id']):'p19' for f in s19}); source.update({str(f['family_id']):'p20' for f in s20})

    ranker.v1.mult.YEARS=YEARS; ranker.v1.mult.MONTH_KEYS=MONTH_KEYS; ranker.v1.mult.TOP_K=100
    runtime=ranker.v1.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts)
    support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS='orbittrace-gmn-p20-transfer-support-diagnostic-v1'; support.RANKING_VARIANTS=('persistence',)
    req(float(support.BLIND_LOW)==BLIND[0] and float(support.BLIND_HIGH)==BLIND[1],'target firewall changed')
    setattr(a,'fixed4_baseline_json',a.v8_result_json)
    _candidate,base,_scorer=support.load_sources(a)
    scan,_cal,labels,sources=support.parse_catalogue(base)
    req(sorted(scan)==list(YEARS),'GMN year panel changed'); req([x['key'] for x in sources]==list(MONTH_KEYS),'GMN month panel changed')

    eligible=ranker.v1.eligible_labels(labels); by={str(f['family_id']):f for f in fams}
    truths={fid:ranker.v1.family_truth(by[fid],labels,eligible) for fid in ids}
    rows=[]
    for fid in ids:
        t=truths[fid]; rows.append({
            'family_id':fid,'source':source[fid],'positive':bool(t['positive']),
            'best_label':t['best_label'],'target':float(t['f1']) if t['positive'] else 0.0,
        })

    by_source={s:[r for r in rows if r['source']==s] for s in ('hard','p19','p20')}
    src_stats={s:stats(rs) for s,rs in by_source.items()}
    p20_pos=[r for r in by_source['p20'] if r['target']>0.0]
    p20_hi=[r for r in by_source['p20'] if r['target']>0.5]
    p20_hi_groups=sorted({str(r['best_label']) for r in p20_hi if r['best_label'] is not None})
    result={
        'stage':'GMN_TARGET_EXCLUDED_P20_TRANSFER_SUPPORT_DIAGNOSTIC_V1',
        'candidate_counts':{'hard':len(hard),'p19':len(s19),'p20':len(s20),'union':len(fams)},
        'eligible_recurrent_labels':len(eligible),
        'source_statistics':src_stats,
        'p20_diagnostics':{
            'positive_target_family_count':len(p20_pos),
            'high_quality_target_gt_0_5_family_count':len(p20_hi),
            'high_quality_target_gt_0_5_distinct_recurrent_groups':len(p20_hi_groups),
            'high_quality_group_fold_occupancy':src_stats['p20']['target_gt_0_5_group_fold_occupancy'],
            'high_quality_family_ids_sha256':digest_strings([str(r['family_id']) for r in p20_hi]),
            'high_quality_recurrent_groups_sha256':digest_strings(p20_hi_groups),
        },
        'interpretation_only':True,
        'sonotaco_2013_2014_access':False,
        'maarsy_scientific_access':False,
        'dms_scientific_access':False,
        'target_information_access':False,
        'target_region_events_accessed':False,
        'blind_exclusion':list(BLIND),
    }
    (a.output/'GMN_P20_TRANSFER_SUPPORT_DIAGNOSTIC_V1.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True,allow_nan=False))
    return 0

if __name__=='__main__': raise SystemExit(main())
