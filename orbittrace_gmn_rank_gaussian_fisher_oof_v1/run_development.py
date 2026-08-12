#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math
from pathlib import Path
from typing import Any
import numpy as np
from scipy.special import ndtri
from sklearn.covariance import LedoitWolf
from orbittrace_gmn_v31_principle_local_geometry_oof_v1 import run_development as parent
q=parent.q
N=226; D=23; DIV_L=.8; DIV_S=1.; BLIND=(20.,55.)
FEATURE_SHA='fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5'; ORDER_SHA='2dcaaffaefca68e877fea82ff46a68bbd4c7960dedfdd00a114311d41605b65e'; MARGIN_SHA='f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd'; FISHER_SHA='9957292fbe41efa407b9bc5b1f4160cdc0899632135a10b56d2f91f04d54c46e'
PARENT={'recovered_at_100':69,'recovered_at_50':41,'top100_dominant_precision':0.7677499561973543,'mrr':0.05055989766869564,'qualified_matches':95}
def req(x,m):
    if not x: raise RuntimeError(m)
def verify(m):
    for k,v in PARENT.items():
        if isinstance(v,float): req(abs(float(m[k])-v)<1e-15,f'parent {k} changed')
        else: req(int(m[k])==v,f'parent {k} changed')
def load(root):
    m=json.loads((root/'GMN_DEVELOPMENT_FIXTURE_V1.json').read_text()); req(m['verdict']=='PASS_GMN_DEVELOPMENT_FIXTURE_V1' and m['scientific_change'] is False,'fixture invalid'); req(m['feature_matrix_sha256']==FEATURE_SHA and m['hard_order_sha256']==ORDER_SHA and m['parent_margin_sha256']==MARGIN_SHA and m['fisher_scaled_sha256']==FISHER_SHA,'fixture identity changed'); req(m['blind_exclusion']==[20.0,55.0],'blind changed')
    for k in ('sonotaco_2013_2014_access','target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access'): req(m[k] is False,f'firewall {k}')
    X=np.load(root/'features.npy',allow_pickle=False); cm=np.load(root/'centroids.npy',allow_pickle=False); y=np.load(root/'positive.npy',allow_pickle=False); fs=np.load(root/'fisher_scaled.npy',allow_pickle=False); pm=np.load(root/'parent_margin.npy',allow_pickle=False); p=json.loads((root/'development_labels_and_memberships.json').read_text())
    req(X.shape==(N,D) and parent.array_sha(X)==FEATURE_SHA,'X changed'); req(parent.array_sha(fs)==FISHER_SHA and parent.array_sha(pm)==MARGIN_SHA,'scores changed')
    ids=list(map(str,p['ids'])); order=list(map(str,p['hard_order'])); groups=list(map(str,p['groups'])); hard=p['hard_families']; truths={str(k):v for k,v in p['truths'].items()}; eligible=p['eligible']; req(parent.order_sha(order)==ORDER_SHA and [str(f['family_id']) for f in hard]==ids,'families changed'); req(np.array_equal(y,np.array([bool(truths[i]['positive']) for i in ids],dtype=bool)),'target changed')
    return X,cm,y,fs,pm,ids,order,groups,hard,truths,eligible,m

def rank_gaussian(train_raw, eval_raw):
    n=len(train_raw); req(n>=2 and np.isfinite(train_raw).all() and np.isfinite(eval_raw).all(),'bad raw feature')
    out=np.empty(len(eval_raw),dtype=float)
    for i,x in enumerate(eval_raw):
        less=int(np.sum(train_raw<x)); equal=int(np.sum(train_raw==x)); p=(less+.5*equal+.5)/(n+1.0); req(0<p<1,'plotting position out of range'); out[i]=float(ndtri(p))
    req(np.isfinite(out).all(),'nonfinite rank Gaussian'); return out

def oof(X,y,groups):
    folds=np.array([q.v1.deterministic_fold(g) for g in groups],dtype=int); req(set(folds)==set(range(5)),'folds changed'); out=np.zeros(len(X)); diag=[]
    for f in range(5):
        tr=folds!=f; te=folds==f; ti=np.where(tr)[0]; ei=np.where(te)[0]; req({groups[i] for i in ti}.isdisjoint({groups[i] for i in ei}),'group leakage')
        rawtr=X[tr]; rawte=X[te]; rtr=np.empty_like(rawtr,dtype=float); rte=np.empty_like(rawte,dtype=float)
        constants=0
        for j in range(D):
            rtr[:,j]=rank_gaussian(rawtr[:,j],rawtr[:,j]); rte[:,j]=rank_gaussian(rawtr[:,j],rawte[:,j]); constants+=int(np.all(rawtr[:,j]==rawtr[0,j]))
        mu=rtr.mean(0); sd=rtr.std(0,ddof=0); sc=sd.copy(); sc[sc==0]=1.; ztr=(rtr-mu)/sc; zte=(rte-mu)/sc; pos=y[tr]; neg=~pos; P=ztr[pos]; Nn=ztr[neg]
        mup=P.mean(0); mun=Nn.mean(0); lp=LedoitWolf(assume_centered=False,store_precision=False).fit(P); ln=LedoitWolf(assume_centered=False,store_precision=False).fit(Nn); cp=np.asarray(lp.covariance_); cn=np.asarray(ln.covariance_); pool=.5*(cp+cn); req(np.isfinite(pool).all() and np.allclose(pool,pool.T,rtol=0,atol=1e-12),'bad covariance'); eig=np.linalg.eigvalsh(pool); req(np.isfinite(eig).all() and eig.min()>0,'non-PD'); w=np.linalg.solve(pool,mup-mun); mid=.5*(mup+mun); req(np.isfinite(w).all() and np.linalg.norm(w)>0,'bad direction')
        for j,gi in enumerate(ei.tolist()): out[gi]=float(np.dot(zte[j]-mid,w))
        diag.append({'fold':f,'train_examples':int(tr.sum()),'test_examples':int(te.sum()),'training_constant_raw_features':constants,'post_rank_zero_variance_features':int(np.sum(sd==0)),'positive_references':int(pos.sum()),'nonpositive_references':int(neg.sum()),'positive_ledoit_wolf_shrinkage':float(lp.shrinkage_),'nonpositive_ledoit_wolf_shrinkage':float(ln.shrinkage_),'pooled_min_eigenvalue':float(eig.min()),'pooled_max_eigenvalue':float(eig.max()),'direction_norm':float(np.linalg.norm(w))})
    req(np.isfinite(out).all(),'nonfinite OOF'); return out,diag

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--fixture-root',type=Path,required=True); ap.add_argument('--quality-source',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True); req(parent.sha(a.quality_source)==parent.QUALITY_SHA,'ranker changed')
    X,cm,y,fs,pm,ids,order,groups,hard,truths,eligible,manifest=load(a.fixture_root); hr={fid:i+1 for i,fid in enumerate(order)}; tie=[(hr[i],i) for i in ids]; pi=q.diversity_order(fs,cm,DIV_L,DIV_S,tie); pf=parent.equal_rank_fusion(order,[ids[i] for i in pi]); pmet=q.v1.monotone_metrics(hard,pf,truths,eligible); verify(pmet)
    raw,fd=oof(X,y,groups); ps=float(np.median(np.abs(fs))); rs=float(np.median(np.abs(raw))); req(ps>0 and rs>0 and math.isfinite(ps) and math.isfinite(rs),'bad scale'); uf=ps/rs; scaled=raw*uf; idx=q.diversity_order(scaled,cm,DIV_L,DIV_S,tie); fused=parent.equal_rank_fusion(order,[ids[i] for i in idx]); cand=q.v1.monotone_metrics(hard,fused,truths,eligible); req(int(cand['qualified_matches'])==95,'qualified changed')
    gates={'recovered_at_100_strictly_above_fisher_parent':int(cand['recovered_at_100'])>69,'recovered_at_50_not_below_fisher_parent':int(cand['recovered_at_50'])>=41,'top100_precision_not_below_fisher_parent':float(cand['top100_dominant_precision'])>=PARENT['top100_dominant_precision'],'mrr_not_below_fisher_parent':float(cand['mrr'])>=PARENT['mrr'],'qualified_count_identical':int(cand['qualified_matches'])==95}; passed=all(gates.values())
    r={'verdict':'PASS_GMN_RANK_GAUSSIAN_FISHER_OOF' if passed else 'FAIL_GMN_RANK_GAUSSIAN_FISHER_OOF','scientific_role':'TARGET_EXCLUDED_GMN_RANK_GAUSSIAN_FISHER_SUCCESSOR_ONLY','first_valid_outcome_binding':True,'candidate_count':N,'feature_dimension':D,'feature_matrix_sha256':parent.array_sha(X),'hard_order_sha256':parent.order_sha(order),'parent_margin_sha256':parent.array_sha(pm),'fisher_parent_scaled_sha256':parent.array_sha(fs),'rank_gaussian_raw_sha256':parent.array_sha(raw),'rank_gaussian_scaled_sha256':parent.array_sha(scaled),'fisher_parent_median_absolute_score':ps,'rank_gaussian_raw_median_absolute_score':rs,'unit_factor':uf,'transform':'per-feature fold-training empirical normal score p=(L+0.5E+0.5)/(n+1), then fold-training z-score','mechanism':'balanced Ledoit-Wolf Fisher after rank-Gaussian marginal transform','strict_whole_shower_oof':True,'diversity':{'lambda':DIV_L,'scale':DIV_S},'fusion':'equal rank-sum with immutable P19 hard order','fisher_parent':parent.metric_subset(pmet),'candidate':parent.metric_subset(cand),'pass_gates':gates,'fold_diagnostics':fd,'plotting_position_search':False,'quantile_clipping':False,'transform_search':False,'raw_rank_blend_search':False,'covariance_estimator_search':False,'covariance_weight_search':False,'regularization_search':False,'class_prior_search':False,'feature_search':False,'dimensionality_reduction_search':False,'scale_statistic_search':False,'unit_transform_search':False,'threshold_search':False,'diversity_search':False,'fusion_search':False,'candidate_generation_recomputed':False,'membership_changed':False,'family_deletion':False,'sonotaco_2013_2014_access':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'blind_exclusion':list(BLIND)}
    (a.output/'GMN_RANK_GAUSSIAN_FISHER_OOF_RESULT.json').write_text(json.dumps(r,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':r['verdict'],'fisher100':pmet['recovered_at_100'],'candidate100':cand['recovered_at_100'],'fisher50':pmet['recovered_at_50'],'candidate50':cand['recovered_at_50'],'fisher_precision':pmet['top100_dominant_precision'],'candidate_precision':cand['top100_dominant_precision'],'fisher_mrr':pmet['mrr'],'candidate_mrr':cand['mrr'],'qualified':cand['qualified_matches'],'unit_factor':uf,'scaled_sha256':parent.array_sha(scaled)},indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
