#!/usr/bin/env python3
"""Fast HEASARC TAP schema probe for 5XMM-DR15. No identities emitted."""
from pathlib import Path
import io,json,urllib.parse,urllib.request
from astropy.table import Table
OUT=Path('results/xmm_dr15_tap_semantics.json');OUT.parent.mkdir(parents=True,exist_ok=True)
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'
def q(adql):
    data=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':adql}).encode()
    req=urllib.request.Request(EP,data=data,headers={'User-Agent':'ISEF-XMM-TAP-semantics/1.2','Content-Type':'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req,timeout=45) as r:raw=r.read()
    text=raw.decode('utf-8','replace')
    if 'QUERY_STATUS' in text[:5000] and 'value="ERROR"' in text[:5000]:raise RuntimeError(text[:3000])
    t=Table.read(io.BytesIO(raw),format='votable');rows=[]
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
    for tab in ('xmmssc','xmmstack','xmmstackob'):
      try:
        out[f'{tab}_table']=q(f"SELECT TOP 1 table_name,description FROM TAP_SCHEMA.tables WHERE table_name='{tab}'")
        cols=q(f"SELECT column_name,datatype,unit,description FROM TAP_SCHEMA.columns WHERE table_name='{tab}'")
        wanted=('ra','dec','srcid','iauname','sum_flag','sc_sum_flag','extent','sc_extent','end_time','n_obs','n_contrib','ep_det_ml','sc_det_ml','pn_hr1','pn_hr2','pn_hr3','pn_hr4','approx_source_var','classx_outlier','stack_id','obs_id','obsid')
        out[f'{tab}_relevant_columns']=[c for c in cols if str(c.get('column_name','')).lower() in wanted]
        out[f'{tab}_column_count']=len(cols)
        out[f'{tab}_sample_columns']=cols[:12]
      except Exception as e:out[f'{tab}_error']=f'{type(e).__name__}: {e}'
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps(out,indent=2,sort_keys=True,default=str))
if __name__=='__main__':main()
