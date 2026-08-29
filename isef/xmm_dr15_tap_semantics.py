#!/usr/bin/env python3
"""Fast HEASARC TAP semantics/count probe for 5XMM-DR15.
No source identities are emitted."""
from pathlib import Path
import io,json,urllib.parse,urllib.request
from astropy.table import Table
OUT=Path('results/xmm_dr15_tap_semantics.json');OUT.parent.mkdir(parents=True,exist_ok=True)
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'
def q(adql):
    data=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':adql}).encode()
    req=urllib.request.Request(EP,data=data,headers={'User-Agent':'ISEF-XMM-TAP-semantics/1.1','Content-Type':'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req,timeout=120) as r:raw=r.read()
    text=raw.decode('utf-8','replace')
    if 'QUERY_STATUS' in text[:5000] and 'value="ERROR"' in text[:5000]: raise RuntimeError(text[:3000])
    t=Table.read(io.BytesIO(raw),format='votable')
    rows=[]
    for r in t:
      z={}
      for n in t.colnames:
        x=r[n]
        if hasattr(x,'mask') and x.mask:z[n]=None
        elif isinstance(x,bytes):z[n]=x.decode('utf-8','replace')
        elif hasattr(x,'item'):
          try:z[n]=x.item()
          except:z[n]=str(x)
        else:z[n]=x
      rows.append(z)
    return rows
def main():
    out={'success':True,'endpoint':EP}
    try:
      tabs=q("SELECT table_name,description FROM TAP_SCHEMA.tables WHERE UPPER(table_name) LIKE '%XMM%' ORDER BY table_name")
      out['xmm_tables']=tabs
      for tab in ('xmmssc','xmmstack','xmmstackob'):
        try:
          cols=q(f"SELECT column_name,datatype,unit,description FROM TAP_SCHEMA.columns WHERE table_name='{tab}'")
          out[f'{tab}_columns']=cols
          out[f'{tab}_count']=q(f'SELECT COUNT(*) AS n FROM {tab}')[0]
        except Exception as e: out[f'{tab}_error']=f'{type(e).__name__}: {e}'
    except Exception as e:out={'success':False,'error':f'{type(e).__name__}: {e}','endpoint':EP}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps(out,indent=2,sort_keys=True,default=str))
if __name__=='__main__':main()
