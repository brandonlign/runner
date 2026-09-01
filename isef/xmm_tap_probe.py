#!/usr/bin/env python3
from pathlib import Path
import json, urllib.parse, urllib.request
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'
OUT=Path('results/xmm_tap_probe.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
qs={
 'minimal':'SELECT TOP 1 ra FROM xmmssc',
 'needed_cols':'SELECT TOP 1 ra,dec,obs_id,end_time,sum_flag,extent,ep_det_ml FROM xmmssc',
 'countlike':'SELECT TOP 1 * FROM xmmssc',
}
res={}
for name,q in qs.items():
 try:
  url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q})
  req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-TAP-probe/1.0'})
  with urllib.request.urlopen(req,timeout=90) as r:
   raw=r.read(8192); ct=r.headers.get('Content-Type'); code=r.status
  text=raw.decode('utf-8','replace')
  res[name]={'http_status':code,'content_type':ct,'n_read':len(raw),'has_table':'<TABLE' in text.upper(),'has_error':'QUERY_STATUS" value="ERROR' in text.upper() or '<HTML' in text.upper(),'preview':text[:2000]}
 except Exception as e:
  res[name]={'exception':f'{type(e).__name__}: {e}'}
OUT.write_text(json.dumps(res,indent=2,sort_keys=True)+'\n')
print(json.dumps(res,indent=2,sort_keys=True))
