#!/usr/bin/env python3
"""Exploratory feasibility probe for the newly public AMS-02 all-particle one-second rate catalog.
No discovery search. Measures actual coverage/schema and quantifies first-order orbital-position confounding."""
from pathlib import Path
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.table import Table
OUT=Path('results/ams02_rates_feasibility_probe.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'
def tap(q,timeout=300):
 u=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q}); req=urllib.request.Request(u,headers={'User-Agent':'ISEF-AMS02-rates-feasibility/1.0'})
 with urllib.request.urlopen(req,timeout=timeout) as r:return Table.read(io.BytesIO(r.read()),format='votable')
try:
 cols=tap("SELECT column_name,datatype,description FROM TAP_SCHEMA.columns WHERE table_name='ams02rates'")
 count=tap('SELECT COUNT(*) AS n FROM ams02rates')
 sample=tap('SELECT TOP 200000 * FROM ams02rates ORDER BY time')
 out={'success':True,'row_count':int(count[0][0]),'columns':[{'name':str(r['column_name']),'datatype':str(r['datatype']),'description':str(r['description'])} for r in cols], 'sample_n':len(sample),'sample_columns':list(sample.colnames)}
 # Automatically identify plausible rate/livetime/position/time columns by names, then quantify simple correlations.
 names={c.lower():c for c in sample.colnames}
 def choose(keys):
  for k,c in names.items():
   if any(x in k for x in keys): return c
 rate=choose(['rate']); live=choose(['livetime','live_time']); lat=choose(['latitude','lat']); lon=choose(['longitude','lon']); tim=choose(['time','mjd'])
 out['identified']={'rate':rate,'livetime':live,'latitude':lat,'longitude':lon,'time':tim}
 if rate:
  y=np.asarray(sample[rate],float); good=np.isfinite(y); out['rate_median']=float(np.nanmedian(y));out['rate_p01_p99']=[float(np.nanpercentile(y,1)),float(np.nanpercentile(y,99))]
  for label,col in [('latitude',lat),('longitude',lon),('livetime',live)]:
   if col:
    x=np.asarray(sample[col],float); ok=good&np.isfinite(x)
    if np.sum(ok)>10:out[label+'_pearson_r']=float(np.corrcoef(x[ok],y[ok])[0,1])
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
except Exception as e:
 out={'success':False,'error':f'{type(e).__name__}: {e}'};OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
