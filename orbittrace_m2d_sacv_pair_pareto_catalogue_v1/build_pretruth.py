from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any
import orbittrace_m2d_sacv_fallback_recurrence_v1.build_pretruth as fr

FAIR_SHA='8b0f4629659c1bfd750747303ad04ff67355adf66d4dbe474ce7fba788f5bae5'
SACV_SHA='77528fbec227bf8d8d311b9054c46db43668d7f12e9460b85db680c4a6ce927b'
ROLE='TARGET_EXCLUDED_SACV_ALL_VALIDATED_PAIRS_THREE_VIEW_PARETO_FROZEN_BEFORE_SHOWER_TRUTH'
SCHEMA='ORBITTRACE_M2D_SACV_PAIR_PARETO_CATALOGUE_V1_GMN_PRETRUTH'

def req(x:bool,m:str)->None:
    if not x: raise RuntimeError(m)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def msha(ids:list[str])->str:return hashlib.sha256('|'.join(sorted(map(str,ids))).encode()).hexdigest()
def psha(fid:str,u:str,v:str)->str:return hashlib.sha256((fid+'|'+u+'|'+v).encode()).hexdigest()
def sk(p:dict[str,Any])->dict[tuple[int,int],dict[str,Any]]:return {(int(s['denominator']),int(s['bucket'])):s for s in p['subsets']}

class Fenwick2DMax:
    def __init__(self,n:int,m:int):self.a=[[0]*(m+2) for _ in range(n+2)]
    def query(self,i:int,j:int)->int:
        z=0
        while i>0:
            jj=j
            while jj>0:z=max(z,self.a[i][jj]);jj-=jj&-jj
            i-=i&-i
        return z
    def update(self,i:int,j:int,v:int)->None:
        while i<len(self.a):
            jj=j
            while jj<len(self.a[i]):
                if v>self.a[i][jj]:self.a[i][jj]=v
                jj+=jj&-jj
            i+=i&-i

def pareto_depth(rows:list[dict[str,Any]])->None:
    if not rows:return
    fw=Fenwick2DMax(max(int(r['r22']) for r in rows)+1,max(int(r['r23']) for r in rows)+1)
    ordered=sorted(rows,key=lambda r:(int(r['parent_rank']),int(r['r22']),int(r['r23']),r['pair_hash']))
    for r in ordered:
        i,j=int(r['r22']),int(r['r23']);d=1+fw.query(i,j);r['pareto_depth']=d;fw.update(i,j,d)

def main()->int:
    ap=argparse.ArgumentParser()
    for n in ('fair-pretruth','geometry','sacv-v1-pretruth','output'):ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    req(sha(a.fair_pretruth)==FAIR_SHA,'fair pretruth changed');req(sha(a.sacv_v1_pretruth)==SACV_SHA,'SACV oracle changed')
    fair=json.loads(a.fair_pretruth.read_text());geom=json.loads(a.geometry.read_text());oracle=json.loads(a.sacv_v1_pretruth.read_text())
    req(fair['scientific_role']=='TARGET_EXCLUDED_GMN_SPARSE_LITERATURE_COMPARATORS_FROZEN_BEFORE_TRUTH','fair role')
    req(oracle['scientific_role']=='TARGET_EXCLUDED_SACV_MEMBERSHIPS_FROZEN_BEFORE_SHOWER_TRUTH','SACV role')
    req(oracle['shower_truth_used'] is False and oracle['target_information_access'] is False,'SACV firewall')
    req(geom['scientific_role']=='LABEL_FREE_TARGET_EXCLUDED_GMN_GEOMETRY_ONLY' and geom['shower_truth_exported'] is False,'geometry firewall')
    events=list(geom['events']);req(len(events)==fr.EXPECTED_TOTAL,'geometry count');rt=fr.Runtime(events)
    osub=sk(oracle); out=[]; total_edges=total_unique=total_dups=0
    for fs in fair['subsets']:
        d,b=int(fs['denominator']),int(fs['bucket']);parents=list(fs['successor_candidates']);orefs=list(osub[(d,b)]['extractions']);req(len(parents)==len(orefs),f'oracle count d{d}b{b}')
        pairs=[]; member_lookup={}; admiss22=admiss23=0
        for pos,(c,o) in enumerate(zip(parents,orefs),1):
            raw=rt.proc(c,pos);req(int(raw['rank'])==pos==int(o['rank']),'rank drift');req(str(raw['family_id'])==str(c['family_id'])==str(o['family_id']),'family drift')
            primary=sorted(map(str,raw['output_ids'])) if raw['route']=='sacv_v1_success' else sorted(map(str,c['event_ids']))
            req(primary==sorted(map(str,o['output_ids'])),f'SACV primary drift d{d}b{b}/{pos}')
            nodes={str(n['node_id']):n for n in raw.get('all_graph_nodes',[])}; edges=list(raw.get('all_graph_edges',[]))
            for nid,nrow in nodes.items(): member_lookup[(str(c['family_id']),nid)]=tuple(sorted(map(str,nrow['members'])))
            counts=raw['annual_admissible_counts'];admiss22+=int(counts['2022']);admiss23+=int(counts['2023'])
            for e in edges:
                u,v=str(e['u']),str(e['v']);req(u in nodes and v in nodes,'edge node missing');nu,nv=nodes[u],nodes[v]
                req(int(nu['hypothesis_year'])==2022 and int(nv['hypothesis_year'])==2023,'edge year drift')
                ids=sorted(set(map(str,nu['members']))|set(map(str,nv['members'])));req(ids,'empty pair')
                pairs.append({'parent_rank':pos,'family_id':str(c['family_id']),'u':u,'v':v,'r22':int(nu['local_rank']),'r23':int(nv['local_rank']),'pair_hash':psha(str(c['family_id']),u,v),'member_count':len(ids),'membership_sha256':msha(ids)})
        pareto_depth(pairs)
        ranked=sorted(pairs,key=lambda r:(int(r['pareto_depth']),max(int(r['r22']),int(r['r23'])),min(int(r['r22']),int(r['r23'])),int(r['parent_rank']),r['pair_hash']))
        seen=set();uniq=[];dups=0
        for r in ranked:
            h=r['membership_sha256']
            if h in seen:dups+=1;continue
            seen.add(h);q=dict(r);q['catalogue_rank']=len(uniq)+1;uniq.append(q)
        caps={};short={}
        for y in fr.YEARS:
            for comp in ('sugar2017','hdbscan2025'):
                k=len(fair['panels'][f'd{d}_b{b}_y{y}'][comp]['clusters']);caps[f'{y}:{comp}']=k;short[f'{y}:{comp}']=max(0,k-len(uniq))
        export_k=max(caps.values(),default=0);succ=[]
        for q0 in uniq[:export_k]:
            q=dict(q0);fid=str(q['family_id']);u=str(q['u']);v=str(q['v'])
            ids=sorted(set(member_lookup[(fid,u)])|set(member_lookup[(fid,v)]));req(msha(ids)==q['membership_sha256'],'membership reconstruction drift')
            q['event_ids']=ids;succ.append(q)
        req([x['catalogue_rank'] for x in succ]==list(range(1,len(succ)+1)),'catalogue rank gap')
        adjacent_overlap=0
        for x,y in zip(succ,succ[1:]):
            if set(x['event_ids']).intersection(y['event_ids']):adjacent_overlap+=1
        out.append({'denominator':d,'bucket':b,'parent_candidate_count':len(parents),'annual_admissible_hypotheses_total':{'2022':admiss22,'2023':admiss23},'validated_pair_count':len(pairs),'pareto_layer_count':max([int(x['pareto_depth']) for x in pairs],default=0),'duplicate_membership_count':dups,'unique_candidate_count':len(uniq),'exported_fixed_capacity_prefix_count':len(succ),'adjacent_exported_rank_overlap_count':adjacent_overlap,'comparator_capacities':caps,'capacity_shortfall':short,'successor_candidates':succ,'annual_event_ids':fs['annual_event_ids']})
        total_edges+=len(pairs);total_unique+=len(uniq);total_dups+=dups
        print(json.dumps({'subset':f'd{d}b{b}','pairs':len(pairs),'unique':len(succ),'dups':dups,'layers':out[-1]['pareto_layer_count'],'shortfall':short},sort_keys=True),flush=True)
    payload={'schema':SCHEMA,'scientific_role':ROLE,'fair_pretruth_sha256':FAIR_SHA,'sacv_v1_pretruth_sha256':SACV_SHA,'blind_exclusion':fr.BLIND,'configuration':{'candidate':'every exact validated 2022x2023 SACV edge union','pareto_objectives':['parent_rank','sacv_2022_local_rank','sacv_2023_local_rank'],'tie_order':['pareto_depth','max_local_rank','min_local_rank','parent_rank','stable_pair_hash'],'dedup':'exact membership after ranking, earliest provenance retained'},'summary':{'validated_pairs':total_edges,'unique_candidates':total_unique,'duplicate_memberships':total_dups},'subsets':out,'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_scientific_access':False,'post_result_parameter_search':False}
    a.output.write_text(json.dumps(payload,separators=(',',':'),sort_keys=True,allow_nan=False)+'\n');print(json.dumps({'verdict':'PASS_PAIR_PARETO_CATALOGUE_PRETRUTH','sha256':sha(a.output),'summary':payload['summary']},sort_keys=True),flush=True);return 0
if __name__=='__main__':raise SystemExit(main())
