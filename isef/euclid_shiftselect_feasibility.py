#!/usr/bin/env python3
"""Fast Stage-0 target selection using measured Euclid dither translations."""
import math
import numpy as np
import euclid_routed_feasibility as b

QS=None; SELECTED=None; SHIFTS=None; CENTERS=None

def hits(qs,ra,dec,margin=b.MARGIN):
    # A quadrant is only ~3.4 arcmin wide.  Rank by center distance and perform
    # expensive WCS inversion only on the nearest six quadrants.
    cd=max(math.cos(math.radians(dec)),0.2)
    d2=((CENTERS[:,0]-ra)*cd)**2+(CENTERS[:,1]-dec)**2
    idx=np.argpartition(d2,6)[:6]
    out=[]
    for k in idx:
        q=qs[int(k)]
        try:
            if b.contains(q,ra,dec,margin):
                x,y=b.pix(q,ra,dec); out.append((min(x,b.NX-x,y,b.NY-y),q.k))
        except Exception: pass
    return sorted(out,reverse=True)

def translated(target,shift,sign):
    ra,dec=target; dra,ddec=shift
    return ra+sign*dra/(3600*max(math.cos(math.radians(dec)),0.2)),dec+sign*ddec/3600

def search(qs,shifts):
    med=(float(np.median(CENTERS[:,0])),float(np.median(CENTERS[:,1])))
    order=sorted(range(144),key=lambda k:b.dist_arcsec(qs[k].center,med,med[1]))
    offsets=[0,-20,20,-40,40,-60,60,-80,80]; candidates=[]
    for sign in (-1,1):
      for oi,k in enumerate(order):
        cra,cdec=qs[k].center; cd=max(math.cos(math.radians(cdec)),0.2)
        for dx in offsets:
          for dy in offsets:
            target=(cra+dx/(3600*cd),cdec+dy/3600)
            hs=[hits(qs,*translated(target,shifts[g],sign)) for g in range(4)]
            if all(hs):
                pred={g:hs[g][0][1] for g in range(4)}; score=min(h[0][0] for h in hs)
                candidates.append((score,sign,k,target,pred,med))
        if candidates and max(x[0] for x in candidates)>b.MARGIN+100 and oi>=12: break
    candidates.sort(reverse=True,key=lambda z:z[0]); diagnostics=[]
    for score,sign,k,target,pred,med in candidates[:200]:
        actual={}; ok=True; rows=[]
        for g in range(4):
            q=b.getq(g,pred[g]); x,y=b.pix(q,*target); inside=b.contains(q,*target,b.MARGIN)
            rows.append({'group':g,'k':pred[g],'x':float(x),'y':float(y),'inside':bool(inside)})
            if not inside: ok=False; break
            actual[g]=pred[g]
        diagnostics.append({'score':float(score),'sign':sign,'epoch0_k':k,'pred':pred,'rows':rows})
        if ok:return score,sign,k,target,actual,med,diagnostics
    raise RuntimeError(f'no shift-selected candidate validated against actual group WCS; candidates={len(candidates)} tried={diagnostics[:20]}')

def patched_map_epoch0():return QS

def patched_choose_target(qs):
    score,sign,k,target,routes,med,diag=SELECTED;return k,target[0],target[1],med

def patched_route_groups(qs,target,shifts):
    score,sign,k,t,routes,med,diag=SELECTED;rows=[]
    for g,rk in routes.items():
        q=b.getq(g,rk);x,y=b.pix(q,*t)
        rows.append({'group':g,'candidate_k':rk,'extname':q.name,'x':float(x),'y':float(y),'inside':bool(b.contains(q,*t,b.MARGIN)),'shift_selection_sign':sign})
    rows.append({'selection_predicted_min_edge_margin_pixels':float(score),'validation_attempts':len(diag)})
    return routes,rows

def main():
    global QS,SELECTED,SHIFTS,CENTERS
    QS=b.map_epoch0();CENTERS=np.array([q.center for q in QS]);SHIFTS=b.pointing_shifts();SELECTED=search(QS,SHIFTS)
    print('SHIFT_SELECTED',{'score':SELECTED[0],'sign':SELECTED[1],'epoch0_k':SELECTED[2],'target':SELECTED[3],'routes':SELECTED[4]})
    b.map_epoch0=patched_map_epoch0;b.choose_target=patched_choose_target;b.route_groups=patched_route_groups;b.main()

if __name__=='__main__':main()
