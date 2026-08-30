#!/usr/bin/env python3
import json,re,urllib.request,urllib.parse
from pathlib import Path
URL='https://archive.eso.org/doidownload/script/NGC1427A_MUSE-Deep'
OUT=Path('results/ngc1427a_muse_access_probe.json');OUT.parent.mkdir(exist_ok=True)
def fetch(u,method='GET'):
 req=urllib.request.Request(u,method=method,headers={'User-Agent':'ISEF-NGC1427A-AccessProbe/1.0'})
 with urllib.request.urlopen(req,timeout=120) as r:return r.status,dict(r.headers),r.read() if method=='GET' else b''
o={'status':'ACCESS_ONLY','science_data_read':False,'script_url':URL}
try:
 st,h,b=fetch(URL);txt=b.decode('utf-8','replace');o['script_status']=st;o['script_chars']=len(txt);o['script_text']=txt
 urls=re.findall(r'https?://[^\s\'"<>]+',txt)
 files=[]
 for u in urls:
  u=u.rstrip(');,')
  try:
   s,hh,_=fetch(u,'HEAD');files.append({'url':u,'status':s,'content_length':hh.get('Content-Length'),'content_type':hh.get('Content-Type'),'content_disposition':hh.get('Content-Disposition')})
  except Exception as e:files.append({'url':u,'error':type(e).__name__+': '+str(e)})
 o['url_metadata']=files;o['success']=True
except Exception as e:o['success']=False;o['error']=type(e).__name__+': '+str(e)
OUT.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps(o,indent=2))
