#!/usr/bin/env python3
"""Exact reusable routing for arbitrary Euclid Q2 Field-1 sky positions.

The earlier Stage-0 router inferred detector changes from a global dither shift,
which is adequate for its one selected target but can fail near detector gaps for
arbitrary positions. Here each of the four pointing groups gets its actual 144
quadrant WCS headers; a target is routed by direct WCS containment. The stamp
reader also scalarizes Astropy's 0-D array coordinates before rounding.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import euclid_routed_feasibility as b


def map_groups(max_workers=48):
    groups=[[None]*144 for _ in range(4)]
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        fs={ex.submit(b.getq,g,k):(g,k) for g in range(4) for k in range(144)}
        for f in as_completed(fs):
            g,k=fs[f];groups[g][k]=f.result()
    return groups


def route_target(groups,target,margin=b.MARGIN):
    ra,de=map(float,target);routes={};diag=[]
    for g,qs in enumerate(groups):
        inside=[]
        for q in qs:
            x,y=b.pix(q,ra,de);x=float(np.asarray(x));y=float(np.asarray(y))
            if np.isfinite(x) and np.isfinite(y) and margin<=x<b.NX-margin and margin<=y<b.NY-margin:
                edge=min(x,b.NX-1-x,y,b.NY-1-y);inside.append((edge,q.k,q.name,x,y))
        if not inside:
            raise RuntimeError(f'exact WCS: target not safely contained in any quadrant for group {g}')
        edge,k,name,x,y=max(inside)
        routes[g]=int(k);diag.append({'group':g,'k':int(k),'extname':name,'x':x,'y':y,'edge_margin_px':float(edge),'overlaps':len(inside)})
    return routes,diag


def stamp(epoch,q,ra,de):
    x,y=b.pix(q,float(ra),float(de));x=float(np.asarray(x));y=float(np.asarray(y));cx=int(round(x));cy=int(round(y));x0=cx-b.HALF;y0=cy-b.HALF
    if x0<0 or y0<0 or x0+b.STAMP>b.NX or y0+b.STAMP>b.NY:
        raise RuntimeError(f'exact stamp outside quadrant epoch={epoch} {q.name} x={x} y={y}')
    data0=b.offset(q.k)+b.HDR;start=data0+y0*b.NX*b.BPP;end=data0+(y0+b.STAMP)*b.NX*b.BPP-1;raw,_=b.rr(b.URLS[epoch],start,end,90)
    rows=np.frombuffer(raw,dtype='>f4').reshape(b.STAMP,b.NX);z=rows[:,x0:x0+b.STAMP].astype(np.float32)
    return epoch,z,{'x0':x0,'y0':y0,'x':x,'y':y,'extname':q.name,'k':q.k}
