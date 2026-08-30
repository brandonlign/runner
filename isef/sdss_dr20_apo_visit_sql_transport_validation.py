#!/usr/bin/env python3
"""Validate SkyServer mwm_boss_allvisit against the frozen APO FITS calibration.
Development only: queries APO visits, never LCO source outcomes or identities.
"""
from pathlib import Path
from collections import defaultdict
import gzip,json,os,shutil,time,urllib.parse,urllib.request
import numpy as np
from astropy.io import fits
OUT=Path('results/sdss_dr20_apo_visit_sql_transport_validation.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
STAR='https://dr20.sdss.org/sas/dr20/spectro/astra/0.8.1/summary/mwmAllStar-0.8.1.fits.gz'
SQL='https://skyserver.sdss.org/dr20/SkyServerWS/SearchTools/SqlSearch'
EXPECTED={'summary_n':1729,'ge2_quality_visits':1592,'median_within20':1.0,'scatter_le30':0.989321608040201,'atleast2_within30':0.9956030150753769}

def dl(url,p):
 p=Path(p); part=Path(str(p)+'.part'); last=None
 for k in range(1,5):
  try:
   if part.exists():part.unlink()
   req=urllib.request.Request(url,headers={'User-Agent':'ISEF-DR20-APO-SQL-Transport/1.0'})
   with urllib.request.urlopen(req,timeout=600) as r,open(part,'wb') as f:
    exp=r.headers.get('Content-Length'); exp=int(exp) if exp and exp.isdigit() else None;n=0
    while True:
     b=r.read(8<<20)
     if not b:break
     f.write(b);n+=len(b)
    f.flush();os.fsync(f.fileno())
   if exp is not None and n!=exp:raise EOFError('incomplete body')
   if n<=0:raise EOFError('empty body')
   part.replace(p);return
  except Exception as e:
   last=e
   if k<4:time.sleep(2**k)
 raise last

def sql_rows(ids):
 by=defaultdict(list)
 for a in range(0,len(ids),200):
  bb=ids[a:a+200]
  q=("SELECT sdss_id,xcsao_v_rad,xcsao_e_v_rad,snr,zwarning_flags FROM mwm_boss_allvisit "
     "WHERE telescope='apo25m' AND sdss_id IN ("+','.join(str(int(x)) for x in bb)+")")
  url=SQL+'?'+urllib.parse.urlencode({'cmd':q,'format':'json'});req=urllib.request.Request(url,headers={'User-Agent':'ISEF-DR20-APO-SQL-Transport/1.0'})
  with urllib.request.urlopen(req,timeout=180) as r:obj=json.loads(r.read().decode('utf-8','replace'))
  rows=[]
  for t in obj:
   if isinstance(t,dict) and t.get('TableName')=='Table1':rows=t.get('Rows',[])
  for r in rows:
   try: sid=int(r['sdss_id']);rv=float(r['xcsao_v_rad']);e=float(r['xcsao_e_v_rad']);sn=float(r['snr']);z=int(r['zwarning_flags'])
   except:continue
   if np.isfinite(rv) and np.isfinite(e) and np.isfinite(sn) and e<30 and sn>10 and z==0:by[sid].append(rv)
 return by

def main():
 out={'success':False,'status':'APO_SQL_VISIT_TRANSPORT_VALIDATION','lco_source_outcomes_accessed':False,'identities_emitted':False,'expected':EXPECTED}
 try:
  sg=Path('/tmp/aposqls.gz');sf=Path('/tmp/aposqls.fits');dl(STAR,sg)
  with gzip.open(sg,'rb') as a,open(sf,'wb') as b:shutil.copyfileobj(a,b,length=8<<20)
  need=['sdss_id','telescope','v_rad','e_v_rad','std_v_rad','snr','n_good_rvs','zwarning_flags','nmf_flags']
  with fits.open(sf,memmap=True) as h:
   cc=[x.data for x in h[1:] if getattr(x,'data',None) is not None and hasattr(x.data,'names') and all(k in x.data.names for k in need)]
   if not cc:raise RuntimeError('summary schema absent')
   d=max(cc,key=len);tel=np.char.lower(np.char.strip(np.asarray(d['telescope']).astype(str)));v=np.asarray(d['v_rad'],float);ev=np.asarray(d['e_v_rad'],float);sv=np.asarray(d['std_v_rad'],float);sn=np.asarray(d['snr'],float);ng=np.asarray(d['n_good_rvs'],int);zw=np.asarray(d['zwarning_flags'],np.int64);nm=np.asarray(d['nmf_flags'],np.int64)
   m=(tel=='apo25m')&np.isfinite(v)&np.isfinite(ev)&np.isfinite(sv)&np.isfinite(sn)&(sn>10)&(ev<30)&(ng>=2)&(sv<=30)&(zw==0)&(nm==0)&(np.abs(v)>300)
   ids=np.asarray(d['sdss_id'][m],np.int64); vals=v[m]; smap={int(i):float(x) for i,x in zip(ids,vals)}
  by=sql_rows(list(smap));md=[];rs=[];a30=[];usable=0
  for i,x in smap.items():
   rr=np.asarray(by.get(i,[]),float)
   if len(rr)<2:continue
   usable+=1;med=float(np.median(rr));md.append(abs(med-x));rs.append(float(1.4826*np.median(np.abs(rr-med))));a30.append(int(np.sum(np.abs(rr-x)<=30)))
  md=np.asarray(md);rs=np.asarray(rs);a30=np.asarray(a30)
  obs={'summary_n':len(smap),'ge2_quality_visits':usable,'median_within20':float(np.mean(md<=20)) if usable else None,'scatter_le30':float(np.mean(rs<=30)) if usable else None,'atleast2_within30':float(np.mean(a30>=2)) if usable else None}
  out['observed']=obs
  out['exact_count_match']=(obs['summary_n']==EXPECTED['summary_n'] and obs['ge2_quality_visits']==EXPECTED['ge2_quality_visits'])
  out['fraction_max_abs_diff']=max(abs(obs[k]-EXPECTED[k]) for k in ['median_within20','scatter_le30','atleast2_within30']) if usable else None
  out['success']=True;out['decision']='SQL_VISIT_TRANSPORT_VALIDATED' if out['exact_count_match'] and out['fraction_max_abs_diff']<1e-12 else 'SQL_VISIT_TRANSPORT_MISMATCH'
 except Exception as e:
  out['error_type']=type(e).__name__;out['error']=str(e)[:500];out['decision']='INFRASTRUCTURE_FAILURE_NO_SCIENTIFIC_DECISION'
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True));print(OUT.read_text())
if __name__=='__main__':main()
