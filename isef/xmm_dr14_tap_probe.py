#!/usr/bin/env python3
"""Probe Strasbourg 4XMM-DR14 TAP and recover aggregate DR14 ObsID availability.
No source identities are emitted."""
from pathlib import Path
import io,json,urllib.parse,urllib.request
from astropy.table import Table
OUT=Path('results/xmm_dr14_tap_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
ENDPOINTS=['https://xcatdb.unistra.fr/xtapdb/sync','https://xcatdb.unistra.fr/xtapdb/tap/sync','https://xcatdb.unistra.fr/4xmmdr14/tap/sync']

def query(ep,sql):
    b=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':sql}).encode()
    req=urllib.request.Request(ep,data=b,headers={'User-Agent':'ISEF-4XMM-DR14-TAP/1.0','Content-Type':'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req,timeout=60) as r:raw=r.read()
    txt=raw.decode('utf-8','replace')
    if 'QUERY_STATUS' in txt[:8000] and 'ERROR' in txt[:8000]:raise RuntimeError(txt[:4000])
    return Table.read(io.BytesIO(raw),format='votable')
def serial(t,limit=100):
    z=[]
    for r in t[:limit]:
      d={}
      for n in t.colnames:
        x=r[n]
        if hasattr(x,'mask') and x.mask:d[n]=None
        elif isinstance(x,bytes):d[n]=x.decode('utf-8','replace')
        elif hasattr(x,'item'):
          try:d[n]=x.item()
          except:d[n]=str(x)
        else:d[n]=str(x) if not isinstance(x,(int,float,str,bool,type(None))) else x
      z.append(d)
    return z
def main():
    out={'success':False,'attempts':[]}
    for ep in ENDPOINTS:
      try:
        tabs=query(ep,"SELECT table_name,description FROM TAP_SCHEMA.tables")
        names=[str(x) for x in tabs['table_name']]
        likely=[x for x in names if '4xmm' in x.lower() or 'xmm' in x.lower()]
        rec={'endpoint':ep,'tables_total':len(names),'likely_tables':likely[:100]}
        # Probe likely catalogue tables for OBS_ID/OBSID columns and aggregate distinct counts.
        probes=[]
        for tab in likely[:20]:
          try:
            cols=query(ep,f"SELECT column_name,datatype,description FROM TAP_SCHEMA.columns WHERE table_name='{tab}'")
            cc=[str(x) for x in cols['column_name']]
            obs=[x for x in cc if x.lower() in ('obs_id','obsid')]
            probes.append({'table':tab,'obs_columns':obs,'column_count':len(cc)})
            if obs:
              oc=obs[0]
              try:
                n=query(ep,f'SELECT COUNT(DISTINCT {oc}) AS n FROM {tab}')
                probes[-1]['distinct_obsids']=int(n['n'][0])
              except Exception as e:probes[-1]['count_error']=f'{type(e).__name__}: {e}'
          except Exception as e:probes.append({'table':tab,'error':f'{type(e).__name__}: {e}'})
        rec['probes']=probes;out={'success':True,**rec};break
      except Exception as e:out['attempts'].append({'endpoint':ep,'error':f'{type(e).__name__}: {e}'})
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps(out,indent=2,sort_keys=True,default=str))
if __name__=='__main__':main()
