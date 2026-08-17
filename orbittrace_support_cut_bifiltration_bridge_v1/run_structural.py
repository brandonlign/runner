#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any

SUPPORT_SHA='4529eadd9ff93aae057f0a6fd5e0dd923f2300b7c6e01b74a0b7638e22da6de6'
BIF_SHA='95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c'
DS=(128,1024); BS=(0,1,2,3); MIN_SUPPORT=4

def req(x:bool,m:str)->None:
    if not x: raise RuntimeError(m)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def mkey(r:dict[str,Any])->tuple[str,...]:return tuple(sorted(str(x) for x in r['event_ids']))
def restrict(rows:list[dict[str,Any]],u:set[str])->list[frozenset[str]]:
    out=[];seen=set()
    for r in rows:
        s=frozenset(str(x) for x in r['event_ids'] if str(x) in u)
        if len(s)>=MIN_SUPPORT and s not in seen:seen.add(s);out.append(s)
    return out
def mbj(fine:list[dict[str,Any]],coarse:list[dict[str,Any]],u:set[str])->float:
    fs=[frozenset(str(x) for x in r['event_ids']) for r in fine]; cs=restrict(coarse,u)
    if not fs:return 0.0
    vals=[]
    for a in fs:
        best=0.0
        for b in cs:
            i=len(a&b)
            if i:best=max(best,i/len(a|b))
        vals.append(best)
    return sum(vals)/len(vals)

def main()->int:
    a=argparse.ArgumentParser();a.add_argument('--support',type=Path,required=True);a.add_argument('--bif',type=Path,required=True);a.add_argument('--output',type=Path,required=True);q=a.parse_args();q.output.mkdir(parents=True,exist_ok=True)
    req(sha(q.support)==SUPPORT_SHA,'support prelabel changed');req(sha(q.bif)==BIF_SHA,'bif prelabel changed')
    s=json.loads(q.support.read_text());b=json.loads(q.bif.read_text())
    req(s['scientific_role']=='PRELABEL_TOPOMODAL_SUPPORT_RESOLVED_CUT_V1' and s['shower_truth_used'] is False,'support role/truth')
    req(b['scientific_role']=='PRELABEL_TARGET_EXCLUDED_GMN_RANKING_RECOVERY' and b['shower_truth_used'] is False,'bif role/truth')
    for p in (s,b):
        req(p['target_information_access'] is False and p['target_region_events_accessed'] is False,'target firewall')
        req(p['sonotaco_2013_2014_access'] is False,'SonotaCo flag')
    sm={(int(x['denominator']),int(x['bucket'])):x for x in s['subsets']};bm={(int(x['denominator']),int(x['bucket'])):x for x in b['subsets']}
    req(set(sm)==set(bm)=={(d,z) for d in DS for z in BS},'panel set')
    panels=[]; bridge={}; recurrent={}; universes={}
    for k in sorted(sm):
        ss,bb=sm[k],bm[k];K=int(ss['equal_budget_k']);req(K==int(bb['equal_budget_k']),'K mismatch')
        area={mkey(r):r for r in bb['bifiltration_candidates']}; rows=[]
        for r in ss['successor_candidates']:
            m=mkey(r)
            if m not in area:continue
            z=dict(r);z['bifiltration_persistence_area']=float(area[m]['persistence_area']);rows.append(z)
        rows.sort(key=lambda r:(-float(r['bifiltration_persistence_area']),-int(r['member_count']),str(r['family_hash'])))
        bridge[k]=rows;recurrent[k]=list(ss['recurrent_candidates'])
        # support prelabel does not store IDs by year, but bif prelabel does.
        u=set()
        for v in bb['annual_event_ids'].values():u.update(str(x) for x in v)
        universes[k]=u
        disjoint=True
        sets=[frozenset(mkey(r)) for r in rows]
        for i,x in enumerate(sets):
            for y in sets[i+1:]:
                if x&y:disjoint=False
        panels.append({'denominator':k[0],'bucket':k[1],'K':K,'support_candidate_count':len(ss['successor_candidates']),'exact_match_count':len(rows),'exact_match_fraction':len(rows)/len(ss['successor_candidates']),'capacity':len(rows)>=K,'pairwise_disjoint':disjoint})
    cross=[]
    for z in BS:
        fk=(1024,z);ck=(128,z);Kf=int(sm[fk]['equal_budget_k']);Kc=int(sm[ck]['equal_budget_k']);u=universes[fk]
        br=mbj(bridge[fk][:Kf],bridge[ck][:Kc],u) if bridge[fk] else 0.0
        rr=mbj(recurrent[fk],recurrent[ck],u)
        cross.append({'bucket':z,'bridge_mean_best_jaccard':br,'recurrent_mean_best_jaccard':rr,'nonlower':br>=rr})
    bmj=sum(x['bridge_mean_best_jaccard'] for x in cross)/4;rmj=sum(x['recurrent_mean_best_jaccard'] for x in cross)/4;n=sum(bool(x['nonlower']) for x in cross)
    gates={'exact_match_capacity_all_8':all(x['capacity'] for x in panels),'pairwise_disjoint_all_8':all(x['pairwise_disjoint'] for x in panels),'topk_unique_event_coverage_nonzero_all_8':all(len(bridge[(x['denominator'],x['bucket'])][:x['K']])>0 for x in panels),'cross_scale_mean_not_lower_than_recurrent':bmj>=rmj,'cross_scale_nonlower_at_least_3_of_4':n>=3}
    verdict='PASS_SUPPORT_CUT_BIFILTRATION_BRIDGE_V1_STRUCTURAL' if all(gates.values()) else 'FAIL_SUPPORT_CUT_BIFILTRATION_BRIDGE_V1_STRUCTURAL'
    out={'schema':'ORBITTRACE_SUPPORT_CUT_BIFILTRATION_BRIDGE_V1_STRUCTURAL','scientific_role':'ZERO_LABEL_STRUCTURAL_DIAGNOSTIC_ONLY','verdict':verdict,'support_prelabel_sha256':SUPPORT_SHA,'bif_prelabel_sha256':BIF_SHA,'panels':panels,'cross_scale':cross,'aggregate':{'bridge_cross_scale_mean':bmj,'recurrent_cross_scale_mean':rmj,'nonlower_buckets':n},'gates':gates,'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'method_parameter_selection_from_result':False}
    (q.output/'SUPPORT_CUT_BIFILTRATION_BRIDGE_V1_STRUCTURAL.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
