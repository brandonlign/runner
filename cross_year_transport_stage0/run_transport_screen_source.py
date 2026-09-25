from __future__ import annotations
import argparse, collections, gzip, hashlib, json, math, random
from pathlib import Path
import numpy as np
from sklearn.metrics import roc_auc_score

YEARS=(2019,2021,2023,2025)
K_VALUES=(4,6,8)
RADII=(0.8,1.0,1.2,1.5,1.8,2.2)
EVENTS_PER_YEAR=64
REPLICATES=1
WINDOW=10.0
OBLIQUITY=math.radians(23.4392911)
GHOST_SOL=36.9
GHOST_RA=247.17
GHOST_DEC=-14.34
GHOST_VG=37.62


def args():
 p=argparse.ArgumentParser();p.add_argument('--events',type=Path,required=True);p.add_argument('--audit',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);return p.parse_args()
def stable(*x):return int.from_bytes(hashlib.sha256('|'.join(map(str,x)).encode()).digest()[:8],'big')
def wrap(x):return (x+180.0)%360.0-180.0
def angular_sep(ra1,dec1,ra2,dec2):
 a1,a2,d1,d2=map(math.radians,(ra1,ra2,dec1,dec2));v=math.sin(d1)*math.sin(d2)+math.cos(d1)*math.cos(d2)*math.cos(a1-a2);return math.degrees(math.acos(max(-1,min(1,v))))
def ghost_mask(e):return abs(wrap(float(e['sol'])-GHOST_SOL))<=6 and angular_sep(float(e['ra']),float(e['dec']),GHOST_RA,GHOST_DEC)<=12 and abs(float(e['vg'])-GHOST_VG)<=6
def ecliptic(e):
 ra=math.radians(float(e['ra']));dec=math.radians(float(e['dec']));x=math.cos(dec)*math.cos(ra);y=math.cos(dec)*math.sin(ra);z=math.sin(dec);xe=x;ye=math.cos(OBLIQUITY)*y+math.sin(OBLIQUITY)*z;ze=-math.sin(OBLIQUITY)*y+math.cos(OBLIQUITY)*z;return math.degrees(math.atan2(ye,xe))%360,math.degrees(math.asin(max(-1,min(1,ze))))
def vec(e,center):
 lon,lat=ecliptic(e);return np.array([wrap(float(e['sol'])-center)/2.0,wrap(lon-float(e['sol']))/3.0,lat/3.0,float(e['vg'])/3.0],dtype=np.float32)
def circ_mean(vals):
 z=np.mean(np.exp(1j*np.radians(vals)));return math.degrees(math.atan2(z.imag,z.real))%360

def load(path):
 showers=collections.defaultdict(list);spor=collections.defaultdict(list)
 with gzip.open(path,'rt',encoding='utf-8') as f:
  for line in f:
   e=json.loads(line);iau=int(e['iau']);y=int(e['year'])
   if iau>0:showers[(iau,y)].append(e)
   elif not ghost_mask(e):spor[(y,int(float(e['sol']))%360)].append(e)
 for k in showers:showers[k].sort(key=lambda e:(float(e['sol']),str(e['id'])))
 for key in spor:spor[key].sort(key=lambda e:(float(e['sol']),str(e['id'])))
 return showers,spor

def pool_bg(spor,year,center):
 out=[];c=int(center)%360;span=int(math.ceil(WINDOW))+1
 for d in range(-span,span+1):out.extend(spor.get((year,(c+d)%360),()))
 return [e for e in out if abs(wrap(float(e['sol'])-center))<=WINDOW]
def choose_near(events,center,count,rng):
 ranked=sorted(events,key=lambda e:(abs(wrap(float(e['sol'])-center)),str(e['id'])));eligible=[e for e in ranked if abs(wrap(float(e['sol'])-center))<=WINDOW]
 if len(eligible)<count:return None
 width=min(len(eligible),max(count,3*count));return rng.sample(eligible[:width],count)
def make_scene(iau,k,rep,kind,showers,spor):
 allm=[e for y in YEARS for e in showers[(iau,y)]]
 if not allm:return None
 mean=circ_mean([float(e['sol']) for e in allm]);ordered=sorted(allm,key=lambda e:(wrap(float(e['sol'])-mean),str(e['id'])));anchor=ordered[stable(iau,k,rep,'anchor')%len(ordered)];center=float(anchor['sol'])
 available=[y for y in YEARS if len([e for e in showers[(iau,y)] if abs(wrap(float(e['sol'])-center))<=WINDOW])>=max(k,3*k if kind=='artifact' else k)]
 if kind=='artifact':
  if not available:return None
  artifact_year=available[stable(iau,k,rep,'artifact')%len(available)];active=[]
 else:
  available=[y for y in YEARS if len([e for e in showers[(iau,y)] if abs(wrap(float(e['sol'])-center))<=WINDOW])>=k]
  if len(available)<3:return None
  rotation=stable(iau,k,rep,'active')%len(available);active=(available[rotation:]+available[:rotation])[:3];artifact_year=None
 Xs=[]
 for y in YEARS:
  rng=random.Random(stable(iau,k,rep,kind,y));nm=k if kind=='positive' and y in active else (3*k if kind=='artifact' and y==artifact_year else 0);members=choose_near(showers[(iau,y)],center,nm,rng) if nm else []
  if members is None:return None
  bgpool=pool_bg(spor,y,center)
  if len(bgpool)<EVENTS_PER_YEAR-nm:return None
  bg=rng.sample(bgpool,EVENTS_PER_YEAR-nm);ev=members+bg;rng.shuffle(ev);Xs.append(np.stack([vec(e,center) for e in ev]))
 return Xs

def greedy_edges(A,B,r):
 D=np.linalg.norm(A[:,None,:]-B[None,:,:],axis=2);ii,jj=np.where(D<=r);order=np.argsort(D[ii,jj]);ui=set();uj=set();out=[]
 for t in order:
  i=int(ii[t]);j=int(jj[t])
  if i in ui or j in uj:continue
  ui.add(i);uj.add(j);out.append((i,j,float(D[i,j])))
 return out

def cycle_transport_score(Xs,r):
 n=EVENTS_PER_YEAR;parent=list(range(4*n));edges=[]
 def find(a):
  while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
  return a
 def union(a,b):
  a=find(a);b=find(b)
  if a!=b:parent[b]=a
 for y in range(4):
  for z in range(y+1,4):
   for i,j,d in greedy_edges(Xs[y],Xs[z],r):
    a=y*n+i;b=z*n+j;union(a,b);edges.append((a,b,d))
 comps=collections.defaultdict(list)
 for node in range(4*n):comps[find(node)].append(node)
 ed=collections.defaultdict(list)
 for a,b,d in edges:ed[find(a)].append(d)
 weights=[]
 for root,nodes in comps.items():
  coverage=len({node//n for node in nodes})
  if coverage<3:continue
  consistency=coverage/len(nodes);md=float(np.mean(ed[root])) if ed[root] else r;weights.append((coverage-2)*consistency*math.exp(-0.5*(md/r)**2))
 weights.sort(reverse=True);return float(sum(weights[:12]))

def score_scene(Xs):
 allx=np.concatenate(Xs,axis=0);Dall=np.linalg.norm(allx[:,None,:]-allx[None,:,:],axis=2);Dyears=[[None]*4 for _ in range(4)]
 for i in range(4):
  for j in range(i+1,4):Dyears[i][j]=np.linalg.norm(Xs[i][:,None,:]-Xs[j][None,:,:],axis=2)
 out={}
 for r in RADII:
  pooled=float(np.max(np.sum(Dall<=r,axis=1)-1));annual=[]
  for X in Xs:
   D=np.linalg.norm(X[:,None,:]-X[None,:,:],axis=2);annual.append(float(np.max(np.sum(D<=r,axis=1)-1)))
  annual_confirmation=float(sorted(annual,reverse=True)[2]);supports=[]
  for y in range(4):
   for i in range(EVENTS_PER_YEAR):
    s=0.0
    for z in range(4):
     if z==y:continue
     D=Dyears[min(y,z)][max(y,z)];md=float(np.min(D[i,:])) if y<z else float(np.min(D[:,i]));s+=math.exp(-0.5*(md/r)**2) if md<=2*r else 0.0
    supports.append(s)
  supports.sort(reverse=True);cross=float(sum(supports[:12]));out[r]={'pooled_density':pooled,'annual_confirmation':annual_confirmation,'crossyear_support':cross,'cycle_partial_transport':cycle_transport_score(Xs,r)}
 return out

def episodes_for_units(units,profiles,showers,spor):
 iaus=sorted([iau for iau,p in profiles.items() if p['complex_key'] in units],key=lambda x:stable('panel',x))[:8];rec=[]
 for iau in iaus:
  for k in K_VALUES:
   for rep in range(REPLICATES):
    for kind in ('positive','negative','artifact'):
     X=make_scene(iau,k,rep,kind,showers,spor)
     if X is not None:rec.append({'iau':iau,'k':k,'rep':rep,'kind':kind,'scores':score_scene(X)})
 return rec

def auc(records,r,method):
 use=[x for x in records if x['kind'] in ('positive','negative')];y=[x['kind']=='positive' for x in use];s=[x['scores'][r][method] for x in use];return roc_auc_score(y,s) if len(set(y))==2 else float('nan')
def artifact_rate(records,r,method,threshold):
 vals=[x['scores'][r][method] for x in records if x['kind']=='artifact'];return float(np.mean(np.array(vals)>=threshold)) if vals else float('nan')
def neg_threshold(records,r,method):
 vals=[x['scores'][r][method] for x in records if x['kind']=='negative'];return float(np.quantile(vals,.90)) if vals else float('nan')

def main():
 a=args();a.output.mkdir(parents=True,exist_ok=True);audit=json.load(open(a.audit));base=json.load(open(a.baseline));showers,spor=load(a.events);profiles={int(p['iau']):p for p in audit['profiles'] if p.get('eligible')};folds={int(k):set(v) for k,v in base['fold_units'].items()};methods=('pooled_density','annual_confirmation','crossyear_support','cycle_partial_transport');fold_results=[];records_by_fold={f:episodes_for_units(folds[f],profiles,showers,spor) for f in range(5)}
 for f in range(5):
  val=records_by_fold[(f+1)%5];test=records_by_fold[f];fr={'fold':f,'validation_scenes':len(val),'test_scenes':len(test),'methods':{}}
  for m in methods:
   vals={str(r):auc(val,r,m) for r in RADII};best=max(RADII,key=lambda r:(-999 if math.isnan(vals[str(r)]) else vals[str(r)],-r));ta=auc(test,best,m);th=neg_threshold(val,best,m);ar=artifact_rate(test,best,m,th);fr['methods'][m]={'validation_aucs':vals,'selected_radius':best,'test_auc':ta,'validation_negative_threshold':th,'test_artifact_detection_rate':ar}
  fold_results.append(fr)
 mean={m:float(np.mean([x['methods'][m]['test_auc'] for x in fold_results])) for m in methods};artifact={m:float(np.mean([x['methods'][m]['test_artifact_detection_rate'] for x in fold_results])) for m in methods};best=max(mean,key=mean.get);best_auc=mean[best];candidate='cycle_partial_transport';reference='crossyear_support';fold_wins=sum(fr['methods'][candidate]['test_auc']>=fr['methods'][reference]['test_auc']-.03 for fr in fold_results);gates={'candidate_mean_auc_at_least_0_90':mean[candidate]>=.90,'candidate_within_0_03_of_crossyear_support':mean[candidate]>=mean[reference]-.03,'candidate_artifact_rate_at_most_0_10':artifact[candidate]<=.10,'artifact_improvement_at_least_0_05':artifact[reference]-artifact[candidate]>=.05,'at_least_four_folds_no_material_auc_collapse':fold_wins>=4};verdict='PROCEED_TO_FULL_PARTIAL_TRANSPORT_BENCHMARK' if all(gates.values()) else 'KILL_CYCLE_CONSISTENT_PARTIAL_TRANSPORT';payload={'configuration':{'years':YEARS,'k_values':K_VALUES,'radii':RADII,'events_per_year':EVENTS_PER_YEAR,'replicates':REPLICATES,'active_years':3,'window_deg':WINDOW,'ghoststream_masked':True},'fold_results':fold_results,'mean_aucs':mean,'mean_artifact_detection_rates':artifact,'best_baseline':best,'best_baseline_mean_auc':best_auc,'reference_method':reference,'candidate_method':candidate,'folds_without_material_collapse':fold_wins,'gates':gates,'verdict':verdict};(a.output/'transport_screen.json').write_text(json.dumps(payload,indent=2,default=lambda o:o.item() if hasattr(o,'item') else str(o)));lines=['# Cycle-consistent partial transport screening','',f"Candidate mean AUROC: **{mean[candidate]:.4f}**",f"Cross-year-support AUROC: **{mean[reference]:.4f}**",f"Candidate artifact rate: **{artifact[candidate]:.4f}**",f"Cross-year-support artifact rate: **{artifact[reference]:.4f}**",'',f"Verdict: **{verdict}**",'']+[f"- {'PASS' if v else 'FAIL'} — `{k}`" for k,v in gates.items()];(a.output/'REPORT.md').write_text('\n'.join(lines));print('\n'.join(lines))
if __name__=='__main__':main()
