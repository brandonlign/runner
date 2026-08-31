#!/usr/bin/env python3
"""External-positive-control path-integrated strip significance diagnostic.

Allowed image data: only published Oyashio UGC9050-Dw1 GO-16890 F814W combined
HAP/DRC. No MATLAS Table-A.1 science target and no MATLAS null-control image is
queried/opened.

This is deliberately NOT a blind search. The published track is used as an
external labelled positive only after a fixed preprocessing and a source-frozen
width/null grid are defined. The statistic compares a narrow central strip with
symmetric local sidebands and evaluates it against translated copies of the
same curved track over the whole usable field. This diagnoses whether coherent
low-surface-brightness signal survives preprocessing and what externally
calibrated width range is plausible before building a blind path search.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates, binary_dilation
from skimage.morphology import disk
import matlas_oyashio_blind_detector_pilot as p

OUT=Path('results/matlas_oyashio_strip_significance');OUT.mkdir(parents=True,exist_ok=True)
WIDTHS_PX=(2,3,4,5,6,8,10)
TRACK_STEP_PX=2.0
NULL_TRANSLATIONS_N=800
MIN_SAMPLE_VALID_FRACTION=0.90
RNG_SEED=20260831


def preprocess(arr):
    finite=np.isfinite(arr)
    zero=(arr==0)&finite
    if zero.mean()>0.005: finite &= ~zero
    med=float(np.median(arr[finite])); fill=np.where(finite,arr,med).astype(np.float32)
    broad=gaussian_filter(fill,p.BROAD_SIGMA_PX,mode='nearest')
    resid=(fill-broad).astype(np.float32)
    sig=p.robust_sigma(resid[finite]); norm=(resid/sig).astype(np.float32)
    small=gaussian_filter(norm,1.0,mode='nearest')
    bright=small>p.BRIGHT_MASK_SIGMA
    bright=binary_dilation(bright,structure=disk(p.BRIGHT_MASK_DILATE_PX))
    valid=finite & ~bright
    e=p.EDGE_PX;valid[:e,:]=False;valid[-e:,:]=False;valid[:,:e]=False;valid[:,-e:]=False
    return norm,valid,{'resid_sigma_native':sig,'analysis_valid_fraction':float(valid.mean()),'bright_mask_fraction':float(bright.mean())}


def resample_track():
    raw,_=p.truth_points_dense()
    # Arc-length resample the clicked polyline at fixed 2-pixel spacing.
    d=np.sqrt(np.sum(np.diff(raw,axis=0)**2,axis=1)); s=np.r_[0,np.cumsum(d)]
    ss=np.arange(0,s[-1]+1e-9,TRACK_STEP_PX)
    x=np.interp(ss,s,raw[:,0]); y=np.interp(ss,s,raw[:,1])
    # Smooth finite-difference tangent only for strip normals; centerline remains
    # the published positive-control track.
    dx=np.gradient(x);dy=np.gradient(y);nn=np.hypot(dx,dy);nn=np.maximum(nn,1e-9)
    nx=-dy/nn;ny=dx/nn
    return np.c_[x,y],np.c_[nx,ny],float(s[-1])


def offsets_for_width(w):
    central=np.arange(-w,w+0.001,1.0)
    inner=2*w+2
    outer=4*w+2
    side=np.r_[np.arange(-outer,-inner+0.001,1.0),np.arange(inner,outer+0.001,1.0)]
    return central,side


def strip_score(img,valid,track,normals,w,dx=0.0,dy=0.0):
    cen,side=offsets_for_width(w)
    def sample(off):
        xx=track[:,0,None]+dx+normals[:,0,None]*off[None,:]
        yy=track[:,1,None]+dy+normals[:,1,None]*off[None,:]
        vals=map_coordinates(img,[yy.ravel(),xx.ravel()],order=1,mode='constant',cval=np.nan).reshape(xx.shape)
        vm=map_coordinates(valid.astype(np.float32),[yy.ravel(),xx.ravel()],order=0,mode='constant',cval=0).reshape(xx.shape)>0.5
        vals[~vm]=np.nan
        return vals,vm
    cv,cm=sample(cen);sv,sm=sample(side)
    # Require most of both strips to lie on usable image.
    frac=float((cm.sum()+sm.sum())/(cm.size+sm.size))
    if frac<MIN_SAMPLE_VALID_FRACTION:return None
    # Equal-weight each longitudinal position so a handful of bright residuals
    # cannot dominate merely by having more finite transverse samples.
    cprof=np.nanmean(cv,axis=1);sprof=np.nanmean(sv,axis=1)
    good=np.isfinite(cprof)&np.isfinite(sprof)
    if good.mean()<MIN_SAMPLE_VALID_FRACTION:return None
    diff=cprof[good]-sprof[good]
    # Trim the top/bottom 2.5% longitudinal differences symmetrically to reduce
    # residual compact-source leverage. This rule is frozen for all widths/nulls.
    lo,hi=np.quantile(diff,[.025,.975]);use=diff[(diff>=lo)&(diff<=hi)]
    return {'mean_excess_sigma':float(np.mean(use)),'median_excess_sigma':float(np.median(diff)),
            'sample_valid_fraction':frac,'longitudinal_n':int(good.sum()),'trimmed_n':int(len(use))}


def translated_nulls(img,valid,track,normals,w):
    rng=np.random.default_rng(RNG_SEED+int(w*100))
    # Translation bounds preserve the entire central+sideband geometry inside
    # the array before masks are considered.
    _,side=offsets_for_width(w);margin=float(np.max(np.abs(side))+3)
    xmin=track[:,0].min();xmax=track[:,0].max();ymin=track[:,1].min();ymax=track[:,1].max()
    dxlo=int(np.ceil(margin-xmin));dxhi=int(np.floor(img.shape[1]-1-margin-xmax))
    dylo=int(np.ceil(margin-ymin));dyhi=int(np.floor(img.shape[0]-1-margin-ymax))
    out=[];attempts=0
    # Exclude translations whose centerline remains within 50 px of the labelled
    # positive track; otherwise the positive could contaminate its own null.
    while len(out)<NULL_TRANSLATIONS_N and attempts<NULL_TRANSLATIONS_N*60:
        attempts+=1
        dx=int(rng.integers(dxlo,dxhi+1));dy=int(rng.integers(dylo,dyhi+1))
        if abs(dx)<=50 and abs(dy)<=50:continue
        z=strip_score(img,valid,track,normals,w,dx,dy)
        if z is not None:out.append({'dx':dx,'dy':dy,**z})
    if len(out)<NULL_TRANSLATIONS_N:raise RuntimeError(f'Only {len(out)} usable null translations for width {w}')
    return out


def robust_z(x,null):
    a=np.asarray(null,float);med=float(np.median(a));mad=float(np.median(np.abs(a-med)));s=max(1.4826*mad,1e-12)
    return (float(x)-med)/s,med,s


def main():
    rows=p.query_products();row=next(r for r in rows if r['filename']==p.EXPECTED_COMBINED)
    path=p.download_one(row);arr,hdr=p.load_sci(path);img,valid,meta=preprocess(arr)
    track,normals,length=resample_track()
    rep={'role':'external positive-control path-integrated diagnostic only','matlas_target_science_values_opened':False,
         'matlas_null_control_science_values_opened':False,
         'information_barrier':'Only GO-16890 UGC9050-Dw1 F814W combined DRC opened',
         'frozen_grid':{'width_half_px':list(WIDTHS_PX),'track_step_px':TRACK_STEP_PX,'null_translations_n':NULL_TRANSLATIONS_N,
                        'sidebands':'for half-width w: |offset| from 2w+2 through 4w+2 px','min_sample_valid_fraction':MIN_SAMPLE_VALID_FRACTION,
                        'longitudinal_trim':'symmetric 2.5% tails'},
         'image':{'filename':row['filename'],'header':hdr,'preprocess':meta},'track_length_px':length,'results':[]}
    for w in WIDTHS_PX:
        print('WIDTH',w,flush=True)
        truth=strip_score(img,valid,track,normals,w)
        if truth is None:raise RuntimeError(f'Published track invalid for width {w}')
        nulls=translated_nulls(img,valid,track,normals,w)
        mz=[x['mean_excess_sigma'] for x in nulls];medz=[x['median_excess_sigma'] for x in nulls]
        zmean,nmed,nscale=robust_z(truth['mean_excess_sigma'],mz)
        zmedian,mmed,mscale=robust_z(truth['median_excess_sigma'],medz)
        rep['results'].append({'width_half_px':w,'central_full_width_px':2*w+1,'truth':truth,
            'empirical_null':{'n':len(nulls),'mean_stat_median':nmed,'mean_stat_robust_sigma':nscale,
                              'median_stat_median':mmed,'median_stat_robust_sigma':mscale,
                              'mean_stat_empirical_ge_fraction':float(np.mean(np.asarray(mz)>=truth['mean_excess_sigma'])),
                              'median_stat_empirical_ge_fraction':float(np.mean(np.asarray(medz)>=truth['median_excess_sigma']))},
            'truth_vs_null_robust_z_mean':float(zmean),'truth_vs_null_robust_z_median':float(zmedian)})
    path.unlink(missing_ok=True)
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    print(json.dumps([{'w':x['width_half_px'],'zmean':x['truth_vs_null_robust_z_mean'],'zmedian':x['truth_vs_null_robust_z_median'],
                       'pmean':x['empirical_null']['mean_stat_empirical_ge_fraction']} for x in rep['results']],indent=2))
if __name__=='__main__':main()
