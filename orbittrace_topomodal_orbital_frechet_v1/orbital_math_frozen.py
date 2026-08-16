#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import math
from typing import Any

MIN_SUPPORT=4


def req(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)

def dsh2(a:dict[str,float],b:dict[str,float])->float:
    e1,q1=float(a['e']),float(a['q_au']); e2,q2=float(b['e']),float(b['q_au'])
    i1,w1,o1=map(math.radians,(float(a['i_deg']),float(a['peri_deg']),float(a['node_deg'])))
    i2,w2,o2=map(math.radians,(float(b['i_deg']),float(b['peri_deg']),float(b['node_deg'])))
    ci=math.cos(i1)*math.cos(i2)+math.sin(i1)*math.sin(i2)*math.cos(o1-o2); I=math.acos(max(-1.0,min(1.0,ci)))
    dO=o2-o1; sgn=1.0 if abs(dO)<=math.pi else -1.0; den=math.cos(I/2.0); req(abs(den)>1e-14,'degenerate antiparallel orbital planes')
    x=math.cos((i2+i1)/2.0)*math.sin(dO/2.0)/den; x=max(-1.0,min(1.0,x)); Pi=w2-w1+sgn*2.0*math.asin(x)
    value=(q1-q2)**2+(e1-e2)**2+(2.0*math.sin(I/2.0))**2+(((e1+e2)/2.0)*2.0*math.sin(Pi/2.0))**2
    req(math.isfinite(value) and value>=-1e-14,'invalid D_SH^2'); return max(0.0,float(value))

def frechet(members:list[str],mapping:dict[str,dict[str,float]])->tuple[float,str,str]:
    ids=sorted(map(str,members)); n=len(ids); req(n>=MIN_SUPPORT,'sub-support candidate'); req(all(eid in mapping and mapping[eid] is not None for eid in ids),'candidate missing orbit')
    sums=[0.0]*n; h=hashlib.sha256()
    for j in range(n):
        for k in range(j+1,n):
            d=dsh2(mapping[ids[j]],mapping[ids[k]]); sums[j]+=d; sums[k]+=d; h.update(f'{ids[j]}|{ids[k]}={float(d).hex()}\n'.encode())
    means=[x/float(n-1) for x in sums]; best=min(means); med=min(ids[j] for j,v in enumerate(means) if abs(v-best)<=1e-15); return float(best),med,h.hexdigest()

def orbital_order(rows:list[dict[str,Any]],mapping:dict[str,dict[str,float]])->list[dict[str,Any]]:
    out=[]
    for src in rows:
        ids=list(map(str,src['event_ids'])); energy,med,pairsha=frechet(ids,mapping); r=dict(src); r['family_id']=hashlib.sha256(('ORBF1|'+'|'.join(sorted(ids))).encode()).hexdigest()[:20]; r['orbital_frechet_energy']=energy; r['orbital_medoid_event_id']=med; r['pairwise_dsh2_sha256']=pairsha; out.append(r)
    out.sort(key=lambda r:(0 if bool(r['is_root']) else 1,float(r['orbital_frechet_energy']),str(r['family_hash'])))
    for rank,r in enumerate(out,1):r['rank']=rank
    req([int(r['rank']) for r in out]==list(range(1,len(out)+1)),'rank continuity'); return out
