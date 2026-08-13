from __future__ import annotations
from pathlib import Path
from types import SimpleNamespace
import run_urc_union_ranker as q
YEARS=(2022,2023); MONTH_KEYS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13)); BLIND=(20.0,55.0)
def req(x,m):
    if not x: raise RuntimeError(m)
def load(a):
    q.v1.mult.YEARS=YEARS; q.v1.mult.MONTH_KEYS=MONTH_KEYS; q.v1.mult.TOP_K=100
    runtime=q.v1.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts)
    support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS='orbittrace-gmn-v31-measurement-uncertainty-schema-v1'; support.RANKING_VARIANTS=('persistence',)
    req(float(support.BLIND_LOW)==20.0 and float(support.BLIND_HIGH)==55.0,'active blind interval drift')
    box=SimpleNamespace(support_source_parts=a.support_source_parts,candidate_payload=a.candidate_payload,baseline_payload=a.baseline_payload,scorer_parts=a.scorer_parts,v8_result_json=a.v8_result_json,fixed4_baseline_json=a.v8_result_json,output=a.output)
    _candidate,base,_scorer=support.load_sources(box); scan,_cal,_hidden,sources=support.parse_catalogue(base)
    req(sorted(scan)==list(YEARS),'active years drift'); req([x['key'] for x in sources]==list(MONTH_KEYS),'active month panel drift')
    for y in YEARS:
        seen=set()
        for row in scan[y]:
            eid=str(row['id']); req(eid and eid not in seen,f'duplicate active ID {y}/{eid}'); seen.add(eid)
            sol=float(row['sol'])%360.0; req(not (BLIND[0]<=sol<=BLIND[1]),f'protected event reached active scan {y}/{eid}')
    return scan
