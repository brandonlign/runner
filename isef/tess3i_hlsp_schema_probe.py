#!/usr/bin/env python3
"""Inspect only metadata/schema of the latest TESS-3I light-curve HLSP FITS files.

The script downloads small light-curve FITS products but does not read table rows,
flux arrays, periodograms, or any science values. It reports HDU names, dimensions,
column names/formats/units, and selected non-science header metadata only.
"""
import json,urllib.request
from pathlib import Path
from astropy.io import fits
OUT=Path('results/tess3i_hlsp_schema_probe.json'); OUT.parent.mkdir(exist_ok=True)
REC='https://zenodo.org/api/records/19376249'
o={'status':'SCHEMA_ONLY','science_flux_rows_accessed':False,'success':False}
try:
 req=urllib.request.Request(REC,headers={'User-Agent':'ISEF-TESS3I-Schema/1.0'})
 with urllib.request.urlopen(req,timeout=120) as r: meta=json.load(r)
 files=[]
 for f in meta.get('files',[]):
  name=f.get('key','')
  if name.endswith('_lc.fits'):
   url=f.get('links',{}).get('content') or f.get('links',{}).get('self')
   if not url: continue
   p=Path('/tmp')/name
   req=urllib.request.Request(url,headers={'User-Agent':'ISEF-TESS3I-Schema/1.0'})
   with urllib.request.urlopen(req,timeout=180) as r, open(p,'wb') as w:
    while True:
     b=r.read(1<<20)
     if not b: break
     w.write(b)
   info={'name':name,'bytes':p.stat().st_size,'hdus':[]}
   with fits.open(p,memmap=True,lazy_load_hdus=False) as h:
    for i,x in enumerate(h):
     hh=x.header
     d={'index':i,'extname':hh.get('EXTNAME','PRIMARY'),'naxis':hh.get('NAXIS'),'naxis1':hh.get('NAXIS1'),'naxis2':hh.get('NAXIS2')}
     if isinstance(x,(fits.BinTableHDU,fits.TableHDU)):
      d['columns']=[{'name':c.name,'format':c.format,'unit':c.unit} for c in x.columns]
     for k in ['TELESCOP','INSTRUME','OBJECT','SECTOR','CAMERA','CCD','TIMESYS','TIMEUNIT','TSTART','TSTOP','CADENCE','VERSION']:
      if k in hh: d[k.lower()]=str(hh[k])
     info['hdus'].append(d)
   files.append(info)
 o['record_version']=meta.get('metadata',{}).get('version'); o['lightcurve_files']=files
 o['success']=True; o['decision']='TESS3I_HLSP_SCHEMA_READY' if files else 'NO_LC_FILES_FOUND'
except Exception as e:
 o['error']=type(e).__name__+': '+str(e); o['decision']='INFRASTRUCTURE_FAILURE_NO_SCIENCE_DECISION'
OUT.write_text(json.dumps(o,indent=2)+'\n'); print(json.dumps(o,indent=2))
