#!/usr/bin/env python3
"""Preregistered development-only test of variable-source loss in 5XMM.

Hypothesis and analysis were frozen in brandonlign/isef before querying FRATIO values.
Even 30-degree RA sectors only. Odd-sector holdout remains closed. No source identities
or coordinates are emitted; only aggregate/model statistics.
"""
from pathlib import Path
from collections import defaultdict
import io,json,math,urllib.parse,urllib.request
import numpy as np
from astropy.io import fits
from astropy.table import Table
from astropy.coordinates import SkyCoord
import astropy.units as u
import statsmodels.api as sm
OUT=Path('results/xmm_development_variability_mechanism.json');OUT.parent.mkdir(parents=True,exist_ok=True)
E5='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync';T5='xmmstack'
E4='https://sky.esa.int/esasky-tap/tap/sync';T4='catalogues.mv_xsa_epic_stack_cat_fdw'
U5='https://xmmssc.aip.de/files/dr15/5xmmdr15_stacklist.fits.gz';U4='https://xmmssc.aip.de/files/dr14s/xmmstack_v3.2_4xmmdr14s_obslist.fits.gz'
SECS=(0,2,4,6,8,10);MARGIN=.04

def cv(x):
 if np.ma.is_masked(x):return None
 if isinstance(x,(bytes,np.bytes_)):return x.decode('utf-8','replace').strip()
 if hasattr(x,'item'):
  try:return x.item()
  except:return str(x)
 return x

def tap(ep,q,timeout=420):
 d=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','QUERY':q}).encode();req=urllib.request.Request(ep,data=d,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-XMM-var-mech/1.0'})
 with urllib.request.urlopen(req,timeout=timeout) as r:raw=r.read()
 t=Table.read(io.BytesIO(raw),format='votable');return [{n:cv(rr[n]) for n in t.colnames} for rr in t]
def stacks(url,p):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-var-mech/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r,p.open('wb') as f:
  while True:
   b=r.read(1<<20)
   if not b:break
   f.write(b)
 with fits.open(p,memmap=False) as h:
  tabs=[z for z in h if getattr(z,'data',None) is not None and hasattr(z.data,'names') and z.data.names];d=max(tabs,key=lambda z:len(z.data)).data
  s=defaultdict(set);rev=defaultdict(set)
  for x in d:
   a=str(cv(x['STACK_ID']));o=str(cv(x['OBS_ID']));s[a].add(o);rev[o].add(a)
  return dict(s),dict(rev)
def maps():
 s4,r4=stacks(U4,Path('/tmp/v4.gz'));s5,r5=stacks(U5,Path('/tmp/v5.gz'));bad4={a for v in r4.values() if len(v)>1 for a in v};bad5={a for v in r5.values() if len(v)>1 for a in v};by5=defaultdict(list)
 for a,o in s5.items():by5[frozenset(o)].append(a)
 ps=[(a,b) for a,o in s4.items() for b in by5.get(frozenset(o),[]) if a not in bad4 and b not in bad5];m45=dict(ps);m54={b:a for a,b in ps};e4={o:next(iter(v)) for o,v in r4.items() if len(v)==1 and next(iter(v)) in m45};e5={o:next(iter(v)) for o,v in r5.items() if len(v)==1 and next(iter(v)) in m54};return m45,m54,e4,e5
def par(x,e):
 s=str(x);return e.get(s[1:11]) if len(s)==16 and s.startswith('3') and s.isdigit() else None
def clause(lo,hi,m=0):
 a=lo-m;b=hi+m
 if a<0:return f'(ra>={360+a:.8f} OR ra<{b:.8f})'
 if b>=360:return f'(ra>={a:.8f} OR ra<{b-360:.8f})'
 return f'(ra>={a:.8f} AND ra<{b:.8f})'
def fnum(x):
 try:
  v=float(x);return v if np.isfinite(v) else None
 except:return None

def classify_loss(old,new_by_parent,m45,radius):
 p4=old['parent'];p5=m45.get(p4);pool=new_by_parent.get(p5,[])
 if not pool:return 1
 c=SkyCoord(old['ra']*u.deg,old['dec']*u.deg);t=SkyCoord([x[0] for x in pool]*u.deg,[x[1] for x in pool]*u.deg);_,sp,_=c.match_to_catalog_sky(t)
 s=float(np.asarray(sp.arcsec).reshape(-1)[0]);return int(s>radius)
def raw_or(y,strong):
 y=np.asarray(y,int);s=np.asarray(strong,int);a=int(np.sum((s==1)&(y==1)));b=int(np.sum((s==1)&(y==0)));c=int(np.sum((s==0)&(y==1)));d=int(np.sum((s==0)&(y==0)))
 # Haldane correction only if a cell is zero
 aa,bb,cc,dd=(a,b,c,d) if min(a,b,c,d)>0 else (a+.5,b+.5,c+.5,d+.5)
 return {'strong_lost':a,'strong_retained':b,'weak_lost':c,'weak_retained':d,'strong_loss_fraction':a/(a+b) if a+b else None,'weak_loss_fraction':c/(c+d) if c+d else None,'odds_ratio':(aa*dd)/(bb*cc)}
def fit_model(rows,radius,min_ml):
 z=[r for r in rows if r['ep_det_ml']>=min_ml]
 y=np.array([r[f'lost{int(radius)}'] for r in z],float);strong=np.array([int(r['fratio']>=5) for r in z],float);logml=np.log(np.array([r['ep_det_ml'] for r in z],float));ncon=np.log1p(np.array([r['n_contrib'] for r in z],float));perr=np.log1p(np.array([r['radec_err'] for r in z],float));secs=np.array([r['sector'] for r in z],int)
 # categorical sector fixed effects: sector 0 reference
 X=[np.ones(len(z)),strong,logml,ncon,perr];names=['intercept','fratio_ge5','log_ep_det_ml','log1p_n_contrib','log1p_radec_err']
 for s in SECS[1:]:X.append((secs==s).astype(float));names.append(f'sector_{s}')
 X=np.column_stack(X);groups=np.array([r['parent'] for r in z])
 try:
  fit=sm.GLM(y,X,family=sm.families.Binomial()).fit(cov_type='cluster',cov_kwds={'groups':groups})
  i=names.index('fratio_ge5');beta=float(fit.params[i]);se=float(fit.bse[i]);p=float(fit.pvalues[i]);lo=beta-1.959963984540054*se;hi=beta+1.959963984540054*se
  model={'success':True,'n':len(z),'lost':int(y.sum()),'loss_fraction':float(y.mean()),'strong_n':int(strong.sum()),'strong_fraction':float(strong.mean()),'clusters':len(set(groups)),'adjusted_or':math.exp(beta),'ci95':[math.exp(lo),math.exp(hi)],'p_value':p,'beta':beta,'se_cluster':se,'raw':raw_or(y,strong)}
 except Exception as e:model={'success':False,'error':f'{type(e).__name__}: {e}','n':len(z),'raw':raw_or(y,strong)}
 return model
def main():
 try:
  m45,m54,e4,e5=maps();old=[];new=defaultdict(list);qcounts={}
  for sec in SECS:
   lo=sec*30;hi=lo+30
   # Primary DR14 population and frozen variability/covariate fields only.
   q4=f"SELECT TOP 200000 srcid,ra,dec,radec_err,stack_flag,extent,ep_det_ml,n_obs,n_contrib,fratio FROM {T4} WHERE n_obs IS NOT NULL AND {clause(lo,hi)} AND stack_flag<=1 AND extent=0 AND ep_det_ml>=10 AND n_contrib>=2 AND fratio IS NOT NULL"
   # Conservative counterpart pool: ANY 5XMM summary source, regardless of quality/likelihood/extent.
   q5=f"SELECT TOP 200000 srcid,ra,dec,n_obs FROM {T5} WHERE n_obs IS NOT NULL AND {clause(lo,hi,MARGIN)}"
   a=tap(E4,q4);b=tap(E5,q5);ka=[];kb=0
   for r in a:
    p=par(r['srcid'],e4);fr=fnum(r.get('fratio'));ml=fnum(r.get('ep_det_ml'));nc=fnum(r.get('n_contrib'));pe=fnum(r.get('radec_err'))
    if p not in m45 or fr is None or fr<=0 or ml is None or nc is None or nc<2 or pe is None or pe<0:continue
    ka.append({'parent':p,'ra':float(r['ra']),'dec':float(r['dec']),'fratio':fr,'ep_det_ml':ml,'n_contrib':nc,'radec_err':pe,'sector':sec})
   for r in b:
    p=par(r['srcid'],e5)
    if p in m54:new[p].append((float(r['ra']),float(r['dec'])));kb+=1
   old.extend(ka);qcounts[str(sec)]={'dr14_raw':len(a),'dr14_eligible':len(ka),'dr15_any_summary_raw':len(b),'dr15_exact_input_rows':kb,'top_truncated':len(a)>=200000 or len(b)>=200000}
  for r in old:
   for rad in (5.,7.,10.,15.):r[f'lost{int(rad)}']=classify_loss(r,new,m45,rad)
  primary=fit_model(old,5.,10.);ml15=fit_model(old,5.,15.);r7=fit_model(old,7.,10.)
  # sector-specific raw effects; used only to verify no single sector drives direction.
  sectors={}
  for s in SECS:
   zz=[r for r in old if r['sector']==s];sectors[str(s)]={'n':len(zz),'lost5':sum(r['lost5'] for r in zz),'raw':raw_or([r['lost5'] for r in zz],[int(r['fratio']>=5) for r in zz]) if zz else None}
  conditions={'primary_or_gt1':primary.get('adjusted_or',0)>1 if primary.get('success') else False,'primary_ci_low_gt1':primary.get('ci95',[0])[0]>1 if primary.get('success') else False,'ml15_direction_gt1':ml15.get('adjusted_or',0)>1 if ml15.get('success') else False,'r7_direction_gt1':r7.get('adjusted_or',0)>1 if r7.get('success') else False,'all_nonempty_sectors_direction_gt1':all((v['raw']['odds_ratio']>1) for v in sectors.values() if v['raw'] and min(v['raw']['strong_lost']+v['raw']['strong_retained'],v['raw']['weak_lost']+v['raw']['weak_retained'])>0)}
  passed=all(conditions.values())
  out={'success':True,'status':'DEVELOPMENT_ONLY','holdout_opened':False,'exact_pairs':len(m45),'fratio_threshold_frozen':5.0,'primary_loss_radius_arcsec_frozen':5.0,'query_counts':qcounts,'eligible_dr14_sources':len(old),'primary_ml10_r5':primary,'sensitivity_ml15_r5':ml15,'sensitivity_ml10_r7':r7,'sector_raw_effects':sectors,'success_conditions':conditions,'decision':'VARIABILITY_MECHANISM_DEVELOPMENT_PASS' if passed else 'VARIABILITY_MECHANISM_DEVELOPMENT_FAIL','note':'No source identities or coordinates emitted. FRATIO>=5 and covariates were preregistered before source variability values were queried. 5XMM loss means no 5XMM summary source of any quality within radius in the exact paired parent stack.'}
 except Exception as e:out={'success':False,'status':'DEVELOPMENT_ONLY','holdout_opened':False,'error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
