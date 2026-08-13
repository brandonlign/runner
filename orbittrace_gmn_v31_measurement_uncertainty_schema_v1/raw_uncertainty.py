from __future__ import annotations
import csv,hashlib,math,urllib.request
from pathlib import Path
from typing import Any
YEARS=(2022,2023); MONTHS=tuple(range(1,13)); BLIND=(20.0,55.0)
URL='https://globalmeteornetwork.org/data/traj_summary_data/monthly/traj_summary_monthly_{year}{month:02d}.txt'
IDX={'id':0,'sol':5,'ra_sigma':8,'dec_sigma':10,'vg_sigma':16}

def req(x,m):
    if not x: raise RuntimeError(m)
def num(x):
    t=(x or '').strip()
    if not t or t.lower() in {'nan','none','null','na','...'}: return None
    try: v=float(t)
    except ValueError: return None
    return v if math.isfinite(v) else None

def fetch(url: str,path: Path)->dict[str,Any]:
    h=hashlib.sha256(); n=0
    r=urllib.request.Request(url,headers={'User-Agent':'orbittrace-gmn-v31-uncertainty-schema-v1/1.0'})
    with urllib.request.urlopen(r,timeout=300) as q,path.open('wb') as out:
        while True:
            b=q.read(1<<20)
            if not b: break
            h.update(b); n+=len(b); out.write(b)
    return {'url':url,'bytes':n,'sha256':h.hexdigest()}

def load(root: Path):
    data={}; sources=[]; counts={'raw_records':0,'protected_discarded_before_uncertainty':0,'invalid_id_or_sol':0,'retained_raw_records':0}
    for y in YEARS:
        for m in MONTHS:
            p=root/f'{y}{m:02d}.txt'; meta=fetch(URL.format(year=y,month=m),p); meta.update(year=y,month=m); sources.append(meta)
            with p.open('r',encoding='utf-8-sig',errors='replace',newline='') as f:
                for row in csv.reader(f,delimiter=';'):
                    if not row or row[0].lstrip().startswith('#'): continue
                    counts['raw_records']+=1
                    if len(row)<=IDX['sol']:
                        counts['invalid_id_or_sol']+=1; continue
                    eid=row[IDX['id']].strip(); sol=num(row[IDX['sol']])
                    if not eid or sol is None or not 0<=sol<360:
                        counts['invalid_id_or_sol']+=1; continue
                    if BLIND[0]<=sol<=BLIND[1]:
                        counts['protected_discarded_before_uncertainty']+=1; continue
                    sig=(None,None,None) if len(row)<=IDX['vg_sigma'] else (num(row[IDX['ra_sigma']]),num(row[IDX['dec_sigma']]),num(row[IDX['vg_sigma']]))
                    key=(y,eid); req(key not in data,f'duplicate raw ID {key}'); data[key]=sig; counts['retained_raw_records']+=1
            p.unlink(missing_ok=True)
    req(len(sources)==24,'missing fixed monthly source')
    return data,sources,counts
