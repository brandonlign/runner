#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np

MODEL_SHA256='acae7fa4b4702e8d3f823defb5f2b3a3e2922b12c3bb07269b6e354316a558cb'
QUALITY_SOURCE_SHA256='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
EXPECTED_N={'sugar':267,'hdbscan':229}


def req(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def array_sha(x:np.ndarray)->str:
    a=np.ascontiguousarray(x)
    h=hashlib.sha256(); h.update(str(a.dtype).encode()); h.update(json.dumps(list(a.shape),separators=(',',':')).encode()); h.update(a.tobytes(order='C'))
    return h.hexdigest()


def order_sha(order:list[str])->str:
    return hashlib.sha256('\n'.join(order).encode()).hexdigest()


def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); req(spec is not None and spec.loader is not None,f'cannot import {path}')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--model',type=Path,required=True); p.add_argument('--quality-source',type=Path,required=True); p.add_argument('--payload-root',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.model)==MODEL_SHA256,'model changed'); req(sha(a.quality_source)==QUALITY_SOURCE_SHA256,'#839 source changed')
    model=joblib.load(a.model); req(getattr(model,'n_features_in_',None)==34,'model feature count changed')
    qmod=load_module(a.quality_source,'frozen_839_compat_portability_probe')
    routes={}
    for route in ('sugar','hdbscan'):
        root=a.payload_root/route
        meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        req(meta['truth_accessed'] is False,'truth marker changed'); req(meta['feature_dimension']==71,'feature dimension changed'); req(meta['feature_blocks']=={'raw_839':34,'relative_noncat_839':30,'rank_percentiles':3,'consensus_graph':4},'feature blocks changed')
        req(meta['target_information_access'] is False and meta['maarsy_scientific_access'] is False and meta['dms_scientific_access'] is False,'firewall changed')
        ids=list(map(str,meta['family_ids'])); req(len(ids)==EXPECTED_N[route],'candidate count changed')
        X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False)
        scores=np.asarray(model.predict(X[:,:34]),float); req(np.isfinite(scores).all(),'nonfinite score')
        tie=[(int(meta['tie_rank'][i]),ids[i]) for i in range(len(ids))]
        idx=qmod.diversity_order(scores,C,0.8,1.0,tie); order=[ids[i] for i in idx]; req(len(order)==len(ids) and len(set(order))==len(ids),'incomplete order')
        routes[route]={'candidate_count':len(ids),'score_sha256':array_sha(scores),'order_sha256':order_sha(order),'complete_order':order,'score_min':float(scores.min()),'score_max':float(scores.max())}
    result={'scientific_role':'PRETRUTH_ENGINEERING_PORTABILITY_PROBE_ONLY','truth_accessed':False,'model_sha256':MODEL_SHA256,'scikit_learn_runtime_recorded_externally_by_workflow':True,'routes':routes,'sonotaco_truth_artifact_accessed':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'blind_exclusion':[20.0,55.0]}
    out=a.output/'PRETRUTH_PORTABILITY_PROBE.json'; out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({r:{k:v for k,v in routes[r].items() if k!='complete_order'} for r in routes},indent=2,sort_keys=True)); return 0

if __name__=='__main__': raise SystemExit(main())
