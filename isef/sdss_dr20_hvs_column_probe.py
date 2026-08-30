#!/usr/bin/env python3
from pathlib import Path
import urllib.request,re,html,json
OUT=Path('results/sdss_dr20_hvs_column_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
URL='https://data.sdss.org/datamodel/files/MWM_ORBITS/GravPot16.html'
try:
 s=urllib.request.urlopen(urllib.request.Request(URL,headers={'User-Agent':'ISEF-SDSS-HVS/1.2'}),timeout=60).read().decode('utf-8','replace')
 # Extract table rows from datamodel, retaining schema only.
 rows=[]
 for tr in re.findall(r'<tr[^>]*>(.*?)</tr>',s,re.I|re.S):
  cells=[re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',x))).strip() for x in re.findall(r'<td[^>]*>(.*?)</td>',tr,re.I|re.S)]
  if len(cells)>=3: rows.append(cells)
 out={'success':True,'status':'SCHEMA_ONLY','rows':rows,'note':'Documentation only.'}
except Exception as e:out={'success':False,'status':'SCHEMA_ONLY','error':f'{type(e).__name__}: {e}'}
OUT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
