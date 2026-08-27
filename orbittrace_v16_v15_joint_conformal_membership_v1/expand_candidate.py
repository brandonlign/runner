#!/usr/bin/env python3
from __future__ import annotations
import argparse, copy, hashlib, json
from collections import defaultdict
from pathlib import Path
from typing import Any
import numpy as np

ALPHA=0.05
NEIGHBOR_ORDER=2
MODEL_ORDER=1
ACTIVITY_PADDING_DEG=6.0
DENSITY_CEILING=1.5
TRAJECTORY_CEILING=1.5
YEARS=(2013,2014)
SOURCE_PR=461
SOURCE_RUN=31237700141
SOURCE_ARTIFACT=9016226576


def require(ok: bool,msg: str)->None:
    if not ok: raise RuntimeError(msg)

def sha256_json(obj: Any)->str:
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def wrap180(x): return (np.asarray(x,dtype=np.float64)+180.0)%360.0-180.0

def circular_mean_deg(values):
    a=np.radians(np.asarray(values,dtype=np.float64)%360.0)
    c=float(np.mean(np.cos(a))); s=float(np.mean(np.sin(a)))
    require(abs(c)+abs(s)>1e-15,"undefined circular mean")
    return float(np.degrees(np.arctan2(s,c))%360.0)

def circular_arc(values):
    x=sorted(float(v)%360.0 for v in values); require(bool(x),"empty circular arc")
    if len(x)==1: return x[0],x[0]
    gaps=[(x[i+1]-x[i],i) for i in range(len(x)-1)]
    gaps.append(((x[0]+360.0)-x[-1],len(x)-1))
    _,i=max(gaps,key=lambda t:(t[0],-t[1]))
    return x[(i+1)%len(x)],x[i]

def in_activity_arc(sol,source_values):
    start,end=circular_arc(source_values); width=(end-start)%360.0
    if width+2.0*ACTIVITY_PADDING_DEG>=360.0: return np.ones(len(sol),dtype=bool)
    s=(start-ACTIVITY_PADDING_DEG)%360.0; e=(end+ACTIVITY_PADDING_DEG)%360.0
    return (sol>=s)|(sol<=e) if s>e else (sol>=s)&(sol<=e)

def exact_distance_matrix(left,right):
    if not left or not right: return np.empty((len(left),len(right)),dtype=np.float64)
    rs=np.asarray([float(e['sol']) for e in right]); rl=np.asarray([float(e['sun_lon']) for e in right]); rb=np.asarray([float(e['ecl_lat']) for e in right]); rv=np.asarray([float(e['vg']) for e in right])
    out=np.empty((len(left),len(right)),dtype=np.float64)
    for lo in range(0,len(left),1024):
        rows=left[lo:lo+1024]
        ls=np.asarray([float(e['sol']) for e in rows])[:,None]; ll=np.asarray([float(e['sun_lon']) for e in rows])[:,None]; lb=np.asarray([float(e['ecl_lat']) for e in rows])[:,None]; lv=np.asarray([float(e['vg']) for e in rows])[:,None]
        dsol=wrap180(ls-rs[None,:])/4.0
        dlon=wrap180(ll-rl[None,:])*np.cos(np.radians(0.5*(lb+rb[None,:])))/2.0
        dlat=(lb-rb[None,:])/2.0; dvg=(lv-rv[None,:])/2.0
        out[lo:lo+len(rows)]=np.sqrt(dsol*dsol+dlon*dlon+dlat*dlat+dvg*dvg)
    return out

def source_leave_one_out_d2(events):
    require(len(events)>=4,"source family-year has fewer than four seeds")
    d=exact_distance_matrix(events,events); np.fill_diagonal(d,np.inf)
    return np.partition(d,1,axis=1)[:,1]

def target_d2(events,source):
    if not events: return np.empty(0,dtype=np.float64)
    d=exact_distance_matrix(events,source); require(d.shape[1]>=2,"source support fewer than two")
    return np.partition(d,1,axis=1)[:,1]

def fit_line(x,y):
    require(len(x)==len(y) and len(x)>=2,"invalid affine fit")
    design=np.column_stack((np.ones(len(x),dtype=np.float64),np.asarray(x,dtype=np.float64)))
    beta=np.linalg.lstsq(design,np.asarray(y,dtype=np.float64),rcond=None)[0]
    return float(beta[0]),float(beta[1])

def fit_trajectory(events):
    require(len(events)>=3,"trajectory fit fewer than three seeds")
    sol0=circular_mean_deg([float(e['sol']) for e in events]); lon0=circular_mean_deg([float(e['sun_lon']) for e in events])
    x=wrap180(np.asarray([float(e['sol']) for e in events])-sol0); ylon=wrap180(np.asarray([float(e['sun_lon']) for e in events])-lon0)
    lat=np.asarray([float(e['ecl_lat']) for e in events]); vg=np.asarray([float(e['vg']) for e in events])
    li,ls=fit_line(x,ylon); ai,aslope=fit_line(x,lat); vi,vs=fit_line(x,vg)
    return {'sol0':sol0,'lon0':lon0,'lon_intercept':li,'lon_slope':ls,'lat_intercept':ai,'lat_slope':aslope,'vg_intercept':vi,'vg_slope':vs}

def trajectory_residuals(model,events):
    if not events: return np.empty(0,dtype=np.float64)
    sol=np.asarray([float(e['sol']) for e in events]); x=wrap180(sol-float(model['sol0']))
    lonhat=(float(model['lon0'])+float(model['lon_intercept'])+float(model['lon_slope'])*x)%360.0
    lathat=float(model['lat_intercept'])+float(model['lat_slope'])*x; vghat=float(model['vg_intercept'])+float(model['vg_slope'])*x
    lon=np.asarray([float(e['sun_lon']) for e in events]); lat=np.asarray([float(e['ecl_lat']) for e in events]); vg=np.asarray([float(e['vg']) for e in events])
    dlon=wrap180(lon-lonhat)*np.cos(np.radians(0.5*(lat+lathat)))/2.0; dlat=(lat-lathat)/2.0; dvg=(vg-vghat)/2.0
    return np.sqrt(dlon*dlon+dlat*dlat+dvg*dvg)

def loo_residuals(events):
    require(len(events)>=4,"trajectory source fewer than four seeds")
    out=np.empty(len(events),dtype=np.float64)
    for i in range(len(events)): out[i]=trajectory_residuals(fit_trajectory(events[:i]+events[i+1:]),[events[i]])[0]
    return out

def source_empirical_pvalues(values):
    x=np.asarray(values,dtype=np.float64); require(x.ndim==1 and len(x)>=4 and np.all(np.isfinite(x)),"invalid source reference")
    ordered=np.sort(x); ge=len(x)-np.searchsorted(ordered,x,side='left'); return ge.astype(np.float64)/float(len(x))

def target_empirical_pvalues(values,reference):
    x=np.asarray(values,dtype=np.float64); ref=np.sort(np.asarray(reference,dtype=np.float64)); require(len(ref)>=4,"invalid target reference")
    ge=len(ref)-np.searchsorted(ref,x,side='left'); return (1.0+ge.astype(np.float64))/float(len(ref)+1)

def fisher_nonconformity(pd,pt): return -2.0*(np.log(np.asarray(pd))+np.log(np.asarray(pt)))
def joint_conformal_pvalues(scores,reference): return target_empirical_pvalues(scores,reference)

def expand(rows_by_year,candidate):
    families=copy.deepcopy(candidate['families']); original={str(f['family_id']):set(str(x) for x in f['event_ids']) for f in families}; lookup={y:{str(e['id']):e for e in rows_by_year[y]} for y in YEARS}; fam_lookup={str(f['family_id']):f for f in families}
    diagnostics={'configuration':{'alpha':ALPHA,'neighbor_order':NEIGHBOR_ORDER,'model_order':MODEL_ORDER,'activity_padding_deg':ACTIVITY_PADDING_DEG,'density_ceiling':DENSITY_CEILING,'trajectory_ceiling':TRAJECTORY_CEILING,'source_pr':SOURCE_PR,'source_run':SOURCE_RUN,'source_artifact':SOURCE_ARTIFACT,'parameter_search':False},'new_members_by_year':{},'eligible_pairs_by_year':{},'conflicted_pairs_by_year':{},'source_seed_count_by_year':{}}
    assignments={str(y):{} for y in YEARS}
    for target_year in YEARS:
        source_year=YEARS[1] if target_year==YEARS[0] else YEARS[0]; target=rows_by_year[target_year]; target_sol=np.asarray([float(e['sol'])%360.0 for e in target]); target_seed_owner={}
        for fid,ids in original.items():
            for eid in sorted(ids & set(lookup[target_year])):
                prior=target_seed_owner.get(eid); require(prior is None or prior==fid,f'seed event belongs to multiple families: {eid}'); target_seed_owner[eid]=fid
        best={}; eligible=0
        for family in families:
            fid=str(family['family_id']); source_ids=sorted(original[fid] & set(lookup[source_year])); require(len(source_ids)>=4,f'{fid} lacks four source-year seeds')
            source=[lookup[source_year][eid] for eid in source_ids]; sd2=source_leave_one_out_d2(source); sr=loo_residuals(source); source_scores=fisher_nonconformity(source_empirical_pvalues(sd2),source_empirical_pvalues(sr)); model=fit_trajectory(source)
            idx=np.flatnonzero(in_activity_arc(target_sol,[float(e['sol']) for e in source])); candidates=[target[int(i)] for i in idx]; d2=target_d2(candidates,source); residual=trajectory_residuals(model,candidates); scores=fisher_nonconformity(target_empirical_pvalues(d2,sd2),target_empirical_pvalues(residual,sr)); jp=joint_conformal_pvalues(scores,source_scores)
            for i,d,r,s,p in zip(idx.tolist(),d2.tolist(),residual.tolist(),scores.tolist(),jp.tolist()):
                eid=str(target[i]['id'])
                if eid in target_seed_owner or float(d)>DENSITY_CEILING+1e-12 or float(r)>TRAJECTORY_CEILING+1e-12 or float(p)<=ALPHA+1e-15: continue
                eligible+=1; key=(-float(p),float(s),fid)
                old=best.get(eid)
                if old is None or key<old[0]: best[eid]=(key,fid)
        by_family=defaultdict(list)
        for eid,(_key,fid) in best.items(): by_family[fid].append(eid)
        for fid,ids in by_family.items():
            ids.sort(); fam_lookup[fid]['event_ids']=sorted(set(str(x) for x in fam_lookup[fid]['event_ids'])|set(ids)); assignments[str(target_year)][fid]=ids
        diagnostics['new_members_by_year'][str(target_year)]=len(best); diagnostics['eligible_pairs_by_year'][str(target_year)]=eligible; diagnostics['conflicted_pairs_by_year'][str(target_year)]=max(0,eligible-len(best)); diagnostics['source_seed_count_by_year'][str(target_year)]=len(target_seed_owner)
    diagnostics['total_new_members']=sum(diagnostics['new_members_by_year'].values()); diagnostics['expanded_membership_sha256']=sha256_json({str(f['family_id']):f['event_ids'] for f in families})
    for before,after in zip(candidate['families'],families):
        require(str(before['family_id'])==str(after['family_id']) and int(before['rank'])==int(after['rank']),'family order changed'); require(set(map(str,before['event_ids'])).issubset(set(map(str,after['event_ids']))),'seed lost')
    return families,diagnostics,assignments

def main():
    p=argparse.ArgumentParser(); p.add_argument('--rows-2013',type=Path,required=True); p.add_argument('--rows-2014',type=Path,required=True); p.add_argument('--candidate',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    rows={2013:json.loads(a.rows_2013.read_text()),2014:json.loads(a.rows_2014.read_text())}; candidate=json.loads(a.candidate.read_text()); require(candidate.get('truth_accessed') is False,'input candidate not pretruth'); require(candidate.get('target_information_access') is False,'target information in input candidate')
    families,diag,assign=expand(rows,candidate); out=copy.deepcopy(candidate); out['candidate_name']='OrbitTrace v16 v15-locator joint-conformal membership'; out['families']=families; out['truth_accessed']=False; out['target_information_access']=False; out['v15_family_order_unchanged']=True; out['joint_conformal_membership']=True
    (a.output/'candidate_primary_output.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); (a.output/'v16_membership_diagnostics.json').write_text(json.dumps(diag,indent=2,sort_keys=True)+'\n'); (a.output/'v16_assignments.json').write_text(json.dumps(assign,indent=2,sort_keys=True)+'\n')
    summary={'verdict':'PASS_V16_EXPOSED_DEVELOPMENT_OUTPUT_FREEZE','family_count':len(families),'original_family_order_sha256':sha256_json([(f['rank'],f['family_id']) for f in candidate['families']]),'expanded_family_order_sha256':sha256_json([(f['rank'],f['family_id']) for f in families]),'expanded_membership_sha256':diag['expanded_membership_sha256'],'total_new_members':diag['total_new_members'],'truth_accessed':False,'target_information_access':False,'maarsy_access':False,'dms_access':False}
    require(summary['original_family_order_sha256']==summary['expanded_family_order_sha256'],'v15 order changed'); (a.output/'v16_pretruth_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n'); print(json.dumps(summary,indent=2,sort_keys=True))
if __name__=='__main__': main()
