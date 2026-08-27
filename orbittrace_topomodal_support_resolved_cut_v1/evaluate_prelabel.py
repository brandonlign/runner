#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,importlib.util,json
from pathlib import Path
from typing import Any
import numpy as np

YEARS=(2022,2023); MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13)); BLIND=(20.0,55.0)
QUALITY_SHA256="dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"; V8_RESULT_SHA256="fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"; STRUCTURAL_RESULT_SHA256="e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497"
SALT="ORBITTRACE_SCALE_STRESS_V1|"; BUCKETS=(0,1,2,3)
def req(x:bool,m:str)->None:
    if not x: raise RuntimeError(m)
def sha256(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load_module(p:Path,n:str)->Any:
    s=importlib.util.spec_from_file_location(n,p); req(s is not None and s.loader is not None,f"import {p}"); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def hu(e:str)->int:return int.from_bytes(hashlib.sha256((SALT+e).encode()).digest()[:8],"big")
def idx(h:np.ndarray,d:int,b:int)->np.ndarray:return np.flatnonzero((h%np.uint64(d))==np.uint64(b))
def uh(ids:list[str])->str:return hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()
def compact(m:dict[str,Any])->dict[str,Any]:return {k:v for k,v in m.items() if k!="first_rank_by_label"}
def agg(ps:list[dict[str,Any]],key:str)->dict[str,Any]:
    v=[p[key] for p in ps]; return {"qualified_total":sum(int(x["qualified_matches"]) for x in v),"mrr_mean":float(np.mean([float(x["mrr"]) for x in v])),"precision_mean":float(np.mean([float(x["top100_dominant_precision"]) for x in v])),"fragmentation_mean":float(np.mean([float(x["fragmentation_median_top500"]) for x in v])),"recovered_at_25_total":sum(int(x["recovered_at_25"]) for x in v),"recovered_at_50_total":sum(int(x["recovered_at_50"]) for x in v),"recovered_at_100_total":sum(int(x["recovered_at_100"]) for x in v),"recovered_at_500_total":sum(int(x["recovered_at_500"]) for x in v)}

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--prelabel",type=Path,required=True); ap.add_argument("--parent-runner",type=Path,required=True); ap.add_argument("--quality-source",type=Path,required=True); ap.add_argument("--support-source-parts",type=Path,required=True); ap.add_argument("--candidate-payload",type=Path,required=True); ap.add_argument("--baseline-payload",type=Path,required=True); ap.add_argument("--scorer-parts",type=Path,required=True); ap.add_argument("--v8-result-json",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(sha256(a.quality_source)==QUALITY_SHA256,"quality source changed"); req(sha256(a.v8_result_json)==V8_RESULT_SHA256,"v8 changed")
    pre_sha=sha256(a.prelabel); pre=json.loads(a.prelabel.read_text()); req(pre["schema"]=="ORBITTRACE_TOPOMODAL_SUPPORT_RESOLVED_CUT_V1_PRELABEL" and pre["scientific_role"]=="PRELABEL_TOPOMODAL_SUPPORT_RESOLVED_CUT_V1","wrong prelabel"); req(pre["structural_result_sha256"]==STRUCTURAL_RESULT_SHA256,"structural hash"); req(pre["configuration"]["cut_rule"]=="split_iff_both_immediate_children_support_ge_4_else_keep_parent" and pre["configuration"]["ranking"]=="modal_contrast_desc_then_family_hash_asc","method changed"); req(pre["blind_exclusion"]==list(BLIND) and pre["shower_truth_used"] is False,"prelabel firewall")
    sm={(int(r["denominator"]),int(r["bucket"])):r for r in pre["subsets"]}; req(set(sm)=={(d,b) for d in (128,1024) for b in BUCKETS},"panels")
    all_k=True
    for r in pre["subsets"]:
        s=r["successor_candidates"]; p=r["recurrent_candidates"]; K=min(len(s),len(p)); req(K==int(r["equal_budget_k"]),"K changed"); all_k&=K>=1; req([x["rank"] for x in s]==list(range(1,len(s)+1)),"rank continuity"); req([x["family_id"] for x in s]==[x["family_id"] for x in sorted(s,key=lambda x:(-float(x["modal_contrast"]),str(x["family_hash"])))],"rank order"); req(r["cut_summary"]["pairwise_disjoint"] is True and float(r["cut_summary"]["diagram_reconstruction_max_abs_error"])<=1e-12,"cut audit")
    parent=load_module(a.parent_runner,"cut_eval_parent"); q=load_module(a.quality_source,"cut_eval_gmn"); q.v1.mult.YEARS=YEARS; q.v1.mult.MONTH_KEYS=MONTH_KEYS; q.v1.mult.TOP_K=100; runtime=q.v1.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts); support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS="orbittrace-topomodal-support-resolved-cut-v1-evaluator"; support.RANKING_VARIANTS=("persistence",); req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,"firewall changed"); setattr(a,"fixed4_baseline_json",a.v8_result_json); _c,base,_s=support.load_sources(a); scan,_cal,hidden,sources=support.parse_catalogue(base); req(isinstance(hidden,dict) and sorted(scan)==list(YEARS) and [x["key"] for x in sources]==list(MONTH_KEYS),"truth/source set")
    events=[]
    for y in YEARS:events.extend(parent.normalize_event(r,y) for r in list(scan[y]))
    req(len(events)==738682 and all(not(BLIND[0]<=float(e["sol"])<=BLIND[1]) for e in events),"event universe/firewall"); ids=[str(e["id"]) for e in events]; yrs=np.asarray([int(e["year"]) for e in events],dtype=np.int64); hashes=np.asarray([hu(x) for x in ids],dtype=np.uint64)
    panels=[]
    for d in (128,1024):
        for b in BUCKETS:
            fr=sm[(d,b)]; ii=idx(hashes,d,b); sid=[ids[int(i)] for i in ii]; sy=np.asarray(yrs[ii],dtype=np.int64); req(len(sid)==int(fr["events_total"]) and uh(sid)==fr["event_universe_sha256"],f"universe d{d}b{b}"); K=int(fr["equal_budget_k"])
            if K<1:continue
            succ=fr["successor_candidates"][:K]; par=fr["recurrent_candidates"][:K]
            for y in YEARS:
                annual={sid[int(i)] for i in np.flatnonzero(sy==y)}; pm=compact(parent.metrics(par,hidden,annual)); smet=compact(parent.metrics(succ,hidden,annual)); panels.append({"denominator":d,"bucket":b,"year":y,"equal_budget_k":K,"parent_equal_budget":pm,"successor_equal_budget":smet,"qualified_nonlower":int(smet["qualified_matches"])>=int(pm["qualified_matches"]),"qualified_strict_win":int(smet["qualified_matches"])>int(pm["qualified_matches"])})
    scales={}
    for d in (128,1024):
        ps=[p for p in panels if p["denominator"]==d]
        if len(ps)!=8:scales[str(d)]={"panel_count":len(ps),"all_k_positive":False};continue
        pa,sa=agg(ps,"parent_equal_budget"),agg(ps,"successor_equal_budget"); non=sum(p["qualified_nonlower"] for p in ps); win=sum(p["qualified_strict_win"] for p in ps); scales[str(d)]={"panel_count":8,"all_k_positive":True,"parent_equal_budget":pa,"successor_equal_budget":sa,"qualified_nonlower_panels":non,"qualified_strict_win_panels":win,"qualified_loss_panels":8-non}
    if all_k and all(scales[str(d)].get("panel_count")==8 for d in (128,1024)):
        fp,fs=scales["1024"]["parent_equal_budget"],scales["1024"]["successor_equal_budget"]; cp,cs=scales["128"]["parent_equal_budget"],scales["128"]["successor_equal_budget"]
        gates={"fine_qualified_total_strictly_greater":fs["qualified_total"]>fp["qualified_total"],"fine_qualified_nonlower_at_least_6_of_8":scales["1024"]["qualified_nonlower_panels"]>=6,"fine_mrr_mean_not_lower":fs["mrr_mean"]>=fp["mrr_mean"],"fine_precision_mean_not_lower":fs["precision_mean"]>=fp["precision_mean"],"fine_fragmentation_mean_not_higher":fs["fragmentation_mean"]<=fp["fragmentation_mean"],"coarse_qualified_total_not_lower":cs["qualified_total"]>=cp["qualified_total"],"coarse_qualified_nonlower_at_least_6_of_8":scales["128"]["qualified_nonlower_panels"]>=6,"coarse_mrr_mean_not_lower":cs["mrr_mean"]>=cp["mrr_mean"],"coarse_precision_mean_not_lower":cs["precision_mean"]>=cp["precision_mean"],"coarse_fragmentation_mean_not_higher":cs["fragmentation_mean"]<=cp["fragmentation_mean"]}
    else:gates={k:False for k in ("fine_qualified_total_strictly_greater","fine_qualified_nonlower_at_least_6_of_8","fine_mrr_mean_not_lower","fine_precision_mean_not_lower","fine_fragmentation_mean_not_higher","coarse_qualified_total_not_lower","coarse_qualified_nonlower_at_least_6_of_8","coarse_mrr_mean_not_lower","coarse_precision_mean_not_lower","coarse_fragmentation_mean_not_higher")}
    verdict="PASS_TOPOMODAL_SUPPORT_RESOLVED_CUT_V1" if all_k and all(gates.values()) else "FAIL_TOPOMODAL_SUPPORT_RESOLVED_CUT_V1"
    out={"schema":"ORBITTRACE_TOPOMODAL_SUPPORT_RESOLVED_CUT_V1","scientific_role":"TARGET_EXCLUDED_GMN_2022_2023_SPARSE_RECOVERY_DEVELOPMENT","verdict":verdict,"prelabel_sha256":pre_sha,"all_subsets_have_positive_equal_budget":bool(all_k),"structural_source_run_id":31955621864,"structural_source_artifact_id":9265889512,"structural_result_sha256":STRUCTURAL_RESULT_SHA256,"panels":panels,"scale_aggregates":scales,"gates":gates,"blind_exclusion":list(BLIND),"target_information_access":False,"target_region_events_accessed":False,"sonotaco_2013_2014_access":False,"asfn_event_level_access":False,"efn_event_level_access":False,"amos_scientific_access":False,"maarsy_scientific_access":False,"dms_scientific_access":False,"method_parameter_selection_from_result":False}
    p=a.output/"TOPOMODAL_SUPPORT_RESOLVED_CUT_V1.json"; p.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+"\n"); print(json.dumps({"verdict":verdict,"prelabel_sha256":pre_sha,"all_k_positive":all_k,"scales":scales,"gates":gates},indent=2,sort_keys=True),flush=True); return 0
if __name__=="__main__":raise SystemExit(main())
