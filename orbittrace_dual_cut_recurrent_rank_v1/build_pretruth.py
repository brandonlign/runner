#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "orbittrace_recurrent_eom_hdbscan_v1"))
import recurrent_eom as reom  # noqa: E402

YEARS=(2013,2014)
ROUTES=("sugar","hdbscan")
BUDGETS=(10,14,20,40,43,50,100)
ROW_SHA={
("sugar",2013):"47fb0b700fbf710c7b061eead343016bd8d182756eb0c7f406507c5739e4c4f8",
("sugar",2014):"bc83c113e9a14b1c6e1ef460ca9a40e05df77f3a449fec6064f8910add04c912",
("hdbscan",2013):"2433b556d4a859580ef5431d2307ef34c8fa4c15d42841a2ec7b0c11e5f1f158",
("hdbscan",2014):"206692292b2ca252777e40c13c367880740d8e2576d27615f7ea94b7790e3f55",
}
EXPECTED={("sugar",2013):18638,("sugar",2014):15400,("hdbscan",2013):16028,("hdbscan",2014):13283}


def req(x:bool,msg:str)->None:
    if not x: raise RuntimeError(msg)

def sha256(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()

def install_hdb_compat()->None:
    import hdbscan.hdbscan_ as hi
    from sklearn.utils import check_array as sk
    def compat(*a:Any,**kw:Any)->Any:
        if "ensure_all_finite" in kw: kw["force_all_finite"]=kw.pop("ensure_all_finite")
        return sk(*a,**kw)
    hi.check_array=compat

def geo(rows:list[dict[str,Any]])->np.ndarray:
    sol=np.radians(np.asarray([float(r["sol"])%360 for r in rows])); lon=np.radians(np.asarray([float(r["sun_lon"]) for r in rows])); lat=np.radians(np.asarray([float(r["ecl_lat"]) for r in rows])); vg=np.asarray([float(r["vg"]) for r in rows])
    X=np.column_stack((np.cos(sol),np.sin(sol),np.sin(lon)*np.cos(lat),np.cos(lon)*np.cos(lat),np.sin(lat),vg/72.0))
    req(X.shape==(len(rows),6) and np.all(np.isfinite(X)),"invalid GEO6"); return X

def membership_map(tree:np.ndarray,nodes:set[int])->dict[int,tuple[int,...]]:
    root=int(tree["parent"].min()); children:dict[int,list[int]]=defaultdict(list); clusters:set[int]=set()
    for p,c in zip(tree["parent"],tree["child"]):
        p,c=int(p),int(c); children[p].append(c); clusters.add(p)
        if c>=root: clusters.add(c)
    memo:dict[int,tuple[int,...]]={}
    for node in sorted(clusters,reverse=True):
        pts=[]
        for c in children.get(node,[]): pts.append(c) if c<root else pts.extend(memo[c])
        memo[node]=tuple(sorted(pts))
    return {n:memo[n] for n in nodes}

def mh(ids:list[str])->str:return hashlib.sha256("|".join(sorted(ids)).encode()).hexdigest()

def catalogue(rows:list[dict[str,Any]],nodes:set[int],members:dict[int,tuple[int,...]],ordinary:dict[float,float],recurrent:dict[float,float],origin:dict[int,list[str]])->list[dict[str,Any]]:
    out=[]
    for node in nodes:
        ids=sorted(str(rows[i]["id"]) for i in members[node])
        out.append({"family_id":"DCRR"+mh(ids)[:16],"node_id":node,"event_ids":ids,"member_hash":mh(ids),"member_count":len(ids),"ordinary_stability":float(ordinary[float(node)]),"recurrent_stability":float(recurrent[float(node)]),"origin":sorted(origin[node])})
    out.sort(key=lambda f:(-f["recurrent_stability"],-f["ordinary_stability"],-f["member_count"],f["member_hash"]))
    for i,f in enumerate(out,1):f["rank"]=i
    return out

def canonical(labels:np.ndarray)->list[tuple[int,...]]:
    return sorted(tuple(np.flatnonzero(labels==lab).tolist()) for lab in np.unique(labels) if int(lab)>=0)

def cut_catalogue(rows,labels,nodes,ordinary,recurrent,kind):
    pos=sorted(int(x) for x in np.unique(labels) if int(x)>=0); req(pos==list(range(len(nodes))),"compact mapping changed")
    out=[]
    for lab,node in enumerate(nodes):
        ids=sorted(str(rows[int(i)]["id"]) for i in np.flatnonzero(labels==lab)); out.append({"member_hash":mh(ids),"node_id":int(node),"member_count":len(ids),"ordinary_stability":float(ordinary[float(node)]),"recurrent_stability":float(recurrent[float(node)])})
    if kind=="ordinary": out.sort(key=lambda f:(-f["ordinary_stability"],-f["member_count"],f["member_hash"]))
    else: out.sort(key=lambda f:(-f["recurrent_stability"],-f["ordinary_stability"],-f["member_count"],f["member_hash"]))
    for i,f in enumerate(out,1):f["rank"]=i
    return out

def relation(a:set[str],b:set[str])->str:
    if not a&b:return "disjoint"
    if a==b:return "equal"
    if a<b:return "contained_by"
    if b<a:return "contains"
    return "partial_overlap"

def route(root:Path,name:str)->dict[str,Any]:
    rows=[]
    for y in YEARS:
        p=root/f"{name}_{y}.json"; req(p.exists(),f"missing {p}"); req(sha256(p)==ROW_SHA[(name,y)],"row hash drift"); part=json.loads(p.read_text()); req(len(part)==EXPECTED[(name,y)],"row count drift"); rows.extend(part)
    X=geo(rows); years=np.asarray([int(r["year"]) for r in rows],dtype=np.int64)
    model=hdbscan.HDBSCAN(min_cluster_size=10,min_samples=10,metric="euclidean",cluster_selection_method="eom",cluster_selection_epsilon=0.0,allow_single_cluster=False,prediction_data=False).fit(X)
    tree=model.condensed_tree_._raw_tree; ordinary=compute_stability(tree); recurrent,_annual=reom.recurrent_stability(tree,years)
    onodes=tuple(reom.selected_eom_nodes(tree,ordinary)); rnodes=tuple(reom.selected_eom_nodes(tree,recurrent)); olab=reom.eom_labels(tree,ordinary); rlab=reom.eom_labels(tree,recurrent)
    req(canonical(model.labels_)==canonical(olab),"ordinary extraction mismatch")
    ocut=cut_catalogue(rows,olab,onodes,ordinary,recurrent,"ordinary"); rcut=cut_catalogue(rows,rlab,rnodes,ordinary,recurrent,"recurrent")
    nodes=set(onodes)|set(rnodes); origin={n:[] for n in nodes}
    for n in onodes:origin[n].append("ordinary")
    for n in rnodes:origin[n].append("recurrent")
    members=membership_map(tree,nodes); dcrr=catalogue(rows,nodes,members,ordinary,recurrent,origin)
    # Validate cut memberships against descendant reconstruction.
    node_hash={n:mh(sorted(str(rows[i]["id"]) for i in members[n])) for n in nodes}
    req(all(node_hash[int(x["node_id"])]==x["member_hash"] for x in ocut),"ordinary membership reconstruction drift")
    req(all(node_hash[int(x["node_id"])]==x["member_hash"] for x in rcut),"recurrent membership reconstruction drift")
    rec_hash=[x["member_hash"] for x in rcut]; union_hash=[x["member_hash"] for x in dcrr]; rec_set=set(rec_hash)
    diagnostics={}
    for k in BUDGETS:
        u=dcrr[:k]; r=rcut[:k]; us={x["member_hash"] for x in u}; rs={x["member_hash"] for x in r}
        additions=[x for x in u if "recurrent" not in x["origin"]]
        rec_all=[(x,set(x["event_ids"])) for x in dcrr if "recurrent" in x["origin"]]
        add_rows=[]
        for x in additions:
            s=set(x["event_ids"]); rel=[]
            for y,ys in rec_all:
                z=relation(s,ys)
                if z!="disjoint":rel.append({"recurrent_node_id":y["node_id"],"recurrent_union_rank":y["rank"],"relation":z})
            add_rows.append({"rank":x["rank"],"node_id":x["node_id"],"member_count":x["member_count"],"recurrent_stability":x["recurrent_stability"],"ordinary_stability":x["ordinary_stability"],"overlapping_recurrent_candidates":rel})
        diagnostics[str(k)]={"dcrr_count":len(u),"current_recurrent_count":len(r),"exact_set_overlap":len(us&rs),"current_recurrent_topk_retained":len(rs&us),"ordinary_only_additions":len(additions),"same_set_as_current_recurrent":us==rs,"same_rank_positions":sum(a==b for a,b in zip(union_hash[:k],rec_hash[:k])),"addition_details":add_rows}
    return {"event_count":len(rows),"events_by_year":{str(y):int(np.sum(years==y)) for y in YEARS},"ordinary_candidate_count":len(ocut),"current_recurrent_candidate_count":len(rcut),"dcrr_candidate_count":len(dcrr),"ordinary_only_node_count":len(set(onodes)-set(rnodes)),"recurrent_only_node_count":len(set(rnodes)-set(onodes)),"mechanism_active":union_hash!=rec_hash,"budget_diagnostics":diagnostics,"dcrr_candidates":dcrr,"truth_accessed":False,"shower_label_fields_accessed":False}

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--rows-root",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True);install_hdb_compat()
    routes={r:route(a.rows_root,r) for r in ROUTES};req(any(v["mechanism_active"] for v in routes.values()),"DCRR inactive")
    result={"schema":"ORBITTRACE_DUAL_CUT_RECURRENT_RANK_V1_PRETRUTH","scientific_role":"LABEL_FREE_DCRR_ACTIVITY_AUDIT_ON_EXACT_PAPER_INPUTS","routes":routes,"truth_accessed":False,"shower_label_fields_accessed":False,"post_activity_method_change_authorized":False}
    p=a.output/"DCRR_V1_PRETRUTH.json";p.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({r:{"ordinary":v["ordinary_candidate_count"],"recurrent":v["current_recurrent_candidate_count"],"dcrr":v["dcrr_candidate_count"],"budgets":{k:{z:v["budget_diagnostics"][k][z] for z in ("exact_set_overlap","ordinary_only_additions","same_rank_positions")} for k in map(str,(14,40,43))}} for r,v in routes.items()},indent=2,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
