#!/usr/bin/env python3
"""Run the blinded 5XMM-vs-4XMM probe with parallel HTTP range downloads.
This revision picks up the official slim 4XMM-DR14 unique-source catalogue.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import urllib.request
import xmm_dr15_reprocessing_probe as base

def head(url):
    req=urllib.request.Request(url,method='HEAD',headers={'User-Agent':'ISEF-XMM-fast/1.1'})
    with urllib.request.urlopen(req,timeout=30) as r:return int(r.headers['Content-Length'])

def one(url,start,end,path):
    req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-fast/1.1','Range':f'bytes={start}-{end}'})
    with urllib.request.urlopen(req,timeout=120) as r:
        if r.status not in (200,206):raise RuntimeError(f'HTTP {r.status}')
        data=r.read()
    expected=end-start+1
    if len(data)!=expected:raise RuntimeError(f'range {start}-{end}: got {len(data)}, expected {expected}')
    path.write_bytes(data);return len(data)

def parallel_dl(url,p,workers=16):
    total=head(url)
    if p.exists() and p.stat().st_size==total:return
    chunk=(total+workers-1)//workers;parts=[]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        fs=[]
        for i in range(workers):
            s=i*chunk
            if s>=total:break
            e=min(total-1,(i+1)*chunk-1);part=Path(f'{p}.part{i:02d}');parts.append(part);fs.append(ex.submit(one,url,s,e,part))
        for f in as_completed(fs):f.result()
    with p.open('wb') as out:
        for part in parts:
            with part.open('rb') as src:
                while True:
                    b=src.read(16*1024*1024)
                    if not b:break
                    out.write(b)
            part.unlink()
    if p.stat().st_size!=total:raise RuntimeError(f'assembled size {p.stat().st_size} != {total}')

base.dl=parallel_dl
base.main()
