#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial.distance import pdist
from scipy.stats import spearmanr
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.neighbors import NearestNeighbors

from orbittrace_gmn_sonotaco_domainshift_diagnostic_v1 import run_diagnostic as base

SOURCES=("hard","p19","p20")
EXPECTED_BASELINE_ARTIFACT_AUC=0.88356922921475
AUC_REDUCTION_GATE=0.10
SPEARMAN_GATE=0.90
NN_RETENTION_GATE=0.70
SVD_REL_TOL=1e-12
SEED=20260809


def req(cond: bool, msg: str) -> None:
    if not cond:
        raise RuntimeError(msg)


def domain_model() -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(
        learning_rate=0.05,
        max_iter=250,
        max_leaf_nodes=31,
        l2_regularization=1.0,
        random_state=SEED,
    )


def fisher_mean(values: list[float]) -> float:
    a=np.asarray(values,dtype=float)
    req(a.size>0 and np.isfinite(a).all(),"invalid Fisher correlation inputs")
    a=np.clip(a,-1.0+1e-12,1.0-1e-12)
    return float(np.tanh(np.mean(np.arctanh(a))))


def pairwise_spearman(a: np.ndarray, b: np.ndarray) -> float:
    req(a.shape==b.shape and a.ndim==2 and len(a)>=3,"invalid structure arrays")
    da=pdist(a,metric="euclidean")
    db=pdist(b,metric="euclidean")
    r=float(spearmanr(da,db).statistic)
    req(np.isfinite(r),"non-finite pairwise Spearman")
    return r


def nn_retention(a: np.ndarray, b: np.ndarray, k: int=10) -> float:
    req(a.shape==b.shape and a.ndim==2 and len(a)>=2,"invalid neighbor arrays")
    kk=min(k,len(a)-1)
    na=NearestNeighbors(n_neighbors=kk+1,metric="euclidean").fit(a).kneighbors(a,return_distance=False)[:,1:]
    nb=NearestNeighbors(n_neighbors=kk+1,metric="euclidean").fit(b).kneighbors(b,return_distance=False)[:,1:]
    vals=[]
    for i in range(len(a)):
        vals.append(len(set(map(int,na[i])) & set(map(int,nb[i]))) / float(kk))
    return float(np.mean(vals))


def project_fold(xtr: np.ndarray, xte: np.ndarray, dtr: np.ndarray, str_: np.ndarray) -> tuple[np.ndarray,np.ndarray,np.ndarray,int,np.ndarray,np.ndarray]:
    mu=np.mean(xtr,axis=0)
    sd=np.std(xtr,axis=0,ddof=0)
    sd=np.where(sd>0.0,sd,1.0)
    ztr=(xtr-mu)/sd
    zte=(xte-mu)/sd
    rows=[]
    for s in SOURCES:
        m0=(dtr==0)&(str_==s)
        m1=(dtr==1)&(str_==s)
        req(int(np.sum(m0))>0 and int(np.sum(m1))>0,f"missing fold-training domain/source stratum {s}")
        rows.append(np.mean(ztr[m1],axis=0)-np.mean(ztr[m0],axis=0))
    delta=np.asarray(rows,dtype=float)
    req(delta.shape==(3,21) and np.isfinite(delta).all(),"invalid nuisance difference matrix")
    _u,svals,vt=np.linalg.svd(delta,full_matrices=False)
    req(svals.size==3 and np.isfinite(svals).all() and float(np.max(svals))>0.0,"degenerate nuisance SVD")
    rank=int(np.sum(svals > float(np.max(svals))*SVD_REL_TOL))
    req(1<=rank<=3,"nuisance rank outside frozen range")
    v=vt[:rank]
    ptr=ztr-(ztr@v.T)@v
    pte=zte-(zte@v.T)@v
    req(np.isfinite(ptr).all() and np.isfinite(pte).all(),"non-finite projected features")
    return ptr,pte,v,rank,svals,zte


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--quality-source",type=Path,required=True)
    p.add_argument("--purity-source",type=Path,required=True)
    p.add_argument("--v8-result-json",type=Path,required=True)
    p.add_argument("--p19-result-json",type=Path,required=True)
    p.add_argument("--p19-prelabel-json",type=Path,required=True)
    p.add_argument("--p20-result-json",type=Path,required=True)
    p.add_argument("--p20-prelabel-json",type=Path,required=True)
    p.add_argument("--prepared",type=Path,required=True)
    p.add_argument("--support-source-parts",type=Path,required=True)
    p.add_argument("--candidate-payload",type=Path,required=True)
    p.add_argument("--baseline-payload",type=Path,required=True)
    p.add_argument("--scorer-parts",type=Path,required=True)
    p.add_argument("--expected-domainshift-json",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)

    expected=json.loads(a.expected_domainshift_json.read_text())
    expected_auc=float(expected["domain_classifier"]["overall_roc_auc"])
    req(abs(expected_auc-EXPECTED_BASELINE_ARTIFACT_AUC)<1e-15,"authoritative domain-shift artifact changed")
    req(expected.get("sonotaco_shower_truth_accessed") is False,"expected artifact truth firewall changed")
    req(expected.get("literature_evaluation_performed") is False,"expected artifact literature firewall changed")

    state: dict[str,Any]={"folds":None,"domain":None,"source":None,"ids":None,"x":None,"pred":None,"call":0}
    orig_assign=base.assign_folds

    def capture_assign(domains: np.ndarray, sources: np.ndarray, ids: list[str]) -> np.ndarray:
        folds=orig_assign(domains,sources,ids)
        state["folds"]=np.asarray(folds,dtype=int).copy()
        state["domain"]=np.asarray(domains,dtype=int).copy()
        state["source"]=np.asarray(sources,dtype=object).copy()
        state["ids"]=list(ids)
        state["x"]=np.full((len(ids),21),np.nan,dtype=float)
        state["pred"]=np.full(len(ids),np.nan,dtype=float)
        return folds

    class CaptureModel:
        def __init__(self) -> None:
            self.model=domain_model()
            self.fold=int(state["call"])
            state["call"]=self.fold+1
        def fit(self,x: np.ndarray,y: np.ndarray,sample_weight: np.ndarray|None=None) -> "CaptureModel":
            self.model.fit(x,y,sample_weight=sample_weight); return self
        def predict_proba(self,x: np.ndarray) -> np.ndarray:
            pr=self.model.predict_proba(x)
            folds=np.asarray(state["folds"])
            mask=folds==self.fold
            req(int(np.sum(mask))==len(x),f"capture fold-size mismatch {self.fold}")
            state["x"][mask]=x
            state["pred"][mask]=pr[:,1]
            return pr

    base.assign_folds=capture_assign
    base.domain_model=lambda: CaptureModel()
    base_out=a.output/"baseline_reproduction"
    argv=[
        "run_diagnostic.py",
        "--quality-source",str(a.quality_source),"--purity-source",str(a.purity_source),
        "--v8-result-json",str(a.v8_result_json),"--p19-result-json",str(a.p19_result_json),
        "--p19-prelabel-json",str(a.p19_prelabel_json),"--p20-result-json",str(a.p20_result_json),
        "--p20-prelabel-json",str(a.p20_prelabel_json),"--prepared",str(a.prepared),
        "--support-source-parts",str(a.support_source_parts),"--candidate-payload",str(a.candidate_payload),
        "--baseline-payload",str(a.baseline_payload),"--scorer-parts",str(a.scorer_parts),
        "--output",str(base_out),
    ]
    old_argv=sys.argv
    try:
        sys.argv=argv
        rc=base.main()
    finally:
        sys.argv=old_argv
        base.assign_folds=orig_assign
    req(rc==0,"baseline diagnostic reconstruction failed")

    x=np.asarray(state["x"],dtype=float); domain=np.asarray(state["domain"],dtype=int); source=np.asarray(state["source"],dtype=object); folds=np.asarray(state["folds"],dtype=int); base_pred=np.asarray(state["pred"],dtype=float)
    req(x.shape==(4838,21) and np.isfinite(x).all(),"captured 21D matrix invalid")
    req(np.isfinite(base_pred).all() and int(state["call"])==5,"baseline capture incomplete")
    baseline_auc=float(roc_auc_score(domain,base_pred))
    baseline_bacc=float(balanced_accuracy_score(domain,base_pred>=0.5))
    req(abs(baseline_auc-expected_auc)<1e-12,f"baseline AUC reproduction mismatch: {baseline_auc} vs {expected_auc}")

    pred=np.full(len(x),np.nan,dtype=float)
    fold_diag=[]
    corr_by_domain={0:[],1:[]}
    nn_by_domain={0:[],1:[]}
    for fold in range(5):
        tr=folds!=fold; te=folds==fold
        ptr,pte,v,rank,svals,zte=project_fold(x[tr],x[te],domain[tr],source[tr])
        n0=int(np.sum(tr&(domain==0))); n1=int(np.sum(tr&(domain==1)))
        weights=np.zeros(len(x),dtype=float)
        weights[tr&(domain==0)]=float(np.sum(tr))/(2.0*n0)
        weights[tr&(domain==1)]=float(np.sum(tr))/(2.0*n1)
        model=domain_model(); model.fit(ptr,domain[tr],sample_weight=weights[tr]); pred[te]=model.predict_proba(pte)[:,1]
        local_domain=domain[te]
        struct={}
        for d,label in ((0,"gmn"),(1,"sonotaco")):
            m=local_domain==d
            rho=pairwise_spearman(zte[m],pte[m])
            nn=nn_retention(zte[m],pte[m],10)
            corr_by_domain[d].append(rho); nn_by_domain[d].append(nn)
            struct[label]={"pairwise_distance_spearman":rho,"nn10_retention":nn,"count":int(np.sum(m))}
        fold_diag.append({
            "fold":fold,"nuisance_rank":rank,"singular_values":[float(q) for q in svals],
            "removed_basis_frobenius_norm":float(np.linalg.norm(v)),"structure":struct,
        })

    req(np.isfinite(pred).all(),"successor predictions incomplete")
    successor_auc=float(roc_auc_score(domain,pred))
    successor_bacc=float(balanced_accuracy_score(domain,pred>=0.5))
    reduction=float(baseline_auc-successor_auc)
    gmn_rho=fisher_mean(corr_by_domain[0]); sono_rho=fisher_mean(corr_by_domain[1])
    gmn_nn=float(np.mean(nn_by_domain[0])); sono_nn=float(np.mean(nn_by_domain[1]))
    gates={
        "baseline_exact_reproduction":abs(baseline_auc-expected_auc)<1e-12,
        "auc_reduction_ge_0_10":reduction>=AUC_REDUCTION_GATE,
        "gmn_pairwise_spearman_ge_0_90":gmn_rho>=SPEARMAN_GATE,
        "sonotaco_pairwise_spearman_ge_0_90":sono_rho>=SPEARMAN_GATE,
        "gmn_nn10_retention_ge_0_70":gmn_nn>=NN_RETENTION_GATE,
        "sonotaco_nn10_retention_ge_0_70":sono_nn>=NN_RETENTION_GATE,
        "rank_1_to_3_all_folds":all(1<=int(z["nuisance_rank"])<=3 for z in fold_diag),
    }
    passed=all(gates.values())
    result={
        "stage":"GMN_SONOTACO_NUISANCE_NULLSPACE_REPRESENTATION_DIAGNOSTIC_V1",
        "verdict":"PASS_NUISANCE_NULLSPACE_V1_TRUTH_FREE_REPRESENTATION_GATE" if passed else "FAIL_NUISANCE_NULLSPACE_V1_TRUTH_FREE_REPRESENTATION_GATE",
        "feature_dimension":21,"removed_rank_max":3,"svd_relative_tolerance":SVD_REL_TOL,
        "baseline_domain_auc":baseline_auc,"baseline_balanced_accuracy":baseline_bacc,
        "successor_domain_auc":successor_auc,"successor_balanced_accuracy":successor_bacc,"domain_auc_reduction":reduction,
        "structure":{"gmn_pairwise_distance_spearman":gmn_rho,"sonotaco_pairwise_distance_spearman":sono_rho,"gmn_nn10_retention":gmn_nn,"sonotaco_nn10_retention":sono_nn},
        "gates":gates,"fold_diagnostics":fold_diag,
        "successor_scientific_ranker_trained":False,"sonotaco_shower_truth_accessed":False,"literature_evaluation_performed":False,"matched_comparator_rows_used":False,
        "target_information_access":False,"target_region_events_accessed":False,"maarsy_scientific_access":False,"dms_scientific_access":False,
        "robust_scaling_used":False,"feature_subset_selected":False,"nuisance_rank_selected":False,"threshold_search":False,"post_result_second_search":False,
    }
    out=a.output/"GMN_SONOTACO_NUISANCE_NULLSPACE_REPRESENTATION_DIAGNOSTIC_V1.json"
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
