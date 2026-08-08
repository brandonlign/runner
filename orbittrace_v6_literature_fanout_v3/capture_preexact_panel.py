from __future__ import annotations

import argparse
import pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_literature_fanout_v3.panel_common import canonical_sha, materialize, require


def parse_args() -> argparse.Namespace:
    p=argparse.ArgumentParser()
    p.add_argument("--panel",required=True,choices=("hdbscan","sugar"))
    p.add_argument("--year",required=True,type=int,choices=(2023,2025))
    p.add_argument("--v6-source",required=True,type=Path); p.add_argument("--base-runner",required=True,type=Path); p.add_argument("--exact-row-runner",required=True,type=Path)
    p.add_argument("--id-manifest",required=True,type=Path); p.add_argument("--support-source-parts",required=True,type=Path); p.add_argument("--candidate-payload",required=True,type=Path); p.add_argument("--baseline-payload",required=True,type=Path); p.add_argument("--scorer-parts",required=True,type=Path); p.add_argument("--archive",required=True,type=Path); p.add_argument("--output",required=True,type=Path)
    return p.parse_args()


def main() -> int:
    args=parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    ctx=materialize(args,f"capture_{args.panel}_{args.year}")
    v6=ctx["v6"]; old=ctx["old"]; support=ctx["support"]; base=ctx["base"]
    centers:dict[float,dict[str,Any]]={}; original=v6.exact_rescore_window_v6

    def capture(old_arg,records,window_events,event_lookup,support_arg,base_arg):
        del old_arg,event_lookup,support_arg,base_arg
        require(bool(records),"unexpected empty exact call")
        center=float(records[0]["window_center"]); require(all(float(r["window_center"])==center for r in records),"mixed center exact call"); require(center not in centers,f"duplicate center {center}")
        record_copy=[dict(r) for r in records]; ids=[str(e["id"]) for e in window_events]
        centers[center]={"records":record_copy,"records_sha256":canonical_sha(record_copy),"window_event_ids":ids,"window_event_ids_sha256":canonical_sha(ids)}
        print(f"LIT_FANOUT_CAPTURE panel={args.panel} year={args.year} center={center:.1f} proposals={len(records):,} events={len(ids):,}",flush=True)
        return []

    v6.exact_rescore_window_v6=capture
    try:
        v6.scan_year_v6(old,args.year,ctx["scan_events"],ctx["calibration"],ctx["candidate"],base,ctx["scorer"],support)
    finally:
        v6.exact_rescore_window_v6=original
    require(bool(centers),"no exact centers captured")
    ordered=sorted(centers); total=sum(len(centers[c]["records"]) for c in ordered)
    pre={"format":"orbittrace-v6-matched-literature-preexact-v3","panel":args.panel,"year":args.year,"id_manifest_sha256":ctx["manifest_sha"],"blind_exclusion":[20.0,55.0],"scan_count":ctx["scan_count"],"calibration_count":ctx["calibration_count"],"scan_rows_sha256":canonical_sha(ctx["scan_events"]),"calibration_rows_sha256":canonical_sha(ctx["calibration"]),"ordered_centers":ordered,"centers":centers,"total_records":total,"firewall":{"truth_accessed":False,"competitor_cluster_labels_accessed":False,"target_interval_remains_excluded":True}}
    raw=pickle.dumps(pre,protocol=pickle.HIGHEST_PROTOCOL); path=args.output/f"preexact_{args.panel}_{args.year}.pkl"; path.write_bytes(raw)
    import hashlib
    digest=hashlib.sha256(raw).hexdigest(); path.with_suffix(".sha256").write_text(digest+"\n")
    (args.output/f"preexact_{args.panel}_{args.year}.json").write_text(__import__('json').dumps({"panel":args.panel,"year":args.year,"centers":len(ordered),"total_records":total,"checkpoint_sha256":digest},indent=2,sort_keys=True)+"\n")
    print(f"PASS_LITERATURE_FANOUT_PREEXACT panel={args.panel} year={args.year} centers={len(ordered)} proposals={total:,} sha={digest}",flush=True); return 0

if __name__=="__main__": raise SystemExit(main())
