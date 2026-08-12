#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

YEARS=(2022,2023)
MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13))
BLIND=(20.0,55.0)
EXPECTED=(226,1075,3203,4504)
QUALITY_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
P19_RESULT_SHA='6f1ad0626b8a8bda03f18e7f3435f0651af8bebf65cfd1d970a6b61a8ba52319'
P19_PRELABEL_SHA='276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8'
P20_RESULT_SHA='9ec53f29281b11002a9e22b1086d12e054392e466ea74fe82ead0187289ba303'
P20_PRELABEL_SHA='8ca358ae0f3ac96b188de9eac7bcfd6f870470873a2b7ee73b7ae76497c12734'
V8_SHA='fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'
CONTROL={'recovered_at_25':22,'recovered_at_50':40,'recovered_at_100':75,'recovered_at_500':159,'qualified_matches':256,'top100_dominant_precision':0.7645689180574315,'mrr':0.019037817654898162}
LOG_V_SCALE=math.log(1.08)


def req(x:bool,msg:str)->None:
    if not x: raise RuntimeError(msg)
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); req(spec is not None and spec.loader is not None,f'cannot import {path}')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def order_sha(order:list[str])->str: return hashlib.sha256('\n'.join(order).encode()).hexdigest()
def trimmed(m:dict[str,Any])->dict[str,Any]: return {k:v for k,v in m.items() if k!='first_rank_by_label'}
def assert_control(m:dict[str,Any])->None:
    for k,v in CONTROL.items():
        if isinstance(v,float): req(abs(float(m[k])-v)<1e-12,f'#839 control changed: {k} {m[k]} != {v}')
        else: req(int(m[k])==int(v),f'#839 control changed: {k} {m[k]} != {v}')


def solar_bin(sol:float)->int:
    return int(math.floor((float(sol)%360.0)/2.0))%180


def build_background_index(lookup:dict[str,dict[str,Any]], pred:Any)->tuple[dict[str,dict[str,float]],dict[tuple[int,int],dict[str,Any]]]:
    norms:dict[str,dict[str,float]]={}
    staging:dict[tuple[int,int],dict[str,list[Any]]]={}
    for eid0,row in lookup.items():
        eid=str(eid0); year=int(eid[:4])
        if year not in YEARS: continue
        r=pred.normalize_event(row); req(not (BLIND[0]<=float(r['sol'])<=BLIND[1]),f'protected event reached background index: {eid}')
        norms[eid]=r; key=(year,solar_bin(r['sol']))
        d=staging.setdefault(key,{'ids':[],'sol':[],'u':[],'logv':[]})
        d['ids'].append(eid); d['sol'].append(float(r['sol'])); d['u'].append(pred.unit(float(r['lon']),float(r['lat']))); d['logv'].append(math.log(float(r['vg'])))
    out:dict[tuple[int,int],dict[str,Any]]={}
    for key,d in staging.items():
        out[key]={'ids':np.asarray(d['ids'],dtype=object),'sol':np.asarray(d['sol'],float),'u':np.asarray(d['u'],float),'logv':np.asarray(d['logv'],float)}
        req(out[key]['u'].ndim==2 and out[key]['u'].shape[1]==3 and len(out[key]['ids'])==len(out[key]['sol'])==len(out[key]['logv'])==out[key]['u'].shape[0],f'bad background bin {key}')
    return norms,out


def fit_full_model(rows:list[dict[str,float]],center_sol:float,pred:Any)->tuple[str,Any,Any]:
    req(len(rows)>0,'candidate-year has no members')
    units=np.asarray([pred.unit(r['lon'],r['lat']) for r in rows],float); logs=np.asarray([math.log(r['vg']) for r in rows],float)
    if len(rows)<2:
        u=np.mean(units,axis=0); n=float(np.linalg.norm(u)); req(math.isfinite(n) and n>1e-12,'degenerate static candidate radiant'); u/=n
        return ('static',u,float(np.mean(logs)))
    x=np.asarray([pred.signed_circular_delta(r['sol'],center_sol)/10.0 for r in rows],float)
    D=np.column_stack([np.ones(len(rows),float),x]); T=np.column_stack([units,logs]); coef,*_=np.linalg.lstsq(D,T,rcond=None); req(coef.shape==(2,4) and np.isfinite(coef).all(),'nonfinite full candidate trajectory fit')
    return ('affine',coef,None)


def residuals_for_bin(entry:dict[str,Any],model:tuple[str,Any,Any],center_sol:float,exclude:set[str],pred:Any)->np.ndarray:
    ids=entry['ids']; mask=np.asarray([str(eid) not in exclude for eid in ids],dtype=bool)
    if not mask.any(): return np.empty(0,float)
    sol=entry['sol'][mask]; actual_u=entry['u'][mask]; actual_logv=entry['logv'][mask]
    kind,a,b=model
    if kind=='static':
        pu=np.repeat(np.asarray(a,float)[None,:],len(sol),axis=0); plog=np.full(len(sol),float(b),float)
    else:
        x=((sol-float(center_sol)+180.0)%360.0-180.0)/10.0; D=np.column_stack([np.ones(len(sol),float),x]); y=D@np.asarray(a,float); pu=y[:,:3]; norms=np.linalg.norm(pu,axis=1); req(np.isfinite(norms).all() and np.all(norms>1e-12),'degenerate background predicted radiant'); pu=pu/norms[:,None]; plog=y[:,3]; req(np.isfinite(plog).all(),'nonfinite background predicted speed')
    dots=np.clip(np.sum(actual_u*pu,axis=1),-1.0,1.0); radiant=np.degrees(np.arccos(dots))/3.0; speed=np.abs(actual_logv-plog)/LOG_V_SCALE; out=np.hypot(radiant,speed); req(np.isfinite(out).all(),'nonfinite background residual'); return out


def candidate_background_features(f:dict[str,Any],norms:dict[str,dict[str,float]],bg:dict[tuple[int,int],dict[str,Any]],pred:Any)->dict[str,Any]:
    centroids=f.get('centroids',{}); all_ids=list(map(str,f['event_ids'])); exclude=set(all_ids); annual=[]
    for year in YEARS:
        c=centroids.get(str(year)); req(c is not None,f'missing centroid {f["family_id"]} {year}')
        ids=[eid for eid in all_ids if int(eid[:4])==year]; req(ids,f'no annual members {f["family_id"]} {year}')
        rows=[]
        for eid in ids: req(eid in norms,f'candidate member absent from target-excluded background index: {eid}'); rows.append(norms[eid])
        center_sol=float(c['sol']); internal=pred.loo_year(rows,center_sol); tube=float(internal['pred_q90']); req(math.isfinite(tube) and tube>=0.0,'invalid internal q90')
        model=fit_full_model(rows,center_sol,pred); bins=sorted({solar_bin(r['sol']) for r in rows}); intruding=0; total=0
        for b in bins:
            entry=bg.get((year,b)); req(entry is not None,f'missing background stratum {year}/{b}')
            residual=residuals_for_bin(entry,model,center_sol,exclude,pred); intruding+=int(np.count_nonzero(residual<=tube)); total+=int(residual.size)
        req(total>0,f'empty local nonmember background {f["family_id"]} {year}')
        annual.append({'year':year,'members':len(rows),'bins':bins,'tube_q90':tube,'background_count':total,'intruding_count':intruding,'intrusion_fraction':float(intruding/total),'learned_fraction':float(internal['learned'])})
    worst=max(float(a['intrusion_fraction']) for a in annual); mean=float(np.mean([a['intrusion_fraction'] for a in annual])); q90=max(float(a['tube_q90']) for a in annual)
    return {'worst_year_intrusion_fraction':worst,'mean_intrusion_fraction':mean,'worst_year_predictive_q90':q90,'annual':annual}


def contrast_order(rows:list[dict[str,Any]])->list[str]:
    return [str(r['family_id']) for r in sorted(rows,key=lambda r:(float(r['features']['worst_year_intrusion_fraction']),float(r['features']['mean_intrusion_fraction']),float(r['features']['worst_year_predictive_q90']),str(r['family_id'])))]


def fuse(base:list[str],contrast:list[str])->list[str]:
    req(len(base)==len(contrast) and set(base)==set(contrast),'fusion universe mismatch'); br={fid:i+1 for i,fid in enumerate(base)}; cr={fid:i+1 for i,fid in enumerate(contrast)}
    return sorted(base,key=lambda fid:(br[fid]+cr[fid],br[fid],fid))


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--quality-source',type=Path,required=True); p.add_argument('--predictive-source',type=Path,required=True); p.add_argument('--support-source-parts',type=Path,required=True); p.add_argument('--candidate-payload',type=Path,required=True); p.add_argument('--baseline-payload',type=Path,required=True); p.add_argument('--scorer-parts',type=Path,required=True); p.add_argument('--v8-result-json',type=Path,required=True); p.add_argument('--p19-result-json',type=Path,required=True); p.add_argument('--p19-prelabel-json',type=Path,required=True); p.add_argument('--p20-result-json',type=Path,required=True); p.add_argument('--p20-prelabel-json',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.quality_source)==QUALITY_SHA,'#839 source changed'); req(sha(a.v8_result_json)==V8_SHA,'v8 changed'); req(sha(a.p19_result_json)==P19_RESULT_SHA and sha(a.p19_prelabel_json)==P19_PRELABEL_SHA,'P19 changed'); req(sha(a.p20_result_json)==P20_RESULT_SHA and sha(a.p20_prelabel_json)==P20_PRELABEL_SHA,'P20 changed')
    qmod=load_module(a.quality_source,'frozen_839_background_contrast'); pred=load_module(a.predictive_source,'frozen_internal_tube_rule')
    p19=json.loads(a.p19_prelabel_json.read_text()); p20=json.loads(a.p20_prelabel_json.read_text()); hard=p19['hard_families']; s19=p19['soft_families']; s20=p20['soft_families']; hard_order=list(map(str,p19['hard_order'])); fams=hard+s19+s20
    req((len(hard),len(s19),len(s20),len(fams))==EXPECTED,'candidate universe changed'); ids=[str(f['family_id']) for f in fams]; req(len(set(ids))==4504,'candidate ID collision')
    source={str(f['family_id']):'hard' for f in hard}; source.update({str(f['family_id']):'p19' for f in s19}); source.update({str(f['family_id']):'p20' for f in s20}); hard_rank={fid:i+1 for i,fid in enumerate(hard_order)}

    qmod.v1.mult.YEARS=YEARS; qmod.v1.mult.MONTH_KEYS=MONTH_KEYS; qmod.v1.mult.TOP_K=100; runtime=qmod.v1.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts); support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS='orbittrace-gmn-local-background-trajectory-contrast-v1'; support.RANKING_VARIANTS=('persistence',); req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'blind interval changed'); setattr(a,'fixed4_baseline_json',a.v8_result_json); _candidate,base,_scorer=support.load_sources(a); scan,_cal,labels,sources=support.parse_catalogue(base); req(sorted(scan)==list(YEARS) and [x['key'] for x in sources]==list(MONTH_KEYS),'GMN panel changed')
    lookup=qmod.v2.event_lookup(scan); norms,bg=build_background_index(lookup,pred); req(len(norms)>0 and len(bg)>0,'background index empty')

    # Complete label-free local-background vector/order before any truth-derived ranking operation.
    feature_rows=[]
    for i,f in enumerate(fams,1):
        feature_rows.append({'family_id':str(f['family_id']),'source':source[str(f['family_id'])],'features':candidate_background_features(f,norms,bg,pred)})
        if i%250==0: print(json.dumps({'BACKGROUND_CONTRAST_PROGRESS':i,'total':len(fams)}),flush=True)
    corder=contrast_order(feature_rows); req(len(corder)==4504 and set(corder)==set(ids),'contrast order invalid')
    prelabel={'scope':'GMN 2022/2023 target-excluded local-background trajectory contrast','candidate_counts':{'hard':226,'p19':1075,'p20':3203,'union':4504},'background_stratum_degrees':2.0,'tube_definition':'candidate annual leave-one-out predictive q90','contrast_order_sha256':order_sha(corder),'families':feature_rows,'parameter_search':False,'truth_used_in_contrast':False,'blind_exclusion':list(BLIND),'sonotaco_2013_2014_access':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False}
    pp=a.output/'GMN_LOCAL_BACKGROUND_TRAJECTORY_CONTRAST_PRELABEL.json'; pp.write_text(json.dumps(prelabel,indent=2,sort_keys=True,allow_nan=False)+'\n'); prelabel_sha=sha(pp)

    # Exact active #839 grouped-OOF baseline.
    eligible=qmod.v1.eligible_labels(labels); by={str(f['family_id']):f for f in fams}; truths={fid:qmod.v1.family_truth(by[fid],labels,eligible) for fid in ids}; cm=qmod.centroid_matrix(fams); nf=qmod.neighbor_features(cm); x=[]
    for i,f in enumerate(fams):
        fid=str(f['family_id']); src=source[fid]; srcf=[float(src=='hard'),float(src=='p19'),float(src=='p20')]; p20f=[float(f.get('p20_cross_year_distance',0.0)),math.log1p(max(int(f.get('p20_min_anchor_count',0)),0)),float(f.get('p20_min_bin_strength',0.0)),float(f.get('p20_min_quartet_score',0.0))]; x.append(qmod.v1.structural_features(f,hard_rank)+qmod.v2.cohesion_features(f,lookup,support,base)+srcf+p20f+nf[i].tolist())
    x=np.asarray(x,float); req(x.shape==(4504,34) and np.isfinite(x).all(),'active feature matrix changed'); target=np.asarray([float(truths[fid]['f1']) if truths[fid]['positive'] else 0.0 for fid in ids],float); groups=[('SHOWER/'+str(truths[fid]['best_label'])) if truths[fid]['best_label'] is not None else ('NEG/'+fid) for fid in ids]; folds=np.asarray([qmod.v1.deterministic_fold(g) for g in groups],int); weights=qmod.grouped_weights(groups); oof=np.zeros(4504,float)
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; req(tr.any() and te.any(),f'empty fold {fold}'); req({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}),f'group leakage {fold}'); m=qmod.model(); m.fit(x[tr],target[tr],sample_weight=weights[tr]); oof[te]=m.predict(x[te])
    tie=[(hard_rank.get(fid,999999),fid) for fid in ids]; baseline_order=[ids[i] for i in qmod.diversity_order(oof,cm,0.8,1.0,tie)]; baseline=qmod.v1.monotone_metrics(fams,baseline_order,truths,eligible); assert_control(baseline)
    fused_order=fuse(baseline_order,corder); fused=qmod.v1.monotone_metrics(fams,fused_order,truths,eligible); gates={'recovered_at_100_strictly_better':int(fused['recovered_at_100'])>75,'recovered_at_50_not_worse':int(fused['recovered_at_50'])>=40,'recovered_at_25_not_worse':int(fused['recovered_at_25'])>=22,'top100_precision_not_worse':float(fused['top100_dominant_precision'])>=CONTROL['top100_dominant_precision'],'mrr_not_worse':float(fused['mrr'])>=CONTROL['mrr']}; passed=all(gates.values()); verdict='PASS_GMN_LOCAL_BACKGROUND_TRAJECTORY_CONTRAST_V1' if passed else 'FAIL_GMN_LOCAL_BACKGROUND_TRAJECTORY_CONTRAST_V1'
    result={'verdict':verdict,'scientific_role':'TARGET_EXCLUDED_GMN_LOCAL_BACKGROUND_CONTRAST_DIAGNOSTIC','candidate_counts':prelabel['candidate_counts'],'baseline':trimmed(baseline),'background_contrast_only':trimmed(qmod.v1.monotone_metrics(fams,corder,truths,eligible)),'equal_rank_fusion':trimmed(fused),'pass_gates':gates,'prelabel_sha256':prelabel_sha,'baseline_order_sha256':order_sha(baseline_order),'contrast_order_sha256':order_sha(corder),'fused_order_sha256':order_sha(fused_order),'background_stratum_degrees':2.0,'parameter_search':False,'background_statistic_search':False,'fusion_search':False,'family_deletion':False,'membership_changed':False,'candidate_generation_recomputed':False,'hdbscan_tree_score_used':False,'sonotaco_2013_2014_access':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'blind_exclusion':list(BLIND),'claim_boundary':'GMN development only. PASS may authorize one separately frozen SonotaCo/v31 transfer; FAIL permanently closes this exact background-contrast rule.'}; out=a.output/'GMN_LOCAL_BACKGROUND_TRAJECTORY_CONTRAST_V1.json'; out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':verdict,'baseline25':baseline['recovered_at_25'],'fused25':fused['recovered_at_25'],'baseline50':baseline['recovered_at_50'],'fused50':fused['recovered_at_50'],'baseline100':baseline['recovered_at_100'],'fused100':fused['recovered_at_100'],'baseline_precision':baseline['top100_dominant_precision'],'fused_precision':fused['top100_dominant_precision'],'baseline_mrr':baseline['mrr'],'fused_mrr':fused['mrr'],'gates':gates,'prelabel_sha256':prelabel_sha},indent=2,sort_keys=True)); return 0

if __name__=='__main__': raise SystemExit(main())
