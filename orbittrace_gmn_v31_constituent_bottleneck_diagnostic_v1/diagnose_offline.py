#!/usr/bin/env python3
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
MARGIN_SHA='f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd'
HARD={'recovered_at_25':21,'recovered_at_50':38,'recovered_at_100':59,'top100_dominant_precision':0.6884631112636006,'mrr':0.046734076055452344,'qualified_matches':95}
FUSED={'recovered_at_25':23,'recovered_at_50':41,'recovered_at_100':66,'top100_dominant_precision':0.7229521515453452,'mrr':0.050244164168646674,'qualified_matches':95}

def req(x,m):
    if not x: raise RuntimeError(m)

def fsha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def asha(a:np.ndarray)->str:
    h=hashlib.sha256(); h.update(str(a.dtype).encode()); h.update(str(tuple(a.shape)).encode()); h.update(np.ascontiguousarray(a).tobytes()); return h.hexdigest()
def close(a,b): return abs(float(a)-float(b))<=1e-15

def fusion(hard,local):
    hr={x:i+1 for i,x in enumerate(hard)}; lr={x:i+1 for i,x in enumerate(local)}
    return sorted(hard,key=lambda x:(hr[x]+lr[x],hr[x],x))

def subset(m): return {k:v for k,v in m.items() if k!='first_rank_by_label'}

def first_ranks(order,truths,eligible):
    out={}
    for r,fid in enumerate(order,1):
        t=truths[fid]
        if bool(t.get('positive')):
            lab=t.get('best_label')
            if lab in eligible and lab not in out: out[lab]=r
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--manifest',type=Path,required=True); ap.add_argument('--features',type=Path,required=True); ap.add_argument('--centroids',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(fsha(a.manifest)==MANIFEST_SHA,'manifest changed'); m=json.loads(a.manifest.read_text()); X=np.load(a.features,allow_pickle=False); C=np.load(a.centroids,allow_pickle=False)
    req(m['verdict']=='PASS_GMN_V31_OFFLINE_DEVELOPMENT_PACKAGE_V1','package not PASS'); req(X.shape==(N,D) and C.shape==(N,CD),'shape changed'); req(asha(X)==X_SHA and asha(C)==C_SHA,'array hash changed'); req(m['blind_exclusion']==BLIND,'blind changed')
    for k in ('raw_event_rows_exported','raw_event_ids_exported','raw_hidden_label_mapping_exported','sonotaco_2013_2014_access','target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access'): req(m[k] is False,f'package firewall {k}')
    ids=[str(x) for x in m['family_input_order']]; hard=[str(x) for x in m['hard_order']]; rows=m['rows']; eligible=set(str(x) for x in m['eligible_labels']); req(len(eligible)==355,'eligible universe')
    truths={str(r['family_id']):r['truth'] for r in rows}; groups=[str(r['strict_group']) for r in rows]; folds=np.array([int(r['fold']) for r in rows]); y=np.array([bool(r['truth']['positive']) for r in rows])
    req(len(ids)==N and [str(r['family_id']) for r in rows]==ids and sum(y)==111,'row universe changed'); hr={f:i+1 for i,f in enumerate(hard)}
    margin=np.zeros(N)
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; tri=np.where(tr)[0]; tei=np.where(te)[0]; req({groups[i] for i in tri}.isdisjoint({groups[i] for i in tei}),f'group leak {fold}')
        mu=X[tr].mean(0); sd=X[tr].std(0,ddof=0); sc=sd.copy(); sc[sc==0]=1.; Ztr=(X[tr]-mu)/sc; Zte=(X[te]-mu)/sc; yt=y[tr]; tids=[ids[i] for i in tri]
        P=Ztr[yt]; Q=Ztr[~yt]; pids=[tids[i] for i in np.where(yt)[0]]; nids=[tids[i] for i in np.where(~yt)[0]]
        for j,gi in enumerate(tei):
            dp=np.linalg.norm(P-Zte[j],axis=1); dn=np.linalg.norm(Q-Zte[j],axis=1)
            ip=min(range(len(dp)),key=lambda i:(float(dp[i]),hr[pids[i]],pids[i])); inn=min(range(len(dn)),key=lambda i:(float(dn[i]),hr[nids[i]],nids[i]))
            margin[gi]=float(dn[inn]-dp[ip])
    req(asha(margin)==MARGIN_SHA,'parent margin failed reproduction')
    tie=[(hr[f],f) for f in ids]; li=q.diversity_order(margin,C,0.8,1.0,tie); local=[ids[i] for i in li]; fused=fusion(hard,local)
    fam=[{'family_id':f} for f in ids]; em={x:None for x in eligible}; hm=q.v1.monotone_metrics(fam,hard,truths,em); lm=q.v1.monotone_metrics(fam,local,truths,em); fm=q.v1.monotone_metrics(fam,fused,truths,em)
    for k,v in HARD.items(): req(close(hm[k],v) if isinstance(v,float) else int(hm[k])==v,f'hard metric {k}')
    for k,v in FUSED.items(): req(close(fm[k],v) if isinstance(v,float) else int(fm[k])==v,f'fused metric {k}')
    ranks={'hard':first_ranks(hard,truths,eligible),'local':first_ranks(local,truths,eligible),'fused':first_ranks(fused,truths,eligible)}
    qualified=set(ranks['fused']); req(len(qualified)==95 and qualified==set(ranks['hard'])==set(ranks['local']),'qualified label set changed')
    budgets={}
    for B in (25,50,100):
        for name,met in [('hard',hm),('local',lm),('fused',fm)]: req(sum(ranks[name][l]<=B for l in qualified)==int(met[f'recovered_at_{B}']),f'first-rank/evaluator mismatch {name}@{B}')
        cats={'BOTH':[],'HARD_ONLY':[],'LOCAL_ONLY':[],'NEITHER':[]}
        for l in qualified:
            h=ranks['hard'][l]<=B; g=ranks['local'][l]<=B
            cats['BOTH' if h and g else 'HARD_ONLY' if h else 'LOCAL_ONLY' if g else 'NEITHER'].append(l)
        missed=[l for l in qualified if ranks['fused'][l]>B]; mc={k:sorted(set(v)&set(missed)) for k,v in cats.items()}; avail=mc['BOTH']+mc['HARD_ONLY']+mc['LOCAL_ONLY']; absent=mc['NEITHER']; n=len(missed)
        diffs=[ranks['local'][l]-ranks['hard'][l] for l in missed]
        hardset={l for l in qualified if ranks['hard'][l]<=B}; localset={l for l in qualified if ranks['local'][l]<=B}; fusedset={l for l in qualified if ranks['fused'][l]<=B}
        budgets[str(B)]={
            'hard_recovered':len(hardset),'local_recovered':len(localset),'fused_recovered':len(fusedset),'fused_missed':n,
            'fused_missed_categories':{k:{'count':len(v),'fraction':(len(v)/n if n else 0.0)} for k,v in mc.items()},
            'constituent_available':{'count':len(avail),'fraction':(len(avail)/n if n else 0.0)},'constituent_absent':{'count':len(absent),'fraction':(len(absent)/n if n else 0.0)},
            'hard_to_fused_gained':len(fusedset-hardset),'hard_to_fused_lost':len(hardset-fusedset),'local_to_fused_gained':len(fusedset-localset),'local_to_fused_lost':len(localset-fusedset),
            'missed_local_better_than_hard':sum(ranks['local'][l]<ranks['hard'][l] for l in missed),'missed_local_equal_hard':sum(ranks['local'][l]==ranks['hard'][l] for l in missed),'missed_local_worse_than_hard':sum(ranks['local'][l]>ranks['hard'][l] for l in missed),
            'missed_median_local_minus_hard':float(np.median(diffs)) if diffs else 0.0,
        }
    a100=budgets['100']['constituent_available']['count']; z100=budgets['100']['constituent_absent']['count']; outcome='FUSION_DOMINANT' if a100>z100 else 'CONSTITUENT_DOMINANT' if z100>a100 else 'MIXED'
    result={'verdict':'PASS_GMN_V31_CONSTITUENT_BOTTLENECK_DIAGNOSTIC_V1','scientific_role':'GMN_TARGET_EXCLUDED_PARENT_DIAGNOSTIC_ONLY','diagnostic_outcome_top100':outcome,'candidate_count':N,'qualified_labels':95,'hard_metrics':subset(hm),'local_diversified_metrics':subset(lm),'fused_metrics':subset(fm),'budgets':budgets,'parent_margin_sha256':asha(margin),'feature_matrix_sha256':asha(X),'centroid_matrix_sha256':asha(C),'new_rank_evaluated':False,'successor_selected':False,'alternate_fusion_evaluated':False,'weight_search':False,'threshold_search':False,'feature_search':False,'metric_search':False,'k_search':False,'truth_search':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'raw_event_rows_accessed':False,'raw_event_ids_accessed':False,'raw_hidden_label_mapping_accessed':False,'blind_exclusion':BLIND}
    (a.output/'GMN_V31_CONSTITUENT_BOTTLENECK_DIAGNOSTIC_V1.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'outcome':outcome,'hard':subset(hm),'local':subset(lm),'fused':subset(fm),'budgets':budgets},indent=2,sort_keys=True,allow_nan=False))
if __name__=='__main__': main()
