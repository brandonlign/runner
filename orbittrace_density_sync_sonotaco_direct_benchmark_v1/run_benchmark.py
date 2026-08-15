#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability
from scipy.optimize import linear_sum_assignment

from orbittrace_recurrent_eom_hdbscan_v1.recurrent_eom import eom_labels, recurrent_stability, selected_eom_nodes
from orbittrace_density_synchronous_recurrent_eom_v1.density_synchronous_eom import density_synchronous_stability

YEARS=(2013,2014)
ROUTES=("sugar","hdbscan")
PANELS=(("sugar",2013),("sugar",2014),("hdbscan",2013),("hdbscan",2014))
BLIND=(20.0,55.0)
MCS=10
MS=10
LABEL_FREE_MANIFEST_SHA="0a24077f352ddba91c5fea2a102f996d6bea154b1bc769235a4dd916850dba2b"
LABEL_FREE_ROWS_SHA={
 ("sugar",2013):"47fb0b700fbf710c7b061eead343016bd8d182756eb0c7f406507c5739e4c4f8",
 ("sugar",2014):"bc83c113e9a14b1c6e1ef460ca9a40e05df77f3a449fec6064f8910add04c912",
 ("hdbscan",2013):"2433b556d4a859580ef5431d2307ef34c8fa4c15d42841a2ec7b0c11e5f1f158",
 ("hdbscan",2014):"206692292b2ca252777e40c13c367880740d8e2576d27615f7ea94b7790e3f55",
}
EXPECTED_COUNTS={("sugar",2013):18638,("sugar",2014):15400,("hdbscan",2013):16028,("hdbscan",2014):13283}
V31_RESULT_SHA="f69555d443f453fd40a769da09b2bbec8bf62cd4a932cd84278bb23305b5ac8e"
V31={
 ("sugar",2013):{"budget":34,"macro_f1":0.2719801488280529,"recovered":16},
 ("sugar",2014):{"budget":46,"macro_f1":0.31529041952487225,"recovered":17},
 ("hdbscan",2013):{"budget":11,"macro_f1":0.14888037368183737,"recovered":9},
 ("hdbscan",2014):{"budget":9,"macro_f1":0.15198123772301594,"recovered":9},
}
RECURRENT_RESULT_SHA="c2395a86be5ba8a8b801210ac6e64b97c446e724991207aef85062ee00b89f12"


def req(ok: bool,msg: str)->None:
    if not ok: raise RuntimeError(msg)

def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def canon_sha(obj:Any)->str: return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()

def field(row:dict[str,Any],name:str)->float:
    req(name in row and row[name] is not None,f"missing {name}")
    x=float(row[name]); req(math.isfinite(x),f"nonfinite {name}"); return x

def norm(row:dict[str,Any],year:int)->dict[str,Any]:
    eid=str(row["id"]); ry=int(row["year"])
    req(ry==year,f"year mismatch {eid}"); req(eid.startswith(f"SNT{year}:"),f"id/year mismatch {eid}")
    sol=field(row,"sol")%360.0; lon=field(row,"sun_lon"); lat=field(row,"ecl_lat"); vg=field(row,"vg")
    req(vg>0,f"nonpositive vg {eid}"); req(not(BLIND[0]<=sol<=BLIND[1]),f"protected row {eid}")
    return {"id":eid,"year":year,"sol":sol,"lon":lon,"lat":lat,"vg":vg}

def geo(events:list[dict[str,Any]])->np.ndarray:
    sol=np.radians(np.asarray([e["sol"] for e in events],float)); lon=np.radians(np.asarray([e["lon"] for e in events],float)); lat=np.radians(np.asarray([e["lat"] for e in events],float)); vg=np.asarray([e["vg"] for e in events],float)
    return np.column_stack((np.cos(sol),np.sin(sol),np.sin(lon)*np.cos(lat),np.cos(lon)*np.cos(lat),np.sin(lat),vg/72.0))

def partition(labels:np.ndarray)->tuple[tuple[int,...],...]:
    return tuple(sorted(tuple(np.flatnonzero(labels==lab).tolist()) for lab in sorted(int(x) for x in np.unique(labels) if int(x)>=0)))

def fid(route:str,method:str,members:tuple[str,...])->str:
    if method=="recurrent":
        payload=f"SNT-REOM1|{route}|"+"|".join(members)
    else:
        payload="DSEOM1|"+"|".join(members)
    return hashlib.sha256(payload.encode()).hexdigest()[:20]

def extract(route:str,method:str,events:list[dict[str,Any]],tree:np.ndarray,ordinary:dict[float,float],quality:dict[float,float])->dict[str,Any]:
    labels=eom_labels(tree,quality); nodes=selected_eom_nodes(tree,quality)
    pos=sorted(int(x) for x in np.unique(labels) if int(x)>=0); req(pos==list(range(len(nodes))),f"compact mapping changed {route} {method}")
    c=[]
    for lab,node in enumerate(nodes):
        idx=np.flatnonzero(labels==lab); members=tuple(sorted(events[int(i)]["id"] for i in idx)); req(len(members)>=MCS,f"subminimum {route} {method}")
        score=float(quality[float(node)])
        c.append({"family_id":fid(route,method,members),"rank":0,"node_id":int(node),"event_ids":list(members),"member_count":len(members),"method_score":score,"ordinary_stability":float(ordinary[float(node)])})
    c.sort(key=lambda x:(-x["method_score"],-x["ordinary_stability"],-x["member_count"],x["family_id"]))
    for i,row in enumerate(c,1): row["rank"]=i
    membership_order=[hashlib.sha256("|".join(row["event_ids"]).encode()).hexdigest() for row in c]
    return {"selected_nodes":list(nodes),"candidate_count":len(c),"candidate_order_membership_sha256":hashlib.sha256("\n".join(membership_order).encode()).hexdigest(),"candidates":c}

def build_route(route:str,rows_by_year:dict[int,list[dict[str,Any]]])->dict[str,Any]:
    events=[]
    for y in YEARS: events.extend(norm(r,y) for r in rows_by_year[y])
    req(len({e["id"] for e in events})==len(events),f"duplicate pooled IDs {route}")
    years=np.asarray([e["year"] for e in events],np.int64); X=geo(events)
    model=hdbscan.HDBSCAN(min_cluster_size=MCS,min_samples=MS,metric="euclidean",cluster_selection_method="eom",cluster_selection_epsilon=0.0,allow_single_cluster=False,prediction_data=False).fit(X)
    tree=model.condensed_tree_._raw_tree; ordinary=compute_stability(tree)
    req(partition(model.labels_)==partition(eom_labels(tree,ordinary)),f"ordinary extraction mismatch {route}")
    recurrent,annual=recurrent_stability(tree,years)
    sync,annual_parent,annual_recon=density_synchronous_stability(tree,years)
    req(canon_sha({str(k):list(v) for k,v in sorted(annual.items())})==canon_sha({str(k):list(v) for k,v in sorted(annual_parent.items())}),f"annual parent mismatch {route}")
    rec=extract(route,"recurrent",events,tree,ordinary,recurrent)
    ds=extract(route,"density_sync",events,tree,ordinary,sync)
    return {
      "events":len(events),"events_by_year":{str(y):int(np.sum(years==y)) for y in YEARS},
      "ordinary_selected_nodes":list(selected_eom_nodes(tree,ordinary)),"recurrent":rec,"density_sync":ds,
      "mechanism_active_vs_recurrent":bool(rec["selected_nodes"]!=ds["selected_nodes"] or rec["candidate_order_membership_sha256"]!=ds["candidate_order_membership_sha256"]),
      "annual_recurrent_stability_sha256":canon_sha({str(k):list(v) for k,v in sorted(annual.items())}),
      "annual_reconstructed_sha256":canon_sha({str(k):list(v) for k,v in sorted(annual_recon.items())}),
    }

def pretruth(rows_root:Path,out:Path)->int:
    out.mkdir(parents=True,exist_ok=True)
    mp=rows_root/"label_free_preparation_manifest.json"; req(sha(mp)==LABEL_FREE_MANIFEST_SHA,"manifest changed")
    m=json.loads(mp.read_text()); req(m["verdict"]=="PASS_FINAL_SONOTACO_LABEL_FREE_PREPARATION","label-free prep not pass"); req(m["shower_truth_accessed"] is False,"truth exposed in prep"); req(m["target_region_retained"] is False,"protected retained")
    routes={}
    for route in ROUTES:
        by={}
        for y in YEARS:
            p=rows_root/f"{route}_{y}.json"; req(sha(p)==LABEL_FREE_ROWS_SHA[(route,y)],f"rows changed {route} {y}")
            rows=json.loads(p.read_text()); req(len(rows)==EXPECTED_COUNTS[(route,y)],f"count changed {route} {y}"); req(all(str(r.get("complex_key"))=="HIDDEN" for r in rows),f"truth placeholder changed {route} {y}"); by[y]=rows
        routes[route]=build_route(route,by)
    obj={"scientific_role":"PRETRUTH_FROZEN_DENSITY_SYNC_SONOTACO_DIRECT_BENCHMARK_V1","sonotaco_role":"EXPOSED_DEVELOPMENT_VALIDATION_BENCHMARK","routes":routes,"blind_exclusion":list(BLIND),"truth_accessed":False,"v31_accessed":False,"historical_recurrent_result_accessed":False,"target_information_access":False,"target_region_events_accessed":False,"amos_access":False,"maarsy_scientific_access":False,"dms_scientific_access":False}
    p=out/"DENSITY_SYNC_SONOTACO_DIRECT_PRETRUTH.json"; p.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+"\n"); print(json.dumps({"pretruth_sha256":sha(p),"routes":{r:{"events":routes[r]["events"],"recurrent_candidates":routes[r]["recurrent"]["candidate_count"],"density_sync_candidates":routes[r]["density_sync"]["candidate_count"],"mechanism_active":routes[r]["mechanism_active_vs_recurrent"]} for r in ROUTES}},indent=2,sort_keys=True)); return 0

def evaluate(families:list[dict[str,Any]],truth:dict[str,str],budget:int)->dict[str,Any]:
    counts=Counter(v for v in truth.values() if v!="SPORADIC"); labels=sorted(k for k,n in counts.items() if n>=4); truth_sets={k:{eid for eid,v in truth.items() if v==k} for k in labels}; tids=set(truth)
    active=[]
    for f in families:
        members=set(map(str,f["event_ids"]))&tids
        if members: active.append((int(f["rank"]),str(f["family_id"]),members))
    active=sorted(active,key=lambda x:(x[0],x[1]))[:int(budget)]
    mat=np.zeros((len(labels),len(active)),float)
    for i,label in enumerate(labels):
        actual=truth_sets[label]
        for j,(_rank,_id,pred) in enumerate(active):
            ov=len(actual&pred)
            if ov:
                pr=ov/len(pred); re=ov/len(actual); mat[i,j]=2*pr*re/(pr+re)
    n=max(len(labels),len(active)); cost=np.zeros((n,n),float); cost[:len(labels),:len(active)]=-mat; ri,cj=linear_sum_assignment(cost)
    vals=[float(mat[i,j]) if j<len(active) else 0.0 for i,j in zip(ri.tolist(),cj.tolist()) if i<len(labels)]
    return {"eligible_showers":len(labels),"macro_f1":float(np.mean(vals)) if vals else 0.0,"recovered_f1_gt_0_5":int(sum(x>0.5 for x in vals)),"candidate_used":len(active)}

def main_eval(pretruth_path:Path,truth_root:Path,v31_path:Path,recurrent_result_path:Path,out:Path)->int:
    out.mkdir(parents=True,exist_ok=True); p=json.loads(pretruth_path.read_text()); req(p["scientific_role"]=="PRETRUTH_FROZEN_DENSITY_SYNC_SONOTACO_DIRECT_BENCHMARK_V1","wrong pretruth"); req(p["truth_accessed"] is False and p["v31_accessed"] is False and p["historical_recurrent_result_accessed"] is False,"pretruth exposed")
    req(sha(v31_path)==V31_RESULT_SHA,"v31 bytes changed"); req(sha(recurrent_result_path)==RECURRENT_RESULT_SHA,"historical recurrent result bytes changed")
    old=json.loads(recurrent_result_path.read_text()); oldpan={(x["comparator"],int(x["year"])):x for x in old["panels"]}; req(old["verdict"]=="PASS_RECURRENT_EOM_SONOTACO_V31_SUPERIORITY_V1","historical recurrent verdict changed")
    panels=[]; v31wins=0; no_reg=True; strict=False
    for route,y in PANELS:
        truth=json.loads((truth_root/f"truth_{route}_{y}.json").read_text()); frozen=json.loads((truth_root/f"evaluation_{route}_{y}.json").read_text()); budget=int(frozen["candidate_budget"]["comparator_budget"]); req(budget==V31[(route,y)]["budget"],f"budget changed {route} {y}")
        rec=evaluate(p["routes"][route]["recurrent"]["candidates"],truth,budget); ds=evaluate(p["routes"][route]["density_sync"]["candidates"],truth,budget)
        hp=oldpan[(route,y)]; req(abs(rec["macro_f1"]-float(hp["recurrent_eom_macro_f1"]))<1e-12 and rec["recovered_f1_gt_0_5"]==int(hp["recurrent_eom_recovered_f1_gt_0_5"]),f"recurrent benchmark did not reproduce {route} {y}")
        vm=V31[(route,y)]["macro_f1"]; vr=V31[(route,y)]["recovered"]; vpass=bool(ds["macro_f1"]>vm and ds["recovered_f1_gt_0_5"]>=vr); v31wins+=int(vpass)
        nr=bool(ds["macro_f1"]>=rec["macro_f1"]-1e-15 and ds["recovered_f1_gt_0_5"]>=rec["recovered_f1_gt_0_5"]); no_reg=no_reg and nr
        st=bool(ds["macro_f1"]>rec["macro_f1"]+1e-15 or ds["recovered_f1_gt_0_5"]>rec["recovered_f1_gt_0_5"]); strict=strict or st
        lit=frozen["comparator_summary"]; lpass=bool(ds["macro_f1"]>float(lit["macro_f1"]) and ds["recovered_f1_gt_0_5"]>=int(lit["recovered_f1_gt_0_5"]))
        panels.append({"comparator":route,"year":y,"budget":budget,"recurrent_eom":rec,"density_sync":ds,"macro_f1_delta_vs_recurrent":ds["macro_f1"]-rec["macro_f1"],"recovered_delta_vs_recurrent":ds["recovered_f1_gt_0_5"]-rec["recovered_f1_gt_0_5"],"nonregression_vs_recurrent":nr,"strict_improvement_vs_recurrent":st,"v31_superiority_pair_pass":vpass,"literature_superiority_pair_pass":lpass})
    mechanism=any(bool(p["routes"][r]["mechanism_active_vs_recurrent"]) for r in ROUTES)
    if v31wins==4 and no_reg and strict and mechanism: verdict="PASS_DENSITY_SYNC_SONOTACO_DIRECT_BENCHMARK_V1"
    elif v31wins==4 and no_reg and not strict: verdict="NEUTRAL_DENSITY_SYNC_SONOTACO_DIRECT_BENCHMARK_V1"
    else: verdict="FAIL_DENSITY_SYNC_SONOTACO_DIRECT_BENCHMARK_V1"
    obj={"verdict":verdict,"scientific_role":"EXPOSED_SONOTACO_DIRECT_METHOD_SELECTION_BENCHMARK","sonotaco_role":"EXPOSED_DEVELOPMENT_VALIDATION_BENCHMARK","pretruth_sha256":sha(pretruth_path),"historical_recurrent_result_sha256":sha(recurrent_result_path),"v31_result_sha256":sha(v31_path),"v31_panel_wins":v31wins,"recurrent_nonregression_all_four":no_reg,"strict_improvement_any_panel":strict,"mechanism_active":mechanism,"panels":panels,"blind_exclusion":list(BLIND),"target_information_access":False,"target_region_events_accessed":False,"amos_access":False,"maarsy_scientific_access":False,"dms_scientific_access":False,"post_result_parameter_search":False}
    rp=out/"DENSITY_SYNC_SONOTACO_DIRECT_BENCHMARK_V1.json"; rp.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+"\n"); print(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)); return 0

def main()->int:
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest="cmd",required=True); a=sp.add_parser("pretruth"); a.add_argument("--rows-root",type=Path,required=True); a.add_argument("--output",type=Path,required=True); b=sp.add_parser("evaluate"); b.add_argument("--pretruth",type=Path,required=True); b.add_argument("--truth-root",type=Path,required=True); b.add_argument("--v31-result",type=Path,required=True); b.add_argument("--recurrent-result",type=Path,required=True); b.add_argument("--output",type=Path,required=True); x=ap.parse_args(); return pretruth(x.rows_root,x.output) if x.cmd=="pretruth" else main_eval(x.pretruth,x.truth_root,x.v31_result,x.recurrent_result,x.output)

if __name__=="__main__": raise SystemExit(main())
