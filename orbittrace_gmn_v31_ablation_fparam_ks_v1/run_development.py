#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, re
from pathlib import Path
import numpy as np
import pandas as pd

BLIND=(20.0,55.0); YEARS=(2022,2023); N=226; D=23
P19_PRELABEL_SHA='276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8'
V8_SHA='fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'
MANIFEST_SHA='16fb5ef3cd8dbbb3873e9bc23874fe7da3db68498772a5e992fbceed6cb980d7'
X_SHA='fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5'
C_SHA='a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f'
MARGIN_SHA='f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd'
RANKER_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
HARD={'recovered_at_25':21,'recovered_at_50':38,'recovered_at_100':59,'top100_dominant_precision':0.6884631112636006,'mrr':0.046734076055452344,'qualified_matches':95}
PARENT={'recovered_at_25':23,'recovered_at_50':41,'recovered_at_100':66,'top100_dominant_precision':0.7229521515453452,'mrr':0.050244164168646674,'qualified_matches':95}

def req(x,m):
    if not x: raise RuntimeError(m)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def arrsha(a):
    a=np.ascontiguousarray(a); h=hashlib.sha256(); h.update(str(a.dtype).encode()); h.update(str(tuple(a.shape)).encode()); h.update(a.tobytes()); return h.hexdigest()
def ordersha(x): return hashlib.sha256('\n'.join(x).encode()).hexdigest()
def close(a,b): return abs(float(a)-float(b))<=1e-15
def load(path,name):
    s=importlib.util.spec_from_file_location(name,path); req(s and s.loader,f'cannot load {path}'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def ks2(a,b):
    a=np.sort(np.asarray(a,float)); b=np.sort(np.asarray(b,float)); req(len(a)>0 and len(b)>0,'empty KS sample'); z=np.unique(np.concatenate([a,b])); fa=np.searchsorted(a,z,side='right')/len(a); fb=np.searchsorted(b,z,side='right')/len(b); d=float(np.max(np.abs(fa-fb))); req(math.isfinite(d) and 0<=d<=1,'invalid KS'); return d
def equal_fuse(hard,local):
    hr={x:i+1 for i,x in enumerate(hard)}; lr={x:i+1 for i,x in enumerate(local)}; return sorted(hard,key=lambda x:(hr[x]+lr[x],hr[x],x))
def trim(m): return {k:v for k,v in m.items() if k!='first_rank_by_label'}
def assert_metrics(m,e,label):
    for k,v in e.items(): req(close(m[k],v) if isinstance(v,float) else int(m[k])==v,f'{label} {k}: {m[k]} != {v}')
def oof_margin(X,folds,y,ids,hard_rank):
    out=np.zeros(len(ids),float)
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; mu=X[tr].mean(0); sd=X[tr].std(0,ddof=0); sc=sd.copy(); sc[sc==0]=1.; ztr=(X[tr]-mu)/sc; zte=(X[te]-mu)/sc; yt=y[tr]; tids=[ids[i] for i in np.where(tr)[0]]; P=ztr[yt]; Q=ztr[~yt]; pids=[tids[i] for i in np.where(yt)[0]]; nids=[tids[i] for i in np.where(~yt)[0]]
        for j,gi in enumerate(np.where(te)[0]):
            dp=np.linalg.norm(P-zte[j],axis=1); dn=np.linalg.norm(Q-zte[j],axis=1); ip=min(range(len(dp)),key=lambda i:(float(dp[i]),hard_rank[pids[i]],pids[i])); inn=min(range(len(dn)),key=lambda i:(float(dn[i]),hard_rank[nids[i]],nids[i])); out[gi]=float(dn[inn]-dp[ip])
    req(np.isfinite(out).all(),'nonfinite OOF margin'); return out
def normcol(x): return re.sub(r'[^a-z0-9]','',str(x).lower())

def main():
    p=argparse.ArgumentParser()
    for n in ('ranker_source','support_source_parts','candidate_payload','baseline_payload','scorer_parts','v8_result_json','p19_prelabel_json','offline_manifest','offline_x','offline_centroids','output'): p.add_argument('--'+n.replace('_','-'),dest=n,type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.ranker_source)==RANKER_SHA,'ranker changed'); req(sha(a.v8_result_json)==V8_SHA,'v8 changed'); req(sha(a.p19_prelabel_json)==P19_PRELABEL_SHA,'P19 changed'); req(sha(a.offline_manifest)==MANIFEST_SHA,'offline manifest changed')
    q=load(a.ranker_source,'frozen_ranker'); q.v1.mult.YEARS=YEARS; q.v1.mult.MONTH_KEYS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13)); q.v1.mult.TOP_K=100
    runtime=q.v1.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts); support.YEARS=YEARS; support.MONTH_KEYS=q.v1.mult.MONTH_KEYS; support.CORPUS='orbittrace-gmn-v31-fparam-ks-v1'; support.RANKING_VARIANTS=('persistence',); req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'firewall changed'); setattr(a,'fixed4_baseline_json',a.v8_result_json); _c,base,_s=support.load_sources(a); scan,_cal,labels,_sources=support.parse_catalogue(base); req(sorted(scan)==list(YEARS),'years changed')
    p19=json.loads(a.p19_prelabel_json.read_text()); hard=p19['hard_families']; hard_order=[str(x) for x in p19['hard_order']]; req(len(hard)==N and len(hard_order)==N,'hard universe changed'); ids=[str(f['family_id']) for f in hard]; man=json.loads(a.offline_manifest.read_text()); req(ids==list(map(str,man['family_input_order'])),'offline/raw family order mismatch'); by={str(f['family_id']):f for f in hard}; hard_rank={fid:i+1 for i,fid in enumerate(hard_order)}
    eligible=q.v1.eligible_labels(labels); truths={fid:q.v1.family_truth(by[fid],labels,eligible) for fid in ids}; lookup=q.v2.event_lookup(scan); cm=q.centroid_matrix(hard); req(arrsha(cm)==C_SHA,'centroid hash mismatch'); nf=q.neighbor_features(cm)
    rows=[]
    for i,f in enumerate(hard):
        s=q.v1.structural_features(f,hard_rank); req(len(s)==14,'structural schema changed'); rows.append(s[1:11]+q.v2.cohesion_features(f,lookup,support,base)+nf[i].tolist())
    X=np.asarray(rows,float); req(X.shape==(N,D) and np.isfinite(X).all(),'23D reconstruction invalid'); req(arrsha(X)==X_SHA,'23D hash mismatch'); Xoff=np.load(a.offline_x,allow_pickle=False); Coff=np.load(a.offline_centroids,allow_pickle=False); req(np.array_equal(X,Xoff) and np.array_equal(cm,Coff),'offline/raw arrays differ')
    folds=np.asarray([int(r['fold']) for r in man['rows']],int); y=np.asarray([bool(r['truth']['positive']) for r in man['rows']],bool); req(set(folds.tolist())==set(range(5)) and int(y.sum())==111,'fold/truth changed'); raw_groups=[('SHOWER/'+str(truths[fid]['best_label'])) if truths[fid]['best_label'] is not None else ('NEG/'+fid) for fid in ids]; req(raw_groups==[str(r['strict_group']) for r in man['rows']],'strict groups changed')
    parent=oof_margin(X,folds,y,ids,hard_rank); req(arrsha(parent)==MARGIN_SHA,'parent margin hash mismatch')

    # Source pass for the sole additional field. The protected sol mask is established before any f-param value is retained.
    allowed_ids=set(lookup)
    member_ids={str(eid) for f in hard for eid in f['event_ids']}
    req(member_ids.issubset(allowed_ids),'frozen family member absent from blind-allowed lookup')
    fmap={}; seen=set(); resolved_cols=set()
    for key in support.MONTH_KEYS:
        text=support.dd.get_monthly_file_content_by_date(key); frame=support.read_gmn_frame(text); cols=support.column_map(frame); candidates=[c for c in frame.columns if normcol(c)=='fparam']; req(len(candidates)==1,f'fparam column resolution failed {key}: {candidates}'); fcol=candidates[0]; resolved_cols.add(str(fcol))
        sol=pd.to_numeric(frame[cols['sol']],errors='coerce'); ids_raw=frame[cols['id']].astype(str); valid=np.isfinite(sol); valid &= sol.between(0.0,360.0); valid &= ~sol.between(BLIND[0],BLIND[1],inclusive='both')
        for idx in frame.index[valid]:
            eid=str(ids_raw.loc[idx])
            if eid in seen: continue
            seen.add(eid)
            if eid not in allowed_ids or eid not in member_ids: continue
            v=pd.to_numeric(pd.Series([frame.loc[idx,fcol]]),errors='coerce').iloc[0]
            if pd.isna(v): continue
            fv=float(v); req(math.isfinite(fv) and 0.0<=fv<=1.0,f'out-of-range fparam for frozen family member {eid}: {fv}'); fmap[eid]=fv
    req(len(resolved_cols)==1,'fparam column name changed across months')

    ksvals=[]; counts=[]
    for f in hard:
        annual=[]; cc=[]
        for year in YEARS:
            vals=[fmap[eid] for eid in map(str,f['event_ids']) if int(str(eid)[:4])==year and eid in fmap]; req(vals,f'no finite fparam {f["family_id"]} {year}'); annual.append(vals); cc.append(len(vals))
        ksvals.append(ks2(annual[0],annual[1])); counts.append(cc)
    ks=np.asarray(ksvals,float); req(ks.shape==(N,) and np.isfinite(ks).all(),'F-KS invalid'); X24=np.column_stack([X,ks]); cand=oof_margin(X24,folds,y,ids,hard_rank)
    tie=[(hard_rank[fid],fid) for fid in ids]; pidx=q.diversity_order(parent,cm,.8,1.0,tie); p_local=[ids[i] for i in pidx]; p_fused=equal_fuse(hard_order,p_local); fam=[{'family_id':fid} for fid in ids]; parent_metrics=q.v1.monotone_metrics(fam,p_fused,truths,eligible); hard_metrics=q.v1.monotone_metrics(fam,hard_order,truths,eligible); assert_metrics(parent_metrics,PARENT,'parent'); assert_metrics(hard_metrics,HARD,'hard')
    cidx=q.diversity_order(cand,cm,.8,1.0,tie); c_local=[ids[i] for i in cidx]; c_fused=equal_fuse(hard_order,c_local); local_metrics=q.v1.monotone_metrics(fam,c_local,truths,eligible); metrics=q.v1.monotone_metrics(fam,c_fused,truths,eligible); req(int(metrics['qualified_matches'])==95,'qualified changed')
    gates={'recovered_at_100_strictly_better_than_parent':int(metrics['recovered_at_100'])>66,'recovered_at_50_not_worse_than_parent':int(metrics['recovered_at_50'])>=41,'recovered_at_25_not_worse_than_parent':int(metrics['recovered_at_25'])>=23,'top100_precision_not_worse_than_parent':float(metrics['top100_dominant_precision'])>=PARENT['top100_dominant_precision'],'mrr_not_worse_than_parent':float(metrics['mrr'])>=PARENT['mrr'],'qualified_count_identical':int(metrics['qualified_matches'])==95}; passed=all(gates.values()); pos=ks[y]; neg=ks[~y]; c22=np.asarray([c[0] for c in counts]); c23=np.asarray([c[1] for c in counts])
    result={'verdict':'PASS_GMN_V31_FPARAM_KS_V1' if passed else 'FAIL_GMN_V31_FPARAM_KS_V1','scientific_role':'TARGET_EXCLUDED_GMN_2022_2023_V31_SUCCESSOR_DEVELOPMENT_ONLY','first_valid_outcome_binding':True,'candidate_count':N,'feature_dimension_parent':23,'feature_dimension_candidate':24,'parent_feature_sha256':arrsha(X),'centroid_sha256':arrsha(cm),'parent_margin_sha256':arrsha(parent),'fparam_ks_sha256':arrsha(ks),'candidate_margin_sha256':arrsha(cand),'candidate_fused_order_sha256':ordersha(c_fused),'resolved_fparam_column':next(iter(resolved_cols)),'hard_control':HARD,'parent_control':PARENT,'parent_reproduced_metrics':trim(parent_metrics),'fparam_local_only':trim(local_metrics),'fparam_equal_rank_fusion':trim(metrics),'pass_gates':gates,'ks_summary_all':{'min':float(ks.min()),'median':float(np.median(ks)),'max':float(ks.max())},'ks_summary_positive':{'min':float(pos.min()),'median':float(np.median(pos)),'max':float(pos.max())},'ks_summary_nonpositive':{'min':float(neg.min()),'median':float(np.median(neg)),'max':float(neg.max())},'finite_counts_2022':{'min':int(c22.min()),'median':float(np.median(c22)),'max':int(c22.max())},'finite_counts_2023':{'min':int(c23.min()),'median':float(np.median(c23)),'max':int(c23.max())},'per_family':[{'family_id':fid,'fparam_ks':float(ks[i]),'n2022':counts[i][0],'n2023':counts[i][1]} for i,fid in enumerate(ids)],'feature_search':False,'alternate_fparam_statistic':False,'extra_raw_observable':False,'metric_search':False,'k_search':False,'scaling_search':False,'reference_change':False,'diversity_search':False,'fusion_search':False,'post_result_second_search':False,'blind_exclusion':[20.0,55.0],'protected_fparam_used':False,'sonotaco_2013_2014_access':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'sonotaco_benchmark_authorized_by_this_result':bool(passed)}
    (a.output/'GMN_V31_FPARAM_KS_V1_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({k:v for k,v in result.items() if k!='per_family'},indent=2,sort_keys=True,allow_nan=False)); return 0
if __name__=='__main__': raise SystemExit(main())
