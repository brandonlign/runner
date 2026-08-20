#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
from typing import Any
import numpy as np
from scipy.spatial import cKDTree

YEARS=(2022,2023);RMAX=1.0;MIN_SUPPORT=4;CONTAM_MAX=0.10
DELTAS=np.concatenate(([0.0],np.arange(60.0,301.0,10.0)))
H_SOL=2*math.sin(math.radians(5.0)/2.0);H_RAD=2*math.sin(math.radians(4.0)/2.0);H_LOGV=math.log(1.1)
FAIR_SHA='8b0f4629659c1bfd750747303ad04ff67355adf66d4dbe474ce7fba788f5bae5'
EXPECTED_TOTAL=738682;EXPECTED_COUNTS={'2022':315024,'2023':423658};BLIND=[20.0,55.0]

def req(x:bool,msg:str)->None:
    if not x: raise RuntimeError(msg)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def normalize(e:dict[str,Any])->dict[str,Any]:
    return {'id':str(e['id']),'year':int(e['year']),'sol':float(e['sol']),'sun_lon':float(e.get('sun_lon',e.get('lon'))),'ecl_lat':float(e.get('ecl_lat',e.get('lat'))),'vg':float(e['vg'])}
def full_embed(rows):
    sol=np.radians(np.array([float(e['sol']) for e in rows]));lon=np.radians(np.array([float(e['sun_lon']) for e in rows]));lat=np.radians(np.array([float(e['ecl_lat']) for e in rows]));vg=np.array([float(e['vg']) for e in rows]);cl=np.cos(lat)
    z=np.column_stack([np.cos(sol)/H_SOL,np.sin(sol)/H_SOL,cl*np.cos(lon)/H_RAD,cl*np.sin(lon)/H_RAD,np.sin(lat)/H_RAD,np.log(vg)/H_LOGV]);req(np.all(np.isfinite(z)),'nonfinite full geometry');return z
def static_embed(rows):
    lon=np.radians(np.array([float(e['sun_lon']) for e in rows]));lat=np.radians(np.array([float(e['ecl_lat']) for e in rows]));vg=np.array([float(e['vg']) for e in rows]);cl=np.cos(lat)
    z=np.column_stack([cl*np.cos(lon)/H_RAD,cl*np.sin(lon)/H_RAD,np.sin(lat)/H_RAD,np.log(vg)/H_LOGV]);req(np.all(np.isfinite(z)),'nonfinite static geometry');return z

class Runtime:
    def __init__(self,events):
        self.byyear={y:[] for y in YEARS};self.byid={}
        for e0 in events:
            e=normalize(e0);req(e['year'] in YEARS,'unexpected year');self.byyear[e['year']].append(e);self.byid[e['id']]=e
        req(len(self.byid)==len(events),'duplicate ids')
        for y in YEARS:self.byyear[y].sort(key=lambda e:e['id'])
        self.F={y:full_embed(self.byyear[y]) for y in YEARS};self.S={y:static_embed(self.byyear[y]) for y in YEARS};self.stree={y:cKDTree(self.S[y]) for y in YEARS};self.uidx={y:{e['id']:i for i,e in enumerate(self.byyear[y])} for y in YEARS};self.solrad={y:np.radians(np.array([float(e['sol']) for e in self.byyear[y]])) for y in YEARS}
    def analog_distance_sets(self,e,year):
        cs=static_embed([e])[0];inds=np.asarray(self.stree[year].query_ball_point(cs,r=RMAX),int)
        if len(inds)==0:return [np.empty(0)]*len(DELTAS)
        sd2=np.sum((self.S[year][inds]-cs)**2,axis=1);usol=self.solrad[year][inds];csol=np.radians((float(e['sol'])+DELTAS)%360.0);solar2=(2.0-2.0*np.cos(usol[:,None]-csol[None,:]))/(H_SOL*H_SOL);d2=sd2[:,None]+solar2
        return [np.sort(np.sqrt(d2[d2[:,j]<=RMAX*RMAX+1e-12,j])) for j in range(len(DELTAS))]
    def enumerate_sources(self,ids,year):
        ids=sorted(eid for eid in ids if eid in self.uidx[year])
        if len(ids)<MIN_SUPPORT:return []
        pF=np.array([self.F[year][self.uidx[year][eid]] for eid in ids]);pt=cKDTree(pF);neigh=pt.query_ball_point(pF,r=RMAX);out=[]
        for i,eid in enumerate(ids):
            pind=np.asarray(neigh[i],int)
            if len(pind)<MIN_SUPPORT:continue
            c=pF[i];pd=np.sort(np.linalg.norm(pF[pind]-c,axis=1));radii=np.unique(np.concatenate([pd[MIN_SUPPORT-1:],[RMAX]]));radii=radii[radii<=RMAX+1e-12];ds=self.analog_distance_sets(self.byid[eid],year);obs=ds[0]
            if not len(obs):continue
            nobs=np.searchsorted(obs,radii+1e-12,'right').astype(float);bg=np.vstack([np.searchsorted(a,radii+1e-12,'right') for a in ds[1:]]).mean(axis=0);ps=np.searchsorted(pd,radii+1e-12,'right');contam=np.divide(bg,nobs,out=np.full_like(bg,np.inf),where=nobs>0);excess=nobs-bg;ok=(ps>=MIN_SUPPORT)&(contam<=CONTAM_MAX)&(excess>0)
            if not np.any(ok):continue
            k=np.flatnonzero(ok)[-1];r=float(radii[k]);out.append({'id':eid,'radius':r,'parent_support':int(ps[k]),'field_count':int(nobs[k]),'analog_mean':float(bg[k]),'contamination':float(contam[k]),'excess':float(excess[k]),'center':c})
        out.sort(key=lambda x:x['id']);return out
    def members(self,ids,center,r,year=None):
        out=[]
        for eid in ids:
            e=self.byid[eid]
            if year is not None and e['year']!=year:continue
            if np.linalg.norm(self.F[e['year']][self.uidx[e['year']][eid]]-center)<=r+1e-12:out.append(eid)
        return out
    def proc(self,c,rank):
        ids=sorted(map(str,c['event_ids']));req(all(x in self.byid for x in ids),f'missing parent geometry rank {rank}')
        src={2022:self.enumerate_sources(ids,2022),2023:self.enumerate_sources(ids,2023)}
        for y in YEARS:
            other=2023 if y==2022 else 2022
            for h in src[y]:
                h['members_all']=self.members(ids,h['center'],h['radius'])
                h['cross_support']=sum(self.byid[eid]['year']==other for eid in h['members_all'])
        pairs=[]
        for a in src[2022]:
            if a['cross_support']<MIN_SUPPORT:continue
            for b in src[2023]:
                if b['cross_support']<MIN_SUPPORT:continue
                d=float(np.linalg.norm(a['center']-b['center']))
                if d>a['radius']+1e-12 or d>b['radius']+1e-12:continue
                union=sorted(set(a['members_all'])|set(b['members_all']))
                pairs.append({'a':a['id'],'b':b['id'],'d':d,'ab':int(a['cross_support']),'ba':int(b['cross_support']),'min_cross_support':min(int(a['cross_support']),int(b['cross_support'])),'sum_cross_support':int(a['cross_support'])+int(b['cross_support']),'excess_a':float(a['excess']),'excess_b':float(b['excess']),'min_excess':min(float(a['excess']),float(b['excess'])),'sum_excess':float(a['excess'])+float(b['excess']),'union_n':len(union),'member_ids':union})
        pairs.sort(key=lambda p:(-p['min_cross_support'],p['d'],-p['min_excess'],p['union_n'],p['a'],p['b']))
        sel=pairs[0] if pairs else None;o=sel['member_ids'] if sel else ids
        def pub(h):return {k:v for k,v in h.items() if k not in ('center','members_all','cross_support')}
        def pp(p):return {k:v for k,v in p.items() if k!='member_ids'}
        return {'rank':rank,'family_id':str(c['family_id']),'family_hash':str(c['family_hash']),'parent_n':len(ids),'refined':bool(sel),'output_n':len(o),'ratio':len(o)/len(ids) if ids else 0.0,'output_ids':o,'hypothesis_counts':{str(y):len(src[y]) for y in YEARS},'validated_pair_count':len(pairs),'selected_pair':pp(sel) if sel else None,'hypotheses':{str(y):[pub(h) for h in src[y]] for y in YEARS}}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--fair-pretruth',type=Path,required=True);ap.add_argument('--geometry',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True);req(sha(a.fair_pretruth)==FAIR_SHA,'fair pretruth changed');fair=json.loads(a.fair_pretruth.read_text());geom=json.loads(a.geometry.read_text());req(geom['scientific_role']=='LABEL_FREE_TARGET_EXCLUDED_GMN_GEOMETRY_ONLY','geometry role');req(int(geom['events_total'])==EXPECTED_TOTAL and geom['events_by_year']==EXPECTED_COUNTS,'geometry counts');req(geom['blind_exclusion']==BLIND and geom['shower_truth_exported'] is False,'geometry firewall');events=list(geom['events']);req(len(events)==EXPECTED_TOTAL,'geometry rows');req(all(not(BLIND[0]<=float(e['sol'])<=BLIND[1]) for e in events),'protected row survived');rt=Runtime(events);req({str(y):len(rt.byyear[y]) for y in YEARS}==EXPECTED_COUNTS,'runtime counts');subsets=[];allrows=[]
    for s in fair['subsets']:
        d,b=int(s['denominator']),int(s['bucket']);parents=list(s['successor_candidates']);req([int(x['internal_mass_rank']) for x in parents]==list(range(1,len(parents)+1)),f'rank drift d{d}b{b}');rows=[]
        for pos,c in enumerate(parents,1):r=rt.proc(c,pos);rows.append(r);allrows.append(r)
        subsets.append({'denominator':d,'bucket':b,'parent_candidate_count':len(parents),'extractions':rows});print(json.dumps({'panel':f'd{d}_b{b}','candidates':len(rows),'refined':sum(x['refined'] for x in rows),'mean_ratio':float(np.mean([x['ratio'] for x in rows])),'validated_pairs':sum(x['validated_pair_count'] for x in rows)},sort_keys=True),flush=True)
    payload={'schema':'ORBITTRACE_M2D_SACV_PAIR_V2_GMN_PRETRUTH','scientific_role':'TARGET_EXCLUDED_SACV_RECURRENCE_PAIR_MEMBERSHIPS_FROZEN_BEFORE_SHOWER_TRUTH','fair_pretruth_sha256':FAIR_SHA,'geometry_sha256':sha(a.geometry),'years':list(YEARS),'blind_exclusion':BLIND,'configuration':{'rmax':RMAX,'minimum_support':MIN_SUPPORT,'contamination_max':CONTAM_MAX,'analog_offsets_deg':DELTAS[1:].tolist(),'physical_scales':{'solar_deg':5.0,'radiant_deg':4.0,'speed_fraction':0.10},'annual_hypotheses':'all SACV-v1-admissible per-center widest-radius hypotheses','crossyear_pairs':'exact SACV-v1 reciprocal validation for every annual-hypothesis pair','pair_selection':'max min cross-support, then min center distance, max min annual excess, min union size, lexicographic center IDs','pair_membership':'union of the two selected SACV balls only','fallback':'exact_parent_only_if_no_validated_recurrence_pair'},'subsets':subsets,'summary':{'candidate_occurrences':len(allrows),'refined_occurrences':sum(x['refined'] for x in allrows),'mean_parent_n':float(np.mean([x['parent_n'] for x in allrows])),'mean_output_n':float(np.mean([x['output_n'] for x in allrows])),'validated_pairs':sum(x['validated_pair_count'] for x in allrows)},'parent_discovery_membership_changed':False,'parent_rank_changed':False,'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_scientific_access':False,'post_result_parameter_search':False};a.output.write_text(json.dumps(payload,separators=(',',':'),sort_keys=True,allow_nan=False)+'\n');print(json.dumps({'verdict':'PASS_M2D_SACV_PAIR_V2_GMN_PRETRUTH','sha256':sha(a.output),'summary':payload['summary']},indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
