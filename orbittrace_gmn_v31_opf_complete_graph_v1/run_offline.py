#!/usr/bin/env python3
"""Frozen target-excluded GMN v31 complete-graph supervised OPF successor."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
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
def fsha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def asha(a):
    h=hashlib.sha256(); h.update(str(a.dtype).encode()); h.update(str(tuple(a.shape)).encode()); h.update(np.ascontiguousarray(a).tobytes()); return h.hexdigest()
def osha(order): return hashlib.sha256('\n'.join(order).encode()).hexdigest()
def close(a,b): return abs(float(a)-float(b))<=1e-15
def subset(m): return {k:v for k,v in m.items() if k!='first_rank_by_label'}
def fuse(hard,local):
    hr={x:i+1 for i,x in enumerate(hard)}; lr={x:i+1 for i,x in enumerate(local)}
    return sorted(hard,key=lambda x:(hr[x]+lr[x],hr[x],x))
def pairwise(Z):
    Z=np.asarray(Z,float); d=np.linalg.norm(Z[:,None,:]-Z[None,:,:],axis=2); req(np.isfinite(d).all(),'pairwise distance invalid'); return d

def prim_mst(D):
    n=len(D); req(D.shape==(n,n) and n>=2,'MST matrix invalid')
    key=np.full(n,np.inf); pred=np.full(n,-1,dtype=int); used=np.zeros(n,dtype=bool); key[0]=0.0; order=[]
    for _ in range(n):
        cand=[i for i in range(n) if not used[i]]; p=min(cand,key=lambda i:(float(key[i]),i)); req(np.isfinite(key[p]),'disconnected complete graph'); used[p]=True; order.append(p)
        for r in range(n):
            if not used[r] and r!=p:
                w=float(D[p,r])
                if w < key[r]: key[r]=w; pred[r]=p
    req(pred[0]==-1 and np.all(pred[1:]>=0),'MST predecessor invalid')
    return key,pred,order

def train_opf(D,y):
    y=np.asarray(y,dtype=bool); n=len(y); key,mst_pred,mst_order=prim_mst(D)
    proto=np.zeros(n,dtype=bool)
    for i in range(1,n):
        p=int(mst_pred[i])
        if y[i] != y[p]: proto[i]=True; proto[p]=True
    req(proto.any() and np.any(proto & y) and np.any(proto & ~y),'OPF requires both-class prototypes')
    cost=np.full(n,np.inf); fpred=np.full(n,-1,dtype=int); plabel=np.zeros(n,dtype=bool); used=np.zeros(n,dtype=bool); settle=[]
    for i in np.where(proto)[0]: cost[i]=0.0; plabel[i]=y[i]
    for _ in range(n):
        cand=[i for i in range(n) if not used[i]]; p=min(cand,key=lambda i:(float(cost[i]),i)); req(np.isfinite(cost[p]),'OPF path cost remained infinite'); used[p]=True; settle.append(p)
        for r in range(n):
            if r==p or used[r]: continue
            if cost[p] < cost[r]:
                c=max(float(cost[p]),float(D[p,r]))
                if c < cost[r]: cost[r]=c; fpred[r]=p; plabel[r]=plabel[p]
    srank=np.empty(n,dtype=int)
    for j,i in enumerate(settle): srank[i]=j
    return {'mst_key':key,'mst_pred':mst_pred,'mst_order':mst_order,'prototype':proto,'cost':cost,'forest_pred':fpred,'label':plabel,'settle':settle,'settle_rank':srank}

def test_costs(model,Ztr,z):
    d=np.linalg.norm(Ztr-z[None,:],axis=1); J=np.maximum(model['cost'],d); lab=model['label']; req(np.any(lab) and np.any(~lab),'OPF propagated classes collapsed')
    def win(mask):
        inds=np.where(mask)[0].tolist(); i=min(inds,key=lambda k:(float(J[k]),int(model['settle_rank'][k]))); return float(J[i]),i
    jp,ip=win(lab); jn,inn=win(~lab); all_i=min(range(len(J)),key=lambda k:(float(J[k]),int(model['settle_rank'][k]))); pred=bool(lab[all_i]); margin=jn-jp
    if margin>0: req(pred is True,'OPF sign/prediction mismatch positive')
    if margin<0: req(pred is False,'OPF sign/prediction mismatch negative')
    return jp,jn,margin,ip,inn,all_i,pred,bool(jp==jn)

def self_test():
    Z=np.asarray([[0.],[1.],[4.],[5.]],float); y=np.asarray([False,False,True,True]); Dm=pairwise(Z); model=train_opf(Dm,y)
    req(set(np.where(model['prototype'])[0].tolist())=={1,2},f'prototype self-test failed {np.where(model["prototype"])[0]}')
    req(np.array_equal(model['cost'],np.asarray([1.,0.,0.,1.])),f'cost self-test failed {model["cost"]}')
    req(np.array_equal(model['label'],y),f'propagated label self-test failed {model["label"]}')
    jp,jn,margin,ip,inn,all_i,pred,tie=test_costs(model,Z,np.asarray([3.]))
    req(jp==1.0 and jn==2.0 and margin==1.0 and pred is True and not tie,f'test insertion self-test failed {jp} {jn} {margin} {pred}')
    print(json.dumps({'verdict':'PASS_COMPLETE_GRAPH_OPF_ENGINEERING_SELF_TESTS','prototypes':np.where(model['prototype'])[0].tolist(),'path_costs':model['cost'].tolist(),'J_positive':jp,'J_nonpositive':jn,'margin':margin,'predicted_positive':pred,'validation_learning':False,'pruning':False,'search':False},indent=2,sort_keys=True)); return 0

def main():
    a=parse_args()
    if a.self_test: return self_test()
    req(all(x is not None for x in (a.manifest,a.features,a.centroids,a.output)),'science args required'); a.output.mkdir(parents=True,exist_ok=True)
    req(fsha(a.manifest)==MANIFEST_SHA,'manifest changed'); m=json.loads(a.manifest.read_text()); X=np.load(a.features,allow_pickle=False); C=np.load(a.centroids,allow_pickle=False)
    req(m['verdict']=='PASS_GMN_V31_OFFLINE_DEVELOPMENT_PACKAGE_V1','package not PASS'); req(m['scientific_role']=='ENGINEERING_PROVENANCE_ONLY_NO_SUCCESSOR_EVALUATED','package role changed'); req(m['development_role']=='GMN_2022_2023_TARGET_EXCLUDED_ONLY','development role changed')
    req(X.shape==(N,D) and C.shape==(N,CD) and np.isfinite(X).all() and np.isfinite(C).all(),'matrix invalid'); req(asha(X)==m['feature_matrix_sha256']==X_SHA,'X hash'); req(asha(C)==m['centroid_matrix_sha256']==C_SHA,'C hash'); req(m['parent_prelabel_sha256']==PRELABEL_SHA and m['parent_margin_sha256']==MARGIN_SHA,'parent provenance'); req(m['blind_exclusion']==BLIND,'blind changed')
    for k in ('raw_event_rows_exported','raw_event_ids_exported','raw_hidden_label_mapping_exported','new_feature_or_score_created','new_rank_evaluated','successor_selected','sonotaco_2013_2014_access','target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access'): req(m[k] is False,f'package firewall {k}')
    ids=[str(x) for x in m['family_input_order']]; hard=[str(x) for x in m['hard_order']]; rows=m['rows']; eligible_labels=[str(x) for x in m['eligible_labels']]; req(len(ids)==N and len(set(ids))==N and [str(r['family_id']) for r in rows]==ids,'family universe'); req(len(eligible_labels)==355,'eligible labels')
    truths={str(r['family_id']):r['truth'] for r in rows}; groups=[str(r['strict_group']) for r in rows]; folds=np.asarray([int(r['fold']) for r in rows]); y=np.asarray([bool(r['truth']['positive']) for r in rows]); req(set(folds.tolist())==set(range(5)) and int(y.sum())==111 and int((~y).sum())==115,'fold/truth counts')
    fam=[{'family_id':x} for x in ids]; elig={x:None for x in eligible_labels}; hm=q.v1.monotone_metrics(fam,hard,truths,elig)
    for k,v in HARD.items(): req(close(hm[k],v) if isinstance(v,float) else int(hm[k])==v,f'hard {k}'); req(close(m['parent_baseline_metrics'][k],v) if isinstance(v,float) else int(m['parent_baseline_metrics'][k])==v,f'package hard {k}')
    for k,v in PARENT.items(): req(close(m['parent_fused_metrics'][k],v) if isinstance(v,float) else int(m['parent_fused_metrics'][k])==v,f'package parent {k}')
    parent=np.zeros(N); opf=np.zeros(N); evidence=[]; fdiag=[]
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; tri=np.where(tr)[0]; tei=np.where(te)[0]; req({groups[i] for i in tri}.isdisjoint({groups[i] for i in tei}),f'group leak {fold}')
        mu=X[tr].mean(0); sd=X[tr].std(0,ddof=0); sc=sd.copy(); sc[sc==0]=1.; Ztr=(X[tr]-mu)/sc; Zte=(X[te]-mu)/sc; yt=y[tr]; tids=[ids[i] for i in tri]; Dtr=pairwise(Ztr); model=train_opf(Dtr,yt)
        prot=np.where(model['prototype'])[0]; train_disagree=int(np.sum(model['label']!=yt)); ties=0; fmarg=[]; pmarg=[]
        for j,gi in enumerate(tei):
            z=Zte[j]; dp=np.linalg.norm(Ztr[yt]-z,axis=1); dn=np.linalg.norm(Ztr[~yt]-z,axis=1); mp=float(np.min(dn)-np.min(dp)); parent[gi]=mp; pmarg.append(mp)
            jp,jn,mo,ip,inn,iw,pred,ctie=test_costs(model,Ztr,z); opf[gi]=mo; fmarg.append(mo); ties+=int(ctie)
            evidence.append({'family_id':ids[gi],'fold':fold,'parent_margin':mp,'J_positive':jp,'J_nonpositive':jn,'raw_opf_margin':mo,'winning_positive_node':tids[ip],'winning_nonpositive_node':tids[inn],'canonical_winning_node':tids[iw],'canonical_predicted_positive':pred,'class_cost_tie':ctie})
        mst_edges=[]
        for i,p in enumerate(model['mst_pred']):
            if p>=0: mst_edges.append((min(tids[i],tids[p]),max(tids[i],tids[p]),float(Dtr[i,p])))
        mst_text='\n'.join(f'{a}|{b}|{w:.17g}' for a,b,w in sorted(mst_edges)); mst_sha=hashlib.sha256(mst_text.encode()).hexdigest()
        fdiag.append({'fold':fold,'train_examples':int(tr.sum()),'test_examples':int(te.sum()),'prototype_count':int(len(prot)),'positive_prototype_count':int(np.sum(yt[prot])),'nonpositive_prototype_count':int(np.sum(~yt[prot])),'mst_total_weight':float(np.sum(model['mst_key'])),'mst_edge_sha256':mst_sha,'path_cost_min':float(np.min(model['cost'])),'path_cost_median':float(np.median(model['cost'])),'path_cost_max':float(np.max(model['cost'])),'propagated_positive_count':int(np.sum(model['label'])),'propagated_nonpositive_count':int(np.sum(~model['label'])),'training_propagated_label_disagreement_count':train_disagree,'heldout_class_cost_tie_count':ties,'parent_margin_min':float(np.min(pmarg)),'parent_margin_median':float(np.median(pmarg)),'parent_margin_max':float(np.max(pmarg)),'opf_margin_min':float(np.min(fmarg)),'opf_margin_median':float(np.median(fmarg)),'opf_margin_max':float(np.max(fmarg))})
    req(asha(parent)==MARGIN_SHA,'parent margin reproduction failed'); req(np.isfinite(opf).all() and len(evidence)==N,'OPF evidence invalid')
    ps=float(np.median(np.abs(parent))); os=float(np.median(np.abs(opf))); req(np.isfinite(ps) and ps>0,'parent scale invalid'); req(np.isfinite(os) and os>0,'OPF median absolute score zero/nonfinite: technical no-go'); factor=ps/os; scaled=opf*factor; req(np.isfinite(scaled).all() and factor>0,'unit factor invalid')
    hr={x:i+1 for i,x in enumerate(hard)}; tie=[(hr[x],x) for x in ids]; pi=q.diversity_order(parent,C,LAMBDA,DSCALE,tie); pl=[ids[i] for i in pi]; pf=fuse(hard,pl); pm=q.v1.monotone_metrics(fam,pf,truths,elig)
    for k,v in PARENT.items(): req(close(pm[k],v) if isinstance(v,float) else int(pm[k])==v,f'parent metric {k}')
    oi=q.diversity_order(scaled,C,LAMBDA,DSCALE,tie); oo=[ids[i] for i in oi]; fo=fuse(hard,oo); lm=q.v1.monotone_metrics(fam,oo,truths,elig); fm=q.v1.monotone_metrics(fam,fo,truths,elig); req(int(lm['qualified_matches'])==95 and int(fm['qualified_matches'])==95,'qualified changed')
    gates={'recovered_at_100_strictly_better_than_parent':int(fm['recovered_at_100'])>66,'recovered_at_50_not_worse_than_parent':int(fm['recovered_at_50'])>=41,'recovered_at_25_not_worse_than_parent':int(fm['recovered_at_25'])>=23,'top100_precision_not_worse_than_parent':float(fm['top100_dominant_precision'])>=PARENT['top100_dominant_precision'],'mrr_not_worse_than_parent':float(fm['mrr'])>=PARENT['mrr'],'qualified_count_identical':int(fm['qualified_matches'])==95}; passed=all(gates.values()); verdict='PASS_GMN_V31_COMPLETE_GRAPH_OPF_V1' if passed else 'FAIL_GMN_V31_COMPLETE_GRAPH_OPF_V1'
    ev={'scientific_role':'TARGET_EXCLUDED_GMN_OOF_COMPLETE_GRAPH_OPF_EVIDENCE','rows':sorted(evidence,key=lambda r:r['family_id']),'fold_diagnostics':fdiag,'parent_margin_sha256':asha(parent),'raw_opf_margin_sha256':asha(opf),'scaled_opf_margin_sha256':asha(scaled),'parent_median_absolute_margin':ps,'opf_median_absolute_margin':os,'unit_factor':factor,'raw_event_rows_accessed':False,'raw_event_ids_accessed':False,'raw_hidden_label_mapping_accessed':False,'sonotaco_2013_2014_access':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'blind_exclusion':BLIND}; (a.output/'GMN_V31_COMPLETE_GRAPH_OPF_EVIDENCE.json').write_text(json.dumps(ev,indent=2,sort_keys=True,allow_nan=False)+'\n')
    result={'verdict':verdict,'scientific_role':'TARGET_EXCLUDED_GMN_2022_2023_V31_SUCCESSOR_DEVELOPMENT_ONLY','first_valid_outcome_binding':True,'candidate_count':N,'feature_dimension':D,'feature_matrix_sha256':asha(X),'centroid_matrix_sha256':asha(C),'package_manifest_sha256':fsha(a.manifest),'parent_prelabel_sha256':m['parent_prelabel_sha256'],'parent_margin_sha256':m['parent_margin_sha256'],'recomputed_parent_margin_sha256':asha(parent),'raw_opf_margin_sha256':asha(opf),'scaled_opf_margin_sha256':asha(scaled),'hard_order_sha256':osha(hard),'local_diversified_order_sha256':osha(oo),'fused_order_sha256':osha(fo),'hard_control':HARD,'parent_control':PARENT,'hard_reproduced_metrics':subset(hm),'parent_reproduced_metrics':subset(pm),'opf_local_only':subset(lm),'opf_equal_rank_fusion':subset(fm),'pass_gates':gates,'parent_median_absolute_margin':ps,'opf_median_absolute_margin':os,'unit_factor':factor,'strict_whole_shower_oof':True,'fold_count':5,'parent_standardization':'fold-training mean/population-standard-deviation z-score','metric':'Euclidean L2 in standardized 23D parent representation','opf_graph':'complete','opf_prototype_rule':'both endpoints of deterministic Prim-MST cross-class edges','opf_path_cost':'minimax fmax','local_score':'best nonpositive OPF insertion cost - best positive OPF insertion cost','diversity':{'lambda':LAMBDA,'scale':DSCALE},'fusion':'equal rank-sum with immutable P19 hard order','fold_diagnostics':fdiag,'validation_learning':False,'pruning':False,'knn_sparse_graph':False,'alternative_path_cost':False,'prototype_search':False,'class_weighting':False,'metric_search':False,'feature_search':False,'scaling_search':False,'score_calibration':False,'threshold_search':False,'parent_opf_blend':False,'graph_density_augmentation':False,'diversity_search':False,'fusion_search':False,'post_result_second_search':False,'raw_event_rows_accessed':False,'raw_event_ids_accessed':False,'raw_hidden_label_mapping_accessed':False,'sonotaco_2013_2014_access':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'blind_exclusion':BLIND,'sonotaco_benchmark_authorized_by_this_result':bool(passed)}; (a.output/'GMN_V31_COMPLETE_GRAPH_OPF_V1_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    keys=('recovered_at_25','recovered_at_50','recovered_at_100','recovered_at_500','top100_dominant_precision','mrr','qualified_matches'); print(json.dumps({'verdict':verdict,'parent':PARENT,'candidate':{k:fm[k] for k in keys},'local_only':{k:lm[k] for k in keys},'gates':gates,'parent_median_absolute_margin':ps,'opf_median_absolute_margin':os,'unit_factor':factor,'raw_opf_margin_sha256':asha(opf),'scaled_opf_margin_sha256':asha(scaled),'fold_diagnostics':fdiag},indent=2,sort_keys=True,allow_nan=False)); return 0
if __name__=='__main__': raise SystemExit(main())
