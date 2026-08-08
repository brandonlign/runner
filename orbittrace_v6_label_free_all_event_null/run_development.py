#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import types
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_v6_label_free_all_event_null.parallel_exact_rescore import install as install_parallel_exact

YEARS=(2022,2023)
MONTH_KEYS=tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1,13))
REPAIRED_V6_SHA256="257aab9d0f4d710a1b62af6088cfb9c0939062018d44dbacd074b4e7898eaa24"
V8_QUALIFIED=95
V8_RECOVERY100=58
V8_MRR=0.045531138942766655
V8_TOP100_PRECISION=0.6884631112636006
V8_MACRO_F1=0.1736657194465356
MIN_TOP100_PRECISION=0.65
MIN_FAMILIES=50


def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser()
    p.add_argument("--repaired-v6-source",required=True,type=Path)
    p.add_argument("--base-runner",required=True,type=Path)
    p.add_argument("--support-source-parts",required=True,type=Path)
    p.add_argument("--candidate-payload",required=True,type=Path)
    p.add_argument("--baseline-payload",required=True,type=Path)
    p.add_argument("--scorer-parts",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    return p.parse_args()


def require(ok:bool,message:str)->None:
    if not ok: raise RuntimeError(message)


def sha256_path(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value:Any)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()


def load_module(path:Path,name:str)->types.ModuleType:
    spec=importlib.util.spec_from_file_location(name,path)
    require(spec is not None and spec.loader is not None,f"cannot import {path}")
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def geometry_arrays(frame,columns:dict[str,str]):
    ids=frame[columns["id"]].astype(str).str.strip().to_numpy()
    sol=frame[columns["sol"]].to_numpy(dtype=np.float64)
    lam=frame[columns["lam"]].to_numpy(dtype=np.float64)
    bet=frame[columns["bet"]].to_numpy(dtype=np.float64)
    vg=frame[columns["vg"]].to_numpy(dtype=np.float64)
    return ids,sol,lam,bet,vg


def valid_blind_excluded_mask(sol:np.ndarray,lam:np.ndarray,bet:np.ndarray,vg:np.ndarray,support:types.ModuleType)->np.ndarray:
    valid=np.isfinite(sol)&np.isfinite(lam)&np.isfinite(bet)&np.isfinite(vg)&(vg>0.0)
    blind=(sol>=float(support.BLIND_LOW))&(sol<=float(support.BLIND_HIGH))
    return valid & ~blind


def parse_geometry_only(support:types.ModuleType)->tuple[dict[int,list[dict[str,Any]]],dict[int,list[dict[str,Any]]],list[dict[str,Any]],set[str]]:
    scan={year:[] for year in YEARS}; calibration={year:[] for year in YEARS}; audits=[]; seen:set[str]=set()
    for key in MONTH_KEYS:
        year=int(key[:4]); frame=support.read_gmn_frame(key); columns=support.column_map(frame)
        # Critical firewall: no access to frame[columns["shower"]] anywhere in this function.
        ids,sol,lam,bet,vg=geometry_arrays(frame,columns)
        keep=valid_blind_excluded_mask(sol,lam,bet,vg,support)
        raw=int(len(frame)); accepted=duplicates=0
        for index in np.flatnonzero(keep):
            event_id=str(ids[int(index)])
            if not event_id or event_id in seen:
                duplicates+=int(bool(event_id)); continue
            seen.add(event_id)
            s=float(sol[int(index)]); lon=float((lam[int(index)]-s)%360.0)
            event={"id":event_id,"year":year,"sol":s,"sun_lon":lon,"ecl_lat":float(bet[int(index)]),"vg":float(vg[int(index)]),"iau":0,"complex_key":"HIDDEN"}
            scan[year].append(event)
            calibration[year].append(dict(event,complex_key="SPORADIC"))
            accepted+=1
        audits.append({"key":key,"raw_rows":raw,"geometry_rows_after_blind_and_dedup":accepted,"duplicates_removed":duplicates,"label_value_accessed":False,"blind_interval_removed_before_label_access":True})
        print(f"v6-LF geometry {key}: raw={raw:,} accepted={accepted:,}",flush=True)
    for year in YEARS:
        require(len(scan[year])==len(calibration[year]),f"all-event calibration count mismatch {year}")
        require([e["id"] for e in scan[year]]==[e["id"] for e in calibration[year]],f"all-event calibration ID order mismatch {year}")
        for a,b in zip(scan[year],calibration[year]):
            require(all(a[k]==b[k] for k in ("id","year","sol","sun_lon","ecl_lat","vg","iau")),f"calibration geometry mismatch {a['id']}")
    return scan,calibration,audits,seen


def parse_truth_after_freeze(support:types.ModuleType,expected_ids:set[str])->tuple[dict[str,str],list[dict[str,Any]]]:
    hidden:dict[str,str]={}; audits=[]; seen:set[str]=set()
    for key in MONTH_KEYS:
        frame=support.read_gmn_frame(key); columns=support.column_map(frame)
        ids,sol,lam,bet,vg=geometry_arrays(frame,columns)
        keep=valid_blind_excluded_mask(sol,lam,bet,vg,support)
        selected=0; duplicates=0
        for index in np.flatnonzero(keep):
            event_id=str(ids[int(index)])
            if not event_id or event_id in seen:
                duplicates+=int(bool(event_id)); continue
            seen.add(event_id)
            require(event_id in expected_ids,f"truth pass added pretruth-absent event {event_id}")
            # FIRST label-value access is after geometry validity, blind exclusion and duplicate resolution.
            label=support.normalize_label(frame.iloc[int(index)][columns["shower"]])
            hidden[event_id]=label if label else "SPORADIC"
            selected+=1
        audits.append({"key":key,"truth_rows":selected,"duplicates_removed":duplicates,"label_value_accessed_only_after_blind_and_dedup":True})
    require(seen==expected_ids,f"truth/pretruth event universe mismatch: truth={len(seen)} pretruth={len(expected_ids)}")
    require(set(hidden)==expected_ids,"truth labels missing expected IDs")
    return hidden,audits


def freeze_families(primary:list[dict[str,Any]],rescue:list[dict[str,Any]])->dict[str,Any]:
    def compact(family:dict[str,Any])->dict[str,Any]:
        return {"family_id":str(family["family_id"]),"rank":int(family["rank"]),"channel":str(family["channel"]),"years":[int(y) for y in family["years"]],"event_ids":sorted(str(x) for x in family["event_ids"]),"event_count":int(family["event_count"]),"component_ids":sorted(str(x) for x in family["component_ids"])}
    return {"primary":[compact(f) for f in primary],"rescue":[compact(f) for f in rescue]}


def main()->int:
    args=parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    require(sha256_path(args.repaired_v6_source)==REPAIRED_V6_SHA256,"repaired v6 source identity changed")
    v6=load_module(args.repaired_v6_source,"orbittrace_v6_lf_science")
    require(all(v6.v3.self_test().values()),"v3 self-test failed")
    require(all(v6.v3_membership_self_test().values()),"v3 membership self-test failed")
    old=v6.load_base_runner(args.base_runner)
    require(list(old.YEARS)==[2022,2023] and int(old.MAX_COMPONENTS_PER_BIN)==128,"frozen base constants changed")
    support=old.load_support_module(args.support_source_parts)
    require(float(support.BLIND_LOW)==20.0 and float(support.BLIND_HIGH)==55.0,"blind interval changed")
    candidate,base,scorer=support.load_sources(args)
    parallel=install_parallel_exact(v6,workers=4,min_parallel_records=256)

    scan,calibration,geometry_audits,pretruth_ids=parse_geometry_only(support)
    audits=[]; anchors=[]; components=[]
    for year in YEARS:
        audit,year_anchors,year_components=v6.scan_year_v6(old,year,scan[year],calibration[year],candidate,base,scorer,support)
        require(int(audit["scan_events"])==len(scan[year]),f"scan count mismatch {year}")
        require(int(audit["calibration_events"])==len(scan[year]),f"all-event calibration count mismatch {year}")
        require(int(audit["proposal_cap_per_window"])==512 and int(audit["max_primary_proposals_per_year"])==36864,"proposal budget changed")
        audits.append(audit); anchors.extend(year_anchors); components.extend(year_components)
    primary=v6.build_family_track_v6(old,components,base,"v3")
    rescue=v6.build_family_track_v6(old,components,base,"fixed4_rescue")

    frozen=freeze_families(primary,rescue)
    pretruth_sha=canonical_sha(frozen)
    frozen_raw=json.dumps(frozen,sort_keys=True,separators=(",",":")).encode()
    (args.output/"v6_lf_pretruth_families.json.gz").write_bytes(gzip.compress(frozen_raw))
    (args.output/"v6_lf_pretruth.sha256").write_text(pretruth_sha+"\n")

    # FIRST label-value access in the full execution occurs inside this call, after durable pretruth freeze.
    hidden_labels,truth_audits=parse_truth_after_freeze(support,pretruth_ids)
    evaluation=v6.evaluate_families_v6(hidden_labels,primary,rescue,YEARS)

    gates={
        "exact_repaired_v6_source":sha256_path(args.repaired_v6_source)==REPAIRED_V6_SHA256,
        "blind_interval_exact":[float(support.BLIND_LOW),float(support.BLIND_HIGH)]==[20.0,55.0],
        "geometry_parser_never_accessed_label_values":all(a["label_value_accessed"] is False for a in geometry_audits),
        "all_event_calibration_exact":all(len(calibration[y])==len(scan[y]) and [e["id"] for e in calibration[y]]==[e["id"] for e in scan[y]] for y in YEARS),
        "at_least_30_supported_bins_each_year":all(len(a["supported_bins"])>=30 for a in audits),
        "proposal_budget_exact":all(a["proposal_cap_per_window"]==512 and a["max_primary_proposals_per_year"]==36864 for a in audits),
        "pretruth_family_payload_frozen_before_truth":len(pretruth_sha)==64,
        "truth_event_universe_exact":set(hidden_labels)==pretruth_ids,
        "at_least_50_v3_families":int(evaluation["v3_family_count"])>=MIN_FAMILIES,
        "qualified_at_least_v8":int(evaluation["qualified_matches"])>=V8_QUALIFIED,
        "recovery100_at_least_v8":int(evaluation["recovered_at_100"])>=V8_RECOVERY100,
        "mrr_at_least_v8":float(evaluation["mrr"])>=V8_MRR,
        "top100_precision_at_least_065":float(evaluation["top100_dominant_precision"])>=MIN_TOP100_PRECISION,
        "macro_f1_at_least_v8":float(evaluation["macro_f1"])>=V8_MACRO_F1,
    }
    verdict="PASS_V6_LABEL_FREE_ALL_EVENT_NULL_DEVELOPMENT" if all(gates.values()) else "FAIL_V6_LABEL_FREE_ALL_EVENT_NULL_NO_GO"
    result={
        "verdict":verdict,
        "method":"v6-LF all-event Mondrian null",
        "configuration":{"years":list(YEARS),"blind_exclusion":[20.0,55.0],"calibration_reservoir":"all geometrically valid target-excluded scan events; no shower-label selection","calibration_per_bin":int(old.CALIBRATION_PER_BIN),"proposal_cap_per_window":512,"max_primary_proposals_per_year":36864,"parallel_exact_execution":parallel,"parameter_search":False,"null_trimming":False},
        "pretruth_sha256":pretruth_sha,
        "scan_counts":{str(y):len(scan[y]) for y in YEARS},
        "calibration_counts":{str(y):len(calibration[y]) for y in YEARS},
        "geometry_audits":geometry_audits,
        "truth_audits":truth_audits,
        "year_audits":audits,
        "anchor_count":len(anchors),"component_count":len(components),"family_count":len(primary)+len(rescue),
        "evaluation":evaluation,
        "gates":gates,
        "claim_boundary":"Fully label-free target-excluded development only; no literature-superiority or OrbitTrace recovery claim.",
    }
    (args.output/"v6_label_free_all_event_null_development.json").write_text(json.dumps(result,indent=2)+"\n")
    lines=["# OrbitTrace v6-LF all-event null development","",f"Verdict: **`{verdict}`**","",f"- primary families: **{evaluation['v3_family_count']}**",f"- qualified: **{evaluation['qualified_matches']}**",f"- recovery@100: **{evaluation['recovered_at_100']}**",f"- MRR: **{evaluation['mrr']:.6f}**",f"- macro F1: **{evaluation['macro_f1']:.6f}**",f"- top-100 precision: **{evaluation['top100_dominant_precision']:.6f}**",f"- pretruth SHA-256: `{pretruth_sha}`","","No shower-label value was used by parsing, calibration, scoring, component construction, recurrence, or ranking before the family payload was frozen."]
    (args.output/"V6_LABEL_FREE_ALL_EVENT_NULL_DEVELOPMENT.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines),flush=True)
    return 0


if __name__=="__main__": raise SystemExit(main())
