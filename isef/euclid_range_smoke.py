#!/usr/bin/env python3
"""Safe Euclid Q2 HTTP byte-range smoke test.

Never reads more than the requested byte count + 1, even if the origin ignores
Range and responds with the entire multi-GB object.
"""
from __future__ import annotations
import json, time, urllib.request
from pathlib import Path

URL='https://irsa.ipac.caltech.edu/data/Euclid/q2/data/EUC_VIS_SWL-DET-067070-00-1__20250621T020155.487037Z_sci.fits'
OUT=Path('results/euclid_range_smoke.json')

def bounded_range(start,end):
    want=end-start+1
    req=urllib.request.Request(URL,headers={'Range':f'bytes={start}-{end}','User-Agent':'isef-euclid-feasibility/1.1'})
    with urllib.request.urlopen(req,timeout=30) as r:
        data=r.read(want+1)
        return data,dict(r.headers.items()),r.status

def main():
    t=time.time(); result={'url':URL,'success':False}
    try:
        data,h,status=bounded_range(0,1023)
        result['status']=status
        result['bytes_read']=len(data)
        result['content_range']=h.get('Content-Range')
        result['accept_ranges']=h.get('Accept-Ranges')
        result['content_length']=h.get('Content-Length')
        result['fits_prefix']=data[:80].decode('ascii',errors='replace')
        if status!=206:
            raise RuntimeError(f'Range ignored: HTTP {status}; safely stopped after {len(data)} bytes')
        if len(data)!=1024:
            raise RuntimeError(f'Unexpected range length {len(data)}')
        if not data.startswith(b'SIMPLE'):
            raise RuntimeError('Response does not begin with FITS SIMPLE card')
        result['success']=True
    except Exception as e:
        result['error']=f'{type(e).__name__}: {e}'
        raise
    finally:
        result['elapsed_seconds']=round(time.time()-t,3)
        OUT.parent.mkdir(parents=True,exist_ok=True)
        OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__': main()
