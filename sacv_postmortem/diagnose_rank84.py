#!/usr/bin/env python3
"""Forensic diagnostic only. Uses revealed OrbitTrace IDs to explain SACV v1 failure.
NOT a candidate method, NOT eligible for promotion/tuning, and MUST NOT alter frozen memberships.
"""
from __future__ import annotations
import argparse, importlib.util, json, math, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree


def load(path: Path, name: str):
    s=importlib.util.spec_from_file_location(name,path); assert s and s.loader
    m=importlib.util.module_from_spec(s); sys.modules[name]=m; s.loader.exec_module(m); return m


def score_center(rt, sacv, parent_ids, eid, year):
    ids=sorted(x for x in parent_ids if x in rt.uidx[year])
    pF=np.array([rt.F[year][rt.uidx[year][x]] for x in ids]); pt=cKDTree(pF)
    i=ids.index(eid); c=pF[i]; pind=np.asarray(pt.query_ball_point(c,r=sacv.RMAX),int)
    if len(pind)<sacv.MIN_SUPPORT:return None
    pd=np.sort(np.linalg.norm(pF[pind]-c,axis=1)); radii=np.unique(np.concatenate([pd[sacv.MIN_SUPPORT-1:],[sacv.RMAX]])); radii=radii[radii<=sacv.RMAX+1e-12]
    ds=rt.analog_distance_sets(rt.byid[eid],year); obs=ds[0]
    if not len(obs):return None
    nobs=np.searchsorted(obs,radii+1e-12,'right').astype(float)
    bg=np.vstack([np.searchsorted(a,radii+1e-12,'right') for a in ds[1:]]).mean(axis=0)
    ps=np.searchsorted(pd,radii+1e-12,'right')
    contam=np.divide(bg,nobs,out=np.full_like(bg,np.inf),where=nobs>0); excess=nobs-bg
    ok=(ps>=sacv.MIN_SUPPORT)&(contam<=sacv.CONTAM_MAX)&(excess>0)
    if not np.any(ok):return None
    k=np.flatnonzero(ok)[-1]; r=float(radii[k]); key=(float(excess[k]),int(ps[k]),-float(contam[k]),-r)
    members=rt.members(parent_ids,c,r)
    return {'id':eid,'year':year,'radius':r,'parent_support':int(ps[k]),'field_count':int(nobs[k]),'analog_mean':float(bg[k]),'contamination':float(contam[k]),'excess':float(excess[k]),'key':list(key),'center':c,'members':members}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--sacv-source',type=Path,required=True); ap.add_argument('--events',type=Path,required=True); ap.add_argument('--stage-a',type=Path,required=True); ap.add_argument('--result',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
    sacv=load(a.sacv_source,'sacv_postmortem_runtime')
    events=json.loads(a.events.read_text())['events']; rt=sacv.Runtime(events)
    stage=json.loads(a.stage_a.read_text()); result=json.loads(a.result.read_text()); row=stage['extractions'][83]; assert row['rank']==84 and row['parent_n']==1814
    sel=result['selected_candidate']; targets=set(sel['extraction']['overlap_2022_ids']+sel['extraction']['overlap_2023_ids']); assert len(targets)==18
    parent=sorted(row['output_ids']) # SACV fell back, so output == parent
    assert set(targets)<=set(parent)
    scored={}
    for y in sacv.YEARS:
        rows=[]
        for eid in parent:
            if eid in rt.uidx[y]:
                q=score_center(rt,sacv,parent,eid,y)
                if q: rows.append(q)
        rows.sort(key=lambda q:(tuple(q['key']), tuple([-ord(c) for c in q['id']])), reverse=True)
        # exact selector ordering: descending key, lexicographically smallest ID on ties
        rows=sorted(rows,key=lambda q:(-q['key'][0],-q['key'][1],-q['key'][2],-q['key'][3],q['id']))
        for j,q in enumerate(rows,1):q['rank_among_admissible_centers']=j
        scored[y]=rows
    target_rows={str(y):[{k:v for k,v in q.items() if k not in ('center','members')} | {'target_overlap':len(set(q['members'])&targets),'member_count':len(q['members'])} for q in scored[y] if q['id'] in targets] for y in sacv.YEARS}
    selected={str(y):next(q for q in scored[y] if q['id']==row['source'][str(y)]['id']) for y in sacv.YEARS}
    selected_public={str(y):{k:v for k,v in q.items() if k not in ('center','members')} | {'target_overlap':len(set(q['members'])&targets),'member_count':len(q['members'])} for y,q in [(y,selected[str(y)])] for y in []}
    selected_public={str(y):({k:v for k,v in selected[str(y)].items() if k not in ('center','members')} | {'target_overlap':len(set(selected[str(y)]['members'])&targets),'member_count':len(selected[str(y)]['members'])}) for y in sacv.YEARS}
    # Exhaustive target-centered cross-year diagnostic: asks whether the true stream is representable by SACV balls even though top-1 selection missed it.
    pairs=[]
    for qa in [q for q in scored[2022] if q['id'] in targets]:
      for qb in [q for q in scored[2023] if q['id'] in targets]:
        d=float(np.linalg.norm(qa['center']-qb['center'])); ab=len(rt.members(parent,qa['center'],qa['radius'],2023)); ba=len(rt.members(parent,qb['center'],qb['radius'],2022)); mutual=d<=qa['radius']+1e-12 and d<=qb['radius']+1e-12
        union=sorted(set(qa['members'])|set(qb['members'])); ov=len(set(union)&targets); prec=ov/len(union) if union else 0; rec=ov/18; f1=2*prec*rec/(prec+rec) if prec+rec else 0
        pairs.append({'a':qa['id'],'b':qb['id'],'d':d,'ab':ab,'ba':ba,'mutual':mutual,'would_validate':bool(mutual and ab>=4 and ba>=4),'union_n':len(union),'target_overlap':ov,'target_precision':prec,'target_recall':rec,'target_f1':f1})
    pairs.sort(key=lambda x:(x['would_validate'],x['target_f1'],x['target_overlap'],-x['union_n']),reverse=True)
    out={'schema':'ORBITTRACE_SACV_V1_FAILURE_POSTMORTEM','scientific_role':'TARGET_AWARE_FORENSIC_DIAGNOSTIC_ONLY_NOT_METHOD_DEVELOPMENT','frozen_failure':{'rank':84,'parent_n':1814,'output_n':1814,'cross':row['cross'],'source':row['source']},'target_count':18,'admissible_center_counts':{str(y):len(scored[y]) for y in sacv.YEARS},'selected_sources':selected_public,'target_center_hypotheses':target_rows,'best_target_centered_crossyear_pairs':pairs[:20],'diagnostic_only':True,'method_change_authorized':False,'promotion_eligible':False}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,sort_keys=True,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x)+'\n')
    print(json.dumps({'admissible_center_counts':out['admissible_center_counts'],'selected_sources':selected_public,'best_pair':pairs[0] if pairs else None},indent=2,sort_keys=True))
if __name__=='__main__':main()
