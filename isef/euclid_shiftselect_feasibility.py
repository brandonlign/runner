#!/usr/bin/env python3
"""Fast Stage-0 target selection using measured Euclid dither translations."""
import math
import numpy as np
import euclid_routed_feasibility as b

QS=None;SELECTED=None;SHIFTS=None;CENTERS=None

def approx_hit(ra,dec):
    cd=max(math.cos(math.radians(dec)),0.2)
    d=np.hypot((CENTERS[:,0]-ra)*cd,CENTERS[:,1]-dec)*3600
    k=int(np.argmin(d)); arc=float(d[k])
    # A VIS quadrant is about 205 arcsec across. Requiring center distance <70
    # arcsec is deliberately conservative; exact WCS validates finalists.
    if arc>=70:return None
    return (1024-arc/0.1,k)

def translated(target,shift,sign):
    ra,dec=target;dra,ddec=shift
    return ra+sign*dra/(3600*max(math.cos(math.radians(dec)),0.2)),dec+sign*ddec/3600

def search(qs,shifts):
    med=(float(np.median(CENTERS[:,0])),float(np.median(CENTERS[:,1])))
    order=sorted(range(144),key=lambda k:b.dist_arcsec(qs[k].center,med,med[1]))
    offsets=[0,-20,20,-40,40,-60,60,-80,80];candidates=[]
    for sign in (-1,1):
      for oi,k in enumerate(order):
        cra,cdec=qs[k].center;cd=max(math.cos(math.radians(cdec)),0.2)
        for dx in offsets:
          for dy in offsets:
            target=(cra+dx/(3600*cd),cdec+dy/3600)
            hs=[approx_hit(*translated(target,shifts[g],sign)) for g in range(4)]
            if all(h is not None for h in hs):
                pred={g:hs[g][1] for g in range(4)};score=min(h[0] for h in hs)
                candidates.append((score,sign,k,target,pred,med))
        if candidates and oi>=20:break
    candidates.sort(reverse=True,key=lambda z:z[0]);diagnostics=[]
    for score,sign,k,target,pred,med in candidates[:300]:
        actual={};ok=True;rows=[]
        for g in range(4):
            q=b.getq(g,pred[g]);x,y=b.pix(q,*target);inside=b.contains(q,*target,b.MARGIN)
            rows.append({'group':g,'k':pred[g],'x':float(x),'y':float(y),'inside':bool(inside)})
            if not inside:ok=False;break
            actual[g]=pred[g]
        diagnostics.append({'score':float(score),'sign':sign,'epoch0_k':k,'pred':pred,'rows':rows})
        if ok:return score,sign,k,target,actual,med,diagnostics
    raise RuntimeError(f'no candidate validated; proposed={len(candidates)} tried={diagnostics[:30]}')

def patched_map_epoch0():return QS

def patched_choose_target(qs):
    score,sign,k,target,routes,med,diag=SELECTED;return k,target[0],target[1],med

def patched_route_groups(qs,target,shifts):
    score,sign,k,t,routes,med,diag=SELECTED;rows=[]
    for g,rk in routes.items():
        q=b.getq(g,rk);x,y=b.pix(q,*t)
        rows.append({'group':g,'candidate_k':rk,'extname':q.name,'x':float(x),'y':float(y),'inside':bool(b.contains(q,*t,b.MARGIN)),'shift_selection_sign':sign})
    rows.append({'selection_approx_margin_pixels':float(score),'validation_attempts':len(diag)})
    return routes,rows

def main():
    global QS,SELECTED,SHIFTS,CENTERS
    QS=b.map_epoch0();CENTERS=np.array([q.center for q in QS]);SHIFTS=b.pointing_shifts();SELECTED=search(QS,SHIFTS)
    print('SHIFT_SELECTED',{'score':SELECTED[0],'sign':SELECTED[1],'epoch0_k':SELECTED[2],'target':SELECTED[3],'routes':SELECTED[4]})
    b.map_epoch0=patched_map_epoch0;b.choose_target=patched_choose_target;b.route_groups=patched_route_groups;b.main()

if __name__=='__main__':main()
