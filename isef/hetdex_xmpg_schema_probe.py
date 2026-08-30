#!/usr/bin/env python3
"""Schema/size-only probe for HETDEX HPSC1/HPSC2 XMPG project.
No catalog rows or source identities are read.
"""
from pathlib import Path
import json,re,time,urllib.request
OUT=Path('results/hetdex_xmpg_schema_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
BASE1='https://web.corral.tacc.utexas.edu/hetdex/HETDEX/catalogs/hetdex_source_catalog_1/'
BASE2='https://web.corral.tacc.utexas.edu/hetdex/HETDEX/pdr/pdr1/hetdex_source_catalog_2/'
FILES={
 'hpsc1_readme':BASE1+'README',
 'hpsc1_source':BASE1+'hetdex_sc1_v3.2.dat',
 'hpsc1_det':BASE1+'hetdex_sc1_detinfo_v3.2.dat',
 'hpsc1_spec':BASE1+'hetdex_sc1_spec_v3.2.fits',
 'hpsc2_readme':BASE2+'readme',
 'hpsc2_source':BASE2+'hetdex_sc2_v1.5.dat',
 'hpsc2_det':BASE2+'hetdex_sc2_detinfo_v1.5.dat',
 'hpsc2_spec':BASE2+'hetdex_sc2_spec_v1.5.fits',
}
def req(url,method='GET',headers=None,timeout=120):
 h={'User-Agent':'ISEF-HETDEX-XMPG-schema/1.0'};h.update(headers or {})
 r=urllib.request.Request(url,method=method,headers=h)
 return urllib.request.urlopen(r,timeout=timeout)
def head(url):
 try:
  with req(url,'HEAD',timeout=60) as r:return {'status':r.status,'content_length':r.headers.get('Content-Length'),'content_type':r.headers.get('Content-Type'),'last_modified':r.headers.get('Last-Modified')}
 except Exception as e:return {'error':f'{type(e).__name__}: {e}'}
def read_text_retry(url,max_bytes=100000):
 last=None
 for i in range(4):
  try:
   with req(url,'GET',headers={'Range':f'bytes=0-{max_bytes-1}'},timeout=90) as r:
    b=r.read(max_bytes);return b.decode('utf-8','replace')
  except Exception as e:last=e;time.sleep(2*(i+1))
 raise last
def main():
 out={'success':True,'status':'SCHEMA_ONLY','files':{},'readmes':{},'note':'No catalog source rows or spectra inspected.'}
 for k,u in FILES.items():out['files'][k]=head(u)
 for key,u in [('hpsc1',FILES['hpsc1_readme']),('hpsc2',FILES['hpsc2_readme'])]:
  try:
   t=read_text_retry(u,120000)
   # retain only documentation text; redact anything looking like explicit HETDEX source designation
   t=re.sub(r'HETDEX\s+J\d{6,}[.+-]\d+','[SOURCE_REDACTED]',t)
   out['readmes'][key]=t[:30000]
  except Exception as e:out['readmes'][key]={'error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
