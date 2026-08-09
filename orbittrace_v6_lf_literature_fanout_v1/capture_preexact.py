from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_lf_literature_fanout_v1.common import canonical_sha, materialize, require


def parse_args() -> argparse.Namespace:
    p=argparse.ArgumentParser()
    p.add_argument("--panel",required=True,choices=("hdbscan","sugar")); p.add_argument("--year",required=True,type=int,choices=(2023,2025))
    p.add_argument("--v6-source",required=True,type=Path); p.add_argument("--base-runner",required=True,type=Path); p.add_argument("--exact-row-runner",required=True,type=Path); p.add_argument("--id-manifest",required=True,type=Path)
    p.add_argument("--support-source-parts",required=True,type=Path); p.add_argument("--candidate-payload",required=True,type=Path); p.add_argument("--baseline-payload",required=True,type=Path); p.add_argument("--scorer-parts",required=True,type=Path); p.add_argument("--archive",required=True,type=Path); p.add_argument("--output",required=True,type=Path)
    return p.parse_args()


def main() -> int:
    args=parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    ctx=materialize(args,f"capture_{args.panel}_{args.year}"); v6=ctx["v6"]; centers:dict[float,dict[str,Any]]={}; original=v6.exact_rescore_window_v6
    def capture(_old,records,window_events,_lookup,_support,_base):
        require(bool(records),"empty exact call"); center=float(records[0]["window_center"]); require(all(float(r["window_center"])==center for r in records),"mixed center"); require(center not in centers,f"duplicate center {center}")
        copied=[dict(r) for r in records]; ids=[str(e["id"]) for e in window_events]
        centers[center]={"records":copied,"records_sha256":canonical_sha(copied),"window_event_ids":ids,"window_event_ids_sha256":canonical_sha(ids)}
        print(f"V6_LF_LIT_CAPTURE panel={args.panel} year={args.year} center={center:.1f} records={len(copied)} events={len(ids)}",flush=True); return []
    v6.exact_rescore_window_v6=capture
    try: v6.scan_year_v6(ctx["old"],args.year,ctx["scan_events"],ctx["calibration"],ctx["candidate"],ctx["base"],ctx["scorer"],ctx["support"])
    finally: v6.exact_rescore_window_v6=original
    require(bool(centers),"no exact centers captured"); ordered=sorted(centers); total=sum(len(centers[c]["records"]) for c in ordered)
    pre={"format":"orbittrace-v6-lf-literature-preexact-v1","panel":args.panel,"year":args.year,"id_manifest_sha256":ctx["manifest_sha"],"scan_rows_sha256":canonical_sha(ctx["scan_events"]),"calibration_rows_sha256":canonical_sha(ctx["calibration"]),"scan_count":ctx["scan_count"],"calibration_count":ctx["calibration_count"],"native_background_count_unused":ctx["native_background_count"],"ordered_centers":ordered,"centers":centers,"total_records":total,"firewall":{"truth_accessed":False,"mapping_accessed":False,"competitor_cluster_labels_accessed":False,"native_background_membership_used_for_calibration":False,"target_interval_remains_excluded":True}}
    raw=pickle.dumps(pre,protocol=pickle.HIGHEST_PROTOCOL); path=args.output/f"preexact_{args.panel}_{args.year}.pkl"; path.write_bytes(raw); digest=hashlib.sha256(raw).hexdigest(); path.with_suffix(".sha256").write_text(digest+"\n")
    (args.output/f"preexact_{args.panel}_{args.year}.json").write_text(json.dumps({"panel":args.panel,"year":args.year,"centers":len(ordered),"total_records":total,"checkpoint_sha256":digest},indent=2,sort_keys=True)+"\n")
    print(f"PASS_V6_LF_LITERATURE_PREEXACT panel={args.panel} year={args.year} centers={len(ordered)} records={total} sha={digest}",flush=True); return 0

if __name__=="__main__": raise SystemExit(main())
