#!/usr/bin/env python3
from __future__ import annotations

import argparse,hashlib,importlib.util,json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np

YEARS=(2022,2023); BLIND=(20.0,55.0); DENOMS=(128,1024); BUCKETS=(0,1,2,3); MIN_SUPPORT=4
BASELINE_SHA='7b1ddfcd32cd0b52321e3b3dfc614a88dd9b973f947c1d4d0de74fddf26b59cd'
BIF_SHA='95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c'

def req(x,m):
    if not x: raise RuntimeError(m)
def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path,n:str)->Any:
    s=importlib.util.spec_from_file_location(n,p); req(s is not None and s.loader is not None,f'cannot import {p}'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def m2d(c:set[str], bif:list[dict[str,Any]])->tuple[float,int]:
    n=len(c); req(n>=MIN_SUPPORT,'sub-support candidate'); total=0.0; k=0
    for b in bif:
        bs=set(map(str,b['event_ids']))
        if bs.issubset(c): total += (len(bs)/n)*float(b['persistence_area']); k+=1
    return float(total),k

def compressed_tree(rows:list[dict[str,Any]])->tuple[list[int|None],list[list[int]]]:
    sets=[set(map(str,r['event_ids'])) for r in rows]; sizes=[len(s) for s in sets]
    by_event:dict[str,list[int]]=defaultdict(list)
    for i,s in enumerate(sets):
        for eid in s: by_event[eid].append(i)
    parent:[int|None]=[None]*len(rows)
    for i,s in enumerate(sets):
        rep=min(s); supers=[]
        for j in by_event[rep]:
            if sizes[j]>sizes[i] and s.issubset(sets[j]): supers.append(j)
        if supers:
            parent[i]=min(supers,key=lambda j:(sizes[j],str(rows[j]['family_hash'])))
    children=[[] for _ in rows]
    for i,p in enumerate(parent):
        if p is not None: children[p].append(i)
    req(all(len(x)<=2 for x in children),'compressed hierarchy nonbinary')
    return parent,children

def evidence_cut(rows:list[dict[str,Any]], parent:list[int|None], children:list[list[int]])->tuple[list[dict[str,Any]],dict[str,Any]]:
    selected=[]; split_nodes=[]; single_child_descents=[]
    def rec(i:int):
        ch=children[i]
        if not ch:
            selected.append(i); return
        if len(ch)==1:
            single_child_descents.append(i); rec(ch[0]); return
        a,b=ch; ps=float(rows[i]['internal_2d_mass']); ca=float(rows[a]['internal_2d_mass']); cb=float(rows[b]['internal_2d_mass'])
        if max(ca,cb)>ps:
            split_nodes.append({'node':i,'parent_m2d':ps,'child_m2d':[ca,cb],'parent_members':int(rows[i]['member_count']),'child_members':[int(rows[a]['member_count']),int(rows[b]['member_count'])]}); rec(a); rec(b)
        else: selected.append(i)
    roots=[i for i,p in enumerate(parent) if p is None]
    for r in roots: rec(r)
    out=[dict(rows[i]) for i in selected]; out.sort(key=lambda r:(-float(r['internal_2d_mass']),str(r['family_hash'])))
    for k,r in enumerate(out,1): r['rank']=k
    sets=[set(map(str,r['event_ids'])) for r in out]
    req(all(not a.intersection(b) for i,a in enumerate(sets) for b in sets[i+1:]),'selected candidates overlap')
    return out,{'reportable_node_count':len(rows),'compressed_root_count':len(roots),'evidence_split_count':len(split_nodes),'single_reportable_child_descent_count':len(single_child_descents),'selected_candidate_count':len(out),'split_examples':split_nodes[:20],'pairwise_disjoint':True}

def sizes(rows:list[dict[str,Any]])->dict[str,float|int]:
    v=sorted(int(r['member_count']) for r in rows); req(v,'empty catalogue')
    return {'candidate_count':len(v),'mean_member_count':float(mean(v)),'median_member_count':float(np.median(v)),'p90_member_count':float(np.quantile(np.asarray(v,float),.9)),'max_member_count':max(v),'min_member_count':min(v)}

def main():
    ap=argparse.ArgumentParser()
    for n in ('structural-runner','structural-result-json','parent-runner','quality-source','support-source-parts','candidate-payload','baseline-payload','scorer-parts','v8-result-json','baseline-m2d-prelabel','bif-prelabel'): ap.add_argument('--'+n,type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); a.output.parent.mkdir(parents=True,exist_ok=True)
    req(sha(a.baseline_m2d_prelabel)==BASELINE_SHA,'baseline M2D changed'); req(sha(a.bif_prelabel)==BIF_SHA,'bif prelabel changed')
    original=load(Path('orbittrace_topomodal_support_resolved_cut_v1/generate_prelabel.py'),'rec_original'); structural=load(a.structural_runner,'rec_structural'); parent_runner=load(a.parent_runner,'rec_parent')
    req(tuple(structural.BLIND)==BLIND and float(structural.RADIUS)==1.0 and int(structural.MIN_SUPPORT)==4,'structural constants'); req(tuple(parent_runner.BLIND)==BLIND,'parent blind')
    req(original.sha256(a.quality_source)==original.QUALITY_SHA256 and original.sha256(a.v8_result_json)==original.V8_RESULT_SHA256 and original.sha256(a.structural_result_json)==original.STRUCTURAL_RESULT_SHA256,'frozen source identity')
    sr=json.loads(a.structural_result_json.read_text()); expected={(int(r['denominator']),int(r['bucket'])):r for r in sr['fits']}; basepre=json.loads(a.baseline_m2d_prelabel.read_text()); bifpre=json.loads(a.bif_prelabel.read_text())
    bm={(int(s['denominator']),int(s['bucket'])):s for s in basepre['subsets']}; bf={(int(s['denominator']),int(s['bucket'])):s for s in bifpre['subsets']}; keys={(d,b) for d in DENOMS for b in BUCKETS}; req(set(expected)==set(bm)==set(bf)==keys,'panel set')
    q=original.load_module(a.quality_source,'rec_loader'); q.v1.mult.YEARS=YEARS; q.v1.mult.MONTH_KEYS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13)); q.v1.mult.TOP_K=100; rt=q.v1.mult.load_frozen_runtime(); support=rt.load_support_module(a.support_source_parts); support.YEARS=YEARS; support.MONTH_KEYS=q.v1.mult.MONTH_KEYS; support.CORPUS='orbittrace-m2d-recursive-evidence-cut-v1-target-excluded'; support.RANKING_VARIANTS=('persistence',); req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'loader blind'); setattr(a,'fixed4_baseline_json',a.v8_result_json); _c,base,_s=support.load_sources(a); scan,_cal,hidden_unused,sources=support.parse_catalogue(base); del hidden_unused; req(sorted(scan)==list(YEARS),'scan years')
    events=[]
    for y in YEARS: events.extend(parent_runner.normalize_event(r,y) for r in list(scan[y]))
    req(len(events)==738682 and all(not(BLIND[0]<=float(e['sol'])<=BLIND[1]) for e in events),'event firewall'); ids=[str(e['id']) for e in events]; hashes=np.asarray([original.event_hash_u64(x) for x in ids],dtype=np.uint64)
    subsets=[]
    for d in DENOMS:
      for b in BUCKETS:
        key=(d,b); ix=original.selected_indices(hashes,d,b); sub=[events[int(i)] for i in ix]; subids=[ids[int(i)] for i in ix]; bs=bm[key]; frozen={str(y):[str(x) for x in bs['annual_event_ids'][str(y)]] for y in YEARS}; req(set(subids)==set(frozen['2022']).union(frozen['2023']),'universe drift')
        full_sets,summary=structural.topomodal_candidates(sub); ex=expected[key]; req(ex['topomodal']['candidate_rows']==summary['candidate_rows'] and int(ex['topomodal']['candidate_count'])==int(summary['candidate_count']),'hierarchy drift')
        rows=[]; bif=list(bf[key]['bifiltration_candidates'])
        for s in full_sets:
            ss=set(map(str,s)); score,k=m2d(ss,bif); rows.append({'family_hash':structural.member_hash(s),'event_ids':sorted(ss),'member_count':len(ss),'internal_2d_mass':score,'internal_bif_component_count':k})
        rows.sort(key=lambda r:(int(r['member_count']),str(r['family_hash'])))
        parent,children=compressed_tree(rows); selected,cut=evidence_cut(rows,parent,children)
        baseline=list(bs['successor_candidates']); req(len(selected)>0 and cut['pairwise_disjoint'],'bad cut')
        subsets.append({'denominator':d,'bucket':b,'event_count':len(subids),'annual_event_ids':frozen,'equal_budget_k':int(bs['equal_budget_k']),'refined_candidates':selected,'baseline_candidates':baseline,'cut_summary':cut,'size_summary':{'refined':sizes(selected),'baseline':sizes(baseline)}})
        print(f'[recursive-evidence] d={d} b={b} nodes={len(rows)} selected={len(selected)} splits={cut["evidence_split_count"]}',flush=True)
    allr=[r for s in subsets for r in s['refined_candidates']]; allb=[r for s in subsets for r in s['baseline_candidates']]
    payload={'schema':'ORBITTRACE_M2D_RECURSIVE_EVIDENCE_CUT_V1_PRETRUTH','scientific_role':'TARGET_EXCLUDED_GMN_RECURSIVE_M2D_EVIDENCE_CUT_FROZEN_BEFORE_TRUTH','configuration':{'radius':1.0,'minimum_support':4,'split_rule':'recurse_both_reportable_children_iff_max_child_M2D_strictly_exceeds_parent_M2D;compress_subsupport_twigs','ranking':['internal_2d_mass_desc','family_hash_asc'],'new_tuned_parameters':[]},'baseline_m2d_prelabel_sha256':BASELINE_SHA,'bif_prelabel_sha256':BIF_SHA,'subsets':subsets,'global_size_summary':{'refined':sizes(allr),'baseline':sizes(allb)},'total_evidence_split_count':sum(int(s['cut_summary']['evidence_split_count']) for s in subsets),'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'orbittrace_reveal_access':False,'sonotaco_scientific_access':False,'post_result_parameter_search':False}
    a.output.write_text(json.dumps(payload,separators=(',',':'),sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':'RECURSIVE_EVIDENCE_PRETRUTH_SEALED','sha256':sha(a.output),'total_splits':payload['total_evidence_split_count'],'global_size_summary':payload['global_size_summary']},indent=2,sort_keys=True))
if __name__=='__main__': main()
