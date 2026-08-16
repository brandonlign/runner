#!/usr/bin/env python3
from __future__ import annotations

import argparse,hashlib,importlib.util,json,math,sys
from pathlib import Path
from typing import Any

STRUCTURAL_SHA="e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497"
INTRINSIC_BLOB="752df8212ce601227f6e9170b0fe994ba06b515d"
MIN_SUPPORT=4


def req(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path,n:str)->Any:
    s=importlib.util.spec_from_file_location(n,p); req(s is not None and s.loader is not None,f'cannot import {p}'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def dsh2(a:dict[str,float],b:dict[str,float])->float:
    e1,q1=float(a['e']),float(a['q_au']); e2,q2=float(b['e']),float(b['q_au'])
    i1,w1,o1=map(math.radians,(float(a['i_deg']),float(a['peri_deg']),float(a['node_deg'])))
    i2,w2,o2=map(math.radians,(float(b['i_deg']),float(b['peri_deg']),float(b['node_deg'])))
    ci=math.cos(i1)*math.cos(i2)+math.sin(i1)*math.sin(i2)*math.cos(o1-o2)
    I=math.acos(max(-1.0,min(1.0,ci)))
    dO=o2-o1; sgn=1.0 if abs(dO)<=math.pi else -1.0; den=math.cos(I/2.0)
    req(abs(den)>1e-14,'degenerate antiparallel orbital planes')
    x=math.cos((i2+i1)/2.0)*math.sin(dO/2.0)/den; x=max(-1.0,min(1.0,x))
    Pi=w2-w1+sgn*2.0*math.asin(x)
    v=(q1-q2)**2+(e1-e2)**2+(2.0*math.sin(I/2.0))**2+(((e1+e2)/2.0)*2.0*math.sin(Pi/2.0))**2
    req(math.isfinite(v) and v>=-1e-14,'invalid D_SH^2'); return max(0.0,float(v))

def frechet(members:list[str],mapping:dict[str,dict[str,float]])->tuple[float,str,str]:
    ids=sorted(map(str,members)); n=len(ids); req(n>=MIN_SUPPORT,'sub-support candidate')
    req(all(eid in mapping and mapping[eid] is not None for eid in ids),'candidate missing orbit')
    sums=[0.0]*n
    h=hashlib.sha256()
    for j in range(n):
        for k in range(j+1,n):
            d=dsh2(mapping[ids[j]],mapping[ids[k]]); sums[j]+=d; sums[k]+=d
            h.update(ids[j].encode()); h.update(b'|'); h.update(ids[k].encode()); h.update(b'='); h.update(float(d).hex().encode()); h.update(b'\n')
    means=[x/float(n-1) for x in sums]; best=min(means); med=min(ids[j] for j,v in enumerate(means) if abs(v-best)<=1e-15)
    return float(best),med,h.hexdigest()

def orbital_topomodal(structural:Any,events:list[dict[str,Any]],mapping:dict[str,dict[str,float]])->tuple[list[dict[str,Any]],dict[str,Any]]:
    candidates,meta=structural.topomodal_candidates(events); rows={str(r['family_hash']):r for r in meta['candidate_rows']}; req(len(rows)==len(candidates),'candidate metadata mismatch')
    out=[]
    for members in candidates:
        ids=sorted(members); fh=structural.member_hash(frozenset(ids)); req(fh in rows,'family hash missing'); sr=rows[fh]
        energy,medoid,pair_sha=frechet(ids,mapping)
        out.append({'family_id':hashlib.sha256(('ORBF1|'+'|'.join(ids)).encode()).hexdigest()[:20],'family_hash':fh,'event_ids':ids,'member_count':len(ids),'first_node':int(sr['first_node']),'is_root':bool(sr['is_root']),'orbital_frechet_energy':energy,'orbital_medoid_event_id':medoid,'pairwise_dsh2_sha256':pair_sha})
    out.sort(key=lambda r:(0 if r['is_root'] else 1,float(r['orbital_frechet_energy']),str(r['family_hash'])))
    for rank,r in enumerate(out,1):r['rank']=rank
    req([r['rank'] for r in out]==list(range(1,len(out)+1)),'rank continuity')
    return out,{'candidate_count':len(out),'candidate_rows':meta['candidate_rows'],'leaf_count':meta['leaf_count'],'internal_node_count':meta['internal_node_count'],'root_count':meta['root_count'],'finite_persistence_point_count':meta['finite_persistence_point_count']}

def main()->int:
    ap=argparse.ArgumentParser()
    for n in ('base-generator','intrinsic-runner','structural-runner','structural-result-json','orbit-mapping','availability-result','local-orderstat-source','parent-runner','quality-source','support-source-parts','candidate-payload','baseline-payload','scorer-parts','v8-result-json'):ap.add_argument('--'+n,type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.structural_result_json)==STRUCTURAL_SHA,'#1284 structural artifact changed')
    availability=json.loads(a.availability_result.read_text()); req(availability['verdict']=='PASS_TOPOMODAL_ORBIT_AVAILABILITY_V1','orbit availability not activated'); req(all(v['all_events_usable'] for v in availability['subset_stats'].values()),'incomplete orbit panel')
    req(sha(a.orbit_mapping)==availability['orbit_mapping_sha256'],'orbit mapping hash'); mapping=json.loads(a.orbit_mapping.read_text()); req(len(mapping)==23080 and all(v is not None for v in mapping.values()),'orbit mapping incomplete')
    base=load(a.base_generator,'orbf_base'); structural=load(a.structural_runner,'orbf_structural')
    base.rankdensity_topomodal=lambda parent,structural_mod,events: orbital_topomodal(structural_mod,events,mapping)
    old=sys.argv[:]
    sys.argv=[str(a.base_generator),'--intrinsic-runner',str(a.intrinsic_runner),'--structural-runner',str(a.structural_runner),'--structural-result-json',str(a.structural_result_json),'--local-orderstat-source',str(a.local_orderstat_source),'--parent-runner',str(a.parent_runner),'--quality-source',str(a.quality_source),'--support-source-parts',str(a.support_source_parts),'--candidate-payload',str(a.candidate_payload),'--baseline-payload',str(a.baseline_payload),'--scorer-parts',str(a.scorer_parts),'--v8-result-json',str(a.v8_result_json),'--output',str(a.output)]
    try:rc=int(base.main())
    finally:sys.argv=old
    req(rc==0,'base prelabel harness failed')
    p=a.output/'RANKDENSITY_TOPOMODAL_V1_PRELABEL.json'; pre=json.loads(p.read_text()); expected={(int(x['denominator']),int(x['bucket'])):x for x in json.loads(a.structural_result_json.read_text())['fits']}
    for row in pre['subsets']:
        ex=expected[(int(row['denominator']),int(row['bucket']))]; req(row['successor_summary']['candidate_count']==ex['topomodal']['candidate_count'] and row['successor_summary']['candidate_rows']==ex['topomodal']['candidate_rows'],'#1284 membership changed')
    pre['schema']='ORBITTRACE_TOPOMODAL_ORBITAL_FRECHET_V1_PRELABEL'; pre['scientific_role']='PRELABEL_TOPOMODAL_ORBITAL_FRECHET_V1'; pre['structural_result_sha256']=STRUCTURAL_SHA; pre['orbit_mapping_sha256']=availability['orbit_mapping_sha256']; pre['intrinsic_source_blob']=INTRINSIC_BLOB
    pre['configuration']={'candidate_generator':'exact_1284_complete_topomodal_hierarchy','density':'exact_1284_radius_degree_over_subset_n','graph':'exact_1284_physical_radius_1','min_candidate_support':4,'orbital_dissimilarity':'Southworth_Hawkins_D_SH_squared_exact_appendix_formula','orbital_center':'observed_member_Frechet_medoid','orbital_energy':'minimum_mean_D_SH_squared_to_all_other_candidate_members','ranking':'roots_first_then_orbital_frechet_energy_ascending_then_family_hash','equal_budget':'recurrent_candidate_count'}
    pre['shower_truth_used']=False; pre['target_information_access']=False; pre['method_parameter_selection_from_result']=False
    out=a.output/'TOPOMODAL_ORBITAL_FRECHET_V1_PRELABEL.json'; out.write_text(json.dumps(pre,indent=2,sort_keys=True,allow_nan=False)+'\n'); p.unlink(); print(json.dumps({'prelabel_sha256':sha(out),'orbit_mapping_sha256':availability['orbit_mapping_sha256'],'candidate_budget_shortage_any_panel':pre['candidate_budget_shortage_any_panel'],'cross_scale':pre['cross_scale']},indent=2,sort_keys=True)); return 0
if __name__=='__main__':raise SystemExit(main())
