#!/usr/bin/env python3
"""Schema/catalog-only probe for prospective IMAP + SOLAR-1 multi-L1 shock geometry.

Queries HAPI catalog/info metadata only. No science data values are requested.
"""
import json, urllib.request, urllib.parse
from pathlib import Path
OUT=Path('results/imap_solar1_multil1_schema_probe.json'); OUT.parent.mkdir(exist_ok=True)
o={'status':'SCHEMA_ONLY','science_values_accessed':False,'success':False}
SERVERS={'cdaweb':'https://cdaweb.gsfc.nasa.gov/hapi','ncei':'https://www.ncei.noaa.gov/access/hapi'}
def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-MultiL1-Schema/1.0'})
 with urllib.request.urlopen(req,timeout=120) as r: return json.load(r)
try:
 out={}
 for name,base in SERVERS.items():
  try:
   cat=get(base+'/catalog')
   ids=[]
   for x in cat.get('catalog',[]):
    sid=str(x.get('id','')); title=str(x.get('title',''))
    hay=(sid+' '+title).lower()
    if any(k in hay for k in ['imap','solar-1','solar1','swfo','sol-1']): ids.append({'id':sid,'title':title})
   infos=[]
   for x in ids[:80]:
    try:
     inf=get(base+'/info?'+urllib.parse.urlencode({'id':x['id']}))
     pars=[{'name':p.get('name'),'type':p.get('type'),'units':p.get('units'),'size':p.get('size'),'description':p.get('description')} for p in inf.get('parameters',[])]
     infos.append({'id':x['id'],'title':x['title'],'startDate':inf.get('startDate'),'stopDate':inf.get('stopDate'),'cadence':inf.get('cadence'),'parameters':pars})
    except Exception as e: infos.append({'id':x['id'],'info_error':type(e).__name__+': '+str(e)})
   out[name]={'matching_catalog_entries':ids,'info':infos}
  except Exception as e: out[name]={'server_error':type(e).__name__+': '+str(e)}
 o['servers']=out; o['success']=True; o['decision']='SCHEMA_PROBE_COMPLETE'
except Exception as e:
 o['error']=type(e).__name__+': '+str(e); o['decision']='INFRASTRUCTURE_FAILURE_NO_SCIENCE_DECISION'
OUT.write_text(json.dumps(o,indent=2)+'\n'); print(json.dumps(o,indent=2))
