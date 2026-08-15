#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np

import recurrent_eom as parent_reom
from density_synchronous_eom import density_synchronous_stability
from sporadic_analogue_eom import _descendant_weight_sums

YEARS=(2022,2023)
MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13))
BLIND=(20.0,55.0)
EXPECTED_WEIGHTS_SHA256='648b88efc09192738dcce8eb2af15e215676dd62451a88cd9230337d80fd5347'
EXPECTED_CHAMPION_COUNT=2094


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec=importlib.util.spec_from_file_location(name,path)
    req(spec is not None and spec.loader is not None, f'cannot import {path}')
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--parent-runner',type=Path,required=True)
    ap.add_argument('--quality-source',type=Path,required=True)
    ap.add_argument('--support-source-parts',type=Path,required=True)
    ap.add_argument('--candidate-payload',type=Path,required=True)
    ap.add_argument('--baseline-payload',type=Path,required=True)
    ap.add_argument('--scorer-parts',type=Path,required=True)
    ap.add_argument('--v8-result-json',type=Path,required=True)
    ap.add_argument('--weights-npy',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)

    req(sha(a.weights_npy)==EXPECTED_WEIGHTS_SHA256,'frozen failed-endpoint weight array changed')
    weights=np.load(a.weights_npy,allow_pickle=False)
    req(weights.shape==(738682,) and weights.dtype==np.float64,'weight array shape/dtype changed')
    req(np.all(np.isfinite(weights)) and np.all(weights>0.0),'invalid frozen weights')

    pr=load_module(a.parent_runner,'accounting_parent_runner')
    req(tuple(pr.YEARS)==YEARS and tuple(pr.BLIND)==BLIND,'parent constants changed')
    req(sha(a.quality_source)==pr.QUALITY_SHA,'GMN runtime utility changed')
    req(sha(a.v8_result_json)==pr.V8_RESULT_SHA,'runtime support artifact changed')
    qmod=pr.load_module(a.quality_source,'accounting_gmn_utility')
    qmod.v1.mult.YEARS=YEARS; qmod.v1.mult.MONTH_KEYS=MONTH_KEYS; qmod.v1.mult.TOP_K=100
    runtime=qmod.v1.mult.load_frozen_runtime()
    support=runtime.load_support_module(a.support_source_parts)
    support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS
    support.CORPUS='orbittrace-sporadic-analogue-accounting-audit-target-excluded'
    support.RANKING_VARIANTS=('persistence',)
    req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'firewall changed')
    setattr(a,'fixed4_baseline_json',a.v8_result_json)
    _candidate,base,_scorer=support.load_sources(a)
    scan,_cal,_hidden_sealed,sources=support.parse_catalogue(base)
    req(sorted(scan)==list(YEARS),'wrong years')
    req([x['key'] for x in sources]==list(MONTH_KEYS),'source list changed')

    events=[]
    for year in YEARS:
        raw=list(scan[year]); rows=[pr.normalize_event(row,year) for row in raw]
        req(len(rows)==len(raw),f'event count changed {year}')
        events.extend(rows)
    req(len(events)==738682,'pooled event count changed')
    X=pr.geo_matrix(events)
    years=np.asarray([e['year'] for e in events],dtype=np.int64)

    model=hdbscan.HDBSCAN(min_cluster_size=10,min_samples=10,metric='euclidean',cluster_selection_method='eom',cluster_selection_epsilon=0.0,allow_single_cluster=False,prediction_data=False).fit(X)
    tree=model.condensed_tree_._raw_tree
    champion_score,_annual,_recon=density_synchronous_stability(tree,years)
    champion_labels=parent_reom.eom_labels(tree,champion_score)
    champion_nodes=parent_reom.selected_eom_nodes(tree,champion_score)
    req(len(champion_nodes)==len(set(int(x) for x in champion_labels if int(x)>=0)),'champion label/node mismatch')
    req(len(champion_nodes)==EXPECTED_CHAMPION_COUNT,f'champion identity mismatch {len(champion_nodes)}')

    root=int(tree['parent'].min())
    desc=_descendant_weight_sums(tree,years,weights)
    yvals=(2022,2023); y_index={y:i for i,y in enumerate(yvals)}
    rows_by_parent=defaultdict(list)
    for p_raw,c_raw,lam_raw,_size_raw in tree:
        rows_by_parent[int(p_raw)].append((float(lam_raw),int(c_raw)))

    worst=[]
    total_negative_steps=0
    for p,rows in rows_by_parent.items():
        alive=np.asarray(desc[p],dtype=np.float64).copy()
        initial=alive.copy()
        min_alive=alive.copy()
        sorted_rows=sorted(rows,key=lambda x:(x[0],x[1]))
        i=0
        while i<len(sorted_rows):
            lam=sorted_rows[i][0]
            departure=np.zeros(2,dtype=np.float64)
            j=i
            while j<len(sorted_rows) and sorted_rows[j][0]==lam:
                child=sorted_rows[j][1]
                if child<root:
                    departure[y_index[int(years[child])]]+=float(weights[child])
                else:
                    departure+=desc[child]
                j+=1
            alive-=departure
            min_alive=np.minimum(min_alive,alive)
            if np.any(alive<0.0): total_negative_steps+=1
            i=j

        # Independent high-accuracy final accounting by year.
        dep_terms=[[],[]]
        for _lam,child in sorted_rows:
            if child<root:
                dep_terms[y_index[int(years[child])]].append(float(weights[child]))
            else:
                dep_terms[0].append(float(desc[child][0])); dep_terms[1].append(float(desc[child][1]))
        fsum_residual=np.asarray([float(initial[k])-math.fsum(dep_terms[k]) for k in (0,1)],dtype=float)
        scale=float(max(1.0,np.max(np.abs(initial))))
        worst.append({
            'node':int(p),
            'initial':initial.tolist(),
            'sequential_final':alive.tolist(),
            'sequential_min':min_alive.tolist(),
            'fsum_final':fsum_residual.tolist(),
            'max_abs_sequential_residual':float(np.max(np.abs(alive))),
            'max_abs_fsum_residual':float(np.max(np.abs(fsum_residual))),
            'relative_sequential_residual':float(np.max(np.abs(alive))/scale),
            'relative_fsum_residual':float(np.max(np.abs(fsum_residual))/scale),
        })

    worst_by_seq=sorted(worst,key=lambda r:r['max_abs_sequential_residual'],reverse=True)[:20]
    root_row=next(r for r in worst if r['node']==root)
    max_rel=max(r['relative_sequential_residual'] for r in worst)
    max_abs=max(r['max_abs_sequential_residual'] for r in worst)
    # Diagnostic classification only. No scientific scoring/pretruth/truth.
    numerical_only=bool(max_rel <= 1e-12 and max_abs <= 1e-6)
    result={
        'verdict':'PASS_WEIGHTED_ACCOUNTING_NUMERICAL_RESIDUAL_ONLY' if numerical_only else 'FAIL_WEIGHTED_ACCOUNTING_STRUCTURAL_MISMATCH',
        'scientific_role':'PRETRUTH_ENGINEERING_DIAGNOSTIC_ONLY',
        'champion_candidate_count':len(champion_nodes),
        'root_node':root,
        'root_accounting':root_row,
        'max_abs_sequential_residual':max_abs,
        'max_relative_sequential_residual':max_rel,
        'negative_step_count':total_negative_steps,
        'worst_20':worst_by_seq,
        'weights_sha256':sha(a.weights_npy),
        'weights_mean':float(np.mean(weights)),
        'weights_min':float(np.min(weights)),
        'weights_max':float(np.max(weights)),
        'successor_score_computed':False,
        'successor_pretruth_created':False,
        'scientific_result_created':False,
        'hidden_truth_accessed':False,
        'target_information_access':False,
        'target_region_events_accessed':False,
        'sonotaco_2013_2014_access':False,
        'asfn_access':False,
        'efn_access':False,
        'amos_access':False,
        'maarsy_scientific_access':False,
        'dms_scientific_access':False,
    }
    (a.output/'WEIGHTED_ACCOUNTING_DIAGNOSTIC.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
