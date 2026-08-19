#!/usr/bin/env python3
from __future__ import annotations

import argparse,hashlib,importlib.util,json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any
import numpy as np
from scipy.optimize import linear_sum_assignment

YEARS=(2022,2023); MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13)); BLIND=(20.0,55.0); DENOMS=(128,1024); BUCKETS=(0,1,2,3)
INTERNAL_BASELINE_SHA="7b1ddfcd32cd0b52321e3b3dfc614a88dd9b973f947c1d4d0de74fddf26b59cd"; QUALITY_SHA="dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"; V8_SHA="fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
CAPACITY="PR1377_EXACT: k=len(published comparator clusters); method=method_candidates[:k]; shortfall allowed and scored; never padded"

def req(x:bool,m:str)->None:
    if not x:raise RuntimeError(m)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path,n:str)->Any:
    s=importlib.util.spec_from_file_location(n,p); req(s is not None and s.loader is not None,f"cannot import {p}"); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def evaluate(cands:list[dict[str,Any]],hidden:dict[str,str],annual:set[str])->dict[str,Any]:
    cnt=Counter(v for k,v in hidden.items() if k in annual and v!="SPORADIC"); labels=sorted(k for k,n in cnt.items() if n>=4); L,C=len(labels),len(cands)
    if L==0:return {"eligible_showers":0,"candidate_count":C,"macro_f1":0.0,"macro_precision":0.0,"macro_recall":0.0,"recovered_f1_gt_05":0,"recovered_f1_gt_08":0}
    f=np.zeros((L,C)); p=np.zeros_like(f); r=np.zeros_like(f); li={lab:i for i,lab in enumerate(labels)}
    for j,c in enumerate(cands):
        ids=[str(x) for x in c["event_ids"] if str(x) in annual]; n=len(ids)
        if not n:continue
        cc=Counter(hidden.get(e,"SPORADIC") for e in ids)
        for lab,ov in cc.items():
            if lab not in li:continue
            i=li[lab]; pp=ov/n; rr=ov/cnt[lab]; ff=2*pp*rr/(pp+rr) if pp+rr else 0.0; f[i,j]=ff; p[i,j]=pp; r[i,j]=rr
    if C:ri,cj=linear_sum_assignment(f,maximize=True)
    else:ri,cj=np.asarray([],int),np.asarray([],int)
    af=np.zeros(L); ap=np.zeros(L); ar=np.zeros(L)
    for i,j in zip(ri,cj):af[i]=f[i,j]; ap[i]=p[i,j]; ar[i]=r[i,j]
    return {"eligible_showers":L,"candidate_count":C,"macro_f1":float(np.mean(af)),"macro_precision":float(np.mean(ap)),"macro_recall":float(np.mean(ar)),"recovered_f1_gt_05":int(np.sum(af>0.5)),"recovered_f1_gt_08":int(np.sum(af>0.8))}
def agg(rows:list[dict[str,Any]],side:str)->dict[str,Any]:
    v=[x[side] for x in rows]; return {"panels":len(v),"mean_macro_f1":mean(float(x["macro_f1"]) for x in v),"mean_macro_precision":mean(float(x["macro_precision"]) for x in v),"mean_macro_recall":mean(float(x["macro_recall"]) for x in v),"total_recovered_f1_gt_05":sum(int(x["recovered_f1_gt_05"]) for x in v),"total_recovered_f1_gt_08":sum(int(x["recovered_f1_gt_08"]) for x in v)}

def main()->int:
    ap=argparse.ArgumentParser()
    for n in ("rbt-pretruth","literature-pretruth","quality-source","support-source-parts","candidate-payload","baseline-payload","scorer-parts","v8-result-json","output"):ap.add_argument("--"+n,type=Path,required=True)
    ap.add_argument("--expected-pretruth-sha",required=True); a=ap.parse_args(); a.output.parent.mkdir(parents=True,exist_ok=True)
    req(sha(a.rbt_pretruth)==a.expected_pretruth_sha,"sealed RBT pretruth changed"); req(sha(a.quality_source)==QUALITY_SHA and sha(a.v8_result_json)==V8_SHA,"runtime input changed")
    pre=json.loads(a.rbt_pretruth.read_text()); lit=json.loads(a.literature_pretruth.read_text())
    req(pre["scientific_role"]=="TARGET_EXCLUDED_GMN_RBT_V1_RANKING_FROZEN_BEFORE_SHOWER_TRUTH" and pre["structural_pass"] is True,"RBT structural gate not passed")
    req(pre["configuration"]["density"]=="min(d22/n22,d23/n23)" and pre["configuration"]["new_tuned_parameters"]==[],"RBT method changed")
    req(pre["shower_truth_used"] is False and pre["target_information_access"] is False and pre["target_region_events_accessed"] is False and pre["orbittrace_reveal_access"] is False and pre["sonotaco_scientific_access"] is False,"RBT firewall")
    req(lit["scientific_role"]=="TARGET_EXCLUDED_GMN_SPARSE_LITERATURE_COMPARATORS_FROZEN_BEFORE_TRUTH" and lit["internal_prelabel_sha256"]==INTERNAL_BASELINE_SHA,"literature pretruth changed")
    sm={(int(s["denominator"]),int(s["bucket"])):s for s in pre["subsets"]}; req(set(sm)=={(d,b) for d in DENOMS for b in BUCKETS},"panel set")
    q=load(a.quality_source,"rbt_truth_q"); q.v1.mult.YEARS=YEARS; q.v1.mult.MONTH_KEYS=MONTH_KEYS; q.v1.mult.TOP_K=100; rt=q.v1.mult.load_frozen_runtime(); support=rt.load_support_module(a.support_source_parts); support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS="orbittrace-rbt-v1-gmn-truth"; support.RANKING_VARIANTS=("persistence",); req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,"blind changed"); setattr(a,"fixed4_baseline_json",a.v8_result_json); _c,base,_s=support.load_sources(a); scan,_cal,hidden,sources=support.parse_catalogue(base); req(isinstance(hidden,dict),"truth missing"); req(sorted(scan)==list(YEARS) and [x["key"] for x in sources]==list(MONTH_KEYS),"source set")
    allids=set()
    for s in sm.values():
        for y in YEARS:allids.update(str(x) for x in s["annual_event_ids"][str(y)])
    req(all(e in hidden for e in allids),"panel event missing truth")
    comps=[]
    for d in DENOMS:
      for b in BUCKETS:
        s=sm[(d,b)]; rbt=list(s["rbt_candidates"]); baseline=list(s["support_pruned_baseline_candidates"])
        for y in YEARS:
          annual=set(str(x) for x in s["annual_event_ids"][str(y)]); pp=lit["panels"][f"d{d}_b{b}_y{y}"]; req(int(pp["event_count"])==len(annual),"annual universe drift")
          for comp in ("sugar2017","hdbscan2025"):
            literature=list(pp[comp]["clusters"]); k=len(literature); rc=rbt[:k]; bc=baseline[:k]
            comps.append({"denominator":d,"bucket":b,"year":y,"comparator":comp,"comparator_capacity_k":k,"rbt_available_candidates":len(rbt),"support_pruned_available_candidates":len(baseline),"rbt_capacity_shortfall":max(0,k-len(rbt)),"support_pruned_capacity_shortfall":max(0,k-len(baseline)),"rbt":evaluate(rc,hidden,annual),"support_pruned":evaluate(bc,hidden,annual),"literature":evaluate(literature,hidden,annual)})
    req(len(comps)==32,"comparison count")
    routes={}
    for comp in ("sugar2017","hdbscan2025"):
        rows=[r for r in comps if r["comparator"]==comp]; routes[comp]={"rbt":agg(rows,"rbt"),"support_pruned":agg(rows,"support_pruned"),"literature":agg(rows,"literature")}
    scales={}
    for d in DENOMS:
        rows=[r for r in comps if r["denominator"]==d]; scales[str(d)]={"rbt":agg(rows,"rbt"),"support_pruned":agg(rows,"support_pruned")}
    g={"sugar_f1_not_lower":routes["sugar2017"]["rbt"]["mean_macro_f1"]>=routes["sugar2017"]["support_pruned"]["mean_macro_f1"],"sugar_recovery_not_lower":routes["sugar2017"]["rbt"]["total_recovered_f1_gt_05"]>=routes["sugar2017"]["support_pruned"]["total_recovered_f1_gt_05"],"hdb_f1_not_lower":routes["hdbscan2025"]["rbt"]["mean_macro_f1"]>=routes["hdbscan2025"]["support_pruned"]["mean_macro_f1"],"hdb_recovery_not_lower":routes["hdbscan2025"]["rbt"]["total_recovered_f1_gt_05"]>=routes["hdbscan2025"]["support_pruned"]["total_recovered_f1_gt_05"],"coarse_f1_not_lower":scales["128"]["rbt"]["mean_macro_f1"]>=scales["128"]["support_pruned"]["mean_macro_f1"],"coarse_recovery_not_lower":scales["128"]["rbt"]["total_recovered_f1_gt_05"]>=scales["128"]["support_pruned"]["total_recovered_f1_gt_05"],"fine_f1_not_lower":scales["1024"]["rbt"]["mean_macro_f1"]>=scales["1024"]["support_pruned"]["mean_macro_f1"],"fine_recovery_not_lower":scales["1024"]["rbt"]["total_recovered_f1_gt_05"]>=scales["1024"]["support_pruned"]["total_recovered_f1_gt_05"],"still_beats_sugar_published":routes["sugar2017"]["rbt"]["mean_macro_f1"]>routes["sugar2017"]["literature"]["mean_macro_f1"] and routes["sugar2017"]["rbt"]["total_recovered_f1_gt_05"]>=routes["sugar2017"]["literature"]["total_recovered_f1_gt_05"],"still_beats_hdb_published":routes["hdbscan2025"]["rbt"]["mean_macro_f1"]>routes["hdbscan2025"]["literature"]["mean_macro_f1"] and routes["hdbscan2025"]["rbt"]["total_recovered_f1_gt_05"]>=routes["hdbscan2025"]["literature"]["total_recovered_f1_gt_05"]}
    verdict="PASS_RECURRENCE_BOTTLENECK_TOPOMODAL_V1_GMN_DEVELOPMENT" if all(g.values()) else "FAIL_RECURRENCE_BOTTLENECK_TOPOMODAL_V1_GMN_DEVELOPMENT"
    out={"schema":"ORBITTRACE_RECURRENCE_BOTTLENECK_TOPOMODAL_V1_GMN_RESULT","scientific_role":"TARGET_EXCLUDED_GMN_RBT_V1_BINDING_DEVELOPMENT","verdict":verdict,"rbt_pretruth_sha256":sha(a.rbt_pretruth),"literature_pretruth_sha256":sha(a.literature_pretruth),"capacity_semantics":CAPACITY,"routes":routes,"scales":scales,"size_summary":pre["size_summary"],"structural_gates":pre["structural_gates"],"gates":g,"comparisons":comps,"method_changed_after_pretruth":False,"target_information_access":False,"target_region_events_accessed":False,"orbittrace_reveal_access":False,"sonotaco_scientific_access":False,"post_result_parameter_search":False,"interpretation_boundary":"Target-excluded GMN 2022/2023 is development-exposed. PASS authorizes frozen transfer only; it does not establish tuned-HDBSCAN-family superiority or untouched external validation."}
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+"\n"); print(json.dumps({"verdict":verdict,"routes":routes,"scales":scales,"gates":g,"result_sha256":sha(a.output)},indent=2,sort_keys=True),flush=True); return 0
if __name__=="__main__":raise SystemExit(main())
