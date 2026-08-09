from __future__ import annotations

import argparse, hashlib, json, pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_label_free_all_event_null import run_development as lf
from orbittrace_v6_lf_gmn_2024_2025_holdout import holdout_context as ctx


def parse_args():
    p=argparse.ArgumentParser(); p.add_argument('--year',required=True,type=int,choices=ctx.HOLDOUT_YEARS)
    p.add_argument('--repaired-v6-source',required=True,type=Path); p.add_argument('--base-runner',required=True,type=Path)
    p.add_argument('--support-source-parts',required=True,type=Path); p.add_argument('--candidate-payload',required=True,type=Path)
    p.add_argument('--baseline-payload',required=True,type=Path); p.add_argument('--scorer-parts',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path); return p.parse_args()


def main()->int:
    args=parse_args(); args.output.mkdir(parents=True,exist_ok=True); ctx.activate()
    lf.require(lf.sha256_path(args.repaired_v6_source)==lf.REPAIRED_V6_SHA256,'repaired v6 source changed')
    v6=lf.load_module(args.repaired_v6_source,f'orbittrace_v6_lf_holdout_capture_{args.year}')
    old=v6.load_base_runner(args.base_runner); support=old.load_support_module(args.support_source_parts)
    ctx.configure_runtime(v6,old,support)
    candidate,base,scorer=support.load_sources(args)
    lf.require(float(support.BLIND_LOW)==20.0 and float(support.BLIND_HIGH)==55.0,'blind interval changed')
    scan_by_year,cal_by_year,audits,_ids=lf.parse_geometry_only(support,base)
    scan=scan_by_year[args.year]; calibration=cal_by_year[args.year]
    lf.require(len(scan)>=1000 and len(calibration)==len(scan),'holdout scan/calibration power mismatch')
    lf.require([e['id'] for e in scan]==[e['id'] for e in calibration],'holdout calibration IDs changed')
    scan_sha=lf.canonical_sha(scan); cal_sha=lf.canonical_sha(calibration)
    year_audits=[a for a in audits if str(a['key']).startswith(str(args.year))]
    lf.require(len(year_audits)==12,f'incomplete monthly holdout retrieval {args.year}: {len(year_audits)}')
    audit_sha=hashlib.sha256(json.dumps(year_audits,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

    centers:dict[float,dict[str,Any]]={}; original=v6.exact_rescore_window_v6
    def capture(old_arg,records,window_events,event_lookup,support_arg,base_arg):
        del old_arg,support_arg,base_arg
        lf.require(bool(records),'empty exact capture'); center=float(records[0]['window_center'])
        lf.require(all(float(r['window_center'])==center for r in records),'mixed exact center')
        lf.require(center not in centers,f'duplicate exact center {center}')
        ids=[str(e['id']) for e in window_events]
        lf.require(all(event_lookup[eid] is window_events[i] for i,eid in enumerate(ids)),'window/event lookup identity changed')
        copied=[dict(r) for r in records]
        centers[center]={'records':copied,'records_sha256':lf.canonical_sha(copied),'window_event_ids':ids,'window_event_ids_sha256':lf.canonical_sha(ids)}
        print(f'V6_LF_HOLDOUT_CAPTURE year={args.year} center={center:.1f} records={len(records):,}',flush=True)
        return []
    v6.exact_rescore_window_v6=capture
    try: v6.scan_year_v6(old,args.year,scan,calibration,candidate,base,scorer,support)
    finally: v6.exact_rescore_window_v6=original
    lf.require(bool(centers),'no holdout exact centers captured')
    ordered=sorted(centers); total=sum(len(centers[c]['records']) for c in ordered)
    # Use the already-audited generic v6-LF fanout envelope so the immutable
    # exact/replay engines can be reused unchanged. Holdout identity remains
    # explicit in years/corpus and in the source-audited runtime namespace.
    payload={'format':'orbittrace-v6-lf-preexact-fanout-v1','year':args.year,'years':list(ctx.HOLDOUT_YEARS),'corpus':ctx.HOLDOUT_CORPUS,'repaired_v6_sha256':lf.REPAIRED_V6_SHA256,'scan_rows_sha256':scan_sha,'calibration_rows_sha256':cal_sha,'geometry_audit_sha256':audit_sha,'ordered_centers':ordered,'centers':centers,'total_records':total,'firewall':{'blind_exclusion':[20.0,55.0],'target_interval_remains_excluded':True,'label_values_not_accessed':True,'all_event_calibration':True,'scientific_result_not_evaluated':True}}
    raw=pickle.dumps(payload,protocol=pickle.HIGHEST_PROTOCOL); path=args.output/f'v6_lf_preexact_{args.year}.pkl'; path.write_bytes(raw)
    digest=hashlib.sha256(raw).hexdigest(); path.with_suffix('.sha256').write_text(digest+'\n')
    (args.output/f'v6_lf_preexact_{args.year}.json').write_text(json.dumps({'year':args.year,'checkpoint_sha256':digest,'centers':len(ordered),'total_records':total,'scan_rows':len(scan),'calibration_rows':len(calibration),'corpus':ctx.HOLDOUT_CORPUS},indent=2,sort_keys=True)+'\n')
    print(f'PASS_V6_LF_HOLDOUT_PREEXACT year={args.year} centers={len(ordered)} records={total:,} sha={digest}',flush=True); return 0


if __name__=='__main__': raise SystemExit(main())