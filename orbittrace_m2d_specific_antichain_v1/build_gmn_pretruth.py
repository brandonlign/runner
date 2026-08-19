#!/usr/bin/env python3
from __future__ import annotations

import importlib.util,json,sys
from pathlib import Path
from typing import Any

def req(x,m):
    if not x: raise RuntimeError(m)
def load(p:Path,n:str)->Any:
    s=importlib.util.spec_from_file_location(n,p); req(s is not None and s.loader is not None,f'cannot import {p}'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def specific_antichain(rows:list[dict[str,Any]], parent:list[int|None], children:list[list[int]]):
    del parent,children
    sets=[set(map(str,r['event_ids'])) for r in rows]
    for r in rows:
        n=int(r['member_count']); req(n>=4,'sub-support'); r['specific_2d_mass']=float(r['internal_2d_mass'])/n
    order=sorted(range(len(rows)),key=lambda i:(-float(rows[i]['specific_2d_mass']),-float(rows[i]['internal_2d_mass']),str(rows[i]['family_hash'])))
    acc=[]; broad=0; narrow=0; rejected=0; examples=[]
    for i in order:
        s=sets[i]; ov=[j for j in acc if not s.isdisjoint(sets[j])]
        if not ov: acc.append(i); continue
        rejected+=1
        for j in ov: req(s.issubset(sets[j]) or sets[j].issubset(s),'non-laminar overlap')
        if any(sets[j].issubset(s) and sets[j]!=s for j in ov): broad+=1
        if any(s.issubset(sets[j]) and sets[j]!=s for j in ov): narrow+=1
        if len(examples)<20: examples.append({'rejected_hash':rows[i]['family_hash'],'rejected_members':rows[i]['member_count'],'rejected_d2d':rows[i]['specific_2d_mass'],'accepted_overlap':[{'hash':rows[j]['family_hash'],'members':rows[j]['member_count'],'d2d':rows[j]['specific_2d_mass']} for j in ov[:4]]})
    out=[dict(rows[i]) for i in acc]
    out.sort(key=lambda r:(-float(r['specific_2d_mass']),-float(r['internal_2d_mass']),str(r['family_hash'])))
    for k,r in enumerate(out,1): r['rank']=k
    os=[set(map(str,r['event_ids'])) for r in out]; req(all(a.isdisjoint(b) for i,a in enumerate(os) for b in os[i+1:]),'output overlap')
    return out,{'evidence_split_count':rejected,'overlap_rejection_count':rejected,'rejected_broad_ancestor_count':broad,'rejected_narrow_descendant_count':narrow,'selected_candidate_count':len(out),'reportable_node_count':len(rows),'pairwise_disjoint':True,'packing_rule':'specific_2d_mass_desc_then_raw_M2D_desc_then_hash; accept iff disjoint','rejected_examples':examples}

def main():
    args=list(sys.argv[1:]); req('--recursive-builder' in args,'missing helper'); p=args.index('--recursive-builder'); helper=Path(args[p+1]); del args[p:p+2]; req('--output' in args,'missing output'); out=Path(args[args.index('--output')+1])
    rec=load(helper,'specific_m2d_frozen_label_free_helper'); rec.evidence_cut=specific_antichain
    old=sys.argv
    try: sys.argv=[old[0],*args]; rc=int(rec.main() or 0)
    finally: sys.argv=old
    req(rc==0 and out.is_file(),'helper failed'); r=json.loads(out.read_text()); req(r['shower_truth_used'] is False and r['target_information_access'] is False and r['target_region_events_accessed'] is False and r['orbittrace_reveal_access'] is False and r['sonotaco_scientific_access'] is False,'firewall'); req(r['post_result_parameter_search'] is False,'post-result search')
    rej=int(r.pop('total_evidence_split_count')); r['schema']='ORBITTRACE_M2D_SPECIFIC_ANTICHAIN_V1_PRETRUTH'; r['scientific_role']='TARGET_EXCLUDED_GMN_SPECIFIC_M2D_ANTICHAIN_FROZEN_BEFORE_TRUTH'; r['configuration']={'radius':1.0,'minimum_support':4,'specific_score':'D2D=M2D/member_count','packing_rule':'D2D_desc_then_M2D_desc_then_hash; greedy disjoint antichain','new_tuned_parameters':[]}; r['total_overlap_rejection_count']=rej; r['total_rejected_broad_ancestor_count']=sum(int(s['cut_summary'].get('rejected_broad_ancestor_count',0)) for s in r['subsets']); r['total_rejected_narrow_descendant_count']=sum(int(s['cut_summary'].get('rejected_narrow_descendant_count',0)) for s in r['subsets']); out.write_text(json.dumps(r,separators=(',',':'),sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':'SPECIFIC_M2D_ANTICHAIN_PRETRUTH_SEALED','rejections':rej,'broad_ancestors':r['total_rejected_broad_ancestor_count'],'sizes':r['global_size_summary']},indent=2,sort_keys=True))
if __name__=='__main__': main()
