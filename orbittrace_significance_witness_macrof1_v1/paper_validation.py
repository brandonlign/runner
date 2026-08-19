#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math
from collections import Counter
from pathlib import Path
from typing import Any
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree

YEARS=(2013,2014)
ROUTES=("sugar","hdbscan")
ROW_SHA={
("sugar",2013):"47fb0b700fbf710c7b061eead343016bd8d182756eb0c7f406507c5739e4c4f8",
("sugar",2014):"bc83c113e9a14b1c6e1ef460ca9a40e05df77f3a449fec6064f8910add04c912",
("hdbscan",2013):"2433b556d4a859580ef5431d2307ef34c8fa4c15d42841a2ec7b0c11e5f1f158",
("hdbscan",2014):"206692292b2ca252777e40c13c367880740d8e2576d27615f7ea94b7790e3f55",
}
EXPECTED={('sugar',2013):18638,('sugar',2014):15400,('hdbscan',2013):16028,('hdbscan',2014):13283}
B=199; ALPHA=0.05; MIN_SUPPORT=4; RADIUS=1.0
NULL_SALT="ORBITTRACE_SIGPRUNE_TM_SONOTACO_V1|"
EXPECTED_PAPER_RESULT_BLOB="1ac067658d7a1d99b1a276099ca6d3fee83a6c0b"
EXPECTED_GMN_VERDICT="PASS_SIGNIFICANCE_WITNESS_MACROF1_V1_GMN"

def req(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)
def sha256_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def sha256(p:Path)->str:return sha256_bytes(p.read_bytes())
def git_blob_sha(p:Path)->str:
    b=p.read_bytes();return hashlib.sha1(f"blob {len(b)}\0".encode()+b).hexdigest()
def arr_hash(a:np.ndarray,dtype:str="<f8")->str:
    return sha256_bytes(np.ascontiguousarray(np.asarray(a,dtype=dtype)).tobytes())
def ids_hash(ids:list[str])->str:return sha256_bytes("\n".join(sorted(ids)).encode())
def member_hash(ids:list[str])->str:return sha256_bytes("|".join(sorted(ids)).encode())[:20]
def family_id(prefix:str,ids:list[str])->str:return prefix+sha256_bytes((prefix+"|"+"|".join(sorted(ids))).encode())[:20]

def geo6(rows:list[dict[str,Any]])->np.ndarray:
    sol=np.radians(np.asarray([float(r['sol']) for r in rows])); lon=np.radians(np.asarray([float(r['sun_lon']) for r in rows])); lat=np.radians(np.asarray([float(r['ecl_lat']) for r in rows])); vg=np.asarray([float(r['vg']) for r in rows]); cl=np.cos(lat)
    X=np.column_stack([np.cos(sol),np.sin(sol),np.sin(lon)*cl,np.cos(lon)*cl,np.sin(lat),vg/72.0]); req(np.all(np.isfinite(X)),"nonfinite GEO6");return X

def physical_embedding(rows:list[dict[str,Any]])->np.ndarray:
    hs=2.0*math.sin(math.radians(5.0)/2.0); hr=2.0*math.sin(math.radians(4.0)/2.0); hv=math.log(1.1)
    sol=np.radians(np.asarray([float(r['sol']) for r in rows])); lon=np.radians(np.asarray([float(r['sun_lon']) for r in rows])); lat=np.radians(np.asarray([float(r['ecl_lat']) for r in rows])); vg=np.asarray([float(r['vg']) for r in rows]); req(np.all(vg>0),"nonpositive vg"); cl=np.cos(lat)
    Z=np.column_stack([np.cos(sol)/hs,np.sin(sol)/hs,cl*np.cos(lon)/hr,cl*np.sin(lon)/hr,np.sin(lat)/hr,np.log(vg)/hv]);req(np.all(np.isfinite(Z)),"nonfinite physical embedding");return Z

def graph_and_q(rows:list[dict[str,Any]]):
    ordered=sorted(rows,key=lambda r:str(r['id']));ids=[str(r['id']) for r in ordered];X=geo6(ordered);d,_=cKDTree(X).query(X,k=4,workers=1);r3=np.asarray(d[:,3]);req(np.all(r3>0),"invalid r3");order=np.lexsort((np.asarray(ids,dtype=str),r3)); ranks=np.empty(len(ids),dtype=np.int64);ranks[order]=np.arange(1,len(ids)+1);q=1.0-ranks.astype(float)/float(len(ids)+1)
    Z=physical_embedding(ordered);raw=cKDTree(Z).query_ball_point(Z,r=RADIUS,p=2.0,eps=0.0,return_sorted=True);neighbors=[list(map(int,x)) for x in raw];adj=[set(x) for x in neighbors];req(all(i in adj[i] for i in range(len(ids))),"self missing");req(all(i in adj[j] for i,row in enumerate(neighbors) for j in row),"graph asymmetric")
    h=hashlib.sha256();
    for i,row in enumerate(neighbors):h.update(f"{i}:".encode());h.update(",".join(map(str,row)).encode());h.update(b"\n")
    return ordered,ids,r3,ranks,q,neighbors,h.hexdigest()

def null_seed(route:str,rep:int)->int:
    return int.from_bytes(hashlib.sha256(f"{NULL_SALT}{route}|{rep}".encode()).digest()[:8],"big")

def p_fwer(prom:float,nullmax:np.ndarray)->float:return float((1+int(np.count_nonzero(nullmax>=prom)))/(B+1))

def tomato_candidates(rows:list[dict[str,Any]],route:str):
    from gudhi.clustering.tomato import Tomato
    ordered,ids,r3,ranks,q,neighbors,gh=graph_and_q(rows);n=len(ids)
    m=Tomato(graph_type='manual',density_type='manual');m.fit(neighbors,weights=q)
    leaf=np.asarray(m.leaf_labels_,dtype=np.int64);L=int(m.n_leaves_);children=np.asarray(m.children_,dtype=np.int64).reshape((-1,2));diag=np.asarray(m.diagram_,dtype=float);roots_expected=len(np.asarray(m.max_weight_per_cc_,dtype=float));req(L-len(children)==roots_expected,"root arithmetic");req(len(diag)==len(children),"diagram child mismatch")
    prom=np.maximum(np.asarray(diag[:,0]-diag[:,1],dtype=float),0.0) if len(diag) else np.empty(0)
    peaks=np.asarray([float(np.max(q[np.flatnonzero(leaf==l)])) for l in range(L)]);finite={};used=set()
    for birth,p in zip(diag[:,0].tolist() if len(diag) else [],prom.tolist()):
        dif=np.abs(peaks-float(birth));l=int(np.argmin(dif));req(float(dif[l])<=1e-12 and l not in used,"birth mapping");used.add(l);finite[l]=float(p)
    roots=set(range(L))-used;req(len(roots)==roots_expected,"root count")
    nullmax=np.empty(B,float)
    for rep in range(1,B+1):
        qp=np.random.Generator(np.random.PCG64(null_seed(route,rep))).permutation(q)
        nm=Tomato(graph_type='manual',density_type='manual');nm.fit(neighbors,weights=qp);d=np.asarray(nm.diagram_,dtype=float);nullmax[rep-1]=float(np.max(np.maximum(d[:,0]-d[:,1],0.0))) if d.size else 0.0
        if rep%25==0: print(json.dumps({'route':route,'null_rep':rep,'B':B}),flush=True)
    tau=float(np.sort(nullmax)[-10]);m.merge_threshold_=tau;labels=np.asarray(m.labels_,dtype=np.int64);rowsout=[]
    for lab in sorted(int(x) for x in np.unique(labels)):
        ix=np.flatnonzero(labels==lab);leaves=sorted(set(int(x) for x in leaf[ix]));surv=max(leaves,key=lambda l:(float(peaks[l]),-l));isroot=surv in roots; fp=None if isroot else float(finite[surv]);pf=None if isroot else p_fwer(fp,nullmax)
        if not isroot:req(fp>tau and pf<=ALPHA,"finite survivor not significant")
        mem=sorted(ids[int(i)] for i in ix)
        if len(mem)<MIN_SUPPORT:continue
        rowsout.append({'family_id':family_id('SPTM1',mem),'family_hash':member_hash(mem),'event_ids':mem,'member_count':len(mem),'is_root_survivor':bool(isroot),'finite_prominence':fp,'p_fwer':pf,'survivor_peak_q':float(peaks[surv])})
    rowsout.sort(key=lambda r:(0,float(r['p_fwer']),-float(r['finite_prominence']),-float(r['survivor_peak_q']),str(r['family_hash'])) if not r['is_root_survivor'] else (1,-float(r['survivor_peak_q']),-int(r['member_count']),str(r['family_hash'])))
    for i,r in enumerate(rowsout,1):r['rank']=i
    return rowsout,{'event_count':n,'event_universe_sha256':ids_hash(ids),'r3_sha256':arr_hash(r3),'q_sha256':arr_hash(q),'density_rank_sha256':arr_hash(ranks,'<i8'),'graph_sha256':gh,'null_max_sha256':arr_hash(nullmax),'tau':tau,'candidate_count':len(rowsout),'null_seed_rule':NULL_SALT+route+'|replicate','B':B,'alpha':ALPHA}

def build_witness(recurrent:list[dict[str,Any]],sig:list[dict[str,Any]]):
    rec=sorted(recurrent,key=lambda r:(int(r.get('rank',10**9)),str(r.get('family_id',''))));sig=sorted(sig,key=lambda r:(int(r['rank']),str(r['family_hash'])));rs=[set(map(str,r['event_ids'])) for r in rec];ss=[set(map(str,s['event_ids'])) for s in sig]
    for i in range(len(ss)):
        for j in range(i):req(not(ss[i]&ss[j]),"significance overlap")
    emitted=set();out=[];orphans=0
    for i,r in enumerate(rec):
        ovs=[len(rs[i]&s) for s in ss];best=max(ovs,default=0)
        if best>0:
            winners=[j for j,v in enumerate(ovs) if v==best];j=min(winners,key=lambda z:str(sig[z]['family_hash']))
            if j not in emitted:
                s=sig[j];mem=sorted(map(str,s['event_ids']));out.append({'family_id':family_id('SWMF1SIG',mem),'event_ids':mem,'member_count':len(mem),'origin':'significance_witness','source_significance_rank':int(s['rank']),'source_significance_family_hash':str(s['family_hash']),'first_recurrent_witness_rank':int(r.get('rank',i+1)),'witness_overlap_count':int(best)});emitted.add(j)
        else:
            mem=sorted(map(str,r['event_ids']));out.append({'family_id':family_id('SWMF1ORPHAN',mem),'event_ids':mem,'member_count':len(mem),'origin':'recurrent_orphan','source_recurrent_rank':int(r.get('rank',i+1))});orphans+=1
    for j,s in enumerate(sig):
        if j in emitted:continue
        mem=sorted(map(str,s['event_ids']));out.append({'family_id':family_id('SWMF1SIG',mem),'event_ids':mem,'member_count':len(mem),'origin':'significance_append','source_significance_rank':int(s['rank']),'source_significance_family_hash':str(s['family_hash'])});emitted.add(j)
    for i,r in enumerate(out,1):r['rank']=i
    os=[set(map(str,r['event_ids'])) for r in out]
    for i in range(len(os)):
        for j in range(i):req(not(os[i]&os[j]),"successor overlap")
    return out,{'recurrent_count':len(rec),'significance_count':len(sig),'successor_count':len(out),'recurrent_orphan_count':orphans,'mechanism_active': [r['event_ids'] for r in out[:min(len(rec),len(out))]] != [r['event_ids'] for r in rec[:min(len(rec),len(out))]]}

def score(families:list[dict[str,Any]],truth:dict[str,str],budget:int):
    counts=Counter(v for v in truth.values() if v!='SPORADIC');labels=sorted(k for k,n in counts.items() if n>=4);ids=set(truth);active=[]
    for i,f in enumerate(families):
        mem=set(map(str,f['event_ids']))&ids
        if mem:active.append((int(f.get('rank',i+1)),str(f.get('family_id',i)),mem))
    active.sort(key=lambda z:(z[0],z[1]));active=active[:budget];ts={lab:{eid for eid,v in truth.items() if v==lab} for lab in labels};mat=np.zeros((len(labels),len(active)),float)
    for i,lab in enumerate(labels):
        a=ts[lab]
        for j,(_,_,p) in enumerate(active):
            o=len(a&p)
            if o:pr=o/len(p);re=o/len(a);mat[i,j]=2*pr*re/(pr+re)
    n=max(len(labels),len(active));
    if n==0:return {'eligible_showers':len(labels),'macro_f1':0.0,'recovered_f1_gt_0_5':0,'candidate_used':0}
    cost=np.zeros((n,n));cost[:len(labels),:len(active)]=-mat;ri,cj=linear_sum_assignment(cost);vals=[float(mat[i,j]) if j<len(active) else 0.0 for i,j in zip(ri.tolist(),cj.tolist()) if i<len(labels)]
    return {'eligible_showers':len(labels),'macro_f1':float(np.mean(vals)) if vals else 0.0,'recovered_f1_gt_0_5':int(sum(v>0.5 for v in vals)),'candidate_used':len(active)}

def find_truth(root:Path,route:str,year:int)->dict[str,str]:
    xs=list(root.rglob(f'truth_{route}_{year}.json'));req(len(xs)==1,f'truth file missing {route} {year}');x=json.loads(xs[0].read_text());req(isinstance(x,dict),"truth shape");return {str(k):str(v) for k,v in x.items()}

def cmd_pretruth(a):
    route=a.route;req(route in ROUTES,"route");recall=json.loads(a.recurrent.read_text());req(recall.get('truth_accessed') is False and recall.get('target_information_access') is False,"recurrent pretruth firewall");rows=[]
    for y in YEARS:
        p=a.rows_root/f'{route}_{y}.json';req(sha256(p)==ROW_SHA[(route,y)],f'row hash drift {route} {y}');x=json.loads(p.read_text());req(len(x)==EXPECTED[(route,y)],"row count");rows.extend(x)
    req(all(not (20.0<=float(r['sol'])<=55.0) for r in rows),'protected SonotaCo row present')
    sig,diag=tomato_candidates(rows,route);succ,wdiag=build_witness(list(recall['routes'][route]['candidates']),sig);req(wdiag['mechanism_active'],"witness mechanism inactive");req(len(succ)>=max(43,14),"insufficient candidate capacity")
    out={'schema':'ORBITTRACE_SIGNIFICANCE_WITNESS_MACROF1_V1_SONOTACO_PRETRUTH','route':route,'scientific_role':'EXPOSED_SONOTACO_CURRENT_PAPER_VALIDATION_PRETRUTH','method_identity':'frozen significance-witness macro-F1 v1','rows':diag,'witness':wdiag,'successor_candidates':succ,'truth_accessed':False,'target_information_access':False,'target_region_events_accessed':False,'post_result_method_change_authorized':False}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n');print(json.dumps({'route':route,'pretruth_sha256':sha256(a.output),'candidate_count':len(succ),'tau':diag['tau']},indent=2),flush=True)

def cmd_eval(a):
    req(git_blob_sha(a.paper_result)==EXPECTED_PAPER_RESULT_BLOB,"paper result drift");old=json.loads(a.paper_result.read_text());req(old['verdict']=='PASS_TEMPORAL_FAIR_LITERATURE_4_OF_4',"paper baseline verdict drift")
    pre={}
    for route in ROUTES:
        xs=list(a.pretruth_root.rglob(f'*{route}*.json'));xs=[p for p in xs if 'PRETRUTH' in p.name.upper()];req(len(xs)==1,f'pretruth missing {route}: {xs}');p=json.loads(xs[0].read_text());req(p['route']==route and p['truth_accessed'] is False,"pretruth role");pre[route]=p
    panels=[]
    oldmap={(p['route'],int(p['year'])):p for p in old['panels']}
    for route in ROUTES:
        fam=pre[route]['successor_candidates']
        for y in YEARS:
            base=oldmap[(route,y)];BUD=int(base['budget']);truth=find_truth(a.truth_root,route,y);s=score(fam,truth,BUD);req(s['eligible_showers']==int(base['recurrent']['eligible_showers']),"eligible truth drift")
            lit=base['literature'];rec=base['recurrent'];g1=s['macro_f1']>lit['macro_f1'];g2=s['recovered_f1_gt_0_5']>=lit['recovered_f1_gt_0_5'];g3=s['macro_f1']>=rec['macro_f1'];g4=s['recovered_f1_gt_0_5']>=rec['recovered_f1_gt_0_5'];strict_rec=s['macro_f1']>rec['macro_f1']
            panels.append({'route':route,'year':y,'budget':BUD,'successor':s,'recurrent':rec,'literature':lit,'strict_vs_literature':g1,'recovery_ge_literature':g2,'macro_ge_recurrent':g3,'recovery_ge_recurrent':g4,'strict_vs_recurrent':strict_rec})
    mean_s=float(np.mean([p['successor']['macro_f1'] for p in panels]));mean_r=float(np.mean([p['recurrent']['macro_f1'] for p in panels]));gates={'strict_literature_4_of_4':all(p['strict_vs_literature'] for p in panels),'recovery_ge_literature_4_of_4':all(p['recovery_ge_literature'] for p in panels),'macro_ge_recurrent_4_of_4':all(p['macro_ge_recurrent'] for p in panels),'recovery_ge_recurrent_4_of_4':all(p['recovery_ge_recurrent'] for p in panels),'strict_recurrent_any':any(p['strict_vs_recurrent'] for p in panels),'mean_macro_strict_recurrent':mean_s>mean_r};passed=all(gates.values());res={'schema':'ORBITTRACE_SIGNIFICANCE_WITNESS_MACROF1_V1_CURRENT_PAPER_VALIDATION','verdict':'PASS_SIGNIFICANCE_WITNESS_MACROF1_V1_CURRENT_PAPER_VALIDATION' if passed else 'FAIL_SIGNIFICANCE_WITNESS_MACROF1_V1_CURRENT_PAPER_VALIDATION','gates':gates,'successor_mean_macro_f1':mean_s,'recurrent_mean_macro_f1':mean_r,'panels':panels,'paper_result_blob':EXPECTED_PAPER_RESULT_BLOB,'sonotaco_role':'EXPOSED_DEVELOPMENT_CURRENT_PAPER_BENCHMARK_NOT_PRISTINE_EXTERNAL_VALIDATION','binding':True,'post_result_rescue_authorized':False};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(res,indent=2,sort_keys=True,allow_nan=False)+'\n');print(json.dumps(res,indent=2),flush=True)

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('pretruth');p.add_argument('--route',required=True,choices=ROUTES);p.add_argument('--rows-root',type=Path,required=True);p.add_argument('--recurrent',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    e=sub.add_parser('evaluate');e.add_argument('--pretruth-root',type=Path,required=True);e.add_argument('--truth-root',type=Path,required=True);e.add_argument('--paper-result',type=Path,required=True);e.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();cmd_pretruth(a) if a.cmd=='pretruth' else cmd_eval(a)
if __name__=='__main__':main()
