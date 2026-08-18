#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json, math
from pathlib import Path
from typing import Any
import numpy as np
from scipy.spatial import cKDTree

YEARS=(2022,2023); BLIND=(20.0,55.0)
EXPECTED_EVENTS_TOTAL=738682; EXPECTED_EVENTS_BY_YEAR={'2022':315024,'2023':423658}
EXPECTED_PARENT_PRELABEL_SHA256='efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993'
EXPECTED_PARENT_RESULT_SHA256='ca6aeed2b82739003ea5d39b59e869df876de2962164344a938fe4935ea38711'
EXPECTED_PARENT_COUNT=2094
EXPECTED_PARENT_ORDERED_MEMBERSHIP_SHA256='e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2'
EXPECTED_PROTOCOL_BLOB='c903e91acd3b916e646dec5fa3bf2c2c25cb8da5'
H_SOL=2.0*math.sin(math.radians(5.0)/2.0); H_RAD=2.0*math.sin(math.radians(4.0)/2.0); H_LOGV=math.log(1.1)

def req(x:bool,m:str)->None:
    if not x: raise RuntimeError(m)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def blob(p:Path)->str:
    b=p.read_bytes();return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
def membership_sha(ids:list[str])->str:return hashlib.sha256('|'.join(sorted(ids)).encode()).hexdigest()
def ordered_sha(rows:list[dict[str,Any]])->str:return hashlib.sha256('\n'.join('|'.join(str(x) for x in r['event_ids']) for r in rows).encode()).hexdigest()
def embedding(events:list[dict[str,Any]])->np.ndarray:
    sol=np.radians(np.asarray([float(e['sol']) for e in events]));lon=np.radians(np.asarray([float(e['lon']) for e in events]));lat=np.radians(np.asarray([float(e['lat']) for e in events]));vg=np.asarray([float(e['vg']) for e in events]);req(np.all(np.isfinite(vg)) and np.all(vg>0),'invalid speed');cl=np.cos(lat)
    z=np.column_stack([np.cos(sol)/H_SOL,np.sin(sol)/H_SOL,cl*np.cos(lon)/H_RAD,cl*np.sin(lon)/H_RAD,np.sin(lat)/H_RAD,np.log(vg)/H_LOGV]).astype(float)
    req(z.shape==(len(events),6) and np.all(np.isfinite(z)),'invalid embedding');return z

def core(parent_ids:list[str], event_by_id:dict[str,dict[str,Any]])->tuple[list[str],dict[str,Any]]:
    ids=sorted(str(x) for x in parent_ids); req(ids and len(ids)==len(set(ids)),'bad parent ids')
    ev=[event_by_id[x] for x in ids]; years=np.asarray([int(e['year']) for e in ev]);req(set(years.tolist())==set(YEARS),'parent missing year')
    z=embedding(ev); d=np.empty(len(ids),dtype=float)
    for y,other in ((2022,2023),(2023,2022)):
        ii=np.flatnonzero(years==y); jj=np.flatnonzero(years==other);req(len(ii)>0 and len(jj)>0,'empty annual side')
        tree=cKDTree(z[jj]); dd,_=tree.query(z[ii],k=1,p=2.0,eps=0.0,workers=1);d[ii]=np.asarray(dd,dtype=float)
    req(np.all(np.isfinite(d)) and np.all(d>=0),'invalid cross-year distances')
    q1=float(np.quantile(d,0.25,method='linear'));q3=float(np.quantile(d,0.75,method='linear'));iqr=q3-q1;req(iqr>=0 and np.isfinite(iqr),'invalid iqr');fence=float(q3+1.5*iqr);req(np.isfinite(fence) and fence>=q3,'invalid fence')
    keep=d<=fence;raw=[ids[i] for i in np.flatnonzero(keep)];raw_counts={str(y):sum(int(event_by_id[x]['year'])==y for x in raw) for y in YEARS};fallback=not all(raw_counts[str(y)]>=4 for y in YEARS);final=ids if fallback else raw
    removed=[ids[i] for i in np.flatnonzero(~keep)]
    return final,{'parent_member_count':len(ids),'parent_events_by_year':{str(y):int(np.sum(years==y)) for y in YEARS},'q1':q1,'q3':q3,'iqr':iqr,'tukey_multiplier':1.5,'fence':fence,'distance_min':float(np.min(d)),'distance_median':float(np.median(d)),'distance_max':float(np.max(d)),'raw_core_member_count':len(raw),'raw_core_events_by_year':raw_counts,'fallback':fallback,'decision':'PARENT_FALLBACK_ANNUAL_SUPPORT_LT4' if fallback else 'TUKEY_CORE','removed_member_count':0 if fallback else len(removed),'raw_removed_member_count':len(removed),'retention_fraction':len(final)/len(ids),'final_membership_sha256':membership_sha(final)}

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument('--protocol',type=Path,required=True);ap.add_argument('--geometry',type=Path,required=True);ap.add_argument('--parent-prelabel',type=Path,required=True);ap.add_argument('--parent-result',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    req(blob(a.protocol)==EXPECTED_PROTOCOL_BLOB,'protocol changed');req(sha(a.parent_prelabel)==EXPECTED_PARENT_PRELABEL_SHA256,'parent prelabel changed');req(sha(a.parent_result)==EXPECTED_PARENT_RESULT_SHA256,'parent result changed')
    pp=json.loads(a.parent_prelabel.read_text());pr=json.loads(a.parent_result.read_text());req(pp['scientific_role']=='PRELABEL_FROZEN_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1','wrong parent role');req(pr['verdict']=='PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_GMN_DEVELOPMENT','parent not pass');parents=list(pp['successor_candidates']);req(len(parents)==EXPECTED_PARENT_COUNT,'parent count');req(ordered_sha(parents)==EXPECTED_PARENT_ORDERED_MEMBERSHIP_SHA256 and pp['successor_ordered_membership_sha256']==EXPECTED_PARENT_ORDERED_MEMBERSHIP_SHA256,'parent ordered membership changed')
    g=json.loads(a.geometry.read_text());req(g['schema']=='ORBITTRACE_RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1_GEOMETRY' and g['scientific_role']=='LABEL_FREE_TARGET_EXCLUDED_GMN_GEOMETRY_ONLY','wrong geometry');req(g['events_total']==EXPECTED_EVENTS_TOTAL and g['events_by_year']==EXPECTED_EVENTS_BY_YEAR,'geometry counts');req(g['blind_exclusion']==list(BLIND) and g['shower_truth_exported'] is False,'geometry firewall');events=list(g['events']);by={str(e['id']):e for e in events};req(len(by)==EXPECTED_EVENTS_TOTAL,'geometry id count');req(all(not(BLIND[0]<=float(e['sol'])<=BLIND[1]) for e in events),'protected event survived')
    seen=set();succ=[];diag=[];changed=0;fallbacks=0;removed=0
    for rank,p in enumerate(parents,1):
        ids=[str(x) for x in p['event_ids']];req(set(ids).issubset(by),'parent outside geometry');req(seen.isdisjoint(ids),'parent overlap');seen.update(ids)
        final,ds=core(ids,by);chg=final!=sorted(ids);changed+=int(chg);fallbacks+=int(ds['fallback']);removed+=len(ids)-len(final)
        succ.append({'rank':rank,'family_id':str(p['family_id']),'parent_family_id':str(p['family_id']),'parent_node_id':int(p['node_id']),'event_ids':final,'member_count':len(final),'representation_changed':chg})
        diag.append({'rank':rank,'family_id':str(p['family_id']),'parent_membership_sha256':membership_sha(sorted(ids)),'parent_event_ids':sorted(ids),'final_event_ids':final,'representation_changed':chg,'crossyear_tukey':ds})
        if rank<=10 or rank%100==0:print(f'[tukey-core] rank={rank}/{len(parents)} n={len(ids)} final={len(final)} changed={chg}',flush=True)
    req(len(succ)==EXPECTED_PARENT_COUNT and [x['rank'] for x in succ]==list(range(1,EXPECTED_PARENT_COUNT+1)),'slot order changed');fs=set();
    for p,s in zip(parents,succ):req(set(s['event_ids']).issubset(set(p['event_ids'])),'successor escaped parent');req(fs.isdisjoint(s['event_ids']),'successor overlap');fs.update(s['event_ids'])
    req(changed>0 and removed>0,'mechanism vacuous')
    ret=np.asarray([d['crossyear_tukey']['retention_fraction'] for d in diag],float);fences=np.asarray([d['crossyear_tukey']['fence'] for d in diag],float)
    pre={'schema':'ORBITTRACE_RECURRENT_CROSSYEAR_TUKEY_CORE_V1_PRELABEL','scientific_role':'PRELABEL_TARGET_EXCLUDED_FIXED_RANK_CROSSYEAR_TUKEY_CORE','parent_binding_run_id':31852836840,'parent_binding_artifact_id':9238142199,'parent_prelabel_sha256':EXPECTED_PARENT_PRELABEL_SHA256,'parent_result_sha256':EXPECTED_PARENT_RESULT_SHA256,'parent_ordered_membership_sha256':EXPECTED_PARENT_ORDERED_MEMBERSHIP_SHA256,'parent_candidate_count':EXPECTED_PARENT_COUNT,'successor_candidate_count':EXPECTED_PARENT_COUNT,'catalogue_slot_order_unchanged':True,'every_successor_subset_of_same_rank_parent':True,'successor_slots_pairwise_event_disjoint':True,'mechanism_active':True,'changed_slot_count':changed,'fallback_slot_count':fallbacks,'total_removed_events':removed,'changed_rank_windows':{'top25':sum(d['representation_changed'] and d['rank']<=25 for d in diag),'top50':sum(d['representation_changed'] and d['rank']<=50 for d in diag),'top100':sum(d['representation_changed'] and d['rank']<=100 for d in diag),'top500':sum(d['representation_changed'] and d['rank']<=500 for d in diag)},'retention_fraction_summary':{'min':float(ret.min()),'median':float(np.median(ret)),'mean':float(ret.mean()),'p90':float(np.quantile(ret,.9)),'max':float(ret.max())},'fence_summary':{'min':float(fences.min()),'median':float(np.median(fences)),'mean':float(fences.mean()),'max':float(fences.max())},'parent_candidates':[{'rank':i+1,'family_id':str(p['family_id']),'node_id':int(p['node_id']),'event_ids':[str(x) for x in p['event_ids']]} for i,p in enumerate(parents)],'successor_candidates':succ,'diagnostics':diag,'successor_ordered_membership_sha256':ordered_sha(succ),'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'asfn_event_level_access':False,'efn_event_level_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'post_result_parameter_search':False}
    a.output.write_text(json.dumps(pre,indent=2,sort_keys=True,allow_nan=False)+'\n');print(json.dumps({'verdict':'PASS_RECURRENT_CROSSYEAR_TUKEY_CORE_V1_PRETRUTH','changed_slot_count':changed,'fallback_slot_count':fallbacks,'total_removed_events':removed,'changed_rank_windows':pre['changed_rank_windows'],'successor_ordered_membership_sha256':pre['successor_ordered_membership_sha256']},indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
