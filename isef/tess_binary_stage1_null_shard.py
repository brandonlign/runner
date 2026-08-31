#!/usr/bin/env python3
"""Run frozen Stage-1 on one shard of the checksum-locked 128 TSSYS nulls."""
from __future__ import annotations
import hashlib,json,os
from pathlib import Path
import numpy as np,requests
from tess_binary_stage1_detector import detect

CONTROLS=Path('tess_binary_tssys_null_controls.txt')
EXPECTED='760298f1dd8ba8d7e97bfb70af3d0ed538ba6062066e1ca1bc78c6a6d0a7f6de'
ROOT='https://archive.konkoly.hu/pub/tssys/dr1/lightcurves_spectra/'
SHARDS=8
OUTROOT=Path('results/tess_binary_stage1_null')

def clean(x):
    if isinstance(x,(float,np.floating)):return float(x) if np.isfinite(x) else None
    if isinstance(x,(int,np.integer)):return int(x)
    if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [clean(v) for v in x]
    return x

def main():
    b=CONTROLS.read_bytes();sha=hashlib.sha256(b).hexdigest()
    if sha!=EXPECTED:raise RuntimeError(f'control checksum mismatch {sha}')
    ids=[int(x) for x in CONTROLS.read_text().split()]
    if len(ids)!=128 or len(set(ids))!=128:raise RuntimeError('control cardinality mismatch')
    si=int(os.environ['SHARD_INDEX']);chosen=ids[si::SHARDS]
    out=OUTROOT/f'shard_{si}';out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for n in chosen:
        url=f'{ROOT}{n}.lc'
        try:
            r=requests.get(url,timeout=120,headers={'User-Agent':'ISEF-stage1-null/1.0'});r.raise_for_status()
            a=np.loadtxt(__import__('io').BytesIO(r.content))
            if a.ndim!=2 or a.shape[1]<10:raise RuntimeError(f'unexpected shape {a.shape}')
            z=detect(a[:,1],a[:,4],a[:,5],a[:,9].astype(int))
            rows.append({'number':n,'status':'OK','download_sha256':hashlib.sha256(r.content).hexdigest(),'detector':clean(z)})
        except Exception as e:
            rows.append({'number':n,'status':'ERROR','error':f'{type(e).__name__}: {e}'})
        print(n,rows[-1]['status'],rows[-1].get('detector',{}).get('hard_pass'),rows[-1].get('detector',{}).get('score'),flush=True)
    rep={'shard_index':si,'shard_count':SHARDS,'control_manifest_sha256':sha,'year8_values_opened':False,'rows':rows}
    (out/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True,allow_nan=False)+'\n')
    errs=sum(x['status']!='OK' for x in rows);hp=sum(bool(x.get('detector',{}).get('hard_pass')) for x in rows)
    print(json.dumps({'shard':si,'n':len(rows),'errors':errs,'hard_pass':hp},indent=2))
    raise SystemExit(0 if errs==0 else 2)
if __name__=='__main__':main()
