#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import ExtraTreesClassifier

from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as two

ROUTES=('sugar','hdbscan')
YEARS=(2013,2014)
PANELS=(('sugar',2013),('sugar',2014),('hdbscan',2013),('hdbscan',2014))
FEATURE_DIM=71
RANKER_SOURCE_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
TWO_SOURCE_GIT_BLOB='cb981af547f74664a0956a72547a4ee6037cd438'
REP_SOURCE_GIT_BLOB='263b4200ce7ed4e04813bedd58db229fdba69c96'
VARIANT='v24_twohead_repclassifier_v19_equal_rank_sum'

TWO_EXPECT={
 ('sugar',2013):(0.27806630131631344,16),
 ('sugar',2014):(0.32869544907104964,17),
 ('hdbscan',2013):(0.14257102406283795,10),
 ('hdbscan',2014):(0.12833942693327394,7),
}
REP_EXPECT={
 ('sugar',2013):(0.27806630131631344,16),
 ('sugar',2014):(0.31911211573771636,17),
 ('hdbscan',2013):(0.13911011444031582,9),
 ('hdbscan',2014):(0.13072925356649356,7),
}


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def git_blob_sha(path:Path)->str:
    data=path.read_bytes()
    header=f'blob {len(data)}\0'.encode()
    return hashlib.sha1(header+data).hexdigest()


def classifier()->ExtraTreesClassifier:
    return ExtraTreesClassifier(
        n_estimators=600,max_depth=4,min_samples_leaf=5,max_features=None,
        random_state=20260809,n_jobs=1,class_weight='balanced',
    )


def rep_eligible_truth(by_year:dict[int,dict[str,str]])->dict[str,Counter[int]]:
    d:dict[str,Counter[int]]=defaultdict(Counter)
    for year in YEARS:
        for label in by_year[year].values():
            if label!='SPORADIC': d[str(label)][year]+=1
    return {label:c for label,c in d.items() if sum(c.values())>=8 and all(c.get(y,0)>=4 for y in YEARS)}


def rep_family_truth(family:dict[str,Any],hidden:dict[str,str],eligible:dict[str,Counter[int]])->dict[str,Any]:
    ids=list(map(str,family['event_ids']))
    counts=Counter(hidden.get(eid,'SPORADIC') for eid in ids)
    rows=[]
    for label,year_counts in eligible.items():
        overlap=int(counts.get(label,0))
        if overlap<=0: continue
        total=int(sum(year_counts.values())); precision=overlap/max(len(ids),1); recall=overlap/total
        f1=2.0*precision*recall/(precision+recall) if precision+recall else 0.0
        rows.append((f1,precision,overlap,str(label),recall))
    if not rows:
        return {'positive':False,'best_label':None,'overlap':0,'precision':0.0,'recall':0.0,'f1':0.0}
    f1,precision,overlap,label,recall=max(rows,key=lambda z:(z[0],z[1],z[2],z[3]))
    return {'positive':bool(precision>=0.5 and overlap>=4),'best_label':label,'overlap':overlap,'precision':float(precision),'recall':float(recall),'f1':float(f1)}


def representative_labels(ids:list[str],truths:list[dict[str,Any]])->np.ndarray:
    by:dict[str,list[int]]=defaultdict(list)
    for i,t in enumerate(truths):
        if t['positive'] and t['best_label'] is not None: by[str(t['best_label'])].append(i)
    y=np.zeros(len(ids),dtype=np.int8)
    for label,inds in sorted(by.items()):
        best=sorted(inds,key=lambda i:(-float(truths[i]['f1']),-float(truths[i]['precision']),-int(truths[i]['overlap']),ids[i]))[0]
        y[best]=1
    return y


def positive_probability(model:ExtraTreesClassifier,X:np.ndarray)->np.ndarray:
    require(set(map(int,model.classes_.tolist()))=={0,1},f'classifier classes changed: {model.classes_}')
    j=int(np.where(model.classes_==1)[0][0])
    p=np.asarray(model.predict_proba(X)[:,j],dtype=np.float64)
    require(p.shape==(len(X),) and np.all(np.isfinite(p)) and np.all((p>=0)&(p<=1)),'invalid representative probabilities')
    return p


def equal_three_way_rank_sum(ids:list[str],a:list[str],b:list[str],c:list[str],tie_rank:list[int])->list[str]:
    require(set(a)==set(b)==set(c)==set(ids) and len(a)==len(b)==len(c)==len(ids),'fusion universe mismatch')
    ra={fid:i+1 for i,fid in enumerate(a)}; rb={fid:i+1 for i,fid in enumerate(b)}; rc={fid:i+1 for i,fid in enumerate(c)}
    tie={fid:int(tie_rank[i]) for i,fid in enumerate(ids)}
    return sorted(ids,key=lambda fid:(ra[fid]+rb[fid]+rc[fid],tie[fid],fid))


def panel_eval(families:list[dict[str,Any]],truth:dict[str,str],budget:int)->dict[str,Any]:
    return two.v22.evaluate(families,truth,budget)


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--payload-root',type=Path,required=True)
    p.add_argument('--truth-root',type=Path,required=True)
    p.add_argument('--ranker-source',type=Path,required=True)
    p.add_argument('--rep-source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)

    require(two.v22.sha(a.ranker_source)==RANKER_SOURCE_SHA,'#839 ranker source changed')
    require(git_blob_sha(Path(two.__file__))==TWO_SOURCE_GIT_BLOB,'exact PR #950 source changed')
    require(git_blob_sha(a.rep_source)==REP_SOURCE_GIT_BLOB,'exact PR #951 source changed')

    truth_year={}; frozen={}
    for route,year in PANELS:
        truth_year[(route,year)]=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text())
        frozen[(route,year)]=json.loads((a.truth_root/f'evaluation_{route}_{year}.json').read_text())

    ranker=two.v22.load_module(a.ranker_source,'frozen_839_v24_complementary_fusion')
    data={}; Xs=[]; y13s=[]; y14s=[]; yreps=[]; groups=[]; offsets={}; cursor=0

    for route in ROUTES:
        root=a.payload_root/route
        meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        fp=json.loads((root/'family_memberships.json').read_text())
        require(meta['feature_dimension']==FEATURE_DIM and meta['truth_accessed'] is False and fp['truth_accessed'] is False,f'{route} invalid immutable pretruth payload')
        ids=list(map(str,meta['family_ids'])); fams=fp['families']
        require([str(f['family_id']) for f in fams]==ids,f'{route} family alignment changed')
        X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False)
        require(X.shape==(len(ids),FEATURE_DIM) and C.shape==(len(ids),8),f'{route} pretruth array shape changed')
        require(two.v22.array_sha(X)==meta['feature_sha256'] and two.v22.array_sha(C)==meta['centroid_sha256'],f'{route} immutable pretruth hash mismatch')

        by_year={y:truth_year[(route,y)] for y in YEARS}; hidden={**by_year[2013],**by_year[2014]}
        eligible_two=two.v22.eligible_from_year_truth(by_year)
        truths_two=[two.v22.family_truth(f,hidden,eligible_two) for f in fams]
        yy13=[]; yy14=[]; gs=[]
        for i,(family,t) in enumerate(zip(fams,truths_two)):
            label=t['best_label']; gs.append(('SHOWER/'+str(label)) if label is not None else ('NEG/'+route+'/'+ids[i]))
            if not t['positive'] or label is None: yy13.append(0.0); yy14.append(0.0)
            else:
                q13,q14=two.annual_f1_for_fixed_label(family,str(label),by_year); yy13.append(q13); yy14.append(q14)

        eligible_rep=rep_eligible_truth(by_year)
        truths_rep=[rep_family_truth(f,hidden,eligible_rep) for f in fams]
        rep_groups=[('SHOWER/'+str(t['best_label'])) if t['best_label'] is not None else ('NEG/'+route+'/'+ids[i]) for i,t in enumerate(truths_rep)]
        require(rep_groups==gs,f'{route} #950/#951 strict group assignments differ')
        yrep=representative_labels(ids,truths_rep)

        arr13=np.asarray(yy13,dtype=np.float64); arr14=np.asarray(yy14,dtype=np.float64)
        require(int(yrep.sum())==({'sugar':29,'hdbscan':27}[route]),f'{route} representative target count does not reproduce #951')
        offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids)
        Xs.append(X); y13s.append(arr13); y14s.append(arr14); yreps.append(yrep); groups.extend(gs)
        data[route]={'ids':ids,'fams':fams,'C':C,'tie':list(map(int,meta['tie_rank'])),'v19':list(map(str,meta['v19_order']))}

    Xall=np.vstack(Xs); y13=np.concatenate(y13s); y14=np.concatenate(y14s); yrep=np.concatenate(yreps); groups=list(map(str,groups))
    require(Xall.shape==(cursor,FEATURE_DIM) and len(y13)==len(y14)==len(yrep)==len(groups)==cursor,'stacked training shape mismatch')
    folds=np.asarray([two.v22.v1.deterministic_fold(g) for g in groups],dtype=int)
    weights=np.asarray(ranker.grouped_weights(groups),dtype=np.float64)
    oof13=np.zeros(cursor); oof14=np.zeros(cursor); oofrep=np.zeros(cursor)
    fold_diag=[]
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; require(tr.any() and te.any(),f'empty fold {fold}')
        tg={groups[i] for i in np.where(tr)[0]}; eg={groups[i] for i in np.where(te)[0]}; require(tg.isdisjoint(eg),f'group leakage fold {fold}')
        m13=ranker.model(); m14=ranker.model(); mc=classifier()
        m13.fit(Xall[tr],y13[tr],sample_weight=weights[tr]); m14.fit(Xall[tr],y14[tr],sample_weight=weights[tr])
        require(set(np.unique(yrep[tr]).tolist())=={0,1},f'representative training fold {fold} lacks class')
        mc.fit(Xall[tr],yrep[tr],sample_weight=weights[tr])
        oof13[te]=m13.predict(Xall[te]); oof14[te]=m14.predict(Xall[te]); oofrep[te]=positive_probability(mc,Xall[te])
        fold_diag.append({'fold':fold,'train_examples':int(tr.sum()),'test_examples':int(te.sum()),'train_groups':len(tg),'test_groups':len(eg),'test_representatives':int(yrep[te].sum())})

    two_score=np.minimum(oof13,oof14); require(np.all(np.isfinite(two_score)) and np.all(np.isfinite(oofrep)),'nonfinite OOF signal')
    routes_out={}; historical_controls=[]
    for route in ROUTES:
        lo,hi=offsets[route]; rd=data[route]; ids=rd['ids']; tie=[(rd['tie'][i],ids[i]) for i in range(len(ids))]
        oi=ranker.diversity_order(two_score[lo:hi],rd['C'],0.8,1.0,tie); two_order=[ids[i] for i in oi]
        ri=ranker.diversity_order(oofrep[lo:hi],rd['C'],0.8,1.0,tie); rep_order=[ids[i] for i in ri]
        two_hist=list(two.v19.fusion_orders(two_order,rd['v19'])['rank_sum'])
        rep_hist=list(two.v19.fusion_orders(rep_order,rd['v19'])['rank_sum'])
        fused=equal_three_way_rank_sum(ids,two_order,rep_order,rd['v19'],rd['tie'])
        routes_out[route]={
            'two_control':two.v22.rerank(rd['fams'],two_hist),
            'rep_control':two.v22.rerank(rd['fams'],rep_hist),
            'fusion':two.v22.rerank(rd['fams'],fused),
            'two_order_sha256':hashlib.sha256('\n'.join(two_order).encode()).hexdigest(),
            'rep_order_sha256':hashlib.sha256('\n'.join(rep_order).encode()).hexdigest(),
            'v19_order_sha256':hashlib.sha256('\n'.join(rd['v19']).encode()).hexdigest(),
            'fusion_order_sha256':hashlib.sha256('\n'.join(fused).encode()).hexdigest(),
        }
        for year in YEARS:
            budget=int(frozen[(route,year)]['candidate_budget']['comparator_budget'])
            tc=panel_eval(routes_out[route]['two_control'],truth_year[(route,year)],budget)
            rc=panel_eval(routes_out[route]['rep_control'],truth_year[(route,year)],budget)
            te=TWO_EXPECT[(route,year)]; re=REP_EXPECT[(route,year)]
            require(abs(tc['macro_f1']-te[0])<1e-12 and tc['recovered_f1_gt_0_5']==te[1],f'#950 control mismatch {route} {year}')
            require(abs(rc['macro_f1']-re[0])<1e-12 and rc['recovered_f1_gt_0_5']==re[1],f'#951 control mismatch {route} {year}')
            historical_controls.append({'comparator':route,'year':year,'twohead_macro_f1':tc['macro_f1'],'twohead_recovered':tc['recovered_f1_gt_0_5'],'repclassifier_macro_f1':rc['macro_f1'],'repclassifier_recovered':rc['recovered_f1_gt_0_5']})

    panels=[]
    for route,year in PANELS:
        budget=int(frozen[(route,year)]['candidate_budget']['comparator_budget'])
        cur=panel_eval(routes_out[route]['fusion'],truth_year[(route,year)],budget); lit=frozen[(route,year)]['comparator_summary']
        cm=float(cur['macro_f1']); cr=int(cur['recovered_f1_gt_0_5']); lm=float(lit['macro_f1']); lr=int(lit['recovered_f1_gt_0_5'])
        panels.append({'comparator':route,'year':year,'budget':budget,'candidate_macro_f1':cm,'literature_macro_f1':lm,'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,'macro_f1_ratio':cm/lm,'recovery_ratio':cr/lr,'superiority_pair_pass':bool(cm>lm and cr>=lr)})
    wins=sum(int(x['superiority_pair_pass']) for x in panels); passed=wins==4

    freeze={'verdict':'NOT_FROZEN_V24_COMPLEMENTARY_FUSION_OOF_FAIL'}
    if passed:
        f13=ranker.model(); f14=ranker.model(); fc=classifier(); f13.fit(Xall,y13,sample_weight=weights); f14.fit(Xall,y14,sample_weight=weights); fc.fit(Xall,yrep,sample_weight=weights)
        f13.set_params(n_jobs=1); f14.set_params(n_jobs=1)
        p13=a.output/'v24_fusion_annual_2013.joblib'; p14=a.output/'v24_fusion_annual_2014.joblib'; pc=a.output/'v24_fusion_representative_classifier.joblib'
        joblib.dump(f13,p13); joblib.dump(f14,p14); joblib.dump(fc,pc)
        freeze={'verdict':'PASS_V24_COMPLEMENTARY_FUSION_FULL_EXPOSED_MODEL_FREEZE','annual_2013_sha256':two.v22.sha(p13),'annual_2014_sha256':two.v22.sha(p14),'representative_classifier_sha256':two.v22.sha(pc),'feature_dimension':FEATURE_DIM,'training_examples':cursor,'in_sample_score_used_for_promotion':False}
    (a.output/'V24_COMPLEMENTARY_FUSION_FULL_MODEL_FREEZE.json').write_text(json.dumps(freeze,indent=2,sort_keys=True)+'\n')

    result={
        'scientific_stage':'V24_TWOHEAD_REPCLASSIFIER_V19_COMPLEMENTARY_EQUAL_RANK_FUSION_V1',
        'verdict':'PASS_V24_COMPLEMENTARY_FUSION_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V24_COMPLEMENTARY_FUSION_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'promotion_variant':VARIANT,'panel_wins':wins,'all_panel_win':passed,'panels':panels,'historical_controls':historical_controls,'fold_diagnostics':fold_diag,
        'route_order_hashes':{r:{k:v for k,v in routes_out[r].items() if k.endswith('_sha256')} for r in ROUTES},
        'feature_dimension':FEATURE_DIM,'fusion_components':['#950 diversity-processed two-head annual-quality OOF order','#951 diversity-processed representative-classifier OOF order','exact frozen v19 order'],'fusion_rule':'equal sum of 1-based complete-catalogue ranks; v19 counted once','tie_rule':'exact v22 tie_rank then stable family_id','fusion_weight_search':False,'rank_product_evaluated':False,'sequential_fusion_evaluated':False,
        'candidate_membership_changed':False,'pretruth_feature_changed':False,'strict_whole_shower_oof':True,'diversity':{'lambda':0.8,'scale':1.0},'feature_search':False,'target_search':False,'model_search':False,'hyperparameter_search':False,'class_weight_search':False,'calibration_search':False,'diversity_search':False,'source_quota_selected':False,'post_result_second_search':False,
        'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0],'full_model_freeze':freeze,
    }
    (a.output/'V24_COMPLEMENTARY_FUSION_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'panel_wins':wins,'panels':panels,'full_model_freeze':freeze},indent=2,sort_keys=True,allow_nan=False))
    return 0

if __name__=='__main__': raise SystemExit(main())
