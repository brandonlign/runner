#!/usr/bin/env python3
"""Inspect TESS-3I LC extension headers only; do not read any table rows."""
import json,urllib.request
from pathlib import Path
from astropy.io import fits
OUT=Path('results/tess3i_aperture_header_probe.json'); OUT.parent.mkdir(exist_ok=True)
REC='https://zenodo.org/api/records/19376249'
o={'status':'HEADER_ONLY','science_rows_accessed':False,'success':False}
try:
 with urllib.request.urlopen(urllib.request.Request(REC,headers={'User-Agent':'ISEF-TESS3I-ApertureHeader/1.0'}),timeout=120) as r: meta=json.load(r)
 fs=[f for f in meta.get('files',[]) if f.get('key','').endswith('_lc.fits')]
 out=[]
 for f in fs:
  name=f['key']; url=f.get('links',{}).get('content') or f.get('links',{}).get('self'); p=Path('/tmp')/name
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ISEF-TESS3I-ApertureHeader/1.0'}),timeout=180) as r, open(p,'wb') as w:
   while True:
    b=r.read(1<<20)
    if not b: break
    w.write(b)
  ff={'name':name,'extensions':[]}
  with fits.open(p,memmap=True,lazy_load_hdus=False) as h:
   for x in h[1:4]:
    hdr=x.header
    # Emit all non-structural header cards; header metadata are not row science values.
    skip={'XTENSION','BITPIX','NAXIS','NAXIS1','NAXIS2','PCOUNT','GCOUNT','TFIELDS'}
    cards={}
    for c in hdr.cards:
     k=c.keyword
     if k in skip or k.startswith('TTYPE') or k.startswith('TFORM') or k.startswith('TUNIT'): continue
     if k and k not in {'COMMENT','HISTORY',''}:
      try: cards[k]=str(c.value)
      except Exception: pass
    ff['extensions'].append({'extname':hdr.get('EXTNAME'),'cards':cards})
  out.append(ff)
 o['files']=out; o['success']=True; o['decision']='APERTURE_HEADERS_READY'
except Exception as e:
 o['error']=type(e).__name__+': '+str(e); o['decision']='INFRASTRUCTURE_FAILURE_NO_SCIENCE_DECISION'
OUT.write_text(json.dumps(o,indent=2)+'\n'); print(json.dumps(o,indent=2))
