#!/usr/bin/env python3
"""Metadata-only probe that verifies XMMSSC SRCIDs retrieve observation rows in XMMSTACK."""
from pathlib import Path
import io,json,urllib.parse,urllib.request
from astropy.table import Table
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'
OUT=Path('results/xmm_detection_join_probe.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
def tap(q):
 u=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q})
 with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'ISEF-XMM-join-probe/1.0'}),timeout=90) as r: raw=r.read()
 return Table.read(io.BytesIO(raw),format='votable')
def norm(x): return x.decode().strip() if isinstance(x,bytes) else str(x).strip()
try:
 a=tap('SELECT TOP 1 srcid FROM xmmssc WHERE n_obs > 1')
 sid=norm(a['srcid'][0]).replace("'","''")
 b=tap("SELECT TOP 100 srcid,obsid FROM xmmstack WHERE srcid='"+sid+"'")
 obs=[norm(x) for x in b['obsid']] if 'obsid' in b.colnames else []
 out={'success':True,'source_query_rows':len(a),'joined_rows':len(b),'nonblank_obsid_rows':sum(bool(x) for x in obs),'has_srcid_col':'srcid' in b.colnames,'has_obsid_col':'obsid' in b.colnames,'privacy':'SRCID and ObsIDs intentionally not emitted.'}
except Exception as e: out={'success':False,'error':f'{type(e).__name__}: {e}'}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))
