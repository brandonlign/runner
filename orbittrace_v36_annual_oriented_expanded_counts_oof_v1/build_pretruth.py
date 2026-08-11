#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np

BASE_DIM=71
AUG_DIM=73
FORBIDDEN={'label','shower','truth','known_shower','native_background','sporadic'}

def require(ok,msg):
    if not ok: raise RuntimeError(msg)
def array_sha(x):
    a=np.ascontiguousarray(x); h=hashlib.sha256(); h.update(str(a.dtype).encode()); h.update(json.dumps(list(a.shape),separators=(',',':')).encode()); h.update(a.tobytes(order='C')); return h.hexdigest()

def main():
    p=argparse.ArgumentParser(); p.add_argument('--route',choices=['sugar','hdbscan'],required=True); p.add_argument('--payload-root',type=Path,required=True); p.add_argument('--rows-2013',type=Path,required=True); p.add_argument('--rows-2014',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    meta=json.loads((a.payload_root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fp=json.loads((a.payload_root/'family_memberships.json').read_text())
    require(meta['truth_accessed'] is False and fp['truth_accessed'] is False and int(meta['feature_dimension'])==BASE_DIM,'invalid immutable v24 pretruth payload')
    ids=list(map(str,meta['family_ids'])); fams=fp['families']; require([str(f['family_id']) for f in fams]==ids,'family alignment changed')
    X=np.load(a.payload_root/'features.npy',allow_pickle=False); require(X.shape==(len(ids),BASE_DIM) and array_sha(X)==meta['feature_sha256'],'base feature identity changed')
    rows={2013:json.loads(a.rows_2013.read_text()),2014:json.loads(a.rows_2014.read_text())}
    yearsets={}
    for year in (2013,2014):
        require(rows[year] and all(int(r['year'])==year for r in rows[year]),f'invalid label-free rows {year}')
        require(all(not (FORBIDDEN & {str(k).lower() for k in r}) for r in rows[year]),f'truth-bearing field in label-free rows {year}')
        yearsets[year]={str(r['id']) for r in rows[year]}; require(len(yearsets[year])==len(rows[year]),f'duplicate row IDs {year}')
    require(yearsets[2013].isdisjoint(yearsets[2014]),'row ID overlap across years')
    union=yearsets[2013]|yearsets[2014]
    aug=[]; counts=[]
    for fam in fams:
        eids=set(map(str,fam['event_ids'])); missing=eids-union; require(not missing,f"membership IDs absent from label-free row universe: {str(fam['family_id'])} count={len(missing)}")
        n13=len(eids & yearsets[2013]); n14=len(eids & yearsets[2014]); require(n13+n14==len(eids),'membership year partition failed')
        counts.append({'family_id':str(fam['family_id']),'expanded_member_count_2013':n13,'expanded_member_count_2014':n14})
        aug.append([math.log1p(n13),math.log1p(n14)])
    A=np.asarray(aug,dtype=np.float64); require(A.shape==(len(ids),2) and np.all(np.isfinite(A)),'invalid annual count augmentation')
    X73=np.column_stack([X,A]).astype(np.float64,copy=False); require(X73.shape==(len(ids),AUG_DIM) and np.all(np.isfinite(X73)),'invalid 73D feature matrix')
    np.save(a.output/'features_73.npy',X73,allow_pickle=False)
    result={'verdict':'PASS_V36_ANNUAL_ORIENTED_EXPANDED_COUNT_PRETRUTH','route':a.route,'family_ids':ids,'base_feature_dimension':BASE_DIM,'augmented_feature_dimension':AUG_DIM,'augmentation_feature_names':['log1p_expanded_member_count_2013','log1p_expanded_member_count_2014'],'base_feature_sha256':array_sha(X),'augmented_feature_sha256':array_sha(X73),'annual_count_payload':counts,'annual_count_payload_sha256':hashlib.sha256(json.dumps(counts,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'membership_changed':False,'truth_accessed':False,'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False}
    (a.output/'V36_PRETRUTH_MANIFEST.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps({k:v for k,v in result.items() if k not in ('family_ids','annual_count_payload')},indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
