#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

FEATURE_DIM=71
RADIUS=1.0
RECOVERY=0.5
EXPECTED_HDB={2013:(0.14888037368183737,9,11),2014:(0.15198123772301594,9,9)}


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def order_sha(order:list[str])->str:
    return hashlib.sha256('\n'.join(map(str,order)).encode()).hexdigest()


def wrap180(x:float)->float:
    return float((float(x)+180.0)%360.0-180.0)


def annual_distance(a:np.ndarray,b:np.ndarray)->float:
    d_sol=wrap180(float(a[0])-float(b[0]))/4.0
    d_lon=wrap180(float(a[1])-float(b[1]))*math.cos(math.radians(0.5*(float(a[2])+float(b[2]))))/2.0
    d_lat=(float(a[2])-float(b[2]))/2.0
    d_vg=(math.exp(float(a[3]))-math.exp(float(b[3])))/2.0
    return float(math.sqrt(d_sol*d_sol+d_lon*d_lon+d_lat*d_lat+d_vg*d_vg))


def build_graph(root:Path)->dict[str,Any]:
    meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False)
    ids=list(map(str,meta['family_ids'])); sources=list(map(str,meta['sources']))
    require(meta['truth_accessed'] is False and meta['feature_dimension']==FEATURE_DIM,'invalid immutable pretruth manifest')
    require(X.shape==(len(ids),FEATURE_DIM) and C.shape==(len(ids),8) and len(sources)==len(ids),'pretruth array shape changed')
    require(v22.array_sha(X)==meta['feature_sha256'] and v22.array_sha(C)==meta['centroid_sha256'],'pretruth array identity changed')
    adj=[{i} for i in range(len(ids))]; edges=[]
    for i in range(len(ids)):
        for j in range(i+1,len(ids)):
            d=max(annual_distance(C[i,:4],C[j,:4]),annual_distance(C[i,4:],C[j,4:]))
            if d<=RADIUS:
                adj[i].add(j); adj[j].add(i); edges.append((i,j,float(d)))
    degree=np.asarray([math.log1p(len(a)-1) for a in adj],float)
    cross=np.asarray([math.log1p(sum(sources[j]!=sources[i] for j in adj[i])) for i in range(len(ids))],float)
    nsrc=np.asarray([float(len({sources[j] for j in adj[i]})-1) for i in range(len(ids))],float)
    require(np.max(np.abs(degree-X[:,67]))<=1e-12,'radius-1 degree graph feature identity failed')
    require(np.max(np.abs(cross-X[:,68]))<=1e-12,'radius-1 cross-source graph feature identity failed')
    require(np.max(np.abs(nsrc-X[:,69]))<=1e-12,'radius-1 source-count graph feature identity failed')
    return {
        'ids':ids,'sources':sources,
        'adjacency':[[int(j) for j in sorted(a)] for a in adj],
        'edges':[[int(i),int(j),float(d)] for i,j,d in edges],
        'edge_count':len(edges),
        'graph_feature_identity_max_abs_error':{
            'log1p_degree':float(np.max(np.abs(degree-X[:,67]))),
            'log1p_cross_source_neighbors':float(np.max(np.abs(cross-X[:,68]))),
            'distinct_other_sources':float(np.max(np.abs(nsrc-X[:,69])),),
        },
    }


def graph_mode(payload_root:Path,output:Path)->int:
    output.mkdir(parents=True,exist_ok=True); result={'verdict':'PASS_RADIUS1_PRETRUTH_GRAPH_IDENTITY','radius':RADIUS,'truth_accessed':False,'routes':{},'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False}
    for route in v24.ROUTES:
        g=build_graph(payload_root/route); result['routes'][route]={'family_ids':g['ids'],'sources':g['sources'],'adjacency':g['adjacency'],'edges':g['edges'],'edge_count':g['edge_count'],'graph_feature_identity_max_abs_error':g['graph_feature_identity_max_abs_error']}
    raw=(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); (output/'RADIUS1_PRETRUTH_GRAPH_IDENTITY.json').write_text(raw); print(json.dumps({'verdict':result['verdict'],'radius':RADIUS,'edge_counts':{r:result['routes'][r]['edge_count'] for r in v24.ROUTES},'identity_errors':{r:result['routes'][r]['graph_feature_identity_max_abs_error'] for r in v24.ROUTES}},indent=2,sort_keys=True)); return 0


def summarize(rows:list[dict[str,Any]])->dict[str,Any]:
    if not rows: return {'groups':0,'median_representative_rank':None,'median_best_neighbor_rank':None,'median_rank_uplift':None,'groups_with_neighbor_in_budget':0,'groups_best_neighbor_other_shower':0,'groups_best_neighbor_neg':0}
    return {'groups':len(rows),'median_representative_rank':float(np.median([r['representative_rank'] for r in rows])),'median_best_neighbor_rank':float(np.median([r['best_neighbor_rank'] for r in rows])),'median_rank_uplift':float(np.median([r['rank_uplift'] for r in rows])),'groups_with_neighbor_in_budget':int(sum(r['any_neighbor_in_budget'] for r in rows)),'groups_best_neighbor_other_shower':int(sum(r['best_neighbor_relation']=='OTHER_SHOWER' for r in rows)),'groups_best_neighbor_neg':int(sum(r['best_neighbor_relation']=='NEG' for r in rows))}


def diagnose_mode(payload_root:Path,truth_root:Path,ranker_source:Path,graph_file:Path,output:Path)->int:
    output.mkdir(parents=True,exist_ok=True); pre=json.loads(graph_file.read_text()); require(pre['verdict']=='PASS_RADIUS1_PRETRUTH_GRAPH_IDENTITY' and pre['truth_accessed'] is False and float(pre['radius'])==RADIUS,'invalid pretruth graph identity payload')
    require(v22.sha(ranker_source)==v24.RANKER_SOURCE_SHA,'#839 ranker source changed'); ranker=v22.load_module(ranker_source,'frozen_839_v31_graphdiag')
    truth={}; frozen={}
    for route,year in v24.PANELS:
        truth[(route,year)]=json.loads((truth_root/f'truth_{route}_{year}.json').read_text()); frozen[(route,year)]=json.loads((truth_root/f'evaluation_{route}_{year}.json').read_text())
    data={}; Xs=[]; y13s=[]; y14s=[]; groups=[]; offsets={}; cursor=0
    for route in v24.ROUTES:
        root=payload_root/route; meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fp=json.loads((root/'family_memberships.json').read_text())
        ids=list(map(str,meta['family_ids'])); fams=fp['families']; X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False)
        require(pre['routes'][route]['family_ids']==ids,'pretruth graph family identity changed after truth')
        by={y:truth[(route,y)] for y in v24.YEARS}; eligible=v22.eligible_from_year_truth(by); hidden={}; hidden.update(by[2013]); hidden.update(by[2014]); base=[v22.family_truth(f,hidden,eligible) for f in fams]
        q13=[]; q14=[]; rg=[]
        for i,(fam,t) in enumerate(zip(fams,base)):
            label=t['best_label']; rg.append(('SHOWER/'+str(label)) if label is not None else f'NEG/{route}/{ids[i]}')
            if not t['positive'] or label is None: a13=a14=0.0
            else: a13,a14=v24.annual_f1_for_fixed_label(fam,str(label),by)
            q13.append(float(a13)); q14.append(float(a14))
        offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids); Xs.append(X); y13s.append(np.asarray(q13,float)); y14s.append(np.asarray(q14,float)); groups.extend(rg); data[route]={'meta':meta,'fams':fams,'ids':ids,'centroids':C,'groups':rg,'y13':np.asarray(q13,float),'y14':np.asarray(q14,float)}
    Xall=np.vstack(Xs); y13all=np.concatenate(y13s); y14all=np.concatenate(y14s); groups=list(map(str,groups)); folds=np.asarray([v22.v1.deterministic_fold(g) for g in groups],int); margin13=np.zeros(cursor); margin14=np.zeros(cursor)
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; require({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}),f'group leakage fold {fold}'); mu=Xall[tr].mean(0); sd=Xall[tr].std(0,ddof=0); scale=sd.copy(); scale[scale==0.0]=1.0; Ztr=(Xall[tr]-mu)/scale; Zte=(Xall[te]-mu)/scale; teidx=np.where(te)[0]
        for year,yall,out in ((2013,y13all,margin13),(2014,y14all,margin14)):
            pos=yall[tr]>RECOVERY; neg=~pos; P=Ztr[pos]; N=Ztr[neg]; require(len(P)>0 and len(N)>0,f'{year} fold {fold} missing references')
            for j,gi in enumerate(teidx.tolist()): out[gi]=float(np.min(np.linalg.norm(N-Zte[j],axis=1))-np.min(np.linalg.norm(P-Zte[j],axis=1)))
    combined=np.minimum(margin13,margin14); lo,hi=offsets['hdbscan']; rd=data['hdbscan']; ids=rd['ids']; tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]; idx=ranker.diversity_order(combined[lo:hi],rd['centroids'],0.8,1.0,tie); local=[ids[i] for i in idx]; v19order=list(map(str,rd['meta']['v19_order'])); order=list(v19.fusion_orders(local,v19order)['rank_sum']); ranked=v22.rerank(rd['fams'],order); rank={fid:i+1 for i,fid in enumerate(order)}; byid={fid:i for i,fid in enumerate(ids)}; raw_score={fid:float(combined[lo+i]) for i,fid in enumerate(ids)}
    controls={}
    for year,(em,er,budget) in EXPECTED_HDB.items():
        cur=v22.evaluate(ranked,truth[('hdbscan',year)],budget); require(abs(float(cur['macro_f1'])-em)<1e-12 and int(cur['recovered_f1_gt_0_5'])==er,f'v31 HDB {year} reproduction failed'); controls[str(year)]={'macro_f1':float(cur['macro_f1']),'recovered_f1_gt_0_5':int(cur['recovered_f1_gt_0_5']),'budget':budget}
    adj=pre['routes']['hdbscan']['adjacency']; edges=pre['routes']['hdbscan']['edges']; require(len(adj)==len(ids),'graph adjacency size changed')
    purity={'total_edges':len(edges),'same_shower_group':0,'different_shower_groups':0,'involving_neg':0}
    for i,j,_ in edges:
        gi=rd['groups'][int(i)]; gj=rd['groups'][int(j)]
        if gi.startswith('NEG/') or gj.startswith('NEG/'): purity['involving_neg']+=1
        elif gi==gj: purity['same_shower_group']+=1
        else: purity['different_shower_groups']+=1
    total=max(purity['total_edges'],1); purity.update({'same_shower_fraction':purity['same_shower_group']/total,'different_shower_fraction':purity['different_shower_groups']/total,'neg_involved_fraction':purity['involving_neg']/total})
    annual_diag={}
    for year in (2013,2014):
        annual=rd['y13'] if year==2013 else rd['y14']; budget=EXPECTED_HDB[year][2]; positive=np.where(annual>RECOVERY)[0].tolist(); group_to_pos={}
        for i in positive: group_to_pos.setdefault(rd['groups'][i],[]).append(i)
        rows=[]
        for g,inds in sorted(group_to_pos.items()):
            require(g.startswith('SHOWER/'),'annual-positive family lacks shower group'); rep=sorted(inds,key=lambda i:(rank[ids[i]],ids[i]))[0]; union=set()
            for i in inds: union.update(map(int,adj[i]))
            best=min(union,key=lambda j:(rank[ids[j]],ids[j])); bg=rd['groups'][best]
            relation='SAME_SHOWER' if bg==g else ('NEG' if bg.startswith('NEG/') else 'OTHER_SHOWER')
            truth_groups={rd['groups'][j] for j in union}; rows.append({'group':g,'representative_family_id':ids[rep],'representative_rank':rank[ids[rep]],'representative_raw_margin':raw_score[ids[rep]],'surfaced':bool(rank[ids[rep]]<=budget),'direct_neighbor_union_count':len(union),'distinct_neighbor_truth_groups':len(truth_groups),'best_neighbor_family_id':ids[best],'best_neighbor_rank':rank[ids[best]],'best_neighbor_raw_margin':raw_score[ids[best]],'rank_uplift':int(rank[ids[rep]]-rank[ids[best]]),'best_neighbor_relation':relation,'any_neighbor_in_budget':bool(any(rank[ids[j]]<=budget for j in union))})
        surfaced=[r for r in rows if r['surfaced']]; missed=[r for r in rows if not r['surfaced']]
        annual_diag[str(year)]={'budget':budget,'annual_recoverable_groups':len(rows),'surfaced_groups':len(surfaced),'missed_groups':len(missed),'surfaced_summary':summarize(surfaced),'missed_summary':summarize(missed),'groups':rows}
    result={'verdict':'PASS_V31_RADIUS1_GRAPH_SURFACING_DIAGNOSTIC','scientific_role':'POST_RESULT_DIAGNOSTIC_ONLY_NO_PROPAGATED_RANK_EVALUATED','pretruth_graph_identity':{'radius':RADIUS,'hdbscan_edge_count':len(edges),'graph_feature_identity_max_abs_error':pre['routes']['hdbscan']['graph_feature_identity_max_abs_error']},'v31_hdb_reproduction':controls,'v31_order_sha256':order_sha(order),'global_graph_purity':purity,'annual_diagnostics':annual_diag,'propagated_score_evaluated':False,'successor_selected':False,'radius_search':False,'hop_search':False,'neighbor_aggregation_search':False,'blend_search':False,'feature_search':False,'model_search':False,'post_result_second_search':False,'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0]}
    (output/'V31_RADIUS1_GRAPH_SURFACING_DIAGNOSTIC.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); compact={'verdict':result['verdict'],'v31_hdb_reproduction':controls,'global_graph_purity':purity,'annual':{}}
    for year in ('2013','2014'): compact['annual'][year]={k:v for k,v in annual_diag[year].items() if k!='groups'}
    print(json.dumps(compact,indent=2,sort_keys=True,allow_nan=False)); return 0


def main()->int:
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='mode',required=True); g=sub.add_parser('graph'); g.add_argument('--payload-root',type=Path,required=True); g.add_argument('--output',type=Path,required=True); d=sub.add_parser('diagnose'); d.add_argument('--payload-root',type=Path,required=True); d.add_argument('--truth-root',type=Path,required=True); d.add_argument('--ranker-source',type=Path,required=True); d.add_argument('--graph-file',type=Path,required=True); d.add_argument('--output',type=Path,required=True); a=p.parse_args(); return graph_mode(a.payload_root,a.output) if a.mode=='graph' else diagnose_mode(a.payload_root,a.truth_root,a.ranker_source,a.graph_file,a.output)


if __name__=='__main__': raise SystemExit(main())
