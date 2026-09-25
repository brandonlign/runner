#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

PANELS=(('sugar',2013),('sugar',2014),('hdbscan',2013),('hdbscan',2014))
SUCCESSORS=('consensus_only','rank_sum','rank_product')
PREFERENCE={'rank_sum':3,'rank_product':2,'consensus_only':1}
V17_METRICS={
    ('sugar',2013):(0.2772197612820636,15),('sugar',2014):(0.3169578830313374,17),
    ('hdbscan',2013):(0.12010507969574384,6),('hdbscan',2014):(0.11542944613677675,6),
}


def require(ok: bool,msg: str)->None:
    if not ok: raise RuntimeError(msg)


def evaluate(families: list[dict[str,Any]],truth: dict[str,str],budget: int)->dict[str,Any]:
    counts=Counter(v for v in truth.values() if v!='SPORADIC')
    labels=sorted(k for k,n in counts.items() if n>=4)
    truth_sets={label:{eid for eid,v in truth.items() if v==label} for label in labels}
    truth_ids=set(truth); active=[]
    for family in families:
        members=set(map(str,family['event_ids'])) & truth_ids
        if members: active.append((int(family['rank']),str(family['family_id']),members))
    active=sorted(active,key=lambda x:(x[0],x[1]))[:int(budget)]
    f1=np.zeros((len(labels),len(active)),dtype=np.float64)
    for i,label in enumerate(labels):
        actual=truth_sets[label]
        for j,(_rank,_fid,pred) in enumerate(active):
            ov=len(actual & pred)
            if ov:
                p=ov/len(pred); r=ov/len(actual); f1[i,j]=2.0*p*r/(p+r)
    n=max(len(labels),len(active)); cost=np.zeros((n,n),dtype=np.float64); cost[:len(labels),:len(active)]=-f1
    ri,cj=linear_sum_assignment(cost); assigned=[]
    for i,j in zip(ri.tolist(),cj.tolist()):
        if i>=len(labels): continue
        assigned.append(float(f1[i,j]) if j<len(active) else 0.0)
    return {
        'eligible_showers':len(labels),
        'macro_f1':float(np.mean(assigned)) if assigned else 0.0,
        'recovered_f1_gt_0_5':int(sum(x>0.5 for x in assigned)),
        'candidate_used':len(active),
    }


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--candidate-root',type=Path,required=True); p.add_argument('--truth-root',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.parent.mkdir(parents=True,exist_ok=True)
    manifests={}
    for comparator in ('sugar','hdbscan'):
        m=json.loads((a.candidate_root/comparator/'V19_PRETRUTH_VARIANT_MANIFEST.json').read_text())
        require(m['verdict']=='PASS_V19_ALL_VARIANTS_PRETRUTH_FREEZE',f'{comparator} variants not frozen')
        require(m['truth_accessed'] is False and m['target_information_access'] is False and m['maarsy_scientific_access'] is False and m['dms_scientific_access'] is False,'pretruth firewall violation')
        manifests[comparator]=m

    truth={}; frozen={}
    for comparator,year in PANELS:
        truth[(comparator,year)]=json.loads((a.truth_root/f'truth_{comparator}_{year}.json').read_text())
        frozen[(comparator,year)]=json.loads((a.truth_root/f'evaluation_{comparator}_{year}.json').read_text())

    # Mandatory exact v17 control reproduction before accepting any successor result.
    control=[]
    for comparator,year in PANELS:
        c=json.loads((a.candidate_root/comparator/'v17_control'/'candidate_primary_output.json').read_text())
        budget=int(frozen[(comparator,year)]['candidate_budget']['comparator_budget'])
        cur=evaluate(c['families'],truth[(comparator,year)],budget); expected=V17_METRICS[(comparator,year)]
        require(abs(cur['macro_f1']-expected[0])<1e-12 and cur['recovered_f1_gt_0_5']==expected[1],f'v17 control metric mismatch {comparator} {year}: {cur} != {expected}')
        control.append({'comparator':comparator,'year':year,**cur})

    rows=[]
    for variant in SUCCESSORS:
        panels=[]
        for comparator,year in PANELS:
            c=json.loads((a.candidate_root/comparator/variant/'candidate_primary_output.json').read_text())
            budget=int(frozen[(comparator,year)]['candidate_budget']['comparator_budget'])
            cur=evaluate(c['families'],truth[(comparator,year)],budget); comp=frozen[(comparator,year)]['comparator_summary']
            cm=float(cur['macro_f1']); cr=int(cur['recovered_f1_gt_0_5']); lm=float(comp['macro_f1']); lr=int(comp['recovered_f1_gt_0_5'])
            mr=cm/lm if lm>0 else float('inf'); rr=cr/lr if lr>0 else float('inf'); win=bool(cm>lm and cr>=lr)
            panels.append({'comparator':comparator,'year':year,'budget':budget,'candidate_macro_f1':cm,'literature_macro_f1':lm,'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,'macro_f1_ratio':mr,'recovery_ratio':rr,'superiority_pair_pass':win})
        wins=sum(int(x['superiority_pair_pass']) for x in panels); minm=min(x['macro_f1_ratio'] for x in panels); minr=min(x['recovery_ratio'] for x in panels); meanm=float(np.mean([x['macro_f1_ratio'] for x in panels])); meanr=float(np.mean([x['recovery_ratio'] for x in panels]))
        key=[wins,minm,minr,meanm,meanr,PREFERENCE[variant]]
        rows.append({'variant':variant,'panel_wins':wins,'all_panel_win':wins==4,'min_macro_f1_ratio':minm,'min_recovery_ratio':minr,'mean_macro_f1_ratio':meanm,'mean_recovery_ratio':meanr,'selection_key':key,'panels':panels})
    winner=max(rows,key=lambda r:tuple(r['selection_key']))
    result={
        'scientific_stage':'V19_EXPOSED_SONOTACO_QUALITY_CONSENSUS_FUSION_DEVELOPMENT',
        'v17_control_reproduction_pass':True,'v17_control':control,'all_results':rows,'winner':winner,
        'verdict':'PASS_V19_EXPOSED_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if winner['all_panel_win'] else 'FAIL_V19_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','post_result_second_search':False,
        'maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,
    }
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'winner':winner,'v17_control_reproduction_pass':True},indent=2,sort_keys=True,allow_nan=False))
    return 0

if __name__=='__main__': raise SystemExit(main())
