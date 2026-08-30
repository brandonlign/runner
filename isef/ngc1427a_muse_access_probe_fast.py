#!/usr/bin/env python3
import json,re,urllib.request
from pathlib import Path
URL='https://archive.eso.org/doidownload/script/NGC1427A_MUSE-Deep'
OUT=Path('results/ngc1427a_muse_access_probe_fast.json');OUT.parent.mkdir(exist_ok=True)
o={'status':'ACCESS_SCRIPT_ONLY','science_data_read':False,'url':URL}
try:
 req=urllib.request.Request(URL,headers={'User-Agent':'ISEF-NGC1427A-FastProbe/1.0'})
 with urllib.request.urlopen(req,timeout=30) as r:
  raw=r.read();o['status_code']=r.status;o['headers']={k:v for k,v in r.headers.items()};txt=raw.decode('utf-8','replace')
 o['script_chars']=len(txt);o['script_text']=txt
 o['http_urls']=re.findall(r'https?://[^\s\'"<>]+',txt)
 o['fits_tokens']=re.findall(r'[^\s\'"<>]+\.fits(?:\.fz|\.gz)?',txt,re.I)
 o['success']=True
except Exception as e:o['success']=False;o['error']=type(e).__name__+': '+str(e)
OUT.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps(o,indent=2))
