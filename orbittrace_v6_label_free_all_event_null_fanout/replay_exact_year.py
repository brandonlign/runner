from __future__ import annotations

import argparse
import hashlib
import json
import math
import pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_label_free_all_event_null import run_development as lf

FLOAT_REL_TOL=1e-12
FLOAT_ABS_TOL=1e-12


def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser()
    p.add_argument("--year",required=True,type=int,choices=lf.YEARS)
    p.add_argument("--preexact-checkpoint",required=True,type=Path)
    p.add_argument("--exact-shards-dir",required=True,type=Path)
    p.add_argument("--repaired-v6-source",required=True,type=Path)
    p.add_argument("--base-runner",required=True,type=Path)
    p.add_argument("--support-source-parts",required=True,type=Path)
    p.add_argument("--candidate-payload",required=True,type=Path)
    p.add_argument("--baseline-payload",required=True,type=Path)
    p.add_argument("--scorer-parts",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    return p.parse_args()


def load_pickle(path:Path)->tuple[Any,str]:
    raw=path.read_bytes(); side=path.with_suffix(".sha256")
    lf.require(side.exists(),f"missing SHA sidecar {path.name}")
    digest=hashlib.sha256(raw).hexdigest(); lf.require(digest==side.read_text().strip().split()[0],f"SHA mismatch {path.name}")
    return pickle.loads(raw),digest


def semantic_record_equivalence(captured:Any,replayed:Any,center:float)->dict[str,Any]:
    """Require exact proposal structure; permit only machine-precision float drift."""
    stats={"float_values":0,"max_abs_float_delta":0.0,"max_rel_float_delta":0.0}
    def compare(a:Any,b:Any,path:str)->None:
        if isinstance(a,bool) or isinstance(b,bool):
            lf.require(type(a) is type(b) and a==b,f"semantic boolean mismatch center {center} path {path}: {a!r} != {b!r}"); return
        if isinstance(a,float) or isinstance(b,float):
            lf.require(isinstance(a,(int,float)) and isinstance(b,(int,float)),f"semantic numeric type mismatch center {center} path {path}")
            af=float(a); bf=float(b); lf.require(math.isfinite(af) and math.isfinite(bf),f"nonfinite proposal float center {center} path {path}")
            delta=abs(af-bf); scale=max(abs(af),abs(bf),FLOAT_ABS_TOL); rel=delta/scale
            stats["float_values"]+=1; stats["max_abs_float_delta"]=max(float(stats["max_abs_float_delta"]),delta); stats["max_rel_float_delta"]=max(float(stats["max_rel_float_delta"]),rel)
            lf.require(math.isclose(af,bf,rel_tol=FLOAT_REL_TOL,abs_tol=FLOAT_ABS_TOL),f"semantic float mismatch center {center} path {path}: captured={af:.17g} replayed={bf:.17g} abs={delta:.3g} rel={rel:.3g}"); return
        if isinstance(a,dict) or isinstance(b,dict):
            lf.require(isinstance(a,dict) and isinstance(b,dict),f"semantic dict type mismatch center {center} path {path}")
            lf.require(set(a)==set(b),f"semantic dict keys mismatch center {center} path {path}: {sorted(set(a)^set(b))}")
            for key in sorted(a,key=str): compare(a[key],b[key],f"{path}.{key}")
            return
        if isinstance(a,(list,tuple)) or isinstance(b,(list,tuple)):
            lf.require(isinstance(a,(list,tuple)) and isinstance(b,(list,tuple)),f"semantic sequence type mismatch center {center} path {path}")
            lf.require(len(a)==len(b),f"semantic sequence length mismatch center {center} path {path}: {len(a)} != {len(b)}")
            for index,(av,bv) in enumerate(zip(a,b)): compare(av,bv,f"{path}[{index}]")
            return
        lf.require(type(a) is type(b) and a==b,f"semantic value mismatch center {center} path {path}: {a!r} != {b!r}")
    compare(captured,replayed,"records")
    return stats


def align_exact_outputs_to_records(outputs:list[dict[str,Any]],records:list[dict[str,Any]],center:float)->tuple[list[dict[str,Any]],bool]:
    expected=[str(r["proposal_anchor_id"]) for r in records]; actual=[str(r["proposal_anchor_id"]) for r in outputs]
    lf.require(len(expected)==len(set(expected)),f"duplicate captured proposal anchor center {center}")
    lf.require(len(actual)==len(set(actual)),f"duplicate exact output proposal anchor center {center}")
    lf.require(len(actual)==len(expected) and set(actual)==set(expected),f"exact output proposal set changed center {center}")
    if actual==expected: return outputs,False
    by_anchor={str(r["proposal_anchor_id"]):r for r in outputs}; aligned=[by_anchor[event_id] for event_id in expected]
    lf.require([str(r["proposal_anchor_id"]) for r in aligned]==expected,f"exact output realignment failed center {center}")
    return aligned,True


def main()->int:
    args=parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    pre,pre_sha=load_pickle(args.preexact_checkpoint)
    lf.require(pre["format"]=="orbittrace-v6-lf-preexact-fanout-v1" and int(pre["year"])==args.year,"preexact identity mismatch")
    lf.require(pre["firewall"]["label_values_not_accessed"] is True and pre["firewall"]["all_event_calibration"] is True,"preexact firewall mismatch")
    paths=sorted(args.exact_shards_dir.glob(f"v6_lf_exact_{args.year}_shard_*.pkl")); lf.require(bool(paths),"no exact shard files")
    exact_by_center={}; shard_count=None; seen=set()
    for path in paths:
        shard,_=load_pickle(path)
        lf.require(shard["format"]=="orbittrace-v6-lf-exact-shard-v1" and int(shard["year"])==args.year,f"shard identity changed {path.name}")
        lf.require(shard["preexact_sha256"]==pre_sha and shard["scan_rows_sha256"]==pre["scan_rows_sha256"],f"shard/preexact mismatch {path.name}")
        lf.require(shard["firewall"]["label_values_not_accessed"] is True,f"shard label firewall failed {path.name}")
        count=int(shard["shard_count"]); shard_count=count if shard_count is None else shard_count; lf.require(count==shard_count,"mixed shard counts")
        index=int(shard["shard_index"]); lf.require(index not in seen,f"duplicate shard index {index}"); seen.add(index)
        for center in shard["centers"]:
            center=float(center); lf.require(center not in exact_by_center,f"duplicate exact center {center}"); exact_by_center[center]=shard["exact_by_center"][center]
    lf.require(shard_count is not None and seen==set(range(shard_count)),f"incomplete shards {sorted(seen)} / {shard_count}")
    ordered=[float(c) for c in pre["ordered_centers"]]; lf.require(set(exact_by_center)==set(ordered),"center coverage mismatch")

    lf.require(lf.sha256_path(args.repaired_v6_source)==lf.REPAIRED_V6_SHA256==pre["repaired_v6_sha256"],"repaired source mismatch")
    v6=lf.load_module(args.repaired_v6_source,f"orbittrace_v6_lf_replay_{args.year}")
    old=v6.load_base_runner(args.base_runner); support=old.load_support_module(args.support_source_parts); candidate,base,scorer=support.load_sources(args)
    scan_by_year,cal_by_year,geometry_audits,_ids=lf.parse_geometry_only(support,base)
    scan=scan_by_year[args.year]; calibration=cal_by_year[args.year]
    lf.require(lf.canonical_sha(scan)==pre["scan_rows_sha256"],"scan changed before replay")
    lf.require(lf.canonical_sha(calibration)==pre["calibration_rows_sha256"],"calibration changed before replay")
    audit_rows=[a for a in geometry_audits if str(a["key"]).startswith(str(args.year))]
    audit_sha=hashlib.sha256(json.dumps(audit_rows,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
    lf.require(audit_sha==pre["geometry_audit_sha256"],"geometry parser audit changed before replay")

    original=v6.exact_rescore_window_v6; replayed=[]; semantic_fallback_centers=[]; realigned_centers=[]; max_abs_float_delta=0.0; max_rel_float_delta=0.0
    def replay(old_arg,records,window_events,event_lookup,support_arg,base_arg):
        nonlocal max_abs_float_delta,max_rel_float_delta
        del old_arg,event_lookup,support_arg,base_arg
        lf.require(bool(records),"empty replay exact call")
        center=float(records[0]["window_center"]); lf.require(center in pre["centers"] and center not in replayed,f"unexpected/duplicate center {center}")
        spec=pre["centers"][center]; captured=spec["records"]
        if lf.canonical_sha(records)!=spec["records_sha256"]:
            stats=semantic_record_equivalence(captured,records,center); semantic_fallback_centers.append(center)
            max_abs_float_delta=max(max_abs_float_delta,float(stats["max_abs_float_delta"])); max_rel_float_delta=max(max_rel_float_delta,float(stats["max_rel_float_delta"]))
            print(f"V6_LF_REPLAY_SEMANTIC_EQUIVALENCE year={args.year} center={center:.1f} float_values={stats['float_values']} max_abs={stats['max_abs_float_delta']:.3g} max_rel={stats['max_rel_float_delta']:.3g}",flush=True)
        lf.require([str(r["proposal_anchor_id"]) for r in records]==[str(r["proposal_anchor_id"]) for r in captured],f"replay/captured proposal order mismatch center {center}")
        ids=[str(e["id"]) for e in window_events]; lf.require(lf.canonical_sha(ids)==spec["window_event_ids_sha256"],f"window changed center {center}")
        outputs,realigned=align_exact_outputs_to_records(exact_by_center[center],captured,center)
        if realigned:
            realigned_centers.append(center); print(f"V6_LF_REPLAY_REALIGNED_BY_CAPTURED_ANCHOR year={args.year} center={center:.1f}",flush=True)
        replayed.append(center); return outputs
    v6.exact_rescore_window_v6=replay
    try:
        audit,anchors,components=v6.scan_year_v6(old,args.year,scan,calibration,candidate,base,scorer,support)
    finally:
        v6.exact_rescore_window_v6=original
    lf.require(replayed==ordered,"replay center order changed")
    lf.require(int(audit["scan_events"])==len(scan)==len(calibration)==int(audit["calibration_events"]),"all-event year counts changed")
    lf.require(int(audit["proposal_cap_per_window"])==512 and int(audit["max_primary_proposals_per_year"])==36864,"proposal budget changed")
    checkpoint={"format":"orbittrace-v6-lf-year-checkpoint-v1","year":args.year,"repaired_v6_sha256":lf.REPAIRED_V6_SHA256,"scan_rows_sha256":pre["scan_rows_sha256"],"calibration_rows_sha256":pre["calibration_rows_sha256"],"geometry_audit_sha256":pre["geometry_audit_sha256"],"execution":{"exact_fanout":True,"exact_shard_count":shard_count,"preexact_sha256":pre_sha,"semantic_record_equivalence_fallback":True,"semantic_float_rel_tol":FLOAT_REL_TOL,"semantic_float_abs_tol":FLOAT_ABS_TOL,"semantic_fallback_center_count":len(semantic_fallback_centers),"semantic_fallback_centers":semantic_fallback_centers,"max_abs_float_delta":max_abs_float_delta,"max_rel_float_delta":max_rel_float_delta,"realigned_center_count":len(realigned_centers),"realigned_centers":realigned_centers},"audit":audit,"anchors":anchors,"components":components,"firewall":{"target_interval_remains_excluded":True,"label_values_not_accessed":True,"all_event_calibration":True,"scientific_result_not_evaluated":True}}
    raw=pickle.dumps(checkpoint,protocol=pickle.HIGHEST_PROTOCOL); path=args.output/f"v6_lf_year_{args.year}.pkl"; path.write_bytes(raw)
    digest=hashlib.sha256(raw).hexdigest(); path.with_suffix(".sha256").write_text(digest+"\n")
    (args.output/f"v6_lf_year_{args.year}.json").write_text(json.dumps({"year":args.year,"checkpoint_sha256":digest,"anchors":len(anchors),"components":len(components),"exact_shard_count":shard_count,"preexact_sha256":pre_sha,"semantic_fallback_center_count":len(semantic_fallback_centers),"semantic_fallback_centers":semantic_fallback_centers,"max_abs_float_delta":max_abs_float_delta,"max_rel_float_delta":max_rel_float_delta,"realigned_center_count":len(realigned_centers),"realigned_centers":realigned_centers},indent=2,sort_keys=True)+"\n")
    print(f"PASS_V6_LF_YEAR_REPLAY year={args.year} anchors={len(anchors)} components={len(components)} semantic_fallback_centers={len(semantic_fallback_centers)} realigned_centers={len(realigned_centers)} sha={digest}",flush=True)
    return 0


if __name__=="__main__": raise SystemExit(main())
