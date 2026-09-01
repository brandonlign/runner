#!/usr/bin/env python3
"""Aggregate-only probe for deterministic 5XMM population join query."""
from pathlib import Path
import io,json,urllib.parse,urllib.request
from astropy.table import Table
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'
O=Path('results/xmm_population_join_probe.json'); O.parent.mkdir(parents=True,exist_ok=True)
q="""SELECT TOP 100000 s.srcid,s.ra,s.dec,d.obsid
FROM xmmssc AS s JOIN xmmstack AS d ON s.srcid=d.srcid
WHERE s.sum_flag < 3 AND s.extent = 0 AND s.ep_det_ml >= 15
AND s.ra >= 0 AND s.ra < 5"""
try:
 u=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q})
 with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'ISEF-XMM-popjoin-probe/1.0'}),timeout=180) as r: raw=r.read()
 t=Table.read(io.BytesIO(raw),format='votable')
 src=[str(x).strip() for x in t['srcid']]
 obs=[str(x).strip() for x in t['obsid']]
 out={'success':True,'rows':len(t),'unique_srcids':len(set(src)),'nonblank_obsid_rows':sum(x not in ('','--','None') for x in obs),'hit_top_cap':len(t)>=100000,'columns':list(t.colnames),'privacy':'No identities or coordinates emitted.'}
except Exception as e: out={'success':False,'error':f'{type(e).__name__}: {e}'}
O.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))
