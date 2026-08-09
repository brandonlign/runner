#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pickle
import re
import warnings
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

YEARS=(2023,2025)
BLIND_LOW=20.0
BLIND_HIGH=55.0
P2_SOURCE_SHA256='f19500f6b0dfe481d845af57f3b4d7ec35e678e2191388b7ff4611f8fb2c4eeb'
V8_SOURCE_COMMIT='c9d6c44704013ba0c9430100e98a29a56b453304'
DSH_SOURCE_SHA256='85cd11afbdebc4a0315ebf1daf42d10d4993d7ab088dd05301e3234b18340a5a'
SUPPORT_INELIGIBLE_RE=re.compile(r'^family ([A-Za-z0-9_.:-]+) year (2023|2025) has only ([0-9]+) events in local window$')
ELIGIBLE='P2 matched-literature pretruth panel checkpoint'
INELIGIBLE='P2_MATCHED_INPUT_INELIGIBLE'

def require(ok:bool,message:str)->None:
    if not ok: raise RuntimeError(message)
def sha256_file(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical_sha(value:Any)->str: return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); require(spec is not None and spec.loader is not None,f'cannot import {path}'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def write_checkpoint(path:Path,payload:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(pickle.dumps(payload,protocol=pickle.HIGHEST_PROTOCOL)); path.with_suffix(path.suffix+'.sha256').write_text(sha256_file(path)+'\n')

def write_ineligible(path:Path,panel:str,kind:str,detail:dict[str,Any])->int:
    payload={'classification':INELIGIBLE,'panel':panel,'years':list(YEARS),'blind_exclusion':[BLIND_LOW,BLIND_HIGH],'ineligibility_kind':kind,'detail':detail,'competitor_cluster_values_accessed':False,'known_shower_truth_accessed':False,'p2_membership_executed':False,'no_support_or_background_relaxation':True}
    write_checkpoint(path,payload); print(INELIGIBLE,panel,kind,json.dumps(detail,sort_keys=True)); return 0

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--panel',required=True,choices=('hdbscan','sugar')); p.add_argument('--strict-id-manifest',required=True,type=Path); p.add_argument('--exact-row-runner',required=True,type=Path); p.add_argument('--p2-source',required=True,type=Path); p.add_argument('--orbit-reader',required=True,type=Path); p.add_argument('--dsh-comparator',required=True,type=Path); p.add_argument('--archive-2023',required=True,type=Path); p.add_argument('--archive-2025',required=True,type=Path); p.add_argument('--base-runner',required=True,type=Path); p.add_argument('--support-source-parts',required=True,type=Path); p.add_argument('--candidate-payload',required=True,type=Path); p.add_argument('--baseline-payload',required=True,type=Path); p.add_argument('--scorer-parts',required=True,type=Path); p.add_argument('--output',required=True,type=Path); a=p.parse_args()
    require(sha256_file(a.p2_source)==P2_SOURCE_SHA256,'canonical P2 source changed'); require(sha256_file(a.dsh_comparator)==DSH_SOURCE_SHA256,'D_SH source changed')
    manifest=json.loads(a.strict_id_manifest.read_text()); require(manifest['classification']=='P2 matched-literature strict pretruth ID-only manifest','wrong P2 ID manifest'); require(manifest['years']==list(YEARS) and manifest['blind_exclusion']==[BLIND_LOW,BLIND_HIGH],'manifest universe changed'); require(manifest['competitor_cluster_values_parsed'] is False and manifest['known_shower_truth_values_parsed'] is False and manifest['native_shower_tokens_parsed'] is False,'labels entered manifest')
    side=a.strict_id_manifest.with_suffix(a.strict_id_manifest.suffix+'.sha256'); require(side.exists() and side.read_text().strip()==canonical_sha(manifest),'manifest hash mismatch')
    exact=load_module(a.exact_row_runner,f'p2_exact_rows_{a.panel}'); p2=load_module(a.p2_source,'p2_canonical_transfer'); orbit_reader=load_module(a.orbit_reader,'p2_exact_orbits'); dsh=p2.load_dsh_module(a.dsh_comparator)
    old=load_module(a.base_runner,'p2_lit_base'); runtime=exact.v8.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts); require(float(support.BLIND_LOW)==BLIND_LOW and float(support.BLIND_HIGH)==BLIND_HIGH,'blind interval changed'); support.YEARS=YEARS; support.MONTH_KEYS=tuple(); support.CORPUS='sonotaco-exact-row-literature-pairwise'; support.RANKING_VARIANTS=exact.RAW_FIXED4_RANKING_VARIANTS
    import types
    srcargs=types.SimpleNamespace(support_source_parts=a.support_source_parts,candidate_payload=a.candidate_payload,baseline_payload=a.baseline_payload,scorer_parts=a.scorer_parts); _candidate,base,_scorer=support.load_sources(srcargs); exact.v8.YEARS=YEARS; exact.v8.MONTH_KEYS=tuple(); exact.v8.mult.YEARS=YEARS; exact.v8.mult.MONTH_KEYS=tuple()
    archives={2023:a.archive_2023,2025:a.archive_2025}; ids_by_year={y:set(map(str,manifest['panels'][a.panel][str(y)]['scan_ids'])) for y in YEARS}; scan={y:exact.read_exact_geometry(y,archives[y],ids_by_year[y],base) for y in YEARS}; require(all(len(scan[y])==len(ids_by_year[y]) for y in YEARS),'exact geometry row count changed'); require(all(all(not(BLIND_LOW<=float(e['sol'])<=BLIND_HIGH) for e in scan[y]) for y in YEARS),'target interval entered P2 matched geometry')
    try:
        v8_panel=exact.run_v8_panel(a.panel,scan,support,runtime,base)
    except RuntimeError as exc:
        m=SUPPORT_INELIGIBLE_RE.fullmatch(str(exc))
        if m is None: raise
        return write_ineligible(a.output,a.panel,'P2_MATCHED_INPUT_INELIGIBLE_EXACT_V8_SUPPORT',{'family_id':m.group(1),'year':int(m.group(2)),'available_local_events':int(m.group(3)),'required_episode_events':128,'exact_exception':str(exc)})
    try:
        orbit_by_id={}
        for y in YEARS:
            orbit_by_id.update(orbit_reader.read_exact_orbits(y,archives[y],ids_by_year[y]))
    except RuntimeError as exc:
        if 'P2_MATCHED_INPUT_INELIGIBLE_' not in str(exc): raise
        return write_ineligible(a.output,a.panel,'P2_MATCHED_INPUT_INELIGIBLE_ORBIT',{'exact_exception':str(exc)})
    require(set(orbit_by_id)==set().union(*ids_by_year.values()),'P2 orbit universe differs from exact-row universe')
    by_id={str(f['family_id']):f for f in v8_panel['families']}; order=list(map(str,v8_panel['multiplicity_order'])); require(len(order)==len(by_id) and set(order)==set(by_id),'v8 order/family universe mismatch'); families=[by_id[fid] for fid in order]; family_rank={fid:i for i,fid in enumerate(order)}; event_lookup={y:{str(e['id']):e for e in scan[y]} for y in YEARS}; global_seeds=set().union(*(set(map(str,f['event_ids'])) for f in families)); require(global_seeds<=set(orbit_by_id),'v8 seed orbit missing')
    nonseed={y:[e for e in scan[y] if str(e['id']) not in global_seeds] for y in YEARS}; directions=[]; tx=[]; ty=[]; tw=[]; direction_audits=[]
    p2.YEARS=YEARS
    for fi,family in enumerate(families):
        fid=str(family['family_id']); ids={y:sorted(str(eid) for eid in family['event_ids'] if str(eid).startswith(f'SNM{y}:')) for y in YEARS}; rows={y:[event_lookup[y][eid] for eid in ids[y]] for y in YEARS}
        for sy,tt in ((2023,2025),(2025,2023)):
            require(len(ids[sy])>=4 and len(ids[tt])>=4,f'family {fid} invalid cross-year seeds'); center,inverse,obs_audit=p2.source_observation_model(rows[sy],base); target_center=p2.pooled_centroid(rows[tt]); mask=p2.wrapped_window_mask(nonseed[tt],target_center['sol'],base); neg=[e for e,k in zip(nonseed[tt],mask.tolist()) if k]
            if len(neg)<int(p2.MIN_DIRECTION_NEGATIVES): return write_ineligible(a.output,a.panel,'P2_MATCHED_INPUT_INELIGIBLE_DIRECTION_BACKGROUND',{'family_id':fid,'source_year':sy,'target_year':tt,'negative_count':len(neg),'required':int(p2.MIN_DIRECTION_NEGATIVES)})
            pos=rows[tt]; pos_ids=ids[tt]; neg_ids=[str(e['id']) for e in neg]; x_pos=np.column_stack((p2.mahalanobis_distance(pos,center,inverse,base),p2.min_exact_dsh_to_source(pos_ids,ids[sy],orbit_by_id,dsh))); x_neg=np.column_stack((p2.mahalanobis_distance(neg,center,inverse,base),p2.min_exact_dsh_to_source(neg_ids,ids[sy],orbit_by_id,dsh)))
            tx.extend((x_pos,x_neg)); ty.extend((np.ones(len(x_pos),dtype=np.int8),np.zeros(len(x_neg),dtype=np.int8))); tw.extend((np.full(len(x_pos),0.5/len(x_pos),dtype=np.float64),np.full(len(x_neg),0.5/len(x_neg),dtype=np.float64))); directions.append({'family_index':fi,'family_id':fid,'source_year':sy,'target_year':tt,'negative_event_ids':neg_ids,'negative_features':x_neg}); direction_audits.append({'family_id':fid,'source_year':sy,'target_year':tt,'source_seed_count':len(ids[sy]),'positive_count':len(x_pos),'negative_count':len(x_neg),'target_centroid_sol':float(target_center['sol']),**obs_audit})
        if (fi+1)%25==0 or fi+1==len(families): print(f'P2 matched feature family {fi+1}/{len(families)}',flush=True)
    X=np.vstack(tx).astype(np.float64,copy=False); y=np.concatenate(ty).astype(np.int8,copy=False); w=np.concatenate(tw).astype(np.float64,copy=False); require(X.shape[1]==2 and len(X)==len(y)==len(w) and np.all(np.isfinite(X)),'P2 matched training shape/finite failure'); require(abs(float(np.sum(w[y==1]))-0.5*len(directions))<=1e-8 and abs(float(np.sum(w[y==0]))-0.5*len(directions))<=1e-8,'P2 matched family-direction weights changed')
    scaler=StandardScaler(); scaler.fit(X,sample_weight=w); Xs=scaler.transform(X); classifier=LogisticRegression(penalty='l2',C=float(p2.LOGISTIC_C),solver='lbfgs',max_iter=int(p2.LOGISTIC_MAX_ITER),tol=float(p2.LOGISTIC_TOL),fit_intercept=True,class_weight=None,random_state=None)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always'); classifier.fit(Xs,y,sample_weight=w)
    convergence=[q for q in caught if issubclass(q.category,ConvergenceWarning)]; require(not convergence and int(np.max(classifier.n_iter_))<int(p2.LOGISTIC_MAX_ITER),'P2 matched logistic convergence failure')
    model={'feature_order':['d_obs','d_orb'],'scaler_mean':np.asarray(scaler.mean_).tolist(),'scaler_scale':np.asarray(scaler.scale_).tolist(),'scaler_var':np.asarray(scaler.var_).tolist(),'logistic_coef':np.asarray(classifier.coef_).tolist(),'logistic_intercept':np.asarray(classifier.intercept_).tolist(),'logistic_n_iter':np.asarray(classifier.n_iter_,dtype=np.int64).tolist(),'settings':{'penalty':'l2','C':float(p2.LOGISTIC_C),'solver':'lbfgs','max_iter':int(p2.LOGISTIC_MAX_ITER),'tol':float(p2.LOGISTIC_TOL),'fit_intercept':True,'class_weight':None,'family_direction_positive_total_weight':0.5,'family_direction_negative_total_weight':0.5,'window_half_width_deg':float(p2.WINDOW_HALF_WIDTH_DEG)}}; model_sha=canonical_sha(model)
    proposals=defaultdict(list); eps=np.finfo(np.float64).eps
    for d in directions:
        feats=np.asarray(d.pop('negative_features'),dtype=np.float64); probs=np.clip(classifier.predict_proba(scaler.transform(feats))[:,1],eps,1.0-eps); odds=probs/(1.0-probs)
        for eid,pr,od in zip(d['negative_event_ids'],probs.tolist(),odds.tolist()): proposals[eid].append({'family_index':int(d['family_index']),'family_id':str(d['family_id']),'source_year':int(d['source_year']),'target_year':int(d['target_year']),'probability':float(pr),'odds':float(od)})
    assignments={}; conflicted=0; resp=[]
    for eid,ps in proposals.items():
        require(eid not in global_seeds,'seed entered P2 matched competition'); conflicted+=int(len(ps)>1); denom=1.0+float(sum(x['odds'] for x in ps)); ranked=sorted(ps,key=lambda x:(-float(x['odds'])/denom,family_rank[str(x['family_id'])],str(x['family_id']))); best=dict(ranked[0]); r=float(best['odds']/denom)
        if r<=float(p2.RESPONSIBILITY_THRESHOLD): continue
        best['responsibility']=r; assignments[eid]=best; resp.append(r)
    added=defaultdict(list)
    for eid,rec in assignments.items(): added[int(rec['family_index'])].append(eid)
    expanded=[]
    for i,f in enumerate(families):
        out=json.loads(json.dumps(f)); seeds=set(map(str,f['event_ids'])); additions=sorted(set(added.get(i,[]))-global_seeds); out['p2_added_event_ids']=additions; out['p2_added_event_count']=len(additions); out['event_ids']=sorted(seeds|set(additions)); out['event_count']=len(out['event_ids']); expanded.append(out)
    membership_sha=canonical_sha(expanded); order_sha=hashlib.sha256(json.dumps(order,separators=(',',':')).encode()).hexdigest(); checkpoint={'classification':ELIGIBLE,'panel':a.panel,'years':list(YEARS),'blind_exclusion':[BLIND_LOW,BLIND_HIGH],'p2_source_sha256':P2_SOURCE_SHA256,'dsh_source_sha256':DSH_SOURCE_SHA256,'v8_source_commit':V8_SOURCE_COMMIT,'exact_event_rows':{str(y):len(scan[y]) for y in YEARS},'v8_family_count':len(families),'v8_multiplicity_order':order,'v8_order_pretruth_sha256':order_sha,'p2_model_pretruth':model,'p2_model_pretruth_sha256':model_sha,'p2_expanded_families':expanded,'p2_membership_pretruth_sha256':membership_sha,'p2_diagnostics':{'training_rows':len(X),'positive_training_rows':int(np.sum(y==1)),'negative_training_rows':int(np.sum(y==0)),'family_directions':len(directions),'assigned_nonseed_events':len(assignments),'conflicted_proposal_events':conflicted,'families_gaining_members':sum(bool(added.get(i)) for i in range(len(families))),'responsibility_median':float(np.median(resp)) if resp else None,'responsibility_min':float(min(resp)) if resp else None,'responsibility_max':float(max(resp)) if resp else None,'direction_audits':direction_audits,'v8_pretruth':{'support_rankings':v8_panel['support_rankings'],'repair':v8_panel['repair'],'scoring_summary':v8_panel['scoring_summary'],'scan_audits':v8_panel['scan_audits'],'quartets':v8_panel['quartets'],'components':v8_panel['components']}},'competitor_cluster_values_accessed':False,'known_shower_truth_accessed':False,'model_membership_and_rank_frozen_before_truth':True}
    require([str(f['family_id']) for f in expanded]==order,'P2 matched rank changed'); require(all(set(map(str,f['event_ids']))<=set(map(str,o['event_ids'])) for f,o in zip(families,expanded)),'P2 matched seed lost'); write_checkpoint(a.output,checkpoint); print(f'PASS_P2_MATCHED_PRETRUTH panel={a.panel} families={len(families)} model_sha={model_sha} membership_sha={membership_sha} order_sha={order_sha}',flush=True); return 0
if __name__=='__main__': raise SystemExit(main())
