#!/usr/bin/env python3
from __future__ import annotations

import argparse,hashlib,importlib.util,json,math
from pathlib import Path
from typing import Any
import numpy as np
from gudhi.clustering.tomato import Tomato
from scipy.spatial import cKDTree

SOURCE_PRELABEL_SHA='db608f84bf333d18d624199f2d31c27b4183ee3a75a3d930cef4b9766a19d4de'
MANIFEST_SHA='3ed5c33216d7d1cf2cbc703da088b3a86132e50532fb996cfe475d7f6052d7f8'
MIN_SUPPORT=4; RADIUS=1.0; BUCKETS=(0,1,2,3)

def req(x:bool,m:str)->None:
    if not x: raise RuntimeError(m)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path,n:str)->Any:
    s=importlib.util.spec_from_file_location(n,p); req(s is not None and s.loader is not None,f'cannot import {p}'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def family_hash(members:frozenset[str])->str:return hashlib.sha256('|'.join(sorted(members)).encode()).hexdigest()[:20]
def diagram_sorted(a:np.ndarray)->np.ndarray:
    a=np.asarray(a,dtype=float)
    if a.size==0:return np.empty((0,2),dtype=float)
    req(a.ndim==2 and a.shape[1]==2 and np.all(np.isfinite(a)),'invalid diagram'); return a[np.lexsort((a[:,1],a[:,0]))]
def jaccard(a:frozenset[str],b:frozenset[str])->float:
    u=len(a|b); return float(len(a&b)/u) if u else 0.0
def cross_scale(coarse:list[frozenset[str]],fine:list[frozenset[str]],fine_universe:frozenset[str])->dict[str,Any]:
    restricted=[]
    for c in coarse:
        r=frozenset(c&fine_universe)
        if len(r)>=MIN_SUPPORT: restricted.append(r)
    scores=[]
    for f in fine:
        scores.append(max((jaccard(f,c) for c in restricted),default=0.0))
    return {'fine_candidate_count':len(fine),'restricted_coarse_candidate_count':len(restricted),'fine_to_coarse_scores':scores,'fine_to_coarse_mean_best_jaccard':float(np.mean(scores)) if scores else 0.0,'fine_to_coarse_median_best_jaccard':float(np.median(scores)) if scores else 0.0}

def excess_cut(structural:Any,events:list[dict[str,Any]])->tuple[list[dict[str,Any]],dict[str,Any]]:
    ordered=sorted(events,key=lambda e:str(e['id'])); ids=[str(e['id']) for e in ordered]; n=len(ids); req(n>=4,'small panel')
    Z=np.asarray(structural.physical_embedding(ordered),dtype=float); req(Z.shape==(n,6) and np.all(np.isfinite(Z)),'embedding')
    neigh=[list(map(int,r)) for r in cKDTree(Z).query_ball_point(Z,r=RADIUS,p=2.0,eps=0.0,return_sorted=True)]; adj=[set(r) for r in neigh]
    req(all(i in adj[i] for i in range(n)) and all(i in adj[j] for i,r in enumerate(neigh) for j in r),'graph')
    rho=np.asarray([len(r)/float(n) for r in neigh],dtype=float); req(np.all(rho>0) and np.all(np.isfinite(rho)),'density')
    model=Tomato(graph_type='manual',density_type='manual'); model.fit(neigh,weights=rho)
    labels=np.asarray(model.leaf_labels_,dtype=np.int64); L=int(model.n_leaves_); children=np.asarray(model.children_,dtype=np.int64).reshape((-1,2)); roots_expected=len(np.asarray(model.max_weight_per_cc_,dtype=float)); req(L-len(children)==roots_expected,'root arithmetic')
    ds=diagram_sorted(np.asarray(model.diagram_,dtype=float)); P=np.sort(np.asarray(ds[:,0]-ds[:,1],dtype=float)) if ds.size else np.empty(0,dtype=float); req(len(P)==len(children) and np.all(P>=-1e-15),'persistence'); P=np.maximum(P,0.0)
    N=L+len(children); members:[Any]=[None]*N; parent=np.full(N,-1,dtype=np.int64); kids:[Any]=[None]*N; active_peak=np.full(N,np.nan); active_key:[Any]=[None]*N; merge_level=np.full(N,np.nan)
    for leaf in range(L):
        ix=np.flatnonzero(labels==leaf); req(len(ix)>0,'empty leaf'); members[leaf]=frozenset(ids[int(i)] for i in ix); pk=float(np.max(rho[ix])); active_peak[leaf]=pk; active_key[leaf]=min(ids[int(i)] for i in ix if float(rho[int(i)])==pk)
    reconstructed=[]
    for off,pair in enumerate(children):
        node=L+off; a,b=int(pair[0]),int(pair[1]); req(0<=a<node and 0<=b<node and parent[a]==-1 and parent[b]==-1,'hierarchy')
        ma,mb=members[a],members[b]; req(ma is not None and mb is not None and ma.isdisjoint(mb),'child membership'); pa,pb=float(active_peak[a]),float(active_peak[b]); ka,kb=str(active_key[a]),str(active_key[b])
        winner,loser=(a,b) if (pa>pb or (pa==pb and ka<kb)) else (b,a); members[node]=frozenset(ma|mb); kids[node]=(a,b); parent[a]=node; parent[b]=node; active_peak[node]=active_peak[winner]; active_key[node]=active_key[winner]
        death=float(active_peak[loser])-float(P[off]); merge_level[node]=death; reconstructed.append([float(active_peak[loser]),death])
    roots=np.flatnonzero(parent==-1); req(len(roots)==roots_expected and sum(len(members[int(r)]) for r in roots)==n,'roots')
    rec=diagram_sorted(np.asarray(reconstructed,dtype=float)); req(rec.shape==ds.shape and np.allclose(rec,ds,rtol=0,atol=1e-12),'diagram reconstruction'); diagerr=float(np.max(np.abs(rec-ds))) if rec.size else 0.0
    complete,complete_summary=structural.topomodal_candidates(ordered); complete_members={tuple(sorted(map(str,m))) for m in complete}
    stability=np.zeros(N,dtype=float); lower=np.zeros(N,dtype=float); upper=np.zeros(N,dtype=float)
    id_to_ix={eid:i for i,eid in enumerate(ids)}
    for node in range(N):
        m=members[node]; req(m is not None,'missing node'); p=int(parent[node]); lo=0.0 if p==-1 else float(merge_level[p]); up=float(active_peak[node]) if kids[node] is None else float(merge_level[node]); req(math.isfinite(lo) and math.isfinite(up) and up+1e-12>=lo,f'lifetime {node}: {lo} {up}'); lo=max(0.0,lo); up=max(lo,up); lower[node]=lo; upper[node]=up
        ix=np.asarray([id_to_ix[eid] for eid in m],dtype=np.int64); stability[node]=float(np.sum(np.maximum(0.0,np.minimum(rho[ix],up)-lo))); req(math.isfinite(stability[node]) and stability[node]>=0,'stability')
    best_score=np.zeros(N,dtype=float); selected:[Any]=[None]*N
    def solve(node:int)->tuple[float,tuple[int,...]]:
        if selected[node] is not None:return float(best_score[node]),selected[node]
        ch=kids[node]; child_score=0.0; child_nodes:tuple[int,...]=()
        if ch is not None:
            parts=[]
            for c in ch:
                sc,sn=solve(int(c)); child_score+=sc; parts.extend(sn)
            child_nodes=tuple(parts)
        reportable=len(members[node])>=MIN_SUPPORT; self_score=float(stability[node]) if reportable else -1.0
        if reportable and self_score>=child_score:
            best_score[node]=self_score; selected[node]=(node,)
        else:
            best_score[node]=child_score; selected[node]=child_nodes
        return float(best_score[node]),selected[node]
    chosen=[]
    for r in roots:
        _s,ns=solve(int(r)); chosen.extend(ns)
    req(len(chosen)==len(set(chosen)),'duplicate selection'); chosen_sets=[members[x] for x in chosen]
    for i,a in enumerate(chosen_sets):
        for b in chosen_sets[i+1:]:req(a.isdisjoint(b),'selection overlap')
    req(all(tuple(sorted(m)) in complete_members for m in chosen_sets),'selected node outside #1284 hierarchy')
    rows=[]
    for node,m in zip(chosen,chosen_sets):
        tup=tuple(sorted(m)); rows.append({'family_hash':structural.member_hash(m),'event_ids':list(tup),'member_count':len(tup),'node':int(node),'is_root':bool(parent[node]==-1),'stability':float(stability[node]),'lower_density':float(lower[node]),'upper_density':float(upper[node]),'active_mode_peak':float(active_peak[node]),'active_mode_key':str(active_key[node])})
    rows.sort(key=lambda r:(-float(r['stability']),str(r['family_hash'])))
    for rank,r in enumerate(rows,1):r['rank']=rank
    return rows,{'selected_candidate_count':len(rows),'complete_candidate_count':len(complete),'complete_candidate_rows':complete_summary['candidate_rows'],'selected_candidate_rows':sorted([{'family_hash':r['family_hash'],'member_count':r['member_count']} for r in rows],key=lambda r:(-r['member_count'],r['family_hash'])),'root_count':len(roots),'selected_root_count':sum(bool(r['is_root']) for r in rows),'pairwise_disjoint':True,'diagram_reconstruction_max_abs_error':diagerr,'total_selected_stability':float(sum(r['stability'] for r in rows))}

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--source-prelabel',type=Path,required=True); ap.add_argument('--universe-manifest',type=Path,required=True); ap.add_argument('--geometry-source',type=Path,required=True); ap.add_argument('--structural-runner',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.source_prelabel)==SOURCE_PRELABEL_SHA,'source prelabel hash'); req(sha(a.universe_manifest)==MANIFEST_SHA,'manifest hash'); src=json.loads(a.source_prelabel.read_text()); manifest=json.loads(a.universe_manifest.read_text()); req(src['shower_truth_used'] is False and manifest['shower_label_accessed'] is False,'pretruth firewall')
    geom=load(a.geometry_source,'eom_geom'); structural=load(a.structural_runner,'eom_structural'); geometry=geom.sparse_geometry(manifest)
    results=[]; runtime={}
    for row in src['subsets']:
        d,b=int(row['denominator']),int(row['bucket']); ids=list(map(str,manifest['subsets'][f'd{d}_b{b}'])); events=[geometry[eid] for eid in ids]; req(len(events)==int(row['events_total']),'panel count'); req(structural.universe_hash(ids)==str(row['event_universe_sha256']) if hasattr(structural,'universe_hash') else True,'universe hash')
        print(f'[eom-cut] d={d} b={b} n={len(events)}',flush=True); selected,summary=excess_cut(structural,events); req(summary['complete_candidate_rows']==row['topomodal_summary']['candidate_rows'] and summary['complete_candidate_count']==len(row['topomodal_candidates']),'#1284 exactness'); req(summary['diagram_reconstruction_max_abs_error']<=1e-12,'diagram error'); req(len(selected)>0,'empty selected set')
        recurrent=[frozenset(map(str,r['event_ids'])) for r in row['recurrent_candidates']]; results.append({'denominator':d,'bucket':b,'events_total':len(ids),'event_universe_sha256':row['event_universe_sha256'],'selected_candidates':selected,'selected_summary':summary,'recurrent_candidates':row['recurrent_candidates'],'recurrent_count':len(recurrent)})
        runtime[(d,b)]={'selected':[frozenset(map(str,r['event_ids'])) for r in selected],'recurrent':recurrent,'ids':frozenset(ids)}
    pairs=[]; s_all=[]; p_all=[]; wins=0
    for b in BUCKETS:
        fine=runtime[(1024,b)]; coarse=runtime[(128,b)]; sm=cross_scale(coarse['selected'],fine['selected'],fine['ids']); pm=cross_scale(coarse['recurrent'],fine['recurrent'],fine['ids']); sv=sm['fine_to_coarse_mean_best_jaccard']; pv=pm['fine_to_coarse_mean_best_jaccard']; wins+=int(sv>pv); s_all.extend(sm['fine_to_coarse_scores']); p_all.extend(pm['fine_to_coarse_scores']); pairs.append({'bucket':b,'selected':sm,'recurrent_eom':pm,'strict_win':sv>pv})
    sp=float(np.mean(s_all)) if s_all else 0.0; pp=float(np.mean(p_all)) if p_all else 0.0; smed=float(np.median([p['selected']['fine_to_coarse_mean_best_jaccard'] for p in pairs])); pmed=float(np.median([p['recurrent_eom']['fine_to_coarse_mean_best_jaccard'] for p in pairs]))
    gates={'pooled_jaccard_strictly_better':sp>pp,'median_bucket_jaccard_strictly_better':smed>pmed,'strict_bucket_wins_at_least_3_of_4':wins>=3,'selected_nonempty_all_eight':all(len(r['selected_candidates'])>0 for r in results),'complete_1284_exactness_all_eight':True,'diagram_reconstruction_all_eight':all(r['selected_summary']['diagram_reconstruction_max_abs_error']<=1e-12 for r in results)}
    verdict='PASS_TOPOMODAL_EXCESS_MASS_CUT_STRUCTURAL_V1' if all(gates.values()) else 'FAIL_TOPOMODAL_EXCESS_MASS_CUT_STRUCTURAL_V1'
    out={'schema':'ORBITTRACE_TOPOMODAL_EXCESS_MASS_CUT_STRUCTURAL_V1','scientific_role':'ZERO_LABEL_STRUCTURAL_DIAGNOSTIC_ONLY','verdict':verdict,'configuration':{'stability':'sum_i max(0,min(rho_i,upper)-lower)','selection':'dynamic_program_max_total_stability_parent_on_tie','ranking':'selected_stability_desc_then_family_hash','support_floor':4,'equal_truth_budget_if_promoted':'min(selected_count,recurrent_count)'},'panels':results,'pairs':pairs,'summary':{'selected_pooled_jaccard':sp,'recurrent_pooled_jaccard':pp,'selected_median_bucket_jaccard':smed,'recurrent_median_bucket_jaccard':pmed,'strict_bucket_wins':wins,'gates':gates},'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'method_parameter_selection_from_result':False}
    p=a.output/'TOPOMODAL_EXCESS_MASS_CUT_STRUCTURAL_V1.json'; p.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':verdict,'summary':out['summary'],'candidate_counts':[{'d':r['denominator'],'b':r['bucket'],'selected':len(r['selected_candidates']),'recurrent':r['recurrent_count']} for r in results]},indent=2,sort_keys=True)); return 0
if __name__=='__main__':raise SystemExit(main())
