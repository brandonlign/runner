#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter
from pathlib import Path
import numpy as np
import run_urc_union_ranker as q

N=226; D=23; CD=8; BLIND=[20.0,55.0]
MANIFEST_SHA='16fb5ef3cd8dbbb3873e9bc23874fe7da3db68498772a5e992fbceed6cb980d7'
X_SHA='fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5'
C_SHA='a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f'
MARGIN_SHA='f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd'
HARD={'recovered_at_25':21,'recovered_at_50':38,'recovered_at_100':59,'top100_dominant_precision':0.6884631112636006,'mrr':0.046734076055452344,'qualified_matches':95}
FUSED={'recovered_at_25':23,'recovered_at_50':41,'recovered_at_100':66,'top100_dominant_precision':0.7229521515453452,'mrr':0.050244164168646674,'qualified_matches':95}

def req(x,m):
    if not x: raise RuntimeError(m)
def fsha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def asha(a):
    h=hashlib.sha256(); h.update(str(a.dtype).encode()); h.update(str(tuple(a.shape)).encode()); h.update(np.ascontiguousarray(a).tobytes()); return h.hexdigest()
def close(a,b): return abs(float(a)-float(b))<=1e-15
def subset(m): return {k:v for k,v in m.items() if k!='first_rank_by_label'}
def fuse(hard,local):
    hr={x:i+1 for i,x in enumerate(hard)}; lr={x:i+1 for i,x in enumerate(local)}
    return sorted(hard,key=lambda x:(hr[x]+lr[x],hr[x],x))
def first_ranks(order,truths,eligible):
    out={}
    for r,fid in enumerate(order,1):
        t=truths[fid]; lab=t.get('best_label')
        if bool(t.get('positive')) and lab in eligible and lab not in out: out[lab]=r
    return out
def five(vals):
    a=np.asarray(vals,dtype=float); req(a.size>0,'empty summary')
    return {'min':float(np.min(a)),'q25':float(np.quantile(a,.25)),'median':float(np.median(a)),'q75':float(np.quantile(a,.75)),'max':float(np.max(a))}
def hist(vals):
    c=Counter(int(x) for x in vals); return {str(k):int(c[k]) for k in sorted(c)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--manifest',type=Path,required=True); ap.add_argument('--features',type=Path,required=True); ap.add_argument('--centroids',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(fsha(a.manifest)==MANIFEST_SHA,'manifest changed'); m=json.loads(a.manifest.read_text()); X=np.load(a.features,allow_pickle=False); C=np.load(a.centroids,allow_pickle=False)
    req(m['verdict']=='PASS_GMN_V31_OFFLINE_DEVELOPMENT_PACKAGE_V1','package not PASS'); req(X.shape==(N,D) and C.shape==(N,CD),'shape changed'); req(asha(X)==X_SHA and asha(C)==C_SHA,'array hash changed'); req(m['blind_exclusion']==BLIND,'blind changed')
    for k in ('raw_event_rows_exported','raw_event_ids_exported','raw_hidden_label_mapping_exported','sonotaco_2013_2014_access','target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access'): req(m[k] is False,f'package firewall {k}')
    ids=[str(x) for x in m['family_input_order']]; hard=[str(x) for x in m['hard_order']]; rows=m['rows']; eligible=set(str(x) for x in m['eligible_labels']); truths={str(r['family_id']):r['truth'] for r in rows}; groups=[str(r['strict_group']) for r in rows]; folds=np.asarray([int(r['fold']) for r in rows]); y=np.asarray([bool(r['truth']['positive']) for r in rows])
    req(len(ids)==N and [str(r['family_id']) for r in rows]==ids and len(eligible)==355 and int(y.sum())==111,'universe changed'); hr={f:i+1 for i,f in enumerate(hard)}
    parent=np.zeros(N); intr=np.full(N,-1,dtype=int); pstar_rank=np.full(N,-1,dtype=int); pstar_dist=np.full(N,np.nan); nstar_dist=np.full(N,np.nan); tie=np.zeros(N,dtype=bool)
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; tri=np.where(tr)[0]; tei=np.where(te)[0]; req({groups[i] for i in tri}.isdisjoint({groups[i] for i in tei}),f'group leak {fold}')
        mu=X[tr].mean(0); sd=X[tr].std(0,ddof=0); sc=sd.copy(); sc[sc==0]=1.; Ztr=(X[tr]-mu)/sc; Zte=(X[te]-mu)/sc; yt=y[tr]; tids=[ids[i] for i in tri]
        req(yt.any() and (~yt).any(),'class missing')
        for j,gi in enumerate(tei):
            z=Zte[j]; d=np.linalg.norm(Ztr-z[None,:],axis=1); req(np.isfinite(d).all(),'distance invalid')
            pos_idx=[i for i in range(len(tids)) if yt[i]]; neg_idx=[i for i in range(len(tids)) if not yt[i]]
            pidx=min(pos_idx,key=lambda i:(float(d[i]),hr[tids[i]],tids[i])); nidx=min(neg_idx,key=lambda i:(float(d[i]),hr[tids[i]],tids[i]))
            pd=float(d[pidx]); nd=float(d[nidx]); parent[gi]=nd-pd; pstar_dist[gi]=pd; nstar_dist[gi]=nd; tie[gi]=(pd==nd)
            all_order=sorted(range(len(tids)),key=lambda i:(float(d[i]),hr[tids[i]],tids[i])); rank=all_order.index(pidx)+1; pstar_rank[gi]=rank; intr[gi]=sum(1 for i in all_order[:rank-1] if not yt[i])
            req(intr[gi]==rank-1,'positive appeared before nearest positive')
            if parent[gi]>0: req(intr[gi]==0,'positive margin but nonpositive intruder')
            if parent[gi]<0: req(intr[gi]>=1,'negative margin without nonpositive intruder')
    req(asha(parent)==MARGIN_SHA,'parent margin reproduction failed')
    # Only positive held-out families are scientifically summarized, but all rows had deterministic geometry computed.
    tie_order=[(hr[f],f) for f in ids]; li=q.diversity_order(parent,C,.8,1.0,tie_order); local=[ids[i] for i in li]; fused=fuse(hard,local); fam=[{'family_id':f} for f in ids]; em={l:None for l in eligible}; hm=q.v1.monotone_metrics(fam,hard,truths,em); lm=q.v1.monotone_metrics(fam,local,truths,em); fm=q.v1.monotone_metrics(fam,fused,truths,em)
    for k,v in HARD.items(): req(close(hm[k],v) if isinstance(v,float) else int(hm[k])==v,f'hard {k}')
    for k,v in FUSED.items(): req(close(fm[k],v) if isinstance(v,float) else int(fm[k])==v,f'fused {k}')
    ranks={'hard':first_ranks(hard,truths,eligible),'local':first_ranks(local,truths,eligible),'fused':first_ranks(fused,truths,eligible)}; qualified=set(ranks['fused']); req(len(qualified)==95 and qualified==set(ranks['hard'])==set(ranks['local']),'qualified set changed')
    by={l:[] for l in qualified}
    for i,fid in enumerate(ids):
        t=truths[fid]; lab=t.get('best_label')
        if bool(t.get('positive')) and lab in by:
            by[lab].append({'family_id':fid,'intrusion_count':int(intr[i]),'nearest_positive_all_rank':int(pstar_rank[i]),'parent_margin':float(parent[i]),'nearest_positive_distance':float(pstar_dist[i]),'nearest_nonpositive_distance':float(nstar_dist[i]),'distance_tie':bool(tie[i])})
    req(all(by[l] for l in qualified),'label without representative')
    label_stats={}
    for l,vals in by.items():
        iv=[v['intrusion_count'] for v in vals]; ms=[v['parent_margin'] for v in vals]
        label_stats[l]={'representative_count':len(vals),'min_intrusion_count':min(iv),'median_intrusion_count':float(np.median(iv)),'max_intrusion_count':max(iv),'representatives_I0':sum(x==0 for x in iv),'representatives_I1':sum(x==1 for x in iv),'representatives_I_ge2':sum(x>=2 for x in iv),'any_positive_support':any(x>0 for x in ms),'max_parent_margin':max(ms),'hard_first_rank':ranks['hard'][l],'local_first_rank':ranks['local'][l],'fused_first_rank':ranks['fused'][l]}
    missed=sorted(l for l in qualified if ranks['fused'][l]>100); req(len(missed)==29,'top100 misses not 29')
    absent=sorted(l for l in missed if ranks['hard'][l]>100 and ranks['local'][l]>100); req(len(absent)==21,'constituent absent not 21'); req(all(not label_stats[l]['any_positive_support'] for l in absent),'21 sign-rejection condition failed')
    no_support=sorted(l for l in missed if not label_stats[l]['any_positive_support']); req(len(no_support)==25,'no-positive-support count not 25')
    def summarize(labels):
        iv=[label_stats[l]['min_intrusion_count'] for l in labels]; n=len(iv); return {'label_count':n,'histogram_min_intrusion':hist(iv),'five_number_min_intrusion':five(iv),'single_intruder':{'count':sum(x==1 for x in iv),'fraction':sum(x==1 for x in iv)/n},'multiple_intruders':{'count':sum(x>=2 for x in iv),'fraction':sum(x>=2 for x in iv)/n}}
    sa=summarize(absent); sn=summarize(no_support); sm=summarize(missed); sq=summarize(sorted(qualified)); req(sa['single_intruder']['count']+sa['multiple_intruders']['count']==21,'sign-rejected absent labels must have I>=1')
    one=sa['single_intruder']['count']; multi=sa['multiple_intruders']['count']; outcome='SINGLE_INTRUDER_DOMINANT' if one>multi else 'MULTIPLE_INTRUDERS_DOMINANT' if multi>one else 'MIXED_INTRUSION_DEPTH'
    result={'verdict':'PASS_GMN_V31_NEGATIVE_INTRUSION_DEPTH_DIAGNOSTIC_V1','scientific_role':'GMN_TARGET_EXCLUDED_PARENT_DIAGNOSTIC_ONLY','diagnostic_outcome_top100_constituent_absent':outcome,'candidate_count':N,'qualified_labels':95,'hard_metrics':subset(hm),'local_diversified_metrics':subset(lm),'fused_metrics':subset(fm),'top100_fused_misses':sm,'top100_no_positive_support':sn,'top100_constituent_absent_sign_rejected':sa,'label_stats':{l:label_stats[l] for l in sorted(label_stats)},'parent_margin_sha256':asha(parent),'feature_matrix_sha256':asha(X),'centroid_matrix_sha256':asha(C),'distance_tie_positive_family_count':int(sum(bool(tie[i]) and bool(y[i]) for i in range(N))),'new_score_created':False,'new_rank_evaluated':False,'successor_selected':False,'alternate_budget':False,'threshold_search':False,'feature_search':False,'metric_search':False,'scaling_search':False,'k_search':False,'reference_change':False,'diversity_variant':False,'fusion_variant':False,'truth_search':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'raw_event_rows_accessed':False,'raw_event_ids_accessed':False,'raw_hidden_label_mapping_accessed':False,'blind_exclusion':BLIND}
    (a.output/'GMN_V31_NEGATIVE_INTRUSION_DEPTH_DIAGNOSTIC_V1.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'outcome':outcome,'top100_constituent_absent':sa,'top100_no_positive_support':sn,'top100_all_misses':sm,'qualified_all':sq},indent=2,sort_keys=True,allow_nan=False))
if __name__=='__main__': main()
