from pathlib import Path
import hashlib

ROOT=Path('orbittrace_m2d_sacv_edge_consensus_v1')

p=ROOT/'build_pretruth.py'
s=p.read_text()
old="""        if comps:\n            win=comps[0]\n            # Sole successor change: edge-consensus membership. An event survives only when it is\n            # inside both endpoint local hypotheses of at least one validated cross-year edge\n            # belonging to the selected recurrent component. Union combines independently\n            # corroborated edge memberships; no frequency threshold or new geometric scale exists.\n            cset=set(win['nodes']); ce=[e for e in edges if ('22:'+e['a']) in cset and ('23:'+e['b']) in cset]\n            consensus=set()\n            for e in ce:\n                consensus.update(set(nodes['22:'+e['a']]['members']) & set(nodes['23:'+e['b']]['members']))\n            o=sorted(consensus);ref=True\n        else:\n            win=None;o=ids;ref=False\n"""
new="""        # Preserve the exact frozen SACV-v1 success path. The all-hypothesis graph is\n        # consulted only when that exact annual top-1 pair would otherwise fall back.\n        top22=byyear[2022][0] if byyear[2022] else None\n        top23=byyear[2023][0] if byyear[2023] else None\n        top_ref=bool(top22 and top23 and any(e['a']==top22['id'] and e['b']==top23['id'] for e in edges))\n        if top_ref:\n            o=sorted(set(top22['members'])|set(top23['members']));ref=True;route='sacv_v1_success';win=None\n        elif comps:\n            win=comps[0];o=list(win['member_ids']);ref=True;route='recurrence_fallback'\n        else:\n            win=None;o=ids;ref=False;route='parent_fallback'\n"""
assert s.count(old)==1, s.count(old)
s=s.replace(old,new,1)
oldret="""        return {'rank':rank,'family_id':str(c['family_id']),'family_hash':str(c['family_hash']),'parent_n':len(ids),'refined':bool(ref and len(o)<len(ids)),'output_n':len(o),'ratio':len(o)/len(ids) if ids else 0.0,'output_ids':o,'annual_admissible_counts':{str(y):len(byyear[y]) for y in YEARS},'annual_top_ids':annual_top,'recurrent_component_count':len(comps),'selected_component':pubcomp(win),'all_component_summaries':[pubcomp(z) for z in comps]}\n"""
newret="""        return {'rank':rank,'family_id':str(c['family_id']),'family_hash':str(c['family_hash']),'parent_n':len(ids),'refined':bool(ref and len(o)<len(ids)),'output_n':len(o),'ratio':len(o)/len(ids) if ids else 0.0,'output_ids':o,'route':route,'original_sacv_validated':bool(top_ref),'annual_admissible_counts':{str(y):len(byyear[y]) for y in YEARS},'annual_top_ids':annual_top,'recurrent_component_count':len(comps),'selected_component':pubcomp(win),'all_component_summaries':[pubcomp(z) for z in comps]}\n"""
assert s.count(oldret)==1, s.count(oldret)
s=s.replace(oldret,newret,1)
s=s.replace('M2D_SACV_EDGE_CONSENSUS_V1','M2D_SACV_FALLBACK_RECURRENCE_V1')
s=s.replace('m2d-sacv-edge-consensus-v1','m2d-sacv-fallback-recurrence-v1')
s=s.replace('edge_consensus_v1','fallback_recurrence_v1')
s=s.replace("'edge_consensus_v1'","'fallback_recurrence_v1'")
p.write_text(s)

for name in ['evaluate_truth.py','run_binding.sh']:
    q=ROOT/name
    x=q.read_text()
    x=x.replace('M2D_SACV_EDGE_CONSENSUS_V1','M2D_SACV_FALLBACK_RECURRENCE_V1')
    x=x.replace('m2d-sacv-edge-consensus-v1','m2d-sacv-fallback-recurrence-v1')
    x=x.replace('orbittrace_m2d_sacv_edge_consensus_v1','orbittrace_m2d_sacv_fallback_recurrence_v1')
    x=x.replace('edge-consensus','fallback-recurrence')
    x=x.replace('EDGE_CONSENSUS','FALLBACK_RECURRENCE')
    q.write_text(x)

for name in ['build_pretruth.py','evaluate_truth.py','run_binding.sh']:
    q=ROOT/name
    print(name,hashlib.sha256(q.read_bytes()).hexdigest(),q.stat().st_size)
