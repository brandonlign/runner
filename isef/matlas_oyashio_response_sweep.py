#!/usr/bin/env python3
"""Bounded external-positive-control response sweep for the MATLAS stream lead.

This script may open only the published Oyashio external positive-control image.
The parameter grid below is frozen in source before execution. It compares two
whole-field ridge statistics and six fixed field quantiles. The published truth
track is evaluated only after each whole-field candidate map and truth-blind
candidate ranking are complete. No MATLAS Table-A.1 target is queried/opened.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter, binary_closing, binary_dilation, label
from scipy.spatial import cKDTree
from skimage.morphology import disk, remove_small_objects, skeletonize
import matlas_oyashio_blind_detector_pilot as p

OUT=Path('results/matlas_oyashio_response_sweep'); OUT.mkdir(parents=True,exist_ok=True)
QUANTILES=(0.90,0.925,0.95,0.975,0.99,0.995)
MIN_AREA=20


def preprocess(arr):
    finite=np.isfinite(arr)
    zero=(arr==0)&finite
    if zero.mean()>0.005: finite &= ~zero
    if finite.mean()<0.20: raise RuntimeError(f'Unexpected valid fraction {finite.mean()}')
    med=float(np.median(arr[finite])); fill=np.where(finite,arr,med).astype(np.float32)
    broad=gaussian_filter(fill,p.BROAD_SIGMA_PX,mode='nearest')
    resid=(fill-broad).astype(np.float32); sig=p.robust_sigma(resid[finite]); norm=(resid/sig).astype(np.float32)
    small=gaussian_filter(norm,1.0,mode='nearest'); bright=small>p.BRIGHT_MASK_SIGMA
    bright=binary_dilation(bright,structure=disk(p.BRIGHT_MASK_DILATE_PX))
    valid=finite & ~bright
    e=p.EDGE_PX; valid[:e,:]=False;valid[-e:,:]=False;valid[:,:e]=False;valid[:,-e:]=False
    return norm,valid,{'raw_valid_fraction':float(finite.mean()),'analysis_valid_fraction':float(valid.mean()),'resid_sigma_native':sig}


def responses(norm,valid):
    vmax=np.zeros(norm.shape,np.float32)
    cmax=np.zeros(norm.shape,np.float32)
    for s in p.HESSIAN_SIGMAS_PX:
        hxx=gaussian_filter(norm,sigma=s,order=(0,2),mode='nearest')*(s*s)
        hyy=gaussian_filter(norm,sigma=s,order=(2,0),mode='nearest')*(s*s)
        hxy=gaussian_filter(norm,sigma=s,order=(1,1),mode='nearest')*(s*s)
        tr=hxx+hyy; disc=np.sqrt(np.maximum((hxx-hyy)**2+4*hxy*hxy,0))
        la=.5*(tr-disc);lb=.5*(tr+disc);sw=np.abs(la)>np.abs(lb)
        small=np.where(sw,lb,la);large=np.where(sw,la,lb)
        rb=np.abs(small)/(np.abs(large)+1e-12)
        ss=np.sqrt(small*small+large*large)
        c=max(float(np.quantile(ss[valid],.95)),1e-12)
        v=np.exp(-(rb*rb)/(2*.5*.5))*(1-np.exp(-(ss*ss)/(2*c*c)));v[large>=0]=0;v[~valid]=0
        vmax=np.maximum(vmax,v.astype(np.float32))
        # Signed ridge-curvature significance: preserve positive ridge sign and
        # anisotropy, but do not saturate contrast against the field q95.
        raw=np.maximum(-large,0)*np.exp(-(rb*rb)/(2*.75*.75)); raw[~valid]=0
        rs=p.robust_sigma(raw[valid]); raw=(raw/rs).astype(np.float32); cmax=np.maximum(cmax,raw)
    return {'vesselness':vmax,'ridge_curvature_snr':cmax}


def truth_dense(): return p.truth_points_dense()[1]


def component_table(resp,valid,q,dense):
    vals=resp[valid]; thr=float(np.quantile(vals,q)); b=(resp>=thr)&valid
    b=binary_closing(b,structure=disk(1));b=remove_small_objects(b,min_size=MIN_AREA,connectivity=2)
    labs,n=label(b,structure=np.ones((3,3),int)); comps=[]
    tree=cKDTree(dense)
    for labv in range(1,n+1):
        m=labs==labv; area=int(m.sum())
        if area<MIN_AREA: continue
        ys,xs=np.nonzero(m); sk=skeletonize(m); sy,sx=np.nonzero(sk);sklen=len(sx)
        if sklen==0:continue
        vv=resp[m]
        # Truth-blind ranking: integrated ridge evidence with length preference.
        score=float(np.mean(vv)*math.sqrt(sklen)*math.log1p(area))
        # Truth evaluation only after score exists.
        candtree=cKDTree(np.c_[sx,sy]); dist,_=candtree.query(dense,k=1)
        coverage=float(np.mean(dist<=p.TRUTH_MATCH_RADIUS_PX))
        comps.append({'label':labv,'score':score,'area_px':area,'skeleton_length_px':sklen,
                      'response_mean':float(np.mean(vv)),'response_q90':float(np.quantile(vv,.9)),
                      'truth_track_coverage':coverage,
                      'x_min':int(xs.min()),'x_max':int(xs.max()),'y_min':int(ys.min()),'y_max':int(ys.max())})
    comps.sort(key=lambda z:(-z['score'],z['label']))
    for i,c in enumerate(comps,1): c['rank']=i
    best=max(comps,key=lambda z:z['truth_track_coverage'],default=None)
    return {'quantile':q,'threshold':thr,'candidate_n':len(comps),
            'best_truth_coverage':None if best is None else best['truth_track_coverage'],
            'best_truth_candidate_rank':None if best is None else best['rank'],
            'best_truth_candidate_score':None if best is None else best['score'],
            'positive_control_pass':bool(best and best['truth_track_coverage']>=0.50 and best['rank']<=10),
            'top20':comps[:20]}


def main():
    rows=p.query_products(); row=next(r for r in rows if r['filename']==p.EXPECTED_COMBINED)
    path=p.download_one(row); arr,hdr=p.load_sci(path); norm,valid,meta=preprocess(arr)
    dense=truth_dense(); rr=responses(norm,valid)
    report={'role':'external positive-control development only','matlas_target_science_values_opened':False,
            'information_barrier':'Only GO-16890 UGC9050-DW1 F814W combined DRC opened',
            'frozen_grid':{'response_types':list(rr),'quantiles':list(QUANTILES),'min_area_px':MIN_AREA,
                           'pass_rule':'single connected candidate truth-track coverage >=0.50 and truth-blind rank <=10'},
            'image':{'filename':row['filename'],'header':hdr,'preprocess':meta},'results':{}}
    for name,resp in rr.items():
        tv=[]
        # response percentile of truth tube is diagnostic only, not candidate construction
        _,dense2=p.truth_points_dense(); tree=cKDTree(dense2)
        x0=max(0,int(dense2[:,0].min()-10));x1=min(resp.shape[1],int(dense2[:,0].max()+11))
        y0=max(0,int(dense2[:,1].min()-10));y1=min(resp.shape[0],int(dense2[:,1].max()+11))
        yy,xx=np.indices((y1-y0,x1-x0)); pts=np.c_[xx.ravel()+x0,yy.ravel()+y0];dist,_=tree.query(pts)
        mask=(dist.reshape(y1-y0,x1-x0)<=10); truthvals=resp[y0:y1,x0:x1][mask]
        vals=resp[valid]
        report['results'][name]={'truth_region_median':float(np.median(truthvals)),
            'truth_region_q95':float(np.quantile(truthvals,.95)),
            'truth_q95_field_percentile':float(np.mean(vals<=np.quantile(truthvals,.95))),
            'threshold_sweep':[component_table(resp,valid,q,dense) for q in QUANTILES]}
    path.unlink(missing_ok=True)
    (OUT/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    compact={k:[{'q':x['quantile'],'pass':x['positive_control_pass'],'rank':x['best_truth_candidate_rank'],'coverage':x['best_truth_coverage'],'n':x['candidate_n']} for x in v['threshold_sweep']] for k,v in report['results'].items()}
    print(json.dumps(compact,indent=2,sort_keys=True))

if __name__=='__main__': main()
