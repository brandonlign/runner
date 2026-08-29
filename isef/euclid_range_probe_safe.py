#!/usr/bin/env python3
"""Safety wrapper around euclid_range_probe: bounded reads even on HTTP 200."""
import urllib.request
import euclid_range_probe as m

def safe_http_range(start,end):
    want=end-start+1
    req=urllib.request.Request(m.URL,headers={'Range':f'bytes={start}-{end}','User-Agent':'isef-euclid-feasibility/1.2'})
    with urllib.request.urlopen(req,timeout=60) as r:
        return r.read(want+1),dict(r.headers.items()),r.status

m.http_range=safe_http_range
m.main()
