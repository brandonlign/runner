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
PAIR_V2_PRETRUTH_SHA='2869de000eeabb0a0852136eff8cd20e8b9244dade76bf6b1001b296f249b6be'
EXPECTED_TOTAL=738682; EXPECTED_COUNTS={'2022':315024,'2023':423658}; BLIND=[20.0,55.0]

def req(x:bool,msg:str)->None:
    if not x: raise RuntimeError(msg)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def normalize(e:dict[str,Any])->dict[str,Any]:
    return {'id':str(e['id']),'year':int(e['year']),'sol':float(e['sol']),'sun_lon':float(e.get('sun_lon',e.get('lon'))),'ecl_lat':float(e.get('ecl_lat',e.get('lat'))),'vg':float(e['vg'])}
def full_embed(rows):
    sol=np.radians(np.array([float(e['sol']) for e in rows])); lon=np.radians(np.array([float(e['sun_lon']) for e in rows])); lat=np.radians(np.array([float(e['ecl_lat']) for e in rows])); vg=np.array([float(e['vg']) for e in rows]); cl=np.cos(lat)
    z=np.column_stack([np.cos(sol)/H_SOL,np.sin(sol)/H_SOL,cl*np.cos(lon)/H_RAD,cl*np.sin(lon)/H_RAD,np.sin(lat)/H_RAD,np.log(vg)/H_LOGV]); req(np.all(np.isfinite(z)),'nonfinite full geometry'); return z
def static_embed(rows):
    lon=np.radians(np.array([float(e['sun_lon']) for e in rows])); lat=np.radians(np.array([float(e['ecl_lat']) for e in rows])); vg=np.array([float(e['vg']) for e in rows]); cl=np.cos(lat)
    z=np.column_stack([cl*np.cos(lon)/H_RAD,cl*np.sin(lon)/H_RAD,np.sin(lat)/H_RAD,np.log(vg)/H_LOGV]); req(np.all(np.isfinite(z)),'nonfinite static geometry'); return z

class Runtime:
    def __init__(self,events):
        self.byyear={y:[] for y in YEARS}; self.byid={}
        for e0 in events:
            e=normalize(e0); req(e['year'] in YEARS,'unexpected year'); self.byyear[e['year']].append(e); self.byid[e['id']]=e
        req(len(self.byid)==len(events),'duplicate ids')
        for y in YEARS:self.byyear[y].sort(key=lambda e:e['id'])
        self.F={y:full_embed(self.byyear[y]) for y in YEARS}; self.S={y:static_embed(self.byyear[y]) for y in YEARS}
        self.stree={y:cKDTree(self.S[y]) for y in YEARS}; self.uidx={y:{e['id']:i for i,e in enumerate(self.byyear[y])} for y in YEARS}; self.solrad={y:np.radians(np.array([float(e['sol']) for e in self.byyear[y]])) for y in YEARS}
    def analog_distance_sets(self,e,year):
        cs=static_embed([e])[0]; inds=np.asarray(self.stree[year].query_ball_point(cs,r=RMAX),int)
        if len(inds)==0:return [np.empty(0)]*len(DELTAS)
        sd2=np.sum((self.S[year][inds]-cs)**2,axis=1); usol=self.solrad[year][inds]; csol=np.radians((float(e['sol'])+DELTAS)%360.0)
        solar2=(2.0-2.0*np.cos(usol[:,None]-csol[None,:]))/(H_SOL*H_SOL); d2=sd2[:,None]+solar2
        return [np.sort(np.sqrt(d2[d2[:,j]<=RMAX*RMAX+1e-12,j])) for j in range(len(DELTAS))]
    def members(self,ids,center,r):
        out=[]
        for eid in ids:
            e=self.byid[eid]; z=self.F[e['year']][self.uidx[e['year']][eid]]
            if np.linalg.norm(z-center)<=r+1e-12:out.append(eid)
        return out
    def enumerate_sources(self,ids,year):
        ids=sorted(eid for eid in ids if eid in self.uidx[year])
        if len(ids)<MIN_SUPPORT:return []
        pF=np.array([self.F[year][self.uidx[year][eid]] for eid in ids]); pt=cKDTree(pF); neigh=pt.query_ball_point(pF,r=RMAX); out=[]
        for i,eid in enumerate(ids):
            pind=np.asarray(neigh[i],int)
            if len(pind)<MIN_SUPPORT:continue
            c=pF[i]; pd=np.sort(np.linalg.norm(pF[pind]-c,axis=1)); radii=np.unique(np.concatenate([pd[MIN_SUPPORT-1:],[RMAX]])); radii=radii[radii<=RMAX+1e-12]
            ds=self.analog_distance_sets(self.byid[eid],year); obs=ds[0]
            if not len(obs):continue
            nobs=np.searchsorted(obs,radii+1e-12,'right').astype(float); bg=np.vstack([np.searchsorted(a,radii+1e-12,'right') for a in ds[1:]]).mean(axis=0); ps=np.searchsorted(pd,radii+1e-12,'right')
            contam=np.divide(bg,nobs,out=np.full_like(bg,np.inf),where=nobs>0); excess=nobs-bg; ok=(ps>=MIN_SUPPORT)&(contam<=CONTAM_MAX)&(excess>0)
            if not np.any(ok):continue
            k=np.flatnonzero(ok)[-1]; r=float(radii[k])
            h={'id':eid,'radius':r,'parent_support':int(ps[k]),'field_count':int(nobs[k]),'analog_mean':float(bg[k]),'contamination':float(contam[k]),'excess':float(excess[k]),'center':c}
            h['members_all']=self.members(ids,c,r); h['cross_support']=sum(self.byid[x]['year']!=year for x in h['members_all']); out.append(h)
        order=sorted(out,key=lambda h:(-h['excess'],-h['parent_support'],h['contamination'],h['radius'],h['id']))
        for rank,h in enumerate(order,1): h['annual_rank']=rank
        return out
    def pairs(self,c,parent_rank):
        ids=sorted(map(str,c['event_ids'])); req(all(x in self.byid for x in ids),f'missing parent geometry rank {parent_rank}')
        src={y:self.enumerate_sources(ids,y) for y in YEARS}; out=[]
        for a in src[2022]:
            if a['cross_support']<MIN_SUPPORT:continue
            for b in src[2023]:
                if b['cross_support']<MIN_SUPPORT:continue
                d=float(np.linalg.norm(a['center']-b['center']))
                if d>a['radius']+1e-12 or d>b['radius']+1e-12:continue
                member_ids=sorted(set(a['members_all'])|set(b['members_all']))
                req(sum(self.byid[x]['year']==2022 for x in member_ids)>=MIN_SUPPORT and sum(self.byid[x]['year']==2023 for x in member_ids)>=MIN_SUPPORT,'pair annual support')
                raw=f"{c['family_hash']}|{a['id']}|{b['id']}".encode()
                out.append({'parent_rank':parent_rank,'family_id':str(c['family_id']),'family_hash':str(c['family_hash']),
                    'center_2022_id':a['id'],'center_2023_id':b['id'],'rank_2022':int(a['annual_rank']),'rank_2023':int(b['annual_rank']),
                    'pair_hash':hashlib.sha256(raw).hexdigest(),'event_ids':member_ids,'event_n':len(member_ids)})
        return out,src

class BIT2D:
    def __init__(self,n,m): self.n=n; self.m=m; self.t=[[0]*(m+1) for _ in range(n+1)]
    def query(self,x,y):
        ans=0; i=x
        while i>0:
            j=y
            while j>0:
                if self.t[i][j]>ans:ans=self.t[i][j]
                j-=j&-j
            i-=i&-i
        return ans
    def update(self,x,y,v):
        i=x
        while i<=self.n:
            j=y
            while j<=self.m:
                if v>self.t[i][j]:self.t[i][j]=v
                j+=j&-j
            i+=i&-i

def assign_layers(children):
    if not children:return []
    na=max(x['rank_2022'] for x in children); nb=max(x['rank_2023'] for x in children); bit=BIT2D(na,nb)
    for x in sorted(children,key=lambda z:(z['parent_rank'],z['rank_2022'],z['rank_2023'],z['pair_hash'])):
        layer=1+bit.query(x['rank_2022'],x['rank_2023']); x['pareto_layer']=layer; bit.update(x['rank_2022'],x['rank_2023'],layer)
    out=sorted(children,key=lambda z:(z['pareto_layer'],z['pair_hash']))
    for rank,x in enumerate(out,1):x['catalogue_rank']=rank
    return out

def main():
    ap=argparse.ArgumentParser()
    for n in ('fair-pretruth','geometry','pair-v2-pretruth','output'):ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args(); a.output.parent.mkdir(parents=True,exist_ok=True)
    req(sha(a.fair_pretruth)==FAIR_SHA,'fair changed'); req(sha(a.pair_v2_pretruth)==PAIR_V2_PRETRUTH_SHA,'pair-v2 pretruth changed')
    fair=json.loads(a.fair_pretruth.read_text()); pv=json.loads(a.pair_v2_pretruth.read_text()); geom=json.loads(a.geometry.read_text())
    req(pv['scientific_role']=='TARGET_EXCLUDED_SACV_RECURRENCE_PAIR_MEMBERSHIPS_FROZEN_BEFORE_SHOWER_TRUTH','pair-v2 role')
    req(pv['shower_truth_used'] is False and pv['target_information_access'] is False and pv['target_region_events_accessed'] is False,'pair-v2 firewall')
    req(geom['scientific_role']=='LABEL_FREE_TARGET_EXCLUDED_GMN_GEOMETRY_ONLY','geometry role'); req(int(geom['events_total'])==EXPECTED_TOTAL and geom['events_by_year']==EXPECTED_COUNTS,'geometry counts'); req(geom['blind_exclusion']==BLIND and geom['shower_truth_exported'] is False,'geometry firewall')
    events=list(geom['events']); req(len(events)==EXPECTED_TOTAL,'geometry rows'); req(all(not(BLIND[0]<=float(e['sol'])<=BLIND[1]) for e in events),'protected row survived')
    rt=Runtime(events); pair_by_key={(int(s['denominator']),int(s['bucket'])):s for s in pv['subsets']}
    subsets=[]; allchildren=[]; capacity_ok=True
    for s in fair['subsets']:
        d,b=int(s['denominator']),int(s['bucket']); parents=list(s['successor_candidates']); K=len(parents); children=[]; raw_pair_count=0
        for pos,c in enumerate(parents,1):
            pp,src=rt.pairs(c,pos); children.extend(pp); raw_pair_count+=len(pp)
            req(sorted(h['annual_rank'] for h in src[2022])==list(range(1,len(src[2022])+1)),f'2022 rank permutation d{d}b{b}/{pos}')
            req(sorted(h['annual_rank'] for h in src[2023])==list(range(1,len(src[2023])+1)),f'2023 rank permutation d{d}b{b}/{pos}')
        frozen=sum(int(x['validated_pair_count']) for x in pair_by_key[(d,b)]['extractions']); req(raw_pair_count==frozen,f'validated pair count drift d{d}b{b}: {raw_pair_count}!={frozen}')
        ranked=assign_layers(children); req(len(ranked)==raw_pair_count,'pair loss'); req([x['catalogue_rank'] for x in ranked]==list(range(1,len(ranked)+1)),'rank permutation')
        cap=len(ranked)>=K; capacity_ok &= cap
        subsets.append({'denominator':d,'bucket':b,'equal_budget_k':K,'complete_pair_count':len(ranked),'capacity_ok':cap,'successor_candidates':ranked})
        allchildren.extend(ranked); print(json.dumps({'panel':f'd{d}_b{b}','K':K,'pairs':len(ranked),'capacity_ok':cap,'layers':max((x['pareto_layer'] for x in ranked),default=0)},sort_keys=True),flush=True)
    verdict='PASS_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_PRETRUTH' if capacity_ok else 'POWER_INCONCLUSIVE_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_GMN_DEVELOPMENT'
    payload={'schema':'ORBITTRACE_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_PRETRUTH','scientific_role':'TARGET_EXCLUDED_SACV_VALIDATED_PAIR_PARETO_CATALOGUE_FROZEN_BEFORE_SHOWER_TRUTH',
      'verdict':verdict,'fair_pretruth_sha256':FAIR_SHA,'geometry_sha256':sha(a.geometry),'pair_v2_pretruth_sha256':PAIR_V2_PRETRUTH_SHA,
      'configuration':{'objectives':['m2d_parent_rank','sacv_2022_hypothesis_rank','sacv_2023_hypothesis_rank'],'pareto':'ordinary_nondominated_layers','tie_order':'pair_hash','equal_budget':'exact_m2d_sacv_parent_count_per_panel','membership':'exact_union_of_validated_endpoint_sacv_balls'},
      'subsets':subsets,'summary':{'validated_pair_children':len(allchildren),'capacity_ok_all_panels':bool(capacity_ok)},
      'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_scientific_access':False,'post_result_parameter_search':False}
    a.output.write_text(json.dumps(payload,separators=(',',':'),sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':verdict,'sha256':sha(a.output),'summary':payload['summary']},indent=2,sort_keys=True)); return 0
if __name__=='__main__':raise SystemExit(main())
