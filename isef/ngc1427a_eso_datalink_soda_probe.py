#!/usr/bin/env python3
"""Metadata-only ESO DataLink/SODA capability probe for NGC1427A MUSE cube."""
import json,urllib.parse,urllib.request
from pathlib import Path
DP='ADP.2026-06-24T16:04:14.194'
OUT=Path('results/ngc1427a_eso_datalink_soda_probe.json');OUT.parent.mkdir(exist_ok=True)
urls=[
 'https://archive.eso.org/datalink/links?'+urllib.parse.urlencode({'ID':'ivo://eso.org/ID?'+DP,'RESPONSEFORMAT':'json'}),
 'https://archive.eso.org/datalink/links?'+urllib.parse.urlencode({'ID':'ivo://eso.org/ID?'+DP})]
o={'status':'METADATA_ONLY','science_data_accessed':False,'dp_id':DP,'success':False,'attempts':[]}
for u in urls:
 try:
  req=urllib.request.Request(u,headers={'User-Agent':'ISEF-NGC1427A-SODA-probe/1.0','Accept':'application/json,application/x-votable+xml,text/xml'})
  with urllib.request.urlopen(req,timeout=120) as r:
   raw=r.read(2_000_000); ct=r.headers.get('Content-Type','')
  text=raw.decode('utf-8','replace')
  rec={'url':u,'content_type':ct,'bytes':len(raw),'preview':text[:1000]}
  # Retain all lines/JSON snippets containing SODA/service/semantics/bounds.
  rec['soda_related_lines']=[ln[:1000] for ln in text.splitlines() if any(k in ln.lower() for k in ['soda','service','access_url','semantics','band','circle','polygon','pos','id='])][:100]
  o['attempts'].append(rec)
  if 'soda' in text.lower() or 'service' in text.lower(): o['success']=True
 except Exception as e:o['attempts'].append({'url':u,'error':type(e).__name__+': '+str(e)})
OUT.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,indent=2,sort_keys=True))
