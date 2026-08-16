#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import hdbscan
from hdbscan._hdbscan_tree import compute_stability

import orbittrace_window_owned_persistence_ranking_v1.run_development as successor

ROUTES=("sugar","hdbscan")
YEARS=(2013,2014)
PANELS=(("sugar",2013),("sugar",2014),("hdbscan",2013),("hdbscan",2014))
LABEL_FREE_MANIFEST_SHA="0a24077f352ddba91c5fea2a102f996d6bea154b1bc769235a4dd916850dba2b"
LABEL_FREE_ROWS_SHA={
 ("sugar",2013):"47fb0b700fbf710c7b061eead343016bd8d182756eb0c7f406507c5739e4c4f8",
 ("sugar",2014):"bc83c113e9a14b1c6e1ef460ca9a40e05df77f3a449fec6064f8910add04c912",
 ("hdbscan",2013):"2433b556d4a859580ef5431d2307ef34c8fa4c15d42841a2ec7b0c11e5f1f158",
 ("hdbscan",2014):"206692292b2ca252777e40c13c367880740d8e2576d27615f7ea94b7790e3f55",
}
EXPECTED_COUNTS={("sugar",2013):18638,("sugar",2014):15400,("hdbscan",2013):16028,("hdbscan",2014):13283}
V31_SHA="f69555d443f453fd40a769da09b2bbec8bf62cd4a932cd84278bb23305b5ac8e"
RECURRENT_SHA="c2395a86be5ba8a8b801210ac6e64b97c446e724991207aef85062ee00b89f12"
BENCHMARK_SOURCE_BLOB="342a7b9307a6dbca72c6043aefce2ecd0346cde5"


def req(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path)
    req(spec is not None and spec.loader is not None,f"cannot import {path}")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def build_route(bench:Any,route:str,rows_by_year:dict[int,list[dict[str,Any]]])->dict[str,Any]:
    events=[]
    for y in YEARS: events.extend(bench.norm(r,y) for r in rows_by_year[y])
    req(len({e["id"] for e in events})==len(events),f"duplicate IDs {route}")
    X=bench.geo(events)
    years=__import__("numpy").asarray([e["year"] for e in events],dtype="int64")
    model=hdbscan.HDBSCAN(min_cluster_size=10,min_samples=10,metric="euclidean",cluster_selection_method="eom",cluster_selection_epsilon=0.0,allow_single_cluster=False,prediction_data=False).fit(X)
    tree=model.condensed_tree_._raw_tree; ordinary=compute_stability(tree)
    recurrent,_annual=bench.recurrent_stability(tree,years)
    rec=bench.extract(route,"recurrent",events,tree,ordinary,recurrent)
    succ,summary=successor.build_successor_candidates(X,events)
    req(all(int(f["rank"])==i for i,f in enumerate(succ,1)),f"successor rank mapping changed {route}")
    return {"events":len(events),"events_by_year":{str(y):sum(e["year"]==y for e in events) for y in YEARS},"recurrent":rec,"successor":{"candidate_count":len(succ),"summary":summary,"candidates":succ}}


def pretruth(rows_root:Path,benchmark_source:Path,out:Path)->int:
    out.mkdir(parents=True,exist_ok=True)
    bench=load_module(benchmark_source,"frozen_sonotaco_direct_benchmark")
    req(tuple(bench.YEARS)==YEARS and tuple(bench.ROUTES)==ROUTES and tuple(bench.BLIND)==(20.0,55.0),"benchmark constants changed")
    req(tuple(bench.PANELS)==PANELS,"benchmark panels changed")
    manifest=rows_root/"label_free_preparation_manifest.json"; req(sha(manifest)==LABEL_FREE_MANIFEST_SHA,"manifest changed")
    m=json.loads(manifest.read_text()); req(m["verdict"]=="PASS_FINAL_SONOTACO_LABEL_FREE_PREPARATION","prep not pass"); req(m["shower_truth_accessed"] is False and m["target_region_retained"] is False,"prep firewall changed")
    routes={}
    for route in ROUTES:
        by={}
        for y in YEARS:
            p=rows_root/f"{route}_{y}.json"; req(sha(p)==LABEL_FREE_ROWS_SHA[(route,y)],f"rows changed {route} {y}")
            rows=json.loads(p.read_text()); req(len(rows)==EXPECTED_COUNTS[(route,y)],f"count changed {route} {y}"); req(all(str(r.get("complex_key"))=="HIDDEN" for r in rows),f"truth placeholder changed {route} {y}"); by[y]=rows
        routes[route]=build_route(bench,route,by)
    obj={"scientific_role":"PRETRUTH_WINDOW_OWNED_PERSISTENCE_SONOTACO_TRANSFER_V1","sonotaco_role":"EXPOSED_DEVELOPMENT_VALIDATION_BENCHMARK","routes":routes,"blind_exclusion":[20.0,55.0],"truth_accessed":False,"v31_accessed":False,"historical_recurrent_result_accessed":False,"literature_result_accessed":False,"target_information_access":False,"target_region_events_accessed":False,"amos_access":False,"maarsy_scientific_access":False,"dms_scientific_access":False}
    p=out/"WINDOW_OWNED_PERSISTENCE_SONOTACO_PRETRUTH.json"; p.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({"pretruth_sha256":sha(p),"routes":{r:{"events":routes[r]["events"],"recurrent_candidates":routes[r]["recurrent"]["candidate_count"],"successor_candidates":routes[r]["successor"]["candidate_count"]} for r in ROUTES}},indent=2,sort_keys=True)); return 0


def evaluate(pretruth_path:Path,benchmark_source:Path,truth_root:Path,v31_path:Path,recurrent_path:Path,out:Path)->int:
    out.mkdir(parents=True,exist_ok=True); bench=load_module(benchmark_source,"frozen_sonotaco_direct_benchmark_eval")
    p=json.loads(pretruth_path.read_text()); req(p["scientific_role"]=="PRETRUTH_WINDOW_OWNED_PERSISTENCE_SONOTACO_TRANSFER_V1","wrong pretruth"); req(p["truth_accessed"] is False and p["v31_accessed"] is False and p["historical_recurrent_result_accessed"] is False and p["literature_result_accessed"] is False,"pretruth exposed controls")
    req(sha(v31_path)==V31_SHA,"v31 changed"); req(sha(recurrent_path)==RECURRENT_SHA,"recurrent result changed")
    old=json.loads(recurrent_path.read_text()); req(old["verdict"]=="PASS_RECURRENT_EOM_SONOTACO_V31_SUPERIORITY_V1","historical recurrent verdict changed"); oldpan={(x["comparator"],int(x["year"])):x for x in old["panels"]}
    panels=[]; all_nr=True; strict=False; all_v31=True; all_lit=True
    for route,y in PANELS:
        truth=json.loads((truth_root/f"truth_{route}_{y}.json").read_text()); frozen=json.loads((truth_root/f"evaluation_{route}_{y}.json").read_text())
        budget=int(frozen["candidate_budget"]["comparator_budget"]); req(budget==int(bench.V31[(route,y)]["budget"]),f"budget changed {route} {y}")
        rec=bench.evaluate(p["routes"][route]["recurrent"]["candidates"],truth,budget); suc=bench.evaluate(p["routes"][route]["successor"]["candidates"],truth,budget)
        hp=oldpan[(route,y)]; req(abs(rec["macro_f1"]-float(hp["recurrent_eom_macro_f1"]))<1e-12 and rec["recovered_f1_gt_0_5"]==int(hp["recurrent_eom_recovered_f1_gt_0_5"]),f"recurrent benchmark did not reproduce {route} {y}")
        nr=bool(suc["macro_f1"]>=rec["macro_f1"]-1e-15 and suc["recovered_f1_gt_0_5"]>=rec["recovered_f1_gt_0_5"]); all_nr=all_nr and nr
        st=bool(suc["macro_f1"]>rec["macro_f1"]+1e-15 or suc["recovered_f1_gt_0_5"]>rec["recovered_f1_gt_0_5"]); strict=strict or st
        vm=float(bench.V31[(route,y)]["macro_f1"]); vr=int(bench.V31[(route,y)]["recovered"]); vpass=bool(suc["macro_f1"]>vm and suc["recovered_f1_gt_0_5"]>=vr); all_v31=all_v31 and vpass
        lit=frozen["comparator_summary"]; lpass=bool(suc["macro_f1"]>float(lit["macro_f1"]) and suc["recovered_f1_gt_0_5"]>=int(lit["recovered_f1_gt_0_5"])); all_lit=all_lit and lpass
        panels.append({"comparator":route,"year":y,"budget":budget,"recurrent_eom":rec,"successor":suc,"macro_f1_delta_vs_recurrent":suc["macro_f1"]-rec["macro_f1"],"recovered_delta_vs_recurrent":suc["recovered_f1_gt_0_5"]-rec["recovered_f1_gt_0_5"],"no_regression_vs_recurrent":nr,"strict_gain_vs_recurrent":st,"v31":{"macro_f1":vm,"recovered":vr,"superiority":vpass},"literature":{"macro_f1":float(lit["macro_f1"]),"recovered":int(lit["recovered_f1_gt_0_5"]),"superiority":lpass}})
    passed=bool(all_nr and strict and all_v31 and all_lit)
    verdict="PASS_WINDOW_OWNED_PERSISTENCE_SONOTACO_TRANSFER_V1" if passed else "FAIL_WINDOW_OWNED_PERSISTENCE_SONOTACO_TRANSFER_V1"
    result={"verdict":verdict,"sonotaco_role":"EXPOSED_DEVELOPMENT_VALIDATION_BENCHMARK","pretruth_sha256":sha(pretruth_path),"panels":panels,"all_panels_no_regression_vs_recurrent":all_nr,"strict_gain_some_panel":strict,"all_panels_v31_superiority":all_v31,"all_panels_literature_superiority":all_lit,"blind_exclusion":[20.0,55.0],"target_information_access":False,"target_region_events_accessed":False,"amos_access":False,"maarsy_scientific_access":False,"dms_scientific_access":False,"post_result_parameter_search":False}
    (out/"WINDOW_OWNED_PERSISTENCE_SONOTACO_TRANSFER_V1.json").write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n"); print(json.dumps(result,indent=2,sort_keys=True)); return 0


def main()->int:
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="mode",required=True)
    p=sub.add_parser("pretruth"); p.add_argument("--rows-root",type=Path,required=True); p.add_argument("--benchmark-source",type=Path,required=True); p.add_argument("--output",type=Path,required=True)
    e=sub.add_parser("evaluate"); e.add_argument("--pretruth",type=Path,required=True); e.add_argument("--benchmark-source",type=Path,required=True); e.add_argument("--truth-root",type=Path,required=True); e.add_argument("--v31-result",type=Path,required=True); e.add_argument("--recurrent-result",type=Path,required=True); e.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    return pretruth(a.rows_root,a.benchmark_source,a.output) if a.mode=="pretruth" else evaluate(a.pretruth,a.benchmark_source,a.truth_root,a.v31_result,a.recurrent_result,a.output)

if __name__=="__main__": raise SystemExit(main())
