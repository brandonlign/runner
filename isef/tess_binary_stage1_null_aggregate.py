#!/usr/bin/env python3
"""Aggregate all 128 frozen Stage-1 TSSYS null results and apply frozen gate."""
from __future__ import annotations
import json,hashlib,math
from pathlib import Path
EXPECTED='760298f1dd8ba8d7e97bfb70af3d0ed538ba6062066e1ca1bc78c6a6d0a7f6de'
ROOT=Path('results/tess_binary_stage1_null_download')
OUT=Path('results/tess_binary_stage1_null_aggregate');OUT.mkdir(parents=True,exist_ok=True)

def main():
    reports=list(ROOT.rglob('report.json'))
    if len(reports)!=8:raise RuntimeError(f'expected 8 shard reports, got {len(reports)}')
    rows=[]
    for p in reports:
        r=json.loads(p.read_text())
        if r['control_manifest_sha256']!=EXPECTED:raise RuntimeError('shard manifest mismatch')
        rows.extend(r['rows'])
    nums=[int(z['number']) for z in rows]
    if len(rows)!=128 or len(set(nums))!=128:raise RuntimeError(f'bad aggregate cardinality {len(rows)}/{len(set(nums))}')
    rows.sort(key=lambda z:z['number'])
    errors=[z for z in rows if z['status']!='OK']
    hp=[z for z in rows if z['status']=='OK' and bool(z.get('detector',{}).get('hard_pass'))]
    scores=[float(z['detector']['score']) for z in hp if z['detector'].get('score') is not None and math.isfinite(float(z['detector']['score']))]
    frac=len(hp)/128.0
    gate=bool(len(errors)==0 and frac<=0.05)
    rep={'role':'frozen independent historical-null Stage-1 gate','year8_values_opened':False,'control_manifest_sha256':EXPECTED,
         'n':len(rows),'error_n':len(errors),'errors':errors,'hard_pass_n':len(hp),'hard_pass_fraction':frac,
         'max_finite_hard_pass_score':max(scores) if scores else None,'finite_hard_pass_scores':sorted(scores),'gate_pass':gate,
         'gate_rule':'all 128 process successfully and hard-pass fraction <= 0.05','rows':rows}
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'n':128,'error_n':len(errors),'hard_pass_n':len(hp),'hard_pass_fraction':frac,'max_score':rep['max_finite_hard_pass_score'],'gate_pass':gate},indent=2))
    raise SystemExit(0 if gate else 3)
if __name__=='__main__':main()
