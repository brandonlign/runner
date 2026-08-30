#!/usr/bin/env python3
"""Metadata-only feasibility probe for IMAP + SOLAR-1 shock geometry.

Uses exact dataset IDs/endpoints recovered from current SPDF catalogue and the
published MIDL downloader. Requests /info only; no magnetic-field or position
science rows are read.
"""
import json, urllib.parse, urllib.request
from pathlib import Path
OUT=Path('results/imap_solar1_multil1_schema_probe_v2.json'); OUT.parent.mkdir(exist_ok=True)
CDA='https://cdaweb.gsfc.nasa.gov/hapi/info'
NOAA='https://www.ncei.noaa.gov/cloud-access/space-weather-portal/api/v1/hapi/info'
IMAP=['imap_mag_l2_norm-gse','imap_mag_l2_norm-gsm','imap_or_ssc','imap_helio1hr_position','imap_swapi_l3a_proton-sw','imap_swapi_l2_sci']
SOL=['mag-l3_solar1','sci_mag-l3_solar1','orb-pr_solar1','SWFO_DefEphem']
o={'status':'INFO_ONLY','science_values_accessed':False,'success':False}
def get(base, params):
 u=base+'?'+urllib.parse.urlencode(params); req=urllib.request.Request(u,headers={'User-Agent':'ISEF-IMAP-SOLAR1-Info/2.0'})
 with urllib.request.urlopen(req,timeout=120) as r: return json.load(r)
def compact(x):
 return {'startDate':x.get('startDate'),'stopDate':x.get('stopDate'),'cadence':x.get('cadence'),'sampleStartDate':x.get('sampleStartDate'),'sampleStopDate':x.get('sampleStopDate'),'parameters':[{'name':p.get('name'),'type':p.get('type'),'units':p.get('units'),'size':p.get('size'),'description':p.get('description'),'fill':p.get('fill')} for p in x.get('parameters',[])]}
try:
 r={'imap':{},'solar1':{}}
 for ds in IMAP:
  try: r['imap'][ds]=compact(get(CDA,{'id':ds}))
  except Exception as e: r['imap'][ds]={'error':type(e).__name__+': '+str(e)}
 for ds in SOL:
  # NOAA uses 'dataset' rather than HAPI-standard 'id'.
  try: r['solar1'][ds]=compact(get(NOAA,{'dataset':ds}))
  except Exception as e: r['solar1'][ds]={'error':type(e).__name__+': '+str(e)}
 o['datasets']=r; o['success']=True; o['decision']='EXACT_INFO_PROBE_COMPLETE'
except Exception as e:
 o['error']=type(e).__name__+': '+str(e); o['decision']='INFRASTRUCTURE_FAILURE_NO_SCIENCE_DECISION'
OUT.write_text(json.dumps(o,indent=2)+'\n'); print(json.dumps(o,indent=2))
