#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

YEARS=(2022,2023)
MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13))
BLIND=(20.0,55.0)
BUCKETS=(0,1,2,3)
QUALITY_SHA256="dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256="fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"


def req(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)

def sha256(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()

def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path);req(spec is not None and spec.loader is not None,f"cannot import {path}");m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def score(families:list[dict[str,Any]],truth:dict[str,str],budget:int)->dict[str,Any]:
    counts=Counter(v for v in truth.values() if v!="SPORADIC")
    labels=sorted(k for k,n in counts.items() if n>=4)
    ids=set(truth)
    active=[]
    for i,f in enumerate(families):
        mem=set(map(str,f["event_ids"])) & ids
        if mem: active.append((int(f.get("rank",i+1)),str(f.get("family_id",f.get("family_hash",i))),mem))
    active.sort(key=lambda z:(z[0],z[1]));active=active[:budget]
    truth_sets={lab:{eid for eid,v in truth.items() if v==lab} for lab in labels}
    mat=np.zeros((len(labels),len(active)),dtype=float)
    for i,lab in enumerate(labels):
        a=truth_sets[lab]
        for j,(_,_,p) in enumerate(active):
            ov=len(a&p)
            if ov:
                pr=ov/len(p); re=ov/len(a); mat[i,j]=2*pr*re/(pr+re)
    n=max(len(labels),len(active))
    if n==0:return {"eligible_showers":0,"macro_f1":0.0,"recovered_f1_gt_0_5":0,"candidate_used":0}
    cost=np.zeros((n,n),dtype=float);cost[:len(labels),:len(active)]=-mat
    ri,cj=linear_sum_assignment(cost)
    vals=[float(mat[i,j]) if j<len(active) else 0.0 for i,j in zip(ri.tolist(),cj.tolist()) if i<len(labels)]
    return {"eligible_showers":len(labels),"macro_f1":float(np.mean(vals)) if vals else 0.0,"recovered_f1_gt_0_5":int(sum(v>0.5 for v in vals)),"candidate_used":len(active)}

def main()->int:
    ap=argparse.ArgumentParser()
    for name in ("intrinsic-runner","prelabel","parent-runner","quality-source","support-source-parts","candidate-payload","baseline-payload","scorer-parts","v8-result-json"):ap.add_argument("--"+name,type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)

    pre=json.loads(a.prelabel.read_text());pre_sha=sha256(a.prelabel)
    req(pre["schema"]=="ORBITTRACE_SIGNIFICANCE_WITNESS_MACROF1_V1_PRELABEL","prelabel schema")
    req(pre["shower_truth_used"] is False and pre["target_information_access"] is False and pre["target_region_events_accessed"] is False,"prelabel firewall")
    req(pre["candidate_budget_sufficient_all_panels"] is True and pre["pairwise_disjoint_all_panels"] is True and pre["mechanism_active_any_panel"] is True,"prelabel gates")
    frozen={(int(r["denominator"]),int(r["bucket"])):r for r in pre["subsets"]};req(set(frozen)=={(d,b) for d in (128,1024) for b in BUCKETS},"panel set")

    intrinsic=load_module(a.intrinsic_runner,"swmf1_intrinsic")
    parent=load_module(a.parent_runner,"swmf1_parent")
    req(tuple(parent.YEARS)==YEARS and tuple(parent.BLIND)==BLIND and int(parent.MIN_CLUSTER_SIZE)==10 and int(parent.MIN_SAMPLES)==10,"parent constants")
    req(sha256(a.quality_source)==QUALITY_SHA256 and sha256(a.v8_result_json)==V8_RESULT_SHA256,"frozen runtime input")
    q=load_module(a.quality_source,"swmf1_gmn");q.v1.mult.YEARS=YEARS;q.v1.mult.MONTH_KEYS=MONTH_KEYS;q.v1.mult.TOP_K=100
    runtime=q.v1.mult.load_frozen_runtime();support=runtime.load_support_module(a.support_source_parts);support.YEARS=YEARS;support.MONTH_KEYS=MONTH_KEYS;support.CORPUS="orbittrace-significance-witness-macrof1-v1-evaluator";support.RANKING_VARIANTS=("persistence",);req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,"firewall changed");setattr(a,"fixed4_baseline_json",a.v8_result_json);_c,base,_s=support.load_sources(a);scan,_cal,hidden,sources=support.parse_catalogue(base)
    req(isinstance(hidden,dict) and sorted(scan)==list(YEARS) and [x["key"] for x in sources]==list(MONTH_KEYS),"truth source")
    events=[]
    for y in YEARS:events.extend(parent.normalize_event(row,y) for row in list(scan[y]))
    req(len(events)==738682 and all(not(BLIND[0]<=float(e["sol"])<=BLIND[1]) for e in events),"universe/firewall")
    ids=np.asarray([str(e["id"]) for e in events],dtype=object);yrs=np.asarray([int(e["year"]) for e in events],dtype=np.int64);hashes=np.asarray([intrinsic.event_hash_u64(str(x)) for x in ids],dtype=np.uint64)

    panels=[]
    for d in (128,1024):
        for b in BUCKETS:
            fr=frozen[(d,b)];ii=intrinsic.selected_indices(hashes,d,b);sid=[str(ids[int(i)]) for i in ii];sy=np.asarray(yrs[ii]);req(len(sid)==int(fr["events_total"]),"subset event count");req(hashlib.sha256("\n".join(sorted(sid)).encode()).hexdigest()==str(fr["event_universe_sha256"]),"event universe hash")
            K=int(fr["equal_budget_k"]);rec=list(fr["recurrent_candidates"]);succ=list(fr["successor_candidates"]);req(len(rec)==K and len(succ)>=K,"candidate budget")
            for y in YEARS:
                annual={sid[int(i)] for i in np.flatnonzero(sy==y)}
                truth={eid:str(hidden[eid]) for eid in annual}
                pm=score(rec,truth,K);sm=score(succ,truth,K)
                panels.append({"denominator":d,"bucket":b,"year":y,"equal_budget_k":K,"parent":pm,"successor":sm,"macro_nonregression":float(sm["macro_f1"])>=float(pm["macro_f1"]),"macro_strict_win":float(sm["macro_f1"])>float(pm["macro_f1"]),"recovery_nonregression":int(sm["recovered_f1_gt_0_5"])>=int(pm["recovered_f1_gt_0_5"])})

    scales={}
    for d in (128,1024):
        ps=[p for p in panels if p["denominator"]==d];req(len(ps)==8,"scale panel count")
        pmean=float(np.mean([p["parent"]["macro_f1"] for p in ps]));smean=float(np.mean([p["successor"]["macro_f1"] for p in ps]));prec=sum(int(p["parent"]["recovered_f1_gt_0_5"]) for p in ps);srec=sum(int(p["successor"]["recovered_f1_gt_0_5"]) for p in ps);non=sum(bool(p["macro_nonregression"]) for p in ps)
        scales[str(d)]={"parent_mean_macro_f1":pmean,"successor_mean_macro_f1":smean,"macro_f1_delta":smean-pmean,"parent_recovered_total":prec,"successor_recovered_total":srec,"recovered_delta":srec-prec,"macro_nonregression_panels":non,"macro_strict_win_panels":sum(bool(p["macro_strict_win"]) for p in ps)}
    fine=scales["1024"];coarse=scales["128"]
    gates={
        "fine_mean_macro_f1_nonlower":fine["successor_mean_macro_f1"]>=fine["parent_mean_macro_f1"],
        "fine_recovered_total_nonlower":fine["successor_recovered_total"]>=fine["parent_recovered_total"],
        "fine_macro_nonregression_at_least_6_of_8":fine["macro_nonregression_panels"]>=6,
        "coarse_mean_macro_f1_nonlower":coarse["successor_mean_macro_f1"]>=coarse["parent_mean_macro_f1"],
        "coarse_recovered_total_nonlower":coarse["successor_recovered_total"]>=coarse["parent_recovered_total"],
        "coarse_macro_nonregression_at_least_6_of_8":coarse["macro_nonregression_panels"]>=6,
        "strict_mean_macro_f1_improvement_some_scale":fine["successor_mean_macro_f1"]>fine["parent_mean_macro_f1"] or coarse["successor_mean_macro_f1"]>coarse["parent_mean_macro_f1"],
        "candidate_budget_sufficient_all_panels":pre["candidate_budget_sufficient_all_panels"] is True,
        "pairwise_disjoint_all_panels":pre["pairwise_disjoint_all_panels"] is True,
        "mechanism_active_any_panel":pre["mechanism_active_any_panel"] is True,
    }
    verdict="PASS_SIGNIFICANCE_WITNESS_MACROF1_V1_GMN" if all(gates.values()) else "FAIL_SIGNIFICANCE_WITNESS_MACROF1_V1_GMN"
    result={"schema":"ORBITTRACE_SIGNIFICANCE_WITNESS_MACROF1_V1_GMN","scientific_role":"PAPER_ALIGNED_HUNGARIAN_MACRO_F1_TARGET_EXCLUDED_GMN_SPARSE_DEVELOPMENT","verdict":verdict,"prelabel_sha256":pre_sha,"panels":panels,"scales":scales,"gates":gates,"blind_exclusion":list(BLIND),"target_information_access":False,"target_region_events_accessed":False,"sonotaco_2013_2014_access":False,"asfn_event_level_access":False,"efn_event_level_access":False,"amos_scientific_access":False,"maarsy_scientific_access":False,"dms_scientific_access":False,"post_result_method_change_authorized":False}
    path=a.output/"RESULT.json";path.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n");print(json.dumps({"verdict":verdict,"scales":scales,"gates":gates},indent=2,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
