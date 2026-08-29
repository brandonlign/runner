#!/usr/bin/env python3
"""Determine how 5XMM unique sources link to stacks and constituent ObsIDs.
Schema/sample diagnostics only; no astronomical source identities or coordinates emitted.
"""
from pathlib import Path
import io,json,urllib.parse,urllib.request
from astropy.table import Table
OUT=Path('results/xmm_dr15_stack_link_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'

def q(adql):
    b=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':adql}).encode()
    req=urllib.request.Request(EP,data=b,headers={'User-Agent':'ISEF-XMM-stack-link/1.0','Content-Type':'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req,timeout=60) as r:raw=r.read()
    txt=raw.decode('utf-8','replace')
    if 'QUERY_STATUS' in txt[:8000] and 'value="ERROR"' in txt[:8000]:raise RuntimeError(txt[:4000])
    return Table.read(io.BytesIO(raw),format='votable')
def rows(t):
    out=[]
    for r in t:
      d={}
      for n in t.colnames:
        x=r[n]
        if hasattr(x,'mask') and x.mask:d[n]=None
        elif isinstance(x,bytes):d[n]=x.decode('utf-8','replace')
        elif hasattr(x,'item'):
          try:d[n]=x.item()
          except:d[n]=str(x)
        else:d[n]=x
      out.append(d)
    return out
def main():
    out={'success':True,'endpoint':EP}
    try:
      for tab in ('xmmssc','xmmstack','xmmstackob'):
        cols=q(f"SELECT column_name,datatype,description FROM TAP_SCHEMA.columns WHERE table_name='{tab}'")
        rr=rows(cols)
        out[f'{tab}_link_columns']=[x for x in rr if any(k in str(x.get('column_name','')).lower() for k in ('stack','obs','srcid','pps_srcnum'))]
      # Only aggregate relationships: no values of source IDs are returned.
      tests={
        'xmmssc_total':'SELECT COUNT(*) AS n FROM xmmssc',
        'xmmstack_total':'SELECT COUNT(*) AS n FROM xmmstack',
        'xmmstackob_total':'SELECT COUNT(*) AS n FROM xmmstackob',
        'xmmssc_distinct_srcid':'SELECT COUNT(DISTINCT srcid) AS n FROM xmmssc',
        'xmmstack_distinct_srcid':'SELECT COUNT(DISTINCT srcid) AS n FROM xmmstack',
        'xmmstackob_distinct_stack':'SELECT COUNT(DISTINCT stack_id) AS n FROM xmmstackob'
      }
      for k,sql in tests.items():
        try:out[k]=rows(q(sql))
        except Exception as e:out[k]={'error':f'{type(e).__name__}: {e}'}
      # Check whether srcid has deterministic numeric prefixes matching stack_id without emitting IDs.
      # ADQL string functions vary, so query harmless datatype/min-max diagnostics on numeric link columns if present.
      try:out['stackob_stack_range']=rows(q('SELECT MIN(stack_id) AS mn,MAX(stack_id) AS mx FROM xmmstackob'))
      except Exception as e:out['stackob_stack_range']={'error':f'{type(e).__name__}: {e}'}
    except Exception as e:out={'success':False,'error':f'{type(e).__name__}: {e}'}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps(out,indent=2,sort_keys=True,default=str))
if __name__=='__main__':main()
