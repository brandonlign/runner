#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any

SOURCE_SHA='bd0d28410d23bef0c5c8847ecd8d54e91b74e148ce62e8533407787d265e468f'
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
    fs=[mem(r) for r in fine];cs=restrict(coarse,u)
    if not fs:return 0.0
    vals=[]
    for a in fs:
        best=0.0
        for b in cs:
            i=len(a&b)
            if i:best=max(best,i/len(a|b))
        vals.append(best)
    return sum(vals)/len(vals)
def family_hash(ids:frozenset[str])->str:
    return hashlib.sha256(('\n'.join(sorted(ids))+'\n').encode()).hexdigest()

def build(row:dict[str,Any]):
    K=int(row['equal_budget_k']); parents=list(row['recurrent_candidates']); children=list(row['successor_candidates'])
    req(len(parents)==K,'parent count changed')
    req([int(x['rank']) for x in parents]==list(range(1,K+1)),'parent rank changed')
    req(disjoint(parents),'parents not disjoint'); req(disjoint(children),'children not disjoint')
    assigned={r:[] for r in range(1,K+1)}
    for c in children:
        r=int(c['corroborating_parent_rank']); req(1<=r<=K,'invalid child parent'); assigned[r].append(c)
        overlaps=[i+1 for i,p in enumerate(parents) if mem(c)&mem(p)]
        req(overlaps==[r],f'child overlap provenance changed: {overlaps} != {[r]}')
    out=[]; audit=[]; seen_child=[]
    for r,p in enumerate(parents,1):
        ps=mem(p); cs=assigned[r]; us=set(ps)
        for c in cs: us.update(mem(c)); seen_child.append(str(c['family_hash']))
        u=frozenset(us)
        outside=len(u-ps); ratio=len(u)/len(ps)
        rec=dict(p)
        rec['event_ids']=sorted(u)
        rec['member_count']=len(u)
        rec['family_id']=f'component-union-d{row["denominator"]}-b{row["bucket"]}-r{r}'
        rec['family_hash']=family_hash(u)
        rec['component_union_rank']=r
        rec['catalogue_source']='recurrent_topomodal_component_union'
        rec['parent_family_id']=str(p['family_id'])
        rec['parent_family_hash']=str(p['family_hash'])
        rec['child_family_hashes']=[str(c['family_hash']) for c in cs]
        rec['child_count']=len(cs)
        rec['parent_member_count']=len(ps)
        rec['outside_parent_count']=outside
        rec['membership_expansion_ratio']=ratio
        out.append(rec)
        audit.append({'rank':r,'parent_family_id':str(p['family_id']),'parent_family_hash':str(p['family_hash']),'child_count':len(cs),'child_family_hashes':[str(c['family_hash']) for c in cs],'parent_member_count':len(ps),'union_member_count':len(u),'outside_parent_count':outside,'outside_parent_fraction':outside/len(u) if u else 0.0,'membership_expansion_ratio':ratio})
    req(sorted(seen_child)==sorted(str(c['family_hash']) for c in children),'child omitted or duplicated')
    return out,audit

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument('--source-prelabel',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.source_prelabel)==SOURCE_SHA,'source prelabel changed')
    src=json.loads(a.source_prelabel.read_text())
    req(src['schema']=='ORBITTRACE_RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1_PRELABEL','wrong source schema')
    req(src['scientific_role']=='PRELABEL_RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1','wrong source role')
    for flag in ('shower_truth_used','target_information_access','target_region_events_accessed','sonotaco_2013_2014_access','amos_scientific_access','maarsy_scientific_access','dms_scientific_access'):
        req(src.get(flag) is False,f'firewall flag {flag}')
    sm={(int(x['denominator']),int(x['bucket'])):x for x in src['subsets']};keys=set(EXPECTED_K);req(set(sm)==keys,'panel set')
    orders={};parents={};universes={};panels=[];frozen=[]
    for key in sorted(keys):
        row=sm[key];K=EXPECTED_K[key];req(int(row['equal_budget_k'])==K,'K changed')
        out,audit=build(row);pr=list(row['recurrent_candidates'])
        universe=set(row['annual_event_ids']['2022'])|set(row['annual_event_ids']['2023']);req(len(universe)==int(row['event_count']),'universe changed')
        req(len(out)==K,'successor count != K');req([int(x['component_union_rank']) for x in out]==list(range(1,K+1)),'successor rank')
        exact_union=True;parent_contained=True
        child_seen=[]
        for r,(cand,p) in enumerate(zip(out,pr),1):
            ps=mem(p); expected=set(ps)
            cs=[c for c in row['successor_candidates'] if int(c['corroborating_parent_rank'])==r]
            for c in cs: expected.update(mem(c)); child_seen.append(str(c['family_hash']))
            exact_union &= mem(cand)==frozenset(expected); parent_contained &= ps.issubset(mem(cand))
        child_complete=sorted(child_seen)==sorted(str(c['family_hash']) for c in row['successor_candidates'])
        req(all(mem(r).issubset(universe) for r in out),'union outside universe')
        ratios=[x['membership_expansion_ratio'] for x in audit]; outs=[x['outside_parent_fraction'] for x in audit]
        pstats={'denominator':key[0],'bucket':key[1],'K':K,'successor_count':len(out),'parents_with_child':sum(x['child_count']>0 for x in audit),'source_child_count':len(row['successor_candidates']),'mean_membership_expansion_ratio':sum(ratios)/len(ratios),'max_membership_expansion_ratio':max(ratios),'mean_outside_parent_fraction':sum(outs)/len(outs),'max_outside_parent_fraction':max(outs),'parent_contained_all':parent_contained,'exact_union_all':exact_union,'child_complete_once':child_complete,'pairwise_disjoint':disjoint(out),'support_ge_4_all':all(len(mem(r))>=4 for r in out),'rank_identity':all(int(x['component_union_rank'])==i for i,x in enumerate(out,1))}
        panels.append(pstats);orders[key]=out;parents[key]=pr;universes[key]=universe
        frozen.append({'denominator':key[0],'bucket':key[1],'event_count':len(universe),'annual_event_ids':row['annual_event_ids'],'equal_budget_k':K,'successor_candidates':out,'recurrent_candidates':pr,'component_union_audit':audit})
    cross=[]
    for b in BS:
        fk=(1024,b);ck=(128,b);fu=universes[fk];req(fu.issubset(universes[ck]),'fine not nested')
        sj=mbj(orders[fk],orders[ck],fu);rj=mbj(parents[fk],parents[ck],fu)
        cross.append({'bucket':b,'successor_mean_best_jaccard':sj,'recurrent_mean_best_jaccard':rj,'nonlower':sj>=rj})
    smn=sum(x['successor_mean_best_jaccard'] for x in cross)/4;rmn=sum(x['recurrent_mean_best_jaccard'] for x in cross)/4;n=sum(x['nonlower'] for x in cross)
    gates={'immutable_source_and_firewall':True,'parent_rank_valid_all_8':all(p['rank_identity'] for p in panels),'child_unique_parent_source_valid':True,'successor_count_exact_k_all_8':all(p['successor_count']==p['K'] for p in panels),'successor_rank_matches_parent_all_8':all(p['rank_identity'] for p in panels),'parent_contained_all_8':all(p['parent_contained_all'] for p in panels),'exact_union_all_8':all(p['exact_union_all'] for p in panels),'child_complete_once_all_8':all(p['child_complete_once'] for p in panels),'pairwise_disjoint_all_8':all(p['pairwise_disjoint'] for p in panels),'support_ge_4_all_8':all(p['support_ge_4_all'] for p in panels),'cross_scale_nonlower_4_of_4':n==4,'cross_scale_aggregate_nonlower':smn>=rmn}
    verdict='PASS_RECURRENT_TOPOMODAL_COMPONENT_UNION_V1_PRETRUTH' if all(gates.values()) else 'FAIL_RECURRENT_TOPOMODAL_COMPONENT_UNION_V1_PRETRUTH'
    pre={'schema':'ORBITTRACE_RECURRENT_TOPOMODAL_COMPONENT_UNION_V1_PRELABEL','scientific_role':'PRELABEL_RECURRENT_TOPOMODAL_COMPONENT_UNION_V1','source_prelabel_sha256':SOURCE_SHA,'configuration':{'rule':'one_recurrent_parent_plus_union_of_all_overlap_confirmed_topomodal_children','ranking':'exact_recurrent_parent_rank','equal_budget':'exact_recurrent_parent_count_per_panel'},'subsets':frozen,'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'asfn_event_level_access':False,'efn_event_level_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'method_parameter_selection_from_result':False}
    pp=a.output/'RECURRENT_TOPOMODAL_COMPONENT_UNION_V1_PRELABEL.json';pp.write_text(json.dumps(pre,indent=2,sort_keys=True)+'\n');ps=sha(pp)
    res={'schema':'ORBITTRACE_RECURRENT_TOPOMODAL_COMPONENT_UNION_V1_PRETRUTH','scientific_role':'ZERO_LABEL_PRETRUTH_AUTHORIZATION','verdict':verdict,'prelabel_sha256':ps,'panels':panels,'cross_scale':cross,'aggregate':{'successor_cross_scale_mean':smn,'recurrent_cross_scale_mean':rmn,'nonlower_buckets':n},'gates':gates,'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'method_parameter_selection_from_result':False}
    (a.output/'RECURRENT_TOPOMODAL_COMPONENT_UNION_V1_PRETRUTH.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'verdict':verdict,'prelabel_sha256':ps,'aggregate':res['aggregate'],'gates':gates,'panels':panels,'cross_scale':cross},indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
