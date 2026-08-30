#!/usr/bin/env python3
"""First Stage-A science transport: predetermined central tile, off-line band only.

Stage-A protocol was frozen before this request. This script downloads the
+75-A null window for the central deterministic tile, but reads/emits FITS
headers only. It does not inspect, summarize, count, plot, or emit pixel values.
"""
import json,math,urllib.parse,urllib.request
from pathlib import Path
from astropy.io import fits
DP='ADP.2026-06-24T16:04:14.194'; ID='ivo://eso.org/ID?'+DP
SODA='https://dataportal.eso.org/dataPortal/soda/sync'
OUT=Path('results/ngc1427a_soda_offline_transport_probe.json');OUT.parent.mkdir(exist_ok=True)
TMP=Path('/tmp/ngc1427a_stagea_offline_center.fits')
# Frozen WCS reference from header-only v3; central normalized tile coincides
# with the WCS reference pixel to <1 pixel.
RA=55.045646972206; DEC=-35.618826927816; RAD=8/3600
c=299792.458; v=2036.0; beta=v/c; D=math.sqrt((1+beta)/(1-beta))
line=5006.843*D; center=line+75.0; lo=(center-12.5)*1e-10; hi=(center+12.5)*1e-10
params={'ID':ID,'CIRCLE':f'{RA} {DEC} {RAD}','BAND':f'{lo:.12e} {hi:.12e}'}
url=SODA+'?'+urllib.parse.urlencode(params)
o={'status':'STAGEA_OFFLINE_TRANSPORT_ONLY','stagea_freeze':'a468846f91e726139bf84e3f14b7138558748db6','science_pixels_downloaded':True,'science_pixel_values_inspected':False,'real_oiii_window_accessed':False,'real_peaks_inspected':False,'query':params,'success':False}
try:
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-NGC1427A-StageA-offline/1.0'})
 with urllib.request.urlopen(req,timeout=300) as r:
  data=r.read(200_000_000); o['http_status']=r.status;o['content_type']=r.headers.get('Content-Type');o['bytes_received']=len(data)
 if len(data)>=200_000_000: raise RuntimeError('unexpectedly large response; refusing further processing')
 TMP.write_bytes(data)
 hd=[]
 with fits.open(TMP,memmap=False,lazy_load_hdus=False) as h:
  for i,x in enumerate(h):
   hdr=x.header
   keep=['EXTNAME','XTENSION','BITPIX','NAXIS','NAXIS1','NAXIS2','NAXIS3','BUNIT','CRPIX1','CRPIX2','CRPIX3','CRVAL1','CRVAL2','CRVAL3','CDELT1','CDELT2','CDELT3','CD1_1','CD2_2','CD3_3','CTYPE1','CTYPE2','CTYPE3','CUNIT1','CUNIT2','CUNIT3']
   hd.append({'index':i,'selected':{k:hdr[k] for k in keep if k in hdr}})
 o['hdus']=hd;o['success']=True
except Exception as e:o['error']=type(e).__name__+': '+str(e)
finally:
 try: TMP.unlink(missing_ok=True)
 except Exception: pass
OUT.write_text(json.dumps(o,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps(o,indent=2,sort_keys=True,default=str))
