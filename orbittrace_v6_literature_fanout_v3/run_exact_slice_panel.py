from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_literature_adapter.parallel_exact_rescore import install
from orbittrace_v6_literature_fanout_v3.panel_common import canonical_sha, materialize, require
from orbittrace_v6_literature_fanout_v3.record_slice_scheduler import build_record_slices


def parse_args() -> argparse.Namespace:
    p=argparse.ArgumentParser(); p.add_argument("--panel",required=True,choices=("hdbscan","sugar")); p.add_argument("--year",required=True,type=int,choices=(2023,2025)); p.add_argument("--shard-index",required=True,type=int); p.add_argument("--shard-count",required=True,type=int); p.add_argument("--workers",type=int,default=4); p.add_argument("--preexact",required=True,type=Path)
    p.add_argument("--v6-source",required=True,type=Path); p.add_argument("--base-runner",required=True,type=Path); p.add_argument("--exact-row-runner",required=True,type=Path); p.add_argument("--id-manifest",required=True,type=Path); p.add_argument("--support-source-parts",required=True,type=Path); p.add_argument("--candidate-payload",required=True,type=Path); p.add_argument("--baseline-payload",required=True,type=Path); p.add_argument("--scorer-parts",required=True,type=Path); p.add_argument("--archive",required=True,type=Path); p.add_argument("--output",required=True,type=Path); return p.parse_args()


def load_pre(path:Path)->tuple[dict[str,Any],str]:
    raw=path.read_bytes(); side=path.with_suffix(".sha256"); require(side.exists(),"missing preexact sidecar"); digest=hashlib.sha256(raw).hexdigest(); require(digest==side.read_text().strip(),"preexact SHA mismatch"); return pickle.loads(raw),digest


def main()->int:
    args=parse_args(); args.output.mkdir(parents=True,exist_ok=True); pre,pre_sha=load_pre(args.preexact)
    require(pre["format"]=="orbittrace-v6-matched-literature-preexact-v3" and pre["panel"]==args.panel and int(pre["year"])==args.year,"wrong preexact identity"); require(pre["firewall"]["truth_accessed"] is False and pre["firewall"]["competitor_cluster_labels_accessed"] is False and pre["firewall"]["target_interval_remains_excluded"] is True,"preexact firewall failed")
    ctx=materialize(args,f"slice_{args.panel}_{args.year}_{args.shard_index}"); require(canonical_sha(ctx["scan_events"])==pre["scan_rows_sha256"] and canonical_sha(ctx["calibration"])==pre["calibration_rows_sha256"],"panel rows changed")
    bins,loads=build_record_slices(pre,args.shard_count); require(0<=args.shard_index<args.shard_count,"invalid shard index"); selected=bins[args.shard_index]; require(bool(selected),"empty exact shard")
    v6=ctx["v6"]; old=ctx["old"]; support=ctx["support"]; base=ctx["base"]; lookup={str(e["id"]):e for e in ctx["scan_events"]}; execution=install(v6,workers=args.workers,min_parallel_records=256)
    slices=[]
    for piece in selected:
        center=float(piece["center"]); start=int(piece["record_start"]); stop=int(piece["record_stop"]); spec=pre["centers"][center]; all_records=spec["records"]
        require(canonical_sha(all_records)==spec["records_sha256"],f"records changed center {center}"); ids=[str(v) for v in spec["window_event_ids"]]; require(canonical_sha(ids)==spec["window_event_ids_sha256"],f"window IDs changed center {center}"); window=[lookup[eid] for eid in ids]; require([str(e["id"]) for e in old.window_events_for_center(ctx["scan_events"],center,base)]==ids,f"window reconstruction changed center {center}")
        records=all_records[start:stop]; exact=v6.exact_rescore_window_v6(old,records,window,lookup,support,base); require([str(r["proposal_anchor_id"]) for r in exact]==[str(r["proposal_anchor_id"]) for r in records],f"exact slice order changed center {center}")
        slices.append({"center":center,"record_start":start,"record_stop":stop,"records_sha256":canonical_sha(records),"outputs":exact}); print(f"LIT_FANOUT_SLICE_DONE panel={args.panel} year={args.year} shard={args.shard_index}/{args.shard_count} center={center:.1f} records={len(records):,}",flush=True)
    payload={"format":"orbittrace-v6-matched-literature-exact-slice-v3","panel":args.panel,"year":args.year,"shard_index":args.shard_index,"shard_count":args.shard_count,"preexact_sha256":pre_sha,"id_manifest_sha256":pre["id_manifest_sha256"],"estimated_loads":loads,"slices":slices,"executor":execution,"firewall":{"truth_accessed":False,"competitor_cluster_labels_accessed":False,"target_interval_remains_excluded":True}}
    raw=pickle.dumps(payload,protocol=pickle.HIGHEST_PROTOCOL); path=args.output/f"exact_{args.panel}_{args.year}_{args.shard_index:02d}.pkl"; path.write_bytes(raw); digest=hashlib.sha256(raw).hexdigest(); path.with_suffix(".sha256").write_text(digest+"\n"); print(f"PASS_LITERATURE_FANOUT_EXACT_SLICE panel={args.panel} year={args.year} shard={args.shard_index}/{args.shard_count} slices={len(slices)} cost={loads[args.shard_index]:,} sha={digest}",flush=True); return 0

if __name__=="__main__": raise SystemExit(main())
