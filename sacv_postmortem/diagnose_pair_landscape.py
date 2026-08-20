#!/usr/bin/env python3
"""Target-aware forensic diagnostic only.
Enumerates the full rank-84 SACV recurrent-pair landscape to identify whether
failure is annual top-1 selection or a deeper recurrence-ranking problem.
NOT method development and NOT promotion eligible.
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
from pathlib import Path
import numpy as np


def load(path: Path, name: str):
    s=importlib.util.spec_from_file_location(name,path); assert s and s.loader
    m=importlib.util.module_from_spec(s); sys.modules[name]=m; s.loader.exec_module(m); return m


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--sacv-source',type=Path,required=True)
    ap.add_argument('--diag-source',type=Path,required=True)
    ap.add_argument('--events',type=Path,required=True)
    ap.add_argument('--stage-a',type=Path,required=True)
    ap.add_argument('--result',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args()
    sacv=load(a.sacv_source,'sacv_pair_runtime')
    diag=load(a.diag_source,'sacv_diag_runtime')
    rt=sacv.Runtime(json.loads(a.events.read_text())['events'])
    stage=json.loads(a.stage_a.read_text()); result=json.loads(a.result.read_text())
    row=stage['extractions'][83]; assert row['rank']==84 and row['parent_n']==1814
    selected=result['selected_candidate']; targets=set(selected['extraction']['overlap_2022_ids']+selected['extraction']['overlap_2023_ids']); assert len(targets)==18
    parent=sorted(row['output_ids']); assert set(targets)<=set(parent)

    scored={}
    for y in sacv.YEARS:
        rows=[]
        for eid in parent:
            if eid in rt.uidx[y]:
                q=diag.score_center(rt,sacv,parent,eid,y)
                if q: rows.append(q)
        rows=sorted(rows,key=lambda q:(-q['key'][0],-q['key'][1],-q['key'][2],-q['key'][3],q['id']))
        for j,q in enumerate(rows,1): q['annual_rank']=j
        scored[y]=rows

    pairs=[]
    for qa in scored[2022]:
        for qb in scored[2023]:
            d=float(np.linalg.norm(qa['center']-qb['center']))
            ab=len(rt.members(parent,qa['center'],qa['radius'],2023))
            ba=len(rt.members(parent,qb['center'],qb['radius'],2022))
            mutual=d<=qa['radius']+1e-12 and d<=qb['radius']+1e-12
            validates=bool(mutual and ab>=4 and ba>=4)
            if not validates: continue
            union=sorted(set(qa['members'])|set(qb['members']))
            ov=len(set(union)&targets); prec=ov/len(union) if union else 0.0; rec=ov/18.0
            f1=2*prec*rec/(prec+rec) if prec+rec else 0.0
            pairs.append({
                'a':qa['id'],'b':qb['id'],'annual_rank_a':qa['annual_rank'],'annual_rank_b':qb['annual_rank'],
                'd':d,'radius_a':qa['radius'],'radius_b':qb['radius'],'ab':ab,'ba':ba,
                'excess_a':qa['excess'],'excess_b':qb['excess'],'support_a':qa['parent_support'],'support_b':qb['parent_support'],
                'min_excess':min(qa['excess'],qb['excess']),'sum_excess':qa['excess']+qb['excess'],
                'min_cross_support':min(ab,ba),'sum_cross_support':ab+ba,
                'union_n':len(union),'target_overlap':ov,'target_precision':prec,'target_recall':rec,'target_f1':f1,
                'target_center_pair':qa['id'] in targets and qb['id'] in targets,
            })

    # Target-free candidate rankings: these scores never use target overlap.
    score_defs={
        'min_excess':lambda p:(p['min_excess'],p['sum_excess'],p['min_cross_support'],-p['union_n']),
        'sum_excess':lambda p:(p['sum_excess'],p['min_excess'],p['min_cross_support'],-p['union_n']),
        'cross_support':lambda p:(p['min_cross_support'],p['sum_cross_support'],p['min_excess'],-p['union_n']),
        'compact_recurrence':lambda p:(p['min_cross_support'],-p['d'],p['min_excess'],-p['union_n']),
    }
    rankings={}
    for name,key in score_defs.items():
        arr=sorted(pairs,key=key,reverse=True)
        for j,p in enumerate(arr,1): p[f'rank_{name}']=j
        t=[p for p in arr if p['target_center_pair']]
        rankings[name]={
            'best_target_pair_rank':min((p[f'rank_{name}'] for p in t),default=None),
            'top_pair':{k:v for k,v in arr[0].items() if not k.startswith('rank_')} if arr else None,
            'best_target_pair':max(t,key=key) if t else None,
        }

    # Bipartite connected components among validated center pairs.
    adj={}
    for p in pairs:
        akey='22:'+p['a']; bkey='23:'+p['b']; adj.setdefault(akey,set()).add(bkey); adj.setdefault(bkey,set()).add(akey)
    seen=set(); comps=[]
    for n in sorted(adj):
        if n in seen: continue
        stack=[n]; seen.add(n); nodes=[]
        while stack:
            u=stack.pop(); nodes.append(u)
            for v in adj.get(u,()):
                if v not in seen: seen.add(v); stack.append(v)
        ids={x.split(':',1)[1] for x in nodes}
        edge_rows=[p for p in pairs if p['a'] in ids and p['b'] in ids]
        target_nodes=len(ids & targets)
        comps.append({'node_count':len(nodes),'edge_count':len(edge_rows),'target_center_nodes':target_nodes,
                      'contains_target_center_pair':any(p['target_center_pair'] for p in edge_rows),
                      'best_target_f1':max((p['target_f1'] for p in edge_rows),default=0.0),
                      'max_min_excess':max((p['min_excess'] for p in edge_rows),default=0.0)})
    comps.sort(key=lambda c:(c['contains_target_center_pair'],c['best_target_f1'],c['max_min_excess']),reverse=True)

    target_pairs=[p for p in pairs if p['target_center_pair']]
    best_target=max(target_pairs,key=lambda p:(p['target_f1'],p['target_overlap'],-p['union_n']),default=None)
    out={
        'schema':'ORBITTRACE_SACV_V1_PAIR_LANDSCAPE_POSTMORTEM',
        'scientific_role':'TARGET_AWARE_FORENSIC_DIAGNOSTIC_ONLY_NOT_METHOD_DEVELOPMENT',
        'admissible_centers':{'2022':len(scored[2022]),'2023':len(scored[2023])},
        'validated_pair_count':len(pairs),'target_center_validated_pair_count':len(target_pairs),
        'best_target_pair_by_target_f1':best_target,'target_free_rankings':rankings,
        'validated_pair_components':comps,'component_count':len(comps),
        'diagnostic_only':True,'method_change_authorized':False,'promotion_eligible':False,
    }
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'validated_pair_count':len(pairs),'target_pair_count':len(target_pairs),'best_target':best_target,
                      'target_free_best_ranks':{k:v['best_target_pair_rank'] for k,v in rankings.items()},
                      'component_count':len(comps),'top_components':comps[:5]},indent=2,sort_keys=True))

if __name__=='__main__': main()
