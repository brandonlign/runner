#!/usr/bin/env python3
"""External-control-only blind ridge-detector pilot for MATLAS GC-stream lead.

Allowed image data in this stage: published Oyashio positive-control target
UGC9050-Dw1, HST GO-16890, F814W only.  No MATLAS Table-A.1 science target is
queried or downloaded.

The published clicked track is used ONLY after the detector scans the whole
field, to score recovery/rank of the known positive. It is never used to steer
background subtraction, orientation, width, component extraction, or the
MATLAS search.

This is a development pilot, not yet the frozen promotion gate. Failed trials
are preserved as provenance rather than silently overwritten.
"""
from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path

import numpy as np
from astropy.io import fits
from astroquery.mast import Observations
from scipy.ndimage import binary_closing, binary_dilation, gaussian_filter, label
from scipy.spatial import cKDTree
from skimage.morphology import disk, remove_small_objects, skeletonize

OUT = Path('results/matlas_oyashio_blind_detector_pilot')
OUT.mkdir(parents=True, exist_ok=True)
DOWNLOAD = OUT / 'download'
DOWNLOAD.mkdir(exist_ok=True)

PROGRAM = '16890'
TARGET = 'UGC9050-DW1'
FILTER = 'F814W'
EXPECTED_COMBINED = 'hst_16890_03_acs_wfc_f814w_jesd03_drc.fits'
TRUTH = Path('oyashio_published_truth_track.csv')

# Development parameters selected without MATLAS science pixels.
BROAD_SIGMA_PX = 32.0
HESSIAN_SIGMAS_PX = (2.0, 3.5, 5.0, 7.0)
BRIGHT_MASK_SIGMA = 12.0
BRIGHT_MASK_DILATE_PX = 6
EDGE_PX = 64
RIDGE_QUANTILE = 0.997
MIN_COMPONENT_AREA_PX = 20
TRUTH_MATCH_RADIUS_PX = 10.0

# Hard information-barrier list: exact published MATLAS sample is deliberately
# absent from every MAST query. This script accepts only GO-16890 + exact target.
FORBIDDEN_PREFIX = 'MATLAS'


def safe(x):
    try:
        if hasattr(x, 'item'):
            x = x.item()
    except Exception:
        pass
    if x is None:
        return None
    if isinstance(x, (str, int, float, bool)):
        return x
    return str(x)


def query_products():
    assert PROGRAM == '16890' and TARGET == 'UGC9050-DW1' and FILTER == 'F814W'
    assert FORBIDDEN_PREFIX not in TARGET.upper()
    obs = Observations.query_criteria(
        obs_collection='HST', proposal_id=PROGRAM, instrument_name='ACS/WFC',
        target_name=TARGET, filters=FILTER,
    )
    if not len(obs):
        raise RuntimeError('No exact Oyashio F814W observations found')
    # Verify MAST returned exactly the intended external target/filter/program.
    for r in obs:
        if str(r['proposal_id']) != PROGRAM or str(r['target_name']).upper() != TARGET or str(r['filters']).upper() != FILTER:
            raise RuntimeError(f'Information barrier query mismatch: {dict(r)!r}')
    prod = Observations.get_product_list(obs)
    rows=[]
    for r in prod:
        fn=str(r['productFilename']) if 'productFilename' in prod.colnames else ''
        sub=str(r['productSubGroupDescription']) if 'productSubGroupDescription' in prod.colnames else ''
        if sub.upper()!='DRC' or not fn.endswith('_drc.fits'):
            continue
        if not fn.startswith('hst_16890_03_acs_wfc_f814w_jesd03'):
            continue
        rows.append({
            'filename':fn,
            'dataURI':str(r['dataURI']) if 'dataURI' in prod.colnames else None,
            'size':int(r['size']) if 'size' in prod.colnames and r['size'] is not None else None,
            'productType':safe(r['productType']) if 'productType' in prod.colnames else None,
        })
    rows=sorted({r['filename']:r for r in rows}.values(), key=lambda x:(len(x['filename']),x['filename']))
    if EXPECTED_COMBINED not in {r['filename'] for r in rows}:
        raise RuntimeError(f'Expected published combined product missing: {[r["filename"] for r in rows]}')
    return rows


def download_one(row):
    # Use MAST's public download endpoint directly from metadata dataURI. No
    # broad product download is allowed, which keeps the barrier auditable.
    import requests
    uri=row['dataURI']
    if not uri:
        raise RuntimeError(f'No dataURI for {row}')
    dest=DOWNLOAD/row['filename']
    if dest.exists() and dest.stat().st_size>0:
        return dest
    url='https://mast.stsci.edu/api/v0.1/Download/file'
    with requests.get(url,params={'uri':uri},stream=True,timeout=(20,180)) as rr:
        rr.raise_for_status()
        with dest.open('wb') as f:
            for chunk in rr.iter_content(1024*1024):
                if chunk: f.write(chunk)
    return dest


def load_sci(path):
    with fits.open(path,memmap=False) as h:
        idx=None
        for j,hd in enumerate(h):
            if getattr(hd,'data',None) is not None and np.ndim(hd.data)==2:
                idx=j;break
        if idx is None: raise RuntimeError(f'No 2-D science image in {path.name}')
        arr=np.asarray(h[idx].data,dtype=np.float32)
        hdr=dict(h[idx].header)
        ph=dict(h[0].header)
    exptime=hdr.get('EXPTIME',ph.get('EXPTIME'))
    bunit=hdr.get('BUNIT',ph.get('BUNIT'))
    return arr, {'science_hdu':idx,'shape':list(arr.shape),'exptime_s':safe(exptime),'bunit':safe(bunit)}


def robust_sigma(a):
    a=np.asarray(a,float);a=a[np.isfinite(a)]
    if not a.size:return 1.0
    med=float(np.median(a));mad=float(np.median(np.abs(a-med)))
    sig=1.4826*mad
    if not np.isfinite(sig) or sig<=0:
        sig=float(np.std(a))
    return max(sig,1e-12)


def hessian_vesselness(resid, valid, sigma):
    # Scale-normalized Hessian. For a bright ridge one principal curvature is
    # strongly negative and the orthogonal curvature is weak.
    hxx=gaussian_filter(resid,sigma=sigma,order=(0,2),mode='nearest')*(sigma*sigma)
    hyy=gaussian_filter(resid,sigma=sigma,order=(2,0),mode='nearest')*(sigma*sigma)
    hxy=gaussian_filter(resid,sigma=sigma,order=(1,1),mode='nearest')*(sigma*sigma)
    tr=hxx+hyy
    disc=np.sqrt(np.maximum((hxx-hyy)**2+4*hxy*hxy,0))
    la=0.5*(tr-disc); lb=0.5*(tr+disc)
    swap=np.abs(la)>np.abs(lb)
    small=np.where(swap,lb,la); large=np.where(swap,la,lb)
    rb=np.abs(small)/(np.abs(large)+1e-12)
    ss=np.sqrt(small*small+large*large)
    # External-field adaptive contrast scale only; this is applied identically
    # to every field and will later be calibrated by whole-field null maxima.
    c=float(np.quantile(ss[valid],0.95)) if np.any(valid) else 1.0
    c=max(c,1e-12)
    beta=0.5
    v=np.exp(-(rb*rb)/(2*beta*beta))*(1-np.exp(-(ss*ss)/(2*c*c)))
    v[large>=0]=0
    v[~valid]=0
    return v.astype(np.float32)


def truth_points_dense():
    rows=[]
    with TRUTH.open() as f:
        for line in f:
            if line.startswith('#'):continue
            if line.strip().startswith('x,'):continue
            if not line.strip():continue
            x,y=map(float,line.strip().split(','));rows.append((x,y))
    p=np.asarray(rows,float)
    dense=[]
    for a,b in zip(p[:-1],p[1:]):
        n=max(2,int(np.ceil(np.hypot(*(b-a))))+1)
        for t in np.linspace(0,1,n,endpoint=False):dense.append(a*(1-t)+b*t)
    dense.append(p[-1])
    return p,np.asarray(dense,float)


def detect(arr):
    finite=np.isfinite(arr)
    # DRC uncovered border/chip areas may be exact zero. Mark only large exact-
    # zero regions invalid by treating zero as invalid when it is common enough.
    zero=(arr==0)&finite
    if zero.mean()>0.005:
        finite &= ~zero
    if finite.mean()<0.5: raise RuntimeError(f'Unexpected valid fraction {finite.mean()}')
    med=float(np.median(arr[finite]))
    fill=np.where(finite,arr,med).astype(np.float32)
    broad=gaussian_filter(fill,BROAD_SIGMA_PX,mode='nearest')
    resid=(fill-broad).astype(np.float32)
    sig=robust_sigma(resid[finite])
    norm=(resid/sig).astype(np.float32)

    small=gaussian_filter(norm,1.0,mode='nearest')
    bright=small>BRIGHT_MASK_SIGMA
    if BRIGHT_MASK_DILATE_PX:
        bright=binary_dilation(bright,structure=disk(BRIGHT_MASK_DILATE_PX))
    valid=finite & ~bright
    valid[:EDGE_PX,:]=False;valid[-EDGE_PX:,:]=False
    valid[:,:EDGE_PX]=False;valid[:,-EDGE_PX:]=False

    vmax=np.zeros(arr.shape,dtype=np.float32)
    best_scale=np.zeros(arr.shape,dtype=np.float32)
    for s in HESSIAN_SIGMAS_PX:
        v=hessian_vesselness(norm,valid,s)
        use=v>vmax
        vmax[use]=v[use];best_scale[use]=s

    vals=vmax[valid]
    threshold=float(np.quantile(vals,RIDGE_QUANTILE))
    binary=(vmax>=threshold)&valid
    binary=binary_closing(binary,structure=disk(1))
    binary=remove_small_objects(binary,min_size=MIN_COMPONENT_AREA_PX,connectivity=2)
    labs,nlab=label(binary,structure=np.ones((3,3),int))

    q50=float(np.quantile(vals,0.50));q999=float(np.quantile(vals,0.999))
    denom=max(q999-q50,1e-9)
    candidates=[]
    for lab in range(1,nlab+1):
        m=labs==lab;area=int(m.sum())
        if area<MIN_COMPONENT_AREA_PX:continue
        ys,xs=np.nonzero(m)
        sk=skeletonize(m);sklen=int(sk.sum())
        vv=vmax[m]
        scale=float(np.median(best_scale[m]))
        # Monotone score used only for within-field ranking in this pilot.
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
        'bright_mask_fraction':float(bright.mean()),'ridge_threshold':threshold,
        'vesselness_q50':q50,'vesselness_q999':q999,
        'candidate_n':len(candidates),'candidates':candidates,
    }, labs, vmax


def evaluate_truth(det,labs,vmax):
    _,dense=truth_points_dense()
    yy,xx=np.indices(labs.shape)
    # Efficient distance-to-track only near its bounding box.
    x0=max(0,int(np.floor(dense[:,0].min()-TRUTH_MATCH_RADIUS_PX-2)))
    x1=min(labs.shape[1],int(np.ceil(dense[:,0].max()+TRUTH_MATCH_RADIUS_PX+3)))
    y0=max(0,int(np.floor(dense[:,1].min()-TRUTH_MATCH_RADIUS_PX-2)))
    y1=min(labs.shape[0],int(np.ceil(dense[:,1].max()+TRUTH_MATCH_RADIUS_PX+3)))
    sy,sx=np.indices((y1-y0,x1-x0));pts=np.c_[sx.ravel()+x0,sy.ravel()+y0]
    dist,_=cKDTree(dense).query(pts,k=1)
    truthmask=np.zeros(labs.shape,bool)
    truthmask[y0:y1,x0:x1]=(dist.reshape(y1-y0,x1-x0)<=TRUTH_MATCH_RADIUS_PX)
    truth_labels=labs[truthmask]
    unique,counts=np.unique(truth_labels[truth_labels>0],return_counts=True)
    overlaps=sorted(zip(unique.tolist(),counts.tolist()),key=lambda z:-z[1])
    cand_by_label={c['label']:c for c in det['candidates']}
    matched=[]
    for lab,count in overlaps:
        if lab in cand_by_label:
            z=dict(cand_by_label[lab]);z['truth_overlap_px']=int(count);matched.append(z)
    truth_v=vmax[truthmask]
    return {
        'truth_track_dense_points_n':int(len(dense)),
        'truth_match_radius_px':TRUTH_MATCH_RADIUS_PX,
        'truth_region_vesselness_median':float(np.median(truth_v)),
        'truth_region_vesselness_q95':float(np.quantile(truth_v,0.95)),
        'matched_candidates':matched,
        'best_truth_candidate_rank':matched[0]['rank'] if matched else None,
        'best_truth_candidate_score':matched[0]['score'] if matched else None,
        'truth_candidate_recovered':bool(matched),
    }


def main():
    products=query_products()
    report={
        'role':'external positive-control development pilot only; not frozen promotion gate',
        'information_barrier':'Only GO-16890 UGC9050-DW1 F814W opened; zero MATLAS Table-A.1 target images queried/downloaded',
        'matlas_target_science_values_opened':False,
        'parameters':{
            'broad_sigma_px':BROAD_SIGMA_PX,'hessian_sigmas_px':list(HESSIAN_SIGMAS_PX),
            'bright_mask_sigma':BRIGHT_MASK_SIGMA,'bright_mask_dilate_px':BRIGHT_MASK_DILATE_PX,
            'edge_px':EDGE_PX,'ridge_quantile':RIDGE_QUANTILE,
            'min_component_area_px':MIN_COMPONENT_AREA_PX,'truth_match_radius_px':TRUTH_MATCH_RADIUS_PX,
        },
        'selected_product_metadata':products,
        'images':[],
    }
    for row in products:
        path=download_one(row)
        arr,hdr=load_sci(path)
        det,labs,v=detect(arr)
        truth=evaluate_truth(det,labs,v)
        report['images'].append({'filename':row['filename'],'header':hdr,'detector':det,'truth_evaluation':truth})
        # Avoid carrying control FITS in artifacts; report is reproducible from MAST.
        path.unlink(missing_ok=True)

    report['combined_filename']=EXPECTED_COMBINED
    combined=next(x for x in report['images'] if x['filename']==EXPECTED_COMBINED)
    individuals=[x for x in report['images'] if x['filename']!=EXPECTED_COMBINED]
    report['headline']={
        'combined_truth_recovered':combined['truth_evaluation']['truth_candidate_recovered'],
        'combined_truth_rank':combined['truth_evaluation']['best_truth_candidate_rank'],
        'individual_products_n':len(individuals),
        'individual_truth_recovered_n':sum(x['truth_evaluation']['truth_candidate_recovered'] for x in individuals),
        'individual_truth_ranks':[x['truth_evaluation']['best_truth_candidate_rank'] for x in individuals],
        'individual_exptimes_s':[x['header']['exptime_s'] for x in individuals],
    }
    (OUT/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report['headline'],indent=2,sort_keys=True))

if __name__=='__main__':main()
