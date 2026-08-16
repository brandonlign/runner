#!/usr/bin/env python3
from __future__ import annotations

import argparse,hashlib,importlib.util,json
from pathlib import Path
from typing import Any
import numpy as np

YEARS=(2022,2023); MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13)); BLIND=(20.0,55.0); BUCKETS=(0,1,2,3)
QUALITY_SHA256="dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"; V8_RESULT_SHA256="fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"; STRUCTURAL_RESULT_SHA256="e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497"; INTRINSIC_SOURCE_BLOB="752df8212ce601227f6e9170b0fe994ba06b515d"

def req(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)
def sha256(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); req(spec is not None and spec.loader is not None,f"cannot import {path}"); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def compact(m:dict[str,Any])->dict[str,Any]:return {k:v for k,v in m.items() if k!="first_rank_by_label"}
def aggregate(panels:list[dict[str,Any]],which:str)->dict[str,Any]:
    vals=[p[which] for p in panels]
    return {"qualified_total":int(sum(int(v["qualified_matches"]) for v in vals)),"mrr_mean":float(np.mean([float(v["mrr"]) for v in vals])) if vals else 0.0,"precision_mean":float(np.mean([float(v["top100_dominant_precision"]) for v in vals])) if vals else 0.0,"fragmentation_mean":float(np.mean([float(v["fragmentation_median_top500"]) for v in vals])) if vals else 0.0,"recovered_at_25_total":int(sum(int(v["recovered_at_25"]) for v in vals)),"recovered_at_50_total":int(sum(int(v["recovered_at_50"]) for v in vals)),"recovered_at_100_total":int(sum(int(v["recovered_at_100"]) for v in vals)),"recovered_at_500_total":int(sum(int(v["recovered_at_500"]) for v in vals))}

def main()->int:
    ap=argparse.ArgumentParser()
    for name in ("intrinsic-runner","prelabel","parent-runner","quality-source","support-source-parts","candidate-payload","baseline-payload","scorer-parts","v8-result-json"):ap.add_argument("--"+name,type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True); a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    intrinsic=load_module(a.intrinsic_runner,"rdtm_eval_intrinsic"); req(sha256(a.quality_source)==QUALITY_SHA256 and sha256(a.v8_result_json)==V8_RESULT_SHA256,"frozen input")
    pre_sha=sha256(a.prelabel); pre=json.loads(a.prelabel.read_text()); req(pre["schema"]=="ORBITTRACE_RANKDENSITY_TOPOMODAL_V1_PRELABEL" and pre["scientific_role"]=="PRELABEL_RANKDENSITY_TOPOMODAL_V1","prelabel schema"); req(pre["structural_result_sha256"]==STRUCTURAL_RESULT_SHA256 and pre["intrinsic_source_blob"]==INTRINSIC_SOURCE_BLOB,"source pin")
    cfg=pre["configuration"]; req(cfg["density"]=="GEO6_third_nearest_other_empirical_rank_q" and cfg["graph"]=="exact_1284_physical_radius_1" and cfg["hierarchy"]=="complete_gudhi_3.12_manual_topomato" and int(cfg["min_candidate_support"])==4,"method changed"); req(pre["blind_exclusion"]==list(BLIND) and pre["shower_truth_used"] is False and pre["target_information_access"] is False and pre["target_region_events_accessed"] is False,"firewall")
    sg={str(k):bool(v) for k,v in pre["cross_scale"]["gates"].items()}; req(set(sg)=={"pooled_fine_to_coarse_mean_best_jaccard_strictly_greater","strict_bucket_wins_at_least_3_of_4"},"structural gates"); req(pre["candidate_budget_shortage_any_panel"] is False,"candidate budget shortage")
    frozen={(int(r["denominator"]),int(r["bucket"])):r for r in pre["subsets"]}; req(set(frozen)=={(d,b) for d in (128,1024) for b in BUCKETS},"panel set")
    for r in pre["subsets"]:
        succ,par=r["successor_candidates"],r["recurrent_candidates"]; req(bool(r["candidate_budget_sufficient"]) and len(succ)>=len(par)==int(r["equal_budget_k"]) and len(par)>0,"budget"); req([int(x["rank"]) for x in succ]==list(range(1,len(succ)+1)),"rank continuity")

    parent=load_module(a.parent_runner,"rdtm_eval_parent"); req(tuple(parent.YEARS)==YEARS and tuple(parent.BLIND)==BLIND and int(parent.MIN_CLUSTER_SIZE)==10 and int(parent.MIN_SAMPLES)==10,"parent")
    q=load_module(a.quality_source,"rdtm_eval_gmn"); q.v1.mult.YEARS=YEARS; q.v1.mult.MONTH_KEYS=MONTH_KEYS; q.v1.mult.TOP_K=100; runtime=q.v1.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts); support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS="orbittrace-rankdensity-topomodal-v1-evaluator"; support.RANKING_VARIANTS=("persistence",); req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,"firewall changed"); setattr(a,"fixed4_baseline_json",a.v8_result_json); _c,base,_s=support.load_sources(a); scan,_cal,hidden,sources=support.parse_catalogue(base); req(isinstance(hidden,dict) and sorted(scan)==list(YEARS) and [x["key"] for x in sources]==list(MONTH_KEYS),"truth source")
    events=[]
    for y in YEARS:events.extend(parent.normalize_event(row,y) for row in list(scan[y]))
    req(len(events)==738682 and all(not(BLIND[0]<=float(e["sol"])<=BLIND[1]) for e in events),"universe/firewall"); ids=[str(e["id"]) for e in events]; yrs=np.asarray([int(e["year"]) for e in events],dtype=np.int64); hashes=np.asarray([intrinsic.event_hash_u64(x) for x in ids],dtype=np.uint64)
    truth=[]
    for d in (128,1024):
        for b in BUCKETS:
            fr=frozen[(d,b)]; ii=intrinsic.selected_indices(hashes,d,b); sid=[ids[int(i)] for i in ii]; sy=np.asarray(yrs[ii]); req(len(sid)==int(fr["events_total"]) and hashlib.sha256("\n".join(sorted(sid)).encode()).hexdigest()==str(fr["event_universe_sha256"]),"event universe"); K=int(fr["equal_budget_k"]); succ=fr["successor_candidates"][:K]; par=fr["recurrent_candidates"]; req(len(succ)==len(par)==K,"budget")
            for y in YEARS:
                annual={sid[int(i)] for i in np.flatnonzero(sy==y)}; pm=compact(parent.metrics(par,hidden,annual)); sm=compact(parent.metrics(succ,hidden,annual)); truth.append({"denominator":d,"bucket":b,"year":y,"equal_budget_k":K,"parent":pm,"successor":sm,"qualified_nonlower":int(sm["qualified_matches"])>=int(pm["qualified_matches"]),"qualified_strict_win":int(sm["qualified_matches"])>int(pm["qualified_matches"])})
    scales={}
    for d in (128,1024):
        ps=[p for p in truth if p["denominator"]==d]; req(len(ps)==8,"panel count"); pa,sa=aggregate(ps,"parent"),aggregate(ps,"successor"); non=sum(bool(p["qualified_nonlower"]) for p in ps); win=sum(bool(p["qualified_strict_win"]) for p in ps); scales[str(d)]={"parent":pa,"successor":sa,"qualified_nonlower_panels":int(non),"qualified_strict_win_panels":int(win),"qualified_loss_panels":int(8-non)}
    fp,fs=scales["1024"]["parent"],scales["1024"]["successor"]; cp,cs=scales["128"]["parent"],scales["128"]["successor"]
    tg={"fine_qualified_total_strictly_greater":fs["qualified_total"]>fp["qualified_total"],"fine_qualified_nonlower_at_least_6_of_8":scales["1024"]["qualified_nonlower_panels"]>=6,"fine_mrr_mean_not_lower":fs["mrr_mean"]>=fp["mrr_mean"],"fine_precision_mean_not_lower":fs["precision_mean"]>=fp["precision_mean"],"fine_fragmentation_mean_not_higher":fs["fragmentation_mean"]<=fp["fragmentation_mean"],"coarse_qualified_total_not_lower":cs["qualified_total"]>=cp["qualified_total"],"coarse_qualified_nonlower_at_least_6_of_8":scales["128"]["qualified_nonlower_panels"]>=6,"coarse_mrr_mean_not_lower":cs["mrr_mean"]>=cp["mrr_mean"],"coarse_precision_mean_not_lower":cs["precision_mean"]>=cp["precision_mean"],"coarse_fragmentation_mean_not_higher":cs["fragmentation_mean"]<=cp["fragmentation_mean"]}
    gates={**{"structural_"+k:v for k,v in sg.items()},**tg}; verdict="PASS_RANKDENSITY_TOPOMODAL_V1" if all(gates.values()) else "FAIL_RANKDENSITY_TOPOMODAL_V1"
    out={"schema":"ORBITTRACE_RANKDENSITY_TOPOMODAL_V1","scientific_role":"TARGET_EXCLUDED_GMN_2022_2023_SPARSE_RECOVERY_AND_GENERALIZATION_DEVELOPMENT","verdict":verdict,"prelabel_sha256":pre_sha,"structural_source_run_id":31955621864,"structural_source_artifact_id":9265889512,"structural_result_sha256":STRUCTURAL_RESULT_SHA256,"intrinsic_source_blob":INTRINSIC_SOURCE_BLOB,"cross_scale":pre["cross_scale"],"panels":truth,"scale_aggregates":scales,"gates":gates,"blind_exclusion":list(BLIND),"target_information_access":False,"target_region_events_accessed":False,"sonotaco_2013_2014_access":False,"asfn_event_level_access":False,"efn_event_level_access":False,"amos_scientific_access":False,"maarsy_scientific_access":False,"dms_scientific_access":False,"method_parameter_selection_from_result":False}
    p=a.output/"RANKDENSITY_TOPOMODAL_V1.json"; p.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+"\n"); print(json.dumps({"verdict":verdict,"prelabel_sha256":pre_sha,"cross_scale":pre["cross_scale"],"scales":scales,"gates":gates},indent=2,sort_keys=True),flush=True); return 0

if __name__=="__main__":raise SystemExit(main())