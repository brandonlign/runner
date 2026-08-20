#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.metadata, json
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment

YEARS=(2013,2014)
GRID=(10,20,30,40,50,60,70,80,90,100,120,150,200,300,500,750,1000)
ROW_SHA={2013:'2433b556d4a859580ef5431d2307ef34c8fa4c15d42841a2ec7b0c11e5f1f158',2014:'206692292b2ca252777e40c13c367880740d8e2576d27615f7ea94b7790e3f55'}
EXPECTED={2013:16028,2014:13283}
HDB_SOURCE_SHA='a8b638f56dad2597973178523e8ad15e177a4f57e7fe6159fedc84d754afd3d2'

def req(x,m):
    if not x: raise RuntimeError(m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load_rows(root):
    rows=[]
    for y in YEARS:
        p=root/f'hdbscan_{y}.json'; req(sha(p)==ROW_SHA[y],f'row hash drift {y}')
        a=json.loads(p.read_text()); req(len(a)==EXPECTED[y],f'row count drift {y}'); rows.extend(a)
    ids=[str(r['id']) for r in rows]; req(len(ids)==len(set(ids)),'duplicate ids'); return rows
def feature_matrix(rows):
    sol=np.radians(np.asarray([float(r['sol']) for r in rows])); lon=np.radians(np.asarray([float(r['sun_lon']) for r in rows])); lat=np.radians(np.asarray([float(r['ecl_lat']) for r in rows])); vg=np.asarray([float(r['vg']) for r in rows])
    X=np.column_stack((np.cos(sol),np.sin(sol),np.sin(lon)*np.cos(lat),np.cos(lon)*np.cos(lat),np.sin(lat),vg/72.0))
    req(np.all(np.isfinite(X)),'non-finite features'); return X
def install_compat():
    import hdbscan.hdbscan_ as hi
    from sklearn.utils import check_array as sk
    def compat(*a,**kw):
        if 'ensure_all_finite' in kw: kw['force_all_finite']=kw.pop('ensure_all_finite')
        return sk(*a,**kw)
    hi.check_array=compat
def family_hash(ids): return hashlib.sha256(json.dumps(sorted(ids),separators=(',',':')).encode()).hexdigest()[:20]
def run_one(X,rows,mcs):
    import hdbscan
    model=hdbscan.HDBSCAN(min_cluster_size=int(mcs),min_samples=None,metric='euclidean',cluster_selection_method='eom',allow_single_cluster=False,prediction_data=False,core_dist_n_jobs=1)
    labels=np.asarray(model.fit_predict(X),dtype=np.int32); probs=np.asarray(model.probabilities_,dtype=float)
    out=[]
    for lab in sorted(int(v) for v in np.unique(labels) if v>=0):
        idx=np.flatnonzero(labels==lab); ids=sorted(str(rows[int(i)]['id']) for i in idx)
        out.append({'family_id':'HDB_CAL_'+family_hash(ids),'native_label':lab,'member_ids':ids,'member_count':len(ids),'mean_membership_probability':float(np.mean(probs[idx]))})
    out.sort(key=lambda f:str(f['family_id'])); return out
def pretruth(a):
    req(sha(a.hdb_source)==HDB_SOURCE_SHA,'HDB source drift'); req(importlib.metadata.version('hdbscan')=='0.8.44','hdbscan version drift'); install_compat()
    rows=load_rows(a.rows_root); X=feature_matrix(rows); catalogues={}
    for mcs in GRID:
        fam=run_one(X,rows,mcs); catalogues[str(mcs)]=fam; print(json.dumps({'min_cluster_size':mcs,'families':len(fam)}),flush=True)
    rec=json.loads(a.recurrent.read_text()); req(rec.get('truth_accessed') is False,'recurrent truth contaminated'); req(rec.get('target_information_access') is False,'target access')
    result={'role':'EXPOSED_CORRECTIVE_HDBSCAN_FAIRNESS_PRETRUTH','truth_accessed':False,'target_information_access':False,'grid':list(GRID),'pooled_event_count':len(rows),'hdbscan_version':'0.8.44','hdb_source_sha256':sha(a.hdb_source),'catalogues':catalogues,'recurrent_candidates':rec['routes']['hdbscan']['candidates']}
    a.output.mkdir(parents=True,exist_ok=True); p=a.output/'PRETRUTH.json'; p.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'pretruth_sha256':sha(p),'catalogue_counts':{k:len(v) for k,v in catalogues.items()}},indent=2))
def members(f): return set(map(str,f.get('event_ids',f.get('member_ids',[]))))
def score(fams,truth,budget=None,ranked=False):
    counts=Counter(v for v in truth.values() if v!='SPORADIC'); labs=sorted(k for k,n in counts.items() if n>=4); ids=set(truth); active=[]
    for i,f in enumerate(fams):
        m=members(f)&ids
        if m: active.append((int(f.get('rank',i+1)),str(f['family_id']),m))
    active=sorted(active,key=lambda x:(x[0],x[1])) if ranked else sorted(active,key=lambda x:x[1])
    if budget is not None: active=active[:int(budget)]
    ts={l:{eid for eid,v in truth.items() if v==l} for l in labs}; M=np.zeros((len(labs),len(active)))
    for i,l in enumerate(labs):
        actual=ts[l]
        for j,(_,_,pred) in enumerate(active):
            o=len(actual&pred)
            if o:
                pr=o/len(pred); re=o/len(actual); M[i,j]=2*pr*re/(pr+re)
    n=max(len(labs),len(active)); cost=np.zeros((n,n)); cost[:len(labs),:len(active)]=-M
    ri,cj=linear_sum_assignment(cost); vals=[float(M[i,j]) if j<len(active) else 0.0 for i,j in zip(ri.tolist(),cj.tolist()) if i<len(labs)]
    recovered=int(sum(v>0.5 for v in vals)); return {'eligible_showers':len(labs),'candidate_used':len(active),'macro_f1':float(np.mean(vals)) if vals else 0.0,'recovered_f1_gt_0_5':recovered,'recovered_per_candidate':float(recovered/len(active)) if active else 0.0}
def truth(root,y):
    xs=list(root.rglob(f'truth_hdbscan_{y}.json')); req(len(xs)==1,f'truth missing {y}: {xs}'); return json.loads(xs[0].read_text())
def evaluate(a):
    p=json.loads(a.pretruth.read_text()); req(p['truth_accessed'] is False,'pretruth contaminated'); truths={y:truth(a.truth_root,y) for y in YEARS}; results=[]
    for evaly,caly in ((2013,2014),(2014,2013)):
        calibration=[]
        for mcs in GRID:
            s=score(p['catalogues'][str(mcs)],truths[caly]); calibration.append({'min_cluster_size':mcs,**s})
        chosen=max(calibration,key=lambda r:(r['macro_f1'],r['recovered_f1_gt_0_5'],-r['min_cluster_size']))['min_cluster_size']
        h=score(p['catalogues'][str(chosen)],truths[evaly]); r=score(p['recurrent_candidates'],truths[evaly],h['candidate_used'],ranked=True)
        if r['macro_f1']>h['macro_f1'] and r['recovered_f1_gt_0_5']>=h['recovered_f1_gt_0_5']: verdict='RECURRENT_EOM_WIN'
        elif h['macro_f1']>r['macro_f1'] and h['recovered_f1_gt_0_5']>=r['recovered_f1_gt_0_5']: verdict='HDBSCAN_WIN'
        else: verdict='MIXED'
        results.append({'eval_year':evaly,'calibration_year':caly,'selected_min_cluster_size':chosen,'calibration_grid':calibration,'hdbscan':h,'recurrent':r,'verdict':verdict})
    verdicts=[x['verdict'] for x in results]
    overall='RECURRENT_EOM_BETTER_THAN_CALIBRATED_HDBSCAN' if verdicts==['RECURRENT_EOM_WIN','RECURRENT_EOM_WIN'] else ('CALIBRATED_HDBSCAN_BETTER_THAN_RECURRENT_EOM' if verdicts==['HDBSCAN_WIN','HDBSCAN_WIN'] else 'NO_UNAMBIGUOUS_WINNER')
    out={'verdict':overall,'results':results,'exposed_corrective_evidence':True,'claim_boundary':'Cross-year calibrated published-geometry GEO/eom HDBSCAN; not pristine validation.'}
    a.output.mkdir(parents=True,exist_ok=True); q=a.output/'RESULT.json'; q.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps(out,indent=2))
def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('pretruth'); p.add_argument('--rows-root',type=Path,required=True); p.add_argument('--hdb-source',type=Path,required=True); p.add_argument('--recurrent',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    e=sub.add_parser('evaluate'); e.add_argument('--pretruth',type=Path,required=True); e.add_argument('--truth-root',type=Path,required=True); e.add_argument('--output',type=Path,required=True)
    a=ap.parse_args(); pretruth(a) if a.cmd=='pretruth' else evaluate(a)
if __name__=='__main__': main()
