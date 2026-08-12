#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math
from pathlib import Path
from typing import Any
import numpy as np
from sklearn.covariance import LedoitWolf
from orbittrace_gmn_v31_principle_local_geometry_oof_v1 import run_development as parent
q=parent.q
N=226; D=23; DIV_L=0.8; DIV_S=1.0; BLIND=(20.0,55.0)
FEATURE_SHA='fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5'
ORDER_SHA='2dcaaffaefca68e877fea82ff46a68bbd4c7960dedfdd00a114311d41605b65e'
MARGIN_SHA='f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd'
FISHER_SHA='9957292fbe41efa407b9bc5b1f4160cdc0899632135a10b56d2f91f04d54c46e'
PARENT={'recovered_at_100':69,'recovered_at_50':41,'top100_dominant_precision':0.7677499561973543,'mrr':0.05055989766869564,'qualified_matches':95}

def req(x,m):
    if not x: raise RuntimeError(m)

def verify(metrics):
    for k,v in PARENT.items():
        if isinstance(v,float): req(abs(float(metrics[k])-v)<1e-15,f'parent {k} changed')
        else: req(int(metrics[k])==v,f'parent {k} changed')

def load(root:Path):
    m=json.loads((root/'GMN_DEVELOPMENT_FIXTURE_V1.json').read_text())
    req(m['verdict']=='PASS_GMN_DEVELOPMENT_FIXTURE_V1' and m['scientific_change'] is False,'fixture invalid')
    req(m['feature_matrix_sha256']==FEATURE_SHA and m['hard_order_sha256']==ORDER_SHA,'fixture identity changed')
    req(m['parent_margin_sha256']==MARGIN_SHA and m['fisher_scaled_sha256']==FISHER_SHA,'fixture parent hashes changed')
    req(m['blind_exclusion']==[20.0,55.0],'fixture blind changed')
    for k in ('sonotaco_2013_2014_access','target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access'): req(m[k] is False,f'fixture firewall {k}')
    X=np.load(root/'features.npy',allow_pickle=False); cm=np.load(root/'centroids.npy',allow_pickle=False); y=np.load(root/'positive.npy',allow_pickle=False); fs=np.load(root/'fisher_scaled.npy',allow_pickle=False); pm=np.load(root/'parent_margin.npy',allow_pickle=False)
    p=json.loads((root/'development_labels_and_memberships.json').read_text())
    req(X.shape==(N,D) and parent.array_sha(X)==FEATURE_SHA,'X changed'); req(parent.array_sha(fs)==FISHER_SHA and parent.array_sha(pm)==MARGIN_SHA,'score arrays changed')
    ids=list(map(str,p['ids'])); order=list(map(str,p['hard_order'])); groups=list(map(str,p['groups'])); hard=p['hard_families']; truths={str(k):v for k,v in p['truths'].items()}; eligible=p['eligible']
    req(parent.order_sha(order)==ORDER_SHA and [str(f['family_id']) for f in hard]==ids,'family/order changed')
    req(np.array_equal(y,np.array([bool(truths[i]['positive']) for i in ids],dtype=bool)),'labels changed')
    return X,cm,y,fs,pm,ids,order,groups,hard,truths,eligible,m

def oof_diag(X,y,groups):
    folds=np.array([q.v1.deterministic_fold(g) for g in groups],dtype=int); req(set(folds)==set(range(5)),'folds changed')
    out=np.zeros(len(X)); diag=[]
    for f in range(5):
        tr=folds!=f; te=folds==f; tg={groups[i] for i in np.where(tr)[0]}; eg={groups[i] for i in np.where(te)[0]}; req(tg.isdisjoint(eg),'group leakage')
        mu=X[tr].mean(0); sd=X[tr].std(0,ddof=0); sc=sd.copy(); sc[sc==0]=1.; ztr=(X[tr]-mu)/sc; zte=(X[te]-mu)/sc; pos=y[tr]; neg=~pos; P=ztr[pos]; Nn=ztr[neg]
        mup=P.mean(0); mun=Nn.mean(0); lp=LedoitWolf(assume_centered=False,store_precision=False).fit(P); ln=LedoitWolf(assume_centered=False,store_precision=False).fit(Nn)
        cp=np.asarray(lp.covariance_); cn=np.asarray(ln.covariance_); vp=np.diag(cp).copy(); vn=np.diag(cn).copy(); req(np.isfinite(vp).all() and np.isfinite(vn).all() and np.all(vp>0) and np.all(vn>0),'invalid diagonal variance')
        vd=.5*(vp+vn); req(np.all(np.isfinite(vd)) and np.all(vd>0),'invalid pooled diagonal'); w=(mup-mun)/vd; mid=.5*(mup+mun); req(np.isfinite(w).all() and np.linalg.norm(w)>0,'invalid direction')
        for j,gi in enumerate(np.where(te)[0].tolist()): out[gi]=float(np.dot(zte[j]-mid,w))
        offp=float(np.linalg.norm(cp-np.diag(vp),'fro')); offn=float(np.linalg.norm(cn-np.diag(vn),'fro'))
        diag.append({'fold':f,'train_examples':int(tr.sum()),'test_examples':int(te.sum()),'positive_references':int(pos.sum()),'nonpositive_references':int(neg.sum()),'positive_ledoit_wolf_shrinkage':float(lp.shrinkage_),'nonpositive_ledoit_wolf_shrinkage':float(ln.shrinkage_),'positive_offdiag_frobenius':offp,'nonpositive_offdiag_frobenius':offn,'pooled_diagonal_min':float(vd.min()),'pooled_diagonal_max':float(vd.max()),'direction_norm':float(np.linalg.norm(w))})
    req(np.isfinite(out).all(),'nonfinite score'); return out,diag

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--fixture-root',type=Path,required=True); ap.add_argument('--quality-source',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(parent.sha(a.quality_source)==parent.QUALITY_SHA,'ranker changed')
    X,cm,y,fs,pm,ids,order,groups,hard,truths,eligible,manifest=load(a.fixture_root); hr={fid:i+1 for i,fid in enumerate(order)}; tie=[(hr[i],i) for i in ids]
    pi=q.diversity_order(fs,cm,DIV_L,DIV_S,tie); po=[ids[i] for i in pi]; pf=parent.equal_rank_fusion(order,po); pmet=q.v1.monotone_metrics(hard,pf,truths,eligible); verify(pmet)
    raw,fd=oof_diag(X,y,groups); ps=float(np.median(np.abs(fs))); rs=float(np.median(np.abs(raw))); req(ps>0 and rs>0 and math.isfinite(ps) and math.isfinite(rs),'bad scale'); uf=ps/rs; scaled=raw*uf
    idx=q.diversity_order(scaled,cm,DIV_L,DIV_S,tie); local=[ids[i] for i in idx]; fused=parent.equal_rank_fusion(order,local); cand=q.v1.monotone_metrics(hard,fused,truths,eligible); req(int(cand['qualified_matches'])==95,'qualified changed')
    gates={'recovered_at_100_strictly_above_fisher_parent':int(cand['recovered_at_100'])>69,'recovered_at_50_not_below_fisher_parent':int(cand['recovered_at_50'])>=41,'top100_precision_not_below_fisher_parent':float(cand['top100_dominant_precision'])>=PARENT['top100_dominant_precision'],'mrr_not_below_fisher_parent':float(cand['mrr'])>=PARENT['mrr'],'qualified_count_identical':int(cand['qualified_matches'])==95}; passed=all(gates.values())
    r={'verdict':'PASS_GMN_DIAGONAL_SHRINKAGE_FISHER_OOF' if passed else 'FAIL_GMN_DIAGONAL_SHRINKAGE_FISHER_OOF','scientific_role':'TARGET_EXCLUDED_GMN_DIAGONAL_SHRINKAGE_FISHER_SUCCESSOR_ONLY','first_valid_outcome_binding':True,'candidate_count':N,'feature_dimension':D,'feature_matrix_sha256':parent.array_sha(X),'hard_order_sha256':parent.order_sha(order),'parent_margin_sha256':parent.array_sha(pm),'fisher_parent_scaled_sha256':parent.array_sha(fs),'diagonal_raw_sha256':parent.array_sha(raw),'diagonal_scaled_sha256':parent.array_sha(scaled),'fisher_parent_median_absolute_score':ps,'diagonal_raw_median_absolute_score':rs,'unit_factor':uf,'mechanism':'diagonal of classwise Ledoit-Wolf covariances then equal-class pooled Fisher','strict_whole_shower_oof':True,'diversity':{'lambda':DIV_L,'scale':DIV_S},'fusion':'equal rank-sum with immutable P19 hard order','fisher_parent':parent.metric_subset(pmet),'candidate':parent.metric_subset(cand),'pass_gates':gates,'fold_diagnostics':fd,'diagonal_variance_estimator_search':False,'full_diagonal_interpolation_search':False,'covariance_estimator_search':False,'regularization_search':False,'class_prior_search':False,'feature_search':False,'parent_diagonal_blend_search':False,'scale_statistic_search':False,'unit_transform_search':False,'threshold_search':False,'diversity_search':False,'fusion_search':False,'candidate_generation_recomputed':False,'membership_changed':False,'family_deletion':False,'sonotaco_2013_2014_access':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'blind_exclusion':list(BLIND)}
    (a.output/'GMN_DIAGONAL_SHRINKAGE_FISHER_OOF_RESULT.json').write_text(json.dumps(r,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':r['verdict'],'fisher100':pmet['recovered_at_100'],'candidate100':cand['recovered_at_100'],'fisher50':pmet['recovered_at_50'],'candidate50':cand['recovered_at_50'],'fisher_precision':pmet['top100_dominant_precision'],'candidate_precision':cand['top100_dominant_precision'],'fisher_mrr':pmet['mrr'],'candidate_mrr':cand['mrr'],'qualified':cand['qualified_matches'],'unit_factor':uf,'scaled_sha256':parent.array_sha(scaled)},indent=2,sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())
