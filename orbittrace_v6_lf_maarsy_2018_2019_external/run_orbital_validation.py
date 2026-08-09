#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_v6_lf_maarsy_2018_2019_external import maarsy_transport as transport

YEARS=transport.YEARS
DSH_THRESHOLD=0.05
MIN_YEAR_ORBIT_MEMBERS=4
MIN_FAMILY_PRECISION=0.50
MIN_Q=10
MIN_VALID_ROW_FRACTION=0.90


def require(ok:bool,message:str)->None:
    if not ok: raise RuntimeError(message)


def canonical_sha(value:Any)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()


def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); require(spec is not None and spec.loader is not None,f"cannot load {path}")
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


class UnionFind:
    def __init__(self,n:int): self.parent=list(range(n)); self.size=[1]*n
    def find(self,x:int)->int:
        while self.parent[x]!=x: self.parent[x]=self.parent[self.parent[x]]; x=self.parent[x]
        return x
    def union(self,a:int,b:int)->None:
        a=self.find(a); b=self.find(b)
        if a==b:return
        if self.size[a]<self.size[b]:a,b=b,a
        self.parent[b]=a; self.size[a]+=self.size[b]


def corroborate(families:list[dict[str,Any]],orbits:dict[str,dict[str,float]],dsh:Any)->tuple[dict[str,dict[str,Any]],dict[str,Any]]:
    rows={}; qualified=0; total_rows=0; valid_rows=0; qualified_precisions=[]
    for family in families:
        fid=str(family["family_id"]); ids=list(map(str,family["event_ids"])); total_rows+=len(ids); valid=[eid for eid in ids if eid in orbits]; valid_rows+=len(valid)
        best=[]; best_counts={}
        if len(valid)>=2:
            q=[orbits[e]["q"] for e in valid]; ecc=[orbits[e]["e"] for e in valid]; inc=[orbits[e]["i"] for e in valid]; arg=[orbits[e]["arg"] for e in valid]; node=[orbits[e]["node"] for e in valid]
            matrix=dsh.pairwise_dsh(q,ecc,inc,arg,node); uf=UnionFind(len(valid)); ii,jj=np.where(np.triu(matrix<DSH_THRESHOLD,k=1))
            for a,b in zip(ii.tolist(),jj.tolist()): uf.union(int(a),int(b))
            groups={}
            for i,eid in enumerate(valid): groups.setdefault(uf.find(i),[]).append(eid)
            candidates=[]
            for component in groups.values():
                counts=Counter(transport.parse_event_id(eid)[0] for eid in component)
                if all(counts.get(y,0)>=MIN_YEAR_ORBIT_MEMBERS for y in YEARS): candidates.append((len(component)/len(ids),len(component),component,dict(counts)))
            if candidates: _p,_n,best,best_counts=max(candidates,key=lambda x:(x[0],x[1],sorted(x[2])))
        precision=len(best)/len(ids) if ids else 0.0
        ok=bool(best and precision>=MIN_FAMILY_PRECISION and all(best_counts.get(y,0)>=MIN_YEAR_ORBIT_MEMBERS for y in YEARS)); qualified+=int(ok)
        if ok: qualified_precisions.append(precision)
        rows[fid]={"family_id":fid,"family_event_count":len(ids),"valid_orbit_count":len(valid),"valid_orbit_fraction":len(valid)/len(ids) if ids else 0.0,"largest_cross_year_dsh_component":len(best),"component_year_counts":{str(y):int(best_counts.get(y,0)) for y in YEARS},"orbital_corroboration_precision":precision,"orbitally_corroborated":ok,"dsh_threshold":DSH_THRESHOLD}
    return rows,{"family_count":len(families),"orbitally_corroborated_families":qualified,"family_event_rows":total_rows,"valid_family_event_rows":valid_rows,"valid_family_event_row_fraction":valid_rows/total_rows if total_rows else 0.0,"median_corroborated_precision":float(np.median(qualified_precisions)) if qualified_precisions else 0.0}


def ranking_metrics(order:list[str],corr:dict[str,dict[str,Any]])->dict[str,Any]:
    require(len(order)==len(set(order)) and set(order)==set(corr),"ranking universe changed")
    good={fid for fid,row in corr.items() if row["orbitally_corroborated"]}; ranks=[i for i,fid in enumerate(order,start=1) if fid in good]
    return {"Q":len(good),"T25":sum(fid in good for fid in order[:25]),"T50":sum(fid in good for fid in order[:50]),"MRR_Q":float(np.mean([1.0/r for r in ranks])) if ranks else 0.0,"corroborated_ranks":ranks}


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--geometry-freeze",required=True,type=Path); p.add_argument("--geometry-sha",required=True,type=Path); p.add_argument("--dsh-comparator",required=True,type=Path); p.add_argument("--output",required=True,type=Path); args=p.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    geometry=json.loads(args.geometry_freeze.read_text()); stored=str(args.geometry_sha.read_text()).strip(); frozen_sha=str(geometry.pop("preorbit_canonical_sha256")); require(stored==frozen_sha==canonical_sha(geometry),"preorbit geometry/ranking freeze changed"); geometry["preorbit_canonical_sha256"]=frozen_sha
    require(geometry["schema"]=="orbittrace-v6-lf-maarsy-2018-2019-geometry-freeze-v1" and geometry["verdict"]=="PASS_V6_LF_MAARSY_2018_2019_EXTERNAL_GEOMETRY_FREEZE","geometry power/integrity did not pass")
    require(geometry["years"]==list(YEARS) and geometry["blind_exclusion"]==[20.0,55.0],"geometry identity changed")
    require(geometry["orbit_access"] is False and geometry["label_access"] is False and geometry["target_information_access"] is False,"preorbit firewall changed")
    require(all(geometry["geometry_integrity_gates"].values()),"geometry gate changed")
    dsh=load_module(args.dsh_comparator,"orbittrace_maarsy_2018_2019_dsh"); require(abs(float(dsh.RUD2014_DSH_THRESHOLD)-DSH_THRESHOLD)<1e-15,"D_SH comparator threshold changed")

    v6_families=geometry["v6lf"]["families"]; v6_order=list(map(str,geometry["v6lf"]["primary_order"])); v8_families=geometry["v8"]["families"]; v8_order=list(map(str,geometry["v8"]["multiplicity_order"]))
    require([str(f["family_id"]) for f in v6_families]==v6_order,"v6-LF order/families changed"); require([str(f["family_id"]) for f in v8_families]==v8_order,"v8 order/families changed")
    v6_order_sha=canonical_sha(v6_order); v8_order_sha=canonical_sha(v8_order)
    needed={str(eid) for f in v6_families+v8_families for eid in f["event_ids"]}; require(needed,"empty frozen family-event union")

    # FIRST orbital-value access. Only exact IDs already present in the immutable preorbit families are read.
    orbits,orbit_audit=transport.read_needed_orbits(needed,args.output)
    v6_corr,v6_summary=corroborate(v6_families,orbits,dsh); v8_corr,v8_summary=corroborate(v8_families,orbits,dsh)
    v6_metrics=ranking_metrics(v6_order,v6_corr); v8_metrics=ranking_metrics(v8_order,v8_corr)
    require(canonical_sha(v6_order)==v6_order_sha and canonical_sha(v8_order)==v8_order_sha,"ranking mutated after orbit access")

    integrity={
        "immutable_preorbit_geometry_and_rankings":True,
        "only_frozen_family_event_orbits_read":orbit_audit["needed_family_events"]==len(needed),
        "all_needed_archive_members_found":orbit_audit["needed_archive_members"]==orbit_audit["seen_needed_archive_members"],
        "native_kepler_semantics":orbit_audit["native_kepler_mapping"]==["a_m","e","i_deg","omega_deg","Omega_deg","nu_deg"] and orbit_audit["au_m"]==149_597_870_700.0,
        "kepler_std_unopened":orbit_audit["kepler_std_opened"] is False,
        "geometry_fields_unopened_in_orbit_stage":orbit_audit["geometry_fields_opened_this_stage"] is False,
        "D_SH_threshold_005":abs(float(dsh.RUD2014_DSH_THRESHOLD)-0.05)<1e-15,
        "rankings_unchanged_after_orbit_access":canonical_sha(v6_order)==v6_order_sha and canonical_sha(v8_order)==v8_order_sha,
        "no_target_information":orbit_audit["target_information_access"] is False,
    }
    power={"Q_v6lf_at_least_10":v6_metrics["Q"]>=MIN_Q,"Q_v8_at_least_10":v8_metrics["Q"]>=MIN_Q,"v6lf_valid_family_event_rows_at_least_90pct":v6_summary["valid_family_event_row_fraction"]>=MIN_VALID_ROW_FRACTION,"v8_valid_family_event_rows_at_least_90pct":v8_summary["valid_family_event_row_fraction"]>=MIN_VALID_ROW_FRACTION}
    science={
        "Q_v6lf_at_least_80pct_v8":v6_metrics["Q"]>=math.ceil(0.80*v8_metrics["Q"]),
        "T25_v6lf_retention_and_absolute_min":v6_metrics["T25"]>=max(2,math.ceil(0.80*v8_metrics["T25"])),
        "T50_v6lf_retention_and_absolute_min":v6_metrics["T50"]>=max(4,math.ceil(0.80*v8_metrics["T50"])),
        "MRR_Q_v6lf_at_least_80pct_v8":v6_metrics["MRR_Q"]>=0.80*v8_metrics["MRR_Q"],
        "median_precision_Q_v6lf_at_least_060":v6_summary["median_corroborated_precision"]>=0.60,
        "rankings_byte_semantics_unchanged":canonical_sha(v6_order)==v6_order_sha and canonical_sha(v8_order)==v8_order_sha,
    }
    if not all(integrity.values()): verdict="FAIL_V6_LF_MAARSY_2018_2019_EXTERNAL_INTEGRITY"
    elif not all(power.values()): verdict="INCONCLUSIVE_V6_LF_MAARSY_2018_2019_EXTERNAL_POWER"
    elif all(science.values()): verdict="PASS_V6_LF_MAARSY_2018_2019_EXTERNAL_VALIDATION"
    else: verdict="FAIL_V6_LF_MAARSY_2018_2019_EXTERNAL_VALIDATION"
    result={"schema":"orbittrace-v6-lf-maarsy-2018-2019-external-validation-v1","verdict":verdict,"configuration":{"years":list(YEARS),"blind_exclusion":[20.0,55.0],"D_SH_threshold":DSH_THRESHOLD,"minimum_year_orbit_members":MIN_YEAR_ORBIT_MEMBERS,"family_inclusion_precision":MIN_FAMILY_PRECISION,"Q_power_floor_each_method":MIN_Q,"valid_family_event_row_fraction_floor":MIN_VALID_ROW_FRACTION,"parameter_search":False,"alternate_year_or_subset_search":False},"preorbit_canonical_sha256":frozen_sha,"v6lf":{"summary":v6_summary,"metrics":v6_metrics,"order_sha256":v6_order_sha},"v8":{"summary":v8_summary,"metrics":v8_metrics,"order_sha256":v8_order_sha},"orbit_read_audit":orbit_audit,"integrity_gates":integrity,"power_gates":power,"scientific_gates":science,"target_information_access":False}
    (args.output/"v6_lf_maarsy_2018_2019_external_validation.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    (args.output/"v6_lf_maarsy_2018_2019_orbital_corroboration.json").write_text(json.dumps({"v6lf":v6_corr,"v8":v8_corr},sort_keys=True)+"\n")
    print(json.dumps({"verdict":verdict,"Q_v6lf":v6_metrics["Q"],"Q_v8":v8_metrics["Q"],"T25_v6lf":v6_metrics["T25"],"T25_v8":v8_metrics["T25"],"T50_v6lf":v6_metrics["T50"],"T50_v8":v8_metrics["T50"],"MRR_Q_v6lf":v6_metrics["MRR_Q"],"MRR_Q_v8":v8_metrics["MRR_Q"],"median_precision_Q_v6lf":v6_summary["median_corroborated_precision"]},sort_keys=True),flush=True)
    return 0


if __name__=="__main__": raise SystemExit(main())
