#!/usr/bin/env python3
"""Frozen target-excluded GMN v31 successor using reverse-1NN slack geometry."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any
import numpy as np
import run_urc_union_ranker as q

N=226; D=23; CD=8; BLIND=[20.0,55.0]
MANIFEST_SHA='16fb5ef3cd8dbbb3873e9bc23874fe7da3db68498772a5e992fbceed6cb980d7'
X_SHA='fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5'
C_SHA='a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f'
PRELABEL_SHA='b45c4ce1a45bff515e411e211bc51dee879229ee97f7fcb7d8e7e05bfc106d09'
MARGIN_SHA='f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd'
LAMBDA=.8; DSCALE=1.0
HARD={'recovered_at_25':21,'recovered_at_50':38,'recovered_at_100':59,'top100_dominant_precision':0.6884631112636006,'mrr':0.046734076055452344,'qualified_matches':95}
PARENT={'recovered_at_25':23,'recovered_at_50':41,'recovered_at_100':66,'top100_dominant_precision':0.7229521515453452,'mrr':0.050244164168646674,'qualified_matches':95}

def req(x,m):
    if not x: raise RuntimeError(m)
def args():
    p=argparse.ArgumentParser(); p.add_argument('--self-test',action='store_true'); p.add_argument('--manifest',type=Path); p.add_argument('--features',type=Path); p.add_argument('--centroids',type=Path); p.add_argument('--output',type=Path); return p.parse_args()
def fsha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def asha(a:np.ndarray):
    h=hashlib.sha256(); h.update(str(a.dtype).encode()); h.update(str(tuple(a.shape)).encode()); h.update(np.ascontiguousarray(a).tobytes()); return h.hexdigest()
def osha(order): return hashlib.sha256('\n'.join(order).encode()).hexdigest()
def close(a,b): return abs(float(a)-float(b))<=1e-15
def subset(m): return {k:v for k,v in m.items() if k!='first_rank_by_label'}
def fuse(hard,local):
    hr={x:i+1 for i,x in enumerate(hard)}; lr={x:i+1 for i,x in enumerate(local)}
    return sorted(hard,key=lambda x:(hr[x]+lr[x],hr[x],x))
def winner(values, ids, hr):
    req(len(values)==len(ids) and len(ids)>0,'winner universe mismatch'); req(np.isfinite(values).all(),'nonfinite support')
    return min(range(len(ids)),key=lambda i:(-float(values[i]),hr[ids[i]],ids[i]))
def pairwise_radii(Z):
    Z=np.asarray(Z,dtype=float); req(Z.ndim==2 and len(Z)>=2,'invalid training geometry')
    diff=Z[:,None,:]-Z[None,:,:]; dist=np.linalg.norm(diff,axis=2); np.fill_diagonal(dist,np.inf); rho=np.min(dist,axis=1)
    req(np.isfinite(rho).all() and np.all(rho>0),'nonpositive/nonfinite reverse-1NN radius')
    return rho

def self_test():
    Z=np.asarray([[0.,0.],[2.,0.],[10.,0.]],dtype=float); rho=pairwise_radii(Z); req(np.array_equal(rho,np.asarray([2.,2.,8.])),f'radius test {rho}')
    z=np.asarray([7.,0.]); d=np.linalg.norm(Z-z,axis=1); slack=rho-d; req(np.array_equal(slack,np.asarray([-5.,-3.,5.])),f'slack test {slack}')
    # Sparse positive reference can have greater reverse slack than a closer dense negative reference.
    # p at 10 has rho 8 and q=7 => +5; n at 2 is closer (distance 5) but rho 2 => -3.
    req(float(d[1])<float(d[2]) and float(slack[2])>float(slack[1]),'density-adaptive support self-test failed')
    print(json.dumps({'verdict':'PASS_REVERSE1NN_SLACK_ENGINEERING_SELF_TESTS','radii':rho.tolist(),'slack':slack.tolist(),'reverse_k':1,'radius_label_blind':True,'search':False},indent=2,sort_keys=True)); return 0

def main():
    a=args()
    if a.self_test: return self_test()
    req(all(x is not None for x in (a.manifest,a.features,a.centroids,a.output)),'science args required'); a.output.mkdir(parents=True,exist_ok=True)
    req(fsha(a.manifest)==MANIFEST_SHA,'manifest changed'); m=json.loads(a.manifest.read_text()); X=np.load(a.features,allow_pickle=False); C=np.load(a.centroids,allow_pickle=False)
    req(m['verdict']=='PASS_GMN_V31_OFFLINE_DEVELOPMENT_PACKAGE_V1','package not PASS'); req(m['scientific_role']=='ENGINEERING_PROVENANCE_ONLY_NO_SUCCESSOR_EVALUATED','package role changed'); req(m['development_role']=='GMN_2022_2023_TARGET_EXCLUDED_ONLY','development role changed')
    req(X.shape==(N,D) and C.shape==(N,CD) and np.isfinite(X).all() and np.isfinite(C).all(),'matrix invalid'); req(asha(X)==m['feature_matrix_sha256']==X_SHA,'X hash'); req(asha(C)==m['centroid_matrix_sha256']==C_SHA,'C hash'); req(m['parent_prelabel_sha256']==PRELABEL_SHA and m['parent_margin_sha256']==MARGIN_SHA,'parent provenance'); req(m['blind_exclusion']==BLIND,'blind changed')
    for k in ('raw_event_rows_exported','raw_event_ids_exported','raw_hidden_label_mapping_exported','new_feature_or_score_created','new_rank_evaluated','successor_selected','sonotaco_2013_2014_access','target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access'): req(m[k] is False,f'package firewall {k}')
    ids=[str(x) for x in m['family_input_order']]; hard=[str(x) for x in m['hard_order']]; rows=m['rows']; eligible_labels=[str(x) for x in m['eligible_labels']]
    req(len(ids)==N and len(set(ids))==N and len(hard)==N and set(hard)==set(ids),'family universe'); req([str(r['family_id']) for r in rows]==ids,'row alignment'); req(len(eligible_labels)==355 and len(set(eligible_labels))==355,'eligible labels')
    truths={str(r['family_id']):r['truth'] for r in rows}; groups=[str(r['strict_group']) for r in rows]; folds=np.asarray([int(r['fold']) for r in rows]); y=np.asarray([bool(r['truth']['positive']) for r in rows]); req(set(folds.tolist())==set(range(5)) and int(y.sum())==111 and int((~y).sum())==115,'fold/truth counts')
    fam=[{'family_id':x} for x in ids]; elig={x:None for x in eligible_labels}; hm=q.v1.monotone_metrics(fam,hard,truths,elig)
    for k,v in HARD.items(): req(close(hm[k],v) if isinstance(v,float) else int(hm[k])==v,f'hard metric {k}'); req(close(m['parent_baseline_metrics'][k],v) if isinstance(v,float) else int(m['parent_baseline_metrics'][k])==v,f'package hard {k}')
    for k,v in PARENT.items(): req(close(m['parent_fused_metrics'][k],v) if isinstance(v,float) else int(m['parent_fused_metrics'][k])==v,f'package parent {k}')
    hr={x:i+1 for i,x in enumerate(hard)}; parent=np.zeros(N); rev=np.zeros(N); evidence=[]; fdiag=[]
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; tri=np.where(tr)[0]; tei=np.where(te)[0]; req({groups[i] for i in tri}.isdisjoint({groups[i] for i in tei}),f'group leak {fold}')
        mu=X[tr].mean(0); sd=X[tr].std(0,ddof=0); sc=sd.copy(); sc[sc==0]=1.; Ztr=(X[tr]-mu)/sc; Zte=(X[te]-mu)/sc; yt=y[tr]; tids=[ids[i] for i in tri]; req(yt.any() and (~yt).any(),'class missing')
        rho=pairwise_radii(Ztr); P=Ztr[yt]; Q=Ztr[~yt]; pids=[tids[i] for i in np.where(yt)[0]]; nids=[tids[i] for i in np.where(~yt)[0]]; prho=rho[yt]; nrho=rho[~yt]
        foldrev=[]; foldpar=[]; pos_inside=0; neg_inside=0
        for j,gi in enumerate(tei):
            z=Zte[j]; dp=np.linalg.norm(P-z,axis=1); dn=np.linalg.norm(Q-z,axis=1); ppar=float(np.min(dp)); npar=float(np.min(dn)); mp=npar-ppar; parent[gi]=mp; foldpar.append(mp)
            ps=prho-dp; ns=nrho-dn; ip=winner(ps,pids,hr); inn=winner(ns,nids,hr); Apos=float(ps[ip]); Aneg=float(ns[inn]); mr=Apos-Aneg; rev[gi]=mr; foldrev.append(mr); pos_inside+=int(Apos>0); neg_inside+=int(Aneg>0)
            evidence.append({'family_id':ids[gi],'fold':fold,'parent_margin':mp,'positive_support_slack':Apos,'nonpositive_support_slack':Aneg,'raw_reverse_margin':mr,'winning_positive_reference':pids[ip],'winning_nonpositive_reference':nids[inn],'inside_any_positive_reverse1nn_radius':bool(Apos>0),'inside_any_nonpositive_reverse1nn_radius':bool(Aneg>0)})
        fdiag.append({'fold':fold,'train_examples':int(tr.sum()),'test_examples':int(te.sum()),'positive_references':int(yt.sum()),'nonpositive_references':int((~yt).sum()),'rho_min':float(np.min(rho)),'rho_median':float(np.median(rho)),'rho_max':float(np.max(rho)),'parent_margin_min':float(np.min(foldpar)),'parent_margin_median':float(np.median(foldpar)),'parent_margin_max':float(np.max(foldpar)),'reverse_margin_min':float(np.min(foldrev)),'reverse_margin_median':float(np.median(foldrev)),'reverse_margin_max':float(np.max(foldrev)),'heldout_inside_positive_radius_count':pos_inside,'heldout_inside_nonpositive_radius_count':neg_inside})
    req(asha(parent)==MARGIN_SHA,'parent margin reproduction failed'); req(np.isfinite(rev).all() and len(evidence)==N,'reverse evidence invalid')
    ps=float(np.median(np.abs(parent))); rs=float(np.median(np.abs(rev))); req(np.isfinite(ps) and ps>0,'parent scale invalid'); req(np.isfinite(rs) and rs>0,'reverse median absolute score is zero/nonfinite: technical no-go under frozen protocol'); factor=ps/rs; scaled=rev*factor; req(np.isfinite(scaled).all() and factor>0,'unit factor invalid')
    tie=[(hr[x],x) for x in ids]; pi=q.diversity_order(parent,C,LAMBDA,DSCALE,tie); pl=[ids[i] for i in pi]; pf=fuse(hard,pl); pm=q.v1.monotone_metrics(fam,pf,truths,elig)
    for k,v in PARENT.items(): req(close(pm[k],v) if isinstance(v,float) else int(pm[k])==v,f'parent metric reproduction {k}')
    ri=q.diversity_order(scaled,C,LAMBDA,DSCALE,tie); ro=[ids[i] for i in ri]; fo=fuse(hard,ro); lm=q.v1.monotone_metrics(fam,ro,truths,elig); fm=q.v1.monotone_metrics(fam,fo,truths,elig); req(int(lm['qualified_matches'])==95 and int(fm['qualified_matches'])==95,'qualified changed')
    gates={'recovered_at_100_strictly_better_than_parent':int(fm['recovered_at_100'])>66,'recovered_at_50_not_worse_than_parent':int(fm['recovered_at_50'])>=41,'recovered_at_25_not_worse_than_parent':int(fm['recovered_at_25'])>=23,'top100_precision_not_worse_than_parent':float(fm['top100_dominant_precision'])>=PARENT['top100_dominant_precision'],'mrr_not_worse_than_parent':float(fm['mrr'])>=PARENT['mrr'],'qualified_count_identical':int(fm['qualified_matches'])==95}; passed=all(gates.values()); verdict='PASS_GMN_V31_REVERSE1NN_SLACK_V1' if passed else 'FAIL_GMN_V31_REVERSE1NN_SLACK_V1'
    ev={'scientific_role':'TARGET_EXCLUDED_GMN_OOF_REVERSE1NN_SLACK_EVIDENCE','rows':sorted(evidence,key=lambda r:r['family_id']),'fold_diagnostics':fdiag,'parent_margin_sha256':asha(parent),'raw_reverse_margin_sha256':asha(rev),'scaled_reverse_margin_sha256':asha(scaled),'parent_median_absolute_margin':ps,'reverse_median_absolute_margin':rs,'unit_factor':factor,'raw_event_rows_accessed':False,'raw_event_ids_accessed':False,'raw_hidden_label_mapping_accessed':False,'sonotaco_2013_2014_access':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'blind_exclusion':BLIND}; (a.output/'GMN_V31_REVERSE1NN_SLACK_EVIDENCE.json').write_text(json.dumps(ev,indent=2,sort_keys=True,allow_nan=False)+'\n')
    result={'verdict':verdict,'scientific_role':'TARGET_EXCLUDED_GMN_2022_2023_V31_SUCCESSOR_DEVELOPMENT_ONLY','first_valid_outcome_binding':True,'candidate_count':N,'feature_dimension':D,'feature_matrix_sha256':asha(X),'centroid_matrix_sha256':asha(C),'package_manifest_sha256':fsha(a.manifest),'parent_prelabel_sha256':m['parent_prelabel_sha256'],'parent_margin_sha256':m['parent_margin_sha256'],'recomputed_parent_margin_sha256':asha(parent),'raw_reverse_margin_sha256':asha(rev),'scaled_reverse_margin_sha256':asha(scaled),'hard_order_sha256':osha(hard),'local_diversified_order_sha256':osha(ro),'fused_order_sha256':osha(fo),'hard_control':HARD,'parent_control':PARENT,'hard_reproduced_metrics':subset(hm),'parent_reproduced_metrics':subset(pm),'reverse_local_only':subset(lm),'reverse_equal_rank_fusion':subset(fm),'pass_gates':gates,'parent_median_absolute_margin':ps,'reverse_median_absolute_margin':rs,'unit_factor':factor,'strict_whole_shower_oof':True,'fold_count':5,'parent_standardization':'fold-training mean/population-standard-deviation z-score','metric':'Euclidean L2 in standardized 23D parent representation','reverse_k':1,'radius_geometry':'label-blind training 1-NN radius over all other fold-training references','local_score':'max_positive(rho-distance) - max_nonpositive(rho-distance), positively rescaled only for inherited diversity units','diversity':{'lambda':LAMBDA,'scale':DSCALE},'fusion':'equal rank-sum with immutable P19 hard order','fold_diagnostics':fdiag,'k_search':False,'same_class_radius':False,'opposite_class_radius':False,'reverse_count_score':False,'slack_aggregation_search':False,'slack_clipping':False,'parent_margin_blend':False,'radius_multiplier_search':False,'reference_deletion':False,'reference_relabeling':False,'reference_pruning':False,'reference_multiplicative_weighting':False,'prototype_construction':False,'metric_search':False,'feature_search':False,'scaling_search':False,'class_conditional_calibration':False,'graph_propagation':False,'diversity_search':False,'fusion_search':False,'post_result_second_search':False,'raw_event_rows_accessed':False,'raw_event_ids_accessed':False,'raw_hidden_label_mapping_accessed':False,'sonotaco_2013_2014_access':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'blind_exclusion':BLIND,'sonotaco_benchmark_authorized_by_this_result':bool(passed)}; (a.output/'GMN_V31_REVERSE1NN_SLACK_V1_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    keys=('recovered_at_25','recovered_at_50','recovered_at_100','recovered_at_500','top100_dominant_precision','mrr','qualified_matches'); print(json.dumps({'verdict':verdict,'parent':PARENT,'candidate':{k:fm[k] for k in keys},'local_only':{k:lm[k] for k in keys},'gates':gates,'parent_median_absolute_margin':ps,'reverse_median_absolute_margin':rs,'unit_factor':factor,'raw_reverse_margin_sha256':asha(rev),'scaled_reverse_margin_sha256':asha(scaled)},indent=2,sort_keys=True,allow_nan=False)); return 0
if __name__=='__main__': raise SystemExit(main())
