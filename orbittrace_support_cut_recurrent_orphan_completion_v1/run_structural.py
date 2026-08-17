#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any

SUPPORT_SHA='4529eadd9ff93aae057f0a6fd5e0dd923f2300b7c6e01b74a0b7638e22da6de6'
UNIVERSE_SHA='95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c'
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

def build(srows:list[dict[str,Any]],prows:list[dict[str,Any]]):
    req(disjoint(srows),'support rows not disjoint');req(disjoint(prows),'recurrent rows not disjoint')
    ss=[mem(r) for r in srows]; emitted_support=set(); out=[]; audit=[]
    rep_rank={}
    for prank,p in enumerate(prows,1):
        req(int(p.get('rank',prank))==prank,'recurrent order changed')
        ps=mem(p);counts=[len(ps&s) for s in ss];best=max(counts,default=0)
        if best>0:
            choices=[i for i,c in enumerate(counts) if c==best]
            w=min(choices,key=lambda i:str(srows[i]['family_hash']))
            if w not in emitted_support:
                emitted_support.add(w);r=dict(srows[w]);r['catalogue_source']='support_projection';r['witness_recurrent_rank']=prank;r['witness_intersection_count']=best;out.append(r)
            rr=next(i+1 for i,r in enumerate(out) if r.get('catalogue_source')=='support_projection' and str(r['family_hash'])==str(srows[w]['family_hash']))
            rep_rank[prank]=rr
            audit.append({'recurrent_rank':prank,'recurrent_family_id':str(p['family_id']),'max_support_intersection':best,'representation_source':'support_projection','representation_family_id':str(srows[w]['family_id']),'representation_rank':rr})
        else:
            r=dict(p);r['catalogue_source']='recurrent_orphan';r['witness_recurrent_rank']=prank;r['witness_intersection_count']=0;out.append(r);rr=len(out);rep_rank[prank]=rr
            audit.append({'recurrent_rank':prank,'recurrent_family_id':str(p['family_id']),'max_support_intersection':0,'representation_source':'recurrent_orphan','representation_family_id':str(p['family_id']),'representation_rank':rr})
    for i,r0 in enumerate(srows):
        if i in emitted_support:continue
        r=dict(r0);r['catalogue_source']='support_append';r['witness_recurrent_rank']=None;r['witness_intersection_count']=None;out.append(r)
    for rank,r in enumerate(out,1):r['orphan_completion_rank']=rank
    return out,audit,rep_rank

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument('--support-prelabel',type=Path,required=True);ap.add_argument('--universe-prelabel',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.support_prelabel)==SUPPORT_SHA,'support prelabel changed');req(sha(a.universe_prelabel)==UNIVERSE_SHA,'universe prelabel changed')
    s=json.loads(a.support_prelabel.read_text());u=json.loads(a.universe_prelabel.read_text())
    req(s['scientific_role']=='PRELABEL_TOPOMODAL_SUPPORT_RESOLVED_CUT_V1' and u['scientific_role']=='PRELABEL_TARGET_EXCLUDED_GMN_RANKING_RECOVERY','wrong roles')
    for x in (s,u):
        req(x['shower_truth_used'] is False,'truth in input');req(x['target_information_access'] is False and x['target_region_events_accessed'] is False,'target firewall');req(x['sonotaco_2013_2014_access'] is False,'SonotaCo flag')
    sm={(int(x['denominator']),int(x['bucket'])):x for x in s['subsets']};um={(int(x['denominator']),int(x['bucket'])):x for x in u['subsets']};keys=set(EXPECTED_K);req(set(sm)==set(um)==keys,'panel set')
    orders={};parents={};universes={};panels=[];frozen=[]
    for key in sorted(keys):
        ss,uu=sm[key],um[key];K=EXPECTED_K[key];req(int(ss['equal_budget_k'])==int(uu['equal_budget_k'])==K,'K changed')
        srows=list(ss['successor_candidates']);prows=list(ss['recurrent_candidates']);req(len(srows)>=K and len(prows)>=K,'capacity')
        req([int(r['rank']) for r in srows]==list(range(1,len(srows)+1)),'support order');req([int(r['rank']) for r in prows]==list(range(1,len(prows)+1)),'parent order')
        universe=set();[universe.update(str(v) for v in vals) for vals in uu['annual_event_ids'].values()];req(len(universe)==int(uu['event_count'])==int(ss['events_total']),'universe changed')
        req(all(mem(r).issubset(universe) for r in srows+prows),'candidate outside universe')
        out,audit,rep=build(srows,prows)
        # Orphans must have zero overlap with every support candidate.
        supportsets=[mem(r) for r in srows]
        orphans=[r for r in out if r['catalogue_source']=='recurrent_orphan']
        orphan_zero=all(all(not(mem(r)&z) for z in supportsets) for r in orphans)
        req(len({str(r['family_id']) for r in out})==len(out),'output family id collision')
        orders[key]=out;parents[key]=prows;universes[key]=universe
        top_nonexp=all(rep[i]<=i for i in range(1,K+1));complete=len(rep)==len(prows)
        panels.append({'denominator':key[0],'bucket':key[1],'K':K,'candidate_count':len(out),'support_candidate_count':len(srows),'recurrent_candidate_count':len(prows),'recurrent_orphan_count':len(orphans),'support_projection_count':sum(r['catalogue_source']=='support_projection' for r in out),'global_pairwise_disjoint':disjoint(out),'complete_parent_representation':complete,'topk_parent_rank_nonexpansion':top_nonexp,'orphan_zero_support_overlap':orphan_zero})
        frozen.append({'denominator':key[0],'bucket':key[1],'event_count':len(universe),'annual_event_ids':uu['annual_event_ids'],'equal_budget_k':K,'successor_candidates':out,'recurrent_candidates':prows,'representation_audit':audit})
    cross=[]
    for b in BS:
        fk=(1024,b);ck=(128,b);fu=universes[fk];req(fu.issubset(universes[ck]),'fine not nested')
        oj=mbj(orders[fk][:EXPECTED_K[fk]],orders[ck][:EXPECTED_K[ck]],fu);rj=mbj(parents[fk][:EXPECTED_K[fk]],parents[ck][:EXPECTED_K[ck]],fu)
        cross.append({'bucket':b,'orphan_completion_mean_best_jaccard':oj,'recurrent_mean_best_jaccard':rj,'nonlower':oj>=rj})
    om=sum(x['orphan_completion_mean_best_jaccard'] for x in cross)/4;rm=sum(x['recurrent_mean_best_jaccard'] for x in cross)/4;n=sum(x['nonlower'] for x in cross)
    gates={'candidate_capacity_all_8':all(p['candidate_count']>=p['K'] for p in panels),'global_pairwise_disjoint_all_8':all(p['global_pairwise_disjoint'] for p in panels),'complete_parent_representation_all':all(p['complete_parent_representation'] for p in panels),'topk_parent_rank_nonexpansion_all':all(p['topk_parent_rank_nonexpansion'] for p in panels),'orphan_zero_support_overlap_all':all(p['orphan_zero_support_overlap'] for p in panels),'cross_scale_mean_not_lower_than_recurrent':om>=rm,'cross_scale_nonlower_4_of_4':n==4,'immutable_membership_budget_order_audit':True}
    verdict='PASS_SUPPORT_CUT_RECURRENT_ORPHAN_COMPLETION_V1_STRUCTURAL' if all(gates.values()) else 'FAIL_SUPPORT_CUT_RECURRENT_ORPHAN_COMPLETION_V1_STRUCTURAL'
    pre={'schema':'ORBITTRACE_SUPPORT_CUT_RECURRENT_ORPHAN_COMPLETION_V1_PRELABEL','scientific_role':'PRELABEL_SUPPORT_CUT_RECURRENT_ORPHAN_COMPLETION_V1','support_prelabel_sha256':SUPPORT_SHA,'universe_prelabel_sha256':UNIVERSE_SHA,'configuration':{'rule':'max_exact_intersection_support_projection_else_zero_overlap_recurrent_orphan_then_native_support_append','equal_budget':'stored_recurrent_candidate_count_per_panel'},'subsets':frozen,'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'method_parameter_selection_from_result':False}
    pp=a.output/'SUPPORT_CUT_RECURRENT_ORPHAN_COMPLETION_V1_PRELABEL.json';pp.write_text(json.dumps(pre,indent=2,sort_keys=True)+'\n');ps=sha(pp)
    res={'schema':'ORBITTRACE_SUPPORT_CUT_RECURRENT_ORPHAN_COMPLETION_V1_STRUCTURAL','scientific_role':'ZERO_LABEL_STRUCTURAL_GATE','verdict':verdict,'prelabel_sha256':ps,'panels':panels,'cross_scale':cross,'aggregate':{'orphan_completion_cross_scale_mean':om,'recurrent_cross_scale_mean':rm,'nonlower_buckets':n},'gates':gates,'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'method_parameter_selection_from_result':False}
    (a.output/'SUPPORT_CUT_RECURRENT_ORPHAN_COMPLETION_V1_STRUCTURAL.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'verdict':verdict,'prelabel_sha256':ps,'aggregate':res['aggregate'],'gates':gates,'panels':panels,'cross_scale':cross},indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())