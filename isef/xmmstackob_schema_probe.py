#!/usr/bin/env python3
from pathlib import Path
import io,json,urllib.parse,urllib.request
from astropy.table import Table
OUT=Path('results/xmmstackob_schema_probe.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'
def tap(q):
    url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q})
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ISEF-XMMSTACKOB-probe/1.0'}),timeout=180) as r:
        return Table.read(io.BytesIO(r.read()),format='votable')
try:
    t=tap('SELECT TOP 1 * FROM xmmstackob')
    c=tap("SELECT column_name,datatype,description FROM TAP_SCHEMA.columns WHERE table_name='xmmstackob'")
    n=tap('SELECT COUNT(*) AS n FROM xmmstackob')
    out={'success':True,'row_count':int(n[0][0]),'sample_columns':list(t.colnames),'columns':[{'name':str(r['column_name']),'datatype':str(r['datatype']),'description':str(r['description'])} for r in c]}
except Exception as e:
    out={'success':False,'error':f'{type(e).__name__}: {e}'}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))
