#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from typing import Any
import numpy as np
from gudhi.clustering.tomato import Tomato
from scipy.spatial import cKDTree

YEARS=(2022,2023); MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13)); BLIND=(20.0,55.0); BUCKETS=(0,1,2,3); RADIUS=1.0
QUALITY_SHA256="dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"; V8_RESULT_SHA256="fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"; STRUCTURAL_RESULT_SHA256="e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497"

def lineage_ranked(base:Any,structural:Any,events:list[dict[str,Any]])->tuple[list[dict[str,Any]],dict[str,Any]]:
    ordered=sorted(events,key=lambda e:str(e["id"])); ids=[str(e["id"]) for e in ordered]; Z=structural.physical_embedding(ordered)
    neigh=[list(map(int,r)) for r in cKDTree(Z).query_ball_point(Z,r=RADIUS,p=2.0,eps=0.0,return_sorted=True)]; deg=np.asarray([len(r) for r in neigh],dtype=float); rho=deg/len(ids)
    model=Tomato(graph_type="manual",density_type="manual"); model.fit(neigh,weights=rho); labels=np.asarray(model.leaf_labels_,dtype=np.int64); L=int(model.n_leaves_); children=np.asarray(model.children_,dtype=np.int64).reshape((-1,2)); roots_expected=len(np.asarray(model.max_weight_per_cc_,dtype=float)); base.req(L-len(children)==roots_expected,"root arithmetic")
    diagram=np.asarray(model.diagram_,dtype=float); ds=base.diagram_sorted(diagram); P=np.sort(np.asarray(diagram[:,0]-diagram[:,1],dtype=float)) if diagram.size else np.empty(0); base.req(len(P)==len(children),"persistence count"); P=np.maximum(P,0.0)
    N=L+len(children); members:[Any]=[None]*N; parent=np.full(N,-1,dtype=np.int64); active_peak=np.full(N,np.nan); active_key:[Any]=[None]*N; merge_level=np.full(N,np.nan)
    for leaf in range(L):
        ix=np.flatnonzero(labels==leaf); members[leaf]=frozenset(ids[int(i)] for i in ix); peak=float(np.max(rho[ix])); keys=sorted(ids[int(i)] for i in ix if float(rho[int(i)])==peak); active_peak[leaf]=peak; active_key[leaf]=keys[0]
    rec=[]
    for off,pair in enumerate(children):
        node=L+off; a,b=int(pair[0]),int(pair[1]); ma,mb=members[a],members[b]; base.req(ma is not None and mb is not None and ma.isdisjoint(mb) and parent[a]==-1 and parent[b]==-1,"bad hierarchy")
        pa,pb=float(active_peak[a]),float(active_peak[b]); ka,kb=str(active_key[a]),str(active_key[b]); winner,loser=(a,b) if pa>pb or (pa==pb and ka<kb) else (b,a)
        members[node]=frozenset(ma.union(mb)); parent[a]=node; parent[b]=node; active_peak[node]=float(active_peak[winner]); active_key[node]=str(active_key[winner]); death=float(active_peak[loser])-float(P[off]); merge_level[node]=death; rec.append([float(active_peak[loser]),death])
    roots=np.flatnonzero(parent==-1); base.req(len(roots)==roots_expected and sum(len(members[int(r)]) for r in roots)==len(ids),"roots")
    rr=base.diagram_sorted(np.asarray(rec,dtype=float)); base.req(rr.shape==ds.shape and np.allclose(rr,ds,rtol=0,atol=1e-12),"diagram reconstruction")
    full,summary=structural.topomodal_candidates(ordered); eligible={tuple(sorted(str(x) for x in m)) for m in full}; node_by_members={}
    for node,m in enumerate(members):
        tup=tuple(sorted(str(x) for x in m));
        if tup in eligible and tup not in node_by_members: node_by_members[tup]=node
    base.req(set(node_by_members)==eligible,"eligible hierarchy mapping")
    rows=[]
    for tup,node in node_by_members.items():
        p=int(parent[node]); outside=0.0 if p==-1 else float(merge_level[p]); formation=float(active_peak[node]) if node<L else float(merge_level[node]); lifetime=formation-outside; base.req(np.isfinite(lifetime) and lifetime>=-1e-12,f"bad lifetime {node}"); m=frozenset(tup)
        rows.append({"family_id":base.family_id("TLIN1",tup),"family_hash":structural.member_hash(m),"event_ids":list(tup),"member_count":len(tup),"node":node,"is_root":p==-1,"lineage_key":str(active_key[node]),"formation_level":formation,"outside_merge_level":outside,"level_lifetime":max(0.0,float(lifetime))})
    by={}
    for r in rows:by.setdefault(r["lineage_key"],[]).append(r)
    for vals in by.values():
        vals.sort(key=lambda r:(-r["level_lifetime"],r["family_hash"]));
        for k,r in enumerate(vals,1):r["lineage_round"]=k
    rows.sort(key=lambda r:(r["lineage_round"],-r["level_lifetime"],r["family_hash"]));
    for k,r in enumerate(rows,1):r["rank"]=k
    base.req(len(rows)==int(summary["candidate_count"]) and [r["rank"] for r in rows]==list(range(1,len(rows)+1)),"candidate/rank count")
    return rows,{"candidate_count":len(rows),"candidate_rows":summary["candidate_rows"],"lineage_count":len(by),"max_lineage_round":max((r["lineage_round"] for r in rows),default=0),"diagram_reconstruction_max_abs_error":float(np.max(np.abs(rr-ds))) if rr.size else 0.0}

def main()->int:
    ap=argparse.ArgumentParser()
    for n in ("support-cut-runner","structural-runner","structural-result-json","parent-runner","quality-source","support-source-parts","candidate-payload","baseline-payload","scorer-parts","v8-result-json"):ap.add_argument("--"+n,type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True); a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    base_mod=__import__('importlib.util').util.spec_from_file_location("lin_base",a.support_cut_runner); base=__import__('importlib.util').util.module_from_spec(base_mod); base_mod.loader.exec_module(base)
    base.req(base.sha256(a.quality_source)==QUALITY_SHA256 and base.sha256(a.v8_result_json)==V8_RESULT_SHA256 and base.sha256(a.structural_result_json)==STRUCTURAL_RESULT_SHA256,"frozen input hash")
    sr=json.loads(a.structural_result_json.read_text()); expected={(int(r["denominator"]),int(r["bucket"])):r for r in sr["fits"]}; structural=base.load_module(a.structural_runner,"lin_struct"); parent=base.load_module(a.parent_runner,"lin_parent")
    q=base.load_module(a.quality_source,"lin_gmn"); q.v1.mult.YEARS=YEARS; q.v1.mult.MONTH_KEYS=MONTH_KEYS; q.v1.mult.TOP_K=100; runtime=q.v1.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts); support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS="orbittrace-topomodal-lineage-balanced-v1-target-excluded"; support.RANKING_VARIANTS=("persistence",); base.req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,"firewall"); setattr(a,"fixed4_baseline_json",a.v8_result_json); _c,bsrc,_s=support.load_sources(a); scan,_cal,hidden_unused,sources=support.parse_catalogue(bsrc); del hidden_unused; base.req(sorted(scan)==list(YEARS),"years")
    events=[]
    for y in YEARS:events.extend(parent.normalize_event(r,y) for r in list(scan[y]))
    base.req(len(events)==738682 and all(not(BLIND[0]<=float(e["sol"])<=BLIND[1]) for e in events),"universe/firewall"); Xfull=parent.geo_matrix(events); yrs=np.asarray([int(e["year"]) for e in events],dtype=np.int64); ids=[str(e["id"]) for e in events]; hashes=np.asarray([base.event_hash_u64(x) for x in ids],dtype=np.uint64)
    subsets=[]
    for d in (128,1024):
      for b in BUCKETS:
        ii=base.selected_indices(hashes,d,b); sub=[events[int(i)] for i in ii]; sx=np.asarray(Xfull[ii]); sy=np.asarray(yrs[ii]); sid=[ids[int(i)] for i in ii]; print(f"[lineage-prelabel] d={d} b={b} n={len(sid)}",flush=True); succ,ss=lineage_ranked(base,structural,sub); par,ps=base.recurrent_ranked(parent,sx,sy,sid); ex=expected[(d,b)]; base.req(ss["candidate_rows"]==ex["topomodal"]["candidate_rows"] and len(succ)==int(ex["topomodal"]["candidate_count"]),"#1284 successor mismatch"); base.req(ps["candidate_rows"]==ex["recurrent_eom"]["candidate_rows"] and len(par)==int(ex["recurrent_eom"]["candidate_count"]),"parent mismatch"); base.req(len(succ)>=len(par),"successor shorter than parent"); subsets.append({"denominator":d,"bucket":b,"events_total":len(sid),"events_by_year":{str(y):int(np.sum(sy==y)) for y in YEARS},"event_universe_sha256":base.universe_hash(sid),"equal_budget_k":len(par),"lineage_summary":ss,"successor_candidates":succ,"recurrent_candidates":par})
    pre={"schema":"ORBITTRACE_TOPOMODAL_LINEAGE_BALANCED_V1_PRELABEL","scientific_role":"PRELABEL_TOPOMODAL_LINEAGE_BALANCED_V1","structural_source_run_id":31955621864,"structural_source_artifact_id":9265889512,"structural_result_sha256":STRUCTURAL_RESULT_SHA256,"configuration":{"candidate_universe":"complete_exact_1284_hierarchy","lineage":"surviving_active_mode_key","node_score":"density_level_lifetime","ranking":"lineage_round_asc_then_lifetime_desc_then_family_hash","equal_budget":"K_equals_recurrent_candidate_count"},"subsets":subsets,"blind_exclusion":list(BLIND),"target_information_access":False,"target_region_events_accessed":False,"shower_truth_used":False,"sonotaco_2013_2014_access":False,"asfn_event_level_access":False,"efn_event_level_access":False,"amos_scientific_access":False,"maarsy_scientific_access":False,"dms_scientific_access":False,"method_parameter_selection_from_result":False}
    out=a.output/"TOPOMODAL_LINEAGE_BALANCED_V1_PRELABEL.json"; out.write_text(json.dumps(pre,indent=2,sort_keys=True,allow_nan=False)+"\n"); print(json.dumps({"prelabel_sha256":base.sha256(out),"subsets":[{"d":x["denominator"],"b":x["bucket"],"candidates":len(x["successor_candidates"]),"lineages":x["lineage_summary"]["lineage_count"],"K":x["equal_budget_k"]} for x in subsets]},indent=2),flush=True); return 0
if __name__=="__main__":raise SystemExit(main())
