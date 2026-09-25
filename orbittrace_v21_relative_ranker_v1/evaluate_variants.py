#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path
from typing import Any
import numpy as np
from scipy.optimize import linear_sum_assignment

PANELS=(('sugar',2013),('sugar',2014),('hdbscan',2013),('hdbscan',2014))
SUCCESSORS=('relative_quality','relative_v19_rank_sum')
PREF={'relative_quality':2,'relative_v19_rank_sum':1}
V19={('sugar',2013):(0.2813397742020527,17),('sugar',2014):(0.3328665843994243,18),('hdbscan',2013):(0.1386807102765093,9),('hdbscan',2014):(0.11367457228624304,5)}

def req(x,m):
    if not x: raise RuntimeError(m)
def ev(families:list[dict[str,Any]],truth:dict[str,str],budget:int)->dict[str,Any]:
    counts=Counter(v for v in truth.values() if v!='SPORADIC'); labels=sorted(k for k,n in counts.items() if n>=4)
    ts={l:{eid for eid,v in truth.items() if v==l} for l in labels}; ids=set(truth); active=[]
    for f in families:
        s=set(map(str,f['event_ids']))&ids
        if s: active.append((int(f['rank']),str(f['family_id']),s))
    active=sorted(active,key=lambda x:(x[0],x[1]))[:budget]; mat=np.zeros((len(labels),len(active)))
    for i,l in enumerate(labels):
        a=ts[l]
        for j,(_r,_f,p) in enumerate(active):
            o=len(a&p)
            if o:
                pr=o/len(p); rc=o/len(a); mat[i,j]=2*pr*rc/(pr+rc)
    n=max(len(labels),len(active)); c=np.zeros((n,n)); c[:len(labels),:len(active)]=-mat
    ri,cj=linear_sum_assignment(c); vals=[float(mat[i,j]) if j<len(active) else 0.0 for i,j in zip(ri.tolist(),cj.tolist()) if i<len(labels)]
    return {'macro_f1':float(np.mean(vals)) if vals else 0.0,'recovered_f1_gt_0_5':sum(x>0.5 for x in vals),'candidate_used':len(active)}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--candidate-root',type=Path,required=True); p.add_argument('--truth-root',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.parent.mkdir(parents=True,exist_ok=True)
    for comp in ('sugar','hdbscan'):
        m=json.loads((a.candidate_root/comp/'V21_PRETRUTH_VARIANT_MANIFEST.json').read_text())
        req(m['verdict']=='PASS_V21_ALL_VARIANTS_PRETRUTH_FREEZE' and m['sonotaco_training_labels_used'] is False,'invalid v21 pretruth manifest')
        req(m['truth_accessed'] is False and m['target_information_access'] is False and m['maarsy_scientific_access'] is False and m['dms_scientific_access'] is False,'firewall violation')
    truth={}; frozen={}
    for c,y in PANELS:
        truth[(c,y)]=json.loads((a.truth_root/f'truth_{c}_{y}.json').read_text()); frozen[(c,y)]=json.loads((a.truth_root/f'evaluation_{c}_{y}.json').read_text())
    control=[]
    for c,y in PANELS:
        cand=json.loads((a.candidate_root/c/'v19_control'/'candidate_primary_output.json').read_text()); b=int(frozen[(c,y)]['candidate_budget']['comparator_budget']); cur=ev(cand['families'],truth[(c,y)],b)
        req(abs(cur['macro_f1']-V19[(c,y)][0])<1e-12 and cur['recovered_f1_gt_0_5']==V19[(c,y)][1],f'v19 control mismatch {c} {y}')
        control.append({'comparator':c,'year':y,**cur})
    rows=[]
    for variant in SUCCESSORS:
        panels=[]
        for c,y in PANELS:
            cand=json.loads((a.candidate_root/c/variant/'candidate_primary_output.json').read_text()); b=int(frozen[(c,y)]['candidate_budget']['comparator_budget']); cur=ev(cand['families'],truth[(c,y)],b); lit=frozen[(c,y)]['comparator_summary']
            cm=float(cur['macro_f1']); cr=int(cur['recovered_f1_gt_0_5']); lm=float(lit['macro_f1']); lr=int(lit['recovered_f1_gt_0_5']); mr=cm/lm; rr=cr/lr; win=cm>lm and cr>=lr
            panels.append({'comparator':c,'year':y,'budget':b,'candidate_macro_f1':cm,'literature_macro_f1':lm,'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,'macro_f1_ratio':mr,'recovery_ratio':rr,'superiority_pair_pass':win})
        wins=sum(x['superiority_pair_pass'] for x in panels); minm=min(x['macro_f1_ratio'] for x in panels); minr=min(x['recovery_ratio'] for x in panels); meanm=float(np.mean([x['macro_f1_ratio'] for x in panels])); meanr=float(np.mean([x['recovery_ratio'] for x in panels]))
        rows.append({'variant':variant,'panel_wins':wins,'all_panel_win':wins==4,'min_macro_f1_ratio':minm,'min_recovery_ratio':minr,'mean_macro_f1_ratio':meanm,'mean_recovery_ratio':meanr,'selection_key':[wins,minm,minr,meanm,meanr,PREF[variant]],'panels':panels})
    winner=max(rows,key=lambda r:tuple(r['selection_key']))
    result={'scientific_stage':'V21_EXPOSED_SONOTACO_CATALOGUE_RELATIVE_RANKING_DEVELOPMENT','v19_control_reproduction_pass':True,'v19_control':control,'all_results':rows,'winner':winner,'verdict':'PASS_V21_EXPOSED_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if winner['all_panel_win'] else 'FAIL_V21_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT','sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','sonotaco_training_labels_used':False,'post_result_second_search':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False}
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':result['verdict'],'winner':winner},indent=2,sort_keys=True,allow_nan=False)); return 0
if __name__=='__main__': raise SystemExit(main())
