from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_label_free_all_event_null import run_development as lf
from orbittrace_v6_label_free_all_event_null.parallel_exact_rescore import install


def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser()
    p.add_argument("--year",required=True,type=int,choices=lf.YEARS)
    p.add_argument("--shard-index",required=True,type=int)
    p.add_argument("--shard-count",required=True,type=int)
    p.add_argument("--workers",type=int,default=4)
    p.add_argument("--preexact-checkpoint",required=True,type=Path)
    p.add_argument("--repaired-v6-source",required=True,type=Path)
    p.add_argument("--base-runner",required=True,type=Path)
    p.add_argument("--support-source-parts",required=True,type=Path)
    p.add_argument("--candidate-payload",required=True,type=Path)
    p.add_argument("--baseline-payload",required=True,type=Path)
    p.add_argument("--scorer-parts",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    return p.parse_args()


def load_pre(path:Path,year:int)->tuple[dict[str,Any],str]:
    raw=path.read_bytes(); side=path.with_suffix(".sha256")
    lf.require(side.exists(),"missing preexact sidecar")
    digest=hashlib.sha256(raw).hexdigest(); lf.require(digest==side.read_text().strip().split()[0],"preexact SHA mismatch")
    obj=pickle.loads(raw)
    lf.require(obj["format"]=="orbittrace-v6-lf-preexact-fanout-v1","preexact format mismatch")
    lf.require(int(obj["year"])==year,"preexact year mismatch")
    lf.require(obj["firewall"]["label_values_not_accessed"] is True,"preexact label firewall failed")
    lf.require(obj["firewall"]["all_event_calibration"] is True,"preexact calibration identity failed")
    return obj,digest


def balanced(pre:dict[str,Any],count:int)->tuple[list[list[float]],list[int]]:
    lf.require(count>0,"shard count must be positive")
    bins=[[] for _ in range(count)]; loads=[0 for _ in range(count)]
    items=[(float(c),len(pre["centers"][float(c)]["records"])) for c in pre["ordered_centers"]]
    for center,n in sorted(items,key=lambda x:(-x[1],x[0])):
        target=min(range(count),key=lambda i:(loads[i],i)); bins[target].append(center); loads[target]+=n
    for values in bins: values.sort()
    lf.require(sorted(c for values in bins for c in values)==sorted(c for c,_ in items),"shard coverage changed")
    return bins,loads


def main()->int:
    args=parse_args(); lf.require(args.shard_count>0 and 0<=args.shard_index<args.shard_count,"invalid shard index")
    args.output.mkdir(parents=True,exist_ok=True)
    pre,pre_sha=load_pre(args.preexact_checkpoint,args.year)
    lf.require(lf.sha256_path(args.repaired_v6_source)==lf.REPAIRED_V6_SHA256==pre["repaired_v6_sha256"],"repaired source mismatch")
    v6=lf.load_module(args.repaired_v6_source,f"orbittrace_v6_lf_exact_{args.year}_{args.shard_index}")
    old=v6.load_base_runner(args.base_runner); support=old.load_support_module(args.support_source_parts)
    _candidate,base,_scorer=support.load_sources(args)
    scan_by_year,cal_by_year,_audits,_ids=lf.parse_geometry_only(support)
    scan=scan_by_year[args.year]; calibration=cal_by_year[args.year]
    lf.require(lf.canonical_sha(scan)==pre["scan_rows_sha256"],"scan input changed")
    lf.require(lf.canonical_sha(calibration)==pre["calibration_rows_sha256"],"calibration input changed")
    lf.require(len(scan)==len(calibration),"all-event calibration count changed")
    event_lookup={str(e["id"]):e for e in scan}
    config=install(v6,workers=args.workers,min_parallel_records=256)
    shards,loads=balanced(pre,args.shard_count); selected=shards[args.shard_index]
    lf.require(bool(selected),"empty shard")
    print(f"V6_LF_FANOUT_BALANCE year={args.year} loads={loads} selected_load={loads[args.shard_index]}",flush=True)
    exact_by_center={}
    for center in selected:
        spec=pre["centers"][center]; records=spec["records"]
        lf.require(lf.canonical_sha(records)==spec["records_sha256"],f"record hash changed center {center}")
        ids=[str(x) for x in spec["window_event_ids"]]
        lf.require(lf.canonical_sha(ids)==spec["window_event_ids_sha256"],f"window ID hash changed center {center}")
        lf.require(all(eid in event_lookup for eid in ids),f"window event missing center {center}")
        window=[event_lookup[eid] for eid in ids]
        canonical=old.window_events_for_center(scan,center,base)
        lf.require([str(e["id"]) for e in canonical]==ids,f"window reconstruction changed center {center}")
        outputs=v6.exact_rescore_window_v6(old,records,window,event_lookup,support,base)
        lf.require([str(r["proposal_anchor_id"]) for r in outputs]==[str(r["proposal_anchor_id"]) for r in records],f"exact output order changed center {center}")
        exact_by_center[center]=outputs
        print(f"V6_LF_EXACT_DONE year={args.year} shard={args.shard_index}/{args.shard_count} center={center:.1f} records={len(records):,}",flush=True)
    payload={"format":"orbittrace-v6-lf-exact-shard-v1","year":args.year,"shard_index":args.shard_index,"shard_count":args.shard_count,"preexact_sha256":pre_sha,"scan_rows_sha256":pre["scan_rows_sha256"],"centers":selected,"scheduled_proposals":loads[args.shard_index],"all_shard_loads":loads,"exact_by_center":exact_by_center,"executor":config,"firewall":{"target_interval_remains_excluded":True,"label_values_not_accessed":True}}
    raw=pickle.dumps(payload,protocol=pickle.HIGHEST_PROTOCOL)
    path=args.output/f"v6_lf_exact_{args.year}_shard_{args.shard_index:02d}.pkl"; path.write_bytes(raw)
    digest=hashlib.sha256(raw).hexdigest(); path.with_suffix(".sha256").write_text(digest+"\n")
    print(f"PASS_V6_LF_EXACT_SHARD year={args.year} shard={args.shard_index}/{args.shard_count} proposals={loads[args.shard_index]:,} sha={digest}",flush=True)
    return 0


if __name__=="__main__": raise SystemExit(main())
