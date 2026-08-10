#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import joblib,numpy as np
from orbittrace_v23_worst_year_oof_ranker_v1 import train_evaluate as v23
ROUTES=v23.ROUTES; YEARS=v23.YEARS; PANELS=v23.PANELS; DIM=77; V19=v23.V19_METRICS
VARIANTS=('missing_b1_two_head_quality','missing_b1_two_head_v19_rank_sum'); PREF={'missing_b1_two_head_quality':2,'missing_b1_two_head_v19_rank_sum':1}
def req(x,m):
    if not x: raise RuntimeError(m)
def main():
    p=argparse.ArgumentParser(); p.add_argument('--sugar-v22',type=Path,required=True); p.add_argument('--hdb-v22',type=Path,required=True); p.add_argument('--sugar-v28',type=Path,required=True); p.add_argument('--hdb-v28',type=Path,required=True); p.add_argument('--truth-root',type=Path,required=True); p.add_argument('--ranker-source',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(v23.sha(a.ranker_source)==v23.RANKER_SOURCE_SHA,'ranker changed'); b={'sugar':a.sugar_v22,'hdbscan':a.hdb_v22}; n={'sugar':a.sugar_v28,'hdbscan':a.hdb_v28}
    truth={}; frozen={}
    for r,y in PANELS: truth[(r,y)]=json.loads((a.truth_root/f'truth_{r}_{y}.json').read_text()); frozen[(r,y)]=json.loads((a.truth_root/f'evaluation_{r}_{y}.json').read_text())
    ranker=v23.load_module(a.ranker_source,'v28_ranker'); Xs=[]; y13s=[]; y14s=[]; groups=[]; data={}; offsets={}; cur=0
    for r in ROUTES:
        bm=json.loads((b[r]/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fm=json.loads((b[r]/'family_memberships.json').read_text()); nm=json.loads((n[r]/'V28_PRETRUTH_MANIFEST.json').read_text()); ids=list(map(str,bm['family_ids'])); fams=fm['families']; X=np.load(n[r]/'features_v28.npy',allow_pickle=False); C=np.load(b[r]/'centroids.npy',allow_pickle=False)
        req(nm['stage']=='V28_MISSINGNESS_AWARE_B1_PRETRUTH_FREEZE' and nm['truth_accessed'] is False and nm['feature_dimension']==DIM,'bad v28 pretruth'); req(X.shape==(len(ids),DIM) and v23.array_sha(X)==nm['feature_sha256'],'v28 feature hash'); req([str(f['family_id']) for f in fams]==ids,'family align')
        byy={y:truth[(r,y)] for y in YEARS}; elig=v23.eligible_from_year_truth(byy); hidden={**byy[2013],**byy[2014]}; best=[v23.combined_best_label(f,hidden,elig) for f in fams]; a13=[]; a14=[]; gs=[]
        for i,(f,bb) in enumerate(zip(fams,best)):
            lab=bb['best_label']
            if lab is None: f13=f14=0.; g=f'NEG/{r}/{ids[i]}'
            else: f13=v23.year_f1_for_label(f,byy[2013],lab); f14=v23.year_f1_for_label(f,byy[2014],lab); g='SHOWER/'+str(lab)
            a13.append(f13); a14.append(f14); gs.append(g)
        offsets[r]=(cur,cur+len(ids)); cur+=len(ids); Xs.append(X); y13s.append(np.asarray(a13)); y14s.append(np.asarray(a14)); groups+=gs; data[r]={'bm':bm,'fams':fams,'ids':ids,'C':C}
    X=np.vstack(Xs); y13=np.concatenate(y13s); y14=np.concatenate(y14s); groups=list(map(str,groups)); folds=np.asarray([v23.v1.deterministic_fold(g) for g in groups]); w=ranker.grouped_weights(groups); p13=np.zeros(cur); p14=np.zeros(cur); fd=[]
    for f in range(5):
        tr=folds!=f; te=folds==f; m13=ranker.model(); m14=ranker.model(); m13.fit(X[tr],y13[tr],sample_weight=w[tr]); m14.fit(X[tr],y14[tr],sample_weight=w[tr]); p13[te]=m13.predict(X[te]); p14[te]=m14.predict(X[te]); tg={groups[i] for i in np.where(tr)[0]}; eg={groups[i] for i in np.where(te)[0]}; req(tg.isdisjoint(eg),'group leak'); fd.append({'fold':f,'train':int(tr.sum()),'test':int(te.sum()),'train_groups':len(tg),'test_groups':len(eg)})
    score=np.minimum(p13,p14); variants={}; controls=[]; od={}
    for r in ROUTES:
        lo,hi=offsets[r]; d=data[r]; ids=d['ids']; s=score[lo:hi]; tie=[(int(d['bm']['tie_rank'][i]),ids[i]) for i in range(len(ids))]; idx=ranker.diversity_order(s,d['C'],0.8,1.0,tie); qo=[ids[i] for i in idx]; vo=list(map(str,d['bm']['v19_order'])); fu=list(v23.v19.fusion_orders(qo,vo)['rank_sum']); variants[r]={VARIANTS[0]:v23.rerank(d['fams'],qo),VARIANTS[1]:v23.rerank(d['fams'],fu),'v19_control':v23.rerank(d['fams'],vo)}; od[r]={'quality_order_sha256':hashlib.sha256('\n'.join(qo).encode()).hexdigest(),'fused_order_sha256':hashlib.sha256('\n'.join(fu).encode()).hexdigest()}
        for y in YEARS:
            budget=int(frozen[(r,y)]['candidate_budget']['comparator_budget']); z=v23.evaluate(variants[r]['v19_control'],truth[(r,y)],budget); e=V19[(r,y)]; req(abs(z['macro_f1']-e[0])<1e-12 and z['recovered_f1_gt_0_5']==e[1],f'v19 mismatch {r} {y}'); controls.append({'comparator':r,'year':y,**z})
    rows=[]
    for v in VARIANTS:
        panels=[]
        for r,y in PANELS:
            budget=int(frozen[(r,y)]['candidate_budget']['comparator_budget']); z=v23.evaluate(variants[r][v],truth[(r,y)],budget); lit=frozen[(r,y)]['comparator_summary']; cm=z['macro_f1']; cr=z['recovered_f1_gt_0_5']; lm=float(lit['macro_f1']); lr=int(lit['recovered_f1_gt_0_5']); panels.append({'comparator':r,'year':y,'candidate_macro_f1':cm,'literature_macro_f1':lm,'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,'superiority_pair_pass':bool(cm>lm and cr>=lr),'macro_f1_ratio':cm/lm,'recovery_ratio':cr/lr})
        wins=sum(x['superiority_pair_pass'] for x in panels); rows.append({'variant':v,'panel_wins':wins,'all_panel_win':wins==4,'min_macro_f1_ratio':min(x['macro_f1_ratio'] for x in panels),'min_recovery_ratio':min(x['recovery_ratio'] for x in panels),'mean_macro_f1_ratio':float(np.mean([x['macro_f1_ratio'] for x in panels])),'mean_recovery_ratio':float(np.mean([x['recovery_ratio'] for x in panels])),'panels':panels})
    for q in rows:q['selection_key']=[q['panel_wins'],q['min_macro_f1_ratio'],q['min_recovery_ratio'],q['mean_macro_f1_ratio'],q['mean_recovery_ratio'],PREF[q['variant']]]
    win=max(rows,key=lambda q:tuple(q['selection_key'])); passed=win['all_panel_win']; freeze={'verdict':'NOT_FROZEN_V28_OOF_FAIL'}
    if passed:
        h13=ranker.model(); h14=ranker.model(); h13.fit(X,y13,sample_weight=w); h14.fit(X,y14,sample_weight=w); h13.set_params(n_jobs=1); h14.set_params(n_jobs=1); f13=a.output/'v28_head_2013.joblib'; f14=a.output/'v28_head_2014.joblib'; joblib.dump(h13,f13); joblib.dump(h14,f14); freeze={'verdict':'PASS_V28_FULL_MODEL_FREEZE','head_2013_sha256':v23.sha(f13),'head_2014_sha256':v23.sha(f14),'feature_dimension':DIM}
    res={'stage':'V28_EXPOSED_MISSINGNESS_AWARE_B1_TWO_HEAD_OOF','verdict':'PASS_V28_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V28_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT','winner':win,'all_results':rows,'v19_control':controls,'v19_control_reproduction_pass':True,'folds':fd,'order_diagnostics':od,'full_model_freeze':freeze,'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'post_result_second_search':False}
    (a.output/'V28_RESULT.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n'); (a.output/'V28_FULL_MODEL_FREEZE.json').write_text(json.dumps(freeze,indent=2,sort_keys=True)+'\n'); print(json.dumps({'verdict':res['verdict'],'winner':win,'freeze':freeze},indent=2,sort_keys=True))
if __name__=='__main__': main()
