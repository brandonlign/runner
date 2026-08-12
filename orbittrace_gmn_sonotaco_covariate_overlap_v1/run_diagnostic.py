#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from orbittrace_gmn_sonotaco_domainshift_diagnostic_v1 import run_diagnostic as base

SOURCES=("hard","p19","p20")
EXPECTED_BASELINE_AUC=0.88356922921475
SEED=20260809

OVERALL_ESS_FRACTION_GATE=0.25
SOURCE_ESS_FRACTION_GATE=0.20
OVERALL_MAX_SHARE_GATE=0.01
SOURCE_MAX_SHARE_GATE=0.05
OVERALL_OVERLAP_GATE=0.30
SOURCE_OVERLAP_GATE=0.20


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


def qstats(x: np.ndarray) -> dict[str,float]:
    req(x.ndim==1 and x.size>0 and np.isfinite(x).all(),"invalid weight vector")
    return {
        "min":float(np.min(x)),
        "q01":float(np.quantile(x,0.01)),
        "q05":float(np.quantile(x,0.05)),
        "q25":float(np.quantile(x,0.25)),
        "median":float(np.median(x)),
        "q75":float(np.quantile(x,0.75)),
        "q95":float(np.quantile(x,0.95)),
        "q99":float(np.quantile(x,0.99)),
        "max":float(np.max(x)),
        "mean":float(np.mean(x)),
    }


def weight_stats(w: np.ndarray) -> dict[str,Any]:
    req(w.ndim==1 and w.size>0 and np.isfinite(w).all() and np.all(w>0.0),"invalid density-ratio weights")
    sw=float(np.sum(w)); sw2=float(np.sum(w*w)); req(sw>0.0 and sw2>0.0,"degenerate weight sums")
    ess=float(sw*sw/sw2)
    return {
        "count":int(len(w)),
        "weight_quantiles":qstats(w),
        "ess":ess,
        "ess_fraction":float(ess/len(w)),
        "max_normalized_share":float(np.max(w)/sw),
    }


def overlap_score(prob: np.ndarray, domain: np.ndarray) -> float:
    req(prob.ndim==1 and domain.shape==prob.shape,"invalid overlap inputs")
    vals=2.0*np.minimum(prob,1.0-prob)
    m0=domain==0; m1=domain==1
    req(m0.any() and m1.any(),"overlap domain missing")
    return float(0.5*np.mean(vals[m0])+0.5*np.mean(vals[m1]))


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
    req(abs(expected_auc-EXPECTED_BASELINE_AUC)<1e-15,"authoritative domain-shift artifact changed")
    req(expected.get("sonotaco_shower_truth_accessed") is False,"authoritative artifact truth firewall changed")
    req(expected.get("literature_evaluation_performed") is False,"authoritative artifact literature firewall changed")

    state: dict[str,Any]={"folds":None,"domain":None,"source":None,"ids":None,"pred":None,"call":0}
    orig_assign=base.assign_folds
    orig_model=base.domain_model

    def capture_assign(domains: np.ndarray, sources: np.ndarray, ids: list[str]) -> np.ndarray:
        folds=orig_assign(domains,sources,ids)
        state["folds"]=np.asarray(folds,dtype=int).copy()
        state["domain"]=np.asarray(domains,dtype=int).copy()
        state["source"]=np.asarray(sources,dtype=object).copy()
        state["ids"]=list(ids)
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
            folds=np.asarray(state["folds"],dtype=int)
            mask=folds==self.fold
            req(int(np.sum(mask))==len(x),f"capture fold-size mismatch {self.fold}")
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
        base.domain_model=orig_model
    req(rc==0,"baseline domain diagnostic reconstruction failed")

    domain=np.asarray(state["domain"],dtype=int)
    source=np.asarray(state["source"],dtype=object)
    pred=np.asarray(state["pred"],dtype=float)
    req(domain.shape==(4838,) and source.shape==(4838,) and pred.shape==(4838,),"captured diagnostic shape changed")
    req(int(state["call"])==5 and np.isfinite(pred).all(),"domain OOF capture incomplete")
    req(np.all((pred>0.0)&(pred<1.0)),"domain posterior reached 0 or 1; untrimmed odds undefined")
    baseline_auc=float(roc_auc_score(domain,pred))
    req(abs(baseline_auc-expected_auc)<1e-12,f"baseline AUC mismatch {baseline_auc} vs {expected_auc}")

    gmask=domain==0
    weights=pred[gmask]/(1.0-pred[gmask])
    req(np.isfinite(weights).all() and np.all(weights>0.0),"nonfinite/nonpositive GMN density-ratio weight")
    gsource=source[gmask]

    overall=weight_stats(weights)
    by_source={}
    overlap_by_source={}
    for s in SOURCES:
        wm=weights[gsource==s]
        by_source[s]=weight_stats(wm)
        sm=source==s
        overlap_by_source[s]=overlap_score(pred[sm],domain[sm])
    overlap_overall=overlap_score(pred,domain)

    gates={
        "baseline_exact_reproduction":abs(baseline_auc-expected_auc)<1e-12,
        "probabilities_and_weights_strictly_finite_positive":bool(np.isfinite(pred).all() and np.all((pred>0.0)&(pred<1.0)) and np.isfinite(weights).all() and np.all(weights>0.0)),
        "overall_ess_fraction_ge_0_25":overall["ess_fraction"]>=OVERALL_ESS_FRACTION_GATE,
        "all_source_ess_fraction_ge_0_20":all(by_source[s]["ess_fraction"]>=SOURCE_ESS_FRACTION_GATE for s in SOURCES),
        "overall_max_normalized_share_le_0_01":overall["max_normalized_share"]<=OVERALL_MAX_SHARE_GATE,
        "all_source_max_normalized_share_le_0_05":all(by_source[s]["max_normalized_share"]<=SOURCE_MAX_SHARE_GATE for s in SOURCES),
        "overall_overlap_ge_0_30":overlap_overall>=OVERALL_OVERLAP_GATE,
        "all_source_overlap_ge_0_20":all(overlap_by_source[s]>=SOURCE_OVERLAP_GATE for s in SOURCES),
    }
    passed=all(gates.values())

    result={
        "stage":"GMN_SONOTACO_COVARIATE_OVERLAP_DIAGNOSTIC_V1",
        "verdict":"PASS_COVARIATE_OVERLAP_V1_IMPORTANCE_WEIGHTING_FEASIBLE" if passed else "FAIL_COVARIATE_OVERLAP_V1_IMPORTANCE_WEIGHTING_INFEASIBLE",
        "baseline_domain_auc":baseline_auc,
        "density_ratio_formula":"equal-prior cross-fitted domain posterior odds e/(1-e)",
        "overall_gmn_weight_stats":overall,
        "by_source_gmn_weight_stats":by_source,
        "overlap_coefficient":overlap_overall,
        "overlap_coefficient_by_source":overlap_by_source,
        "gates":gates,
        "feature_dimension":21,
        "feature_representation_changed":False,
        "weight_clipping_or_trimming":False,
        "weight_exponent_or_temperature_search":False,
        "alternate_density_ratio_estimator_search":False,
        "scientific_shower_ranker_trained":False,
        "sonotaco_shower_truth_accessed":False,
        "literature_evaluation_performed":False,
        "matched_comparator_rows_used":False,
        "target_information_access":False,
        "target_region_events_accessed":False,
        "maarsy_scientific_access":False,
        "dms_scientific_access":False,
        "post_result_second_search":False,
    }
    out=a.output/"GMN_SONOTACO_COVARIATE_OVERLAP_DIAGNOSTIC_V1.json"
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
