#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_v6_lf_maarsy_2018_2019_external import maarsy_transport as transport
from orbittrace_label_free_sparse_support_v6 import run_development as v8core
from orbittrace_pooled_year_centroid_v8 import run_development as v8comp

YEARS=transport.YEARS
MIN_FAMILIES=50
V6LF_REPAIRED_SHA256="257aab9d0f4d710a1b62af6088cfb9c0939062018d44dbacd074b4e7898eaa24"


def require(ok:bool,message:str)->None:
    if not ok: raise RuntimeError(message)


def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()


def canonical_sha(value:Any)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()


def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); require(spec is not None and spec.loader is not None,f"cannot load {path}")
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def configure_namespace(module:Any)->None:
    for obj in (module,getattr(module,"mult",None)):
        if obj is None: continue
        if hasattr(obj,"YEARS"): obj.YEARS=YEARS
        if hasattr(obj,"MONTH_KEYS"): obj.MONTH_KEYS=tuple()


def pooled_centroids(families:list[dict[str,Any]],components:list[dict[str,Any]],scan:dict[int,list[dict[str,Any]]],support:Any,base:Any)->dict[str,Any]:
    by_component={str(c["component_id"]):c for c in components}; lookup={y:{str(e["id"]):e for e in scan[y]} for y in YEARS}; duplicates=0
    for family in families:
        centers={}
        for year in YEARS:
            cs=[by_component[str(cid)] for cid in family["component_ids"] if int(by_component[str(cid)]["year"])==year]
            require(cs,f"v8 family {family['family_id']} missing {year}"); duplicates+=int(len(cs)>1)
            ids=sorted(set().union(*(set(map(str,c["event_ids"])) for c in cs))); require(ids and all(eid in lookup[year] for eid in ids),"v8 family lookup failed")
            centers[str(year)]=v8comp.pooled_centroid([lookup[year][eid] for eid in ids],support)
        family["centroids"]=centers
    return {"duplicate_family_years":duplicates,"family_membership_changed":False,"pooling_statistic":{"sol":"circular_mean_deg","sun_lon":"circular_mean_deg","ecl_lat":"median","vg":"median"}}


def normalize_v6lf_family(f:dict[str,Any],rank:int)->dict[str,Any]:
    ids=sorted(set(map(str,f["event_ids"]))); require(ids,"empty v6-LF family")
    return {"family_id":str(f["family_id"]),"rank":rank,"years":[int(y) for y in f["years"]],"event_ids":ids}


def normalize_v8_family(f:dict[str,Any])->dict[str,Any]:
    ids=sorted(set(map(str,f["event_ids"]))); require(ids,"empty v8 family")
    return {"family_id":str(f["family_id"]),"years":[int(y) for y in f["years"]],"event_ids":ids}


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--repaired-v6-source",required=True,type=Path); p.add_argument("--base-runner",required=True,type=Path)
    p.add_argument("--support-source-parts",required=True,type=Path); p.add_argument("--candidate-payload",required=True,type=Path); p.add_argument("--baseline-payload",required=True,type=Path); p.add_argument("--scorer-parts",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path); args=p.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    require(sha256_file(args.repaired_v6_source)==V6LF_REPAIRED_SHA256,"repaired v6-LF source changed")
    require(transport.YEARS==(2018,2019) and transport.BLIND_LOW==20.0 and transport.BLIND_HIGH==55.0 and transport.MAX_EVENTS_PER_BIN==10000,"MAARSY transport constants changed")

    # No orbit/label/target values have been opened before this call. stream_geometry itself reads
    # only solar longitude first, applies the blind mask, then retained radiant/speed rows.
    zenodo=transport.verify_zenodo_metadata(); scan_raw,transport_audit=transport.stream_geometry(args.output)
    require(transport_audit["target_interval_radiant_speed_read"] is False and transport_audit["orbital_dataset_opened"] is False and transport_audit["labels_used"] is False,"MAARSY geometry firewall failed")

    # v6-LF exact all-event-null architecture on the fixed retained event universe.
    v6lf=load_module(args.repaired_v6_source,"orbittrace_v6lf_maarsy_external"); configure_namespace(v6lf)
    require(all(v6lf.v3.self_test().values()),"v6-LF v3 self-test failed")
    if hasattr(v6lf,"v3_membership_self_test"): require(all(v6lf.v3_membership_self_test().values()),"v6-LF membership self-test failed")
    old=v6lf.load_base_runner(args.base_runner); configure_namespace(old)
    support=old.load_support_module(args.support_source_parts); support.YEARS=YEARS; support.MONTH_KEYS=tuple(); support.CORPUS="orbittrace-v6-lf-maarsy-2018-2019-external"
    candidate,base,scorer=support.load_sources(args)
    require(float(support.BLIND_LOW)==20.0 and float(support.BLIND_HIGH)==55.0,"v6-LF blind constants changed")
    scan={y:[dict(e,iau=0,complex_key="HIDDEN") for e in scan_raw[y]] for y in YEARS}
    calibration={y:[dict(e,iau=0,complex_key="SPORADIC") for e in scan_raw[y]] for y in YEARS}
    require(all([e["id"] for e in scan[y]]==[e["id"] for e in calibration[y]] for y in YEARS),"all-event calibration IDs changed")
    v6_components=[]; v6_audits=[]
    for year in YEARS:
        audit,_anchors,components=v6lf.scan_year_v6(old,year,scan[year],calibration[year],candidate,base,scorer,support)
        require(int(audit["scan_events"])==int(audit["calibration_events"])==len(scan[year]),f"v6-LF all-event calibration failed {year}")
        require(int(audit["proposal_cap_per_window"])==512 and int(audit["max_primary_proposals_per_year"])==36864,"v6-LF proposal budget changed")
        require(len(audit["supported_bins"])>=24,f"v6-LF insufficient scannable bins {year}")
        v6_audits.append(audit); v6_components.extend(components)
    v6_primary=v6lf.build_family_track_v6(old,v6_components,base,"v3")
    require(len({str(f["family_id"]) for f in v6_primary})==len(v6_primary),"v6-LF family IDs not unique")
    require(all(sorted(map(int,f["years"]))==list(YEARS) for f in v6_primary),"v6-LF family outside 2018/2019")
    v6_families=[normalize_v6lf_family(f,i) for i,f in enumerate(v6_primary,start=1)]

    # Exact promoted-v8 comparator on the identical retained event IDs.
    configure_namespace(v8core); configure_namespace(v8comp); configure_namespace(v8comp.mult)
    require(all(v8comp.mult.v3.self_test().values()) and all(v8comp.mult.brown.self_test().values()),"v8 scorer self-test failed")
    v8runtime=v8comp.mult.load_frozen_runtime(); v8support=v8runtime.load_support_module(args.support_source_parts); v8support.YEARS=YEARS; v8support.MONTH_KEYS=tuple(); v8support.CORPUS="orbittrace-v8-maarsy-2018-2019-external-baseline"
    v8support.RANKING_VARIANTS=("persistence","mean_year_strength","sqrt_support_strength","min_year_strength","size_penalized_strength")
    _cand,v8base,_scorer=v8support.load_sources(args)
    v8_components=[]; v8_audits=[]
    for year in YEARS:
        audit,_passing,components=v8core.label_free_scan_year(year,scan_raw[year],v8support,v8base)
        require(int(audit["scannable_bin_count"])>=24,f"v8 insufficient scannable bins {year}")
        v8_audits.append(audit); v8_components.extend(components)
    v8_families_raw,v8_support_rankings=v8support.build_families(v8_components,v8base)
    require(all(sorted(map(int,f["years"]))==list(YEARS) for f in v8_families_raw),"v8 family outside 2018/2019")
    pooling=pooled_centroids(v8_families_raw,v8_components,scan_raw,v8support,v8base)
    v8comp.mult.YEARS=YEARS; v8comp.mult.MONTH_KEYS=tuple(); v8comp.mult.TOP_K=100
    scored,scoring_summary=v8comp.mult.score_families(v8_families_raw,scan_raw,v8runtime,v8base)
    multiplicity_order=[str(x) for x in v8comp.mult.rank_scored(scored,"multiplicity")]
    v8_ids={str(f["family_id"]) for f in v8_families_raw}; require(len(multiplicity_order)==len(v8_ids) and set(multiplicity_order)==v8_ids,"v8 multiplicity order incomplete")
    raw_by_id={str(f["family_id"]):f for f in v8_families_raw}
    v8_families=[normalize_v8_family(raw_by_id[fid]) for fid in multiplicity_order]
    require({e["id"] for y in YEARS for e in scan[y]}=={e["id"] for y in YEARS for e in scan_raw[y]},"dual-method event universe changed")

    geometry_integrity={
        "exact_years_2018_2019":True,
        "complete_12_months_each_year":all(transport_audit["selected_months"][str(y)]==list(range(1,13)) for y in YEARS),
        "target_interval_excluded_before_radiant_speed":transport_audit["target_interval_radiant_speed_read"] is False,
        "identity_only_10000_per_bin_cap":all(all(int(v)<=10000 for v in transport_audit["selected_by_bin_after_cap"][str(y)].values()) for y in YEARS),
        "identical_dual_method_event_universe":True,
        "v6lf_all_event_calibration":all(int(a["scan_events"])==int(a["calibration_events"]) for a in v6_audits),
        "v6lf_proposal_budget_exact":all(int(a["proposal_cap_per_window"])==512 and int(a["max_primary_proposals_per_year"])==36864 for a in v6_audits),
        "v6lf_at_least_50_primary_families":len(v6_families)>=MIN_FAMILIES,
        "v8_at_least_50_recurrent_families":len(v8_families)>=MIN_FAMILIES,
        "every_family_spans_both_years":all(f["years"]==list(YEARS) for f in v6_families+v8_families),
        "no_orbit_access":transport_audit["orbital_dataset_opened"] is False,
        "no_labels":transport_audit["labels_used"] is False,
        "no_target_information":transport_audit["target_information_access"] is False,
    }
    verdict="PASS_V6_LF_MAARSY_2018_2019_EXTERNAL_GEOMETRY_FREEZE" if all(geometry_integrity.values()) else ("INCONCLUSIVE_V6_LF_MAARSY_2018_2019_EXTERNAL_GEOMETRY_POWER" if all(v for k,v in geometry_integrity.items() if k not in {"v6lf_at_least_50_primary_families","v8_at_least_50_recurrent_families"}) else "FAIL_V6_LF_MAARSY_2018_2019_EXTERNAL_INTEGRITY")
    payload={"schema":"orbittrace-v6-lf-maarsy-2018-2019-geometry-freeze-v1","verdict":verdict,"years":list(YEARS),"blind_exclusion":[20.0,55.0],"zenodo_metadata":zenodo,"transport_audit":transport_audit,"v6lf":{"family_count":len(v6_families),"primary_order":[f["family_id"] for f in v6_families],"families":v6_families,"year_audits":v6_audits},"v8":{"family_count":len(v8_families),"multiplicity_order":multiplicity_order,"families":v8_families,"year_audits":v8_audits,"pooling":pooling,"scoring_summary":scoring_summary},"geometry_integrity_gates":geometry_integrity,"orbit_access":False,"label_access":False,"target_information_access":False}
    digest=canonical_sha(payload); payload["preorbit_canonical_sha256"]=digest
    path=args.output/"maarsy_2018_2019_geometry_freeze.json"; path.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n"); (args.output/"maarsy_2018_2019_geometry_freeze.sha256").write_text(digest+"\n")
    print(json.dumps({"verdict":verdict,"v6lf_families":len(v6_families),"v8_families":len(v8_families),"preorbit_sha256":digest},sort_keys=True),flush=True)
    return 0


if __name__=="__main__": raise SystemExit(main())
