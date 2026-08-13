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
def subset(m): return {k:v for k,v in m.items() if k!='first_rank_by_label'}
def fusion(hard,local):
    hr={x:i+1 for i,x in enumerate(hard)}; lr={x:i+1 for i,x in enumerate(local)}
    return sorted(hard,key=lambda x:(hr[x]+lr[x],hr[x],x))
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
    req(len(ids)==N and [str(r['family_id']) for r in rows]==ids and int(y.sum())==111,'row universe changed'); hr={f:i+1 for i,f in enumerate(hard)}
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
    # Exact family-level positive representatives for each qualified label.
    by_label={l:[] for l in qualified}
    for i,fid in enumerate(ids):
        t=truths[fid]; lab=t.get('best_label')
        if bool(t.get('positive')) and lab in by_label:
            by_label[lab].append((fid,float(margin[i])))
    req(all(len(v)>=1 for v in by_label.values()),'qualified label without positive representative')
    label_stats={}
    for lab,vals in by_label.items():
        ms=np.asarray([x[1] for x in vals],dtype=float); pos=int(np.sum(ms>0)); zero=int(np.sum(ms==0)); neg=int(np.sum(ms<0))
        cat='ALL_POSITIVE' if pos==len(ms) else 'MIXED' if pos>0 else 'ALL_NONPOSITIVE'
        label_stats[lab]={'representative_family_count':len(vals),'positive_margin_count':pos,'zero_margin_count':zero,'negative_margin_count':neg,'sign_category':cat,'max_margin':float(np.max(ms)),'min_margin':float(np.min(ms)),'median_margin':float(np.median(ms)),'hard_first_rank':ranks['hard'][lab],'local_first_rank':ranks['local'][lab],'fused_first_rank':ranks['fused'][lab]}
    budgets={}
    for B in (25,50,100):
        missed=sorted(l for l in qualified if ranks['fused'][l]>B); n=len(missed); cats={c:[l for l in missed if label_stats[l]['sign_category']==c] for c in ('ALL_POSITIVE','MIXED','ALL_NONPOSITIVE')}; anyp=cats['ALL_POSITIVE']+cats['MIXED']; nop=cats['ALL_NONPOSITIVE']; maxm=np.asarray([label_stats[l]['max_margin'] for l in missed],dtype=float)
        local_in=[l for l in missed if ranks['local'][l]<=B]; local_out=[l for l in missed if ranks['local'][l]>B]
        xt={'local_inside_any_positive':sum(label_stats[l]['sign_category']!='ALL_NONPOSITIVE' for l in local_in),'local_inside_no_positive':sum(label_stats[l]['sign_category']=='ALL_NONPOSITIVE' for l in local_in),'local_outside_any_positive':sum(label_stats[l]['sign_category']!='ALL_NONPOSITIVE' for l in local_out),'local_outside_no_positive':sum(label_stats[l]['sign_category']=='ALL_NONPOSITIVE' for l in local_out)}
        rec={'fused_missed':n,'sign_categories':{c:{'count':len(v),'fraction':len(v)/n if n else 0.0} for c,v in cats.items()},'any_positive_support':{'count':len(anyp),'fraction':len(anyp)/n if n else 0.0},'no_positive_support':{'count':len(nop),'fraction':len(nop)/n if n else 0.0},'max_margin_median':float(np.median(maxm)) if n else 0.0,'max_margin_q25':float(np.quantile(maxm,0.25)) if n else 0.0,'max_margin_q75':float(np.quantile(maxm,0.75)) if n else 0.0,'local_inside_budget':len(local_in),'local_outside_budget':len(local_out),'local_budget_x_sign_support':xt}
        if B==100:
            avail=[l for l in missed if ranks['hard'][l]<=100 or ranks['local'][l]<=100]; absent=[l for l in missed if ranks['hard'][l]>100 and ranks['local'][l]>100]; req(len(missed)==29 and len(avail)==8 and len(absent)==21,'prior constituent diagnostic did not reproduce')
            a_any=[l for l in absent if label_stats[l]['sign_category']!='ALL_NONPOSITIVE']; a_no=[l for l in absent if label_stats[l]['sign_category']=='ALL_NONPOSITIVE']
            rec['constituent_available_count']=len(avail); rec['constituent_absent_count']=len(absent); rec['constituent_absent_sign_categories']={c:sum(label_stats[l]['sign_category']==c for l in absent) for c in ('ALL_POSITIVE','MIXED','ALL_NONPOSITIVE')}; rec['constituent_absent_any_positive_support']={'count':len(a_any),'fraction':len(a_any)/len(absent)}; rec['constituent_absent_no_positive_support']={'count':len(a_no),'fraction':len(a_no)/len(absent)}
        budgets[str(B)]=rec
    aa=budgets['100']['constituent_absent_any_positive_support']['count']; nn=budgets['100']['constituent_absent_no_positive_support']['count']; outcome='SIGN_SUPPORT_DOMINANT' if aa>nn else 'SIGN_REJECTION_DOMINANT' if nn>aa else 'MIXED_SIGN_BOTTLENECK'
    result={'verdict':'PASS_GMN_V31_MARGIN_SIGN_BOTTLENECK_DIAGNOSTIC_V1','scientific_role':'GMN_TARGET_EXCLUDED_PARENT_DIAGNOSTIC_ONLY','diagnostic_outcome_top100_constituent_absent':outcome,'candidate_count':N,'qualified_labels':95,'hard_metrics':subset(hm),'local_diversified_metrics':subset(lm),'fused_metrics':subset(fm),'budgets':budgets,'label_stats':{l:label_stats[l] for l in sorted(label_stats)},'parent_margin_sha256':asha(margin),'feature_matrix_sha256':asha(X),'centroid_matrix_sha256':asha(C),'new_score_created':False,'new_rank_evaluated':False,'successor_selected':False,'alternate_margin_threshold':False,'fusion_variant':False,'diversity_variant':False,'feature_search':False,'metric_search':False,'scaling_search':False,'k_search':False,'reference_change':False,'truth_search':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'raw_event_rows_accessed':False,'raw_event_ids_accessed':False,'raw_hidden_label_mapping_accessed':False,'blind_exclusion':BLIND}
    (a.output/'GMN_V31_MARGIN_SIGN_BOTTLENECK_DIAGNOSTIC_V1.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'outcome':outcome,'hard':subset(hm),'local':subset(lm),'fused':subset(fm),'budgets':budgets},indent=2,sort_keys=True,allow_nan=False))
if __name__=='__main__': main()
