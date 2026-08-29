#!/usr/bin/env python3
from pathlib import Path
import io,json,urllib.request,urllib.parse
from astropy.io import fits
from astropy.table import Table
import numpy as np
OUT=Path('results/xmm_srcid_structure_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
U4='https://xmmssc.aip.de/files/dr14s/xmmstack_v3.2_4xmmdr14s_obslist.fits.gz'
U5='https://xmmssc.aip.de/files/dr15/5xmmdr15_stacklist.fits.gz'
EP4='https://sky.esa.int/esasky-tap/tap/sync';EP5='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync';T4='catalogues.mv_xsa_epic_stack_cat_fdw';T5='xmmstack'
def sval(x):
 if isinstance(x,(bytes,np.bytes_)):return x.decode('utf-8','replace').strip()
 if np.ma.is_masked(x):return None
 if hasattr(x,'item'):
  try:return x.item()
  except:return str(x)
 return x
def dl_rows(url,path,n=20):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-srcid-structure/1.0'})
 with urllib.request.urlopen(req,timeout=120) as r,path.open('wb') as f:
  while True:
   b=r.read(1<<20)
   if not b:break
   f.write(b)
 with fits.open(path,memmap=False) as h:
  tabs=[z for z in h if getattr(z,'data',None) is not None and hasattr(z.data,'names') and z.data.names];d=max(tabs,key=lambda z:len(z.data)).data
  names=list(d.names)
  keep=[x for x in names if any(k in x.upper() for k in ('STACK','OBS','RA','DEC','NOBS','N_OBS'))]
  return {'names':names,'rows':[{k:sval(d[k][i]) for k in keep} for i in range(min(n,len(d)))]}
def tap(ep,q):
 d=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','QUERY':q}).encode();req=urllib.request.Request(ep,data=d,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-srcid-structure/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r:raw=r.read()
 t=Table.read(io.BytesIO(raw),format='votable');return [{n:sval(rr[n]) for n in t.colnames} for rr in t]
def summaries(ep,tab):
 return tap(ep,f'SELECT TOP 80 srcid,n_obs FROM {tab} WHERE n_obs IS NOT NULL ORDER BY srcid')
def analyze(rs):
 ids=[str(r['srcid']) for r in rs]
 return {'lengths':sorted(set(map(len,ids))), 'first80':ids, 'prefix_groups':{str(L):len(set(s[:L] for s in ids)) for L in range(4,16)}}
def main():
 out={'success':True,'dr14_stacklist':dl_rows(U4,Path('/tmp/s4.gz')),'dr15_stacklist':dl_rows(U5,Path('/tmp/s5.gz'))}
 r4=summaries(EP4,T4);r5=summaries(EP5,T5);out['dr14_srcid']=analyze(r4);out['dr15_srcid']=analyze(r5)
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
