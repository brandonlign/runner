#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np

YEARS=(2022,2023); BLIND=(20.0,55.0); DENOMS=(128,1024); BUCKETS=(0,1,2,3)
SUPPORT_SHA="57a6fd0fa680fb56b3d6a8a984682213e0235baadf14b27f241927b2dbb4b50f"
BIF_SHA="95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c"
QUALITY_SHA="dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_SHA="fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
UNIVERSE_BLOB="4988997c023d9df2b504372b4290dcab379a6dcc"


def req(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path,n:str)->Any:
    s=importlib.util.spec_from_file_location(n,p); req(s is not None and s.loader is not None,f"cannot import {p}"); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def members(r:dict[str,Any])->frozenset[str]:return frozenset(str(x) for x in r["event_ids"])
def m2d(r:dict[str,Any],bif:list[dict[str,Any]])->tuple[float,int,float]:
    s=members(r); req(len(s)==int(r["member_count"]) and len(s)>=4,"bad candidate")
    score=0.0; raw=0.0; count=0
    for b in bif:
        bs=members(b)
        if bs.issubset(s):
            area=float(b["persistence_area"]); req(area>0 and np.isfinite(area),"bad bif area")
            score+=(len(bs)/len(s))*area; raw+=area; count+=1
    return float(score),int(count),float(raw)
def burden(v:list[int])->float:req(bool(v) and all(x>0 for x in v),"bad sizes"); return float(sum(x*x for x in v)/sum(v))
def q90(v:list[int])->float:req(bool(v),"empty sizes"); return float(np.quantile(np.asarray(v,float),0.90))


def main()->int:
    ap=argparse.ArgumentParser()
    for n in ("rbt-source","structural-source","parent-runner","quality-source","support-source-parts","candidate-payload","baseline-payload","scorer-parts","v8-result-json","support-pruned-pretruth","bif-prelabel"):
        ap.add_argument("--"+n,type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True); a=ap.parse_args(); a.output.parent.mkdir(parents=True,exist_ok=True)
    req(sha(a.quality_source)==QUALITY_SHA and sha(a.v8_result_json)==V8_SHA,"runtime input changed")
    req(sha(a.support_pruned_pretruth)==SUPPORT_SHA and sha(a.bif_prelabel)==BIF_SHA,"frozen prelabel changed")
    frozen=a.rbt_source.parent.parent/"orbittrace_topomodal_support_resolved_cut_v1"/"generate_prelabel.py"
    fb=frozen.read_bytes(); blob=hashlib.sha1(b"blob "+str(len(fb)).encode()+b"\0"+fb).hexdigest(); req(blob==UNIVERSE_BLOB,"sparse universe source changed")
    univ=load(frozen,"rbt_frozen_universe"); rbt=load(a.rbt_source,"rbt_cut"); structural=load(a.structural_source,"rbt_structural"); parent=load(a.parent_runner,"rbt_parent")
    req(univ.SALT=="ORBITTRACE_SCALE_STRESS_V1|" and int(univ.COARSE_D)==128 and int(univ.FINE_D)==1024 and tuple(univ.BUCKETS)==BUCKETS,"sparse panel rule changed")
    req(float(rbt.RADIUS)==float(structural.RADIUS)==1.0 and int(rbt.MIN_SUPPORT)==int(structural.MIN_SUPPORT)==4,"geometry/support changed")
    req(tuple(structural.BLIND)==BLIND and tuple(parent.BLIND)==BLIND,"blind changed")
    base=json.loads(a.support_pruned_pretruth.read_text()); bif=json.loads(a.bif_prelabel.read_text())
    req(base["scientific_role"]=="TARGET_EXCLUDED_GMN_SUPPORT_PRUNED_M2D_RANKING_FROZEN_BEFORE_TRUTH" and base["shower_truth_used"] is False and base["orbittrace_reveal_access"] is False,"baseline firewall")
    req(bif["scientific_role"]=="PRELABEL_TARGET_EXCLUDED_GMN_RANKING_RECOVERY" and bif["shower_truth_used"] is False and bif["target_information_access"] is False and bif["target_region_events_accessed"] is False,"bif firewall")
    bm={(int(s["denominator"]),int(s["bucket"])):s for s in base["subsets"]}; fm={(int(s["denominator"]),int(s["bucket"])):s for s in bif["subsets"]}; keys={(d,b) for d in DENOMS for b in BUCKETS}; req(set(bm)==set(fm)==keys,"panel set")

    q=load(a.quality_source,"rbt_loader"); q.v1.mult.YEARS=YEARS; q.v1.mult.MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13)); q.v1.mult.TOP_K=100; rt=q.v1.mult.load_frozen_runtime(); support=rt.load_support_module(a.support_source_parts); support.YEARS=YEARS; support.MONTH_KEYS=q.v1.mult.MONTH_KEYS; support.CORPUS="orbittrace-rbt-v1-target-excluded"; support.RANKING_VARIANTS=("persistence",); req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,"loader blind"); setattr(a,"fixed4_baseline_json",a.v8_result_json); _c,raw,_s=support.load_sources(a); scan,_cal,hidden_unused,sources=support.parse_catalogue(raw); del hidden_unused; req(sorted(scan)==list(YEARS) and [x["key"] for x in sources]==list(q.v1.mult.MONTH_KEYS),"source set")
    events=[]
    for y in YEARS: events.extend(parent.normalize_event(row,y) for row in list(scan[y]))
    req(len(events)==738682 and len({str(e["id"]) for e in events})==738682,"event universe"); req(all(not(BLIND[0]<=float(e["sol"])<=BLIND[1]) for e in events),"protected event survived")
    ids=[str(e["id"]) for e in events]; hashes=np.asarray([univ.event_hash_u64(x) for x in ids],dtype=np.uint64)

    subsets=[]; rbt_sizes=[]; base_sizes=[]; changed_panels=0
    for d in DENOMS:
      for b in BUCKETS:
        bs,fs=bm[(d,b)],fm[(d,b)]; ix=univ.selected_indices(hashes,d,b); sub=[events[int(i)] for i in ix]; subids=[ids[int(i)] for i in ix]
        frozen_annual={str(y):[str(x) for x in bs["annual_event_ids"][str(y)]] for y in YEARS}; frozen_ids=set(frozen_annual["2022"]).union(frozen_annual["2023"])
        req(set(subids)==frozen_ids and len(subids)==int(bs["event_count"])==int(fs["event_count"]),f"universe mismatch d{d}b{b}")
        req({str(y):list(map(str,fs["annual_event_ids"][str(y)])) for y in YEARS}==frozen_annual,"bif annual universe mismatch")
        print(f"[rbt-pretruth] d={d} b={b} n={len(subids)}",flush=True)
        rows,summary=rbt.recurrence_bottleneck_cut(structural,sub); bifrows=list(fs["bifiltration_candidates"])
        enriched=[]
        for row in rows:
            sc,cnt,rawarea=m2d(row,bifrows); out=dict(row); out["internal_2d_mass"]=sc; out["internal_bif_component_count"]=cnt; out["internal_bif_raw_area_sum"]=rawarea; enriched.append(out)
        enriched.sort(key=lambda r:(-float(r["internal_2d_mass"]),-float(r["modal_contrast"]),str(r["family_hash"])))
        for rank,row in enumerate(enriched,1):row["internal_mass_rank"]=rank; row["rank"]=rank
        baseline=list(bs["refined_candidates"]); k=int(bs["equal_budget_k"]); req(k>0,"bad budget")
        if {tuple(sorted(r["event_ids"])) for r in enriched}!={tuple(sorted(r["event_ids"])) for r in baseline}:changed_panels+=1
        rs=[int(r["member_count"]) for r in enriched[:k]]; ps=[int(r["member_count"]) for r in baseline[:k]]; req(rs and ps,"empty top budget"); rbt_sizes.extend(rs); base_sizes.extend(ps)
        subsets.append({"denominator":d,"bucket":b,"event_count":len(subids),"annual_event_ids":frozen_annual,"equal_budget_k":k,"rbt_candidates":enriched,"support_pruned_baseline_candidates":baseline,"rbt_summary":summary,"capacity":{"rbt_available":len(enriched),"support_pruned_available":len(baseline),"budget_k":k}})
    size={"rbt_mean_top_budget_member_count":mean(rbt_sizes),"support_pruned_mean_top_budget_member_count":mean(base_sizes),"rbt_p90_top_budget_member_count":q90(rbt_sizes),"support_pruned_p90_top_budget_member_count":q90(base_sizes),"rbt_max_top_budget_member_count":max(rbt_sizes),"support_pruned_max_top_budget_member_count":max(base_sizes),"rbt_size_biased_top_budget_member_burden":burden(rbt_sizes),"support_pruned_size_biased_top_budget_member_burden":burden(base_sizes)}
    structural_gates={"structurally_differs":changed_panels>0,"burden_strictly_lower":size["rbt_size_biased_top_budget_member_burden"]<size["support_pruned_size_biased_top_budget_member_burden"],"p90_not_higher":size["rbt_p90_top_budget_member_count"]<=size["support_pruned_p90_top_budget_member_count"],"max_strictly_lower":size["rbt_max_top_budget_member_count"]<size["support_pruned_max_top_budget_member_count"]}
    out={"schema":"ORBITTRACE_RECURRENCE_BOTTLENECK_TOPOMODAL_V1_PRETRUTH","scientific_role":"TARGET_EXCLUDED_GMN_RBT_V1_RANKING_FROZEN_BEFORE_SHOWER_TRUTH","configuration":{"radius":1.0,"minimum_support":4,"density":"min(d22/n22,d23/n23)","cut_rule":"support_pruned_terminal_rule_v1","m2d_formula":"(1/|C|)*sum_{B subseteq C}|B|*A(B)","ranking":["internal_2d_mass_desc","rbt_modal_contrast_desc","membership_hash_asc"],"new_tuned_parameters":[]},"support_pruned_pretruth_sha256":SUPPORT_SHA,"bif_prelabel_sha256":BIF_SHA,"changed_panels":changed_panels,"size_summary":size,"structural_gates":structural_gates,"structural_pass":all(structural_gates.values()),"subsets":subsets,"shower_truth_used":False,"target_information_access":False,"target_region_events_accessed":False,"orbittrace_reveal_access":False,"sonotaco_scientific_access":False,"post_result_parameter_search":False}
    a.output.write_text(json.dumps(out,separators=(",",":"),sort_keys=True,allow_nan=False)+"\n"); print(json.dumps({"verdict":"RBT_V1_PRETRUTH_PASS_TO_TRUTH" if out["structural_pass"] else "RBT_V1_PRETRUTH_NO_GO","sha256":sha(a.output),"changed_panels":changed_panels,"size_summary":size,"structural_gates":structural_gates,"capacities":[{"d":s["denominator"],"b":s["bucket"],**s["capacity"]} for s in subsets]},indent=2,sort_keys=True),flush=True); return 0
if __name__=="__main__":raise SystemExit(main())
