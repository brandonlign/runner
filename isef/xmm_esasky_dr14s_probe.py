#!/usr/bin/env python3
"""Probe ESASky TAP for the preserved 4XMM-DR14s source catalogue.
Infrastructure only: table names/schema/counts; no candidate identity lookup."""
from pathlib import Path
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.table import Table
EP='https://sky.esa.int/esasky-tap/tap/sync'
OUT=Path('results/xmm_esasky_dr14s_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)

def q(adql):
 data=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','QUERY':adql}).encode()
 req=urllib.request.Request(EP,data=data,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-ESASky-DR14s-probe/1.0'})
 with urllib.request.urlopen(req,timeout=120) as r:raw=r.read()
 txt=raw.decode('utf-8','replace')
 if 'QUERY_STATUS' in txt[:10000] and ('value="ERROR"' in txt[:10000] or '>ERROR<' in txt[:10000]):raise RuntimeError(txt[:10000])
 t=Table.read(io.BytesIO(raw),format='votable');out=[]
 for rr in t:
  z={}
  for n in t.colnames:
   x=rr[n]
   if np.ma.is_masked(x):z[n]=None
   elif isinstance(x,bytes):z[n]=x.decode('utf-8','replace')
   elif hasattr(x,'item'):
    try:z[n]=x.item()
    except:z[n]=str(x)
   else:z[n]=x
  out.append(z)
 return out

def main():
 out={'success':True,'endpoint':EP}
 try:
  tabs=q('SELECT table_name,description FROM TAP_SCHEMA.tables')
  hits=[r for r in tabs if any(s in (str(r.get('table_name',''))+' '+str(r.get('description',''))).lower() for s in ('4xmm','dr14s','xmmstack','stacked source'))]
  out['candidate_tables']=hits
  for j,r in enumerate(hits[:20]):
   tab=str(r['table_name']);key='t'+str(j)
   try:
    cols=q("SELECT column_name,datatype,unit,description FROM TAP_SCHEMA.columns WHERE table_name='"+tab.replace("'","''")+"'")
    out[key]={'table':tab,'column_count':len(cols),'relevant_columns':[x for x in cols if any(s in str(x.get('column_name','')).lower() for s in ('src','stack','ra','dec','flag','extent','det_ml','flux','hard','obs'))]}
    out[key]['count']=q(f'SELECT COUNT(*) AS n FROM {tab}')
   except Exception as e:out[key]={'table':tab,'error':f'{type(e).__name__}: {e}'}
 except Exception as e:out={'success':False,'endpoint':EP,'error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps(out,indent=2,sort_keys=True,default=str))
if __name__=='__main__':main()
