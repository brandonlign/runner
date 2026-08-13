from __future__ import annotations
import csv,hashlib,math,tempfile,urllib.request
from pathlib import Path
YEARS=(2022,2023); MONTHS=range(1,13); BLIND=(20.0,55.0); ID=0; SOL=5; NUM_STAT=84
URL='https://globalmeteornetwork.org/data/traj_summary_data/monthly/traj_summary_monthly_{year}{month:02d}.txt'
def num(x):
    try: v=float((x or '').strip())
    except ValueError: return None
    return v if math.isfinite(v) else None
def load(ids):
    wanted=set(map(str,ids)); out={}; sources=[]; protected=0
    with tempfile.TemporaryDirectory(prefix='orbittrace_four_observer_') as td:
        root=Path(td)
        for y in YEARS:
            for m in MONTHS:
                path=root/f'{y}{m:02d}.txt'; url=URL.format(year=y,month=m); h=hashlib.sha256(); size=0
                req=urllib.request.Request(url,headers={'User-Agent':'orbittrace-v31-four-observer-file-v1/1.0'})
                with urllib.request.urlopen(req,timeout=300) as z,path.open('wb') as f:
                    while True:
                        b=z.read(1<<20)
                        if not b: break
                        h.update(b);size+=len(b);f.write(b)
                sources.append({'year':y,'month':m,'url':url,'bytes':size,'sha256':h.hexdigest()})
                with path.open('r',encoding='utf-8-sig',errors='replace',newline='') as f:
                    for row in csv.reader(f,delimiter=';'):
                        if not row or row[0].lstrip().startswith('#') or len(row)<=SOL: continue
                        eid=row[ID].strip(); sol=num(row[SOL])
                        if not eid or sol is None or not 0<=sol<360: continue
                        if BLIND[0]<=sol<=BLIND[1]: protected+=1; continue
                        if eid not in wanted: continue
                        value=num(row[NUM_STAT]) if len(row)>NUM_STAT else None
                        n=int(round(value)) if value is not None and abs(value-round(value))<=1e-9 else None
                        key=(y,eid)
                        if key in out: raise RuntimeError(f'duplicate immutable event {key}')
                        out[key]=n
                path.unlink(missing_ok=True)
    if len(sources)!=24: raise RuntimeError('monthly source count drift')
    result={}
    for eid in sorted(wanted):
        y=int(eid[:4]); n=out.get((y,eid))
        if not isinstance(n,int) or n<2: raise RuntimeError(f'incomplete immutable observer count {eid}')
        result[eid]=n
    if len(result)!=8794: raise RuntimeError(f'complete-member count drift {len(result)}')
    return result,sources,protected
