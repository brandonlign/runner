#!/usr/bin/env python3
"""Probe the public Strasbourg 4XMM-DR14 TAP service.

Infrastructure/semantics only: no 5XMM candidate identities are queried.
"""
from pathlib import Path
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.table import Table
EP='https://xcatdb.unistra.fr/xtapdb/sync'
OUT=Path('results/xmm_dr14_xcatdb_schema.json');OUT.parent.mkdir(parents=True,exist_ok=True)

def query(adql):
    data=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'application/x-votable+xml','QUERY':adql}).encode()
    req=urllib.request.Request(EP,data=data,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-XMM-DR14-schema/1.0'})
    with urllib.request.urlopen(req,timeout=120) as r: raw=r.read()
    text=raw.decode('utf-8','replace')
    if 'QUERY_STATUS' in text[:8000] and 'ERROR' in text[:8000]: raise RuntimeError(text[:8000])
    t=Table.read(io.BytesIO(raw),format='votable')
    out=[]
    for row in t:
        z={}
        for n in t.colnames:
            x=row[n]
            if np.ma.is_masked(x): z[n]=None
            elif isinstance(x,bytes): z[n]=x.decode('utf-8','replace')
            elif hasattr(x,'item'):
                try:z[n]=x.item()
                except:z[n]=str(x)
            else:z[n]=x
        out.append(z)
    return out

def main():
    out={'success':True,'endpoint':EP}
    tests={
      'tables':"SELECT table_name,description FROM TAP_SCHEMA.tables",
      'mergedentry_columns':"SELECT column_name,datatype,unit,description FROM TAP_SCHEMA.columns WHERE table_name='public.mergedentry' OR table_name='mergedentry' OR table_name='\"public\".mergedentry'",
      'top1':"SELECT TOP 1 * FROM \"public\".mergedentry",
    }
    for k,q in tests.items():
        try:out[k]=query(q)
        except Exception as e:out[k+'_error']=f'{type(e).__name__}: {e}'
    # Keep report compact if service exposes many tables/columns.
    if len(out.get('tables',[]))>200:out['tables']=out['tables'][:200]
    if len(out.get('mergedentry_columns',[]))>500:out['mergedentry_columns']=out['mergedentry_columns'][:500]
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps(out,indent=2,sort_keys=True,default=str))
if __name__=='__main__':main()
