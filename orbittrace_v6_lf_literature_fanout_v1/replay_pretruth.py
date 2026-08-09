from __future__ import annotations

import argparse
import hashlib
import math
import pickle
from collections import defaultdict
from pathlib import Path
from typing import Any

from orbittrace_v6_lf_literature_fanout_v1.common import canonical_sha, materialize, require
from orbittrace_v6_lf_literature_fanout_v1.scheduler import build_slices

REL_TOL=1e-12
ABS_TOL=1e-12


def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser(); p.add_argument("--panel",required=True,choices=("hdbscan","sugar")); p.add_argument("--year",required=True,type=int,choices=(2023,2025)); p.add_argument("--preexact",required=True,type=Path); p.add_argument("--exact-dir",required=True,type=Path)
    p.add_argument("--v6-source",required=True,type=Path); p.add_argument("--base-runner",required=True,type=Path); p.add_argument("--exact-row-runner",required=True,type=Path); p.add_argument("--id-manifest",required=True,type=Path); p.add_argument("--support-source-parts",required=True,type=Path); p.add_argument("--candidate-payload",required=True,type=Path); p.add_argument("--baseline-payload",required=True,type=Path); p.add_argument("--scorer-parts",required=True,type=Path); p.add_argument("--archive",required=True,type=Path); p.add_argument("--output",required=True,type=Path); return p.parse_args()


def load_pickle(path:Path)->tuple[Any,str]:
    raw=path.read_bytes(); side=path.with_suffix(".sha256"); require(side.exists(),f"missing SHA {path.name}"); digest=hashlib.sha256(raw).hexdigest(); require(digest==side.read_text().strip(),f"SHA mismatch {path.name}"); return pickle.loads(raw),digest


def semantic_equal(captured:Any,current:Any,center:float)->dict[str,float|int]:
    stats={"floats":0,"max_abs":0.0,"max_rel":0.0}
    def compare(a:Any,b:Any,path:str)->None:
        if isinstance(a,bool) or isinstance(b,bool): require(type(a) is type(b) and a==b,f"bool mismatch center {center} {path}"); return
        if isinstance(a,float) or isinstance(b,float):
            require(isinstance(a,(int,float)) and isinstance(b,(int,float)),f"numeric type mismatch center {center} {path}"); af=float(a); bf=float(b); require(math.isfinite(af) and math.isfinite(bf),f"nonfinite float center {center} {path}"); delta=abs(af-bf); scale=max(abs(af),abs(bf),ABS_TOL); rel=delta/scale; stats["floats"]+=1; stats["max_abs"]=max(float(stats["max_abs"]),delta); stats["max_rel"]=max(float(stats["max_rel"]),rel); require(math.isclose(af,bf,rel_tol=REL_TOL,abs_tol=ABS_TOL),f"float mismatch center {center} {path} abs={delta} rel={rel}"); return
        if isinstance(a,dict) or isinstance(b,dict): require(isinstance(a,dict) and isinstance(b,dict) and set(a)==set(b),f"dict mismatch center {center} {path}"); [compare(a[key],b[key],f"{path}.{key}") for key in sorted(a,key=str)]; return
        if isinstance(a,(list,tuple)) or isinstance(b,(list,tuple)): require(isinstance(a,(list,tuple)) and isinstance(b,(list,tuple)) and len(a)==len(b),f"sequence mismatch center {center} {path}"); [compare(av,bv,f"{path}[{idx}]") for idx,(av,bv) in enumerate(zip(a,b))]; return
        require(type(a) is type(b) and a==b,f"value mismatch center {center} {path}: {a!r} != {b!r}")
    compare(captured,current,"records"); return stats


def main()->int:
    args=parse_args(); pre,pre_sha=load_pickle(args.preexact); require(pre["format"]=="orbittrace-v6-lf-literature-preexact-v1" and pre["panel"]==args.panel and int(pre["year"])==args.year,"preexact identity changed")
    paths=sorted(args.exact_dir.glob(f"exact_{args.panel}_{args.year}_*.pkl")); require(bool(paths),"no exact slice files"); shard_count=None; seen=set(); items=defaultdict(list); declared_loads=None
    for path in paths:
        obj,_=load_pickle(path); require(obj["format"]=="orbittrace-v6-lf-literature-exact-slice-v1" and obj["panel"]==args.panel and int(obj["year"])==args.year,"slice identity changed"); require(obj["preexact_sha256"]==pre_sha and obj["id_manifest_sha256"]==pre["id_manifest_sha256"],"slice input changed")
        firewall=obj["firewall"]; require(all(firewall[key] is False for key in ("truth_accessed","mapping_accessed","competitor_cluster_labels_accessed","native_background_membership_used_for_calibration")) and firewall["target_interval_remains_excluded"] is True,"slice firewall failed")
        count=int(obj["shard_count"]); shard_count=count if shard_count is None else shard_count; require(count==shard_count,"mixed shard count"); idx=int(obj["shard_index"]); require(idx not in seen,"duplicate shard index"); seen.add(idx); loads=[int(v) for v in obj["estimated_loads"]]; declared_loads=loads if declared_loads is None else declared_loads; require(loads==declared_loads,"schedule changed")
        for item in obj["slices"]: items[float(item["center"])].append(item)
    require(shard_count is not None and seen==set(range(shard_count)),f"incomplete shards {seen}"); _bins,expected_loads=build_slices(pre,shard_count); require(declared_loads==expected_loads,"deterministic schedule changed")
    exact_by_center={}
    for raw_center in pre["ordered_centers"]:
        center=float(raw_center); records=pre["centers"][center]["records"]; parts=sorted(items.get(center,[]),key=lambda value:int(value["record_start"])); require(bool(parts),f"missing center {center}"); cursor=0; outputs=[]
        for part in parts:
            start=int(part["record_start"]); stop=int(part["record_stop"]); require(start==cursor and stop>start,f"slice gap center {center}"); expected=records[start:stop]; require(canonical_sha(expected)==part["records_sha256"],f"slice record hash changed center {center}"); exact=part["outputs"]; require([str(r["proposal_anchor_id"]) for r in exact]==[str(r["proposal_anchor_id"]) for r in expected],f"slice output order changed center {center}"); outputs.extend(exact); cursor=stop
        require(cursor==len(records),f"incomplete center {center}"); exact_by_center[center]=outputs

    ctx=materialize(args,f"replay_{args.panel}_{args.year}"); require(ctx["manifest_sha"]==pre["id_manifest_sha256"],"manifest changed"); require(canonical_sha(ctx["scan_events"])==pre["scan_rows_sha256"] and canonical_sha(ctx["calibration"])==pre["calibration_rows_sha256"],"panel rows changed")
    v6=ctx["v6"]; original=v6.exact_rescore_window_v6; replayed=[]; drift=[]; max_abs=0.0; max_rel=0.0
    def replay(_old,records,window_events,_lookup,_support,_base):
        nonlocal max_abs,max_rel
        require(bool(records),"empty replay exact call"); center=float(records[0]["window_center"]); require(center in pre["centers"] and center not in replayed,f"unexpected center {center}"); spec=pre["centers"][center]; captured=spec["records"]
        if canonical_sha(records)!=spec["records_sha256"]:
            stats=semantic_equal(captured,records,center); drift.append(center); max_abs=max(max_abs,float(stats["max_abs"])); max_rel=max(max_rel,float(stats["max_rel"])); print(f"V6_LF_LIT_SEMANTIC_REPLAY panel={args.panel} year={args.year} center={center:.1f} max_abs={stats['max_abs']:.3g} max_rel={stats['max_rel']:.3g}",flush=True)
        require([str(r["proposal_anchor_id"]) for r in records]==[str(r["proposal_anchor_id"]) for r in captured],f"proposal order changed center {center}"); ids=[str(e["id"]) for e in window_events]; require(canonical_sha(ids)==spec["window_event_ids_sha256"],f"window changed center {center}"); outputs=exact_by_center[center]; require([str(r["proposal_anchor_id"]) for r in outputs]==[str(r["proposal_anchor_id"]) for r in captured],f"exact output order changed center {center}"); replayed.append(center); return outputs
    v6.exact_rescore_window_v6=replay
    try: audit,anchors,components=v6.scan_year_v6(ctx["old"],args.year,ctx["scan_events"],ctx["calibration"],ctx["candidate"],ctx["base"],ctx["scorer"],ctx["support"])
    finally: v6.exact_rescore_window_v6=original
    require(replayed==[float(c) for c in pre["ordered_centers"]],"replay center order changed"); require(len(audit["supported_bins"])>=30,"insufficient calibration bins"); require(audit["proposal_cap_per_window"]==512 and audit["max_primary_proposals_per_year"]==36864,"proposal budget changed"); require(int(audit["calibration_events"])==len(ctx["scan_events"]),"all-event calibration identity changed")
    checkpoint={"classification":"v6 exact-row pretruth panel-year checkpoint","method_variant":"v6-LF all-event Mondrian null","panel":args.panel,"year":args.year,"id_manifest_sha256":pre["id_manifest_sha256"],"blind_exclusion":[20.0,55.0],"truth_accessed":False,"mapping_accessed":False,"competitor_cluster_labels_accessed":False,"native_background_membership_used_for_calibration":False,"calibration_reservoir":"all exact matched scan rows","scan_count":len(ctx["scan_events"]),"calibration_count":len(ctx["calibration"]),"audit":audit,"anchors":anchors,"components":components,"execution":{"record_slice_fanout":True,"shard_count":shard_count,"estimated_loads":declared_loads,"preexact_sha256":pre_sha,"strict_semantic_replay":True,"rel_tol":REL_TOL,"abs_tol":ABS_TOL,"semantic_drift_centers":drift,"max_abs_float_delta":max_abs,"max_rel_float_delta":max_rel}}
    args.output.parent.mkdir(parents=True,exist_ok=True); raw=pickle.dumps(checkpoint,protocol=pickle.HIGHEST_PROTOCOL); args.output.write_bytes(raw); digest=hashlib.sha256(raw).hexdigest(); args.output.with_suffix(args.output.suffix+".sha256").write_text(digest+"\n"); print(f"PASS_V6_LF_LITERATURE_REPLAY panel={args.panel} year={args.year} anchors={len(anchors)} components={len(components)} drift={len(drift)} sha={digest}",flush=True); return 0

if __name__=="__main__": raise SystemExit(main())
