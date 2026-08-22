#!/usr/bin/env python3
from __future__ import annotations
import argparse,base64,gzip,hashlib,importlib.util,json,math,sys,tempfile,types
from collections import defaultdict
from pathlib import Path
import numpy as np
import hdbscan

YEARS=(2022,2023)
GRID=(10,20,30,40,50,60,70,80,90,100,120,150,200,300,500,750,1000)
W=np.array([0.335,0.250,0.230,0.215,0.128,0.145,1.0,0.0],dtype=float)
LAMBDA=0.25
MAX_REVEAL_RANK=100


def req(x,msg):
    if not x: raise RuntimeError(msg)
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def fh(indices): return hashlib.sha256(','.join(map(str,sorted(indices))).encode()).hexdigest()[:20]

def load_module(path:Path,name:str):
    s=importlib.util.spec_from_file_location(name,path);req(s is not None and s.loader is not None,f'cannot import {path}')
    m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

def decode_blind_source(parts_root:Path,out:Path):
    parts=sorted(parts_root.glob('part*.b64'))
    req([p.name for p in parts]==[f'part{i:02d}.b64' for i in range(4)],f'bad blind source parts {[p.name for p in parts]}')
    enc=''.join(''.join(p.read_text().split()) for p in parts)
    raw=gzip.decompress(base64.b64decode(enc,validate=True))
    req(len(raw)==24135,f'blind source byte count {len(raw)}')
    forbidden=['april_candidate_members.csv','247.17','-14.34','37.62','OrbitTrace-April-36.9']
    req(not any(x in raw.decode() for x in forbidden),'target literal in blind scanner source')
    out.write_bytes(raw);return load_module(out,'multiscale_blind_transport')

def support_event(r):
    o={'id':str(r['id']),'year':int(r['year']),'sol':float(r['sol']),'lon':float(r['sun_lon']),'lat':float(r['ecl_lat']),'vg':float(r['vg'])}
    req(o['year'] in YEARS,'wrong year');req(all(math.isfinite(float(o[k])) for k in ('sol','lon','lat','vg')) and o['vg']>0,'bad event')
    return o

def feature_matrix(events):
    sol=np.radians(np.asarray([e['sol'] for e in events],float));lon=np.radians(np.asarray([e['lon'] for e in events],float));lat=np.radians(np.asarray([e['lat'] for e in events],float));vg=np.asarray([e['vg'] for e in events],float)
    X=np.column_stack((np.cos(sol),np.sin(sol),np.sin(lon)*np.cos(lat),np.cos(lon)*np.cos(lat),np.sin(lat),vg/72.0))
    req(np.all(np.isfinite(X)),'non-finite GEO6');return X

def run_hdb(X,mcs):
    model=hdbscan.HDBSCAN(min_cluster_size=int(mcs),min_samples=None,metric='euclidean',cluster_selection_method='eom',allow_single_cluster=False,prediction_data=False,core_dist_n_jobs=1).fit(X)
    labels=np.asarray(model.labels_,dtype=np.int32);probs=np.asarray(model.probabilities_,dtype=float);out=[]
    for lab in sorted(int(v) for v in np.unique(labels) if v>=0):
        ix=np.flatnonzero(labels==lab);out.append((frozenset(map(int,ix.tolist())),float(np.mean(probs[ix]))))
    return out

def run_recurrent(X,years,recurrent_source):
    rec=load_module(recurrent_source,'frozen_recurrent_eom_multiscale_witness')
    model=hdbscan.HDBSCAN(min_cluster_size=10,min_samples=10,metric='euclidean',cluster_selection_method='eom',allow_single_cluster=False,prediction_data=False,core_dist_n_jobs=1).fit(X)
    tree=model.condensed_tree_._raw_tree
    stability,_annual=rec.recurrent_stability(tree,years)
    labels=rec.eom_labels(tree,stability);out=[]
    for lab in sorted(int(v) for v in np.unique(labels) if v>=0):
        ix=np.flatnonzero(labels==lab);out.append(frozenset(map(int,ix.tolist())))
    return out

def ranknorm(v):
    v=np.asarray(v,float);n=len(v)
    if n<=1:return np.zeros(n,float)
    o=np.argsort(v,kind='mergesort');z=np.empty(n,float);z[o]=np.linspace(0,1,n);return z

def build_multiscale(events,X,cats,recurrent):
    years=np.asarray([e['year'] for e in events],dtype=np.int16)
    D={}
    for mcs,fs in cats.items():
        for s,p in fs:
            x=D.setdefault(s,{'s':s,'scales':[],'hprobs':[],'recurrent':False});x['scales'].append(int(mcs));x['hprobs'].append(float(p))
    for s in recurrent:
        x=D.setdefault(s,{'s':s,'scales':[],'hprobs':[],'recurrent':False});x['recurrent']=True
    R=list(D.values());inv=defaultdict(list)
    for i,x in enumerate(R):
        for e in x['s']:inv[e].append(i)
    for i,x in enumerate(R):
        cand=set()
        for e in x['s']:cand.update(inv[e])
        best=0.0
        for j in cand:
            if j==i:continue
            aa=x['s'];bb=R[j]['s'];inter=len(aa&bb)
            if inter:best=max(best,inter/len(aa|bb))
        ix=np.fromiter(x['s'],dtype=np.int64,count=len(x['s']));V=X[ix];cen=V.mean(axis=0);scatter=float(np.mean(np.sum((V-cen)**2,axis=1)))
        a=ix[years[ix]==YEARS[0]];b=ix[years[ix]==YEARS[1]]
        if len(a) and len(b):
            A=X[a];B=X[b];ca=A.mean(0);cb=B.mean(0);sa=float(np.mean(np.sum((A-ca)**2,axis=1)));sb=float(np.mean(np.sum((B-cb)**2,axis=1)));sync=float(np.linalg.norm(ca-cb)/(math.sqrt((sa+sb)/2)+1e-9))
        else:sync=9.0
        x.update(bestj=best,scatter=scatter,sync=sync,balance=2*min(len(a),len(b))/len(ix))
    idx=[i for i,x in enumerate(R) if x['scales']]
    raw=np.column_stack([
        [R[i]['bestj'] for i in idx],
        [1/(1+R[i]['scatter']) for i in idx],
        [1/(1+R[i]['sync']) for i in idx],
        [R[i]['balance'] for i in idx],
        [max(R[i]['hprobs']) for i in idx],
        [len(R[i]['scales']) for i in idx],
        [1/min(R[i]['scales']) for i in idx],
        [1/math.log1p(len(R[i]['s'])) for i in idx],
    ])
    F=np.column_stack([ranknorm(raw[:,j]) for j in range(raw.shape[1])]);base=F@W
    sets=[R[i]['s'] for i in idx];inv2=defaultdict(list)
    for q,s in enumerate(sets):
        for e in s:inv2[e].append(q)
    overlaps=[{} for _ in sets]
    for q,s in enumerate(sets):
        cand=set()
        for e in s:cand.update(inv2[e])
        for j in cand:
            if j==q:continue
            inter=len(s&sets[j])
            if inter:overlaps[q][j]=inter/len(s|sets[j])
    avail=np.ones(len(idx),dtype=bool);mx=np.zeros(len(idx),float);order=[]
    for _ in range(len(idx)):
        score=base-LAMBDA*mx;score[~avail]=-1e99;q=int(np.argmax(score));order.append(q);avail[q]=False
        for j,v in overlaps[q].items():
            if avail[j] and v>mx[j]:mx[j]=v
    out=[]
    for rank,q in enumerate(order,1):
        x=R[idx[q]];s=x['s'];out.append({'rank':rank,'family_hash':fh(s),'indices':s,'member_count':len(s),'scales':sorted(x['scales']),'base_score':float(base[q])})
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--blind-source-parts',type=Path,required=True);ap.add_argument('--candidate-payload',type=Path,required=True);ap.add_argument('--baseline-payload',type=Path,required=True);ap.add_argument('--scorer-parts',type=Path,required=True);ap.add_argument('--recurrent-eom-source',type=Path,required=True);ap.add_argument('--scratch-loader',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as td0:
        td=Path(td0);blind=decode_blind_source(a.blind_source_parts,a.scratch_loader);blind.YEARS=YEARS;blind.MONTH_KEYS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13));args=types.SimpleNamespace(candidate_payload=a.candidate_payload,baseline_payload=a.baseline_payload,scorer_parts=a.scorer_parts);_candidate,base,_scorer=blind.load_sources(args);by_year,sources=blind.parse_catalogue(base);req(sorted(by_year)==list(YEARS),f'wrong years {sorted(by_year)}')
        events=[]
        for y in YEARS:events.extend(support_event(e) for e in by_year[y])
        req(len(events)==549636,f'full GMN event count drift {len(events)}');ids=[e['id'] for e in events];req(len(ids)==len(set(ids)),'duplicate IDs')
        X=feature_matrix(events);years=np.asarray([e['year'] for e in events],dtype=np.int16);cats={}
        for m in GRID:
            cats[m]=run_hdb(X,m);print(json.dumps({'mcs':m,'clusters':len(cats[m])}),flush=True)
        recurrent=run_recurrent(X,years,a.recurrent_eom_source);print(json.dumps({'recurrent_witness_clusters':len(recurrent)}),flush=True)
        ranked=build_multiscale(events,X,cats,recurrent);top=[]
        for r in ranked[:MAX_REVEAL_RANK]:
            event_ids=sorted(ids[i] for i in r['indices']);top.append({'rank':r['rank'],'family_hash':r['family_hash'],'member_count':r['member_count'],'scales':r['scales'],'base_score':r['base_score'],'event_ids':event_ids})
        payload={'schema':'ORBITTRACE_MULTISCALE_HDBSCAN_FINAL_BLIND_V1_STAGE_A','scientific_role':'TARGET_INCLUSIVE_GMN_2022_2023_LABEL_FREE_MULTISCALE_RANKING','event_count':len(events),'candidate_count':len(ranked),'grid':list(GRID),'weights':W.tolist(),'lambda':LAMBDA,'auxiliary_recurrent_hdbscan':{'min_cluster_size':10,'min_samples':10,'reportable':False,'candidate_count':len(recurrent)},'hdbscan_catalogue_counts':{str(k):len(v) for k,v in cats.items()},'top100':top,'catalogue_sources':sources,'target_reference_access':False,'canonical_target_ids_accessed':False,'target_coordinates_accessed':False,'activity_interval_used':False,'shower_labels_used':False,'post_result_parameter_search':False,'reranking_after_reveal':False}
        raw=json.dumps(payload,indent=2,sort_keys=True,allow_nan=False)+'\n';a.output.write_text(raw);print(json.dumps({'stage_a_sha256':hashlib.sha256(raw.encode()).hexdigest(),'candidate_count':len(ranked),'top100_count':len(top)},indent=2),flush=True)
if __name__=='__main__':main()
