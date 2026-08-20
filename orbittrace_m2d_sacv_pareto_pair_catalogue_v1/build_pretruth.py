#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
from typing import Any
import numpy as np
from scipy.spatial import cKDTree

YEARS=(2022,2023); RMAX=1.0; MIN_SUPPORT=4; CONTAM_MAX=0.10
DELTAS=np.concatenate(([0.0],np.arange(60.0,301.0,10.0)))
H_SOL=2*math.sin(math.radians(5.0)/2.0); H_RAD=2*math.sin(math.radians(4.0)/2.0); H_LOGV=math.log(1.1)
FAIR_SHA='8b0f4629659c1bfd750747303ad04ff67355adf66d4dbe474ce7fba788f5bae5'
EXPECTED_TOTAL=738682; EXPECTED_COUNTS={'2022':315024,'2023':423658}; BLIND=[20.0,55.0]
ROLE='TARGET_EXCLUDED_SACV_PARETO_PAIR_CATALOGUE_FROZEN_BEFORE_SHOWER_TRUTH'
SCHEMA='ORBITTRACE_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_GMN_PRETRUTH'

def req(x:bool,m:str)->None:
    if not x: raise RuntimeError(m)
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def normalize(e:dict[str,Any])->dict[str,Any]:
    return {'id':str(e['id']),'year':int(e['year']),'sol':float(e['sol']),
            'sun_lon':float(e.get('sun_lon',e.get('lon'))),'ecl_lat':float(e.get('ecl_lat',e.get('lat'))),'vg':float(e['vg'])}
def full_embed(rows):
    sol=np.radians(np.array([float(e['sol']) for e in rows])); lon=np.radians(np.array([float(e['sun_lon']) for e in rows]))
    lat=np.radians(np.array([float(e['ecl_lat']) for e in rows])); vg=np.array([float(e['vg']) for e in rows]); cl=np.cos(lat)
    z=np.column_stack([np.cos(sol)/H_SOL,np.sin(sol)/H_SOL,cl*np.cos(lon)/H_RAD,cl*np.sin(lon)/H_RAD,np.sin(lat)/H_RAD,np.log(vg)/H_LOGV])
    req(np.all(np.isfinite(z)),'nonfinite full geometry'); return z
def static_embed(rows):
    lon=np.radians(np.array([float(e['sun_lon']) for e in rows])); lat=np.radians(np.array([float(e['ecl_lat']) for e in rows]))
    vg=np.array([float(e['vg']) for e in rows]); cl=np.cos(lat)
    z=np.column_stack([cl*np.cos(lon)/H_RAD,cl*np.sin(lon)/H_RAD,np.sin(lat)/H_RAD,np.log(vg)/H_LOGV])
    req(np.all(np.isfinite(z)),'nonfinite static geometry'); return z

class Fenwick2DMax:
    def __init__(self,na:int,nb:int):
        self.na=na; self.nb=nb; self.t=np.zeros((na+1,nb+1),dtype=np.int32)
    def query(self,a:int,b:int)->int:
        out=0; i=a
        while i>0:
            j=b
            while j>0:
                v=int(self.t[i,j])
                if v>out: out=v
                j-=j&-j
            i-=i&-i
        return out
    def update(self,a:int,b:int,v:int)->None:
        i=a
        while i<=self.na:
            j=b
            while j<=self.nb:
                if v>self.t[i,j]: self.t[i,j]=v
                j+=j&-j
            i+=i&-i

class Runtime:
    def __init__(self,events):
        self.byyear={y:[] for y in YEARS}; self.byid={}
        for e0 in events:
            e=normalize(e0); req(e['year'] in YEARS,'unexpected year'); self.byyear[e['year']].append(e); self.byid[e['id']]=e
        req(len(self.byid)==len(events),'duplicate ids')
        for y in YEARS: self.byyear[y].sort(key=lambda e:e['id'])
        self.F={y:full_embed(self.byyear[y]) for y in YEARS}; self.S={y:static_embed(self.byyear[y]) for y in YEARS}
        self.stree={y:cKDTree(self.S[y]) for y in YEARS}
        self.uidx={y:{e['id']:i for i,e in enumerate(self.byyear[y])} for y in YEARS}
        self.solrad={y:np.radians(np.array([float(e['sol']) for e in self.byyear[y]])) for y in YEARS}
    def analog_distance_sets(self,e,year):
        cs=static_embed([e])[0]; inds=np.asarray(self.stree[year].query_ball_point(cs,r=RMAX),int)
        if len(inds)==0: return [np.empty(0)]*len(DELTAS)
        sd2=np.sum((self.S[year][inds]-cs)**2,axis=1); usol=self.solrad[year][inds]
        csol=np.radians((float(e['sol'])+DELTAS)%360.0); solar2=(2.0-2.0*np.cos(usol[:,None]-csol[None,:]))/(H_SOL*H_SOL)
        d2=sd2[:,None]+solar2
        return [np.sort(np.sqrt(d2[d2[:,j]<=RMAX*RMAX+1e-12,j])) for j in range(len(DELTAS))]
    def enumerate_sources(self,ids,year):
        ids=sorted(eid for eid in ids if eid in self.uidx[year])
        if len(ids)<MIN_SUPPORT: return []
        pF=np.array([self.F[year][self.uidx[year][eid]] for eid in ids]); pt=cKDTree(pF); neigh=pt.query_ball_point(pF,r=RMAX); out=[]
        for i,eid in enumerate(ids):
            pind=np.asarray(neigh[i],int)
            if len(pind)<MIN_SUPPORT: continue
            c=pF[i]; pd=np.sort(np.linalg.norm(pF[pind]-c,axis=1))
            radii=np.unique(np.concatenate([pd[MIN_SUPPORT-1:],[RMAX]])); radii=radii[radii<=RMAX+1e-12]
            ds=self.analog_distance_sets(self.byid[eid],year); obs=ds[0]
            if not len(obs): continue
            nobs=np.searchsorted(obs,radii+1e-12,'right').astype(float)
            bg=np.vstack([np.searchsorted(a,radii+1e-12,'right') for a in ds[1:]]).mean(axis=0)
            ps=np.searchsorted(pd,radii+1e-12,'right')
            contam=np.divide(bg,nobs,out=np.full_like(bg,np.inf),where=nobs>0); excess=nobs-bg
            ok=(ps>=MIN_SUPPORT)&(contam<=CONTAM_MAX)&(excess>0)
            if not np.any(ok): continue
            k=np.flatnonzero(ok)[-1]; r=float(radii[k])
            out.append({'id':eid,'radius':r,'parent_support':int(ps[k]),'field_count':int(nobs[k]),
                        'analog_mean':float(bg[k]),'contamination':float(contam[k]),'excess':float(excess[k]),'center':c})
        out.sort(key=lambda h:(-h['excess'],-h['parent_support'],h['contamination'],h['radius'],h['id']))
        for q,h in enumerate(out,1): h['annual_rank']=q
        req([h['annual_rank'] for h in out]==list(range(1,len(out)+1)),'annual rank permutation')
        return out
    def members(self,ids,center,r):
        out=[]
        for eid in ids:
            e=self.byid[eid]; z=self.F[e['year']][self.uidx[e['year']][eid]]
            if np.linalg.norm(z-center)<=r+1e-12: out.append(eid)
        return out

def pair_hash(family_hash:str,a:str,b:str)->str:
    return hashlib.sha256((family_hash+'\0'+a+'\0'+b).encode()).hexdigest()

def assign_layers(rows:list[dict[str,Any]])->None:
    if not rows: return
    ma=max(int(r['annual_rank_2022']) for r in rows); mb=max(int(r['annual_rank_2023']) for r in rows)
    bit=Fenwick2DMax(ma,mb)
    ordered=sorted(rows,key=lambda r:(int(r['parent_rank']),int(r['annual_rank_2022']),int(r['annual_rank_2023']),r['pair_hash']))
    for r in ordered:
        a=int(r['annual_rank_2022']); b=int(r['annual_rank_2023'])
        layer=1+bit.query(a,b); r['pareto_layer']=int(layer); bit.update(a,b,layer)
    req(len({(int(r['parent_rank']),int(r['annual_rank_2022']),int(r['annual_rank_2023'])) for r in rows})==len(rows),'duplicate objective triple')
    rows.sort(key=lambda r:(int(r['pareto_layer']),r['pair_hash']))
    for i,r in enumerate(rows,1): r['catalogue_rank']=i

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--fair-pretruth',type=Path,required=True); ap.add_argument('--geometry',type=Path,required=True); ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args(); a.output.parent.mkdir(parents=True,exist_ok=True)
    req(sha(a.fair_pretruth)==FAIR_SHA,'fair pretruth changed')
    fair=json.loads(a.fair_pretruth.read_text()); geom=json.loads(a.geometry.read_text())
    req(geom['scientific_role']=='LABEL_FREE_TARGET_EXCLUDED_GMN_GEOMETRY_ONLY','geometry role')
    req(int(geom['events_total'])==EXPECTED_TOTAL and geom['events_by_year']==EXPECTED_COUNTS,'geometry counts')
    req(geom['blind_exclusion']==BLIND and geom['shower_truth_exported'] is False,'geometry firewall')
    events=list(geom['events']); req(len(events)==EXPECTED_TOTAL,'geometry rows')
    req(all(not(BLIND[0]<=float(e['sol'])<=BLIND[1]) for e in events),'protected row survived')
    rt=Runtime(events); req({str(y):len(rt.byyear[y]) for y in YEARS}==EXPECTED_COUNTS,'runtime counts')
    subsets=[]; total_pairs=0; capacity_ok=True
    for s in fair['subsets']:
        d,b=int(s['denominator']),int(s['bucket']); parents=list(s['successor_candidates']); K=len(parents)
        req([int(x['internal_mass_rank']) for x in parents]==list(range(1,K+1)),f'parent rank drift d{d}b{b}')
        rows=[]; parent_summaries=[]
        for pos,c in enumerate(parents,1):
            ids=sorted(map(str,c['event_ids'])); req(all(eid in rt.byid for eid in ids),f'missing geometry d{d}b{b}/{pos}')
            src22=rt.enumerate_sources(ids,2022); src23=rt.enumerate_sources(ids,2023)
            for h in src22:
                h['members']=rt.members(ids,h['center'],h['radius'])
                h['cross_support']=sum(rt.byid[eid]['year']==2023 for eid in h['members'])
            for h in src23:
                h['members']=rt.members(ids,h['center'],h['radius'])
                h['cross_support']=sum(rt.byid[eid]['year']==2022 for eid in h['members'])
            pcount=0
            for h22 in src22:
                if int(h22['cross_support'])<MIN_SUPPORT: continue
                for h23 in src23:
                    if int(h23['cross_support'])<MIN_SUPPORT: continue
                    dist=float(np.linalg.norm(h22['center']-h23['center']))
                    if dist>float(h22['radius'])+1e-12 or dist>float(h23['radius'])+1e-12: continue
                    mids=sorted(set(h22['members'])|set(h23['members']))
                    y22=sum(rt.byid[eid]['year']==2022 for eid in mids); y23=len(mids)-y22
                    req(y22>=MIN_SUPPORT and y23>=MIN_SUPPORT,'validated pair support')
                    ph=pair_hash(str(c['family_hash']),str(h22['id']),str(h23['id']))
                    rows.append({'parent_rank':pos,'family_id':str(c['family_id']),'family_hash':str(c['family_hash']),
                                 'center_2022':str(h22['id']),'center_2023':str(h23['id']),
                                 'annual_rank_2022':int(h22['annual_rank']),'annual_rank_2023':int(h23['annual_rank']),
                                 'radius_2022':float(h22['radius']),'radius_2023':float(h23['radius']),
                                 'pair_distance':dist,'member_n':len(mids),'member_n_2022':y22,'member_n_2023':y23,
                                 'event_ids':mids,'pair_hash':ph})
                    pcount+=1
            parent_summaries.append({'parent_rank':pos,'hypotheses_2022':len(src22),'hypotheses_2023':len(src23),'validated_pairs':pcount})
        req(len({r['pair_hash'] for r in rows})==len(rows),f'pair identity collision d{d}b{b}')
        assign_layers(rows); N=len(rows); total_pairs+=N; capacity_ok=capacity_ok and N>=K
        req([int(r['catalogue_rank']) for r in rows]==list(range(1,N+1)),f'catalogue rank d{d}b{b}')
        subsets.append({'denominator':d,'bucket':b,'equal_budget_k':K,'complete_pair_count':N,'parent_summaries':parent_summaries,'pair_candidates':rows})
        print(json.dumps({'panel':f'd{d}_b{b}','K':K,'pairs':N,'capacity_ok':N>=K,'max_layer':max((r['pareto_layer'] for r in rows),default=0)},sort_keys=True),flush=True)
    verdict='PASS_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_PRETRUTH' if capacity_ok else 'POWER_INCONCLUSIVE_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_PRETRUTH'
    payload={'schema':SCHEMA,'scientific_role':ROLE,'verdict':verdict,'fair_pretruth_sha256':FAIR_SHA,'geometry_sha256':sha(a.geometry),
             'years':list(YEARS),'blind_exclusion':BLIND,
             'configuration':{'annual_order':['excess_desc','parent_support_desc','contamination_asc','radius_asc','center_id_asc'],
                              'pair_validation':'exact_reciprocal_sacv_v1','membership':'endpoint_ball_union',
                              'pareto_objectives':['parent_rank_min','annual_rank_2022_min','annual_rank_2023_min'],
                              'final_order':['pareto_layer_asc','pair_hash_asc'],'equal_budget':'exact_parent_candidate_count_no_fill'},
             'subsets':subsets,'summary':{'panel_count':len(subsets),'complete_pair_candidates':total_pairs,'capacity_pass_all_panels':bool(capacity_ok)},
             'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_scientific_access':False,'post_result_parameter_search':False}
    a.output.write_text(json.dumps(payload,separators=(',',':'),sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':verdict,'sha256':sha(a.output),'summary':payload['summary']},indent=2,sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())
