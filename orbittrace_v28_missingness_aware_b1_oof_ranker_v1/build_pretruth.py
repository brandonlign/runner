#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np

def require(ok,msg):
    if not ok: raise RuntimeError(msg)
def arrsha(x):
    a=np.ascontiguousarray(x); h=hashlib.sha256(); h.update(str(a.dtype).encode()); h.update(json.dumps(list(a.shape),separators=(',',':')).encode()); h.update(a.tobytes()); return h.hexdigest()
def main():
    p=argparse.ArgumentParser(); p.add_argument('--route',choices=['sugar','hdbscan'],required=True); p.add_argument('--v22-root',type=Path,required=True); p.add_argument('--census-json',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    m=json.loads((a.v22_root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fam=json.loads((a.v22_root/'family_memberships.json').read_text()); c=json.loads(a.census_json.read_text())
    require(m['comparator']==a.route and m['feature_dimension']==71 and m['truth_accessed'] is False,'bad v22 manifest'); require(fam['truth_accessed'] is False,'truth-bearing family payload'); require(c['comparator']==a.route and c['truth_accessed'] is False and c['scientific_performance_evaluated'] is False,'bad census role')
    ids=list(map(str,m['family_ids'])); require([str(f['family_id']) for f in fam['families']]==ids,'family alignment changed'); require(int(c['families'])==len(ids),'census family count mismatch')
    by={str(r['family_id']):r for r in c['rows']}; require(set(by)==set(ids),'census universe mismatch')
    X=np.load(a.v22_root/'features.npy',allow_pickle=False); C=np.load(a.v22_root/'centroids.npy',allow_pickle=False); require(X.shape==(len(ids),71) and C.shape==(len(ids),8),'v22 array shape changed'); require(arrsha(X)==m['feature_sha256'] and arrsha(C)==m['centroid_sha256'],'v22 internal hash mismatch')
    extra=[]; sc={'PASS':0,'LT4_SCREENED_LOCAL_FIELD':0,'LT4_SOURCE_SEEDS':0}
    for fid in ids:
        annual={int(r['year']):r for r in by[fid]['annual']}; require(set(annual)=={2013,2014},f'{fid} annual census missing')
        row=[]
        for y in (2013,2014):
            r=annual[y]; s=str(r['status']); require(s in sc,f'unexpected census status {s}'); sc[s]+=1
            if s=='PASS':
                v=float(r['mean_log_odds']); require(math.isfinite(v),f'nonfinite census evidence {fid}/{y}'); row.extend([v,0.0,0.0])
            elif s=='LT4_SCREENED_LOCAL_FIELD': row.extend([0.0,1.0,0.0])
            else: row.extend([0.0,0.0,1.0])
        extra.append(row)
    E=np.asarray(extra,dtype=np.float64); require(E.shape==(len(ids),6) and np.all(np.isfinite(E)),'bad v28 evidence matrix'); X77=np.column_stack([X,E]); require(X77.shape==(len(ids),77),'bad v28 feature shape')
    np.save(a.output/'features_v28.npy',X77,allow_pickle=False); np.save(a.output/'b1_missingness_features.npy',E,allow_pickle=False)
    out={'stage':'V28_MISSINGNESS_AWARE_B1_PRETRUTH_FREEZE','route':a.route,'family_ids':ids,'feature_dimension':77,'base_feature_dimension':71,'appended_dimension':6,'feature_sha256':arrsha(X77),'appended_sha256':arrsha(E),'v22_feature_sha256':arrsha(X),'centroid_sha256':arrsha(C),'status_counts':sc,'neutral_missing_log_odds':0.0,'allowed_statuses':['PASS','LT4_SCREENED_LOCAL_FIELD','LT4_SOURCE_SEEDS'],'truth_accessed':False,'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'feature_search':False}
    (a.output/'V28_PRETRUTH_MANIFEST.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps({k:v for k,v in out.items() if k!='family_ids'},indent=2,sort_keys=True))
if __name__=='__main__': main()
