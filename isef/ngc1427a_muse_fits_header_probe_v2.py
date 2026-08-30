#!/usr/bin/env python3
"""Byte-capped structure-only probe for NGC1427A MUSE product.

Uses curl with an explicit Range request and a hard output cap. Only FITS header
cards from the start of the product are parsed; science-array values are never
requested intentionally or interpreted.
"""
import json, subprocess
from pathlib import Path
URL='https://dataportal.eso.org/dataPortal/file/ADP.2026-06-24T16:04:14.194'
OUT=Path('results/ngc1427a_muse_fits_header_probe_v2.json'); OUT.parent.mkdir(exist_ok=True)
o={'status':'HEADER_ONLY_V2','science_values_read':False,'url':URL,'success':False}
try:
    # Request only the first 64 KiB. --max-time bounds transport; --fail makes
    # HTTP failures explicit. Even if an intermediary misbehaves, communicate
    # only enough bytes for the leading header and reject oversized capture.
    p=subprocess.run(['curl','-L','--fail','--silent','--show-error','--max-time','120','--range','0-65535',URL],capture_output=True,timeout=130)
    if p.returncode!=0: raise RuntimeError(p.stderr.decode('utf-8','replace')[:500])
    raw=p.stdout
    if len(raw)>131072: raise RuntimeError(f'byte cap violated: {len(raw)}')
    o['bytes_received']=len(raw)
    cards=[]
    for i in range(0,len(raw)-79,80):
        c=raw[i:i+80].decode('ascii','replace'); cards.append(c)
        if c.startswith('END '): break
    o['primary_header_complete']=any(c.startswith('END ') for c in cards)
    o['primary_header_cards']=len(cards)
    keep={'SIMPLE','BITPIX','NAXIS','NAXIS1','NAXIS2','NAXIS3','EXTEND','DATE','ORIGIN','OBJECT','TELESCOP','INSTRUME','PRODCATG','WCSAXES','CRPIX1','CRPIX2','CRPIX3','CRVAL1','CRVAL2','CRVAL3','CDELT1','CDELT2','CDELT3','CTYPE1','CTYPE2','CTYPE3','CUNIT1','CUNIT2','CUNIT3','BUNIT'}
    meta={}
    for c in cards:
        if len(c)>=10 and c[8:10]=='= ':
            k=c[:8].strip(); v=c[10:].split('/')[0].strip()
            if k in keep: meta[k]=v
    o['primary_selected']=meta
    o['success']=bool(o['primary_header_complete'])
    if not o['success']: o['error']='leading FITS END card not found in capped response'
except Exception as e:
    o['error']=type(e).__name__+': '+str(e)
OUT.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n'); print(json.dumps(o,indent=2,sort_keys=True))
