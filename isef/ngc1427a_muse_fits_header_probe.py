#!/usr/bin/env python3
"""Source-free structure probe for the public NGC1427A deep MUSE product.

Reads only HTTP metadata and the leading FITS header blocks. It refuses to
interpret or emit science-array values.
"""
import json, urllib.request
from pathlib import Path
URL='https://dataportal.eso.org/dataPortal/file/ADP.2026-06-24T16:04:14.194'
OUT=Path('results/ngc1427a_muse_fits_header_probe.json'); OUT.parent.mkdir(exist_ok=True)

def cards(buf):
    out=[]
    for i in range(0,len(buf)-79,80):
        s=buf[i:i+80].decode('ascii','replace')
        out.append(s)
        if s.startswith('END '): break
    return out

def kv(card):
    if len(card)<10 or card[8:10] != '= ': return None,None
    k=card[:8].strip(); v=card[10:].split('/')[0].strip()
    return k,v

o={'status':'HEADER_ONLY','science_values_read':False,'url':URL,'success':False}
try:
    req=urllib.request.Request(URL,method='HEAD',headers={'User-Agent':'ISEF-NGC1427A-PNLF-Header/1.0'})
    with urllib.request.urlopen(req,timeout=60) as r:
        o['head_status']=r.status; o['head_headers']={k:v for k,v in r.headers.items()}
    # FITS headers are ASCII cards in 2880-byte blocks. 1 MiB is enough to
    # discover early HDU headers without deliberately reading any array values.
    req=urllib.request.Request(URL,headers={'Range':'bytes=0-1048575','User-Agent':'ISEF-NGC1427A-PNLF-Header/1.0'})
    with urllib.request.urlopen(req,timeout=120) as r:
        raw=r.read(); o['range_status']=r.status; o['content_range']=r.headers.get('Content-Range'); o['bytes_received']=len(raw)
    # Parse only the first header at byte zero. Do not walk data extents because
    # that could cross into science arrays. Report selected structural metadata.
    cs=cards(raw)
    keep={'SIMPLE','BITPIX','NAXIS','NAXIS1','NAXIS2','NAXIS3','EXTEND','DATE','ORIGIN','OBJECT','TELESCOP','INSTRUME','PRODCATG','WCSAXES','CRPIX1','CRPIX2','CRPIX3','CRVAL1','CRVAL2','CRVAL3','CDELT1','CDELT2','CDELT3','CTYPE1','CTYPE2','CTYPE3','CUNIT1','CUNIT2','CUNIT3','BUNIT'}
    meta={}
    for c in cs:
        k,v=kv(c)
        if k in keep: meta[k]=v
    o['primary_header_cards']=len(cs); o['primary_selected']=meta
    o['primary_header_complete']=any(c.startswith('END ') for c in cs)
    o['success']=True
except Exception as e:
    o['error']=type(e).__name__+': '+str(e)
OUT.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n'); print(json.dumps(o,indent=2,sort_keys=True))
