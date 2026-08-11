#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

EXPECTED_HDB={2013:(0.14257102406283795,10,11),2014:(0.12833942693327394,7,9)}
RECOVERY=0.5


def require(ok: bool,msg: str)->None:
    if not ok: raise RuntimeError(msg)


def summarize(rows:list[dict[str,Any]])->dict[str,Any]:
    if not rows:
        return {'groups':0,'with_internal_edge':0,'with_cross_source_internal_edge':0,'internal_edge_count':0,'candidate_families':0,'largest_component_median':0.0,'incident_edge_purity_mean':0.0}
    return {
        'groups':len(rows),
        'with_internal_edge':sum(bool(r['has_internal_edge']) for r in rows),
        'with_cross_source_internal_edge':sum(bool(r['has_cross_source_internal_edge']) for r in rows),
        'internal_edge_count':sum(int(r['internal_edges']) for r in rows),
        'candidate_families':sum(int(r['candidate_families']) for r in rows),
        'largest_component_median':float(np.median([r['largest_same_group_component'] for r in rows])),
        'incident_edge_purity_mean':float(np.mean([r['incident_edge_purity'] for r in rows])),
    }


def largest_component(nodes:set[int],internal_edges:list[tuple[int,int]])->int:
    if not nodes: return 0
    adj={i:set() for i in nodes}
    for i,j in internal_edges:
        adj[i].add(j); adj[j].add(i)
    seen=set(); best=0
    for start in nodes:
        if start in seen: continue
        stack=[start]; seen.add(start); n=0
        while stack:
            u=stack.pop(); n+=1
            for v in adj[u]:
                if v not in seen: seen.add(v); stack.append(v)
        best=max(best,n)
    return best


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--sugar-root',type=Path,required=True); p.add_argument('--hdbscan-root',type=Path,required=True)
    p.add_argument('--truth-root',type=Path,required=True); p.add_argument('--ranker-source',type=Path,required=True)
    p.add_argument('--graph-json',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(v22.sha(a.ranker_source)==v24.RANKER_SOURCE_SHA,'#839 ranker source changed')

    roots={'sugar':a.sugar_root,'hdbscan':a.hdbscan_root}
    truth={}; frozen_eval={}
    for route,year in v24.PANELS:
        truth[(route,year)]=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text())
        frozen_eval[(route,year)]=json.loads((a.truth_root/f'evaluation_{route}_{year}.json').read_text())

    ranker=v22.load_module(a.ranker_source,'frozen_839_graph_diag')
    route_data={}; Xs=[]; y13s=[]; y14s=[]; groups=[]; offsets={}; cursor=0
    for route in v24.ROUTES:
        root=roots[route]; meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fp=json.loads((root/'family_memberships.json').read_text())
        require(meta['feature_dimension']==71 and meta['truth_accessed'] is False and fp['truth_accessed'] is False,'invalid immutable pretruth payload')
        ids=list(map(str,meta['family_ids'])); fams=fp['families']; require([str(f['family_id']) for f in fams]==ids,'family alignment changed')
        X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False)
        require(v22.array_sha(X)==meta['feature_sha256'] and v22.array_sha(C)==meta['centroid_sha256'],'pretruth array hash changed')
        by={y:truth[(route,y)] for y in v24.YEARS}; eligible=v22.eligible_from_year_truth(by); hidden={}; hidden.update(by[2013]); hidden.update(by[2014])
        base_truths=[v22.family_truth(f,hidden,eligible) for f in fams]
        y13=[]; y14=[]; route_groups=[]
        for i,(f,t) in enumerate(zip(fams,base_truths)):
            label=t['best_label']; route_groups.append(('SHOWER/'+str(label)) if label is not None else f'NEG/{route}/{ids[i]}')
            if not t['positive'] or label is None: y13.append(0.0); y14.append(0.0)
            else:
                q13,q14=v24.annual_f1_for_fixed_label(f,str(label),by); y13.append(q13); y14.append(q14)
        offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids); Xs.append(X); y13s.append(np.asarray(y13,float)); y14s.append(np.asarray(y14,float)); groups.extend(route_groups)
        route_data[route]={'meta':meta,'fams':fams,'ids':ids,'centroids':C,'groups':route_groups,'y13':np.asarray(y13,float),'y14':np.asarray(y14,float)}

    Xall=np.vstack(Xs); y13all=np.concatenate(y13s); y14all=np.concatenate(y14s); groups=list(map(str,groups))
    folds=np.asarray([v22.v1.deterministic_fold(g) for g in groups],dtype=int); weights=np.asarray(ranker.grouped_weights(groups),float)
    o13=np.zeros(cursor); o14=np.zeros(cursor)
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; m13=ranker.model(); m14=ranker.model(); m13.fit(Xall[tr],y13all[tr],sample_weight=weights[tr]); m14.fit(Xall[tr],y14all[tr],sample_weight=weights[tr]); o13[te]=m13.predict(Xall[te]); o14[te]=m14.predict(Xall[te])
        require({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}),f'group leakage fold {fold}')
    worst=np.minimum(o13,o14)

    lo,hi=offsets['hdbscan']; rd=route_data['hdbscan']; ids=rd['ids']; tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]
    idx=ranker.diversity_order(worst[lo:hi],rd['centroids'],0.8,1.0,tie); quality=[ids[i] for i in idx]; v19_order=list(map(str,rd['meta']['v19_order'])); fused=list(v19.fusion_orders(quality,v19_order)['rank_sum'])
    reranked=v22.rerank(rd['fams'],fused)
    reproduction={}
    for year in (2013,2014):
        macro,rec,budget=EXPECTED_HDB[year]; cur=v22.evaluate(reranked,truth[('hdbscan',year)],budget)
        require(abs(float(cur['macro_f1'])-macro)<1e-12 and int(cur['recovered_f1_gt_0_5'])==rec,f'v24 HDB {year} reproduction failed')
        reproduction[str(year)]={'macro_f1':float(cur['macro_f1']),'recovered_f1_gt_0_5':int(cur['recovered_f1_gt_0_5']),'budget':budget}

    graph=json.loads(a.graph_json.read_text()); require(graph['verdict']=='PASS_V24_HDB_GRAPH_PRETRUTH_CAPTURE' and graph['truth_accessed'] is False,'invalid pretruth graph capture')
    require(graph['radius']==1.0 and list(map(str,graph['family_ids']))==ids,'graph identity/alignment changed')
    sources=list(map(str,graph['sources'])); require(sources==list(map(str,rd['meta']['sources'])),'graph source alignment changed')
    edges=[(float(d),int(i),int(j)) for d,i,j in graph['edges']]; require(len(edges)==int(graph['edge_count']),'graph edge count changed')

    group_by_idx=list(map(str,rd['groups'])); idpos={fid:i for i,fid in enumerate(ids)}; rank={fid:i+1 for i,fid in enumerate(fused)}
    edge_same=0; cross_edge_same=0; cross_edges=0; comparable_edges=0
    for _d,i,j in edges:
        gi,gj=group_by_idx[i],group_by_idx[j]
        if gi.startswith('SHOWER/') and gj.startswith('SHOWER/'):
            comparable_edges+=1; edge_same+=int(gi==gj)
            if sources[i]!=sources[j]: cross_edges+=1; cross_edge_same+=int(gi==gj)

    per_year={}
    for year,arr in ((2013,rd['y13']),(2014,rd['y14'])):
        budget=EXPECTED_HDB[year][2]
        positive_groups=sorted({group_by_idx[i] for i in range(len(ids)) if group_by_idx[i].startswith('SHOWER/') and float(arr[i])>RECOVERY})
        rows=[]
        surfaced_count=0
        for g in positive_groups:
            nodes={i for i,x in enumerate(group_by_idx) if x==g}; positive_nodes={i for i in nodes if float(arr[i])>RECOVERY}
            first_positive_rank=min(rank[ids[i]] for i in positive_nodes); surfaced=first_positive_rank<=budget; surfaced_count+=int(surfaced)
            internal=[]; incident=0
            cross_internal=0
            for _d,i,j in edges:
                if i in nodes or j in nodes: incident+=1
                if i in nodes and j in nodes:
                    internal.append((i,j)); cross_internal+=int(sources[i]!=sources[j])
            rows.append({
                'group':g,'surfaced':surfaced,'first_positive_rank':first_positive_rank,'candidate_families':len(nodes),'annual_recoverable_families':len(positive_nodes),
                'internal_edges':len(internal),'has_internal_edge':bool(internal),'cross_source_internal_edges':cross_internal,'has_cross_source_internal_edge':bool(cross_internal),
                'largest_same_group_component':largest_component(nodes,internal),'incident_edges':incident,'incident_edge_purity':float(len(internal)/incident) if incident else 0.0,
            })
        require(surfaced_count==EXPECTED_HDB[year][1],f'{year} diagnostic surfaced-group count does not equal reproduced recovered count')
        surfaced=[r for r in rows if r['surfaced']]; missed=[r for r in rows if not r['surfaced']]
        per_year[str(year)]={'budget':budget,'recoverable_groups':len(rows),'surfaced':summarize(surfaced),'missed':summarize(missed),'groups':rows}

    result={
        'verdict':'PASS_V24_HDB_GRAPH_COHERENCE_DIAGNOSTIC',
        'scientific_role':'POST_RESULT_DIAGNOSTIC_ONLY_NO_SUCCESSOR_SELECTED',
        'v24_hdb_reproduction':reproduction,
        'graph':{'source_pr':843,'radius':1.0,'families':len(ids),'edges':len(edges),'shower_labeled_comparable_edges':comparable_edges,'same_shower_edge_purity':float(edge_same/comparable_edges) if comparable_edges else 0.0,'cross_source_comparable_edges':cross_edges,'cross_source_same_shower_edge_purity':float(cross_edge_same/cross_edges) if cross_edges else 0.0},
        'annual_group_diagnostics':per_year,
        'graph_rank_or_transform_evaluated':False,'successor_selected':False,'radius_search':False,'feature_search':False,'parameter_search':False,'post_result_second_search':False,
        'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0],
    }
    (a.output/'V24_HDB_GRAPH_COHERENCE_DIAGNOSTIC.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'graph':result['graph'],'2013':per_year['2013']|{'groups':'omitted'},'2014':per_year['2014']|{'groups':'omitted'}},indent=2,sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
