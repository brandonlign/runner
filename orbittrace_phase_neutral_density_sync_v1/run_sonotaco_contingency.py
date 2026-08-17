#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability
from scipy.optimize import linear_sum_assignment

import recurrent_eom as parent_reom
from density_synchronous_eom import density_synchronous_stability
from phase_neutral_geometry import phase_neutral_geo_matrix

YEARS = (2013, 2014)
ROUTES = ("sugar", "hdbscan")
PANELS = (("sugar",2013),("sugar",2014),("hdbscan",2013),("hdbscan",2014))
BLIND = (20.0,55.0)
MIN_CLUSTER_SIZE = 10
MIN_SAMPLES = 10
LABEL_FREE_MANIFEST_SHA = "0a24077f352ddba91c5fea2a102f996d6bea154b1bc769235a4dd916850dba2b"
LABEL_FREE_ROWS_SHA = {
    ("sugar",2013):"47fb0b700fbf710c7b061eead343016bd8d182756eb0c7f406507c5739e4c4f8",
    ("sugar",2014):"bc83c113e9a14b1c6e1ef460ca9a40e05df77f3a449fec6064f8910add04c912",
    ("hdbscan",2013):"2433b556d4a859580ef5431d2307ef34c8fa4c15d42841a2ec7b0c11e5f1f158",
    ("hdbscan",2014):"206692292b2ca252777e40c13c367880740d8e2576d27615f7ea94b7790e3f55",
}
EXPECTED_COUNTS = {
    ("sugar",2013):18638,("sugar",2014):15400,
    ("hdbscan",2013):16028,("hdbscan",2014):13283,
}
EXPECTED_CHAMPION = {
    ("sugar",2013):(34,0.3752906816276458,23),
    ("sugar",2014):(46,0.43773122295664196,24),
    ("hdbscan",2013):(11,0.1914598192215768,11),
    ("hdbscan",2014):(9,0.1685878550176112,9),
}


def req(ok: bool, msg: str) -> None:
    if not ok: raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def event_field(row: dict[str,Any], name: str) -> float:
    req(name in row and row[name] is not None, f"missing {name}")
    x=float(row[name]); req(math.isfinite(x),f"nonfinite {name}"); return x


def normalize_event(row: dict[str,Any], year: int) -> dict[str,Any]:
    eid=str(row["id"]); req(int(row["year"])==year,f"row year mismatch {eid}")
    req(eid.startswith(f"SNT{year}:"),f"SonotaCo ID/year mismatch {eid}")
    sol=event_field(row,"sol")%360.0; lon=event_field(row,"sun_lon"); lat=event_field(row,"ecl_lat"); vg=event_field(row,"vg")
    req(vg>0.0,f"nonpositive vg {eid}"); req(not (BLIND[0]<=sol<=BLIND[1]),f"protected row {eid}")
    return {"id":eid,"year":year,"sol":sol,"lon":lon,"lat":lat,"vg":vg}


def geo6(events: list[dict[str,Any]]) -> np.ndarray:
    sol=np.radians(np.asarray([e["sol"] for e in events],float)); lon=np.radians(np.asarray([e["lon"] for e in events],float)); lat=np.radians(np.asarray([e["lat"] for e in events],float)); vg=np.asarray([e["vg"] for e in events],float)
    return np.column_stack((np.cos(sol),np.sin(sol),np.sin(lon)*np.cos(lat),np.cos(lon)*np.cos(lat),np.sin(lat),vg/72.0))


def family_id(prefix: str, route: str, members: tuple[str,...]) -> str:
    return hashlib.sha256((prefix+"|"+route+"|"+"|".join(members)).encode()).hexdigest()[:20]


def sync_candidates(route: str, prefix: str, events: list[dict[str,Any]], X: np.ndarray, years: np.ndarray) -> dict[str,Any]:
    model=hdbscan.HDBSCAN(min_cluster_size=MIN_CLUSTER_SIZE,min_samples=MIN_SAMPLES,metric="euclidean",cluster_selection_method="eom",cluster_selection_epsilon=0.0,allow_single_cluster=False,prediction_data=False).fit(X)
    tree=model.condensed_tree_._raw_tree; ordinary=compute_stability(tree); sync,_annual,_recon=density_synchronous_stability(tree,years)
    labels=parent_reom.eom_labels(tree,sync); nodes=parent_reom.selected_eom_nodes(tree,sync)
    positive=sorted(int(x) for x in np.unique(labels) if int(x)>=0); req(positive==list(range(len(nodes))),f"label/node mapping changed {route}")
    out=[]
    for lab,node in enumerate(nodes):
        idx=np.flatnonzero(labels==lab); members=tuple(sorted(events[int(i)]["id"] for i in idx)); req(len(members)>=10,"subminimum family")
        out.append({"family_id":family_id(prefix,route,members),"rank":0,"node_id":int(node),"event_ids":list(members),"member_count":len(members),"synchronous_stability":float(sync[float(node)]),"ordinary_stability":float(ordinary[float(node)])})
    out.sort(key=lambda f:(-f["synchronous_stability"],-f["ordinary_stability"],-f["member_count"],f["family_id"]))
    for rank,row in enumerate(out,1): row["rank"]=rank
    return {"candidate_count":len(out),"tree_sha256":hashlib.sha256(tree.tobytes()).hexdigest(),"selected_nodes":list(nodes),"order_sha256":hashlib.sha256("\n".join(f["family_id"] for f in out).encode()).hexdigest(),"candidates":out}


def evaluate(families: list[dict[str,Any]], truth: dict[str,str], budget: int) -> dict[str,Any]:
    from collections import Counter
    counts=Counter(v for v in truth.values() if v!="SPORADIC"); labels=sorted(k for k,n in counts.items() if n>=4); truth_sets={label:{eid for eid,value in truth.items() if value==label} for label in labels}; truth_ids=set(truth)
    active=[]
    for family in families:
        members=set(map(str,family["event_ids"])) & truth_ids
        if members: active.append((int(family["rank"]),str(family["family_id"]),members))
    active=sorted(active,key=lambda x:(x[0],x[1]))[:int(budget)]
    mat=np.zeros((len(labels),len(active)),dtype=float)
    for i,label in enumerate(labels):
        actual=truth_sets[label]
        for j,(_rank,_fid,pred) in enumerate(active):
            ov=len(actual & pred)
            if ov:
                p=ov/len(pred); r=ov/len(actual); mat[i,j]=2*p*r/(p+r)
    n=max(len(labels),len(active)); cost=np.zeros((n,n),dtype=float); cost[:len(labels),:len(active)]=-mat; ri,cj=linear_sum_assignment(cost)
    vals=[float(mat[i,j]) if j<len(active) else 0.0 for i,j in zip(ri.tolist(),cj.tolist()) if i<len(labels)]
    return {"eligible_showers":len(labels),"macro_f1":float(np.mean(vals)) if vals else 0.0,"recovered_f1_gt_0_5":int(sum(x>0.5 for x in vals)),"candidate_used":len(active)}


def run_pretruth(rows_root: Path, output: Path) -> int:
    output.mkdir(parents=True,exist_ok=True); mp=rows_root/"label_free_preparation_manifest.json"; req(sha(mp)==LABEL_FREE_MANIFEST_SHA,"label-free manifest changed"); manifest=json.loads(mp.read_text()); req(manifest["verdict"]=="PASS_FINAL_SONOTACO_LABEL_FREE_PREPARATION","label-free prep not passed"); req(manifest["shower_truth_accessed"] is False and manifest["target_information_access"] is False and manifest["target_region_retained"] is False,"label-free boundary changed")
    routes={}
    for route in ROUTES:
        events=[]
        for year in YEARS:
            p=rows_root/f"{route}_{year}.json"; req(sha(p)==LABEL_FREE_ROWS_SHA[(route,year)],f"rows changed {route} {year}"); rows=json.loads(p.read_text()); req(len(rows)==EXPECTED_COUNTS[(route,year)],f"count changed {route} {year}"); req(all(str(r.get("complex_key"))=="HIDDEN" for r in rows),"complex key exposed"); events.extend(normalize_event(r,year) for r in rows)
        years=np.asarray([e["year"] for e in events],dtype=np.int64); champion=sync_candidates(route,"DSEOM6SNT",events,geo6(events),years); successor=sync_candidates(route,"DSEOM4SNT",events,phase_neutral_geo_matrix(events),years)
        routes[route]={"events":len(events),"champion":champion,"successor":successor,"mechanism_active":bool(champion["tree_sha256"]!=successor["tree_sha256"] or champion["order_sha256"]!=successor["order_sha256"])}
    result={"schema":"ORBITTRACE_PHASE_NEUTRAL_DENSITY_SYNC_SONOTACO_PRETRUTH_V1","scientific_role":"PRETRUTH_EXPOSED_SONOTACO_PORTABILITY_CONTINGENCY","routes":routes,"blind_exclusion":list(BLIND),"truth_accessed":False,"target_information_access":False,"target_region_events_accessed":False,"amos_access":False,"maarsy_scientific_access":False,"dms_scientific_access":False}
    path=output/"PHASE_NEUTRAL_DENSITY_SYNC_SONOTACO_PRETRUTH_V1.json"; path.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n"); print(json.dumps({"pretruth_sha256":sha(path),"routes":{r:{"events":routes[r]["events"],"champion_candidates":routes[r]["champion"]["candidate_count"],"successor_candidates":routes[r]["successor"]["candidate_count"],"mechanism_active":routes[r]["mechanism_active"]} for r in ROUTES}},indent=2,sort_keys=True)); return 0


def run_evaluate(pretruth_path: Path, truth_root: Path, output: Path) -> int:
    output.mkdir(parents=True,exist_ok=True); pre=json.loads(pretruth_path.read_text()); req(pre["schema"]=="ORBITTRACE_PHASE_NEUTRAL_DENSITY_SYNC_SONOTACO_PRETRUTH_V1","wrong pretruth"); req(pre["truth_accessed"] is False,"pretruth contaminated")
    panels=[]; strict=False; all_pass=True
    for route,year in PANELS:
        truth=json.loads((truth_root/f"truth_{route}_{year}.json").read_text()); frozen=json.loads((truth_root/f"evaluation_{route}_{year}.json").read_text()); budget=int(frozen["candidate_budget"]["comparator_budget"]); exp_budget,exp_f1,exp_rec=EXPECTED_CHAMPION[(route,year)]; req(budget==exp_budget,f"budget changed {route} {year}")
        cm=evaluate(pre["routes"][route]["champion"]["candidates"],truth,budget); sm=evaluate(pre["routes"][route]["successor"]["candidates"],truth,budget)
        req(np.isclose(cm["macro_f1"],exp_f1,rtol=0,atol=1e-15),f"paired GEO6 champion macro-F1 changed {route} {year}: {cm['macro_f1']} != {exp_f1}"); req(cm["recovered_f1_gt_0_5"]==exp_rec,f"paired GEO6 champion recovery changed {route} {year}")
        macro_ok=sm["macro_f1"]>=cm["macro_f1"]; rec_ok=sm["recovered_f1_gt_0_5"]>=cm["recovered_f1_gt_0_5"]; panel_strict=sm["macro_f1"]>cm["macro_f1"] or sm["recovered_f1_gt_0_5"]>cm["recovered_f1_gt_0_5"]
        strict = strict or panel_strict; all_pass = all_pass and macro_ok and rec_ok
        panels.append({"route":route,"year":year,"budget":budget,"champion":cm,"successor":sm,"macro_f1_not_lower":macro_ok,"recovered_not_lower":rec_ok,"strict_improvement":panel_strict,"macro_f1_delta":sm["macro_f1"]-cm["macro_f1"],"recovered_delta":sm["recovered_f1_gt_0_5"]-cm["recovered_f1_gt_0_5"]})
    mechanism=all(bool(pre["routes"][r]["mechanism_active"]) for r in ROUTES); passed=bool(mechanism and all_pass and strict); verdict="PASS_PHASE_NEUTRAL_DENSITY_SYNC_V1_SONOTACO_PORTABILITY" if passed else "FAIL_PHASE_NEUTRAL_DENSITY_SYNC_V1_SONOTACO_PORTABILITY"
    result={"verdict":verdict,"scientific_role":"EXPOSED_SONOTACO_2013_2014_PORTABILITY_ONLY","pretruth_sha256":sha(pretruth_path),"panels":panels,"mechanism_active_both_routes":mechanism,"all_panel_no_regression":all_pass,"strict_improvement_some_panel":strict,"post_result_parameter_search":False,"blind_exclusion":list(BLIND),"target_information_access":False,"target_region_events_accessed":False,"amos_access":False,"maarsy_scientific_access":False,"dms_scientific_access":False}
    path=output/"PHASE_NEUTRAL_DENSITY_SYNC_SONOTACO_V1.json"; path.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n"); print(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)); return 0


def main() -> int:
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="command",required=True); p=sub.add_parser("pretruth"); p.add_argument("--rows-root",type=Path,required=True); p.add_argument("--output",type=Path,required=True); e=sub.add_parser("evaluate"); e.add_argument("--pretruth",type=Path,required=True); e.add_argument("--truth-root",type=Path,required=True); e.add_argument("--output",type=Path,required=True); a=ap.parse_args(); return run_pretruth(a.rows_root,a.output) if a.command=="pretruth" else run_evaluate(a.pretruth,a.truth_root,a.output)


if __name__=="__main__": raise SystemExit(main())
