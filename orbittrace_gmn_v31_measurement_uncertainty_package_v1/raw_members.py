from __future__ import annotations
import csv,hashlib,math,urllib.request
from pathlib import Path
YEARS=(2022,2023); MONTHS=range(1,13); BLIND=(20.0,55.0)
URL='https://globalmeteornetwork.org/data/traj_summary_data/monthly/traj_summary_monthly_{year}{month:02d}.txt'
IDX={'id':0,'sol':5,'ra':7,'ra_sigma':8,'dec':9,'dec_sigma':10,'vg':15,'vg_sigma':16}
def num(x):
    try: v=float((x or '').strip())
    except ValueError: return None
    return v if math.isfinite(v) else None
def read(needed,root:Path):
    out={}; source=[]; protected=0
    for y in YEARS:
        for m in MONTHS:
            p=root/f'{y}{m:02d}.txt'; u=URL.format(year=y,month=m); h=hashlib.sha256(); n=0
            r=urllib.request.Request(u,headers={'User-Agent':'orbittrace-v31-member-package-v1/1.0'})
            with urllib.request.urlopen(r,timeout=300) as z,p.open('wb') as f:
                while True:
                    b=z.read(1<<20)
                    if not b: break
                    h.update(b); n+=len(b); f.write(b)
            source.append({'year':y,'month':m,'url':u,'bytes':n,'sha256':h.hexdigest()})
            with p.open('r',encoding='utf-8-sig',errors='replace',newline='') as f:
                for row in csv.reader(f,delimiter=';'):
                    if not row or row[0].lstrip().startswith('#') or len(row)<=IDX['sol']: continue
                    eid=row[0].strip(); sol=num(row[IDX['sol']])
                    if not eid or sol is None or not 0<=sol<360: continue
                    if BLIND[0]<=sol<=BLIND[1]: protected+=1; continue
                    if eid not in needed: continue
                    if len(row)<=IDX['vg_sigma']: vals=(None,)*6
                    else: vals=tuple(num(row[IDX[k]]) for k in ('ra','dec','vg','ra_sigma','dec_sigma','vg_sigma'))
                    key=(y,eid)
                    if key in out: raise RuntimeError(f'duplicate needed raw event {key}')
                    out[key]=(sol,)+vals
            p.unlink(missing_ok=True)
    if len(source)!=24: raise RuntimeError('missing monthly source')
    return out,source,protected
