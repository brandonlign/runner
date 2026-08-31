#!/usr/bin/env python3
"""Audit the 13 prospectively excluded MATLAS-proposal fields as controls.

These targets occur in HST programs 16257/16711 but are not in Marleau et al.
2024 Table A.1. They were excluded from the 74-object science sample before any
science image was opened. This stage may therefore inspect their F814W images
as real, exposure-matched control backgrounds, but it must never query a
published-74 target.

Outputs are acquisition/noise/footprint diagnostics only, not a stream search.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import requests
from astropy.io import fits
from astroquery.mast import Observations
from scipy.ndimage import gaussian_filter

OUT=Path('results/matlas_excluded_f814w_background_audit')
OUT.mkdir(parents=True,exist_ok=True)
DL=OUT/'download';DL.mkdir(exist_ok=True)
PROGRAMS=('16257','16711','16082')
EXCLUDED=(
'MATLAS-1177','MATLAS-1297','MATLAS-1598','MATLAS-1847','MATLAS-1957',
'MATLAS-1996','MATLAS-2103','MATLAS-254','MATLAS-28','MATLAS-332',
'MATLAS-40','MATLAS-659','MATLAS-991')
PUBLISHED=set('''MATLAS-42 MATLAS-49 MATLAS-138 MATLAS-141 MATLAS-149 MATLAS-177 MATLAS-203 MATLAS-207 MATLAS-262 MATLAS-290 MATLAS-342 MATLAS-347 MATLAS-365 MATLAS-368 MATLAS-401 MATLAS-405 MATLAS-478 MATLAS-524 MATLAS-585 MATLAS-627 MATLAS-658 MATLAS-682 MATLAS-787 MATLAS-791 MATLAS-799 MATLAS-898 MATLAS-976 MATLAS-984 MATLAS-987 MATLAS-1059 MATLAS-1154 MATLAS-1174 MATLAS-1216 MATLAS-1225 MATLAS-1262 MATLAS-1302 MATLAS-1321 MATLAS-1332 MATLAS-1400 MATLAS-1408 MATLAS-1412 MATLAS-1413 MATLAS-1437 MATLAS-1470 MATLAS-1485 MATLAS-1530 MATLAS-1534 MATLAS-1539 MATLAS-1545 MATLAS-1550 MATLAS-1558 MATLAS-1577 MATLAS-1589 MATLAS-1616 MATLAS-1618 MATLAS-1630 MATLAS-1647 MATLAS-1662 MATLAS-1667 MATLAS-1740 MATLAS-1779 MATLAS-1794 MATLAS-1801 MATLAS-1865 MATLAS-1888 MATLAS-1907 MATLAS-1938 MATLAS-1975 MATLAS-1985 MATLAS-2019 MATLAS-2021 MATLAS-2069 MATLAS-2176 MATLAS-2184'''.split())
assert len(PUBLISHED)==74 and not (set(EXCLUDED)&PUBLISHED)


def robust_sigma(a):
    a=np.asarray(a,float);a=a[np.isfinite(a)]
    med=float(np.median(a));mad=float(np.median(np.abs(a-med)))
    return med,max(1.4826*mad,1e-30)


def choose_product(target):
    """Query proposal metadata first, then exact-filter locally.

    MAST's target_name criterion performs name resolution and returned no result
    for labels such as MATLAS-1177 despite those literal labels being present in
    the proposal metadata. Local exact filtering is the same strategy used by
    the successful frozen 74-target manifest and changes no science selection.
    """
    rows=[]
    for program in PROGRAMS:
        allobs=Observations.query_criteria(obs_collection='HST',proposal_id=program,
            instrument_name='ACS/WFC')
        if not len(allobs):continue
        mask=np.array([(str(r['target_name'])==target and str(r['filters']).upper()=='F814W') for r in allobs],bool)
        obs=allobs[mask]
        if not len(obs):continue
        for r in obs:
            literal=str(r['target_name'])
            if literal in PUBLISHED or literal=='MATLAS2019':
                raise RuntimeError(f'BARRIER BREACH target={literal}')
        prod=Observations.get_product_list(obs)
        for r in prod:
            fn=str(r['productFilename']) if 'productFilename' in prod.colnames else ''
            sub=str(r['productSubGroupDescription']) if 'productSubGroupDescription' in prod.colnames else ''
            if sub.upper()!='DRC' or not fn.endswith('_drc.fits'):continue
            if not fn.startswith('hst_') or '_acs_wfc_f814w_' not in fn or 'skycell' in fn:continue
            rows.append({'program':program,'filename':fn,'dataURI':str(r['dataURI']),
                'size':int(r['size']) if 'size' in prod.colnames and r['size'] is not None else None})
    if not rows:raise RuntimeError(f'No HAP F814W DRC for excluded control {target}')
    rows.sort(key=lambda r:(len(r['filename']),r['filename']))
    return rows[0],rows


def download(row):
    dest=DL/row['filename']
    with requests.get('https://mast.stsci.edu/api/v0.1/Download/file',params={'uri':row['dataURI']},
                      stream=True,timeout=(20,180)) as rr:
        rr.raise_for_status()
        with dest.open('wb') as f:
            for c in rr.iter_content(1024*1024):
                if c:f.write(c)
    return dest


def audit(path):
    with fits.open(path,memmap=False) as h:
        idx=next((j for j,x in enumerate(h) if getattr(x,'data',None) is not None and np.ndim(x.data)==2),None)
        if idx is None:raise RuntimeError('no 2D science')
        a=np.asarray(h[idx].data,dtype=np.float32);hdr=h[idx].header;ph=h[0].header
    finite=np.isfinite(a);zero=(a==0)&finite
    valid=finite & ~(zero if zero.mean()>0.005 else False)
    if valid.mean()<=0:raise RuntimeError(f'empty valid footprint {path.name}')
    med=float(np.median(a[valid]));fill=np.where(valid,a,med).astype(np.float32)
    resid=fill-gaussian_filter(fill,32.0,mode='nearest')
    rmed,rsig=robust_sigma(resid[valid])
    return {'shape':list(a.shape),'science_hdu':idx,'exptime_s':hdr.get('EXPTIME',ph.get('EXPTIME')),
        'bunit':hdr.get('BUNIT',ph.get('BUNIT')),'finite_fraction':float(finite.mean()),
        'nonzero_finite_fraction':float(valid.mean()),'raw_median':med,
        'broad32_residual_median':rmed,'broad32_residual_robust_sigma':rsig}


def main():
    report={'information_barrier':'Only 13 proposal targets excluded from published Table A.1 are opened; published 74 remain sealed',
        'published74_science_values_opened':False,'excluded_controls_n':len(EXCLUDED),'controls':[],
        'transport_repair':'proposal-first metadata query + exact local target/filter match; target set unchanged'}
    for j,target in enumerate(EXCLUDED,1):
        print(f'CONTROL {j}/{len(EXCLUDED)} {target}',flush=True)
        chosen,allrows=choose_product(target)
        path=download(chosen)
        stats=audit(path)
        report['controls'].append({'target':target,'chosen_product':chosen,
            'hap_f814w_drc_candidates':[r['filename'] for r in allrows],'stats':stats})
        path.unlink(missing_ok=True)
    exps=[float(x['stats']['exptime_s']) for x in report['controls'] if x['stats']['exptime_s'] is not None]
    report['summary']={'controls_n':len(report['controls']),'exptime_min_s':min(exps),'exptime_max_s':max(exps),
        'exptime_median_s':float(np.median(exps)),
        'valid_fraction_min':min(x['stats']['nonzero_finite_fraction'] for x in report['controls']),
        'valid_fraction_median':float(np.median([x['stats']['nonzero_finite_fraction'] for x in report['controls']]))}
    (OUT/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True,default=str)+'\n')
    print(json.dumps(report['summary'],indent=2,sort_keys=True))

if __name__=='__main__':main()
