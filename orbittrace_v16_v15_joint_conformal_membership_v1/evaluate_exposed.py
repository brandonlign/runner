#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment


def evaluate(families, truth, budget):
    counts=Counter(v for v in truth.values() if v!='SPORADIC')
    labels=sorted(k for k,n in counts.items() if n>=4)
    truth_sets={label:{eid for eid,v in truth.items() if v==label} for label in labels}
    active=[]
    truth_ids=set(truth)
    for family in families:
        members=set(map(str,family['event_ids'])) & truth_ids
        if members: active.append((int(family['rank']),str(family['family_id']),members))
    active=sorted(active,key=lambda x:(x[0],x[1]))[:int(budget)]
    f1=np.zeros((len(labels),len(active)),dtype=np.float64)
    overlap=np.zeros_like(f1,dtype=np.int64)
    precision=np.zeros_like(f1); recall=np.zeros_like(f1)
    for i,label in enumerate(labels):
        actual=truth_sets[label]
        for j,(_rank,_fid,pred) in enumerate(active):
            ov=len(actual & pred); overlap[i,j]=ov
            if ov:
                p=ov/len(pred); r=ov/len(actual); precision[i,j]=p; recall[i,j]=r; f1[i,j]=2.0*p*r/(p+r)
    n=max(len(labels),len(active)); cost=np.zeros((n,n),dtype=np.float64); cost[:len(labels),:len(active)]=-f1
    ri,cj=linear_sum_assignment(cost)
    assigned=[]; per_shower=[]
    for i,j in zip(ri.tolist(),cj.tolist()):
        if i>=len(labels): continue
        if j<len(active):
            rank,fid,pred=active[j]; score=float(f1[i,j]); ov=int(overlap[i,j]); p=float(precision[i,j]); r=float(recall[i,j]); predicted=len(pred)
        else:
            rank=fid=None; score=p=r=0.0; ov=predicted=0
        assigned.append(score)
        per_shower.append({'truth_label':labels[i],'truth_members':len(truth_sets[labels[i]]),'family_id':fid,'family_rank':rank,'overlap':ov,'predicted_members':predicted,'precision':p,'recall':r,'f1':score})
    return {'eligible_showers':len(labels),'macro_f1':float(np.mean(assigned)) if assigned else 0.0,'recovered_f1_gt_0_5':int(sum(x>0.5 for x in assigned)),'candidate_available_with_year_members':sum(bool(set(map(str,f['event_ids']))&truth_ids) for f in families),'candidate_used':len(active),'per_shower':per_shower}


def main():
    p=argparse.ArgumentParser(); p.add_argument('--candidate',type=Path,required=True); p.add_argument('--truth',type=Path,required=True); p.add_argument('--frozen-evaluation',type=Path,required=True); p.add_argument('--comparator',required=True); p.add_argument('--year',type=int,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args(); a.output.parent.mkdir(parents=True,exist_ok=True)
    candidate=json.loads(a.candidate.read_text()); truth=json.loads(a.truth.read_text()); frozen=json.loads(a.frozen_evaluation.read_text()); budget=int(frozen['candidate_budget']['comparator_budget'])
    current=evaluate(candidate['families'],truth,budget); old=frozen['candidate_summary']; comp=frozen['comparator_summary']
    result={'comparator':a.comparator,'year':a.year,'budget':budget,'v15':{'macro_f1':old['macro_f1'],'recovered_f1_gt_0_5':old['recovered_f1_gt_0_5']},'v16':{k:v for k,v in current.items() if k!='per_shower'},'literature_comparator':{'macro_f1':comp['macro_f1'],'recovered_f1_gt_0_5':comp['recovered_f1_gt_0_5']},'delta_v16_minus_v15_macro_f1':current['macro_f1']-old['macro_f1'],'delta_v16_minus_literature_macro_f1':current['macro_f1']-comp['macro_f1'],'membership_mechanism_improved':current['macro_f1']>old['macro_f1'] and current['recovered_f1_gt_0_5']>=old['recovered_f1_gt_0_5'],'literature_macro_f1_beaten':current['macro_f1']>comp['macro_f1'],'literature_recovery_beaten_or_tied':current['recovered_f1_gt_0_5']>=comp['recovered_f1_gt_0_5'],'per_shower':current['per_shower']}
    result['verdict']='PASS_V16_PAIR_LITERATURE_SUPERIORITY_DEV' if result['literature_macro_f1_beaten'] and result['literature_recovery_beaten_or_tied'] else ('PASS_V16_PAIR_MEMBERSHIP_MECHANISM_DEV' if result['membership_mechanism_improved'] else 'FAIL_V16_PAIR_DEVELOPMENT')
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps({k:v for k,v in result.items() if k!='per_shower'},indent=2,sort_keys=True))
if __name__=='__main__': main()
