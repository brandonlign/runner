#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import orbittrace_m2d_sacv_rc_v1.build_pretruth as base

class FastRuntime(base.Runtime):
    """Exact RC-v1 semantics with hypothesis-local support cached once."""
    def proc(self,c,rank):
        ids=sorted(map(str,c['event_ids']));base.req(all(x in self.byid for x in ids),f'missing parent geometry rank {rank}')
        src={2022:self.enumerate_sources(ids,2022),2023:self.enumerate_sources(ids,2023)};nodes=[]
        for y in base.YEARS:
            other=2023 if y==2022 else 2022
            for h in src[y]:
                h['members_all']=self.members(ids,h['center'],h['radius'])
                h['cross_support']=sum(self.byid[eid]['year']==other for eid in h['members_all'])
                nodes.append((y,h['id']))
        bykey={(y,h['id']):h for y in base.YEARS for h in src[y]};edges=[];adj={n:set() for n in nodes}
        for a in src[2022]:
            if a['cross_support']<base.MIN_SUPPORT:continue
            for b in src[2023]:
                if b['cross_support']<base.MIN_SUPPORT:continue
                d=float(base.np.linalg.norm(a['center']-b['center']))
                if d>a['radius']+1e-12 or d>b['radius']+1e-12:continue
                ab=int(a['cross_support']);ba=int(b['cross_support']);u=(2022,a['id']);v=(2023,b['id']);adj[u].add(v);adj[v].add(u)
                edges.append({'a':a['id'],'b':b['id'],'d':d,'ab':ab,'ba':ba,'min_cross_support':min(ab,ba),'sum_cross_support':ab+ba,'min_excess':min(float(a['excess']),float(b['excess'])),'sum_excess':float(a['excess'])+float(b['excess'])})
        active={n for n in nodes if adj[n]};seen=set();components=[]
        for seed in sorted(active):
            if seed in seen:continue
            stack=[seed];seen.add(seed);cn=[]
            while stack:
                u=stack.pop();cn.append(u)
                for v in sorted(adj[u]):
                    if v not in seen:seen.add(v);stack.append(v)
            cset=set(cn);ce=[e for e in edges if (2022,e['a']) in cset and (2023,e['b']) in cset];mids=sorted(set(eid for n in cn for eid in bykey[n]['members_all']));score=(len(ce),len(cn),sum(int(e['min_cross_support']) for e in ce),sum(float(e['min_excess']) for e in ce));components.append({'nodes':cn,'edges':ce,'member_ids':mids,'score':score})
        components.sort(key=lambda x:(-x['score'][0],-x['score'][1],-x['score'][2],-x['score'][3],hashlib.sha256('\n'.join(x['member_ids']).encode()).hexdigest()));sel=components[0] if components else None;o=sel['member_ids'] if sel else ids
        def pub(h):return {k:v for k,v in h.items() if k not in ('center','members_all','cross_support')}
        pcs=[{'node_count':len(z['nodes']),'edge_count':len(z['edges']),'nodes':[{'year':y,'id':eid} for y,eid in sorted(z['nodes'])],'edges':z['edges'],'member_count':len(z['member_ids']),'member_ids':z['member_ids'],'score':list(z['score'])} for z in components]
        return {'rank':rank,'family_id':str(c['family_id']),'family_hash':str(c['family_hash']),'parent_n':len(ids),'refined':bool(sel),'output_n':len(o),'ratio':len(o)/len(ids) if ids else 0.0,'output_ids':o,'hypothesis_counts':{str(y):len(src[y]) for y in base.YEARS},'validated_edge_count':len(edges),'component_count':len(components),'selected_component_index':0 if sel else None,'selected_component_edge_count':len(sel['edges']) if sel else 0,'selected_component_node_count':len(sel['nodes']) if sel else 0,'components':pcs,'hypotheses':{str(y):[pub(h) for h in src[y]] for y in base.YEARS}}

base.Runtime=FastRuntime
if __name__=='__main__':raise SystemExit(base.main())
