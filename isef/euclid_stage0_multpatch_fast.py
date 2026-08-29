#!/usr/bin/env python3
"""Fast geometry-only selection + multi-patch Euclid Stage-0 replication.

Uses the already validated global dither translation model to propose detector
routes locally, then exact per-epoch WCS only for accepted geometry candidates.
No image/photometry outcome participates in patch selection.
"""
import math,json
from pathlib import Path
import numpy as np
import euclid_routed_feasibility as b
import euclid_stage0_multpatch as m

OUT=Path('results/euclid_stage0_multpatch_fast.json');NPATCH=4;MINSEP=500.0

def shifted(target,shift,sign=-1):
    ra,de=target;dx,dy=shift;cd=max(math.cos(math.radians(de)),0.2);return ra+sign*dx/(3600*cd),de+sign*dy/3600

def main():
    # Astropy returns 0-d ndarray pixel coordinates for scalar sky inputs on
    # some WCS paths. Normalize the shared interface once so arbitrary targets
    # work in stamp()/contains(), rather than only the original wrapper target.
    rawpix=b.pix
    def scalar_pix(q,ra,de):
        x,y=rawpix(q,ra,de);return float(np.asarray(x)),float(np.asarray(y))
    b.pix=scalar_pix
    qs=b.map_epoch0();cent=np.array([q.center for q in qs]);sh=b.pointing_shifts();med=(float(np.median(cent[:,0])),float(np.median(cent[:,1])))
    order=sorted(range(144),key=lambda k:b.dist_arcsec(qs[k].center,med,med[1]));proposals=[]
    offsets=[(0,0),(-35,0),(35,0),(0,-35),(0,35),(-35,-35),(35,35)]
    for k in order:
        cra,cde=qs[k].center;cd=max(math.cos(math.radians(cde)),0.2)
        for dx,dy in offsets:
            t=(cra+dx/(3600*cd),cde+dy/3600);pred={};score=1e9;ok=True
            for g in range(4):
                eq=shifted(t,sh[g],-1);d=np.hypot((cent[:,0]-eq[0])*max(math.cos(math.radians(eq[1])),0.2),cent[:,1]-eq[1])*3600;kk=int(np.argmin(d));arc=float(d[kk])
                if arc>=140:ok=False;break
                pred[g]=kk;score=min(score,140-arc)
            if ok:proposals.append((score,k,t,pred))
    proposals.sort(reverse=True,key=lambda z:z[0]);selected=[];attempts=0
    for score,k,t,pred in proposals:
        if any(b.dist_arcsec(t,p['target'],(t[1]+p['target'][1])/2)<MINSEP for p in selected):continue
        attempts+=1;routes={};marg=[];valid=True
        for g in range(4):
            try:
                q=b.getq(g,pred[g]);x,y=b.pix(q,*t);inside=b.contains(q,*t,b.MARGIN+20)
            except Exception:inside=False
            if not inside:valid=False;break
            routes[g]=pred[g];marg.append(float(min(x,y,b.NX-x,b.NY-y)))
        if valid:selected.append({'target':t,'epoch0_k':k,'routes':routes,'min_margin_pixels':min(marg),'proposal_score':float(score)})
        if len(selected)>=NPATCH:break
    rows=[m.run_patch(p) for p in selected]
    good=[r for r in rows if 'median_fractional_scatter' in r]
    out={'success':len(selected)==NPATCH and len(good)==NPATCH,'note':'fast geometry-only patch selection; exact WCS validates geometry before any pixels are read','selection':{'requested':NPATCH,'selected':len(selected),'exact_validation_attempts':attempts,'minimum_separation_arcsec':MINSEP},'patches':rows}
    if good:out['aggregate']={'patches_good':len(good),'total_valid_stars':int(sum(r['valid_all_epochs'] for r in good)),'median_of_patch_median_scatter':float(np.median([r['median_fractional_scatter'] for r in good])),'range_patch_median_scatter':[float(min(r['median_fractional_scatter'] for r in good)),float(max(r['median_fractional_scatter'] for r in good))],'total_gt10pct_excursions':int(sum(r['gt10pct_excursions'] for r in good)),'total_gt20pct_excursions':int(sum(r['gt20pct_excursions'] for r in good)),'max_excursion':float(max(r['max_excursion'] for r in good))}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
