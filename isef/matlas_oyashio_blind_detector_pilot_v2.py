#!/usr/bin/env python3
"""Geometry-only repair wrapper for Oyashio blind-detector pilot v1.

Pilot v1 stopped before ridge calculation because a HAP DRC has 47.5% valid
footprint while its sanity check required >50%.  This wrapper preserves every
detector parameter/calculation from v1 and changes only that pre-computation
sanity floor from 0.50 to 0.20.  The invalid/uncovered pixels remain excluded
from every statistic.  This is an infrastructure/footprint repair, not a
scientific retune, and the failed v1 run remains preserved in Actions history.
"""
from pathlib import Path
import math

import numpy as np
from scipy.ndimage import binary_closing, binary_dilation, gaussian_filter, label
from skimage.morphology import disk, remove_small_objects, skeletonize

import matlas_oyashio_blind_detector_pilot as p


def detect_v2(arr):
    finite=np.isfinite(arr)
    zero=(arr==0)&finite
    if zero.mean()>0.005:
        finite &= ~zero
    if finite.mean()<0.20:
        raise RuntimeError(f'Unexpectedly tiny valid footprint {finite.mean()}')
    med=float(np.median(arr[finite]))
    fill=np.where(finite,arr,med).astype(np.float32)
    broad=gaussian_filter(fill,p.BROAD_SIGMA_PX,mode='nearest')
    resid=(fill-broad).astype(np.float32)
    sig=p.robust_sigma(resid[finite])
    norm=(resid/sig).astype(np.float32)

    small=gaussian_filter(norm,1.0,mode='nearest')
    bright=small>p.BRIGHT_MASK_SIGMA
    if p.BRIGHT_MASK_DILATE_PX:
        bright=binary_dilation(bright,structure=disk(p.BRIGHT_MASK_DILATE_PX))
    valid=finite & ~bright
    valid[:p.EDGE_PX,:]=False;valid[-p.EDGE_PX:,:]=False
    valid[:,:p.EDGE_PX]=False;valid[:,-p.EDGE_PX:]=False

    vmax=np.zeros(arr.shape,dtype=np.float32)
    best_scale=np.zeros(arr.shape,dtype=np.float32)
    for s in p.HESSIAN_SIGMAS_PX:
        v=p.hessian_vesselness(norm,valid,s)
        use=v>vmax
        vmax[use]=v[use];best_scale[use]=s

    vals=vmax[valid]
    threshold=float(np.quantile(vals,p.RIDGE_QUANTILE))
    binary=(vmax>=threshold)&valid
    binary=binary_closing(binary,structure=disk(1))
    binary=remove_small_objects(binary,min_size=p.MIN_COMPONENT_AREA_PX,connectivity=2)
    labs,nlab=label(binary,structure=np.ones((3,3),int))

    q50=float(np.quantile(vals,0.50));q999=float(np.quantile(vals,0.999))
    denom=max(q999-q50,1e-9)
    candidates=[]
    for lab in range(1,nlab+1):
        m=labs==lab;area=int(m.sum())
        if area<p.MIN_COMPONENT_AREA_PX:continue
        ys,xs=np.nonzero(m)
        sk=skeletonize(m);sklen=int(sk.sum())
        vv=vmax[m]
        scale=float(np.median(best_scale[m]))
        intensity=(float(np.quantile(vv,0.90))-q50)/denom
        score=float(max(intensity,0)*math.sqrt(max(sklen,1))*math.log1p(area))
        candidates.append({
            'label':lab,'score':score,'area_px':area,'skeleton_length_px':sklen,
            'median_scale_px':scale,'vesselness_q90':float(np.quantile(vv,0.90)),
            'x_min':int(xs.min()),'x_max':int(xs.max()),'y_min':int(ys.min()),'y_max':int(ys.max()),
        })
    candidates.sort(key=lambda z:(-z['score'],z['label']))
    for rank,c in enumerate(candidates,1):c['rank']=rank
    return {
        'resid_sigma_native':sig,'valid_fraction':float(valid.mean()),
        'raw_finite_nonzero_fraction_before_masks':float(finite.mean()),
        'bright_mask_fraction':float(bright.mean()),'ridge_threshold':threshold,
        'vesselness_q50':q50,'vesselness_q999':q999,
        'candidate_n':len(candidates),'candidates':candidates,
        'v2_geometry_only_change':'minimum accepted raw valid footprint 0.50 -> 0.20; uncovered pixels still excluded',
    }, labs, vmax


if __name__=='__main__':
    p.OUT=Path('results/matlas_oyashio_blind_detector_pilot_v2')
    p.OUT.mkdir(parents=True,exist_ok=True)
    p.DOWNLOAD=p.OUT/'download';p.DOWNLOAD.mkdir(exist_ok=True)
    p.detect=detect_v2
    p.main()
