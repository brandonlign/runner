from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_lf_literature_fanout_v1.common import canonical_sha, materialize, require
from orbittrace_v6_literature_adapter.parallel_exact_rescore import install


def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser(); p.add_argument("--panel",required=True,choices=("hdbscan","sugar")); p.add_argument("--year",required=True,type=int,choices=(2023,2025)); p.add_argument("--split-records",required=True,type=int); p.add_argument("--workers",type=int,default=4); p.add_argument("--preexact",required=True,type=Path)
    p.add_argument("--v6-source",required=True,type=Path); p.add_argument("--base-runner",required=True,type=Path); p.add_argument("--exact-row-runner",required=True,type=Path); p.add_argument("--id-manifest",required=True,type=Path); p.add_argument("--support-source-parts",required=True,type=Path); p.add_argument("--candidate-payload",required=True,type=Path); p.add_argument("--baseline-payload",required=True,type=Path); p.add_argument("--scorer-parts",required=True,type=Path); p.add_argument("--archive",required=True,type=Path); return p.parse_args()


def load_pre(path:Path)->tuple[dict[str,Any],str]:
    raw=path.read_bytes(); side=path.with_suffix(".sha256"); require(side.exists(),"missing preexact SHA"); digest=hashlib.sha256(raw).hexdigest(); require(digest==side.read_text().strip(),"preexact SHA mismatch"); return pickle.loads(raw),digest


def main()->int:
    args=parse_args(); require(args.split_records>0,"split-records must be positive"); require(1<=args.workers<=4,"workers outside frozen range"); pre,pre_sha=load_pre(args.preexact)
    require(pre["format"]=="orbittrace-v6-lf-literature-preexact-v1" and pre["panel"]==args.panel and int(pre["year"])==args.year,"wrong preexact identity"); firewall=pre["firewall"]; require(all(firewall[key] is False for key in ("truth_accessed","mapping_accessed","competitor_cluster_labels_accessed","native_background_membership_used_for_calibration")) and firewall["target_interval_remains_excluded"] is True,"preexact firewall failed")
    ctx=materialize(args,f"real_equiv_{args.panel}_{args.year}"); require(ctx["manifest_sha"]==pre["id_manifest_sha256"],"manifest changed"); require(canonical_sha(ctx["scan_events"])==pre["scan_rows_sha256"] and canonical_sha(ctx["calibration"])==pre["calibration_rows_sha256"],"matched rows changed")
    eligible=[]
    for raw_center in pre["ordered_centers"]:
        center=float(raw_center); spec=pre["centers"][center]; nr=len(spec["records"]); ne=len(spec["window_event_ids"])
        if nr>args.split_records: eligible.append((nr*ne,nr,ne,center))
    require(bool(eligible),"no real center genuinely splits"); _cost,nr,ne,center=min(eligible); spec=pre["centers"][center]; records=spec["records"]; require(canonical_sha(records)==spec["records_sha256"],"records changed"); ids=[str(v) for v in spec["window_event_ids"]]; require(canonical_sha(ids)==spec["window_event_ids_sha256"],"window IDs changed")
    lookup={str(e["id"]):e for e in ctx["scan_events"]}; require(all(event_id in lookup for event_id in ids),"window event missing"); window=[lookup[event_id] for event_id in ids]; require([str(e["id"]) for e in ctx["old"].window_events_for_center(ctx["scan_events"],center,ctx["base"]) ]==ids,"window reconstruction changed")
    v6=ctx["v6"]; scalar=v6.exact_rescore_window_v6; full=scalar(ctx["old"],records,window,lookup,ctx["support"],ctx["base"]); require([str(r["proposal_anchor_id"]) for r in full]==[str(r["proposal_anchor_id"]) for r in records],"full exact order changed")
    execution=install(v6,workers=args.workers,min_parallel_records=256); split=[]; units=0
    for start in range(0,len(records),args.split_records):
        stop=min(len(records),start+args.split_records); piece=records[start:stop]; exact=v6.exact_rescore_window_v6(ctx["old"],piece,window,lookup,ctx["support"],ctx["base"]); require([str(r["proposal_anchor_id"]) for r in exact]==[str(r["proposal_anchor_id"]) for r in piece],f"split order changed {start}:{stop}"); split.extend(exact); units+=1
    require(units>=2,"center did not split"); require(split==full,"full/split exact outputs differ"); full_bytes=json.dumps(full,sort_keys=True,separators=(",",":"),allow_nan=False).encode(); split_bytes=json.dumps(split,sort_keys=True,separators=(",",":"),allow_nan=False).encode(); require(full_bytes==split_bytes,"canonical full/split bytes differ"); digest=hashlib.sha256(full_bytes).hexdigest()
    print('PASS_V6_LF_LITERATURE_REAL_EXACT_EQUIVALENCE'); print(json.dumps({"panel":args.panel,"year":args.year,"preexact_sha256":pre_sha,"center":center,"proposal_records":nr,"window_events":ne,"split_records":args.split_records,"units":units,"workers":args.workers,"parallel_execution":execution,"canonical_output_sha256":digest,"truth_accessed":False,"mapping_accessed":False,"competitor_cluster_labels_accessed":False,"native_background_membership_used_for_calibration":False,"target_interval_remains_excluded":True},sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
