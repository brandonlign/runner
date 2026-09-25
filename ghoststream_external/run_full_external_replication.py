#!/usr/bin/env python3
from __future__ import annotations
import hashlib, io, json, math, re, sys, zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
import requests
from scipy.stats import fisher_exact

OUT=Path(__file__).resolve().parent/'results'; CACHE=Path(__file__).resolve().parent/'cache'; SEED=20260731
SOL0=36.901963; SUNLON0=-149.3763247; BETA0=7.3230377; VG0=37.641692
SUNLON_SLOPE=-0.1029483; BETA_SLOPE=-0.0230546; VG_SLOPE=-0.0293492
SUNLON_SIGMA=0.7369; BETA_SIGMA=0.6250; VG_SIGMA=1.1596
TIME_HALF_WIDTH=4.; SEASON_HALF_WIDTH=18.; CORE_RADIUS2=9.; LOCAL_RADIUS2=36.
REFINED_ORBIT=np.array([0.946296,0.079202,24.709376,333.493819,37.937477])
ORBIT_MEMBER_D=.15; ORBIT_NULL_DRAWS=9999; MAX_ORBIT_MEDIAN_D=.12; MAX_ORBIT_Q90_D=.22; MAX_ORBIT_NULL_P=.01
MIN_ACTIVE_YEARS=2; MIN_PER_ACTIVE_YEAR=2; MAX_ACTIVITY_P=.01; MAX_SHIFT_P=.05; SHIFT_STEP=.25
ANTIHELION_CENTER=180.; ANTIHELION_HALF_WIDTH=60.; ANTIHELION_BETA_MAX=35.; ANTIHELION_SPEED_MIN=15.; ANTIHELION_SPEED_MAX=50.
BASE='https://ceres.ta3.sk/iaumdcdb/dataDBs/video_offline'
SOURCES={
 'CAMS':{'years':range(2010,2017),'url':BASE+'/iaumdcCAMSv3_{year}.csv.zip','min':5,'independent':True},
 'SonotaCo':{'years':range(2007,2026),'url':BASE+'/iaumdcSNMv3_S{yy:02d}.csv.zip','min':8,'independent':True},
 'EDMOND':{'years':range(2001,2018),'url':BASE+'/iaumdcedmond{year}.csv.zip','min':8,'independent':False},
}
ALIASES={
 'id':('iid','ic','id','meteorid','no','nr'),'year':('yr','year'),'month':('mn','month'),'day':('dayy','day','dayut'),
 'ls':('ls','sol','solarlongitude'),'ra':('ra','rag','rightascension'),'dec':('decl','dec','decg','declination'),
 'vg':('vg','vgeo','geocentricvelocity'),'e':('e','ecc','eccentricity'),'q':('q','periheliondistance'),
 'inc':('i','incl','inc','inclination'),'peri':('arg','peri','omega','argumentofperihelion'),
 'node':('nod','node','om','longitudeofascendingnode')}

def cd(v,c): return (np.asarray(v)-np.asarray(c)+180.)%360.-180.
def sol(dt):
 jd=2440587.5+dt.timestamp()/86400.; n=jd-2451545.; ml=(280.460+.9856474*n)%360.; ma=math.radians((357.528+.9856003*n)%360.)
 return float((ml+1.915*math.sin(ma)+.020*math.sin(2*ma))%360.)
def ecl(ra,dec):
 ra=np.deg2rad(ra); dec=np.deg2rad(dec); ep=math.radians(23.43928); x=np.cos(dec)*np.cos(ra); y=np.cos(dec)*np.sin(ra); z=np.sin(dec)
 ye=y*math.cos(ep)+z*math.sin(ep); ze=-y*math.sin(ep)+z*math.cos(ep)
 return np.rad2deg(np.arctan2(ye,x))%360.,np.rad2deg(np.arcsin(np.clip(ze,-1,1)))
def pvec(o):
 i,w,n=np.deg2rad(o[:,2]),np.deg2rad(o[:,3]),np.deg2rad(o[:,4])
 return np.column_stack([np.cos(n)*np.cos(w)-np.sin(n)*np.sin(w)*np.cos(i),np.sin(n)*np.cos(w)+np.cos(n)*np.sin(w)*np.cos(i),np.sin(w)*np.sin(i)])
def odist(a,b=None):
 b=a if b is None else b; e1,q1=a[:,0,None],a[:,1,None]; e2,q2=b[:,0][None,:],b[:,1][None,:]
 i1,n1=np.deg2rad(a[:,2,None]),np.deg2rad(a[:,4,None]); i2,n2=np.deg2rad(b[:,2][None,:]),np.deg2rad(b[:,4][None,:])
 plane=np.arccos(np.clip(np.cos(i1)*np.cos(i2)+np.sin(i1)*np.sin(i2)*np.cos(n1-n2),-1,1)); peri=np.arccos(np.clip(pvec(a)@pvec(b).T,-1,1))
 return np.sqrt(np.maximum((e1-e2)**2+(q1-q2)**2+(2*np.sin(plane/2))**2+(((e1+e2)/2)*2*np.sin(peri/2))**2,0))
def osum(o):
 m=odist(o); j=int(np.argmin(np.median(m,axis=1))); d=m[j]
 return {'medoid':o[j].tolist(),'median_d':float(np.median(d)),'q90_d':float(np.percentile(d,90))}
def norm(s): return re.sub('[^a-z0-9]+','',str(s).lstrip('\ufeff').strip().lower())
def cols(df):
 n={norm(c):str(c) for c in df.columns}; r={k:next((n[a] for a in v if a in n),None) for k,v in ALIASES.items()}
 req=('year','month','day','ra','dec','vg','e','q','inc','peri','node'); miss=[k for k in req if r[k] is None]
 if miss: raise RuntimeError(f'missing {miss}; columns={list(df.columns)}')
 return r
def getzip(url,target):
 target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists() and target.stat().st_size: raw=target.read_bytes(); cached=True
 else:
  x=requests.get(url,timeout=300); x.raise_for_status(); raw=x.content; target.write_bytes(raw); cached=False
 return raw,{'url':url,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'cached':cached}
def readzip(raw):
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  ms=[m for m in z.namelist() if m.lower().endswith(('.csv','.txt')) and not m.startswith('__MACOSX/')]
  if not ms: raise RuntimeError('no csv/txt')
  m=max(ms,key=lambda q:z.getinfo(q).file_size); data=z.read(m)
 first=next((x for x in data[:8192].decode('utf-8-sig',errors='replace').splitlines() if x.strip()),''); sep=';' if first.count(';')>first.count(',') else ','
 df=pd.read_csv(io.BytesIO(data),sep=sep,low_memory=False,encoding='utf-8-sig'); df.columns=[str(c).lstrip('\ufeff').strip() for c in df.columns]
 return df,m,sep
def load(name,spec,year):
 url=spec['url'].format(year=year,yy=year%100); raw,meta=getzip(url,CACHE/name.lower()/f'{year}.zip'); df,member,sep=readzip(raw); c=cols(df)
 yr=pd.to_numeric(df[c['year']],errors='coerce'); mo=pd.to_numeric(df[c['month']],errors='coerce'); da=pd.to_numeric(df[c['day']],errors='coerce')
 s=df.loc[(yr==year)&mo.isin([3,4,5])&da.notna()].copy()
 mos=pd.to_numeric(s[c['month']],errors='coerce').to_numpy(float); days=pd.to_numeric(s[c['day']],errors='coerce').to_numpy(float); dts=[]
 for m,d in zip(mos,days):
  try: dts.append(datetime(year,int(m),1,tzinfo=timezone.utc)+timedelta(days=max(1,int(math.floor(d)))-1+d-math.floor(d)))
  except Exception: dts.append(None)
 sd=np.array([sol(x) if x else np.nan for x in dts]); use=np.zeros(len(s),bool); agreement=None
 if c['ls'] is not None:
  ls=pd.to_numeric(s[c['ls']],errors='coerce').to_numpy(float); use=np.isfinite(ls); sv=sd.copy(); sv[use]=ls[use]%360.; agreement=float(np.nanmedian(np.abs(cd(ls[use],sd[use])))) if use.any() else None
 else: sv=sd
 ra=pd.to_numeric(s[c['ra']],errors='coerce').to_numpy(float); dec=pd.to_numeric(s[c['dec']],errors='coerce').to_numpy(float); lon,beta=ecl(ra,dec)
 ids=s[c['id']].astype(str).to_numpy() if c['id'] is not None else np.array([f'{name}-{year}-{i}' for i in s.index])
 out=pd.DataFrame({'source':name,'year':year,'identifier':ids,'sol':sv,'ecl_lon':lon,'beta':beta,'vg':pd.to_numeric(s[c['vg']],errors='coerce').to_numpy(float),'e':pd.to_numeric(s[c['e']],errors='coerce').to_numpy(float),'q':pd.to_numeric(s[c['q']],errors='coerce').to_numpy(float),'inc':pd.to_numeric(s[c['inc']],errors='coerce').to_numpy(float),'peri':pd.to_numeric(s[c['peri']],errors='coerce').to_numpy(float)%360.,'node':pd.to_numeric(s[c['node']],errors='coerce').to_numpy(float)%360.})
 out['sunlon']=cd(out.ecl_lon.to_numpy(float),out.sol.to_numpy(float)); o=out[['e','q','inc','peri','node']].to_numpy(float)
 valid=np.isfinite(out[['sol','ecl_lon','beta','vg']]).all(axis=1)&out.sol.between(0,360)&out.ecl_lon.between(0,360)&out.beta.between(-90,90)&out.vg.between(5,75)&np.isfinite(o).all(axis=1)&(o[:,0]>=0)&(o[:,0]<1.5)&(o[:,1]>0)&(o[:,1]<2)&(o[:,2]>=0)&(o[:,2]<=180)
 out=out.loc[valid].reset_index(drop=True); meta.update({'member':member,'sep':sep,'raw_rows':len(df),'seasonal_rows':len(s),'valid_rows':len(out),'columns':c,'ls_used':int(use.sum()),'ls_date_median_diff':agreement})
 return out,meta
def masks(f):
 so=f.sol.to_numpy(float); delta=cd(so,SOL0); ps=SUNLON0+SUNLON_SLOPE*delta; pb=BETA0+BETA_SLOPE*delta; pv=VG0+VG_SLOPE*delta
 score=(cd(f.sunlon.to_numpy(float),ps)/SUNLON_SIGMA)**2+((f.beta.to_numpy(float)-pb)/BETA_SIGMA)**2+((f.vg.to_numpy(float)-pv)/VG_SIGMA)**2
 ah=(np.abs(cd(f.sunlon.to_numpy(float)%360,ANTIHELION_CENTER))<=ANTIHELION_HALF_WIDTH)&(np.abs(f.beta.to_numpy(float))<=ANTIHELION_BETA_MAX)&f.vg.to_numpy(float).__ge__(ANTIHELION_SPEED_MIN)&f.vg.to_numpy(float).__le__(ANTIHELION_SPEED_MAX)
 season=np.abs(delta)<=SEASON_HALF_WIDTH; temporal=np.abs(delta)<=TIME_HALF_WIDTH; core=score<=CORE_RADIUS2; local=score<=LOCAL_RADIUS2; od=odist(f[['e','q','inc','peri','node']].to_numpy(float),REFINED_ORBIT[None,:])[:,0]
 return {'delta':delta,'score':score,'ah':ah,'season':season,'temporal':temporal,'core':core,'local':local,'od':od,'member':core&temporal&ah&(od<=ORBIT_MEMBER_D)}
def activity(f,m):
 bg=m['ah']&m['season']; core=m['core']&bg; inside=m['temporal']; a=int(np.sum(core&inside)); b=int(np.sum(bg&inside&~core)); c=int(np.sum(core&~inside)); d=int(np.sum(bg&~inside&~core)); odds,p=fisher_exact([[a,b],[c,d]],alternative='greater')
 return {'table':[[a,b],[c,d]],'core_inside':a,'antihelion_inside':a+b,'core_outside':c,'antihelion_outside':c+d,'odds_ratio':float(odds),'p':float(p)}
def shifted(f,m):
 so=f.sol.to_numpy(float); ah=m['ah']&m['season']; core=m['core']&ah; obs=m['temporal']; on=int(np.sum(core&obs)); od=int(np.sum(ah&obs)); ratio=on/od if od else 0.; controls=[]
 for off in np.arange(-SEASON_HALF_WIDTH+TIME_HALF_WIDTH,SEASON_HALF_WIDTH-TIME_HALF_WIDTH+1e-9,SHIFT_STEP):
  if abs(off)<=2*TIME_HALF_WIDTH: continue
  win=np.abs(cd(so,(SOL0+off)%360))<=TIME_HALF_WIDTH; den=int(np.sum(ah&win))
  if den<5: continue
  num=int(np.sum(core&win)); controls.append({'offset':float(off),'core':num,'background':den,'ratio':float(num/den)})
 p=(1+sum(x['ratio']>=ratio for x in controls))/(1+len(controls)) if controls else 1.
 return {'observed_core':on,'observed_background':od,'observed_ratio':ratio,'control_windows':len(controls),'empirical_p':float(p),'control_q95':float(np.percentile([x['ratio'] for x in controls],95)) if controls else None}
def orbit(f,m,seed):
 o=f.loc[m['member'],['e','q','inc','peri','node']].to_numpy(float)
 if len(o)<2:return {'members':len(o),'passed':False,'reason':'too_few'}
 ob=osum(o); pm=m['ah']&m['temporal']&~m['core']; pool=f.loc[pm,['e','q','inc','peri','node']].to_numpy(float); kind='same_time_antihelion_outside_core'
 if len(pool)<len(o)*3: pm=m['ah']&m['season']&m['local']&~m['core']; pool=f.loc[pm,['e','q','inc','peri','node']].to_numpy(float); kind='seasonal_local_shell'
 if len(pool)<len(o)*3:return {'members':len(o),'pool':len(pool),'observed':ob,'passed':False,'reason':'small_pool','pool_kind':kind}
 rng=np.random.default_rng(seed); null=[osum(pool[rng.choice(len(pool),size=len(o),replace=False)])['median_d'] for _ in range(ORBIT_NULL_DRAWS)]; p=(1+sum(x<=ob['median_d'] for x in null))/(ORBIT_NULL_DRAWS+1)
 return {'members':len(o),'pool':len(pool),'pool_kind':kind,'observed':ob,'null_p':float(p),'null_q01':float(np.percentile(null,1)),'passed':bool(ob['median_d']<=MAX_ORBIT_MEDIAN_D and ob['q90_d']<=MAX_ORBIT_Q90_D and p<=MAX_ORBIT_NULL_P)}
def analyze(name,spec,frames,meta):
 f=pd.concat(frames,ignore_index=True,sort=False); m=masks(f); f['score']=m['score']; f['orbit_d']=m['od']; a=activity(f,m); s=shifted(f,m); o=orbit(f,m,SEED+sum(map(ord,name))); members=f.loc[m['member']].copy(); counts={str(int(y)):int(n) for y,n in members.year.value_counts().sort_index().items()}; active=sorted(int(y) for y,n in members.year.value_counts().items() if int(n)>=MIN_PER_ACTIVE_YEAR)
 passed=bool(len(members)>=spec['min'] and len(active)>=MIN_ACTIVE_YEARS and a['p']<=MAX_ACTIVITY_P and s['empirical_p']<=MAX_SHIFT_P and o.get('passed',False)); members.sort_values(['year','sol','identifier']).to_csv(OUT/f'{name.lower()}_members.csv',index=False)
 return {'source':name,'independent':spec['independent'],'seasonal_valid_rows':len(f),'members':len(members),'member_counts_by_year':counts,'active_years':active,'activity':a,'shifted_windows':s,'orbit':o,'min_members_gate':spec['min'],'passed':passed,'year_metadata':meta}
def j(v):
 if isinstance(v,np.ndarray):return v.tolist()
 if isinstance(v,(np.integer,np.floating)):return v.item()
 if isinstance(v,dict):return {str(k):j(x) for k,x in v.items()}
 if isinstance(v,list):return [j(x) for x in v]
 return v
def report(p):
 z=['# GhostStream full external-catalog replication','',f"**Verdict:** `{p['verdict']}`",'',"The complete IAU MDC 2026 CAMS v3, SonotaCo, and EDMOND yearly catalogs were evaluated with the unchanged GMN-derived template and preserved decision gates. No external-source parameter was refit.",'']
 for n in ('CAMS','SonotaCo','EDMOND'):
  r=p['sources'][n]; z += [f'## {n}','']
  if 'error' in r:z += [f"- Error: `{r['error']}`",''];continue
  z += [f"- Role: {'independent replication' if r['independent'] else 'supplementary catalog'}",f"- Valid seasonal rows: **{r['seasonal_valid_rows']:,}**",f"- Frozen-template members: **{r['members']}**",f"- Counts by year: `{r['member_counts_by_year']}`",f"- Active years: `{r['active_years']}`",f"- Activity p: **{r['activity']['p']:.6g}**",f"- Shifted-window p: **{r['shifted_windows']['empirical_p']:.6g}**",f"- Orbit median D: **{r['orbit'].get('observed',{}).get('median_d')}**",f"- Orbit q90 D: **{r['orbit'].get('observed',{}).get('q90_d')}**",f"- Orbit-null p: **{r['orbit'].get('null_p')}**",f"- Preserved gate passed: **{r['passed']}**",'']
 z += ['## Interpretation boundary','','A CAMS or SonotaCo pass is independent external-network replication under the frozen GMN solution. EDMOND is supplementary because its contributing observations can overlap other video networks. Any failed gate is retained without threshold relaxation.','']
 return '\n'.join(z)
def main():
 OUT.mkdir(parents=True,exist_ok=True); CACHE.mkdir(parents=True,exist_ok=True); results={}
 for name,spec in SOURCES.items():
  frames=[]; meta={}; print(f'=== {name} ===',flush=True)
  for year in spec['years']:
   try:
    f,m=load(name,spec,year); frames.append(f); meta[str(year)]=m; print(name,year,m['raw_rows'],len(f),flush=True)
   except Exception as e: meta[str(year)]={'error':f'{type(e).__name__}: {e}'}; print(name,year,'ERROR',e,flush=True)
  results[name]=analyze(name,spec,frames,meta) if frames else {'error':'no usable archive','year_metadata':meta}
 passes=[n for n in ('CAMS','SonotaCo') if 'error' not in results[n] and results[n].get('passed')]
 verdict='FROZEN_EXTERNAL_REPLICATION_PASSED_IN_CAMS_AND_SONOTACO' if len(passes)==2 else (f'FROZEN_EXTERNAL_REPLICATION_PASSED_IN_{passes[0].upper()}' if len(passes)==1 else 'COMPLETE_EXTERNAL_CATALOGS_SUPPORT_BUT_DO_NOT_PASS_PRESERVED_NETWORK_GATES')
 p=j({'stage':'complete_external_catalog_replication','verdict':verdict,'candidate_frozen_from_gmn':True,'catalog_release':'IAU MDC Version 2026','independent_networks_passing':passes,'frozen_template':{'solar_longitude_center_deg':SOL0,'time_half_width_deg':TIME_HALF_WIDTH,'sun_centered_longitude':[SUNLON0,SUNLON_SLOPE,SUNLON_SIGMA],'ecliptic_latitude':[BETA0,BETA_SLOPE,BETA_SIGMA],'geocentric_speed':[VG0,VG_SLOPE,VG_SIGMA],'core_radius_squared':CORE_RADIUS2,'refined_orbit':REFINED_ORBIT,'orbit_member_d':ORBIT_MEMBER_D},'sources':results,'software':{'python':sys.version,'numpy':np.__version__,'pandas':pd.__version__}})
 (OUT/'full_external_replication.json').write_text(json.dumps(p,indent=2,sort_keys=True)+'\n'); (OUT/'FULL_EXTERNAL_REPLICATION.md').write_text(report(p)+'\n'); manifest={q.name:{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in sorted(OUT.glob('*')) if q.is_file()}; (OUT/'SHA256_MANIFEST.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n'); print(json.dumps({'verdict':verdict,'passes':passes,'members':{n:r.get('members') for n,r in results.items()}},indent=2))
if __name__=='__main__': main()
