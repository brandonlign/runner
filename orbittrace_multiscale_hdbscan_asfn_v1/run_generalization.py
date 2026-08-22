#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math, zipfile
from collections import Counter, defaultdict
from pathlib import Path
import hdbscan, numpy as np
from scipy.optimize import linear_sum_assignment

YEARS=(2018,2019); BLIND=(20.0,55.0)
ARCHIVE_SHA='c091b0f3f87f10badbe5fa38e6c45ba818af99f1c27c2fd6a23be286074c89a4'
README_SHA='74bacb50b225032461ba8b200eec0d5274799ef3c2700cb9a3465b4d5c02a2bf'
DATA='nasfn_2013-2019_data.txt'; README='nasfn_2013-2019_readme.txt'
GRID=(10,20,30,40,50,60,70,80,90,100,120,150,200,300,500,750,1000)
W=np.array([0.335,0.250,0.230,0.215,0.128,0.145,1.0,0.0],float); LAMBDA=0.25
FIELDS=("time","jd","slon","n","Qstar","sat","lat1","dlat1","lon1","dlon1","h1","dh1","lat2","dlat2","lon2","dlon2","h2","dh2","dur","mag","L_int","eta_p","deta_p","rho_p","drho_p","v_p","dv_p","alp_g","dalp_g","del_g","ddel_g","v_g","dv_g","lam_g","dlam_g","bet_g","dbet_g","q","e","incl","omega","anode","shw","T_j")
IDX={k:i for i,k in enumerate(FIELDS)}
def req(x,m):
 if not x: raise RuntimeError(m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def fh(ids): return hashlib.sha256(json.dumps(sorted(ids),separators=(',',':')).encode()).hexdigest()[:20]
def pf(x):
 try: v=float(x); return v if math.isfinite(v) else None
 except: return None

def parse_events(archive):
 req(sha(archive)==ARCHIVE_SHA,'archive hash drift'); out=[]; stats=Counter()
 with zipfile.ZipFile(archive) as z:
  ds=[i for i in z.infolist() if Path(i.filename).name==DATA]; rs=[i for i in z.infolist() if Path(i.filename).name==README]
  req(len(ds)==len(rs)==1,'archive members drift'); req(hashlib.sha256(z.read(rs[0].filename)).hexdigest()==README_SHA,'readme hash drift')
  ix=0; header=False
  with z.open(ds[0].filename) as f:
   for raw in f:
    line=raw.decode().strip()
    if not line: continue
    t=line.split()
    if not header and t[0].lower()=='time': header=True; continue
    ix+=1
    if len(t)<len(FIELDS): continue
    tt=t[IDX['time']]
    if len(tt)<4 or not tt[:4].isdigit(): continue
    y=int(tt[:4]); sol=pf(t[IDX['slon']])
    if y not in YEARS or sol is None: continue
    sol%=360
    if BLIND[0]<=sol<=BLIND[1]: continue
    lam=pf(t[IDX['lam_g']]); lat=pf(t[IDX['bet_g']]); vg=pf(t[IDX['v_g']])
    if lam is None or lat is None or vg is None or vg<=0: continue
    out.append({'id':f'ASFN:{ix}','row_index':ix,'year':y,'sol':sol,'lon':(lam-sol)%360,'lat':lat,'vg':vg});stats[y]+=1
 req(dict(stats)=={2018:4679,2019:4548},f'event counts drift {stats}')
 return out

def labels(archive,events):
 wanted={e['row_index']:e['id'] for e in events}; out={}
 with zipfile.ZipFile(archive) as z:
  d=[i for i in z.infolist() if Path(i.filename).name==DATA][0]; ix=0; header=False
  with z.open(d.filename) as f:
   for raw in f:
    line=raw.decode().strip()
    if not line: continue
    t=line.split()
    if not header and t[0].lower()=='time': header=True;continue
    ix+=1
    if ix not in wanted: continue
    code=t[IDX['shw']].strip();out[wanted[ix]]='SPORADIC' if code in {'','...'} else code
 req(len(out)==len(events),'label count mismatch');return out

def Xmat(events):
 sol=np.radians([e['sol'] for e in events]);lon=np.radians([e['lon'] for e in events]);lat=np.radians([e['lat'] for e in events]);vg=np.array([e['vg'] for e in events])
 return np.column_stack((np.cos(sol),np.sin(sol),np.sin(lon)*np.cos(lat),np.cos(lon)*np.cos(lat),np.sin(lat),vg/72.0))

def run_hdb(X,events,mcs):
 m=hdbscan.HDBSCAN(min_cluster_size=mcs,min_samples=None,metric='euclidean',cluster_selection_method='eom',allow_single_cluster=False,prediction_data=False,core_dist_n_jobs=1).fit(X)
 labs=m.labels_; probs=m.probabilities_; out=[]
 for lab in sorted(int(v) for v in np.unique(labs) if v>=0):
  ix=np.flatnonzero(labs==lab); ids=tuple(sorted(events[i]['id'] for i in ix));out.append({'family_id':'H'+fh(ids),'event_ids':list(ids),'member_count':len(ids),'mean_membership_probability':float(np.mean(probs[ix]))})
 return out

def ranknorm(v):
 v=np.asarray(v,float);o=np.argsort(v,kind='mergesort');z=np.empty(len(v));z[o]=np.linspace(0,1,len(v));return z

def build_multiscale(events,cats,recurrent):
 year={e['id']:e['year'] for e in events};vec={}
 for e in events:
  s=np.radians(e['sol']);l=np.radians(e['lon']);b=np.radians(e['lat']);vec[e['id']]=np.array([np.cos(s),np.sin(s),np.sin(l)*np.cos(b),np.cos(l)*np.cos(b),np.sin(b),e['vg']/72])
 D={}
 for mcs,fs in cats.items():
  for f in fs:
   s=frozenset(f['event_ids']);x=D.setdefault(s,{'s':s,'scales':[],'hprobs':[],'r':None});x['scales'].append(int(mcs));x['hprobs'].append(float(f['mean_membership_probability']))
 for f in recurrent:
  s=frozenset(f['event_ids']);x=D.setdefault(s,{'s':s,'scales':[],'hprobs':[],'r':None});x['r']=f
 R=list(D.values());inv=defaultdict(set)
 for i,x in enumerate(R):
  for e in x['s']:inv[e].add(i)
 for i,x in enumerate(R):
  cand=set()
  for e in x['s']:cand.update(inv[e])
  best=0.0
  for j in cand:
   if j==i:continue
   aa,bb=x['s'],R[j]['s'];best=max(best,len(aa&bb)/len(aa|bb))
  ids=list(x['s']);V=np.array([vec[e] for e in ids]);cen=V.mean(0);scatter=float(np.mean(np.sum((V-cen)**2,axis=1)))
  a=[e for e in ids if year[e]==2018];b=[e for e in ids if year[e]==2019]
  if a and b:
   A=np.array([vec[e] for e in a]);B=np.array([vec[e] for e in b]);ca=A.mean(0);cb=B.mean(0);sa=float(np.mean(np.sum((A-ca)**2,axis=1)));sb=float(np.mean(np.sum((B-cb)**2,axis=1)));sync=float(np.linalg.norm(ca-cb)/(math.sqrt((sa+sb)/2)+1e-9))
  else: sync=9.0
  x.update(bestj=best,scatter=scatter,sync=sync,balance=2*min(len(a),len(b))/len(ids))
 idx=[i for i,x in enumerate(R) if x['scales']]
 raw=np.column_stack([[R[i]['bestj'] for i in idx],[1/(1+R[i]['scatter']) for i in idx],[1/(1+R[i]['sync']) for i in idx],[R[i]['balance'] for i in idx],[max(R[i]['hprobs']) for i in idx],[len(R[i]['scales']) for i in idx],[1/min(R[i]['scales']) for i in idx],[1/math.log1p(len(R[i]['s'])) for i in idx]])
 F=np.column_stack([ranknorm(raw[:,j]) for j in range(raw.shape[1])]);base=F@W
 sets=[R[i]['s'] for i in idx]; inv2=defaultdict(list)
 for q,s in enumerate(sets):
  for e in s:inv2[e].append(q)
 overlaps=[{} for _ in sets]
 for q,s in enumerate(sets):
  cand=set()
  for e in s:cand.update(inv2[e])
  for j in cand:
   if j==q:continue
   overlaps[q][j]=len(s&sets[j])/len(s|sets[j])
 avail=np.ones(len(idx),bool);mx=np.zeros(len(idx));order=[]
 for _ in range(len(idx)):
  score=base-LAMBDA*mx;score[~avail]=-1e99;q=int(np.argmax(score));order.append(q);avail[q]=False
  for j,v in overlaps[q].items():
   if avail[j] and v>mx[j]:mx[j]=v
 out=[]
 for rank,q in enumerate(order,1):
  x=R[idx[q]];out.append({'family_id':'MS'+fh(x['s']),'event_ids':sorted(x['s']),'rank':rank,'scales':sorted(x['scales']),'score':float(base[q])})
 return out

def matrix_score(fams,truth,event_year,year,budget=None):
 annual={e for e,y in event_year.items() if y==year};cnt=Counter(truth[e] for e in annual if truth[e]!='SPORADIC');labs=sorted(k for k,n in cnt.items() if n>=4);active=[]
 for f in fams:
  s=set(f['event_ids'])&annual
  if s:active.append(s)
 if budget is not None:active=active[:budget]
 M=np.zeros((len(labs),len(active)))
 for i,l in enumerate(labs):
  T={e for e in annual if truth[e]==l}
  for j,s in enumerate(active):
   o=len(T&s)
   if o:M[i,j]=2*o/(len(T)+len(s))
 n=max(M.shape) if M.size else len(labs);C=np.zeros((n,n));C[:M.shape[0],:M.shape[1]]=-M
 ri,cj=linear_sum_assignment(C);vals=[M[i,j] if j<M.shape[1] else 0 for i,j in zip(ri,cj) if i<len(labs)]
 return {'eligible_showers':len(labs),'candidate_used':len(active),'macro_f1':float(np.mean(vals)) if vals else 0.0,'recovered':int(sum(v>.5 for v in vals))}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--historical-prelabel',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 ev=parse_events(a.archive);event_year={e['id']:e['year'] for e in ev};X=Xmat(ev)
 cats={}
 for m in GRID:
  cats[m]=run_hdb(X,ev,m);print(json.dumps({'mcs':m,'clusters':len(cats[m])}),flush=True)
 hist=json.loads(a.historical_prelabel.read_text());req(hist['target_information_access'] is False,'historical prelabel target contaminated');rec=hist['recurrent_candidates']
 req({e['id'] for e in ev}=={e['id'] for e in hist['events']},'historical ASFN event universe drift')
 successor=build_multiscale(ev,cats,rec)
 pre={'role':'FROZEN_SONOTACO_DERIVED_MULTISCALE_HDBSCAN_ASFN_PRETRUTH','grid':list(GRID),'weights':W.tolist(),'lambda':LAMBDA,'events':len(ev),'catalogue_counts':{str(k):len(v) for k,v in cats.items()},'successor':successor,'target_information_access':False,'truth_accessed':False}
 (a.output/'PRETRUTH.json').write_text(json.dumps(pre,sort_keys=True,separators=(',',':'))+'\n')
 truth=labels(a.archive,ev)
 results=[]
 for test,dev in ((2018,2019),(2019,2018)):
  grid=[]
  for m in GRID:grid.append({'mcs':m,**matrix_score(cats[m],truth,event_year,dev)})
  chosen=max(grid,key=lambda x:(x['macro_f1'],x['recovered'],-x['mcs']))['mcs'];base=matrix_score(cats[chosen],truth,event_year,test);succ=matrix_score(successor,truth,event_year,test,base['candidate_used']);win=succ['macro_f1']>base['macro_f1'] and succ['recovered']>=base['recovered']
  results.append({'dev_year':dev,'test_year':test,'selected_mcs':chosen,'hdbscan':base,'multiscale':succ,'pass':win,'calibration_grid':grid})
 verdict='PASS_MULTISCALE_HDBSCAN_ASFN_GENERALIZATION_V1' if all(r['pass'] for r in results) else 'FAIL_MULTISCALE_HDBSCAN_ASFN_GENERALIZATION_V1'
 out={'verdict':verdict,'results':results,'scientific_role':'CROSS_SURVEY_TRANSFER_USING_PREVIOUSLY_PROJECT_EXPOSED_ASFN_WITH_NO_MULTISCALE_TUNING','weights':W.tolist(),'lambda':LAMBDA,'target_information_access':False,'post_result_parameter_search':False}
 (a.output/'RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':main()
