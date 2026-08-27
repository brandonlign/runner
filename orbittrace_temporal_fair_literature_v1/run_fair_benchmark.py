#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, importlib.util, json, math, sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

YEARS=(2013,2014)
ROUTES=("sugar","hdbscan")
SUGAR_SHA="5b7699a2cf07b9b9ac6dee006c66a9b509af73ee3763093fa333d13e1deca0cb"
HDB_SHA="a8b638f56dad2597973178523e8ad15e177a4f57e7fe6159fedc84d754afd3d2"
ROW_SHA={
("sugar",2013):"47fb0b700fbf710c7b061eead343016bd8d182756eb0c7f406507c5739e4c4f8",
("sugar",2014):"bc83c113e9a14b1c6e1ef460ca9a40e05df77f3a449fec6064f8910add04c912",
("hdbscan",2013):"2433b556d4a859580ef5431d2307ef34c8fa4c15d42841a2ec7b0c11e5f1f158",
("hdbscan",2014):"206692292b2ca252777e40c13c367880740d8e2576d27615f7ea94b7790e3f55",
}
EXPECTED={('sugar',2013):18638,('sugar',2014):15400,('hdbscan',2013):16028,('hdbscan',2014):13283}


def req(x,msg):
    if not x: raise RuntimeError(msg)

def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()

def load(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path); req(spec and spec.loader,'module load failed')
    m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m

def families_from_labels(rows, labels, prefix, probs=None):
    g=defaultdict(list)
    for i,x in enumerate(labels):
        if int(x)>=0:g[int(x)].append(i)
    out=[]
    for lab in sorted(g):
        ids=sorted(str(rows[i]['id']) for i in g[lab])
        fid=prefix+hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()[:16]
        r={'family_id':fid,'native_label':int(lab),'member_ids':ids,'member_count':len(ids)}
        if probs is not None:r['membership_probability_mean']=float(np.mean([probs[i] for i in g[lab]]))
        out.append(r)
    return out

def pooled_sugar(rows, source):
    req(sha(source)==SUGAR_SHA,'Sugar source drift'); s=load(source,'sugar_core')
    sol=np.asarray([float(r['sol']) for r in rows]); ra=np.asarray([float(r['ra']) for r in rows]); dec=np.asarray([float(r['dec']) for r in rows]); vg=np.asarray([float(r['vg']) for r in rows])
    ra_sd=np.asarray([float(r['ra_sd']) for r in rows]); dec_sd=np.asarray([float(r['dec_sd']) for r in rows]); vg_sd=np.asarray([float(r['vg_sd']) for r in rows])
    observed=s.feature_matrix_from_equatorial(sol,ra,dec,vg); eps,_=s.transferred_epsilon(observed)
    merger=s.OverlapGraphMerger(len(rows))
    for it in range(1000):
        seed=s.stable_seed(20170209,'sonotaco-final-label-free-sugar-v1-pooled-2013-2014',20132014,'ORBITTRACE_VS_SUGAR_POOLED',it)
        feats=s.clone_feature_matrix(sol,ra,dec,vg,ra_sd,dec_sd,vg_sd,seed=seed)
        merger.add_iteration(it,s.dbscan_clusters(feats,float(eps)))
    masters=merger.finalize(); labels,probs=s.hard_assignment(len(rows),masters,minimum_recurrence=100)
    fam=families_from_labels(rows,np.asarray(labels), 'SUGAR', np.asarray(probs))
    return {'method':'Sugar pooled 2013+2014','event_count':len(rows),'epsilon':float(eps),'families':fam,'truth_accessed':False}

def install_hdb_compat():
    import sklearn, hdbscan.hdbscan_ as hi
    from sklearn.utils import check_array as sk
    def compat(*a,**kw):
        if 'ensure_all_finite' in kw: kw['force_all_finite']=kw.pop('ensure_all_finite')
        return sk(*a,**kw)
    hi.check_array=compat

def pooled_hdb(rows, source):
    req(sha(source)==HDB_SHA,'HDB source drift'); install_hdb_compat(); h=load(source,'hdb_runner')
    X=np.asarray(h.feature_matrix(list(rows)),dtype=float); labels,probs,diag=h.run_hdbscan(X,1)
    fam=families_from_labels(rows,np.asarray(labels),'HDB',np.asarray(probs))
    return {'method':'catalogue HDBSCAN pooled 2013+2014','event_count':len(rows),'families':fam,'native_diagnostics':diag,'truth_accessed':False}

def run_pretruth(rows_root, sources, recurrent, out):
    out.mkdir(parents=True,exist_ok=True)
    rec=json.loads(recurrent.read_text()); req(rec['truth_accessed'] is False,'recurrent pretruth not sealed')
    result={'role':'POOLED_EQUAL_TEMPORAL_INFORMATION_PRETRUTH','truth_accessed':False,'routes':{},'recurrent_sha256':sha(recurrent)}
    for route in ROUTES:
        rows=[]
        for y in YEARS:
            p=rows_root/f'{route}_{y}.json'; req(sha(p)==ROW_SHA[(route,y)],f'{route} {y} rows drift'); r=json.loads(p.read_text()); req(len(r)==EXPECTED[(route,y)],'row count drift'); rows.extend(r)
        if route=='sugar': comp=pooled_sugar(rows,sources/'sugar_uncertainty_core.py')
        else: comp=pooled_hdb(rows,sources/'hdbscan_2025_runner.py')
        result['routes'][route]={'comparator':comp,'recurrent_candidates':rec['routes'][route]['candidates']}
    p=out/'POOLED_FAIR_PRETRUTH.json'; p.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'pretruth_sha256':sha(p),'families':{r:len(result['routes'][r]['comparator']['families']) for r in ROUTES}},indent=2))

def score(families, truth, budget=None, ranked=False):
    counts=Counter(v for v in truth.values() if v!='SPORADIC'); labels=sorted(k for k,n in counts.items() if n>=4); ids=set(truth)
    active=[]
    for i,f in enumerate(families):
        mem=set(map(str,f['event_ids'] if 'event_ids' in f else f['member_ids'])) & ids
        if mem: active.append((int(f.get('rank',i+1)),str(f['family_id']),mem))
    active=sorted(active,key=lambda z:(z[0],z[1]));
    if budget is not None: active=active[:budget]
    ts={lab:{eid for eid,v in truth.items() if v==lab} for lab in labels}; mat=np.zeros((len(labels),len(active)))
    for i,lab in enumerate(labels):
        a=ts[lab]
        for j,(_,_,p) in enumerate(active):
            o=len(a&p)
            if o:
                pr=o/len(p); re=o/len(a); mat[i,j]=2*pr*re/(pr+re)
    n=max(len(labels),len(active)); cost=np.zeros((n,n)); cost[:len(labels),:len(active)]=-mat; ri,cj=linear_sum_assignment(cost)
    vals=[float(mat[i,j]) if j<len(active) else 0.0 for i,j in zip(ri.tolist(),cj.tolist()) if i<len(labels)]
    return {'eligible_showers':len(labels),'macro_f1':float(np.mean(vals)) if vals else 0.0,'recovered_f1_gt_0_5':sum(v>0.5 for v in vals),'candidate_used':len(active)}

def find_truth(root,route,year):
    xs=list(root.rglob(f'truth_{route}_{year}.json')); req(len(xs)==1,f'truth file missing {route} {year}: {xs}'); return json.loads(xs[0].read_text())

def run_eval(pretruth, truth_root, out):
    out.mkdir(parents=True,exist_ok=True); p=json.loads(pretruth.read_text()); req(p['truth_accessed'] is False,'pretruth contaminated')
    panels=[]; wins=0
    for route in ROUTES:
        comp=p['routes'][route]['comparator']['families']; rec=p['routes'][route]['recurrent_candidates']
        for y in YEARS:
            truth=find_truth(truth_root,route,y)
            c=score(comp,truth,None); B=c['candidate_used']; r=score(rec,truth,B)
            passed=r['macro_f1']>c['macro_f1'] and r['recovered_f1_gt_0_5']>=c['recovered_f1_gt_0_5']; wins+=int(passed)
            panels.append({'route':route,'year':y,'budget':B,'recurrent':r,'literature':c,'passed':passed,'macro_f1_delta':r['macro_f1']-c['macro_f1']})
    res={'verdict':'PASS_TEMPORAL_FAIR_LITERATURE_4_OF_4' if wins==4 else f'FAIL_TEMPORAL_FAIR_LITERATURE_{wins}_OF_4','panel_wins':wins,'panels':panels,'temporal_information':'all methods receive pooled 2013+2014 label-free rows before truth','truth_loaded_only_after_pretruth':True,'sonotaco_role':'EXPOSED_DIAGNOSTIC_NOT_PRISTINE_EXTERNAL_VALIDATION'}
    q=out/'POOLED_FAIR_RESULT.json'; q.write_text(json.dumps(res,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps(res,indent=2))

def main():
    a=argparse.ArgumentParser(); sub=a.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('pretruth'); p.add_argument('--rows-root',type=Path,required=True); p.add_argument('--sources',type=Path,required=True); p.add_argument('--recurrent',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    e=sub.add_parser('evaluate'); e.add_argument('--pretruth',type=Path,required=True); e.add_argument('--truth-root',type=Path,required=True); e.add_argument('--output',type=Path,required=True)
    x=a.parse_args(); run_pretruth(x.rows_root,x.sources,x.recurrent,x.output) if x.cmd=='pretruth' else run_eval(x.pretruth,x.truth_root,x.output)
if __name__=='__main__': main()
