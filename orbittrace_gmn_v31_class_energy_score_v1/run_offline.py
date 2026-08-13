#!/usr/bin/env python3
"""Frozen target-excluded GMN v31 successor using empirical class energy scores."""
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
def parse_args():
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
def class_dispersion_v(Z):
    Z=np.asarray(Z,dtype=float); req(Z.ndim==2 and len(Z)>=1 and np.isfinite(Z).all(),'invalid class matrix')
    diff=Z[:,None,:]-Z[None,:,:]; d=np.linalg.norm(diff,axis=2); out=float(np.mean(d)); req(np.isfinite(out) and out>=0,'invalid class dispersion'); return out
def energy_score(Z,z,disp):
    Z=np.asarray(Z,dtype=float); z=np.asarray(z,dtype=float); d=np.linalg.norm(Z-z[None,:],axis=1); req(np.isfinite(d).all(),'invalid query-class distances'); out=float(np.mean(d)-0.5*disp); req(np.isfinite(out),'invalid energy score'); return out

def self_test():
    P=np.asarray([[0.],[2.]],dtype=float); Nn=np.asarray([[4.],[6.]],dtype=float); z=np.asarray([1.],dtype=float)
    dp=class_dispersion_v(P); dn=class_dispersion_v(Nn); ep=energy_score(P,z,dp); en=energy_score(Nn,z,dn); margin=en-ep
    req(dp==1.0 and dn==1.0,f'dispersion self-test failed {dp} {dn}')
    req(ep==0.5 and en==3.5 and margin==3.0,f'energy self-test failed {ep} {en} {margin}')
    # Translation invariance in Euclidean geometry.
    shift=np.asarray([10.]); ep2=energy_score(P+shift,z+shift,class_dispersion_v(P+shift)); en2=energy_score(Nn+shift,z+shift,class_dispersion_v(Nn+shift)); req(ep2==ep and en2==en,'translation invariance self-test failed')
    print(json.dumps({'verdict':'PASS_CLASS_ENERGY_SCORE_ENGINEERING_SELF_TESTS','positive_dispersion':dp,'nonpositive_dispersion':dn,'positive_energy_score':ep,'nonpositive_energy_score':en,'energy_margin':margin,'distance_exponent':1,'v_statistic':True,'search':False},indent=2,sort_keys=True)); return 0

def main():
    a=parse_args()
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
    parent=np.zeros(N); energy=np.zeros(N); evidence=[]; fdiag=[]
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; tri=np.where(tr)[0]; tei=np.where(te)[0]; req({groups[i] for i in tri}.isdisjoint({groups[i] for i in tei}),f'group leak {fold}')
        mu=X[tr].mean(0); sd=X[tr].std(0,ddof=0); sc=sd.copy(); sc[sc==0]=1.; Ztr=(X[tr]-mu)/sc; Zte=(X[te]-mu)/sc; yt=y[tr]; req(yt.any() and (~yt).any(),'class missing')
        P=Ztr[yt]; Nn=Ztr[~yt]; dP=class_dispersion_v(P); dN=class_dispersion_v(Nn); foldpar=[]; foldenergy=[]; pos=zero=neg=0
        for j,gi in enumerate(tei):
            z=Zte[j]; dp=np.linalg.norm(P-z,axis=1); dn=np.linalg.norm(Nn-z,axis=1); mp=float(np.min(dn)-np.min(dp)); parent[gi]=mp; foldpar.append(mp)
            ep=energy_score(P,z,dP); en=energy_score(Nn,z,dN); me=en-ep; energy[gi]=me; foldenergy.append(me); pos+=int(me>0); zero+=int(me==0); neg+=int(me<0)
            evidence.append({'family_id':ids[gi],'fold':fold,'parent_margin':mp,'positive_energy_score':ep,'nonpositive_energy_score':en,'raw_energy_margin':me})
        fdiag.append({'fold':fold,'train_examples':int(tr.sum()),'test_examples':int(te.sum()),'positive_references':int(yt.sum()),'nonpositive_references':int((~yt).sum()),'positive_class_dispersion_v':dP,'nonpositive_class_dispersion_v':dN,'parent_margin_min':float(np.min(foldpar)),'parent_margin_median':float(np.median(foldpar)),'parent_margin_max':float(np.max(foldpar)),'energy_margin_min':float(np.min(foldenergy)),'energy_margin_median':float(np.median(foldenergy)),'energy_margin_max':float(np.max(foldenergy)),'heldout_positive_energy_margin_count':pos,'heldout_zero_energy_margin_count':zero,'heldout_negative_energy_margin_count':neg})
    req(asha(parent)==MARGIN_SHA,'parent margin reproduction failed'); req(np.isfinite(energy).all() and len(evidence)==N,'energy evidence invalid')
    ps=float(np.median(np.abs(parent))); es=float(np.median(np.abs(energy))); req(np.isfinite(ps) and ps>0,'parent scale invalid'); req(np.isfinite(es) and es>0,'energy median absolute score zero/nonfinite: technical no-go'); factor=ps/es; scaled=energy*factor; req(np.isfinite(scaled).all() and factor>0,'unit factor invalid')
    hr={x:i+1 for i,x in enumerate(hard)}; tie=[(hr[x],x) for x in ids]; pi=q.diversity_order(parent,C,LAMBDA,DSCALE,tie); pl=[ids[i] for i in pi]; pf=fuse(hard,pl); pm=q.v1.monotone_metrics(fam,pf,truths,elig)
    for k,v in PARENT.items(): req(close(pm[k],v) if isinstance(v,float) else int(pm[k])==v,f'parent metric reproduction {k}')
    ei=q.diversity_order(scaled,C,LAMBDA,DSCALE,tie); eo=[ids[i] for i in ei]; fo=fuse(hard,eo); lm=q.v1.monotone_metrics(fam,eo,truths,elig); fm=q.v1.monotone_metrics(fam,fo,truths,elig); req(int(lm['qualified_matches'])==95 and int(fm['qualified_matches'])==95,'qualified changed')
    gates={'recovered_at_100_strictly_better_than_parent':int(fm['recovered_at_100'])>66,'recovered_at_50_not_worse_than_parent':int(fm['recovered_at_50'])>=41,'recovered_at_25_not_worse_than_parent':int(fm['recovered_at_25'])>=23,'top100_precision_not_worse_than_parent':float(fm['top100_dominant_precision'])>=PARENT['top100_dominant_precision'],'mrr_not_worse_than_parent':float(fm['mrr'])>=PARENT['mrr'],'qualified_count_identical':int(fm['qualified_matches'])==95}; passed=all(gates.values()); verdict='PASS_GMN_V31_CLASS_ENERGY_SCORE_V1' if passed else 'FAIL_GMN_V31_CLASS_ENERGY_SCORE_V1'
    ev={'scientific_role':'TARGET_EXCLUDED_GMN_OOF_EMPIRICAL_CLASS_ENERGY_SCORE_EVIDENCE','rows':sorted(evidence,key=lambda r:r['family_id']),'fold_diagnostics':fdiag,'parent_margin_sha256':asha(parent),'raw_energy_margin_sha256':asha(energy),'scaled_energy_margin_sha256':asha(scaled),'parent_median_absolute_margin':ps,'energy_median_absolute_margin':es,'unit_factor':factor,'raw_event_rows_accessed':False,'raw_event_ids_accessed':False,'raw_hidden_label_mapping_accessed':False,'sonotaco_2013_2014_access':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'blind_exclusion':BLIND}; (a.output/'GMN_V31_CLASS_ENERGY_SCORE_EVIDENCE.json').write_text(json.dumps(ev,indent=2,sort_keys=True,allow_nan=False)+'\n')
    result={'verdict':verdict,'scientific_role':'TARGET_EXCLUDED_GMN_2022_2023_V31_SUCCESSOR_DEVELOPMENT_ONLY','first_valid_outcome_binding':True,'candidate_count':N,'feature_dimension':D,'feature_matrix_sha256':asha(X),'centroid_matrix_sha256':asha(C),'package_manifest_sha256':fsha(a.manifest),'parent_prelabel_sha256':m['parent_prelabel_sha256'],'parent_margin_sha256':m['parent_margin_sha256'],'recomputed_parent_margin_sha256':asha(parent),'raw_energy_margin_sha256':asha(energy),'scaled_energy_margin_sha256':asha(scaled),'hard_order_sha256':osha(hard),'local_diversified_order_sha256':osha(eo),'fused_order_sha256':osha(fo),'hard_control':HARD,'parent_control':PARENT,'hard_reproduced_metrics':subset(hm),'parent_reproduced_metrics':subset(pm),'energy_local_only':subset(lm),'energy_equal_rank_fusion':subset(fm),'pass_gates':gates,'parent_median_absolute_margin':ps,'energy_median_absolute_margin':es,'unit_factor':factor,'strict_whole_shower_oof':True,'fold_count':5,'parent_standardization':'fold-training mean/population-standard-deviation z-score','metric':'Euclidean L2 in standardized 23D parent representation','energy_distance_exponent':1,'empirical_pair_statistic':'V-statistic including all ordered pairs and diagonals','local_score':'ES_nonpositive(query) - ES_positive(query), positively rescaled only for inherited diversity units','diversity':{'lambda':LAMBDA,'scale':DSCALE},'fusion':'equal rank-sum with immutable P19 hard order','fold_diagnostics':fdiag,'distance_exponent_search':False,'squared_distance_variant':False,'u_statistic':False,'bias_correction':False,'class_prior':False,'class_size_weighting':False,'kernel_mmd':False,'bandwidth_search':False,'wasserstein_ot':False,'threshold_search':False,'parent_margin_blend':False,'nearest_energy_blend':False,'class_subset_or_mixture':False,'reference_weighting':False,'reference_deletion':False,'reference_relabeling':False,'feature_search':False,'metric_search':False,'scaling_search':False,'covariance_fit':False,'diversity_search':False,'fusion_search':False,'post_result_second_search':False,'raw_event_rows_accessed':False,'raw_event_ids_accessed':False,'raw_hidden_label_mapping_accessed':False,'sonotaco_2013_2014_access':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'blind_exclusion':BLIND,'sonotaco_benchmark_authorized_by_this_result':bool(passed)}; (a.output/'GMN_V31_CLASS_ENERGY_SCORE_V1_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    keys=('recovered_at_25','recovered_at_50','recovered_at_100','recovered_at_500','top100_dominant_precision','mrr','qualified_matches'); print(json.dumps({'verdict':verdict,'parent':PARENT,'candidate':{k:fm[k] for k in keys},'local_only':{k:lm[k] for k in keys},'gates':gates,'parent_median_absolute_margin':ps,'energy_median_absolute_margin':es,'unit_factor':factor,'raw_energy_margin_sha256':asha(energy),'scaled_energy_margin_sha256':asha(scaled)},indent=2,sort_keys=True,allow_nan=False)); return 0
if __name__=='__main__': raise SystemExit(main())
