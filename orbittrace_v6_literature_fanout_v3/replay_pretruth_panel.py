from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from collections import defaultdict
from pathlib import Path
from typing import Any

from orbittrace_v6_literature_fanout_v3.panel_common import canonical_sha, materialize, require
from orbittrace_v6_literature_fanout_v3.record_slice_scheduler import build_record_slices


def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser(); p.add_argument("--panel",required=True,choices=("hdbscan","sugar")); p.add_argument("--year",required=True,type=int,choices=(2023,2025)); p.add_argument("--preexact",required=True,type=Path); p.add_argument("--exact-dir",required=True,type=Path)
    p.add_argument("--v6-source",required=True,type=Path); p.add_argument("--base-runner",required=True,type=Path); p.add_argument("--exact-row-runner",required=True,type=Path); p.add_argument("--id-manifest",required=True,type=Path); p.add_argument("--support-source-parts",required=True,type=Path); p.add_argument("--candidate-payload",required=True,type=Path); p.add_argument("--baseline-payload",required=True,type=Path); p.add_argument("--scorer-parts",required=True,type=Path); p.add_argument("--archive",required=True,type=Path); p.add_argument("--output",required=True,type=Path); return p.parse_args()


def load_pickle(path:Path)->tuple[Any,str]:
    raw=path.read_bytes(); side=path.with_suffix(".sha256"); require(side.exists(),f"missing SHA {path.name}"); digest=hashlib.sha256(raw).hexdigest(); require(digest==side.read_text().strip(),f"SHA mismatch {path.name}"); return pickle.loads(raw),digest


def exact_scientific_signature(records:list[dict[str,Any]])->list[tuple[str,int,float]]:
    return [(str(r["proposal_anchor_id"]),int(r["bin"]),float(r["window_center"])) for r in records]


def align_outputs(outputs:list[dict[str,Any]],records:list[dict[str,Any]],center:float)->tuple[list[dict[str,Any]],bool]:
    expected=[str(r["proposal_anchor_id"]) for r in records]; actual=[str(r["proposal_anchor_id"]) for r in outputs]
    require(len(expected)==len(set(expected)),f"duplicate proposal anchor center {center}"); require(len(actual)==len(set(actual)),f"duplicate exact output anchor center {center}"); require(len(actual)==len(expected) and set(actual)==set(expected),f"exact output proposal set changed center {center}")
    if actual==expected: return outputs,False
    by_id={str(r["proposal_anchor_id"]):r for r in outputs}; aligned=[by_id[event_id] for event_id in expected]; require([str(r["proposal_anchor_id"]) for r in aligned]==expected,f"exact alignment failed center {center}"); return aligned,True


def main()->int:
    args=parse_args(); args.output.parent.mkdir(parents=True,exist_ok=True); pre,pre_sha=load_pickle(args.preexact)
    require(pre["format"]=="orbittrace-v6-matched-literature-preexact-v3" and pre["panel"]==args.panel and int(pre["year"])==args.year,"wrong preexact identity")
    files=sorted(args.exact_dir.glob(f"exact_{args.panel}_{args.year}_*.pkl")); require(bool(files),"no exact slice artifacts")
    shard_count=None; seen=set(); by_center:dict[float,list[dict[str,Any]]]=defaultdict(list); declared_loads=None
    for path in files:
        obj,_=load_pickle(path); require(obj["format"]=="orbittrace-v6-matched-literature-exact-slice-v3" and obj["panel"]==args.panel and int(obj["year"])==args.year,"wrong slice identity"); require(obj["preexact_sha256"]==pre_sha and obj["id_manifest_sha256"]==pre["id_manifest_sha256"],"slice input identity changed"); require(obj["firewall"]["truth_accessed"] is False and obj["firewall"]["competitor_cluster_labels_accessed"] is False,"slice truth firewall failed")
        current_count=int(obj["shard_count"]); shard_count=current_count if shard_count is None else shard_count; require(current_count==shard_count,"mixed shard counts"); idx=int(obj["shard_index"]); require(idx not in seen,"duplicate shard index"); seen.add(idx); loads=[int(v) for v in obj["estimated_loads"]]; declared_loads=loads if declared_loads is None else declared_loads; require(loads==declared_loads,"slice schedules differ")
        for item in obj["slices"]: by_center[float(item["center"])].append(item)
    require(shard_count is not None and seen==set(range(shard_count)),f"incomplete exact shards {seen}"); _bins,expected_loads=build_record_slices(pre,shard_count); require(declared_loads==expected_loads,"record-slice schedule changed")
    exact_by_center={}
    for center in [float(c) for c in pre["ordered_centers"]]:
        records=pre["centers"][center]["records"]; items=sorted(by_center.get(center,[]),key=lambda x:int(x["record_start"])); require(bool(items),f"missing center {center}"); cursor=0; outputs=[]
        for item in items:
            start=int(item["record_start"]); stop=int(item["record_stop"]); require(start==cursor and stop>start,f"slice gap/overlap center {center}"); expected=records[start:stop]; require(canonical_sha(expected)==item["records_sha256"],f"slice input hash mismatch center {center}"); exact=item["outputs"]; require([str(r["proposal_anchor_id"]) for r in exact]==[str(r["proposal_anchor_id"]) for r in expected],f"slice output order changed center {center}"); outputs.extend(exact); cursor=stop
        require(cursor==len(records),f"incomplete center {center}"); require([str(r["proposal_anchor_id"]) for r in outputs]==[str(r["proposal_anchor_id"]) for r in records],f"assembled exact order changed center {center}"); exact_by_center[center]=outputs

    ctx=materialize(args,f"replay_{args.panel}_{args.year}"); require(ctx["manifest_sha"]==pre["id_manifest_sha256"],"manifest identity changed"); require(canonical_sha(ctx["scan_events"])==pre["scan_rows_sha256"] and canonical_sha(ctx["calibration"])==pre["calibration_rows_sha256"],"panel rows changed before replay")
    v6=ctx["v6"]; original=v6.exact_rescore_window_v6; replayed=[]; drift=[]; realigned=[]
    def replay(old_arg,records,window_events,event_lookup,support_arg,base_arg):
        del old_arg,event_lookup,support_arg,base_arg
        require(bool(records),"empty replay exact call"); center=float(records[0]["window_center"]); require(center not in replayed and center in pre["centers"],f"unexpected replay center {center}"); spec=pre["centers"][center]; captured=spec["records"]
        current_sig=exact_scientific_signature(records); captured_sig=exact_scientific_signature(captured); require(current_sig==captured_sig,f"scientific proposal identity changed center {center}")
        if canonical_sha(records)!=spec["records_sha256"]: drift.append(center); print(f"LIT_FANOUT_NONSEMANTIC_RECORD_DRIFT panel={args.panel} year={args.year} center={center:.1f}",flush=True)
        ids=[str(e["id"]) for e in window_events]; require(canonical_sha(ids)==spec["window_event_ids_sha256"],f"window changed center {center}")
        outputs,changed=align_outputs(exact_by_center[center],records,center); require(exact_scientific_signature(outputs)==current_sig,f"saved exact scientific identity changed center {center}")
        if changed: realigned.append(center); print(f"LIT_FANOUT_REALIGNED_BY_ANCHOR panel={args.panel} year={args.year} center={center:.1f}",flush=True)
        replayed.append(center); return outputs
    v6.exact_rescore_window_v6=replay
    try: audit,anchors,components=v6.scan_year_v6(ctx["old"],args.year,ctx["scan_events"],ctx["calibration"],ctx["candidate"],ctx["base"],ctx["scorer"],ctx["support"])
    finally: v6.exact_rescore_window_v6=original
    require(replayed==[float(c) for c in pre["ordered_centers"]],"replay center order changed"); require(len(audit["supported_bins"])>=30,"insufficient supported calibration bins"); require(audit["proposal_cap_per_window"]==512 and audit["max_primary_proposals_per_year"]==36864,"proposal budget changed")
    checkpoint={"classification":"v6 exact-row pretruth panel-year checkpoint","panel":args.panel,"year":args.year,"id_manifest_sha256":pre["id_manifest_sha256"],"blind_exclusion":[20.0,55.0],"truth_accessed":False,"mapping_accessed":False,"competitor_cluster_labels_accessed":False,"scan_count":pre["scan_count"],"calibration_count":pre["calibration_count"],"execution":{"record_slice_fanout_v3":True,"shard_count":shard_count,"estimated_shard_costs":declared_loads,"preexact_sha256":pre_sha,"scientific_signature_guard":["proposal_anchor_id","bin","window_center"],"nonsemantic_record_drift_centers":drift,"realigned_centers":realigned},"audit":audit,"anchors":anchors,"components":components}
    raw=pickle.dumps(checkpoint,protocol=pickle.HIGHEST_PROTOCOL); args.output.write_bytes(raw); digest=hashlib.sha256(raw).hexdigest(); args.output.with_suffix(args.output.suffix+".sha256").write_text(digest+"\n"); print(f"PASS_LITERATURE_FANOUT_REPLAY panel={args.panel} year={args.year} anchors={len(anchors)} components={len(components)} drift={len(drift)} realigned={len(realigned)} sha={digest}",flush=True); return 0

if __name__=="__main__": raise SystemExit(main())
