#!/usr/bin/env python3
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
from persistable import Persistable
from persistable.persistable_interactive import (
    compute_defaults,
    X_START_LINE, Y_START_LINE, X_END_LINE, Y_END_LINE,
)

SEEDS=(202608160,202608161,202608162,202608163)
N_DENSE=6144
N_SPARSE=768
MIN_SUPPORT=4
MAX_G=15
CENTERS=np.asarray([[2,0,0,0],[-2,0,0,0],[0,2,0,0],[0,-2,0,0],[0,0,2,0],[0,0,-2,0]],dtype=float)
WEIGHTS=np.asarray([.18,.15,.13,.11,.09,.07,.27])
SIGMAS=np.asarray([.22,.28,.34,.40,.46,.52])


def req(ok,msg):
    if not ok: raise RuntimeError(msg)


def make_data(seed):
    rng=np.random.default_rng(np.random.PCG64(seed))
    z=rng.choice(7,size=N_DENSE,p=WEIGHTS)
    X=np.empty((N_DENSE,4),float)
    for j in range(6):
        ix=np.flatnonzero(z==j)
        X[ix]=CENTERS[j]+SIGMAS[j]*rng.standard_normal((len(ix),4))
    bg=np.flatnonzero(z==6)
    X[bg]=rng.uniform(-4,4,size=(len(bg),4))
    req(np.all(np.isfinite(X)),"nonfinite synthetic data")
    return X


def member_key(ix):
    return tuple(int(x) for x in np.sort(np.asarray(ix,dtype=np.int64)))


def ladder_candidates(X):
    with warnings.catch_warnings(record=True) as ws:
        warnings.simplefilter('always')
        p=Persistable(X,n_neighbors='auto',n_jobs=1)
        extent=np.asarray(p._find_end(),float)
        req(extent.shape==(2,) and np.all(np.isfinite(extent)) and np.all(extent>0),f'invalid extent {extent}')
        defaults,_=compute_defaults(extent,p._default_granularity())
        start=np.asarray([defaults[X_START_LINE],defaults[Y_START_LINE]],float)
        end=np.asarray([defaults[X_END_LINE],defaults[Y_END_LINE]],float)
        req(start.shape==(2,) and end.shape==(2,) and np.all(np.isfinite(start)) and np.all(np.isfinite(end)),'invalid midpoint slice')
        hc=p._bifiltration.lambda_linkage(start,end)
        pd=np.asarray(hc.persistence_diagram(),float)
        req(pd.ndim==2 and pd.shape[1]==2 and np.all(np.isfinite(pd)),'invalid persistence diagram')
        prom=np.abs(pd[:,1]-pd[:,0])
        B=int(np.sum(prom>1e-12))
        req(B>=2,f'too few positive bars {B}')
        maxg=min(MAX_G,B)
        memberships={}
        per_g=[]
        for g in range(2,maxg+1):
            threshold=float(hc._compute_threshold(g))
            req(np.isfinite(threshold),'nonfinite threshold')
            labels=np.asarray(hc.persistence_based_flattening(threshold,flattening_mode='conservative',keep_low_persistence_clusters=False),dtype=np.int64)
            req(labels.shape==(len(X),),f'bad labels g={g}')
            retained=0
            for lab in sorted(int(x) for x in np.unique(labels) if int(x)>=0):
                ix=np.flatnonzero(labels==lab)
                if len(ix)>=MIN_SUPPORT:
                    key=member_key(ix)
                    memberships[key]=key
                    retained+=1
            per_g.append({'g':g,'threshold':threshold,'retained_clusters':retained})
        warn=[str(w.message) for w in ws]
    req(not any('enough neighbors' in s.lower() for s in warn),f'insufficient-neighbor warning {warn}')
    candidates=[frozenset(k) for k in memberships]
    req(len(candidates)<=119,f'candidate ceiling violated {len(candidates)}')
    return candidates, {'find_end':extent.tolist(),'midpoint_slice':[start.tolist(),end.tolist()],'positive_bar_count':B,'max_requested_g':maxg,'candidate_count':len(candidates),'per_g':per_g,'warnings':warn}


def coherence(dense,sparse):
    universe=frozenset(range(N_SPARSE))
    rd=[]
    for c in dense:
        r=frozenset(c.intersection(universe))
        if len(r)>=MIN_SUPPORT: rd.append(r)
    def directional(A,B):
        vals=[]
        for a in A:
            best=0.0
            for b in B:
                inter=len(a.intersection(b))
                if inter: best=max(best,inter/len(a.union(b)))
            vals.append(best)
        return float(np.mean(vals)) if vals else 0.0
    s2d=directional(sparse,rd)
    d2s=directional(rd,sparse)
    return {'sparse_to_dense_mean_best_jaccard':s2d,'dense_to_sparse_mean_best_jaccard':d2s,'symmetric_mean_best_jaccard':(s2d+d2s)/2,'restricted_dense_candidate_count':len(rd),'sparse_candidate_count':len(sparse)}


def main():
    out=Path('output'); out.mkdir(exist_ok=True)
    rows=[]; overall=True
    for seed in SEEDS:
        X=make_data(seed)
        dense,ds=ladder_candidates(X)
        sparse,ss=ladder_candidates(X[:N_SPARSE])
        c=coherence(dense,sparse)
        gates={
            'dense_nonempty':len(dense)>0,
            'sparse_nonempty':len(sparse)>0,
            'candidate_ceiling':len(dense)<=119 and len(sparse)<=119,
            'symmetric_at_least_060':c['symmetric_mean_best_jaccard']>=.60,
            'both_directions_at_least_050':c['sparse_to_dense_mean_best_jaccard']>=.50 and c['dense_to_sparse_mean_best_jaccard']>=.50,
        }
        passed=all(gates.values()); overall=overall and passed
        row={'seed':seed,'dense':ds,'sparse':ss,'coherence':c,'gates':gates,'pass':passed}
        rows.append(row); print(json.dumps(row,sort_keys=True),flush=True)
    verdict='PASS_PERSISTABLE_LADDER_SYNTHETIC_FEASIBILITY' if overall else 'FAIL_PERSISTABLE_LADDER_SYNTHETIC_FEASIBILITY'
    result={'schema':'ORBITTRACE_PERSISTABLE_LADDER_AUDIT_V1','verdict':verdict,'upstream_persistable_commit':'7eb75b2e8d2fe5a18e49248aa7d1c97f829415be','meteor_data_access':False,'target_information_access':False,'manual_parameter_selection':False,'replicates':rows}
    (out/'PERSISTABLE_LADDER_SYNTHETIC_AUDIT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':verdict},indent=2))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
