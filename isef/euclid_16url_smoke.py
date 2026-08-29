#!/usr/bin/env python3
"""Validate all 16 Euclid Q2 Field-1 science URLs with tiny byte ranges."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json, urllib.request, time
from pathlib import Path
import euclid_16epoch_feasibility as m

OUT=Path('results/euclid_16url_smoke.json')

def check(i,url):
    t=time.time(); req=urllib.request.Request(url,headers={'Range':'bytes=0-79','User-Agent':'isef-euclid-feasibility/manifest-check'})
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            data=r.read(81); h=dict(r.headers.items()); status=r.status
        return {'index':i,'file':m.FILES[i],'status':status,'bytes':len(data),'content_range':h.get('Content-Range'),'fits':data.startswith(b'SIMPLE'),'elapsed':round(time.time()-t,3),'ok':status==206 and len(data)==80 and data.startswith(b'SIMPLE')}
    except Exception as e:
        return {'index':i,'file':m.FILES[i],'error':f'{type(e).__name__}: {e}','elapsed':round(time.time()-t,3),'ok':False}

def main():
    t=time.time(); rows=[]
    with ThreadPoolExecutor(max_workers=8) as ex:
        fs=[ex.submit(check,i,u) for i,u in enumerate(m.URLS)]
        for f in as_completed(fs): rows.append(f.result())
    rows.sort(key=lambda x:x['index'])
    result={'success':all(r['ok'] for r in rows),'elapsed_seconds':round(time.time()-t,3),'rows':rows}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
    if not result['success']: raise SystemExit(1)
if __name__=='__main__': main()
