#!/usr/bin/env python3
"""Fast HEASARC TAP semantics/count probe for 5XMM-DR15.
No source identities are emitted."""
from pathlib import Path
import csv,io,json,urllib.parse,urllib.request
OUT=Path('results/xmm_dr15_tap_semantics.json');OUT.parent.mkdir(parents=True,exist_ok=True)
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'
def q(adql):
    data=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'csv','QUERY':adql}).encode()
    req=urllib.request.Request(EP,data=data,headers={'User-Agent':'ISEF-XMM-TAP-semantics/1.0','Content-Type':'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req,timeout=120) as r:s=r.read().decode('utf-8','replace')
    if '<VOTABLE' in s[:1000] or 'QUERY_STATUS' in s[:3000]: raise RuntimeError(s[:3000])
    return list(csv.DictReader(io.StringIO(s)))
def main():
    out={'success':True,'endpoint':EP}
    try:
      tabs=q("SELECT table_name,description FROM TAP_SCHEMA.tables WHERE UPPER(table_name) LIKE '%XMM%' ORDER BY table_name")
      out['xmm_tables']=tabs
      for tab in ('xmmssc','xmmstack','xmmstackob'):
        try:
          cols=q(f"SELECT column_name,datatype,unit,description FROM TAP_SCHEMA.columns WHERE table_name='{tab}' ORDER BY column_index")
          out[f'{tab}_columns']=cols
          out[f'{tab}_count']=q(f'SELECT COUNT(*) AS n FROM {tab}')[0]
        except Exception as e: out[f'{tab}_error']=f'{type(e).__name__}: {e}'
    except Exception as e:out={'success':False,'error':f'{type(e).__name__}: {e}','endpoint':EP}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
