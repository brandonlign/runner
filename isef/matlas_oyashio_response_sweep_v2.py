#!/usr/bin/env python3
"""Execution-equivalent acceleration of matlas_oyashio_response_sweep.py.

Science grid/statistics/ranking/pass rule are unchanged. The only change is
component bookkeeping: operate within scipy label bounding boxes rather than
rescanning the full 36M-pixel label image for every component. Truth is still
consulted only after whole-field candidates have been constructed and scored.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.ndimage import binary_closing, find_objects, label
from scipy.spatial import cKDTree
from skimage.morphology import disk, remove_small_objects, skeletonize
import matlas_oyashio_response_sweep as s
import matlas_oyashio_blind_detector_pilot as p


def component_table_fast(resp,valid,q,dense):
    vals=resp[valid]
    thr=float(np.quantile(vals,q))
    b=(resp>=thr)&valid
    b=binary_closing(b,structure=disk(1))
    b=remove_small_objects(b,min_size=s.MIN_AREA,connectivity=2)
    labs,n=label(b,structure=np.ones((3,3),int))
    objs=find_objects(labs)
    comps=[]
    # Truth bbox is used only to skip expensive post-ranking coverage geometry;
    # it cannot alter candidate construction, response, score or ranking.
    tx0=float(dense[:,0].min()-p.TRUTH_MATCH_RADIUS_PX)
    tx1=float(dense[:,0].max()+p.TRUTH_MATCH_RADIUS_PX)
    ty0=float(dense[:,1].min()-p.TRUTH_MATCH_RADIUS_PX)
    ty1=float(dense[:,1].max()+p.TRUTH_MATCH_RADIUS_PX)
    for labv,sl in enumerate(objs,1):
        if sl is None: continue
        sub=(labs[sl]==labv)
        area=int(sub.sum())
        if area<s.MIN_AREA: continue
        ys0,xs0=np.nonzero(sub)
        sk=skeletonize(sub)
        sy0,sx0=np.nonzero(sk)
        sklen=len(sx0)
        if sklen==0: continue
        yoff=sl[0].start; xoff=sl[1].start
        ys=ys0+yoff; xs=xs0+xoff
        vv=resp[sl][sub]
        score=float(np.mean(vv)*math.sqrt(sklen)*math.log1p(area))
        xmin=int(xs.min());xmax=int(xs.max());ymin=int(ys.min());ymax=int(ys.max())
        comps.append({'label':labv,'score':score,'area_px':area,'skeleton_length_px':sklen,
                      'response_mean':float(np.mean(vv)),'response_q90':float(np.quantile(vv,.9)),
                      'truth_track_coverage':0.0,
                      'x_min':xmin,'x_max':xmax,'y_min':ymin,'y_max':ymax,
                      '_sx':sx0+xoff,'_sy':sy0+yoff,
                      '_truth_bbox_possible':not (xmax<tx0 or xmin>tx1 or ymax<ty0 or ymin>ty1)})
    # Ranking is fully truth-blind and fixed before truth coverage is evaluated.
    comps.sort(key=lambda z:(-z['score'],z['label']))
    for i,c in enumerate(comps,1): c['rank']=i
    for c in comps:
        if c['_truth_bbox_possible']:
            candtree=cKDTree(np.c_[c['_sx'],c['_sy']])
            dist,_=candtree.query(dense,k=1)
            c['truth_track_coverage']=float(np.mean(dist<=p.TRUTH_MATCH_RADIUS_PX))
    best=max(comps,key=lambda z:z['truth_track_coverage'],default=None)
    for c in comps:
        c.pop('_sx',None);c.pop('_sy',None);c.pop('_truth_bbox_possible',None)
    return {'quantile':q,'threshold':thr,'candidate_n':len(comps),
            'best_truth_coverage':None if best is None else best['truth_track_coverage'],
            'best_truth_candidate_rank':None if best is None else best['rank'],
            'best_truth_candidate_score':None if best is None else best['score'],
            'positive_control_pass':bool(best and best['truth_track_coverage']>=0.50 and best['rank']<=10),
            'top20':comps[:20]}

s.component_table=component_table_fast

if __name__=='__main__':
    s.OUT=s.Path('results/matlas_oyashio_response_sweep_v2'); s.OUT.mkdir(parents=True,exist_ok=True)
    s.main()
