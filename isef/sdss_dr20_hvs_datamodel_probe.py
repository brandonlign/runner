#!/usr/bin/env python3
"""Read only the public DR20 GravPot16 data-model HTML; no catalog rows."""
from pathlib import Path
import urllib.request,re,json,html
OUT=Path('results/sdss_dr20_hvs_datamodel_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
URL='https://data.sdss.org/datamodel/files/MWM_ORBITS/GravPot16.html'
def main():
 out={'success':False,'status':'SCHEMA_ONLY','url':URL}
 try:
  req=urllib.request.Request(URL,headers={'User-Agent':'ISEF-SDSS-HVS-schema/1.1'})
  with urllib.request.urlopen(req,timeout=60) as r:s=r.read(2_000_000).decode('utf-8','replace')
  txt=html.unescape(re.sub(r'<[^>]+>',' ',s));txt=re.sub(r'\s+',' ',txt)
  out={'success':True,'status':'SCHEMA_ONLY','url':URL,'text':txt[:120000],'keywords':{k:[m.start() for m in re.finditer(k,txt,re.I)][:20] for k in ['velocity','orbit','energy','eccentric','apoc','peric','error','uncert','monte','gaia','rv','vhelio','distance']},'note':'Documentation only; no source rows or identities inspected.'}
 except Exception as e:out['error']=f'{type(e).__name__}: {e}'
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
