#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import prepare_pretruth as prep


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument('--rows-2013',type=Path,required=True); p.add_argument('--rows-2014',type=Path,required=True)
    p.add_argument('--support-source-parts',type=Path,required=True); p.add_argument('--candidate-payload',type=Path,required=True)
    p.add_argument('--baseline-payload',type=Path,required=True); p.add_argument('--scorer-parts',type=Path,required=True)
    p.add_argument('--ranker-source',type=Path,required=True); p.add_argument('--original-model',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True); p.add_argument('--graph-output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True); a.graph_output.parent.mkdir(parents=True,exist_ok=True)

    require(prep.YEARS==(2013,2014),'v22 SonotaCo years changed')
    require(float(prep.v19.CONSENSUS_RADIUS)==1.0,'frozen consensus radius changed')
    captured={}
    original=prep.v19.build_edges

    def capture(families,support,base):
        edges=original(families,support,base)
        if not captured:
            captured['ids']=[str(f['family_id']) for f in families]
            captured['edges']=[[float(d),int(i),int(j)] for d,i,j in edges]
        return edges

    prep.v19.build_edges=capture
    old_argv=sys.argv[:]
    try:
        sys.argv=['prepare_pretruth.py','--comparator','hdbscan','--rows-2013',str(a.rows_2013),'--rows-2014',str(a.rows_2014),
                  '--support-source-parts',str(a.support_source_parts),'--candidate-payload',str(a.candidate_payload),
                  '--baseline-payload',str(a.baseline_payload),'--scorer-parts',str(a.scorer_parts),
                  '--ranker-source',str(a.ranker_source),'--original-model',str(a.original_model),'--output',str(a.output)]
        rc=prep.main(); require(rc==0,'v22 pretruth regeneration failed')
    finally:
        sys.argv=old_argv; prep.v19.build_edges=original

    require(captured and captured.get('edges') is not None,'graph capture did not execute')
    meta=json.loads((a.output/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    ids=list(map(str,meta['family_ids'])); sources=list(map(str,meta['sources']))
    require(ids==captured['ids'],'captured graph family order differs from v22 manifest')
    require(len(ids)==len(sources),'source alignment changed')
    for d,i,j in captured['edges']:
        require(0<=i<len(ids) and 0<=j<len(ids) and i<j,'invalid graph edge indices')
        require(float(d)<=1.0+1e-12,'captured edge exceeds frozen radius')
    payload={
        'verdict':'PASS_V24_HDB_GRAPH_PRETRUTH_CAPTURE',
        'source_pr':843,'radius':1.0,'years':[2013,2014],
        'family_ids':ids,'sources':sources,'edges':captured['edges'],'edge_count':len(captured['edges']),
        'feature_sha256':meta['feature_sha256'],'centroid_sha256':meta['centroid_sha256'],'v19_family_sha256':meta['v19_family_sha256'],
        'truth_accessed':False,'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,
    }
    raw=(json.dumps(payload,indent=2,sort_keys=True,allow_nan=False)+'\n').encode(); a.graph_output.write_bytes(raw)
    print(json.dumps({'verdict':payload['verdict'],'families':len(ids),'edges':len(captured['edges']),'graph_sha256':hashlib.sha256(raw).hexdigest()},indent=2))
    return 0

if __name__=='__main__': raise SystemExit(main())
