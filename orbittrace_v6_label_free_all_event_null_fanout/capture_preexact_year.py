from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_label_free_all_event_null import run_development as lf


def parse_args() -> argparse.Namespace:
    p=argparse.ArgumentParser()
    p.add_argument("--year",required=True,type=int,choices=lf.YEARS)
    p.add_argument("--repaired-v6-source",required=True,type=Path)
    p.add_argument("--base-runner",required=True,type=Path)
    p.add_argument("--support-source-parts",required=True,type=Path)
    p.add_argument("--candidate-payload",required=True,type=Path)
    p.add_argument("--baseline-payload",required=True,type=Path)
    p.add_argument("--scorer-parts",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    return p.parse_args()


def event_rows_sha(rows:list[dict[str,Any]])->str:
    return lf.canonical_sha(rows)


def main()->int:
    args=parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    lf.require(lf.sha256_path(args.repaired_v6_source)==lf.REPAIRED_V6_SHA256,"repaired v6 source identity changed")
    v6=lf.load_module(args.repaired_v6_source,f"orbittrace_v6_lf_capture_{args.year}")
    lf.require(all(v6.v3.self_test().values()),"v3 self-test failed")
    lf.require(all(v6.v3_membership_self_test().values()),"v3 membership self-test failed")
    old=v6.load_base_runner(args.base_runner)
    lf.require(list(old.YEARS)==[2022,2023] and int(old.MAX_COMPONENTS_PER_BIN)==128,"frozen base constants changed")
    support=old.load_support_module(args.support_source_parts)
    lf.require(float(support.BLIND_LOW)==20.0 and float(support.BLIND_HIGH)==55.0,"blind interval changed")
    candidate,base,scorer=support.load_sources(args)

    scan_by_year,calibration_by_year,geometry_audits,_pretruth_ids=lf.parse_geometry_only(support,base)
    scan=scan_by_year[args.year]; calibration=calibration_by_year[args.year]
    lf.require(len(scan)==len(calibration),"all-event calibration count mismatch")
    lf.require([e["id"] for e in scan]==[e["id"] for e in calibration],"all-event calibration ID mismatch")
    lf.require(all(not (20.0<=float(e["sol"])<=55.0) for e in scan),"blind interval entered scan")
    scan_sha=event_rows_sha(scan); calibration_sha=event_rows_sha(calibration)
    audit_rows=[a for a in geometry_audits if str(a["key"]).startswith(str(args.year))]
    audit_sha=hashlib.sha256(json.dumps(audit_rows,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()

    centers:dict[float,dict[str,Any]]={}
    original=v6.exact_rescore_window_v6
    def capture_exact(old_arg,records,window_events,event_lookup,support_arg,base_arg):
        del old_arg,support_arg,base_arg
        lf.require(bool(records),"unexpected empty exact call")
        center=float(records[0]["window_center"])
        lf.require(all(float(row["window_center"])==center for row in records),"mixed exact centers")
        lf.require(center not in centers,f"duplicate exact center {center}")
        ids=[str(row["id"]) for row in window_events]
        lf.require(all(event_lookup[eid] is window_events[i] for i,eid in enumerate(ids)),"event lookup/window identity mismatch")
        copied=[dict(row) for row in records]
        centers[center]={"records":copied,"records_sha256":lf.canonical_sha(copied),"window_event_ids":ids,"window_event_ids_sha256":lf.canonical_sha(ids)}
        print(f"V6_LF_FANOUT_CAPTURE year={args.year} center={center:.1f} records={len(records):,} events={len(ids):,}",flush=True)
        return []
    v6.exact_rescore_window_v6=capture_exact
    try:
        v6.scan_year_v6(old,args.year,scan,calibration,candidate,base,scorer,support)
    finally:
        v6.exact_rescore_window_v6=original
    lf.require(bool(centers),"no exact centers captured")
    ordered=sorted(centers); total=sum(len(centers[c]["records"]) for c in ordered)
    lf.require(total>0,"no exact proposals captured")
    checkpoint={
        "format":"orbittrace-v6-lf-preexact-fanout-v1",
        "year":args.year,
        "repaired_v6_sha256":lf.REPAIRED_V6_SHA256,
        "scan_rows_sha256":scan_sha,
        "calibration_rows_sha256":calibration_sha,
        "geometry_audit_sha256":audit_sha,
        "ordered_centers":ordered,
        "centers":centers,
        "total_records":total,
        "firewall":{"target_interval_remains_excluded":True,"label_values_not_accessed":True,"all_event_calibration":True,"scientific_result_not_evaluated":True},
    }
    raw=pickle.dumps(checkpoint,protocol=pickle.HIGHEST_PROTOCOL)
    path=args.output/f"v6_lf_preexact_{args.year}.pkl"; path.write_bytes(raw)
    digest=hashlib.sha256(raw).hexdigest(); path.with_suffix(".sha256").write_text(digest+"\n")
    (args.output/f"v6_lf_preexact_{args.year}.json").write_text(json.dumps({"year":args.year,"checkpoint_sha256":digest,"centers":len(ordered),"total_records":total,"scan_rows_sha256":scan_sha,"calibration_rows_sha256":calibration_sha},indent=2,sort_keys=True)+"\n")
    print(f"PASS_V6_LF_FANOUT_PREEXACT year={args.year} centers={len(ordered)} records={total:,} sha={digest}",flush=True)
    return 0


if __name__=="__main__": raise SystemExit(main())
