#!/usr/bin/env python3
"""Target-aware forensic diagnostic only; not a method proposal.
Reconstructs all SACV-valid rank-84 cross-year pairs, finds bipartite recurrence
components, and reports component membership unions and target-free structural
statistics plus diagnostic target overlap.
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
from pathlib import Path
import numpy as np

def load(path:Path,name:str):
    s=importlib.util.spec_from_file_location(name,path); assert s and s.loader
    m=importlib.util.module_from_spec(s); sys.modules[name]=m; s.loader.exec_module(m); return m

def main():
    ap=argparse.ArgumentParser();
    ap.add_argument('--sacv-source',type=Path,required=True); ap.add_argument('--diag-source',type=Path,required=True)
    ap.add_argument('--events',type=Path,required=True); ap.add_argument('--stage-a',type=Path,required=True); ap.add_argument('--result',type=Path,required=True); ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args(); sacv=load(a.sacv_source,'cu_sacv'); diag=load(a.diag_source,'cu_diag')
    events=json.loads(a.events.read_text())['events']; rt=sacv.Runtime(events)
    stage=json.loads(a.stage_a.read_text()); result=json.loads(a.result.read_text()); row=stage['extractions'][83]
    assert row['rank']==84 and row['parent_n']==1814
    targets=set(result['selected_candidate']['extraction']['overlap_2022_ids']+result['selected_candidate']['extraction']['overlap_2023_ids']); assert len(targets)==18
    parent=sorted(row['output_ids'])
    scored={}
    for y in sacv.YEARS:
        rows=[]
        for eid in parent:
            if eid in rt.uidx[y]:
                q=diag.score_center(rt,sacv,parent,eid,y)
                if q: rows.append(q)
        rows.sort(key=lambda q:(-q['key'][0],-q['key'][1],-q['key'][2],-q['key'][3],q['id']))
        for i,q in enumerate(rows,1): q['annual_rank']=i
        scored[y]=rows
    pairs=[]; adj={}
    for qa in scored[2022]:
        for qb in scored[2023]:
            d=float(np.linalg.norm(qa['center']-qb['center']))
            ab=len(rt.members(parent,qa['center'],qa['radius'],2023)); ba=len(rt.members(parent,qb['center'],qb['radius'],2022))
            if not (d<=qa['radius']+1e-12 and d<=qb['radius']+1e-12 and ab>=4 and ba>=4): continue
            p={'a':qa['id'],'b':qb['id'],'d':d,'ab':ab,'ba':ba,'annual_rank_a':qa['annual_rank'],'annual_rank_b':qb['annual_rank'],
               'members_a':qa['members'],'members_b':qb['members'],'excess_a':qa['excess'],'excess_b':qb['excess']}
            pairs.append(p); A='22:'+qa['id']; B='23:'+qb['id']; adj.setdefault(A,set()).add(B); adj.setdefault(B,set()).add(A)
    byid={q['id']:q for y in sacv.YEARS for q in scored[y]}
    seen=set(); comps=[]
    for seed in sorted(adj):
        if seed in seen: continue
        stack=[seed]; seen.add(seed); nodes=[]
        while stack:
            u=stack.pop(); nodes.append(u)
            for v in adj[u]:
                if v not in seen: seen.add(v); stack.append(v)
        ids={n.split(':',1)[1] for n in nodes}; edges=[p for p in pairs if p['a'] in ids and p['b'] in ids]
        member_union=sorted({m for eid in ids for m in byid[eid]['members']})
        ov=sorted(set(member_union)&targets); prec=len(ov)/len(member_union); rec=len(ov)/18; f1=2*prec*rec/(prec+rec) if prec+rec else 0
        comp={'node_count':len(nodes),'edge_count':len(edges),'year22_nodes':sum(n.startswith('22:') for n in nodes),'year23_nodes':sum(n.startswith('23:') for n in nodes),
              'member_union_n':len(member_union),'min_cross_support':min(min(p['ab'],p['ba']) for p in edges),'max_cross_support':max(max(p['ab'],p['ba']) for p in edges),
              'min_edge_excess':min(min(p['excess_a'],p['excess_b']) for p in edges),'max_edge_excess':max(min(p['excess_a'],p['excess_b']) for p in edges),
              'mean_edge_distance':sum(p['d'] for p in edges)/len(edges),'min_edge_distance':min(p['d'] for p in edges),
              'target_overlap':len(ov),'target_precision':prec,'target_recall':rec,'target_f1':f1,'target_center_nodes':len(ids&targets),
              'node_ids':sorted(ids),'member_union_ids':member_union}
        comps.append(comp)
    # target-free structural orders only; target metrics reported after ordering.
    orders={
      'edge_count':lambda c:(c['edge_count'],c['node_count'],c['min_cross_support'],-c['member_union_n']),
      'node_count':lambda c:(c['node_count'],c['edge_count'],c['min_cross_support'],-c['member_union_n']),
      'edge_density':lambda c:(c['edge_count']/(c['year22_nodes']*c['year23_nodes']),c['edge_count'],c['min_cross_support'],-c['member_union_n']),
      'compactness':lambda c:(-c['mean_edge_distance'],c['edge_count'],c['min_cross_support'],-c['member_union_n']),
    }
    rankings={}
    for name,key in orders.items():
        arr=sorted(range(len(comps)),key=lambda i:key(comps[i]),reverse=True)
        rankings[name]=arr
        for rank,i in enumerate(arr,1): comps[i]['rank_'+name]=rank
    out={'schema':'ORBITTRACE_SACV_V1_COMPONENT_UNION_POSTMORTEM','scientific_role':'TARGET_AWARE_FORENSIC_DIAGNOSTIC_ONLY_NOT_METHOD_DEVELOPMENT',
         'validated_pair_count':len(pairs),'component_count':len(comps),'components':comps,'target_free_component_orders':rankings,
         'diagnostic_only':True,'promotion_eligible':False,'method_change_authorized':False}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    brief=[]
    for i,c in enumerate(comps): brief.append({'i':i,**{k:c[k] for k in ('node_count','edge_count','member_union_n','min_cross_support','mean_edge_distance','target_center_nodes','target_overlap','target_precision','target_recall','target_f1','rank_edge_count','rank_node_count','rank_edge_density','rank_compactness')}})
    print(json.dumps({'components':brief,'orders':rankings},indent=2,sort_keys=True))
if __name__=='__main__': main()
