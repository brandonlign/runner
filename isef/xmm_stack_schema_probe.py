#!/usr/bin/env python3
from pathlib import Path
import io,json,urllib.parse,urllib.request
from astropy.table import Table
import numpy as np
OUT=Path('results/xmm_stack_schema_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
EP5='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'
EP4='https://sky.esa.int/esasky-tap/tap/sync'
TAB5='xmmstack';TAB4='catalogues.mv_xsa_epic_stack_cat_fdw'
def tap(ep,q):
 d=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','QUERY':q}).encode();req=urllib.request.Request(ep,data=d,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-XMM-schema/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r:raw=r.read()
 t=Table.read(io.BytesIO(raw),format='votable');out=[]
 for rr in t:
  z={}
  for n in t.colnames:
   x=rr[n]
   if np.ma.is_masked(x): z[n]=None
   elif isinstance(x,bytes): z[n]=x.decode().strip()
   elif hasattr(x,'item'):
    try:z[n]=x.item()
    except:z[n]=str(x)
   else:z[n]=x
  out.append(z)
 return out

def cols(ep,tab):
 q=f"SELECT column_name,datatype,description FROM TAP_SCHEMA.columns WHERE table_name='{tab}' ORDER BY column_name"
 rs=tap(ep,q)
 keys=('stack','src','obs','detid','id','name','ra','dec','n_obs')
 return [r for r in rs if any(k in (str(r.get('column_name') or '').lower()) for k in keys)]
def sample(ep,tab,n=12):
 cs=cols(ep,tab);names=[r['column_name'] for r in cs]
 preferred=[x for x in names if any(k in x.lower() for k in ('stack','srcid','obs_id','observation','n_obs','detid'))]
 preferred=preferred[:20]
 if not preferred:return []
 return tap(ep,f"SELECT TOP {n} {','.join(preferred)} FROM {tab} WHERE n_obs IS NOT NULL ORDER BY srcid")
def main():
 out={'success':True,'dr15_columns':cols(EP5,TAB5),'dr14s_columns':cols(EP4,TAB4)}
 try:out['dr15_sample']=sample(EP5,TAB5)
 except Exception as e:out['dr15_sample_error']=f'{type(e).__name__}: {e}'
 try:out['dr14s_sample']=sample(EP4,TAB4)
 except Exception as e:out['dr14s_sample_error']=f'{type(e).__name__}: {e}'
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
