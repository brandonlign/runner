#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, struct, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path
from typing import Any
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree

YEARS=(2013,2014); BUDGETS=(10,20,30,40); EXPECTED_COMMON={2013:15988,2014:13258}; EXPECTED_POOLED=29246
PRETRUTH_SHA='19828089363280d37aed17aacc9561e60c185abda61b2b7c0dead0226d2740b9'
CPP_SHA='4eef6f1b70b5baee5d1983d2480c02d73569b12af868ec23bbb6009d6ca1fa37'
FIXED_MODAL={'mean_test_auc_macro_f1':0.33211204306639563,'mean_test_macro_f1_at_40':0.4455723912337259,'total_test_recovered_at_40':50,'mean_native_macro_f1':0.7266723655790133}
HDB_EXPECTED={'mean_test_auc_macro_f1':0.345475559012312,'mean_test_macro_f1_at_40':0.46086713246967964,'total_test_recovered_at_40':52,'mean_native_macro_f1':0.4762894120871253}
AUDIT_CANDIDATES=(28,55,93,165,211)

def req(x:bool,msg:str)->None:
    if not x: raise RuntimeError(msg)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load_module(p:Path,name:str)->Any:
    s=importlib.util.spec_from_file_location(name,p);req(s is not None and s.loader is not None,f'cannot import {p}');m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

def load_rows(root:Path, route:str, year:int)->list[dict[str,Any]]:
    p=root/f'{route}_{year}.json'; req(p.exists(),f'missing {p}'); r=json.loads(p.read_text()); req(isinstance(r,list) and r,f'invalid {p}'); return r

def merge_common(root:Path):
    pooled=[]; ids_by_year={}; universe={'route_counts':{},'common_counts':{}}
    for y in YEARS:
        s={str(r['id']):r for r in load_rows(root,'sugar',y)}; h={str(r['id']):r for r in load_rows(root,'hdbscan',y)}; common=sorted(set(s)&set(h));req(len(common)==EXPECTED_COMMON[y],f'common count {y}')
        ids_by_year[y]=set(common);universe['route_counts'][str(y)]={'sugar':len(s),'hdbscan':len(h)};universe['common_counts'][str(y)]=len(common)
        for eid in common:
            r=dict(s[eid])
            for k,v in h[eid].items():
                if k not in r or r[k] is None:r[k]=v
            r['id']=eid;r['year']=y;pooled.append(r)
    req(len(pooled)==EXPECTED_POOLED and len({r['id'] for r in pooled})==EXPECTED_POOLED,'pooled changed')
    return pooled,ids_by_year,universe

def support_event(r):
    o={'id':str(r['id']),'year':int(r['year']),'sol':float(r['sol']),'lon':float(r['sun_lon']),'lat':float(r['ecl_lat']),'vg':float(r['vg'])};req(all(math.isfinite(float(o[k])) for k in ('sol','lon','lat','vg')) and o['vg']>0,'bad event');return o

def build_binary(events,candidates,structural, path:Path):
    Z=structural.physical_embedding(events); raw=cKDTree(Z).query_ball_point(Z,r=1.0,p=2.0,eps=0.0,return_sorted=True)
    years=np.asarray([e['year'] for e in events],dtype=np.int16);d13=np.fromiter((sum(years[j]==2013 for j in ns) for ns in raw),dtype=np.int32,count=len(raw));d14=np.fromiter((sum(years[j]==2014 for j in ns) for ns in raw),dtype=np.int32,count=len(raw));ids=[e['id'] for e in events]; idx={eid:i for i,eid in enumerate(ids)}
    cand_of=np.full(len(events),-1,dtype=np.int32)
    for ci,c in enumerate(candidates):
        for eid in c['event_ids']:
            g=idx[str(eid)];req(cand_of[g]<0,'candidate overlap');cand_of[g]=ci
    with path.open('wb') as f:
        f.write(b'OTIM1\0\0\0');f.write(struct.pack('<III',EXPECTED_COMMON[2013],EXPECTED_COMMON[2014],len(candidates)))
        for ci,c in enumerate(candidates):
            inds=[idx[str(e)] for e in c['event_ids']]; local={g:i for i,g in enumerate(inds)};internal=[];cross=[]
            for li,g in enumerate(inds):
                for j in raw[g]:
                    if j==g:continue
                    cj=int(cand_of[j])
                    if cj==ci:
                        if j>g:internal.append((li,local[j]))
                    else:
                        aa=min(int(d13[g]),int(d13[j]));bb=min(int(d14[g]),int(d14[j]))
                        if aa>0 and bb>0:cross.append((li,aa,bb))
            f.write(struct.pack('<III',len(inds),len(internal),len(cross)))
            for g in inds:f.write(struct.pack('<ii',int(d13[g]),int(d14[g])))
            for u,v in internal:f.write(struct.pack('<II',u,v))
            for u,a,b in cross:f.write(struct.pack('<Iii',u,a,b))
    return raw,d13,d14,cand_of,idx

def parse_scores(path:Path):
    out={};lines=path.read_text().splitlines();req(lines and lines[0].startswith('candidate\t'),'score header')
    for line in lines[1:]:
        p=line.split('\t');out[int(p[0])]=float(p[4])
    return out

def brute_candidate(ci,candidates,raw,d13,d14,cand_of,idx):
    inds=[idx[str(e)] for e in candidates[ci]['event_ids']];loc={g:i for i,g in enumerate(inds)};adj=[set() for _ in inds];cross=[]
    for li,g in enumerate(inds):
        for j in raw[g]:
            if j==g:continue
            if int(cand_of[j])==ci:adj[li].add(loc[j])
            else:
                aa=min(int(d13[g]),int(d13[j]));bb=min(int(d14[g]),int(d14[j]))
                if aa>0 and bb>0:cross.append((li,aa,bb))
    al=sorted(set([int(d13[g]) for g in inds if d13[g]>0]+[a for _,a,_ in cross]),reverse=True);bl=sorted(set([int(d14[g]) for g in inds if d14[g]>0]+[b for _,_,b in cross]),reverse=True)
    total=0.0
    for ib,b in enumerate(bl):
        bn=bl[ib+1] if ib+1<len(bl) else 0; inner=0.0
        for ia,a in enumerate(al):
            an=al[ia+1] if ia+1<len(al) else 0;active={li for li,g in enumerate(inds) if d13[g]>=a and d14[g]>=b};seen=set();good=0
            for s in list(active):
                if s in seen:continue
                stack=[s];seen.add(s);comp=[]
                while stack:
                    u=stack.pop();comp.append(u)
                    for v in adj[u]:
                        if v in active and v not in seen:seen.add(v);stack.append(v)
                bad=any(u in comp and ca>=a and cb>=b for u,ca,cb in cross)
                if len(comp)>=4 and not bad:good+=len(comp)
            inner += good*((a-an)/EXPECTED_COMMON[2013])
        total += inner*((b-bn)/EXPECTED_COMMON[2014])
    return total/len(inds)

def find_truth(root:Path,route:str,y:int):
    p=root/f'truth_{route}_{y}.json';req(p.exists(),f'missing {p}');o=json.loads(p.read_text());req(isinstance(o,dict),'truth dict');return {str(k):str(v) for k,v in o.items()}
def common_truth(root,ids_by_year):
    out={}
    for y in YEARS:
        a=find_truth(root,'sugar',y);b=find_truth(root,'hdbscan',y);ids=ids_by_year[y];req(all(e in a and e in b for e in ids),'truth missing');req(all(a[e]==b[e] for e in ids),'truth disagreement');out[y]={e:a[e] for e in ids}
    return out

def score(families,truth,budget=None):
    counts=Counter(v for v in truth.values() if v!='SPORADIC');labels=sorted(k for k,n in counts.items() if n>=4);ids=set(truth);active=[]
    for i,f in enumerate(families):
        mem=set(map(str,f['member_ids']))&ids
        if mem:active.append((int(f.get('rank',i+1)),str(f['family_id']),mem))
    active.sort(key=lambda z:(z[0],z[1]))
    if budget is not None:active=active[:budget]
    truth_sets={lab:{eid for eid,v in truth.items() if v==lab} for lab in labels};mat=np.zeros((len(labels),len(active)),dtype=float)
    for i,lab in enumerate(labels):
        A=truth_sets[lab]
        for j,(_,_,P) in enumerate(active):
            ov=len(A&P)
            if ov:
                pr=ov/len(P);re=ov/len(A);mat[i,j]=2*pr*re/(pr+re)
    n=max(len(labels),len(active))
    if n==0:return {'eligible_showers':0,'macro_f1':0.0,'recovered_f1_gt_0_5':0,'candidate_used':0}
    cost=np.zeros((n,n),dtype=float);cost[:len(labels),:len(active)]=-mat;ri,cj=linear_sum_assignment(cost);vals=[float(mat[i,j]) if j<len(active) else 0.0 for i,j in zip(ri.tolist(),cj.tolist()) if i<len(labels)]
    return {'eligible_showers':len(labels),'macro_f1':float(np.mean(vals)) if vals else 0.0,'recovered_f1_gt_0_5':int(sum(v>0.5 for v in vals)),'candidate_used':len(active)}
def curve(fam,truth):
    panels={str(k):score(fam,truth,k) for k in BUDGETS};return {'budgets':panels,'auc_macro_f1':float(np.mean([panels[str(k)]['macro_f1'] for k in BUDGETS])),'recovered_sum':int(sum(p['recovered_f1_gt_0_5'] for p in panels.values())),'native':score(fam,truth,None),'candidate_count':len(fam)}
def aggregate(curves):
    return {'mean_test_auc_macro_f1':float(np.mean([curves[y]['auc_macro_f1'] for y in YEARS])),'mean_test_macro_f1_at_40':float(np.mean([curves[y]['budgets']['40']['macro_f1'] for y in YEARS])),'total_test_recovered_at_40':int(sum(curves[y]['budgets']['40']['recovered_f1_gt_0_5'] for y in YEARS)),'mean_native_macro_f1':float(np.mean([curves[y]['native']['macro_f1'] for y in YEARS]))}
def close(a,b,tol=1e-12):return abs(float(a)-float(b))<=tol

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--rows-root',type=Path,required=True);ap.add_argument('--truth-root',type=Path,required=True);ap.add_argument('--structural-source',type=Path,required=True);ap.add_argument('--pretruth-support',type=Path,required=True);ap.add_argument('--baseline-result',type=Path,required=True);ap.add_argument('--exact-cpp',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.pretruth_support)==PRETRUTH_SHA,'pretruth artifact changed');req(sha(a.exact_cpp)==CPP_SHA,'exact accelerator bytes changed')
    pre=json.loads(a.pretruth_support.read_text());req(pre['truth_used'] is False and pre['shower_labels_accessed'] is False and pre['candidate_count']==888,'pretruth firewall');candidates=pre['candidates']
    structural=load_module(a.structural_source,'im_binding_structural');req(float(structural.RADIUS)==1.0 and int(structural.MIN_SUPPORT)==4,'structural constants')
    pooled,ids_by_year,universe=merge_common(a.rows_root);events=sorted([support_event(r) for r in pooled],key=lambda e:e['id'])
    with tempfile.TemporaryDirectory() as td:
        td=Path(td);binp=td/'input.bin';scoresp=td/'scores.tsv';exe=td/'exact';raw,d13,d14,cand_of,idx=build_binary(events,candidates,structural,binp)
        subprocess.run(['g++','-O3','-std=c++17',str(a.exact_cpp),'-o',str(exe)],check=True);subprocess.run([str(exe),str(binp),str(scoresp)],check=True)
        scores=parse_scores(scoresp);req(len(scores)==888,'missing accelerator scores')
        audits=[]
        for ci in AUDIT_CANDIDATES:
            b=brute_candidate(ci,candidates,raw,d13,d14,cand_of,idx);e=scores[ci];req(abs(b-e)<=1e-18,f'accelerator audit mismatch {ci}: {b} {e}');audits.append({'candidate':ci,'brute':b,'accelerated':e,'abs_diff':abs(b-e)})
    ranked=[]
    for ci,c in enumerate(candidates):
        row=dict(c);row['internal_2d_mass']=scores[ci];ranked.append(row)
    ranked.sort(key=lambda r:(-float(r['internal_2d_mass']),-float(r['modal_contrast']),str(r['family_hash'])))
    for i,r in enumerate(ranked,1):r['internal_mass_rank']=i
    ranked_pretruth={'schema':'ORBITTRACE_INTERNAL_MASS_SONOTACO_DEVELOPMENT_V1_RANKED_PRETRUTH','scientific_role':'ZERO_LABEL_EXACT_INTERNAL_MASS_RANKING','universe':universe,'candidate_count':888,'candidates':ranked,'accelerator_audit':audits,'pretruth_support_sha256':PRETRUTH_SHA,'exact_cpp_sha256':CPP_SHA,'truth_used':False,'shower_labels_accessed':False,'post_result_parameter_search':False}
    rp=a.output/'INTERNAL_MASS_SONOTACO_DEVELOPMENT_V1_RANKED_PRETRUTH.json';rp.write_text(json.dumps(ranked_pretruth,indent=2,sort_keys=True,allow_nan=False)+'\n')
    truth=common_truth(a.truth_root,ids_by_year)
    internal_fam=[{'family_id':r['family_id'],'member_ids':r['event_ids'],'member_count':r['member_count'],'rank':int(r['internal_mass_rank'])} for r in ranked]
    modal_rows=sorted(candidates,key=lambda r:(-float(r['modal_contrast']),str(r['family_hash'])));modal_fam=[{'family_id':r['family_id'],'member_ids':r['event_ids'],'member_count':r['member_count'],'rank':i} for i,r in enumerate(modal_rows,1)]
    modal_curves={y:curve(modal_fam,truth[y]) for y in YEARS};modal_agg=aggregate(modal_curves)
    for k,v in FIXED_MODAL.items():req((modal_agg[k]==v) if isinstance(v,int) else close(modal_agg[k],v),f'evaluator/modal reproduction mismatch {k}: {modal_agg[k]} {v}')
    curves={y:curve(internal_fam,truth[y]) for y in YEARS};agg=aggregate(curves)
    base=json.loads(a.baseline_result.read_text());hdb=base['aggregate']['hdbscan']
    for k,v in HDB_EXPECTED.items():req((hdb[k]==v) if isinstance(v,int) else close(hdb[k],v),f'HDB baseline changed {k}')
    gates={'auc_strictly_beats_tuned_hdbscan':agg['mean_test_auc_macro_f1']>HDB_EXPECTED['mean_test_auc_macro_f1'],'auc_strictly_beats_fixed_modal_transfer':agg['mean_test_auc_macro_f1']>FIXED_MODAL['mean_test_auc_macro_f1'],'recovered_at_40_at_least_52':agg['total_test_recovered_at_40']>=52,'candidate_memberships_exact_888':len(ranked)==888 and {tuple(sorted(r['event_ids'])) for r in ranked}=={tuple(sorted(r['event_ids'])) for r in candidates},'label_free_generation_and_ranking':True}
    verdict='PASS_INTERNAL_MASS_SONOTACO_DEVELOPMENT_V1' if all(gates.values()) else 'FAIL_INTERNAL_MASS_SONOTACO_DEVELOPMENT_V1'
    result={'schema':'ORBITTRACE_INTERNAL_MASS_SONOTACO_DEVELOPMENT_V1','scientific_role':'EXPOSED_SONOTACO_DEVELOPMENT_BENCHMARK','verdict':verdict,'aggregate':agg,'year_curves':{str(y):curves[y] for y in YEARS},'gates':gates,'comparators':{'tuned_hdbscan':HDB_EXPECTED,'fixed_modal_transfer_reproduced':modal_agg},'ranked_pretruth_sha256':sha(rp),'pretruth_support_sha256':PRETRUTH_SHA,'exact_cpp_sha256':CPP_SHA,'accelerator_audit':audits,'truth_opened_after_rank_serialization':True,'post_result_parameter_search':False,'claim_boundary':'development benchmark progress only; requires separate untouched external validation before independent generalization claim'}
    op=a.output/'INTERNAL_MASS_SONOTACO_DEVELOPMENT_V1_RESULT.json';op.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n');print(json.dumps({'verdict':verdict,'aggregate':agg,'gates':gates,'ranked_pretruth_sha256':result['ranked_pretruth_sha256']},indent=2,sort_keys=True))
if __name__=='__main__':main()
