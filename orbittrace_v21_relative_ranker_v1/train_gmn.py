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
from scipy.stats import rankdata

from orbittrace_unified_recurrent_catalogue_lab_v1 import run_lab as v1
from orbittrace_urc_unseen_ranker_v1 import application as portable

YEARS=(2022,2023)
MONTH_KEYS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13))
BLIND=(20.0,55.0)
EXPECTED=(226,1075,3203,4504)
P19_RESULT_SHA='6f1ad0626b8a8bda03f18e7f3435f0651af8bebf65cfd1d970a6b61a8ba52319'
P19_PRELABEL_SHA='276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8'
P20_RESULT_SHA='9ec53f29281b11002a9e22b1086d12e054392e466ea74fe82ead0187289ba303'
P20_PRELABEL_SHA='8ca358ae0f3ac96b188de9eac7bcfd6f870470873a2b7ee73b7ae76497c12734'
RANKER_SOURCE_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
CATEGORICAL_COLUMNS={0,21,22,23}


def require(ok: bool,msg: str)->None:
    if not ok: raise RuntimeError(msg)

def sha(path: Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_module(path: Path,name: str)->Any:
    spec=importlib.util.spec_from_file_location(name,path)
    require(spec is not None and spec.loader is not None,f'cannot import {path}')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def relative_transform(x: np.ndarray)->np.ndarray:
    x=np.asarray(x,dtype=np.float64)
    require(x.ndim==2 and x.shape[1]==34 and len(x)>=2 and np.all(np.isfinite(x)),'invalid raw feature matrix')
    out=np.empty_like(x)
    den=float(len(x)-1)
    for j in range(x.shape[1]):
        if j in CATEGORICAL_COLUMNS:
            out[:,j]=x[:,j]
        else:
            out[:,j]=(rankdata(x[:,j],method='average')-1.0)/den
    require(np.all(np.isfinite(out)),'relative transform nonfinite')
    return out


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--support-source-parts',type=Path,required=True); p.add_argument('--candidate-payload',type=Path,required=True)
    p.add_argument('--baseline-payload',type=Path,required=True); p.add_argument('--scorer-parts',type=Path,required=True)
    p.add_argument('--v8-result-json',type=Path,required=True)
    p.add_argument('--p19-result-json',type=Path,required=True); p.add_argument('--p19-prelabel-json',type=Path,required=True)
    p.add_argument('--p20-result-json',type=Path,required=True); p.add_argument('--p20-prelabel-json',type=Path,required=True)
    p.add_argument('--ranker-source',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)

    require(sha(a.ranker_source)==RANKER_SOURCE_SHA,'#839 ranker source changed')
    require(sha(a.p19_result_json)==P19_RESULT_SHA and sha(a.p19_prelabel_json)==P19_PRELABEL_SHA,'P19 development artifacts changed')
    require(sha(a.p20_result_json)==P20_RESULT_SHA and sha(a.p20_prelabel_json)==P20_PRELABEL_SHA,'P20 development artifacts changed')
    r19=json.loads(a.p19_result_json.read_text()); r20=json.loads(a.p20_result_json.read_text())
    require(r19['verdict'].startswith('FAIL_P19_') and r20['verdict']=='FAIL_P20_RECURRENT_ISOLATED_QUARTET_DEVELOPMENT','proposal ancestry changed')
    j19=json.loads(a.p19_prelabel_json.read_text()); j20=json.loads(a.p20_prelabel_json.read_text())
    hard=j19['hard_families']; s19=j19['soft_families']; s20=j20['soft_families']; hard_order=[str(x) for x in j19['hard_order']]
    require(j19['hard_families']==j20['hard_families'] and j19['hard_order']==j20['hard_order'],'P19/P20 hard ancestry differs')
    fams=hard+s19+s20
    require((len(hard),len(s19),len(s20),len(fams))==EXPECTED,'GMN training universe changed')
    ids=[str(f['family_id']) for f in fams]; require(len(ids)==len(set(ids)),'GMN family IDs collide')
    source_by_id={str(f['family_id']):'hard' for f in hard}
    source_by_id.update({str(f['family_id']):'p19' for f in s19}); source_by_id.update({str(f['family_id']):'p20' for f in s20})

    ranker=load_module(a.ranker_source,'frozen_839_for_v21')
    v1.mult.YEARS=YEARS; v1.mult.MONTH_KEYS=MONTH_KEYS; v1.mult.TOP_K=100
    runtime=v1.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts)
    support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS='orbittrace-v21-relative-ranker-gmn'; support.RANKING_VARIANTS=('persistence',)
    require((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'target exclusion changed')
    setattr(a,'fixed4_baseline_json',a.v8_result_json)
    _candidate,base,_scorer=support.load_sources(a)
    scan,_cal,labels,sources=support.parse_catalogue(base)
    require(sorted(scan)==list(YEARS) and [x['key'] for x in sources]==list(MONTH_KEYS),'GMN development panel changed')

    eligible=v1.eligible_labels(labels); by={str(f['family_id']):f for f in fams}
    truths={fid:v1.family_truth(by[fid],labels,eligible) for fid in ids}
    x_raw,cm,tie=portable.build_feature_matrix(
        families=fams,source_by_id=source_by_id,hard_order=hard_order,scan_by_year=scan,years=YEARS,
        support=support,base=base,frozen_ranker_module=ranker,
    )
    x=relative_transform(x_raw)
    target=np.asarray([float(truths[fid]['f1']) if truths[fid]['positive'] else 0.0 for fid in ids],dtype=np.float64)
    groups=[('SHOWER/'+str(truths[fid]['best_label'])) if truths[fid]['best_label'] is not None else ('NEG/'+fid) for fid in ids]
    folds=np.asarray([v1.deterministic_fold(g) for g in groups],dtype=int)
    weights=ranker.grouped_weights(groups)
    oof=np.zeros(len(ids),dtype=np.float64); fold_rows=[]
    for fold in range(5):
        tr=folds!=fold; te=folds==fold
        require(tr.any() and te.any(),f'empty strict group fold {fold}')
        model=ranker.model(); model.fit(x[tr],target[tr],sample_weight=weights[tr]); oof[te]=model.predict(x[te])
        fold_rows.append({'fold':fold,'train':int(tr.sum()),'test':int(te.sum())})
    order_idx=ranker.diversity_order(oof,cm,0.8,1.0,tie); order=[ids[i] for i in order_idx]
    metrics=v1.monotone_metrics(fams,order,truths,eligible)
    passes=(
        int(metrics['recovered_at_100'])>=70 and int(metrics['recovered_at_50'])>=38 and
        float(metrics['top100_dominant_precision'])>=0.70 and int(metrics['qualified_matches'])>=230
    )
    manifest={
        'verdict':'PASS_V21_GMN_RELATIVE_RANKER_GUARD' if passes else 'FAIL_V21_GMN_RELATIVE_RANKER_GUARD',
        'scope':'target-excluded GMN 2022/2023 only','feature_count':34,'categorical_columns':sorted(CATEGORICAL_COLUMNS),
        'relative_transform':'average-tie empirical percentile (rank-1)/(N-1)','model':'exact #839 ExtraTreesRegressor complexity',
        'diversity_lambda':0.8,'diversity_scale':1.0,'oof_metrics':{k:v for k,v in metrics.items() if k!='first_rank_by_label'},
        'folds':fold_rows,'sonotaco_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,
    }
    (a.output/'V21_GMN_RELATIVE_RANKER_GUARD.json').write_text(json.dumps(manifest,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps(manifest,indent=2,sort_keys=True,allow_nan=False))
    require(passes,'v21 relative-ranker GMN guard failed; SonotaCo application forbidden')

    full=ranker.model(); full.fit(x,target,sample_weight=weights); full.set_params(n_jobs=1)
    model_path=a.output/'relative_ranker.joblib'; joblib.dump(full,model_path)
    model_sha=sha(model_path)
    freeze={
        'verdict':'PASS_V21_FULL_GMN_MODEL_FREEZE','model_sha256':model_sha,'training_family_count':len(ids),
        'training_target_sha256':hashlib.sha256(np.ascontiguousarray(target).tobytes()).hexdigest(),
        'relative_feature_sha256':hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest(),
        'sonotaco_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,
    }
    (a.output/'V21_FULL_GMN_MODEL_FREEZE.json').write_text(json.dumps(freeze,indent=2,sort_keys=True)+'\n')
    print(json.dumps(freeze,indent=2,sort_keys=True)); return 0

if __name__=='__main__': raise SystemExit(main())
