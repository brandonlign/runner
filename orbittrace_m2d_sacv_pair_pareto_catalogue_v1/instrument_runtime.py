from pathlib import Path
import hashlib

P=Path('orbittrace_m2d_sacv_fallback_recurrence_v1/build_pretruth.py')
s=P.read_text()
anchor="""        def pubcomp(z):\n            if z is None:return None\n            return {k:v for k,v in z.items() if k not in ('nodes','member_ids')}\n"""
insert="""        local_rank={}\n        for yy in YEARS:\n            tag=str(yy)[-2:]\n            for ii,hh in enumerate(byyear[yy],1): local_rank[tag+':'+hh['id']]=ii\n        all_graph_nodes=[{'node_id':n,'hypothesis_year':int(nodes[n]['year']),'local_rank':int(local_rank[n]),'members':sorted(map(str,nodes[n]['members']))} for n in sorted(nodes)]\n        all_graph_edges=[{'u':'22:'+e['a'],'v':'23:'+e['b'],'d':float(e['d']),'ab':int(e['ab']),'ba':int(e['ba'])} for e in edges]\n        def pubcomp(z):\n            if z is None:return None\n            return {k:v for k,v in z.items() if k not in ('nodes','member_ids')}\n"""
if s.count(anchor)!=1: raise RuntimeError(f'pubcomp anchor count {s.count(anchor)}')
s=s.replace(anchor,insert,1)
old="""'selected_component':pubcomp(win),'all_component_summaries':[pubcomp(z) for z in comps]}\n"""
new="""'selected_component':pubcomp(win),'all_component_summaries':[pubcomp(z) for z in comps],'all_graph_nodes':all_graph_nodes,'all_graph_edges':all_graph_edges}\n"""
if s.count(old)!=1: raise RuntimeError(f'return anchor count {s.count(old)}')
s=s.replace(old,new,1)
P.write_text(s)
print('instrumented_runtime_sha256',hashlib.sha256(P.read_bytes()).hexdigest(),P.stat().st_size)
