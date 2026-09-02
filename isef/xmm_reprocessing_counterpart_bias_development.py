#!/usr/bin/env python3
from pathlib import Path
from collections import defaultdict
import io,json,urllib.parse,urllib.request,hashlib
import numpy as np
from scipy.stats import fisher_exact
from astropy.table import Table,vstack
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'; CAP=100000
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_slim_v1.0.fits.gz'; U4OBS='http://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4xmmdr14_obslist.fits'
P4=Path('/tmp/4XMM_DR14cat_slim_v1.0.fits.gz'); P4OBS=Path('/tmp/4xmmdr14_obslist.fits'); OUT=Path('results/xmm_reprocessing_counterpart_bias_development.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='s.sum_flag < 3 AND s.extent = 0 AND s.ep_det_ml >= 15'
def norm(x):
 if isinstance(x,(bytes,np.bytes_)): x=x.decode('utf-8','replace')
 return str(x).strip()
def num(x):
 try:
  v=float(x); return v if np.isfinite(v) else np.nan
 except: return np.nan
def tap(q,timeout=300):
 url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q}); req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-counterpart-bias/1.0'})
 with urllib.request.urlopen(req,timeout=timeout) as r: raw=r.read()
 return Table.read(io.BytesIO(raw),format='votable')
def dl(url,p):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-counterpart-bias/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r,p.open('wb') as f:
  while True:
   b=r.read(8*1024*1024)
   if not b: break
   f.write(b)
def refs():
 if not P4.exists(): dl(U4,P4)
 if not P4OBS.exists(): dl(U4OBS,P4OBS)
 with fits.open(P4,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}; ra=np.asarray(d[nm['SC_RA']],float).copy(); de=np.asarray(d[nm['SC_DEC']],float).copy()
 with fits.open(P4OBS,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}; old={norm(x) for x in d[nm['OBS_ID']] if norm(x)}
 ok=np.isfinite(ra)&np.isfinite(de); return SkyCoord(ra[ok]*u.deg,de[ok]*u.deg),old
def qbin(lo,hi,depth=0):
 q=f'''SELECT TOP {CAP} s.srcid AS sid,s.ra AS sra,s.dec AS sdec,s.gaiadr3_source_id AS gid,s.gaia_match_prob AS gp,s.wise_name AS wname,s.wise_match_prob AS wp,s.classopt_class AS oclass,d.obsid AS dobsid,d.pps_srcnum AS pps
FROM xmmssc AS s JOIN xmmstack AS d ON s.srcid=d.srcid
WHERE {BASE} AND s.ra >= {lo:.8f} AND s.ra < {hi:.8f} AND d.pps_srcnum IS NOT NULL'''
 t=tap(q)
 if len(t)>=CAP:
  if depth>=8: raise RuntimeError(f'cap persists {lo}-{hi}')
  mid=(lo+hi)/2; return qbin(lo,mid,depth+1)+qbin(mid,hi,depth+1)
 return [t]
def holm(ps):
 items=sorted(ps.items(),key=lambda z:z[1]); out={}; prev=0.0; m=len(items)
 for i,(k,p) in enumerate(items):
  a=max(prev,min(1.0,(m-i)*p)); out[k]=a; prev=a
 return out
def validstr(x):
 s=norm(x); return bool(s and s not in ('--','None','nan','null'))
def main():
 try:
  c4,old=refs(); cases={}; ctrls={}; used=set(); excluded=0
  for lo in range(0,180,5):
   tabs=qbin(float(lo),float(lo+5)); t=vstack(tabs,metadata_conflicts='silent') if len(tabs)>1 else tabs[0]
   props={}; obs=defaultdict(set)
   for row in t:
    sid=norm(row['sid'])
    if sid not in props:
     props[sid]={'ra':num(row['sra']),'dec':num(row['sdec']),'gaia':validstr(row['gid']) and num(row['gp'])>=0.8,'wise':validstr(row['wname']) and num(row['wp'])>=0.8,'optclass':validstr(row['oclass'])}
    o=norm(row['dobsid']);
    if o and o not in ('--','None','nan'): obs[sid].add(o)
   ids=list(props); c=SkyCoord([props[s]['ra'] for s in ids]*u.deg,[props[s]['dec'] for s in ids]*u.deg); _,sep,_=c.match_to_catalog_sky(c4)
   caseids=[ids[i] for i in range(len(ids)) if sep.arcsec[i]>20 and any(o in old for o in obs[ids[i]])]
   ctrlids=[ids[i] for i in range(len(ids)) if sep.arcsec[i]<=20 and any(o in old for o in obs[ids[i]])]
   om=defaultdict(list)
   for s in ctrlids:
    for o in obs[s]&old: om[o].append(s)
   for s in sorted(caseids,key=lambda x:hashlib.sha256(x.encode()).hexdigest()):
    cand=set()
    for o in obs[s]&old: cand.update(om.get(o,[]))
    avail=[x for x in cand if x not in used]; avail.sort(key=lambda x:hashlib.sha256((s+'|'+x).encode()).hexdigest()); chosen=avail[:3]
    if not chosen: excluded+=1; continue
    cases[s]=props[s]
    for x in chosen: ctrls[x]=props[x]; used.add(x)
  outcomes={'gaia':lambda p:p['gaia'],'wise':lambda p:p['wise'],'any':lambda p:p['gaia'] or p['wise'],'optclass':lambda p:p['optclass']}; res={}; raw={}
  for name,fn in outcomes.items():
   ca=sum(bool(fn(p)) for p in cases.values()); cb=len(cases)-ca; xa=sum(bool(fn(p)) for p in ctrls.values()); xb=len(ctrls)-xa
   odds,p=fisher_exact([[ca,cb],[xa,xb]],alternative='two-sided'); raw[name]=float(p)
   res[name]={'case_yes':ca,'case_no':cb,'control_yes':xa,'control_no':xb,'case_fraction':ca/len(cases) if cases else None,'control_fraction':xa/len(ctrls) if ctrls else None,'odds_ratio':float(odds),'raw_p':float(p)}
  adj=holm(raw)
  supported={k:(adj[k]<=0.01 and res[k]['case_fraction']<res[k]['control_fraction']) for k in outcomes}
  out={'success':True,'hemisphere':'development','matched_cases':len(cases),'unique_controls':len(ctrls),'excluded_cases':excluded,'probability_threshold':0.8,'outcomes':res,'holm_adjusted_p':adj,'development_supported':supported,'privacy':'Aggregate counts only; no identities or coordinates emitted.'}
 except Exception as e: out={'success':False,'error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True),flush=True)
if __name__=='__main__': main()
