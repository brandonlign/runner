#!/usr/bin/env python3
from pathlib import Path
import json,urllib.request
from astropy.io import fits
U='http://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4xmmdr14_obslist.fits'
P=Path('/tmp/4xmmdr14_obslist.fits'); O=Path('results/xmm_dr14_obslist_schema_probe.json'); O.parent.mkdir(parents=True,exist_ok=True)
try:
 with urllib.request.urlopen(urllib.request.Request(U,headers={'User-Agent':'ISEF-XMM-obslist-schema/1.1'}),timeout=120) as r,P.open('wb') as f: f.write(r.read())
 with fits.open(P,memmap=True) as h:
  tabs=[z for z in h if isinstance(z,(fits.BinTableHDU,fits.TableHDU)) and z.data is not None]
  t=max(tabs,key=lambda z:len(z.data)); names=list(t.data.names); n=len(t.data)
 out={'success':True,'rows':n,'bytes':P.stat().st_size,'columns':names,'recognized_obsid':[x for x in names if x.upper() in ('OBS_ID','OBSID','OBSERVATION_ID')]}
except Exception as e: out={'success':False,'error':f'{type(e).__name__}: {e}'}
O.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))
