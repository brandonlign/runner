#!/usr/bin/env python3
"""GMN development lab: strict-group event-level calibration of frozen P12 halo additions."""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score

from orbittrace_label_free_sparse_support_v6 import run_development as v6

mult = v6.mult
YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
EXPECTED_FAMILIES = 226
EXPECTED_V8_MACRO = 0.1736657194465356
EXPECTED_P12_MACRO = 0.37661279333940806
SIZE_BINS = (("4-9",4,9),("10-24",10,24),("25-49",25,49),("50-99",50,99),("100+",100,None))


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def parse_args() -> argparse.Namespace:
    p=argparse.ArgumentParser()
    p.add_argument("--support-source-parts",type=Path,required=True)
    p.add_argument("--candidate-payload",type=Path,required=True)
    p.add_argument("--baseline-payload",type=Path,required=True)
    p.add_argument("--scorer-parts",type=Path,required=True)
    p.add_argument("--v8-result-json",type=Path,required=True)
    p.add_argument("--p12-dir",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    return p.parse_args()


def load_gz(path: Path) -> Any:
    with gzip.open(path,"rt",encoding="utf-8") as h:
        return json.load(h)


def core_from_expanded(f: dict[str,Any]) -> dict[str,Any]:
    added={str(x) for x in f.get("p2_added_event_ids",[])}
    out=copy.deepcopy(f)
    out["event_ids"]=[str(x) for x in f["event_ids"] if str(x) not in added]
    out["event_count"]=len(out["event_ids"])
    out["p2_added_event_ids"]=[]
    out["p2_added_event_count"]=0
    return out


def eligible_labels(hidden: dict[str,str]) -> dict[str,Counter[int]]:
    counts: dict[str,Counter[int]]=defaultdict(Counter)
    for eid,label in hidden.items():
        if label=="SPORADIC": continue
        y=int(str(eid)[:4])
        if y in YEARS: counts[label][y]+=1
    return {lab:per for lab,per in counts.items() if sum(per.values())>=8 and all(per.get(y,0)>=4 for y in YEARS)}


def catalogue_metrics(hidden: dict[str,str], families: list[dict[str,Any]], order: list[str]) -> dict[str,Any]:
    by={str(f["family_id"]):f for f in families}
    require(set(by)==set(order),"order/family universe mismatch")
    rank={fid:i+1 for i,fid in enumerate(order)}
    elig=eligible_labels(hidden)
    per={}
    qual=set(); r25=set(); r50=set(); r100=set(); r500=set()
    for label,peryear in elig.items():
        total=sum(peryear.values())
        best={"f1":0.0,"precision":0.0,"recall":0.0,"overlap":0,"family_id":None,"rank":None}
        for fid,f in by.items():
            ids=[str(x) for x in f["event_ids"]]
            ov=sum(hidden.get(eid)==label for eid in ids)
            if ov<=0: continue
            precision=ov/len(ids); recall=ov/total
            f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
            cand=(f1,precision,ov,-rank[fid])
            cur=(best["f1"],best["precision"],best["overlap"],-(best["rank"] or 10**9))
            if cand>cur:
                best={"f1":float(f1),"precision":float(precision),"recall":float(recall),"overlap":int(ov),"family_id":fid,"rank":rank[fid]}
            if ov>=4 and precision>=0.5:
                qual.add(label)
                if rank[fid]<=25:r25.add(label)
                if rank[fid]<=50:r50.add(label)
                if rank[fid]<=100:r100.add(label)
                if rank[fid]<=500:r500.add(label)
        per[label]=best
    top=order[:100]
    dom=[]
    for fid in top:
        f=by[fid]; ids=[str(x) for x in f["event_ids"]]
        c=Counter(hidden.get(eid,"SPORADIC") for eid in ids); c.pop("SPORADIC",None)
        dom.append((c.most_common(1)[0][1]/len(ids)) if c and ids else 0.0)
    return {
        "eligible_labels":len(elig),
        "qualified_matches":len(qual),
        "recovered_at_25":len(r25),"recovered_at_50":len(r50),"recovered_at_100":len(r100),"recovered_at_500":len(r500),
        "best_membership_macro_f1_all_eligible":float(np.mean([r["f1"] for r in per.values()])),
        "top100_dominant_precision":float(np.mean(dom)),
        "per_label":per,
    }


def annual_metrics(hidden:dict[str,str],families:list[dict[str,Any]])->dict[str,Any]:
    out={}
    for year in YEARS:
        counts=Counter(label for eid,label in hidden.items() if int(str(eid)[:4])==year and label!="SPORADIC")
        rows={}
        for label,total in sorted(counts.items()):
            if total<4:continue
            best={"f1":0.0,"precision":0.0,"recall":0.0}
            for f in families:
                ids=[str(eid) for eid in f["event_ids"] if int(str(eid)[:4])==year]
                if not ids:continue
                ov=sum(hidden.get(eid)==label for eid in ids)
                if not ov:continue
                p=ov/len(ids); r=ov/total; f1=2*p*r/(p+r) if p+r else 0.0
                if (f1,p,ov)>(best["f1"],best["precision"],best.get("overlap",0)):
                    best={"f1":float(f1),"precision":float(p),"recall":float(r),"overlap":int(ov)}
            rows[label]={"total":int(total),**best}
        bins={}
        for name,lo,hi in SIZE_BINS:
            rr=[r for r in rows.values() if r["total"]>=lo and (hi is None or r["total"]<=hi)]
            bins[name]={"showers":len(rr),"mean_f1":float(np.mean([r["f1"] for r in rr])) if rr else 0.0}
        bins["all"]={"showers":len(rows),"mean_f1":float(np.mean([r["f1"] for r in rows.values()])) if rows else 0.0}
        out[str(year)]=bins
    return out


def family_target(hidden:dict[str,str],core:dict[str,Any])->tuple[str|None,float,int]:
    ids=[str(x) for x in core["event_ids"]]
    c=Counter(hidden.get(eid,"SPORADIC") for eid in ids); c.pop("SPORADIC",None)
    if not c:return None,0.0,0
    label,ov=c.most_common(1)[0]; purity=ov/len(ids)
    return (label if ov>=4 and purity>=0.5 else None),float(purity),int(ov)


def safe_ratio(a:float,b:float,default:float=0.0)->float:
    if not math.isfinite(a) or not math.isfinite(b) or abs(b)<1e-12:return default
    return float(a/b)


def make_rows(hidden:dict[str,str],cores:list[dict[str,Any]],expanded:list[dict[str,Any]],assignments:dict[str,dict[str,Any]]) -> tuple[np.ndarray,np.ndarray,list[str],list[str],dict[str,Any]]:
    core_by={str(f["family_id"]):f for f in cores}; exp_by={str(f["family_id"]):f for f in expanded}
    target_by={}; family_meta={}
    add_count=Counter(str(r["family_id"]) for r in assignments.values())
    for fid,core in core_by.items():
        target,purity,ov=family_target(hidden,core); target_by[fid]=target
        ys=[float(x) for x in core.get("year_strengths",{}).values()]
        family_meta[fid]={
            "core_count":len(core["event_ids"]),"addition_count":add_count.get(fid,0),
            "expansion_ratio":add_count.get(fid,0)/max(1,len(core["event_ids"])),
            "anchor_count":int(core.get("anchor_count",0)),"quartet_count":int(core.get("quartet_count",0)),
            "component_count":int(core.get("component_count",0)),"best_score":float(core.get("best_score",0.0)),
            "strength_balance":min(ys)/max(ys) if ys and max(ys)>0 else 0.0,
            "core_truth_label":target,"core_truth_purity":purity,"core_truth_overlap":ov,
        }
    X=[]; y=[]; groups=[]; eids=[]
    for eid,row in sorted(assignments.items()):
        fid=str(row["family_id"]); fm=family_meta[fid]; target=target_by[fid]
        dens_thr=float(row["p11_density_threshold"]); dens_score=float(row["p11_density_score"])
        density_ratio=safe_ratio(dens_score,dens_thr,0.0) if math.isfinite(dens_thr) else 0.0
        feat=[
            float(row["responsibility"]),
            float(row["responsibility"])-float(row["membership_floor"]),
            float(row["membership_floor"]),
            float(row["seed_floor"]),
            safe_ratio(float(row["d_drift"]),float(row["obs_ceiling"]),1.0),
            safe_ratio(float(row["d_orb"]),float(row["orb_ceiling"]),1.0),
            density_ratio,
            math.log1p(max(0.0,float(row["odds"]))),
            float(row["membership_floor_rank"]),
            float(row["p11_density_rank"]),
            1.0 if int(row["target_year"])>int(row["source_year"]) else 0.0,
            math.log1p(fm["core_count"]),math.log1p(fm["addition_count"]),float(fm["expansion_ratio"]),
            math.log1p(max(0,fm["anchor_count"])),math.log1p(max(0,fm["quartet_count"])),math.log1p(max(0,fm["component_count"])),
            float(fm["best_score"]),float(fm["strength_balance"]),
        ]
        X.append(feat)
        good=bool(target is not None and hidden.get(str(eid))==target)
        y.append(int(good)); groups.append(target if target is not None else "BG:"+fid); eids.append(str(eid))
    return np.asarray(X,float),np.asarray(y,int),groups,eids,{"family_meta":family_meta,"target_by_family":target_by}


def balanced_group_folds(groups:list[str],nfold:int=5)->list[int]:
    counts=Counter(groups)
    fold_load=[0]*nfold; assignment={}
    ordered=sorted(counts,key=lambda g:(-counts[g],hashlib.sha256(g.encode()).hexdigest()))
    for g in ordered:
        f=min(range(nfold),key=lambda i:(fold_load[i],i)); assignment[g]=f; fold_load[f]+=counts[g]
    return [assignment[g] for g in groups]


def sample_weights(y:np.ndarray,groups:list[str])->np.ndarray:
    gc=Counter(groups); class_count=Counter(int(v) for v in y)
    w=np.asarray([1.0/gc[g] for g in groups],float)
    # Equalize positive/negative total influence after equalizing groups.
    sums={c:float(w[y==c].sum()) for c in class_count}
    for c,s in sums.items():
        if s>0:w[y==c]*=1.0/s
    w*=len(w)/w.sum()
    return w


def model_factories()->list[tuple[str,Any]]:
    return [
        ("ET_d4_l10",lambda:ExtraTreesClassifier(n_estimators=500,max_depth=4,min_samples_leaf=10,max_features="sqrt",random_state=1729,n_jobs=-1,class_weight=None)),
        ("ET_d6_l10",lambda:ExtraTreesClassifier(n_estimators=500,max_depth=6,min_samples_leaf=10,max_features="sqrt",random_state=1729,n_jobs=-1,class_weight=None)),
        ("ET_d8_l10",lambda:ExtraTreesClassifier(n_estimators=500,max_depth=8,min_samples_leaf=10,max_features="sqrt",random_state=1729,n_jobs=-1,class_weight=None)),
        ("ET_d6_l30",lambda:ExtraTreesClassifier(n_estimators=500,max_depth=6,min_samples_leaf=30,max_features="sqrt",random_state=1729,n_jobs=-1,class_weight=None)),
        ("ET_d8_l30",lambda:ExtraTreesClassifier(n_estimators=500,max_depth=8,min_samples_leaf=30,max_features="sqrt",random_state=1729,n_jobs=-1,class_weight=None)),
        ("HGB_l20",lambda:HistGradientBoostingClassifier(max_iter=250,learning_rate=0.05,max_leaf_nodes=15,min_samples_leaf=20,l2_regularization=1.0,random_state=1729)),
        ("HGB_l50",lambda:HistGradientBoostingClassifier(max_iter=250,learning_rate=0.05,max_leaf_nodes=15,min_samples_leaf=50,l2_regularization=1.0,random_state=1729)),
    ]


def oof_predictions(X:np.ndarray,y:np.ndarray,groups:list[str],factory:Any)->tuple[np.ndarray,list[dict[str,int]]]:
    folds=np.asarray(balanced_group_folds(groups),int); pred=np.zeros(len(y),float); diag=[]
    w=sample_weights(y,groups)
    for f in range(5):
        tr=np.where(folds!=f)[0]; te=np.where(folds==f)[0]
        require(set(np.asarray(groups,dtype=object)[tr]).isdisjoint(set(np.asarray(groups,dtype=object)[te])),"group leakage")
        model=factory(); model.fit(X[tr],y[tr],sample_weight=w[tr]); pred[te]=model.predict_proba(X[te])[:,1]
        diag.append({"fold":f,"train":len(tr),"test":len(te),"test_positive":int(y[te].sum())})
    return pred,diag


def filter_membership(cores:list[dict[str,Any]],expanded:list[dict[str,Any]],eids:list[str],scores:np.ndarray,threshold:float,cap_ratio:float)->tuple[list[dict[str,Any]],int]:
    score_by={eid:float(s) for eid,s in zip(eids,scores)}
    out=[]; kept_total=0
    for core,exp in zip(cores,expanded):
        fid=str(core["family_id"]); added=[str(x) for x in exp.get("p2_added_event_ids",[])]
        eligible=[eid for eid in added if score_by[eid]>=threshold]
        eligible.sort(key=lambda eid:(-score_by[eid],eid))
        if math.isfinite(cap_ratio):eligible=eligible[:max(0,int(math.floor(cap_ratio*len(core["event_ids"]))))]
        keep=set(eligible); kept_total+=len(keep)
        f=copy.deepcopy(exp)
        f["event_ids"]=[str(x) for x in exp["event_ids"] if str(x) not in set(added) or str(x) in keep]
        f["event_count"]=len(f["event_ids"]); f["p2_added_event_ids"]=sorted(keep); f["p2_added_event_count"]=len(keep)
        out.append(f)
    return out,kept_total


def main()->int:
    args=parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    expanded=load_gz(args.p12_dir/"p12_expanded_families.json.gz"); decisions=load_gz(args.p12_dir/"p12_decisions_pretruth.json.gz")
    require(len(expanded)==EXPECTED_FAMILIES,"P12 family count changed")
    assignments=decisions["assignments"]; cores=[core_from_expanded(f) for f in expanded]

    runtime=mult.load_frozen_runtime(); support=runtime.load_support_module(args.support_source_parts)
    support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS="orbittrace-event-membership-calibration-lab-v1"; support.RANKING_VARIANTS=("persistence",)
    mult.YEARS=YEARS; mult.MONTH_KEYS=MONTH_KEYS; mult.TOP_K=100
    require(float(support.BLIND_LOW)==BLIND[0] and float(support.BLIND_HIGH)==BLIND[1],"firewall changed")
    setattr(args,"fixed4_baseline_json",args.v8_result_json)
    _candidate,base,_scorer=support.load_sources(args)
    scan_by_year,_calibration,hidden,sources=support.parse_catalogue(base)
    require([r["key"] for r in sources]==list(MONTH_KEYS),"month universe changed")

    hard_scored,_summary=mult.score_families(cores,scan_by_year,runtime,base); order=[str(x) for x in mult.rank_scored(hard_scored,"multiplicity")]
    hist_core=mult.evaluate_order(hidden,cores,order); hist_p12=mult.evaluate_order(hidden,expanded,order)
    require(abs(float(hist_core["macro_f1"])-EXPECTED_V8_MACRO)<1e-12,"v8 reproduction failed")
    require(abs(float(hist_p12["macro_f1"])-EXPECTED_P12_MACRO)<1e-12,"P12 reproduction failed")
    base_metrics=catalogue_metrics(hidden,cores,order); p12_metrics=catalogue_metrics(hidden,expanded,order)
    base_annual=annual_metrics(hidden,cores); p12_annual=annual_metrics(hidden,expanded)

    X,y,groups,eids,meta=make_rows(hidden,cores,expanded,assignments)
    require(len(X)==len(assignments)==17238,"assignment universe changed")
    positive_rate=float(y.mean())

    # Truth-aware event-level ceiling: keep only additions matching the qualified core's dominant shower identity.
    oracle_scores=y.astype(float); oracle_families,oracle_kept=filter_membership(cores,expanded,eids,oracle_scores,0.5,float("inf"))
    oracle_hist=mult.evaluate_order(hidden,oracle_families,order); oracle_metrics=catalogue_metrics(hidden,oracle_families,order); oracle_annual=annual_metrics(hidden,oracle_families)

    thresholds=[0.20,0.30,0.40,0.50,0.60,0.70,0.80,0.90]
    caps=[0.5,1.0,2.0,4.0,float("inf")]
    grid=[]; model_diag={}; best=None
    for model_name,factory in model_factories():
        pred,folds=oof_predictions(X,y,groups,factory)
        auc=float(roc_auc_score(y,pred)); ap=float(average_precision_score(y,pred)); model_diag[model_name]={"roc_auc":auc,"average_precision":ap,"folds":folds}
        for t in thresholds:
            for cap in caps:
                fams,kept=filter_membership(cores,expanded,eids,pred,t,cap)
                hist=mult.evaluate_order(hidden,fams,order); met=catalogue_metrics(hidden,fams,order); ann=annual_metrics(hidden,fams)
                gains={str(yr):ann[str(yr)]["all"]["mean_f1"]-base_annual[str(yr)]["all"]["mean_f1"] for yr in YEARS}
                feasible=(met["qualified_matches"]>=95 and met["recovered_at_100"]>=59 and met["top100_dominant_precision"]>=0.668 and float(hist["macro_f1"])>=0.30 and all(gains[str(yr)]>=0.015 for yr in YEARS))
                row={"model":model_name,"threshold":t,"cap_ratio":"Infinity" if not math.isfinite(cap) else cap,"kept_additions":kept,"historical_macro_f1":float(hist["macro_f1"]),"historical_qualified":int(hist["qualified_matches"]),"qualified_matches":int(met["qualified_matches"]),"recovered_at_100":int(met["recovered_at_100"]),"top100_dominant_precision":float(met["top100_dominant_precision"]),"all_eligible_macro_f1":float(met["best_membership_macro_f1_all_eligible"]),"annual_all_f1_gain":gains,"feasible":bool(feasible)}
                grid.append(row)
                key=(int(feasible),float(hist["macro_f1"]),min(gains.values()),met["top100_dominant_precision"],-kept)
                if best is None or key>best[0]:best=(key,row,fams)
    assert best is not None
    selected=best[1]; selected_families=best[2]
    selected_hist=mult.evaluate_order(hidden,selected_families,order); selected_metrics=catalogue_metrics(hidden,selected_families,order); selected_annual=annual_metrics(hidden,selected_families)
    passing=sum(bool(r["feasible"]) for r in grid)
    verdict="PASS_EVENT_LEVEL_P12_MEMBERSHIP_CALIBRATION_FEASIBILITY" if selected["feasible"] and passing>=3 else "FAIL_EVENT_LEVEL_P12_MEMBERSHIP_CALIBRATION_FEASIBILITY"

    result={
        "verdict":verdict,"scope":"target-excluded GMN 2022/2023 event-level membership development",
        "configuration":{"years":list(YEARS),"blind_exclusion":list(BLIND),"strict_grouping":"all additions attached to cores with same dominant known shower held in one fold; ambiguous cores grouped by family","features":"P12 responsibility/margin, normalized drift/orbit/density geometry, direction, and frozen family structural quantities; no target identity feature","core_never_removed":True,"sonotaco_2013_2014_access":False,"maarsy_access":False,"target_information_access":False},
        "event_training":{"rows":len(y),"positive_rows":int(y.sum()),"positive_rate":positive_rate,"groups":len(set(groups)),"models":model_diag},
        "baseline":{"historical":{k:v for k,v in hist_core.items() if k!="per_label"},"corrected":{k:v for k,v in base_metrics.items() if k!="per_label"},"annual":base_annual},
        "p12_full":{"historical":{k:v for k,v in hist_p12.items() if k!="per_label"},"corrected":{k:v for k,v in p12_metrics.items() if k!="per_label"},"annual":p12_annual},
        "oracle_event_ceiling":{"kept_additions":oracle_kept,"historical":{k:v for k,v in oracle_hist.items() if k!="per_label"},"corrected":{k:v for k,v in oracle_metrics.items() if k!="per_label"},"annual":oracle_annual},
        "selected":{"policy":selected,"historical":{k:v for k,v in selected_hist.items() if k!="per_label"},"corrected":{k:v for k,v in selected_metrics.items() if k!="per_label"},"annual":selected_annual},
        "robustness":{"passing_grid_variants":passing,"tested_grid_variants":len(grid)},
        "grid":sorted(grid,key=lambda r:(not r["feasible"],-r["historical_macro_f1"],-r["qualified_matches"]))[:80],
        "claim_boundary":"Development feasibility only. Any PASS requires fixed-setting repeated group-fold stress and external-interface audit before inclusion in a final candidate.",
    }
    (args.output/"event_membership_calibration_lab_v1.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    (args.output/"EVENT_MEMBERSHIP_CALIBRATION_LAB_V1.md").write_text(
        "# Event-level P12 membership calibration lab v1\n\n"
        f"- verdict: `{verdict}`\n"
        f"- P12 added-event true-positive rate against qualified core identity: `{positive_rate:.4f}`\n"
        f"- v8 historical macro/qualified: `{hist_core['macro_f1']:.6f}` / `{hist_core['qualified_matches']}`\n"
        f"- full P12 historical macro/qualified: `{hist_p12['macro_f1']:.6f}` / `{hist_p12['qualified_matches']}`\n"
        f"- event oracle historical macro/qualified: `{oracle_hist['macro_f1']:.6f}` / `{oracle_hist['qualified_matches']}`\n"
        f"- selected OOF macro/qualified/r100: `{selected_hist['macro_f1']:.6f}` / `{selected_metrics['qualified_matches']}` / `{selected_metrics['recovered_at_100']}`\n"
        f"- selected model/threshold/cap: `{selected['model']}` / `{selected['threshold']}` / `{selected['cap_ratio']}`\n"
        f"- kept additions: `{selected['kept_additions']}` / `17238`\n"
        f"- passing grid variants: `{passing}/{len(grid)}`\n"
    )
    print(verdict)
    return 0

if __name__=="__main__": raise SystemExit(main())
