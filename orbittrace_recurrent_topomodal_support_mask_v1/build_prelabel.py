#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any

SOURCE_SHA='278d659542668e52033a5369f9afdf685e010a2c14c7ff5211b0b60dd73f2d4a'
DS=(128,1024); BS=(0,1,2,3); MIN_SUPPORT=4
EXPECTED_K={(128,0):29,(128,1):35,(128,2):38,(128,3):33,(1024,0):8,(1024,1):5,(1024,2):6,(1024,3):9}

def req(x:bool,m:str)->None:
    if not x: raise RuntimeError(m)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def mem(r:dict[str,Any])->frozenset[str]:return frozenset(str(x) for x in r['event_ids'])
def disjoint(rows:list[dict[str,Any]])->bool:
    ss=[mem(r) for r in rows]
    return all(not a&b for i,a in enumerate(ss) for b in ss[i+1:])
def restrict(rows:list[dict[str,Any]],u:set[str])->list[frozenset[str]]:
    out=[];seen=set()
    for r in rows:
        s=frozenset(x for x in mem(r) if x in u)
        if len(s)>=MIN_SUPPORT and s not in seen:seen.add(s);out.append(s)
    return out
def mbj(fine:list[dict[str,Any]],coarse:list[dict[str,Any]],u:set[str])->float:
    fs=[mem(r) for r in fine]; cs=restrict(coarse,u)
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
    ap=argparse.ArgumentParser();ap.add_argument('--orphan-prelabel',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.orphan_prelabel)==SOURCE_SHA,'source prelabel changed')
    src=json.loads(a.orphan_prelabel.read_text())
    req(src['schema']=='ORBITTRACE_SUPPORT_CUT_RECURRENT_ORPHAN_COMPLETION_V1_PRELABEL','wrong source schema')
    req(src['scientific_role']=='PRELABEL_SUPPORT_CUT_RECURRENT_ORPHAN_COMPLETION_V1','wrong source role')
    req(src['shower_truth_used'] is False,'source used truth')
    req(src['target_information_access'] is False and src['target_region_events_accessed'] is False,'source firewall')
    req(src['sonotaco_2013_2014_access'] is False,'source SonotaCo access')
    sm={(int(x['denominator']),int(x['bucket'])):x for x in src['subsets']};req(set(sm)==set(EXPECTED_K),'panel set changed')
    outputs={};parents={};universes={};panels=[];frozen=[]
    for key in sorted(EXPECTED_K):
        row=sm[key]; K=EXPECTED_K[key]; req(int(row['equal_budget_k'])==K,'K changed')
        parent=list(row['recurrent_candidates']); req(len(parent)==K,'parent candidate count changed')
        req([int(r['rank']) for r in parent]==list(range(1,K+1)),'parent order changed')
        support=[r for r in row['successor_candidates'] if r['catalogue_source'] in {'support_projection','support_append'}]
        req(support,'support catalogue empty'); req(disjoint(support),'support catalogue not disjoint'); req(len({str(r['family_hash']) for r in support})==len(support),'support family duplicate')
        support_union=set(); [support_union.update(mem(r)) for r in support]
        universe=set(); [universe.update(str(x) for x in vals) for vals in row['annual_event_ids'].values()]
        req(len(universe)==int(row['event_count']),'event universe changed')
        out=[];audit=[]
        for r,p in enumerate(parent,1):
            P=mem(p); req(P.issubset(universe),'parent outside universe')
            M=frozenset(P & support_union)
            use_mask=len(M)>=MIN_SUPPORT
            chosen=M if use_mask else P
            q=dict(p);q['event_ids']=sorted(chosen);q['rank']=r;q['support_mask_rank']=r
            q['catalogue_source']='support_mask' if use_mask else 'recurrent_fallback'
            q['parent_member_count']=len(P);q['raw_mask_member_count']=len(M);q['retention_fraction']=len(M)/len(P)
            q['support_component_count']=sum(bool(P & mem(s)) for s in support)
            out.append(q)
            audit.append({'rank':r,'parent_family_id':str(p['family_id']),'parent_member_count':len(P),'raw_mask_member_count':len(M),'output_member_count':len(chosen),'support_component_count':q['support_component_count'],'used_mask':use_mask,'retention_fraction':q['retention_fraction']})
        req(len(out)==K,'successor count changed');req([int(r['rank']) for r in out]==list(range(1,K+1)),'successor ranks changed')
        req(all(len(mem(r))>=MIN_SUPPORT for r in out),'sub-support candidate')
        req(all(mem(out[i]).issubset(mem(parent[i])) for i in range(K)),'output not parent subset')
        req(disjoint(out),'successor candidates overlap')
        for i,(p,q) in enumerate(zip(parent,out)):
            P=mem(p); M=frozenset(P & support_union)
            if len(M)>=MIN_SUPPORT:
                req(q['catalogue_source']=='support_mask' and mem(q)==M,'mask rule changed')
            else:
                req(q['catalogue_source']=='recurrent_fallback' and mem(q)==P,'fallback rule changed')
        masked=sum(r['catalogue_source']=='support_mask' for r in out); fallback=K-masked
        req(masked>=1,'mechanism inactive')
        outputs[key]=out; parents[key]=parent;universes[key]=universe
        panels.append({'denominator':key[0],'bucket':key[1],'K':K,'support_candidate_count':len(support),'masked_candidate_count':masked,'fallback_candidate_count':fallback,'mean_retention_fraction':sum(x['retention_fraction'] for x in audit)/K,'minimum_retention_fraction':min(x['retention_fraction'] for x in audit),'candidate_count_exact_k':len(out)==K,'rank_identity_preserved':all(int(q['rank'])==int(p['rank']) for p,q in zip(parent,out)),'support_at_least_4':all(len(mem(q))>=MIN_SUPPORT for q in out),'parent_subset_all':all(mem(q).issubset(mem(p)) for p,q in zip(parent,out)),'pairwise_disjoint':disjoint(out),'mechanism_active':masked>=1})
        frozen.append({'denominator':key[0],'bucket':key[1],'event_count':len(universe),'annual_event_ids':row['annual_event_ids'],'equal_budget_k':K,'successor_candidates':out,'recurrent_candidates':parent,'membership_audit':audit})
    cross=[]
    for b in BS:
        fu=universes[(1024,b)]; req(fu.issubset(universes[(128,b)]),'fine panel not nested')
        sj=mbj(outputs[(1024,b)],outputs[(128,b)],fu);rj=mbj(parents[(1024,b)],parents[(128,b)],fu)
        cross.append({'bucket':b,'support_mask_mean_best_jaccard':sj,'recurrent_mean_best_jaccard':rj,'nonlower':sj>=rj})
    smj=sum(x['support_mask_mean_best_jaccard'] for x in cross)/4; rmj=sum(x['recurrent_mean_best_jaccard'] for x in cross)/4
    gates={
        'exact_source_restored':True,
        'candidate_count_exact_k_all_8':all(p['candidate_count_exact_k'] for p in panels),
        'rank_identity_preserved_all_8':all(p['rank_identity_preserved'] for p in panels),
        'support_at_least_4_all_8':all(p['support_at_least_4'] for p in panels),
        'parent_subset_all_8':all(p['parent_subset_all'] for p in panels),
        'exact_mask_or_fallback_rule_all_8':True,
        'pairwise_disjoint_all_8':all(p['pairwise_disjoint'] for p in panels),
        'mechanism_active_all_8':all(p['mechanism_active'] for p in panels),
    }
    verdict='PASS_RECURRENT_TOPOMODAL_SUPPORT_MASK_V1_PRETRUTH' if all(gates.values()) else 'FAIL_RECURRENT_TOPOMODAL_SUPPORT_MASK_V1_PRETRUTH'
    pre={'schema':'ORBITTRACE_RECURRENT_TOPOMODAL_SUPPORT_MASK_V1_PRELABEL','scientific_role':'PRELABEL_RECURRENT_TOPOMODAL_SUPPORT_MASK_V1','source_prelabel_sha256':SOURCE_SHA,'configuration':{'mask':'parent_intersection_with_union_of_all_support_cut_candidate_events','fallback':f'original_parent_iff_mask_support_below_{MIN_SUPPORT}','ranking':'exact_recurrent_eom_parent_rank','candidate_budget':'exact_recurrent_eom_candidate_count'},'subsets':frozen,'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'method_parameter_selection_from_result':False}
    pp=a.output/'RECURRENT_TOPOMODAL_SUPPORT_MASK_V1_PRELABEL.json';pp.write_text(json.dumps(pre,indent=2,sort_keys=True,allow_nan=False)+'\n');ps=sha(pp)
    res={'schema':'ORBITTRACE_RECURRENT_TOPOMODAL_SUPPORT_MASK_V1_PRETRUTH','scientific_role':'ZERO_LABEL_PRETRUTH_AUDIT','verdict':verdict,'prelabel_sha256':ps,'panels':panels,'cross_scale_diagnostic':cross,'aggregate_diagnostic':{'support_mask_cross_scale_mean':smj,'recurrent_cross_scale_mean':rmj,'nonlower_buckets':sum(x['nonlower'] for x in cross)},'gates':gates,'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'method_parameter_selection_from_result':False}
    rp=a.output/'RECURRENT_TOPOMODAL_SUPPORT_MASK_V1_PRETRUTH.json';rp.write_text(json.dumps(res,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':verdict,'prelabel_sha256':ps,'aggregate_diagnostic':res['aggregate_diagnostic'],'gates':gates,'panels':panels},indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
